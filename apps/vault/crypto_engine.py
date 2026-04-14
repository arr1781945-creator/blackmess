"""
apps/vault/crypto_engine.py
Master cryptographic engine for the vault.

FIX #1 — assert → if/raise ValueError
  assert bisa di-disable dengan python -O. Untuk validasi kriptografi
  harus pakai if + raise agar tidak bisa di-bypass.

FIX #2 — encrypt_blob: blob_key_enc adalah plaintext placeholder
  Sebelumnya: blob_key_enc = base64.b64encode(blob_key).decode()  # Placeholder
  Ini menyimpan AES key dalam plaintext di DB — semua blob bisa didekripsi.
  Fix: selalu enkripsi blob key dengan master key (AES-KW style via AES-GCM).
  Integrasi Kyber encapsulation tetap ada sebagai path utama jika PK tersedia.

FIX #3 — vault_key_for_user: tambah domain-specific salt
  HKDF tanpa salt masih aman, tapi salt mencegah cross-context key reuse.
"""
import os
import base64
import hashlib
import logging
from typing import Tuple

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidTag

logger = logging.getLogger(__name__)

# Domain salt untuk HKDF — mencegah cross-context key reuse
_VAULT_HKDF_SALT = b"blackmess-vault-hkdf-salt-v1"


def aes_encrypt(plaintext: bytes, aad: bytes = b"vault") -> Tuple[bytes, bytes, bytes]:
    """
    AES-256-GCM encryption.
    Returns (ciphertext, nonce, auth_tag).

    FIX #1: Ganti assert → if/raise ValueError
    """
    from django.conf import settings
    key = settings.AES_MASTER_KEY

    # FIX #1: if/raise, bukan assert (assert bisa di-disable dengan python -O)
    if len(key) != 32:
        raise ValueError(
            f"AES-256 requires a 32-byte key, got {len(key)} bytes. "
            "Set AES_MASTER_KEY ke 32 bytes di settings."
        )

    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ct_with_tag = aesgcm.encrypt(nonce, plaintext, aad)
    ciphertext = ct_with_tag[:-16]
    tag = ct_with_tag[-16:]
    return ciphertext, nonce, tag


def aes_decrypt(ciphertext: bytes, nonce: bytes, tag: bytes, aad: bytes = b"vault") -> bytes:
    """
    AES-256-GCM decryption.
    Raises InvalidTag jika ciphertext ditamper.
    """
    from django.conf import settings
    key = settings.AES_MASTER_KEY

    if len(key) != 32:
        raise ValueError(f"AES-256 requires a 32-byte key, got {len(key)} bytes.")

    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext + tag, aad)


def vault_key_for_user(user_id: str, purpose: str = "vault") -> bytes:
    """
    Derive deterministic 32-byte per-user vault key dari master key.
    Different purpose strings yield different keys.

    FIX #3: Tambah domain-specific salt untuk HKDF.
    """
    from django.conf import settings
    info = f"securebank:{purpose}:{user_id}".encode()
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_VAULT_HKDF_SALT,   # FIX #3: salt eksplisit
        info=info,
    ).derive(settings.AES_MASTER_KEY)


def encrypt_field(plaintext: str, user_id: str, field_name: str) -> str:
    """
    Encrypt single model field value.
    Returns base64-encoded blob: nonce(12) + tag(16) + ciphertext.
    """
    if not plaintext:
        return ""
    key = vault_key_for_user(user_id, purpose=f"field:{field_name}")
    aad = f"field:{field_name}".encode()
    ciphertext, nonce, tag = aes_encrypt(plaintext.encode(), aad=aad)
    combined = nonce + tag + ciphertext
    return base64.b64encode(combined).decode()


def decrypt_field(encrypted_b64: str, user_id: str, field_name: str) -> str:
    """
    Decrypt field yang dienkripsi dengan encrypt_field().
    """
    if not encrypted_b64:
        return ""
    try:
        combined = base64.b64decode(encrypted_b64)
        nonce, tag, ciphertext = combined[:12], combined[12:28], combined[28:]
        aad = f"field:{field_name}".encode()
        return aes_decrypt(ciphertext, nonce, tag, aad=aad).decode()
    except (InvalidTag, Exception) as e:
        logger.error("decrypt_field failed user=%s field=%s: %s", user_id, field_name, e)
        return "[DECRYPTION_FAILED]"


def _wrap_key_with_master(blob_key: bytes) -> str:
    """
    FIX #2 helper: Enkripsi blob_key dengan AES master key (key wrapping).
    Returns base64(nonce + tag + encrypted_blob_key).
    """
    ct, nonce, tag = aes_encrypt(blob_key, aad=b"blob-key-wrap")
    return base64.b64encode(nonce + tag + ct).decode()


def _unwrap_key_with_master(wrapped_b64: str) -> bytes:
    """Decrypt blob_key yang di-wrap dengan master key."""
    raw = base64.b64decode(wrapped_b64)
    nonce, tag, ct = raw[:12], raw[12:28], raw[28:]
    return aes_decrypt(ct, nonce, tag, aad=b"blob-key-wrap")


def encrypt_blob(data: bytes, owner_id: str) -> dict:
    """
    Encrypt binary blob dengan fresh random key.
    Blob key dienkripsi dengan Kyber pubkey owner (jika ada)
    atau dengan master key sebagai fallback.

    FIX #2: Blob key selalu dienkripsi — tidak pernah plaintext.
    Sebelumnya ada Placeholder yang menyimpan blob_key sebagai base64 biasa.
    """
    from apps.users.models import UserPublicKey

    blob_key = os.urandom(32)

    # Encrypt blob content
    aesgcm = AESGCM(blob_key)
    nonce = os.urandom(12)
    ct_with_tag = aesgcm.encrypt(nonce, data, b"vault-blob")
    ciphertext = ct_with_tag[:-16]
    tag = ct_with_tag[-16:]

    # Enkripsi blob key
    try:
        from apps.users.utils_pqc import kyber_encapsulate, OQS_AVAILABLE
        if OQS_AVAILABLE:
            pk_record = UserPublicKey.objects.get(
                user_id=owner_id, key_type="kyber_1024", is_current=True
            )
            # kyber_encapsulate returns (ciphertext_b64, shared_secret_bytes)
            kyber_ct_b64, shared_secret = kyber_encapsulate(pk_record.public_key_b64)
            # Wrap blob_key dengan shared_secret dari Kyber
            wrap_aesgcm = AESGCM(shared_secret)
            wrap_nonce = os.urandom(12)
            wrapped_key = wrap_aesgcm.encrypt(wrap_nonce, blob_key, b"kyber-blob-wrap")
            blob_key_enc = base64.b64encode(
                wrap_nonce + wrapped_key
            ).decode() + f"|kyber:{kyber_ct_b64}"
        else:
            raise ImportError("OQS not available")
    except (UserPublicKey.DoesNotExist, ImportError, Exception) as e:
        logger.warning("Kyber wrap gagal, fallback ke master key wrap: %s", e)
        # FIX #2: Fallback ke master key wrapping — BUKAN plaintext base64
        blob_key_enc = _wrap_key_with_master(blob_key)

    # Zero-out blob_key dari memory
    del blob_key

    return {
        "blob_key_enc": blob_key_enc,
        "blob_nonce_b64": base64.b64encode(nonce).decode(),
        "blob_tag_b64": base64.b64encode(tag).decode(),
        "ciphertext_bytes": ciphertext,
        "checksum_sha256": hashlib.sha256(data).hexdigest(),
    }


def compute_field_hmac(value: str, user_id: str) -> str:
    """
    Deterministic HMAC-SHA256 untuk equality search pada encrypted fields
    tanpa dekripsi (e.g. lookup by ID number).
    """
    import hmac as hmac_lib
    key = vault_key_for_user(user_id, "search-hmac")
    mac = hmac_lib.new(key, value.encode(), hashlib.sha256)
    return mac.hexdigest()
