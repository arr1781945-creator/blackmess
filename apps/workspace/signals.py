"""
apps/workspace/signals.py

FIX — create_default_channels: channel creation tidak pakai transaction.on_commit

Sebelumnya signal post_save langsung membuat channel di dalam handler.
Jika transaksi workspace.save() di-rollback setelah signal berjalan
(mis. karena constraint violation di langkah berikutnya), channel
sudah terbuat tapi workspace tidak ada → data orphan.

Fix: bungkus pembuatan channel dalam transaction.on_commit() sehingga
hanya berjalan jika transaksi workspace benar-benar commit ke DB.

FIX tambahan — UserPresence import tidak dipakai dihapus.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from .models import Workspace


@receiver(post_save, sender=Workspace)
def create_default_channels(sender, instance, created, **kwargs):
    """
    Buat channel default saat workspace baru dibuat.

    FIX: Pakai transaction.on_commit() agar channel hanya dibuat
    jika transaksi workspace sudah benar-benar commit. Tanpa ini,
    jika transaksi di-rollback setelah signal berjalan, channel
    orphan akan terbuat tanpa workspace yang valid.
    """
    if not created:
        return

    def _create_channels():
        # Import di dalam fungsi agar tidak circular saat module load
        from .models import Channel, ChannelMember

        default_channels = [
            {
                "name": "general",
                "slug": "general",
                "channel_type": "public",
                "purpose": "Company-wide announcements",
                "is_read_only": False,
            },
            {
                "name": "random",
                "slug": "random",
                "channel_type": "public",
                "purpose": "Non-work banter",
                "is_read_only": False,
            },
            {
                "name": "compliance",
                "slug": "compliance",
                "channel_type": "compliance",
                "purpose": "Regulatory notices (read-only)",
                "is_read_only": True,
            },
        ]

        for ch_data in default_channels:
            try:
                ch = Channel.objects.create(
                    workspace=instance,
                    created_by=instance.owner,
                    **ch_data,
                )
                ChannelMember.objects.create(
                    channel=ch,
                    user=instance.owner,
                    is_admin=True,
                )
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(
                    "Gagal buat default channel '%s' untuk workspace %s: %s",
                    ch_data["name"], instance.id, e,
                )

    # FIX: on_commit — hanya berjalan jika transaksi workspace commit
    transaction.on_commit(_create_channels)
