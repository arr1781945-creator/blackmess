#!/bin/bash
# =============================================================================
# blackmess_setup.sh
# Script untuk:
#   3. Backfill ImmutableAuditLog.timestamp
#   4. Generate ENCRYPTION_KEY
#   5. Set SECURE settings di environment
#
# Jalankan dari root project:
#   chmod +x backfill_and_setup.sh
#   ./backfill_and_setup.sh
# =============================================================================

set -e  # Exit jika ada error

cd "$(dirname "$0")"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║     BlackMess — Post-Deploy Setup        ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Backfill ImmutableAuditLog.timestamp
# ─────────────────────────────────────────────────────────────────────────────
echo "▶ STEP 3: Backfill ImmutableAuditLog.timestamp..."

python manage.py shell << 'PYEOF'
from apps.compliance.models import ImmutableAuditLog
from django.db.models import F

total = ImmutableAuditLog.objects.filter(timestamp__isnull=True).count()
if total == 0:
    print("  ✓ Tidak ada row yang perlu dibackfill.")
else:
    updated = ImmutableAuditLog.objects.filter(
        timestamp__isnull=True
    ).update(timestamp=F('created_at'))
    print(f"  ✓ Backfill selesai: {updated} row diupdate.")

# Verifikasi
remaining = ImmutableAuditLog.objects.filter(timestamp__isnull=True).count()
if remaining > 0:
    print(f"  ⚠ Masih ada {remaining} row dengan timestamp=NULL!")
else:
    print("  ✓ Semua row sudah punya timestamp.")
PYEOF

echo ""

# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — Generate ENCRYPTION_KEY
# ─────────────────────────────────────────────────────────────────────────────
echo "▶ STEP 4: Generate ENCRYPTION_KEY..."

# Cek apakah sudah ada di environment
if [ -n "$ENCRYPTION_KEY" ]; then
    echo "  ✓ ENCRYPTION_KEY sudah ada di environment, skip generate."
else
    echo "  Generating new ENCRYPTION_KEY..."
    NEW_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    echo ""
    echo "  ┌─────────────────────────────────────────────────────┐"
    echo "  │ ENCRYPTION_KEY (copy ke Railway/env variable):      │"
    echo "  │                                                     │"
    echo "  │ ENCRYPTION_KEY=$NEW_KEY"
    echo "  │                                                     │"
    echo "  │ ⚠ SIMPAN SEKARANG — tidak akan ditampilkan lagi!   │"
    echo "  │ ⚠ JANGAN commit ke git!                            │"
    echo "  └─────────────────────────────────────────────────────┘"
    echo ""

    # Cek apakah ada .env file
    if [ -f ".env" ]; then
        # Cek apakah ENCRYPTION_KEY sudah ada di .env
        if grep -q "ENCRYPTION_KEY" .env; then
            echo "  ⚠ ENCRYPTION_KEY sudah ada di .env — tidak dioverride."
            echo "    Ganti manual jika perlu."
        else
            echo "  Menambahkan ke .env..."
            echo "" >> .env
            echo "# Fernet key untuk enkripsi TOTP secret di MFADevice" >> .env
            echo "ENCRYPTION_KEY=$NEW_KEY" >> .env
            echo "  ✓ ENCRYPTION_KEY ditambahkan ke .env"
        fi
    else
        echo "  ℹ .env tidak ditemukan."
        echo "    Set ENCRYPTION_KEY secara manual di Railway / environment:"
        echo "    ENCRYPTION_KEY=$NEW_KEY"
    fi
fi

echo ""

# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — Verifikasi SECURE settings di settings.py
# ─────────────────────────────────────────────────────────────────────────────
echo "▶ STEP 5: Verifikasi SECURE settings..."

python manage.py shell << 'PYEOF'
from django.conf import settings

checks = [
    ("SECURE_PROXY_SSL_HEADER", 
     getattr(settings, 'SECURE_PROXY_SSL_HEADER', None),
     ('HTTP_X_FORWARDED_PROTO', 'https'),
     "Tambahkan: SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')"),

    ("SECURE_SSL_REDIRECT",
     getattr(settings, 'SECURE_SSL_REDIRECT', False),
     True,
     "Tambahkan: SECURE_SSL_REDIRECT = not DEBUG"),

    ("SESSION_COOKIE_SECURE",
     getattr(settings, 'SESSION_COOKIE_SECURE', False),
     True,
     "Tambahkan: SESSION_COOKIE_SECURE = True"),

    ("CSRF_COOKIE_SECURE",
     getattr(settings, 'CSRF_COOKIE_SECURE', False),
     True,
     "Tambahkan: CSRF_COOKIE_SECURE = True"),

    ("SECURE_HSTS_SECONDS",
     getattr(settings, 'SECURE_HSTS_SECONDS', 0),
     31536000,
     "Tambahkan: SECURE_HSTS_SECONDS = 31536000  # 1 tahun"),

    ("SECURE_CONTENT_TYPE_NOSNIFF",
     getattr(settings, 'SECURE_CONTENT_TYPE_NOSNIFF', False),
     True,
     "Tambahkan: SECURE_CONTENT_TYPE_NOSNIFF = True"),

    ("DEBUG",
     getattr(settings, 'DEBUG', True),
     False,
     "⚠ DEBUG harus False di production!"),

    ("ENCRYPTION_KEY",
     bool(getattr(settings, 'ENCRYPTION_KEY', None)),
     True,
     "Set ENCRYPTION_KEY di environment variable"),
]

print("")
print("  Setting                         Status   Catatan")
print("  " + "─" * 70)

all_ok = True
for name, current, expected, hint in checks:
    if name == "DEBUG":
        ok = current == expected
        status = "✓ OK" if ok else "✗ FAIL"
        note = "" if ok else "DEBUG=True di production!"
    else:
        ok = current == expected or (isinstance(expected, bool) and bool(current) == expected)
        status = "✓ OK  " if ok else "✗ MISS"
        note = "" if ok else hint

    print(f"  {name:<32} {status}   {note}")
    if not ok:
        all_ok = False

print("")
if all_ok:
    print("  ✅ Semua SECURE settings sudah benar!")
else:
    print("  ⚠ Ada settings yang perlu ditambahkan ke core/settings.py")
    print("    Lihat catatan di atas untuk setiap setting yang MISS.")
PYEOF

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║           Setup Selesai!                 ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "Langkah selanjutnya:"
echo "  1. Pastikan ENCRYPTION_KEY sudah di-set di environment"
echo "  2. Tambahkan SECURE settings yang MISS ke core/settings.py"
echo "  3. Restart server: gunicorn / railway up"
echo ""
