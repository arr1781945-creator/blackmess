"""
apps/messaging/models.py
Messaging domain — 11 tables.

Tables:
  1.  Message         — Core message with E2EE ciphertext
  2.  MessageEdit     — Full edit history
  3.  Thread          — Threaded reply context
  4.  Reaction        — Emoji reactions to messages
  5.  Attachment      — File attachments (IPFS-backed)
  6.  MessageRead     — Read receipts per user
  7.  Mention         — @mentions extracted from messages
  8.  MessageSearch   — FTS search index (encrypted metadata only)
  9.  TTLPolicy       — Per-message/channel TTL rules
  10. MessageBookmark — User-saved messages
  11. WebhookEndpoint — Incoming webhook integrations
"""

import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey(
        "workspace.Channel", on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="sent_messages"
    )
    thread = models.ForeignKey(
        "Thread", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )

    # E2EE content — plaintext NEVER stored
    ciphertext_b64 = models.TextField(help_text="AES-256-GCM encrypted message body")
    nonce_b64 = models.CharField(max_length=32, help_text="12-byte GCM nonce, base64")
    auth_tag_b64 = models.CharField(max_length=32, help_text="16-byte GCM auth tag, base64")

    # Hybrid KEM key encapsulation per sender
    kyber_ciphertext_b64 = models.TextField(blank=True, help_text="Kyber-1024 encapsulated symmetric key")
    dilithium_signature_b64 = models.TextField(blank=True, help_text="Dilithium3 message signature")

    # Metadata (NOT encrypted — needed for routing, but minimised)
    message_type = models.CharField(
        max_length=16, default="text",
        choices=[("text", "Text"), ("file", "File"), ("system", "System"), ("call", "Call Event")]
    )
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Self-destruct / TTL
    ttl_seconds = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Seconds until hard-delete. Null = use channel/workspace policy."
    )
    destroy_at = models.DateTimeField(null=True, blank=True, db_index=True)
    is_destroyed = models.BooleanField(default=False, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "messaging_message"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["channel", "created_at"]),
            models.Index(fields=["channel", "is_deleted", "is_destroyed"]),
            models.Index(fields=["destroy_at"]),
            models.Index(fields=["sender", "created_at"]),
        ]

    def set_ttl(self, seconds: int):
        self.ttl_seconds = seconds
        self.destroy_at = timezone.now() + timezone.timedelta(seconds=seconds)

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        # Overwrite ciphertext with zeros — anti-forensics
        self.ciphertext_b64 = ""
        self.nonce_b64 = ""
        self.auth_tag_b64 = ""
        self.save(update_fields=["is_deleted", "deleted_at", "ciphertext_b64", "nonce_b64", "auth_tag_b64"])


class MessageEdit(models.Model):
    """Immutable audit trail of all edits."""
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="edits")
    previous_ciphertext_b64 = models.TextField()
    previous_nonce_b64 = models.CharField(max_length=32)
    edited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    edited_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "messaging_message_edit"
        ordering = ["-edited_at"]


class Thread(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey("workspace.Channel", on_delete=models.CASCADE, related_name="threads")
    root_message = models.OneToOneField(
        Message, on_delete=models.CASCADE, related_name="thread_root", null=True
    )
    reply_count = models.PositiveIntegerField(default=0)
    last_reply_at = models.DateTimeField(null=True, blank=True)
    participant_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "messaging_thread"
        ordering = ["-last_reply_at"]


class Reaction(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="reactions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reactions")
    emoji_code = models.CharField(max_length=64, help_text="Unicode or :custom_name:")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "messaging_reaction"
        unique_together = [("message", "user", "emoji_code")]


class Attachment(models.Model):
    STORAGE_BACKEND_CHOICES = [("ipfs", "IPFS"), ("s3", "S3 Vault"), ("encrypted_blob", "Encrypted Blob Store")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="attachments")
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    original_filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=128)
    size_bytes = models.PositiveBigIntegerField()
    storage_backend = models.CharField(max_length=16, choices=STORAGE_BACKEND_CHOICES, default="ipfs")
    ipfs_cid = models.CharField(max_length=128, blank=True, db_index=True)
    encryption_key_b64 = models.TextField(blank=True, help_text="Per-file AES key, itself encrypted with user's Kyber key")
    checksum_sha256 = models.CharField(max_length=64)
    is_deleted = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "messaging_attachment"


class MessageRead(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="reads")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="message_reads")
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "messaging_message_read"
        unique_together = [("message", "user")]
        indexes = [models.Index(fields=["user", "read_at"])]


class Mention(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="mentions")
    mentioned_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mentions")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "messaging_mention"
        indexes = [models.Index(fields=["mentioned_user", "is_read"])]


class TTLPolicy(models.Model):
    """Configurable TTL rules at channel or workspace level."""
    SCOPE_CHOICES = [("workspace", "Workspace"), ("channel", "Channel"), ("message", "Message")]
    scope = models.CharField(max_length=16, choices=SCOPE_CHOICES)
    scope_id = models.UUIDField(db_index=True)
    ttl_seconds = models.PositiveIntegerField()
    applies_to_type = models.CharField(max_length=16, default="all", choices=[("all", "All"), ("text", "Text Only"), ("file", "Files Only")])
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "messaging_ttl_policy"


class MessageBookmark(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookmarks")
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="bookmarks")
    note = models.CharField(max_length=256, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "messaging_bookmark"
        unique_together = [("user", "message")]


class WebhookEndpoint(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey("workspace.Channel", on_delete=models.CASCADE, related_name="webhooks")
    name = models.CharField(max_length=64)
    token_hash = models.CharField(max_length=256, unique=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_triggered = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "messaging_webhook"


# ─── Messaging Expansion Tables ──────────────────────────────────────────────

class Poll(models.Model):
    """Voting/poll in channel."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey(r'workspace.Channel', on_delete=models.CASCADE, related_name='polls')
    created_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    question = models.TextField()
    options = models.JSONField(default=list)
    is_anonymous = models.BooleanField(default=False)
    is_multiple = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'messaging_poll'


class PollVote(models.Model):
    """Poll vote results."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name=r'poll_votes')
    user = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    option_index = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'messaging_channel_poll_vote'
        unique_together = [r'poll', 'user', 'option_index']


class Reminder(models.Model):
    """Message reminders."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE, related_name='reminders')
    message = models.ForeignKey(r'Message', on_delete=models.CASCADE, related_name='reminders')
    remind_at = models.DateTimeField()
    is_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'messaging_reminder'


class ScheduledMessage(models.Model):
    """Scheduled messages."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey(r'workspace.Channel', on_delete=models.CASCADE)
    sender = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    ciphertext_b64 = models.TextField()
    nonce_b64 = models.TextField()
    auth_tag_b64 = models.TextField()
    scheduled_at = models.DateTimeField()
    is_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'messaging_scheduled_message'


class MessageTemplate(models.Model):
    """Reusable message templates."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(r'workspace.Workspace', on_delete=models.CASCADE)
    created_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    content = models.TextField()
    is_shared = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'messaging_template'


class MessageForward(models.Model):
    """Forward message tracking."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    original_message = models.ForeignKey(r'Message', on_delete=models.CASCADE, related_name='forwards')
    forwarded_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    target_channel = models.ForeignKey(r'workspace.Channel', on_delete=models.CASCADE)
    forwarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'messaging_forward'


class BotCommand(models.Model):
    """Bot commands."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(r'workspace.Workspace', on_delete=models.CASCADE)
    command = models.CharField(max_length=50)
    description = models.TextField()
    handler_url = models.URLField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'messaging_bot_command'


class MessageSearchIndex(models.Model):
    """Full-text search index."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.OneToOneField(r'Message', on_delete=models.CASCADE, related_name='search_index')
    channel = models.ForeignKey(r'workspace.Channel', on_delete=models.CASCADE)
    search_hash = models.CharField(max_length=64)
    indexed_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = r'messaging_search_index'


class SecureVoiceMessage(models.Model):
    """Encrypted voice messages."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey(r'workspace.Channel', on_delete=models.CASCADE, related_name='voice_messages')
    sender = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    audio_cid = models.TextField()
    ciphertext_b64 = models.TextField()
    nonce_b64 = models.TextField()
    auth_tag_b64 = models.TextField()
    duration_seconds = models.PositiveIntegerField(default=0)
    is_transcribed = models.BooleanField(default=False)
    transcript_encrypted_b64 = models.TextField(blank=True)
    destroy_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'messaging_voice_message'


class SecureVideoCall(models.Model):
    """E2EE video call sessions."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey(r'workspace.Channel', on_delete=models.CASCADE, related_name='video_calls')
    initiated_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    participants = models.ManyToManyField(r'users.BankUser', related_name='video_calls')
    session_key_b64 = models.TextField()
    dtls_fingerprint = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=[
        (r'ringing','Ringing'), ('active','Active'),
        (r'ended','Ended'), ('missed','Missed'),
    ], default=r'ringing')
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    recording_cid = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'messaging_video_call'


class AnonymousReport(models.Model):
    """Anonymous whistleblower reporting."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_token = models.CharField(max_length=64, unique=True)
    category = models.CharField(max_length=50, choices=[
        (r'fraud','Fraud'),
        (r'misconduct','Misconduct'),
        (r'aml','AML Violation'),
        (r'data_breach','Data Breach'),
        (r'bribery','Bribery'),
        (r'other','Other'),
    ])
    ciphertext_b64 = models.TextField()
    nonce_b64 = models.TextField()
    auth_tag_b64 = models.TextField()
    attachments_cid = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[
        (r'received','Received'), ('investigating','Investigating'),
        (r'resolved','Resolved'), ('dismissed','Dismissed'),
    ], default=r'received')
    assigned_to = models.ForeignKey(r'users.BankUser', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = r'messaging_anonymous_report'


class ChannelRetentionPolicy(models.Model):
    """Per-channel message retention policy."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.OneToOneField(r'workspace.Channel', on_delete=models.CASCADE, related_name='retention_policy')
    retention_days = models.PositiveIntegerField(default=365)
    auto_wipe = models.BooleanField(default=False)
    legal_hold = models.BooleanField(default=False)
    legal_hold_reason = models.TextField(blank=True)
    legal_hold_by = models.ForeignKey(r'users.BankUser', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = r'messaging_retention_policy'


class TradingCommunication(models.Model):
    """MiFID II compliant trading communications."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.OneToOneField(r'Message', on_delete=models.CASCADE, related_name='trading_comm')
    instrument = models.CharField(max_length=50, blank=True)
    isin = models.CharField(max_length=12, blank=True)
    direction = models.CharField(max_length=10, choices=[(r'buy','Buy'),('sell','Sell'),('hold','Hold')], blank=True)
    quantity = models.DecimalField(max_digits=20, decimal_places=8, null=True)
    price = models.DecimalField(max_digits=20, decimal_places=8, null=True)
    currency = models.CharField(max_length=3, blank=True)
    is_pre_trade = models.BooleanField(default=False)
    is_post_trade = models.BooleanField(default=False)
    mifid_reported = models.BooleanField(default=False)
    reported_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'messaging_trading_comm'


class SecureConferenceRoom(models.Model):
    """Secure virtual conference rooms."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(r'workspace.Workspace', on_delete=models.CASCADE, related_name='conference_rooms')
    name = models.CharField(max_length=100)
    room_type = models.CharField(max_length=50, choices=[
        (r'board','Board Meeting'),
        (r'trading','Trading Floor'),
        (r'compliance','Compliance Review'),
        (r'deal','Deal Discussion'),
        (r'crisis','Crisis Management'),
        (r'general','General'),
    ])
    session_key_b64 = models.TextField(blank=True)
    max_participants = models.PositiveIntegerField(default=50)
    is_recorded = models.BooleanField(default=False)
    recording_cid = models.TextField(blank=True)
    requires_mfa = models.BooleanField(default=True)
    min_clearance = models.PositiveSmallIntegerField(default=1)
    is_active = models.BooleanField(default=False)
    started_by = models.ForeignKey(r'users.BankUser', on_delete=models.SET_NULL, null=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'messaging_conference_room'


class ConferenceParticipant(models.Model):
    """Conference room participants."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(SecureConferenceRoom, on_delete=models.CASCADE, related_name=r'participants')
    user = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=[
        (r'host','Host'), ('presenter','Presenter'),
        (r'participant','Participant'), ('observer','Observer'),
    ], default=r'participant')
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    is_muted = models.BooleanField(default=False)
    is_video_on = models.BooleanField(default=False)

    class Meta:
        db_table = r'messaging_conference_participant'
        unique_together = [r'room', 'user']


class MessageTranslation(models.Model):
    """Multi-language message translation."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(r'Message', on_delete=models.CASCADE, related_name='translations')
    language = models.CharField(max_length=10)
    translated_ciphertext_b64 = models.TextField()
    nonce_b64 = models.TextField()
    auth_tag_b64 = models.TextField()
    translated_by = models.CharField(max_length=50, default=r'deepl')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'messaging_translation'
        unique_together = [r'message', 'language']


class ChatbotSession(models.Model):
    """AI chatbot sessions for banking assistance."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE, related_name='chatbot_sessions')
    channel = models.ForeignKey(r'workspace.Channel', on_delete=models.CASCADE, null=True)
    bot_type = models.CharField(max_length=50, choices=[
        (r'compliance_assistant','Compliance Assistant'),
        (r'trading_assistant','Trading Assistant'),
        (r'kyc_assistant','KYC Assistant'),
        (r'general','General Assistant'),
    ])
    context = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = r'messaging_chatbot_session'


class NotificationQueue(models.Model):
    """Notification delivery queue."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE, related_name='notification_queue')
    notification_type = models.CharField(max_length=50, choices=[
        (r'push','Push'),
        (r'email','Email'),
        (r'sms','SMS'),
        (r'in_app','In-App'),
    ])
    title = models.CharField(max_length=255)
    body = models.TextField()
    data = models.JSONField(default=dict)
    priority = models.CharField(max_length=20, choices=[
        (r'low','Low'), ('normal','Normal'),
        (r'high','High'), ('critical','Critical'),
    ], default=r'normal')
    status = models.CharField(max_length=20, choices=[
        (r'pending','Pending'), ('sent','Sent'),
        (r'failed','Failed'), ('cancelled','Cancelled'),
    ], default=r'pending')
    retry_count = models.PositiveSmallIntegerField(default=0)
    scheduled_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = r'messaging_notification_queue'


class SecureFileRoom(models.Model):
    """Secure file sharing room for deals."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(r'workspace.Workspace', on_delete=models.CASCADE, related_name='file_rooms')
    name = models.CharField(max_length=100)
    room_type = models.CharField(max_length=50, choices=[
        (r'due_diligence','Due Diligence'),
        (r'legal','Legal Documents'),
        (r'financial','Financial Reports'),
        (r'regulatory','Regulatory Filing'),
        (r'board','Board Documents'),
    ])
    participants = models.ManyToManyField(r'users.BankUser', related_name='file_rooms')
    watermark_enabled = models.BooleanField(default=True)
    download_enabled = models.BooleanField(default=False)
    print_enabled = models.BooleanField(default=False)
    screenshot_blocked = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'messaging_file_room'


class FileRoomDocument(models.Model):
    """Documents inside secure file room."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(SecureFileRoom, on_delete=models.CASCADE, related_name=r'documents')
    filename = models.CharField(max_length=255)
    file_cid = models.TextField()
    ciphertext_b64 = models.TextField()
    nonce_b64 = models.TextField()
    auth_tag_b64 = models.TextField()
    file_size = models.BigIntegerField(default=0)
    mime_type = models.CharField(max_length=100, blank=True)
    version = models.PositiveIntegerField(default=1)
    uploaded_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'messaging_file_room_document'


class DocumentAccessLog(models.Model):
    """Track who accessed which document."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(FileRoomDocument, on_delete=models.CASCADE, related_name=r'access_logs')
    user = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=[
        (r'view','View'), ('download','Download'),
        (r'print','Print'), ('share','Share'),
    ])
    ip_address = models.GenericIPAddressField(null=True)
    device_fingerprint = models.CharField(max_length=255, blank=True)
    watermark_id = models.CharField(max_length=64, blank=True)
    accessed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'messaging_document_access_log'


class PinnedResource(models.Model):
    """Pinned resources per channel."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey(r'workspace.Channel', on_delete=models.CASCADE, related_name='pinned_resources')
    resource_type = models.CharField(max_length=50, choices=[
        (r'message','Message'), ('document','Document'),
        (r'link','Link'), ('contact','Contact'),
        (r'deal','Deal'), ('report','Report'),
    ])
    resource_id = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    pinned_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    pinned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'messaging_pinned_resource'


class StatusUpdate(models.Model):
    """Team status updates."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE, related_name='status_updates')
    workspace = models.ForeignKey(r'workspace.Workspace', on_delete=models.CASCADE)
    content_encrypted_b64 = models.TextField()
    nonce_b64 = models.TextField()
    auth_tag_b64 = models.TextField()
    mood = models.CharField(max_length=20, choices=[
        (r'great','Great'),
        (r'good','Good'),
        (r'okay','Okay'),
        (r'stressed','Stressed'),
        (r'blocked','Blocked'),
    ], default=r'good')
    blockers = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'messaging_status_update'


class WaterCooler(models.Model):
    """Virtual water cooler conversations."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(r'workspace.Workspace', on_delete=models.CASCADE)
    topic = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=[
        (r'fun','Fun & Games'),
        (r'news','News & Trends'),
        (r'learning','Learning'),
        (r'health','Health & Wellness'),
        (r'random','Random'),
    ])
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'messaging_water_cooler'


class IceBreaker(models.Model):
    """Ice breaker questions for team building."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(r'workspace.Workspace', on_delete=models.CASCADE)
    question = models.TextField()
    category = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'messaging_ice_breaker'


class IceBreakerResponse(models.Model):
    """Responses to ice breaker questions."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(IceBreaker, on_delete=models.CASCADE, related_name=r'responses')
    user = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    response_encrypted_b64 = models.TextField()
    nonce_b64 = models.TextField()
    auth_tag_b64 = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'messaging_ice_breaker_response'
        unique_together = [r'question', 'user']


class WorkspacePoll(models.Model):
    """Workspace polls."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(r'workspace.Workspace', on_delete=models.CASCADE)
    channel = models.ForeignKey(r'workspace.Channel', on_delete=models.CASCADE, null=True)
    question = models.TextField()
    options = models.JSONField(default=list)
    is_anonymous = models.BooleanField(default=False)
    is_multiple = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'messaging_workspace_poll'


class WorkspacePollVote(models.Model):
    """Votes on workspace polls."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    poll = models.ForeignKey(WorkspacePoll, on_delete=models.CASCADE, related_name=r'votes')
    user = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    option_index = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'messaging_workspace_poll_vote'
        unique_together = [r'poll', 'user', 'option_index']


class MessageThread(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey(r'workspace.Channel', on_delete=models.CASCADE, related_name='message_threads')
    root_message = models.OneToOneField(r'Message', on_delete=models.CASCADE, related_name='message_thread_root')
    reply_count = models.PositiveIntegerField(default=0)
    last_reply_at = models.DateTimeField(null=True)
    participants = models.ManyToManyField(r'users.BankUser', related_name='thread_participations', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'messaging_message_thread'

class MessageDraft(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE, related_name='drafts')
    channel = models.ForeignKey(r'workspace.Channel', on_delete=models.CASCADE, null=True)
    content_encrypted_b64 = models.TextField()
    nonce_b64 = models.TextField()
    auth_tag_b64 = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: db_table = r'messaging_draft'

class SharedLink(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(r'Message', on_delete=models.CASCADE, related_name='shared_links')
    url = models.URLField()
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'messaging_shared_link'

class UserTypingStatus(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    channel = models.ForeignKey(r'workspace.Channel', on_delete=models.CASCADE)
    is_typing = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = r'messaging_typing_status'
        unique_together = [r'user', 'channel']

class MessageStar(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE, related_name='starred_messages')
    message = models.ForeignKey(r'Message', on_delete=models.CASCADE, related_name='stars')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = r'messaging_star'
        unique_together = [r'user', 'message']

class ChannelTopic(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey(r'workspace.Channel', on_delete=models.CASCADE, related_name='topics')
    topic = models.CharField(max_length=255)
    set_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'messaging_channel_topic'

class DirectMessageChannel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(r'workspace.Workspace', on_delete=models.CASCADE)
    user1 = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE, related_name='dm_as_user1')
    user2 = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE, related_name='dm_as_user2')
    is_blocked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = r'messaging_dm_channel'
        unique_together = [r'workspace', 'user1', 'user2']

class GroupDMChannel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(r'workspace.Workspace', on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=True)
    members = models.ManyToManyField(r'users.BankUser', related_name='group_dms')
    created_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'messaging_group_dm'

class AppIntegrationMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey(r'workspace.Channel', on_delete=models.CASCADE)
    app_name = models.CharField(max_length=100)
    app_icon_url = models.URLField(blank=True)
    content = models.JSONField(default=dict)
    is_interactive = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'messaging_app_message'

class MessageReminder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE, related_name='message_reminders')
    message = models.ForeignKey(r'Message', on_delete=models.CASCADE)
    remind_at = models.DateTimeField()
    is_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'messaging_message_reminder'


class EmojiReaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(r'Message', on_delete=models.CASCADE, related_name='emoji_reactions')
    user = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    emoji = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = r'messaging_emoji_reaction'
        unique_together = [r'message', 'user', 'emoji']

class CustomEmoji(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(r'workspace.Workspace', on_delete=models.CASCADE, related_name='custom_emojis_set')
    name = models.CharField(max_length=50)
    image_cid = models.TextField()
    created_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = r'messaging_custom_emoji'
        unique_together = [r'workspace', 'name']

class ChannelInvite(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey(r'workspace.Channel', on_delete=models.CASCADE, related_name='channel_invites')
    invited_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE, related_name='channel_invites_sent')
    invited_user = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE, related_name='channel_invites_received')
    status = models.CharField(max_length=20, default=r'pending')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'messaging_channel_invite'

class MessageVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(r'Message', on_delete=models.CASCADE, related_name='versions')
    ciphertext_b64 = models.TextField()
    nonce_b64 = models.TextField()
    auth_tag_b64 = models.TextField()
    version_number = models.PositiveIntegerField(default=1)
    edited_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'messaging_message_version'

class ReadReceipt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(r'Message', on_delete=models.CASCADE, related_name='read_receipts')
    user = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = r'messaging_read_receipt'
        unique_together = [r'message', 'user']

class ChannelPermission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey(r'workspace.Channel', on_delete=models.CASCADE, related_name='permissions')
    user = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    can_post = models.BooleanField(default=True)
    can_upload = models.BooleanField(default=True)
    can_invite = models.BooleanField(default=False)
    is_moderator = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = r'messaging_channel_permission'
        unique_together = [r'channel', 'user']

class BroadcastMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(r'workspace.Workspace', on_delete=models.CASCADE, related_name='broadcasts')
    title = models.CharField(max_length=255)
    ciphertext_b64 = models.TextField()
    nonce_b64 = models.TextField()
    auth_tag_b64 = models.TextField()
    target_channels = models.ManyToManyField(r'workspace.Channel', related_name='broadcasts', blank=True)
    sent_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    sent_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'messaging_broadcast'

class MessageFlag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(r'Message', on_delete=models.CASCADE, related_name='flags')
    flagged_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    reason = models.CharField(max_length=50, choices=[(r'spam','Spam'),('harassment','Harassment'),('inappropriate','Inappropriate'),('misinformation','Misinformation'),('other','Other')])
    status = models.CharField(max_length=20, default=r'pending')
    reviewed_by = models.ForeignKey(r'users.BankUser', on_delete=models.SET_NULL, null=True, related_name='reviewed_flags')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'messaging_flag'

class AutoResponse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(r'workspace.Workspace', on_delete=models.CASCADE, related_name='auto_responses')
    trigger_keyword = models.CharField(max_length=100)
    response = models.TextField()
    is_case_sensitive = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'messaging_auto_response'
