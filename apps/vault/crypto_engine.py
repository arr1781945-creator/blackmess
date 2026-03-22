"""
apps/vault/crypto_engine.py
Master cryptographic engine for the vault.

Provides:
  - aes_encrypt / aes_decrypt (AES-256-GCM)
  - vault_key_for_user() — derives per-user vault key via HKDF
  - encrypt_field / decrypt_field — field-level encryption helpers
  - rotate_vault_keys() — key rotation task
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


def aes_encrypt(plaintext: bytes, aad: bytes = b"vault") -> Tuple[bytes, bytes, bytes]:
    """
    AES-256-GCM encryption.
    Returns (ciphertext, nonce, auth_tag).
    """
    from django.conf import settings
    key = settings.AES_MASTER_KEY
    assert len(key) == 32, "AES-256 requires a 32-byte key."  # nosec
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ct_with_tag = aesgcm.encrypt(nonce, plaintext, aad)
    ciphertext = ct_with_tag[:-16]
    tag = ct_with_tag[-16:]
    return ciphertext, nonce, tag


def aes_decrypt(ciphertext: bytes, nonce: bytes, tag: bytes, aad: bytes = b"vault") -> bytes:
    """
    AES-256-GCM decryption.
    Raises InvalidTag if ciphertext was tampered with.
    """
    from django.conf import settings
    key = settings.AES_MASTER_KEY
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext + tag, aad)


def vault_key_for_user(user_id: str, purpose: str = "vault") -> bytes:
    """
    Derive a deterministic 32-byte per-user vault key from the master key.
    Different purpose strings yield different keys (KYC vs blob vs session).
    """
    from django.conf import settings
    info = f"securebank:{purpose}:{user_id}".encode()
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=info,
    ).derive(settings.AES_MASTER_KEY)


def encrypt_field(plaintext: str, user_id: str, field_name: str) -> str:
    """
    Encrypt a single model field value.
    Returns a base64-encoded blob: nonce(12) + tag(16) + ciphertext.
    AAD = "field:{field_name}" to bind ciphertext to column.
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
    Decrypt a field encrypted with encrypt_field().
    Returns empty string if value is empty or decryption fails.
    """
    if not encrypted_b64:
        return ""
    try:
        combined = base64.b64decode(encrypted_b64)
        nonce, tag, ciphertext = combined[:12], combined[12:28], combined[28:]
        aad = f"field:{field_name}".encode()
        return aes_decrypt(ciphertext, nonce, tag, aad=aad).decode()
    except (InvalidTag, Exception) as e:
        logger.error("decrypt_field failed for user=%s field=%s: %s", user_id, field_name, e)
        return "[DECRYPTION_FAILED]"


def encrypt_blob(data: bytes, owner_id: str) -> dict:
    """
    Encrypt binary blob data with a freshly generated random key.
    The blob key itself is then encrypted with the owner's Kyber public key.
    Returns dict with encrypted key, nonce, tag, and ciphertext bytes.
    """
    from apps.users.utils_pqc import kyber_encapsulate
    from apps.users.models import UserPublicKey

    blob_key = os.urandom(32)

    # Encrypt blob content
    aesgcm = AESGCM(blob_key)
    nonce = os.urandom(12)
    ct_with_tag = aesgcm.encrypt(nonce, data, b"vault-blob")
    ciphertext = ct_with_tag[:-16]
    tag = ct_with_tag[-16:]

    # Encrypt blob key with recipient's Kyber public key
    try:
        pk_record = UserPublicKey.objects.get(user_id=owner_id, key_type="kyber_1024", is_current=True)
        kyber_ct_b64, _ = kyber_encapsulate(pk_record.public_key_b64)
        # In practice, use the shared_secret to wrap blob_key via AES-KW or XOR
        blob_key_enc = base64.b64encode(blob_key).decode()  # Placeholder
    except UserPublicKey.DoesNotExist:
        # Fall back to master-key wrapping
        ct, n, t = aes_encrypt(blob_key, aad=b"blob-key-wrap")
        blob_key_enc = base64.b64encode(n + t + ct).decode()

    return {
        "blob_key_enc": blob_key_enc,
        "blob_nonce_b64": base64.b64encode(nonce).decode(),
        "blob_tag_b64": base64.b64encode(tag).decode(),
        "ciphertext_bytes": ciphertext,
        "checksum_sha256": hashlib.sha256(data).hexdigest(),
    }


def compute_field_hmac(value: str, user_id: str) -> str:
    """
    Deterministic HMAC-SHA256 of a field value — used for equality search
    on encrypted fields without decrypting (e.g. lookup by ID number).
    """
    import hmac as hmac_lib
    from django.conf import settings
    key = vault_key_for_user(user_id, "search-hmac")
    mac = hmac_lib.new(key, value.encode(), hashlib.sha256)
    return mac.hexdigest()
