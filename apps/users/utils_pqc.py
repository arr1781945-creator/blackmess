"""
apps/users/utils_pqc.py
Post-Quantum Cryptography — Kyber-1024 (KEM) + ML-DSA-65 (Signature).
ML-DSA-65 = Dilithium3 versi baru, standar NIST FIPS 204.
"""
import base64
import hashlib
import logging

logger = logging.getLogger(__name__)

try:
    import oqs
    OQS_AVAILABLE = True
    logger.info("liboqs loaded — PQC fully active")
except ImportError:
    OQS_AVAILABLE = False
    logger.warning("liboqs not available — PQC disabled")


def _require_oqs():
    if not OQS_AVAILABLE:
        raise NotImplementedError("liboqs not installed")


# ─── Kyber-1024 ──────────────────────────────────────────────────────────────

def generate_kyber_keypair() -> tuple[str, str]:
    _require_oqs()
    with oqs.KeyEncapsulation("ML-KEM-1024") as kem:
        pk = kem.generate_keypair()
        sk = kem.export_secret_key()
    return base64.b64encode(pk).decode(), base64.b64encode(sk).decode()


def kyber_encapsulate(pk_b64: str) -> tuple[str, bytes]:
    _require_oqs()
    pk = base64.b64decode(pk_b64)
    with oqs.KeyEncapsulation("ML-KEM-1024") as kem:
        ct, ss = kem.encap_secret(pk)
    return base64.b64encode(ct).decode(), ss


def kyber_decapsulate(sk_b64: str, ct_b64: str) -> bytes:
    _require_oqs()
    sk = base64.b64decode(sk_b64)
    ct = base64.b64decode(ct_b64)
    with oqs.KeyEncapsulation("ML-KEM-1024", sk) as kem:
        return kem.decap_secret(ct)


# ─── ML-DSA-65 (Dilithium3 NIST FIPS 204) ───────────────────────────────────

def generate_dilithium_keypair() -> tuple[str, str]:
    _require_oqs()
    with oqs.Signature("ML-DSA-65") as sig:
        pk = sig.generate_keypair()
        sk = sig.export_secret_key()
    return base64.b64encode(pk).decode(), base64.b64encode(sk).decode()


def dilithium_sign(sk_b64: str, message: bytes) -> str:
    _require_oqs()
    sk = base64.b64decode(sk_b64)
    with oqs.Signature("ML-DSA-65", sk) as sig:
        signature = sig.sign(message)
    return base64.b64encode(signature).decode()


def dilithium_verify(pk_b64: str, message: bytes, sig_b64: str) -> bool:
    _require_oqs()
    pk = base64.b64decode(pk_b64)
    signature = base64.b64decode(sig_b64)
    with oqs.Signature("ML-DSA-65") as sig:
        return sig.verify(message, signature, pk)


# ─── Hybrid KEM (Kyber-1024 + X25519) ───────────────────────────────────────

def hybrid_encapsulate(kyber_pk_b64: str, x25519_pk_bytes: bytes) -> dict:
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

    kyber_ct_b64, kyber_ss = kyber_encapsulate(kyber_pk_b64)
    ephemeral = X25519PrivateKey.generate()
    x25519_pk = X25519PublicKey.from_public_bytes(x25519_pk_bytes)
    x25519_ss = ephemeral.exchange(x25519_pk)
    x25519_pub = ephemeral.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)

    combined = HKDF(
        algorithm=hashes.SHA512(), length=32, salt=None,
        info=b"blackmess-hybrid-kem-v1"
    ).derive(kyber_ss + x25519_ss)

    return {
        "kyber_ciphertext_b64": kyber_ct_b64,
        "x25519_ephemeral_pub_b64": base64.b64encode(x25519_pub).decode(),
        "combined_secret_bytes": combined,
    }


def compute_key_fingerprint(pk_b64: str) -> str:
    return hashlib.sha256(base64.b64decode(pk_b64)).hexdigest()
