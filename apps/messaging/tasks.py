from celery import shared_task
from django.utils import timezone

@shared_task
def delete_expired_messages():
    from apps.messaging.models import Message
    expired = Message.objects.filter(
        self_destruct_at__isnull=False,
        self_destruct_at__lte=timezone.now(),
        is_deleted=False
    )
    count = expired.count()
    expired.update(
        is_deleted=True,
        content='',
        file_cid=''
    )
    return f"Deleted {count} expired messages"

@shared_task
def schedule_message_deletion(message_id: str, seconds: int):
    from apps.messaging.models import Message
    from django.utils import timezone
    import datetime
    try:
        msg = Message.objects.get(id=message_id)
        msg.self_destruct_at = timezone.now() + datetime.timedelta(seconds=seconds)
        msg.save()
    except Message.DoesNotExist:
        pass
