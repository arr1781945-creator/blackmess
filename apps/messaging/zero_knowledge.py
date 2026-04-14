"""
apps/messaging/zero_knowledge.py

FIX — Hapus duplikasi kode (dua versi dalam satu file)
  File sebelumnya berisi versi lama corrupted + versi baru.
  File ini adalah versi bersih saja.

Catatan: fungsi-fungsi ini menggunakan HMAC dengan AES_MASTER_KEY
sebagai secret — ini bukan zero-knowledge proof yang sesungguhnya,
melainkan HMAC-based membership proof. Nama "ZK" di sini adalah
marketing, bukan kriptografi ZK yang formal.
"""
import hashlib
import hmac
import base64
import os
from django.conf import settings


def _master_key_bytes() -> bytes:
    """Pastikan AES_MASTER_KEY selalu bytes, bukan str."""
    key = settings.AES_MASTER_KEY
    if isinstance(key, str):
        return key.encode('utf-8')
    return key


def create_zk_commitment(plaintext: str) -> str:
    """
    Create commitment — SHA-256(salt || plaintext).
    Salt acak 32 bytes memastikan commitment unik meskipun plaintext sama.
    """
    salt = os.urandom(32)
    commitment = hashlib.sha256(
        salt + plaintext.encode('utf-8')
    ).digest()
    return base64.b64encode(salt + commitment).decode()


def verify_zk_commitment(plaintext: str, commitment_b64: str) -> bool:
    """Verify commitment."""
    try:
        raw = base64.b64decode(commitment_b64)
        if len(raw) < 32:
            return False
        salt = raw[:32]
        stored_commitment = raw[32:]
        computed = hashlib.sha256(salt + plaintext.encode('utf-8')).digest()
        return hmac.compare_digest(computed, stored_commitment)
    except Exception:
        return False


def create_zk_channel_proof(user_id: str, channel_id: str) -> str:
    """
    HMAC-based proof bahwa user adalah member channel.
    Server verifikasi — client tidak bisa forge tanpa SECRET_KEY.
    """
    secret = _master_key_bytes()[:32]
    msg = f"{user_id}:{channel_id}".encode()
    proof = hmac.new(secret, msg, hashlib.sha256).digest()
    return base64.b64encode(proof).decode()


def verify_zk_channel_proof(user_id: str, channel_id: str, proof_b64: str) -> bool:
    """Verify channel membership proof."""
    try:
        expected = create_zk_channel_proof(user_id, channel_id)
        return hmac.compare_digest(
            base64.b64decode(proof_b64),
            base64.b64decode(expected),
        )
    except Exception:
        return False


def zk_message_receipt(message_id: str, receiver_id: str) -> str:
    """Zero-knowledge read receipt — HMAC(message_id:receiver_id)."""
    secret = _master_key_bytes()[:32]
    msg = f"receipt:{message_id}:{receiver_id}".encode()
    receipt = hmac.new(secret, msg, hashlib.sha256).digest()
    return base64.b64encode(receipt).decode()
