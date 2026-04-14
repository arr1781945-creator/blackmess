"""
apps/users/tasks.py

LOW FIX #1 — generate_initial_pqc_keys: tidak ada retry logic
  Jika task gagal (OQS library tidak tersedia, DB error, dll), error
  hanya di-log dan user akan ada tanpa PQC keys. Tidak ada alert,
  tidak ada retry. Fix: tambah retry dengan exponential backoff.

LOW FIX #2 — Private key tidak di-wipe dari memory
  kyber_sk dan dilithium_sk di-generate tapi tidak dipakai (arsitektur
  PQ MFA menyimpan private key di client). Variabel Python tidak
  di-zero-out sebelum GC → private key material bisa bertahan di heap
  Celery worker. Fix: del eksplisit + komentar penjelasan arsitektur.
"""
import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    name="apps.users.tasks.generate_initial_pqc_keys",
    bind=True,
    max_retries=3,
    default_retry_delay=10,    # detik, akan di-double tiap retry (exponential)
    autoretry_for=(Exception,),
    retry_backoff=True,        # exponential: 10s, 20s, 40s
    retry_backoff_max=120,     # maksimum 2 menit antar retry
    retry_jitter=True,         # tambah random jitter agar tidak thundering herd
)
def generate_initial_pqc_keys(self, user_id: str):
    """
    Generate Kyber-1024 + Dilithium3 (ML-DSA-65) keypair untuk user baru.

    Arsitektur PQC:
    - Public key disimpan di server (DB + user.pqc_public_key_*)
    - Private key TIDAK disimpan di server — dikembalikan ke client sekali saja
      via PQMFARegisterView dan harus disimpan aman oleh user
    - Task ini hanya generate dan simpan public key

    FIX #1: Retry otomatis hingga 3x dengan exponential backoff jika gagal.
    FIX #2: Private key di-del eksplisit setelah public key disimpan.
    """
    from apps.users.models import BankUser, UserPublicKey
    from apps.users.utils_pqc import (
        generate_kyber_keypair,
        generate_dilithium_keypair,
        compute_key_fingerprint,
        OQS_AVAILABLE,
    )

    if not OQS_AVAILABLE:
        logger.error(
            "PQC key gen gagal untuk user %s: liboqs tidak tersedia di server ini. "
            "Install liboqs atau jalankan di server dengan PQC support.",
            user_id,
        )
        # Tidak retry jika library tidak ada — tidak akan berhasil
        return {"status": "skipped", "reason": "oqs_unavailable", "user_id": user_id}

    try:
        user = BankUser.objects.get(id=user_id)
    except BankUser.DoesNotExist:
        logger.error("PQC key gen: user %s tidak ditemukan", user_id)
        return {"status": "error", "reason": "user_not_found", "user_id": user_id}

    # Generate keypairs
    kyber_pk, kyber_sk = generate_kyber_keypair()
    dilithium_pk, dilithium_sk = generate_dilithium_keypair()

    try:
        # Simpan hanya public key ke DB
        UserPublicKey.objects.get_or_create(
            user=user,
            key_type="kyber_1024",
            defaults={
                "public_key_b64": kyber_pk,
                "fingerprint": compute_key_fingerprint(kyber_pk),
            },
        )
        UserPublicKey.objects.get_or_create(
            user=user,
            key_type="ml_dsa_65",
            defaults={
                "public_key_b64": dilithium_pk,
                "fingerprint": compute_key_fingerprint(dilithium_pk),
            },
        )

        user.pqc_public_key_kyber = kyber_pk
        user.pqc_public_key_dilithium = dilithium_pk
        user.save(update_fields=["pqc_public_key_kyber", "pqc_public_key_dilithium"])

        logger.info("PQC keys generated for user %s", user_id)
        return {"status": "success", "user_id": user_id}

    finally:
        # FIX #2: Del private key dari memory sesegera mungkin.
        # Python GC tidak menjamin kapan memory di-reclaim, tapi del
        # setidaknya menghapus referensi sehingga GC bisa collect lebih cepat.
        # Untuk zero-wipe yang benar, gunakan library seperti `pyca/cryptography`
        # yang mendukung secure memory handling di level C.
        del kyber_sk
        del dilithium_sk
