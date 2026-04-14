"""
core/celery.py — Celery app for async tasks (TTL self-destruct, audit jobs)

FIX — Comment "anti-forensics wipe pass" dihapus
  TTL wipe adalah fitur legitimate sesuai kebijakan retensi yang disetujui
  compliance. Bukan "anti-forensics". Task juga sudah diupdate di tasks_ttl.py
  untuk menghormati ChannelPolicy.require_audit sebelum wipe.
"""
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("blackmess")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

from celery.schedules import crontab  # noqa: E402

app.conf.beat_schedule = {
    # Wipe message yang TTL-nya sudah expired
    # (hanya channel dengan allow_self_destruct=True dan require_audit=False)
    "ttl-message-wipe": {
        "task": "messaging.tasks.wipe_expired_messages",
        "schedule": crontab(minute="*/5"),          # setiap 5 menit
    },
    # Cleanup vault sessions yang expired
    "session-cleanup": {
        "task": "messaging.tasks.wipe_expired_sessions",
        "schedule": crontab(minute="*/10"),         # setiap 10 menit
    },
    # Generate daily audit report jam 3 pagi UTC
    "audit-report-daily": {
        "task": "apps.compliance.tasks_audit.generate_daily_report",
        "schedule": crontab(hour=3, minute=0),
    },
}
