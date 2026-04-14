"""
apps/messaging/ipfs_handler.py
IPFS file upload/download with encryption.

FIX #1 — Path traversal di fallback local storage
  channel_id dari user input langsung dipakai sebagai path component
  tanpa sanitasi. UUID adalah channel_id yang valid — validasi format.

FIX #2 — File encryption key derived dari filename yang predictable
  Sebelumnya: key = HKDF(AES_MASTER_KEY, channel_id, f"file:{filename}")
  Filename dicontrol user — dua file nama sama punya key sama.
  Fix: tambah random file_id (UUID) ke key derivation sehingga
  setiap upload punya key unik meski filename dan channel sama.
  file_id disimpan di return dict dan DB untuk keperluan dekripsi.

FIX #3 — safe_name[:50] bisa collision
  base64(filename)[:50] bisa sama untuk filename berbeda.
  Fix: gunakan UUID sebagai nama file di local storage.
"""
import logging
import base64
import os
import uuid as uuid_lib
from django.conf import settings
from .crypto_e2ee import aes_gcm_encrypt, aes_gcm_decrypt, derive_message_key

logger = logging.getLogger(__name__)

# UUID regex untuk validasi channel_id
import re
_UUID_RE = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.IGNORECASE,
)


def _validate_channel_id(channel_id: str) -> str:
    """
    FIX #1: Validasi channel_id adalah UUID yang valid.
    Cegah path traversal seperti '../../../etc/passwd'.
    """
    if not _UUID_RE.match(str(channel_id)):
        raise ValueError(f"Invalid channel_id format: {channel_id!r}")
    return str(channel_id)


def _get_ipfs_client():
    """Get IPFS client — fallback to local storage if unavailable."""
    try:
        import ipfshttpclient
        return ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')
    except Exception as e:
        logger.warning("IPFS unavailable: %s — using local fallback", e)
        return None


def upload_encrypted_file(file_bytes: bytes, filename: str, channel_id: str) -> dict:
    """
    Encrypt file dengan AES-256-GCM lalu upload ke IPFS.
    Returns dict dengan cid, nonce, auth_tag, file_id.

    FIX #1: Validasi channel_id sebelum pakai sebagai path.
    FIX #2: Tambah file_id unik ke key derivation.
    FIX #3: Gunakan file_id sebagai nama file di local storage.
    """
    channel_id = _validate_channel_id(channel_id)

    # FIX #2: file_id unik per upload — key tidak bisa diprediksi
    file_id = str(uuid_lib.uuid4())

    file_key = derive_message_key(
        settings.AES_MASTER_KEY,
        channel_id,
        f"file:{file_id}",      # FIX #2: pakai file_id, bukan filename
    )

    ct_b64, nonce_b64, tag_b64 = aes_gcm_encrypt(
        file_key, file_bytes, aad=channel_id.encode()
    )
    encrypted_bytes = base64.b64decode(ct_b64)

    client = _get_ipfs_client()
    if client:
        try:
            cid = client.add_bytes(encrypted_bytes)
            logger.info("IPFS upload: %s (file_id=%s) -> %s", filename, file_id, cid)
            return {
                "cid": cid,
                "file_id": file_id,     # FIX #2: simpan untuk dekripsi
                "nonce_b64": nonce_b64,
                "auth_tag_b64": tag_b64,
                "storage": "ipfs",
                "filename": filename,
                "size": len(file_bytes),
            }
        except Exception as e:
            logger.error("IPFS upload failed: %s", e)

    # Fallback: simpan ke media/ dengan UUID sebagai nama file
    fallback_path = os.path.join(settings.MEDIA_ROOT, 'attachments', channel_id)
    os.makedirs(fallback_path, exist_ok=True)

    # FIX #3: gunakan file_id (UUID) sebagai nama file — tidak ada collision
    filepath = os.path.join(fallback_path, file_id)
    with open(filepath, 'wb') as f:
        f.write(encrypted_bytes)

    logger.info("Local fallback upload: %s (file_id=%s)", filename, file_id)
    return {
        "cid": f"local:{file_id}",
        "file_id": file_id,
        "nonce_b64": nonce_b64,
        "auth_tag_b64": tag_b64,
        "storage": "local",
        "filename": filename,
        "size": len(file_bytes),
    }


def download_encrypted_file(
    cid: str,
    nonce_b64: str,
    auth_tag_b64: str,
    channel_id: str,
    file_id: str,       # FIX #2: file_id diperlukan untuk key derivation
) -> bytes:
    """
    Download dan decrypt file dari IPFS atau local storage.
    FIX #2: Butuh file_id untuk derive key yang benar.
    """
    channel_id = _validate_channel_id(channel_id)

    file_key = derive_message_key(
        settings.AES_MASTER_KEY,
        channel_id,
        f"file:{file_id}",   # FIX #2: konsisten dengan upload
    )

    if cid.startswith('local:'):
        stored_file_id = cid[6:]
        filepath = os.path.join(
            settings.MEDIA_ROOT, 'attachments', channel_id, stored_file_id
        )
        with open(filepath, 'rb') as f:
            encrypted_bytes = f.read()
    else:
        client = _get_ipfs_client()
        if not client:
            raise FileNotFoundError("IPFS unavailable and no local fallback")
        encrypted_bytes = client.cat(cid)

    ct_b64 = base64.b64encode(encrypted_bytes).decode()
    return aes_gcm_decrypt(file_key, ct_b64, nonce_b64, auth_tag_b64, aad=channel_id.encode())


def pin_to_ipfs(cid: str) -> bool:
    """Pin CID to prevent garbage collection."""
    client = _get_ipfs_client()
    if not client:
        return False
    try:
        client.pin.add(cid)
        return True
    except Exception as e:
        logger.error("IPFS pin failed: %s", e)
        return False
