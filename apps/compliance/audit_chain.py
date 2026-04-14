"""
apps/compliance/audit_chain.py
Blockchain-style immutable audit chain.

FIX #1: Race condition — get_last_hash + create sekarang dalam satu
         SELECT FOR UPDATE di dalam @transaction.atomic. Tidak ada
         jendela waktu untuk concurrent insert dengan prev_hash sama.

FIX #2: Timestamp mismatch — sebelumnya create_audit_entry pakai
         timezone.now().isoformat() tapi verify_audit_chain pakai
         log.created_at.isoformat(). Keduanya berbeda karena ada delay
         antara Python dan DB auto_now_add, sehingga chain SELALU
         dianggap tampered. Fix: simpan timestamp eksplisit di field
         tersendiri (bukan auto_now_add) dan pakai nilai yang sama
         saat create dan verify.

CATATAN: Requires migration untuk tambah field `timestamp` (DateTimeField,
         bukan auto_now_add) ke model ImmutableAuditLog. Lihat komentar
         di bawah.
"""
import hashlib
import json
import logging
from django.utils import timezone
from django.db import transaction as db_transaction

logger = logging.getLogger(__name__)

GENESIS_HASH = "GENESIS_BLOCK_BLACKMESS"


def compute_chain_hash(prev_hash: str, entry_data: dict) -> str:
    """Blockchain-style hash — setiap log hash dari log sebelumnya."""
    payload = f"{prev_hash}{json.dumps(entry_data, sort_keys=True, default=str)}"
    return hashlib.sha256(payload.encode()).hexdigest()


@db_transaction.atomic
def create_audit_entry(
    workspace_id: str,
    sender_id: str,
    receiver_id: str,
    message_hash: str,
    channel: str,
    action: str,
    device_info: dict = None,
    ip_address: str = None,
):
    """
    Buat entry audit log yang tidak bisa dimanipulasi.

    FIX #1 — Atomic + SELECT FOR UPDATE:
    Dengan select_for_update() pada baris terakhir, tidak ada concurrent
    request yang bisa menyisipkan entry baru dengan prev_hash yang sama
    sebelum kita selesai. Lock dilepas otomatis saat transaksi commit.

    FIX #2 — Satu sumber timestamp:
    Kita buat timestamp sekali di Python, simpan ke field eksplisit
    di model (bukan auto_now_add), dan pakai nilai yang sama persis
    saat build entry_data untuk hashing.
    """
    from apps.compliance.models import ImmutableAuditLog

    # FIX #1: Lock baris terakhir agar tidak ada concurrent insert
    # yang mengambil prev_hash yang sama.
    last = (
        ImmutableAuditLog.objects
        .select_for_update()               # exclusive row lock
        .filter(workspace_id=workspace_id)
        .order_by(r'-timestamp')            # FIX #2: order by field eksplisit, bukan created_at
        .first()
    )
    prev_hash = last.chain_hash if last else GENESIS_HASH

    # FIX #2: Buat timestamp sekali, pakai di entry_data DAN saat simpan ke DB
    ts = timezone.now()
    ts_iso = ts.isoformat()

    entry_data = {
        r'workspace_id': workspace_id,
        r'sender_id': sender_id,
        r'receiver_id': receiver_id,
        r'message_hash': message_hash,
        r'channel': channel,
        r'action': action,
        r'timestamp': ts_iso,              # FIX #2: nilai sama yang disimpan ke model
        r'device_info': device_info or {},
        r'ip_address': ip_address or '',
    }

    chain_hash = compute_chain_hash(prev_hash, entry_data)

    return ImmutableAuditLog.objects.create(
        workspace_id=workspace_id,
        sender_id=sender_id,
        receiver_id=receiver_id,
        message_hash=message_hash,
        channel=channel,
        action=action,
        device_info=json.dumps(device_info or {}),
        ip_address=ip_address or '',
        prev_hash=prev_hash,
        chain_hash=chain_hash,
        timestamp=ts,                     # FIX #2: simpan ke field eksplisit
    )


def verify_audit_chain(workspace_id: str) -> dict:
    """
    Verifikasi integritas chain.

    FIX #2: Gunakan log.timestamp (field eksplisit) bukan log.created_at
    agar hash yang dicompute saat verify cocok dengan hash saat create.
    """
    from apps.compliance.models import ImmutableAuditLog

    logs = (
        ImmutableAuditLog.objects
        .filter(workspace_id=workspace_id)
        .order_by(r'timestamp')            # FIX #2: order by field eksplisit
    )

    if not logs.exists():
        return {r'valid': True, 'message': 'No logs found', 'count': 0}

    prev_hash = GENESIS_HASH
    broken_at = None

    for log in logs:
        entry_data = {
            r'workspace_id': log.workspace_id,
            r'sender_id': log.sender_id,
            r'receiver_id': log.receiver_id,
            r'message_hash': log.message_hash,
            r'channel': log.channel,
            r'action': log.action,
            r'timestamp': log.timestamp.isoformat(),   # FIX #2: pakai log.timestamp
            r'device_info': json.loads(log.device_info) if log.device_info else {},
            r'ip_address': log.ip_address,
        }
        expected_hash = compute_chain_hash(prev_hash, entry_data)

        if expected_hash != log.chain_hash or log.prev_hash != prev_hash:
            broken_at = log.id
            logger.critical(
                "Audit chain BROKEN at entry %s workspace=%s — possible tampering!",
                log.id, workspace_id,
            )
            break

        prev_hash = log.chain_hash

    # Hitung count sekali di akhir (bukan dalam loop)
    total = logs.count()

    if broken_at:
        return {
            r'valid': False,
            r'message': f'Chain broken at entry {broken_at} - possible tampering!',
            r'broken_at': str(broken_at),
            r'count': total,
        }

    return {
        r'valid': True,
        r'message': 'Audit chain integrity verified',
        r'count': total,
    }


# ─── Migration yang perlu dibuat ─────────────────────────────────────────────
#
# Tambahkan field `timestamp` ke ImmutableAuditLog:
#
#   migrations.AddField(
#       model_name=r'immutableauditlog',
#       name=r'timestamp',
#       field=models.DateTimeField(
#           null=True,          # null=True dulu untuk existing rows
#           db_index=True,
#           help_text=r'Explicit timestamp untuk hashing — BUKAN auto_now_add',
#       ),
#   ),
#
# Setelah deploy, backfill: ImmutableAuditLog.objects.filter(timestamp__isnull=True)
#   .update(timestamp=F(r'created_at'))
# Lalu set null=False via migration kedua.
#
# Juga update Meta ordering di model:
#   ordering = [r'timestamp']   # ganti dari ['created_at']
