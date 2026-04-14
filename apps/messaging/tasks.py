"""
apps/messaging/tasks.py
FIXED: C1 - field self_destruct_at → destroy_at, content/file_cid → ciphertext fields
"""
from celery import shared_task
from django.utils import timezone


@shared_task
def delete_expired_messages():
    from apps.messaging.models import Message
    expired = Message.objects.filter(
        destroy_at__isnull=False,
        destroy_at__lte=timezone.now(),
        is_deleted=False
    )
    count = expired.count()
    for msg in expired:
        msg.ciphertext_b64 = ""
        msg.nonce_b64 = ""
        msg.auth_tag_b64 = ""
        msg.is_deleted = True
        msg.save(update_fields=["ciphertext_b64", "nonce_b64", "auth_tag_b64", "is_deleted"])
        msg.delete()
    return f"Deleted {count} expired messages"


@shared_task
def schedule_message_deletion(message_id: str, seconds: int):
    from apps.messaging.models import Message
    import datetime
    try:
        msg = Message.objects.get(id=message_id)
        msg.destroy_at = timezone.now() + datetime.timedelta(seconds=seconds)
        msg.save(update_fields=["destroy_at"])
    except Message.DoesNotExist:
        pass
