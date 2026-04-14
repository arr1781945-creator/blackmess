"""
apps/messaging/signals.py

FIX — update_channel_last_activity: tidak pakai transaction.on_commit
  Jika Message.save() di-rollback setelah signal berjalan,
  channel.last_activity sudah terupdate ke waktu message yang tidak jadi ada.
  Fix: bungkus dalam transaction.on_commit().

FIX — schedule_ttl_if_set: sama, bungkus dalam on_commit
  Task Celery tidak boleh di-dispatch sebelum record benar-benar commit,
  karena task bisa berjalan sebelum record tersedia di DB.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from .models import Message


@receiver(post_save, sender=Message)
def schedule_ttl_if_set(sender, instance, created, **kwargs):
    """
    Dispatch Celery task untuk wipe message saat destroy_at tercapai.
    FIX: on_commit — task hanya di-dispatch setelah message commit ke DB.
    """
    if not created or not instance.destroy_at:
        return

    def _dispatch():
        from .tasks_ttl import wipe_single_message
        wipe_single_message.apply_async(
            args=[str(instance.id)],
            eta=instance.destroy_at,
        )

    transaction.on_commit(_dispatch)


@receiver(post_save, sender=Message)
def update_channel_last_activity(sender, instance, created, **kwargs):
    """
    Update last_activity channel saat ada message baru.
    FIX: on_commit — channel hanya diupdate jika message benar-benar commit.
    """
    if not created:
        return

    channel_id = instance.channel_id
    created_at = instance.created_at

    def _update():
        from apps.workspace.models import Channel
        Channel.objects.filter(pk=channel_id).update(last_activity=created_at)

    transaction.on_commit(_update)
