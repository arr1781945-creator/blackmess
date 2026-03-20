#!/usr/bin/env bash
# ================================================================
# devops/setup_bank_env.sh
# BlackMess — Termux / Ubuntu auto-install script.
# Usage: bash setup_bank_env.sh
# ================================================================

set -euo pipefail
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

info()    { echo -e "${CYAN}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

echo -e "${CYAN}"
echo "  ╔═══════════════════════════════════════╗"
echo "  ║  BlackMess — Setup Script  ║"
echo "  ╚═══════════════════════════════════════╝"
echo -e "${NC}"

# ── Detect environment ──────────────────────────────────────────
IS_TERMUX=false
if [ -d "/data/data/com.termux" ]; then
  IS_TERMUX=true
  info "Detected Termux environment."
fi

# ── 1. System packages ──────────────────────────────────────────
info "Installing system dependencies..."
if $IS_TERMUX; then
  pkg update -y
  pkg install -y python postgresql redis nodejs git libffi openssl liboqs
else
  sudo apt-get update -qq
  sudo apt-get install -y \
    python3.11 python3.11-venv python3-pip \
    postgresql postgresql-contrib \
    redis-server \
    nodejs npm \
    git curl libffi-dev libssl-dev \
    build-essential pkg-config \
    ipfs
fi
success "System packages installed."

# ── 2. Python venv ──────────────────────────────────────────────
info "Creating Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip wheel setuptools -q
success "Virtual environment ready."

# ── 3. Python dependencies ──────────────────────────────────────
info "Installing Python requirements..."
pip install -r requirements.txt -q
success "Python dependencies installed."

# ── 4. PostgreSQL setup ─────────────────────────────────────────
info "Configuring PostgreSQL..."
if $IS_TERMUX; then
  initdb "$PREFIX/var/lib/postgresql" 2>/dev/null || true
  pg_ctl -D "$PREFIX/var/lib/postgresql" start -l "$PREFIX/var/log/postgresql.log" 2>/dev/null || true
else
  sudo systemctl start postgresql
  sudo systemctl enable postgresql
fi

sleep 2

# Create DB and user
if $IS_TERMUX; then
  createuser -s blackmess_user 2>/dev/null || warn "User may already exist."
  createdb -O blackmess_user blackmess_db 2>/dev/null || warn "DB may already exist."
else
  sudo -u postgres psql -c "CREATE USER blackmess_user WITH ENCRYPTED PASSWORD 'CHANGE_THIS_PASSWORD';" 2>/dev/null || warn "User may exist."
  sudo -u postgres psql -c "CREATE DATABASE blackmess_db OWNER blackmess_user;" 2>/dev/null || warn "DB may exist."
  sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE blackmess_db TO blackmess_user;" 2>/dev/null || true
fi
success "PostgreSQL configured."

# ── 5. Redis ────────────────────────────────────────────────────
info "Starting Redis..."
if $IS_TERMUX; then
  redis-server --daemonize yes --logfile "$HOME/redis.log"
else
  sudo systemctl start redis-server
  sudo systemctl enable redis-server
fi
success "Redis running."

# ── 6. IPFS ─────────────────────────────────────────────────────
info "Initialising IPFS..."
if command -v ipfs &>/dev/null; then
  ipfs init 2>/dev/null || warn "IPFS already initialised."
  ipfs daemon &>/dev/null &
  disown
  success "IPFS daemon started."
else
  warn "IPFS not found — file attachments will use fallback storage."
fi

# ── 7. Environment file ─────────────────────────────────────────
if [ ! -f ".env" ]; then
  info "Creating .env from template..."
  cp .env.example .env
  # Generate random secret key
  SK=$(python3 -c "from django.utils.crypto import get_random_string; print(get_random_string(50))" 2>/dev/null || \
       python3 -c "import secrets,string; print(secrets.token_urlsafe(50))")
  JWT_SK=$(python3 -c "import secrets; print(secrets.token_hex(32))")
  AES_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
  sed -i "s/CHANGE_ME_USE_DJANGO_SECRET_KEY_GEN_50_CHARS/$SK/" .env
  sed -i "s/CHANGE_ME_SEPARATE_FROM_SECRET_KEY/$JWT_SK/" .env
  sed -i "s/CHANGE_ME_64_HEX_CHARS_AES256/$AES_KEY/" .env
  success ".env created with generated keys."
else
  warn ".env already exists — skipping."
fi

# ── 8. Generate PQC keys ─────────────────────────────────────────
info "Generating PQC key pairs (Kyber-1024 + Dilithium3)..."
mkdir -p secrets
python3 - <<'PYEOF'
try:
    import oqs, base64
    with oqs.KeyEncapsulation("Kyber1024") as kem:
        pk = kem.generate_keypair()
        sk = kem.export_secret_key()
    with open("secrets/kyber_private.key", "wb") as f: f.write(sk)
    with open("secrets/kyber_public.key", "wb") as f: f.write(pk)

    with oqs.Signature("Dilithium3") as sig:
        pk2 = sig.generate_keypair()
        sk2 = sig.export_secret_key()
    with open("secrets/dilithium_private.key", "wb") as f: f.write(sk2)
    with open("secrets/dilithium_public.key", "wb") as f: f.write(pk2)
    print("  [OK] PQC keys generated in secrets/")
except ImportError:
    print("  [WARN] liboqs-python not available — PQC keys not generated.")
    print("         Install: pip install liboqs-python")
PYEOF
chmod 600 secrets/*.key 2>/dev/null || true

# ── 9. Django setup ──────────────────────────────────────────────
info "Running Django migrations..."
python3 manage.py migrate --no-input
success "Migrations complete."

info "Collecting static files..."
python3 manage.py collectstatic --no-input -v 0
success "Static files collected."

info "Creating __init__.py files for apps..."
for app in users workspace messaging vault compliance; do
  touch "apps/${app}/__init__.py" 2>/dev/null || true
  touch "apps/${app}/apps.py"     2>/dev/null || true
done

# ── 10. Frontend dependencies ─────────────────────────────────────
if [ -f "frontend/package.json" ]; then
  info "Installing frontend dependencies..."
  cd frontend && npm install -q && cd ..
  success "Frontend dependencies installed."
fi

# ── 11. Final summary ────────────────────────────────────────────
echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅  Setup Complete!                          ║${NC}"
echo -e "${GREEN}╠═══════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║${NC}  Start dev server:                            ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}    ${CYAN}source .venv/bin/activate${NC}                  ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}    ${CYAN}daphne -b 0.0.0.0 -p 8000 myproject.asgi:application${NC}   ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}                                               ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  Start Celery worker:                         ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}    ${CYAN}celery -A myproject worker -l INFO${NC}              ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}                                               ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  API Docs:                                    ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}    ${CYAN}http://localhost:8000/api/docs/client/${NC}     ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}                                               ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  ${RED}⚠  Update .env before production deploy!  ${NC}   ${GREEN}║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════╝${NC}"
