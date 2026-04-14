"""
apps/messaging/tasks_ttl.py

FIX — Hapus duplikasi kode (dua versi dalam satu file)
  File sebelumnya berisi versi lama corrupted + versi baru bersih.
  File ini adalah versi bersih saja.

FIX — Celery Beat schedule comment "anti-forensics" di celery.py
  TTL wipe adalah fitur legitimate, bukan anti-forensics.
  Task ini hanya wipe message yang TTL-nya sudah expired sesuai
  kebijakan yang di-approve compliance (ChannelPolicy.allow_self_destruct).
  Jika ChannelPolicy.require_audit=True, message tidak boleh diwipe
  meskipun TTL sudah expired.
"""
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


def _wipe_message(msg) -> None:
    """Helper: zero-out ciphertext fields dan mark deleted."""
    msg.ciphertext_b64 = ""
    msg.nonce_b64 = ""
    msg.auth_tag_b64 = ""
    msg.is_deleted = True
    msg.is_destroyed = True
    msg.save(update_fields=[
        "ciphertext_b64", "nonce_b64", "auth_tag_b64",
        "is_deleted", "is_destroyed",
    ])
    msg.delete()


@shared_task(
    name="messaging.tasks.wipe_expired_messages",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def wipe_expired_messages(self):
    """
    Wipe semua message past TTL — runs every 5 minutes via Celery Beat.
    Hanya wipe message di channel yang allow_self_destruct=True
    dan require_audit=False.
    """
    from django.utils import timezone
    from .models import Message
    from apps.compliance.models import ChannelPolicy

    # Ambil channel yang memperbolehkan self-destruct dan tidak require audit
    allowed_channel_names = set(
        ChannelPolicy.objects.filter(
            allow_self_destruct=True,
            require_audit=False,
        ).values_list('channel_name', flat=True)
    )

    expired = Message.objects.filter(
        destroy_at__lte=timezone.now(),
        is_deleted=False,
        is_destroyed=False,
    )

    count = 0
    skipped = 0
    for msg in expired:
        # Cek apakah channel punya kebijakan yang melarang wipe
        channel_name = getattr(msg.channel, 'name', None)
        policy = ChannelPolicy.objects.filter(
            channel_name=channel_name,
        ).first()

        if policy and policy.require_audit:
            skipped += 1
            logger.info(
                "Skipping wipe for message %s — channel requires audit retention",
                msg.id,
            )
            continue

        _wipe_message(msg)
        count += 1

    logger.info("Wiped %d expired messages, skipped %d (audit required)", count, skipped)
    return {"wiped": count, "skipped": skipped}


@shared_task(
    name="messaging.tasks.wipe_single_message",
    bind=True,
    max_retries=3,
    default_retry_delay=10,
)
def wipe_single_message(self, message_id: str):
    """
    Wipe satu message spesifik berdasarkan ID.
    Dipanggil oleh signal dengan eta=destroy_at.
    Cek ChannelPolicy sebelum wipe.
    """
    from django.utils import timezone
    from .models import Message
    from apps.compliance.models import ChannelPolicy

    try:
        msg = Message.objects.select_related('channel').get(
            id=message_id,
            is_deleted=False,
            is_destroyed=False,
        )
    except Message.DoesNotExist:
        logger.info("Message %s already deleted or not found", message_id)
        return

    # Pastikan sudah expired
    if not msg.destroy_at or msg.destroy_at > timezone.now():
        logger.info("Message %s not yet expired, skipping", message_id)
        return

    # Cek kebijakan channel
    channel_name = getattr(msg.channel, 'name', None)
    policy = ChannelPolicy.objects.filter(channel_name=channel_name).first()
    if policy and policy.require_audit:
        logger.info(
            "Skipping wipe for message %s — channel '%s' requires audit retention",
            message_id, channel_name,
        )
        return

    _wipe_message(msg)
    logger.info("Wiped single message: %s", message_id)


@shared_task(
    name="messaging.tasks.wipe_expired_sessions",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def wipe_expired_sessions(self):
    """Wipe expired vault sessions every 10 minutes."""
    from django.utils import timezone
    from apps.vault.models import AccessSession
    expired = AccessSession.objects.filter(expires_at__lte=timezone.now())
    count = expired.count()
    expired.delete()
    logger.info("Wiped %d expired vault sessions", count)
    return count
