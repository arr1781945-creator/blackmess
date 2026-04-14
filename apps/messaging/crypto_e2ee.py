"""
apps/messaging/crypto_e2ee.py
Client-side E2EE helpers (server-side utilities for key distribution).
AES-256-GCM message encryption/decryption + hybrid KEM session key setup.

NOTE: The server processes only opaque ciphertext. These utilities are used
for the server's own system messages (join/leave notifications), NOT for
decrypting user messages.
"""

import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes


def aes_gcm_encrypt(key_bytes: bytes, plaintext: bytes, aad: bytes = b"") -> tuple[str, str, str]:
    """
    Encrypt plaintext with AES-256-GCM.
    Returns (ciphertext_b64, nonce_b64, auth_tag_b64).
    Note: AESGCM appends 16-byte tag to ciphertext automatically.
    """
    if not (len(key_bytes) == 32): raise ValueError("AES-256 requires 32-byte key")
    nonce = os.urandom(12)  # 96-bit nonce — GCM standard
    aesgcm = AESGCM(key_bytes)
    ct_with_tag = aesgcm.encrypt(nonce, plaintext, aad or None)
    ciphertext = ct_with_tag[:-16]
    auth_tag = ct_with_tag[-16:]
    return (
        base64.b64encode(ciphertext).decode(),
        base64.b64encode(nonce).decode(),
        base64.b64encode(auth_tag).decode(),
    )


def aes_gcm_decrypt(key_bytes: bytes, ciphertext_b64: str, nonce_b64: str, auth_tag_b64: str, aad: bytes = b"") -> bytes:
    """
    Decrypt AES-256-GCM ciphertext. Raises cryptography.exceptions.InvalidTag on tamper.
    """
    nonce = base64.b64decode(nonce_b64)
    ciphertext = base64.b64decode(ciphertext_b64)
    auth_tag = base64.b64decode(auth_tag_b64)
    aesgcm = AESGCM(key_bytes)
    return aesgcm.decrypt(nonce, ciphertext + auth_tag, aad or None)


def derive_message_key(shared_secret: bytes, channel_id: str, message_id: str) -> bytes:
    """
    Derive a per-message AES key from the shared secret using HKDF-SHA-256.
    Info = channel_id + message_id binds the key to this exact message.
    """
    info = f"securebank-msg-key:{channel_id}:{message_id}".encode()
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=info,
    ).derive(shared_secret)


def encrypt_system_message(plaintext: str, channel_id: str) -> dict:
    """
    Encrypt a server-generated system message (e.g. r'User joined channel').
    Uses a deterministic per-channel server key derived from AES_MASTER_KEY.
    """
    from django.conf import settings
    server_key = derive_message_key(settings.AES_MASTER_KEY, channel_id, "system-key")
    ct_b64, nonce_b64, tag_b64 = aes_gcm_encrypt(server_key, plaintext.encode(), aad=channel_id.encode())
    return {
        "ciphertext_b64": ct_b64,
        "nonce_b64": nonce_b64,
        "auth_tag_b64": tag_b64,
        "is_system": True,
    }
