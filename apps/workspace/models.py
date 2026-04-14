"""
apps/workspace/models.py
Workspace domain — 10 tables.

Tables:
  1.  Workspace          — Organisation-level container
  2.  WorkspaceMember    — User membership in workspace
  3.  Channel            — Slack-like channels (public/private/DM)
  4.  ChannelMember      — User membership in channel
  5.  ChannelPin         — Pinned messages per channel
  6.  WorkspaceInvite    — Pending workspace invitations
  7.  Emoji              — Custom workspace emoji
  8.  WorkspaceSettings  — Per-workspace configuration
  9.  WorkspaceAuditLog  — Workspace-level change log
  10. UserPresence       — Real-time presence states
"""

import uuid
from django.db import models
from django.conf import settings
from simple_history.models import HistoricalRecords


class Workspace(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=64, unique=True, db_index=True)
    description = models.TextField(blank=True)
    icon_ipfs_cid = models.CharField(max_length=128, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_workspaces"
    )
    compliance_region = models.CharField(
        max_length=16, default="APAC",
        choices=[("APAC", "Asia-Pacific"), ("EMEA", "Europe/Middle East/Africa"), ("AMER", "Americas")],
    )
    retention_days = models.PositiveIntegerField(default=365, help_text="Message retention period")
    is_e2ee_enforced = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        db_table = "workspace"
        ordering = ["name"]

    def __str__(self):
        return self.name


class WorkspaceMember(models.Model):
    STATUS_CHOICES = [("active", "Active"), ("suspended", "Suspended"), ("pending", "Pending Approval")]
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="workspace_memberships")
    role = models.ForeignKey("users.UserRole", on_delete=models.PROTECT)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending")
    joined_at = models.DateTimeField(auto_now_add=True)
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="sent_invitations")
    display_name_override = models.CharField(max_length=64, blank=True)
    notification_level = models.CharField(
        max_length=16, default="all",
        choices=[("all", "All"), ("mentions", "Mentions Only"), ("none", "None")],
    )

    class Meta:
        db_table = "workspace_member"
        unique_together = [("workspace", "user")]
        indexes = [models.Index(fields=["workspace", "status"])]


class Channel(models.Model):
    CHANNEL_TYPE_CHOICES = [
        ("public",  "Public"),
        ("private", "Private"),
        ("dm",      "Direct Message"),
        ("group_dm","Group DM"),
        ("announcement", "Announcement"),
        ("compliance",   "Compliance (Read-Only)"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="channels")
    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=80, db_index=True)
    description = models.TextField(blank=True)
    channel_type = models.CharField(max_length=16, choices=CHANNEL_TYPE_CHOICES, default="public")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    is_archived = models.BooleanField(default=False)
    is_read_only = models.BooleanField(default=False)
    message_retention_override = models.PositiveIntegerField(null=True, blank=True, help_text="Days. Null = workspace default")
    topic = models.CharField(max_length=256, blank=True)
    purpose = models.CharField(max_length=512, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "workspace_channel"
        unique_together = [("workspace", "slug")]
        indexes = [
            models.Index(fields=["workspace", "channel_type", "is_archived"]),
            models.Index(fields=["last_activity"]),
        ]

    def __str__(self):
        return f"#{self.name} ({self.workspace.slug})"


class ChannelMember(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="channel_memberships")
    joined_at = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)
    last_read_message = models.ForeignKey(
        "messaging.Message", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="+",
    )
    last_read_at = models.DateTimeField(null=True, blank=True)
    mention_count = models.PositiveIntegerField(default=0)
    is_muted = models.BooleanField(default=False)

    class Meta:
        db_table = "workspace_channel_member"
        unique_together = [("channel", "user")]
        indexes = [models.Index(fields=["user", "channel"])]


class ChannelPin(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name="pins")
    message = models.ForeignKey("messaging.Message", on_delete=models.CASCADE, related_name="pins")
    pinned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    pinned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "workspace_channel_pin"
        unique_together = [("channel", "message")]


class WorkspaceInvite(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="workspace_invites")
    email = models.EmailField()
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    role = models.ForeignKey("users.UserRole", on_delete=models.PROTECT)
    token_hash = models.CharField(max_length=256, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "workspace_invite"


class Emoji(models.Model):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="custom_emojis")
    name = models.CharField(max_length=32, db_index=True)
    ipfs_cid = models.CharField(max_length=128)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "workspace_emoji"
        unique_together = [("workspace", "name")]


class WorkspaceSettings(models.Model):
    workspace = models.OneToOneField(Workspace, on_delete=models.CASCADE, related_name="settings")
    allow_guest_access = models.BooleanField(default=False)
    require_mfa_for_all = models.BooleanField(default=True)
    allowed_file_types = models.JSONField(default=list, help_text=r'e.g. ["pdf","docx"]')
    max_file_size_mb = models.PositiveSmallIntegerField(default=25)
    enable_message_editing = models.BooleanField(default=True)
    editing_window_seconds = models.PositiveIntegerField(default=300, help_text="0 = disable editing after send")
    enable_link_preview = models.BooleanField(default=False, help_text="Disabled by default — security")
    screenshot_protection = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "workspace_settings"


class WorkspaceAuditLog(models.Model):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="audit_logs")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=64, db_index=True)
    target_type = models.CharField(max_length=32, blank=True)
    target_id = models.CharField(max_length=64, blank=True)
    detail = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "workspace_audit_log"
        ordering = ["-created_at"]


class UserPresence(models.Model):
    STATUS_CHOICES = [
        ("active",  "Active"),
        ("away",    "Away"),
        ("dnd",     "Do Not Disturb"),
        ("offline", "Offline"),
    ]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="presence")
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="presences")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="offline")
    status_text = models.CharField(max_length=100, blank=True)
    status_emoji = models.CharField(max_length=32, blank=True)
    last_seen = models.DateTimeField(auto_now=True)
    dnd_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "workspace_user_presence"


class BankingChannel(models.Model):
    """Dedicated banking communication channels."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'banking_channels')
    channel = models.OneToOneField(Channel, on_delete=models.CASCADE, related_name=r'banking_config')
    channel_category = models.CharField(max_length=50, choices=[
        (r'trading_desk','Trading Desk'),
        (r'risk_management','Risk Management'),
        (r'compliance','Compliance'),
        (r'treasury','Treasury'),
        (r'retail_banking','Retail Banking'),
        (r'corporate_banking','Corporate Banking'),
        (r'investment','Investment Banking'),
        (r'swift_ops','SWIFT Operations'),
    ])
    requires_compliance_review = models.BooleanField(default=False)
    max_message_ttl = models.PositiveIntegerField(default=86400)
    requires_mfa = models.BooleanField(default=True)
    min_clearance_level = models.PositiveSmallIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'workspace_banking_channel'


class DealRoom(models.Model):
    """Secure deal room for M&A, loans, investments."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'deal_rooms')
    name = models.CharField(max_length=255)
    deal_type = models.CharField(max_length=50, choices=[
        (r'ma','Mergers & Acquisitions'),
        (r'loan','Loan Syndication'),
        (r'ipo','IPO'),
        (r'bond','Bond Issuance'),
        (r'fx','FX Deal'),
    ])
    deal_value = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    currency = models.CharField(max_length=3, default=r'IDR')
    participants = models.ManyToManyField(r'users.BankUser', related_name='deal_rooms')
    nda_required = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    closes_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'workspace_deal_room'


class ComplianceCheckpoint(models.Model):
    """Compliance checkpoint sebelum pesan dikirim."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name=r'checkpoints')
    checkpoint_type = models.CharField(max_length=50, choices=[
        (r'pre_trade','Pre-Trade Check'),
        (r'post_trade','Post-Trade Check'),
        (r'communication','Communication Review'),
        (r'document','Document Approval'),
    ])
    is_required = models.BooleanField(default=True)
    approver_role = models.CharField(max_length=50, blank=True)
    sla_minutes = models.PositiveIntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'workspace_compliance_checkpoint'


class MessageApproval(models.Model):
    """Message approval workflow untuk compliance."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    checkpoint = models.ForeignKey(ComplianceCheckpoint, on_delete=models.CASCADE)
    message_hash = models.CharField(max_length=64)
    requested_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE, related_name='approval_requests')
    approved_by = models.ForeignKey(r'users.BankUser', on_delete=models.SET_NULL, null=True, related_name='approvals_given')
    status = models.CharField(max_length=20, choices=[
        (r'pending','Pending'), ('approved','Approved'),
        (r'rejected','Rejected'), ('expired','Expired'),
    ], default=r'pending')
    notes = models.TextField(blank=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = r'workspace_message_approval'


class TradingDesk(models.Model):
    """Trading desk configuration."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'trading_desks')
    name = models.CharField(max_length=100)
    desk_type = models.CharField(max_length=50, choices=[
        (r'equity','Equity'),
        (r'fixed_income','Fixed Income'),
        (r'fx','Foreign Exchange'),
        (r'derivatives','Derivatives'),
        (r'commodities','Commodities'),
        (r'crypto','Digital Assets'),
    ])
    head_trader = models.ForeignKey(r'users.BankUser', on_delete=models.SET_NULL, null=True, related_name='headed_desks')
    members = models.ManyToManyField(r'users.BankUser', related_name='trading_desks')
    risk_limit = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    daily_var_limit = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'workspace_trading_desk'


class WorkspaceIntegration(models.Model):
    """Third-party integrations — Bloomberg, Reuters, etc."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'integrations')
    integration_type = models.CharField(max_length=50, choices=[
        (r'bloomberg','Bloomberg Terminal'),
        (r'reuters','Reuters Eikon'),
        (r'swift','SWIFT Alliance'),
        (r'murex','Murex'),
        (r'calypso','Calypso'),
        (r'temenos','Temenos'),
        (r'fiserv','Fiserv'),
    ])
    api_endpoint = models.URLField(blank=True)
    encrypted_credentials_b64 = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    last_sync = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(r'users.BankUser', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'workspace_integration'


class EscalationMatrix(models.Model):
    """Escalation matrix for compliance/security issues."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'escalation_matrix')
    issue_type = models.CharField(max_length=50)
    severity = models.CharField(max_length=20, choices=[
        (r'low','Low'), ('medium','Medium'),
        (r'high','High'), ('critical','Critical'),
    ])
    level_1 = models.ForeignKey(r'users.BankUser', on_delete=models.SET_NULL, null=True, related_name='escalation_l1')
    level_2 = models.ForeignKey(r'users.BankUser', on_delete=models.SET_NULL, null=True, related_name='escalation_l2')
    level_3 = models.ForeignKey(r'users.BankUser', on_delete=models.SET_NULL, null=True, related_name='escalation_l3')
    sla_minutes_l1 = models.PositiveIntegerField(default=30)
    sla_minutes_l2 = models.PositiveIntegerField(default=60)
    sla_minutes_l3 = models.PositiveIntegerField(default=120)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'workspace_escalation_matrix'


class WorkspaceAnnouncement(models.Model):
    """Official workspace announcements."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'announcements')
    title = models.CharField(max_length=255)
    ciphertext_b64 = models.TextField()
    nonce_b64 = models.TextField()
    auth_tag_b64 = models.TextField()
    priority = models.CharField(max_length=20, choices=[
        (r'normal','Normal'), ('important','Important'),
        (r'urgent','Urgent'), ('critical','Critical'),
    ], default=r'normal')
    requires_acknowledgement = models.BooleanField(default=False)
    published_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    published_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = r'workspace_announcement'


class AnnouncementAcknowledgement(models.Model):
    """Track who acknowledged announcements."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    announcement = models.ForeignKey(WorkspaceAnnouncement, on_delete=models.CASCADE, related_name=r'acknowledgements')
    user = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    acknowledged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'workspace_announcement_ack'
        unique_together = [r'announcement', 'user']


class WorkflowTemplate(models.Model):
    """Reusable workflow templates."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'workflow_templates')
    name = models.CharField(max_length=100)
    workflow_type = models.CharField(max_length=50, choices=[
        (r'loan_approval','Loan Approval'),
        (r'account_opening','Account Opening'),
        (r'kyc_review','KYC Review'),
        (r'trade_approval','Trade Approval'),
        (r'complaint_handling','Complaint Handling'),
        (r'fraud_investigation','Fraud Investigation'),
        (r'contract_signing','Contract Signing'),
    ])
    steps = models.JSONField(default=list)
    sla_hours = models.PositiveIntegerField(default=24)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(r'users.BankUser', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'workspace_workflow_template'


class WorkflowInstance(models.Model):
    """Active workflow instances."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(WorkflowTemplate, on_delete=models.CASCADE, related_name=r'instances')
    reference_id = models.CharField(max_length=50)
    reference_type = models.CharField(max_length=50)
    current_step = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=[
        (r'active','Active'), ('completed','Completed'),
        (r'rejected','Rejected'), ('expired','Expired'),
        (r'on_hold','On Hold'),
    ], default=r'active')
    initiated_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE, related_name='initiated_workflows')
    assigned_to = models.ForeignKey(r'users.BankUser', on_delete=models.SET_NULL, null=True, related_name='assigned_workflows')
    due_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'workspace_workflow_instance'


class WorkflowStep(models.Model):
    """Individual workflow step records."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instance = models.ForeignKey(WorkflowInstance, on_delete=models.CASCADE, related_name=r'steps')
    step_number = models.PositiveIntegerField()
    step_name = models.CharField(max_length=100)
    action_taken = models.CharField(max_length=50, choices=[
        (r'approved','Approved'), ('rejected','Rejected'),
        (r'escalated','Escalated'), ('returned','Returned'),
        (r'skipped','Skipped'),
    ], blank=True)
    actor = models.ForeignKey(r'users.BankUser', on_delete=models.SET_NULL, null=True)
    comments_encrypted_b64 = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'workspace_workflow_step'


class ServiceLevelAgreement(models.Model):
    """SLA tracking for banking services."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'slas')
    service_name = models.CharField(max_length=100)
    metric_type = models.CharField(max_length=50, choices=[
        (r'response_time','Response Time'),
        (r'uptime','Uptime'),
        (r'transaction_speed','Transaction Speed'),
        (r'resolution_time','Resolution Time'),
    ])
    target_value = models.FloatField()
    current_value = models.FloatField(default=0.0)
    unit = models.CharField(max_length=20)
    is_breached = models.BooleanField(default=False)
    breach_count = models.PositiveIntegerField(default=0)
    last_measured = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'workspace_sla'


class BankingLicense(models.Model):
    """Banking license and regulatory permits."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'licenses')
    license_type = models.CharField(max_length=50, choices=[
        (r'commercial_bank','Commercial Bank'),
        (r'investment_bank','Investment Bank'),
        (r'digital_bank','Digital Bank'),
        (r'payment_institution','Payment Institution'),
        (r'securities_firm','Securities Firm'),
        (r'asset_management','Asset Management'),
    ])
    license_number = models.CharField(max_length=100, unique=True)
    issuing_authority = models.CharField(max_length=50, choices=[
        (r'ojk','OJK'),
        (r'bi','Bank Indonesia'),
        (r'bappebti','BAPPEBTI'),
        (r'sec','SEC'),
    ])
    issued_date = models.DateField()
    expiry_date = models.DateField()
    is_active = models.BooleanField(default=True)
    document_cid = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = r'workspace_banking_license'


class BranchOffice(models.Model):
    """Bank branch offices."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'branches')
    branch_code = models.CharField(max_length=20, unique=True)
    branch_name = models.CharField(max_length=100)
    branch_type = models.CharField(max_length=30, choices=[
        (r'head_office','Head Office'),
        (r'regional','Regional Office'),
        (r'branch','Branch'),
        (r'sub_branch','Sub Branch'),
        (r'atm','ATM'),
        (r'digital','Digital Branch'),
    ])
    address = models.TextField()
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=50, default=r'Indonesia')
    swift_code = models.CharField(max_length=11, blank=True)
    is_active = models.BooleanField(default=True)
    head = models.ForeignKey(r'users.BankUser', on_delete=models.SET_NULL, null=True, related_name='headed_branches')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'workspace_branch_office'


class CorporateHierarchy(models.Model):
    """Corporate organizational hierarchy."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'hierarchy')
    entity_name = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=50, choices=[
        (r'holding','Holding Company'),
        (r'subsidiary','Subsidiary'),
        (r'affiliate','Affiliate'),
        (r'joint_venture','Joint Venture'),
        (r'special_purpose','Special Purpose Vehicle'),
    ])
    parent = models.ForeignKey(r'self', on_delete=models.SET_NULL, null=True, related_name='children')
    ownership_percentage = models.FloatField(default=100.0)
    country = models.CharField(max_length=50)
    is_regulated = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'workspace_corporate_hierarchy'


class BoardResolution(models.Model):
    """Board of directors resolutions."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'board_resolutions')
    resolution_number = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=255)
    content_encrypted_b64 = models.TextField()
    nonce_b64 = models.TextField()
    auth_tag_b64 = models.TextField()
    resolution_date = models.DateField()
    effective_date = models.DateField()
    signatories = models.ManyToManyField(r'users.BankUser', related_name='board_resolutions')
    document_cid = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(r'users.BankUser', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'workspace_board_resolution'


class RemoteWorkSession(models.Model):
    """Virtual office — remote work sessions."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'work_sessions')
    user = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    session_type = models.CharField(max_length=50, choices=[
        (r'focus','Focus Mode'),
        (r'meeting','Meeting'),
        (r'break','Break'),
        (r'available','Available'),
        (r'dnd','Do Not Disturb'),
    ], default=r'available')
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    productive_minutes = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = r'workspace_remote_session'


class TaskBoard(models.Model):
    """Kanban task board."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'task_boards')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'workspace_task_board'


class Task(models.Model):
    """Task/ticket."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    board = models.ForeignKey(TaskBoard, on_delete=models.CASCADE, related_name=r'tasks')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[
        (r'todo','To Do'),
        (r'in_progress','In Progress'),
        (r'review','In Review'),
        (r'done','Done'),
    ], default=r'todo')
    priority = models.CharField(max_length=20, choices=[
        (r'low','Low'),('medium','Medium'),
        (r'high','High'),('urgent','Urgent'),
    ], default=r'medium')
    assignee = models.ForeignKey(r'users.BankUser', on_delete=models.SET_NULL, null=True, related_name='assigned_tasks')
    due_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE, related_name='created_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = r'workspace_task'


class VirtualMeetingRoom(models.Model):
    """Virtual meeting room."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'meeting_rooms')
    name = models.CharField(max_length=100)
    room_type = models.CharField(max_length=50, choices=[
        (r'standup','Daily Standup'),
        (r'planning','Sprint Planning'),
        (r'review','Code Review'),
        (r'all_hands','All Hands'),
        (r'one_on_one','1-on-1'),
        (r'open','Open Room'),
    ])
    max_participants = models.PositiveIntegerField(default=20)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'workspace_virtual_room'


class AttendanceLog(models.Model):
    """Remote work attendance tracking."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE, related_name='attendance')
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    check_in = models.DateTimeField()
    check_out = models.DateTimeField(null=True, blank=True)
    work_hours = models.FloatField(default=0.0)
    location = models.CharField(max_length=100, blank=True)
    date = models.DateField()

    class Meta:
        db_table = r'workspace_attendance'
        unique_together = [r'user', 'date']


class WikiPage(models.Model):
    """Notion-style wiki pages."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'wiki_pages')
    title = models.CharField(max_length=255)
    content_encrypted_b64 = models.TextField(blank=True)
    nonce_b64 = models.TextField(blank=True)
    auth_tag_b64 = models.TextField(blank=True)
    parent = models.ForeignKey(r'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    icon = models.CharField(max_length=10, blank=True)
    cover_ipfs_cid = models.TextField(blank=True)
    is_published = models.BooleanField(default=False)
    created_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = r'workspace_wiki_page'


class WikiPageVersion(models.Model):
    """Wiki page version history."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    page = models.ForeignKey(WikiPage, on_delete=models.CASCADE, related_name=r'versions')
    content_encrypted_b64 = models.TextField()
    nonce_b64 = models.TextField()
    auth_tag_b64 = models.TextField()
    version_number = models.PositiveIntegerField(default=1)
    edited_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'workspace_wiki_version'


class Sprint(models.Model):
    """Agile sprint."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'sprints')
    name = models.CharField(max_length=100)
    goal = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[
        (r'planning','Planning'),
        (r'active','Active'),
        (r'review','Review'),
        (r'done','Done'),
    ], default=r'planning')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    velocity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'workspace_sprint'


class SprintTask(models.Model):
    """Tasks in sprint."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sprint = models.ForeignKey(Sprint, on_delete=models.CASCADE, related_name=r'sprint_tasks')
    task = models.ForeignKey(r'Task', on_delete=models.CASCADE)
    story_points = models.PositiveSmallIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'workspace_sprint_task'
        unique_together = [r'sprint', 'task']


class TimeTracking(models.Model):
    """Time tracking per task."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE, related_name='time_logs')
    task = models.ForeignKey(r'Task', on_delete=models.CASCADE, related_name='time_logs')
    minutes = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    logged_at = models.DateTimeField(auto_now_add=True)
    date = models.DateField()

    class Meta:
        db_table = r'workspace_time_tracking'


class OKR(models.Model):
    """Objectives and Key Results."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'okrs')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    quarter = models.CharField(max_length=10)
    progress = models.FloatField(default=0.0)
    status = models.CharField(max_length=20, choices=[
        (r'on_track','On Track'),
        (r'at_risk','At Risk'),
        (r'behind','Behind'),
        (r'done','Done'),
    ], default=r'on_track')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'workspace_okr'


class KeyResult(models.Model):
    """Key results for OKR."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    okr = models.ForeignKey(OKR, on_delete=models.CASCADE, related_name=r'key_results')
    title = models.CharField(max_length=255)
    target_value = models.FloatField(default=100.0)
    current_value = models.FloatField(default=0.0)
    unit = models.CharField(max_length=20, blank=True)
    due_date = models.DateField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = r'workspace_key_result'


class TeamCalendar(models.Model):
    """Team calendar events."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'calendar_events')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    event_type = models.CharField(max_length=50, choices=[
        (r'meeting','Meeting'),
        (r'deadline','Deadline'),
        (r'review','Review'),
        (r'holiday','Holiday'),
        (r'training','Training'),
        (r'one_on_one','1-on-1'),
    ])
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    attendees = models.ManyToManyField(r'users.BankUser', related_name='calendar_events', blank=True)
    meeting_url = models.URLField(blank=True)
    is_recurring = models.BooleanField(default=False)
    recurrence_rule = models.CharField(max_length=100, blank=True)
    created_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'workspace_calendar_event'


class Standup(models.Model):
    """Daily standup reports."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE, related_name='standups')
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    yesterday = models.TextField()
    today = models.TextField()
    blockers = models.TextField(blank=True)
    mood = models.PositiveSmallIntegerField(choices=[(i,i) for i in range(1,6)], default=3)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'workspace_standup'
        unique_together = [r'user', 'date']


class TeamGoal(models.Model):
    """Team goals and milestones."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'team_goals')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    target_date = models.DateField(null=True, blank=True)
    progress = models.FloatField(default=0.0)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    assigned_to = models.ManyToManyField(r'users.BankUser', related_name='team_goals', blank=True)
    created_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'workspace_team_goal'


class ProjectTemplate(models.Model):
    """Project templates."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'project_templates')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    template_type = models.CharField(max_length=50, choices=[
        (r'software','Software Development'),
        (r'marketing','Marketing Campaign'),
        (r'design','Design Project'),
        (r'research','Research'),
        (r'onboarding','Employee Onboarding'),
        (r'product','Product Launch'),
    ])
    structure = models.JSONField(default=dict)
    is_public = models.BooleanField(default=False)
    created_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'workspace_project_template'


class ProjectMilestone(models.Model):
    """Project milestones."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'milestones')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        (r'upcoming','Upcoming'),
        (r'in_progress','In Progress'),
        (r'completed','Completed'),
        (r'overdue','Overdue'),
    ], default=r'upcoming')
    progress = models.FloatField(default=0.0)
    created_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'workspace_milestone'


class TaskComment(models.Model):
    """Comments on tasks."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(r'Task', on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    content_encrypted_b64 = models.TextField()
    nonce_b64 = models.TextField()
    auth_tag_b64 = models.TextField()
    is_edited = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = r'workspace_task_comment'


class TaskAttachment(models.Model):
    """File attachments on tasks."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(r'Task', on_delete=models.CASCADE, related_name='attachments')
    filename = models.CharField(max_length=255)
    file_cid = models.TextField()
    file_size = models.BigIntegerField(default=0)
    mime_type = models.CharField(max_length=100, blank=True)
    uploaded_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'workspace_task_attachment'


class TaskLabel(models.Model):
    """Labels for tasks."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'labels')
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default=r'#6366f1')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'workspace_label'
        unique_together = [r'workspace', 'name']


class TaskLabelAssignment(models.Model):
    """Assign labels to tasks."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(r'Task', on_delete=models.CASCADE, related_name='labels')
    label = models.ForeignKey(TaskLabel, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'workspace_task_label'
        unique_together = [r'task', 'label']


class DocumentTemplate(models.Model):
    """Document templates."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'doc_templates')
    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=50, choices=[
        (r'meeting_notes','Meeting Notes'),
        (r'project_brief','Project Brief'),
        (r'retrospective','Retrospective'),
        (r'one_on_one','1-on-1 Notes'),
        (r'incident','Incident Report'),
        (r'rfc','RFC Document'),
    ])
    content_encrypted_b64 = models.TextField()
    nonce_b64 = models.TextField()
    auth_tag_b64 = models.TextField()
    created_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'workspace_doc_template'


class MeetingNotes(models.Model):
    """Meeting notes and action items."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'meeting_notes')
    title = models.CharField(max_length=255)
    content_encrypted_b64 = models.TextField(blank=True)
    nonce_b64 = models.TextField(blank=True)
    auth_tag_b64 = models.TextField(blank=True)
    attendees = models.ManyToManyField(r'users.BankUser', related_name='meeting_notes', blank=True)
    action_items = models.JSONField(default=list)
    meeting_date = models.DateTimeField()
    created_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'workspace_meeting_notes'


class WorkspaceIntegrationToken(models.Model):
    """Integration tokens for third-party apps."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'integration_tokens')
    integration_type = models.CharField(max_length=50, choices=[
        (r'github','GitHub'),
        (r'gitlab','GitLab'),
        (r'jira','Jira'),
        (r'notion','Notion'),
        (r'figma','Figma'),
        (r'google_calendar','Google Calendar'),
        (r'zoom','Zoom'),
        (r'lark','Lark'),
    ])
    token_encrypted_b64 = models.TextField()
    nonce_b64 = models.TextField()
    auth_tag_b64 = models.TextField()
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'workspace_integration_token'


class GitHubEvent(models.Model):
    """GitHub webhook events."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'github_events')
    event_type = models.CharField(max_length=50)
    repository = models.CharField(max_length=255)
    actor = models.CharField(max_length=100)
    payload = models.JSONField(default=dict)
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'workspace_github_event'


class Department(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'departments')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    head = models.ForeignKey(r'users.BankUser', on_delete=models.SET_NULL, null=True, related_name='headed_departments')
    parent = models.ForeignKey(r'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='sub_departments')
    budget = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'workspace_department'

class DepartmentMember(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name=r'members')
    user = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    role = models.CharField(max_length=50, default=r'member')
    joined_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = r'workspace_department_member'
        unique_together = [r'department', 'user']

class ProjectRoadmap(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'roadmaps')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    status = models.CharField(max_length=20, default=r'active')
    created_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'workspace_roadmap'

class RoadmapItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    roadmap = models.ForeignKey(ProjectRoadmap, on_delete=models.CASCADE, related_name=r'items')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, default=r'planned')
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    progress = models.FloatField(default=0.0)
    owner = models.ForeignKey(r'users.BankUser', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'workspace_roadmap_item'

class BudgetTracker(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'budgets')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True)
    category = models.CharField(max_length=50)
    allocated = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    spent = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    period = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'workspace_budget'

class BudgetExpense(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    budget = models.ForeignKey(BudgetTracker, on_delete=models.CASCADE, related_name=r'expenses')
    title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    receipt_cid = models.TextField(blank=True)
    submitted_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    approved_by = models.ForeignKey(r'users.BankUser', on_delete=models.SET_NULL, null=True, related_name='approved_expenses')
    status = models.CharField(max_length=20, default=r'pending')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'workspace_expense'

class ResourceBooking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'bookings')
    resource_type = models.CharField(max_length=50, choices=[(r'room','Meeting Room'),('equipment','Equipment'),('license','Software License'),('server','Server')])
    resource_name = models.CharField(max_length=100)
    booked_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    purpose = models.TextField(blank=True)
    status = models.CharField(max_length=20, default=r'confirmed')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'workspace_resource_booking'

class WorkspaceSubscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'subscriptions')
    plan = models.CharField(max_length=20, choices=[(r'free','Free'),('pro','Pro'),('enterprise','Enterprise')])
    max_members = models.PositiveIntegerField(default=10)
    max_storage_gb = models.PositiveIntegerField(default=10)
    features = models.JSONField(default=list)
    billing_cycle = models.CharField(max_length=20, default=r'monthly')
    next_billing = models.DateField(null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'workspace_subscription'

class WorkspaceAnalytics(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'analytics')
    date = models.DateField()
    active_users = models.PositiveIntegerField(default=0)
    messages_sent = models.PositiveIntegerField(default=0)
    files_uploaded = models.PositiveIntegerField(default=0)
    tasks_completed = models.PositiveIntegerField(default=0)
    meeting_minutes = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = r'workspace_analytics'
        unique_together = [r'workspace', 'date']

class ChannelAnalytics(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name=r'analytics')
    date = models.DateField()
    messages_sent = models.PositiveIntegerField(default=0)
    active_members = models.PositiveIntegerField(default=0)
    reactions_given = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = r'workspace_channel_analytics'
        unique_together = [r'channel', 'date']


class CustomField(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'custom_fields')
    name = models.CharField(max_length=100)
    field_type = models.CharField(max_length=20, choices=[(r'text','Text'),('number','Number'),('date','Date'),('select','Select'),('multiselect','Multi-Select'),('checkbox','Checkbox'),('url','URL'),('email','Email')])
    options = models.JSONField(default=list)
    is_required = models.BooleanField(default=False)
    apply_to = models.CharField(max_length=20, choices=[(r'task','Task'),('project','Project'),('user','User')])
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'workspace_custom_field'

class CustomFieldValue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    field = models.ForeignKey(CustomField, on_delete=models.CASCADE, related_name=r'values')
    object_id = models.CharField(max_length=50)
    value = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'workspace_custom_field_value'

class Automation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'automations')
    name = models.CharField(max_length=100)
    trigger = models.CharField(max_length=50, choices=[(r'task_created','Task Created'),('task_completed','Task Completed'),('message_sent','Message Sent'),('member_joined','Member Joined'),('due_date','Due Date Reached')])
    conditions = models.JSONField(default=dict)
    actions = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    run_count = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'workspace_automation'

class AutomationLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    automation = models.ForeignKey(Automation, on_delete=models.CASCADE, related_name=r'logs')
    trigger_data = models.JSONField(default=dict)
    actions_taken = models.JSONField(default=list)
    status = models.CharField(max_length=20, default=r'success')
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'workspace_automation_log'

class WorkspaceTheme(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'themes')
    name = models.CharField(max_length=100)
    primary_color = models.CharField(max_length=7, default=r'#6366f1')
    secondary_color = models.CharField(max_length=7, default=r'#8b5cf6')
    background_color = models.CharField(max_length=7, default=r'#0a0a0f')
    sidebar_color = models.CharField(max_length=7, default=r'#1a1d21')
    is_active = models.BooleanField(default=False)
    created_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'workspace_theme'

class WorkspaceApp(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'apps')
    app_name = models.CharField(max_length=100)
    app_type = models.CharField(max_length=50, choices=[(r'bot','Bot'),('integration','Integration'),('webhook','Webhook'),('slash_command','Slash Command')])
    app_url = models.URLField(blank=True)
    token_encrypted_b64 = models.TextField(blank=True)
    nonce_b64 = models.TextField(blank=True)
    auth_tag_b64 = models.TextField(blank=True)
    permissions = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    installed_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'workspace_app'

class SlashCommand(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'slash_commands')
    command = models.CharField(max_length=50)
    description = models.CharField(max_length=255)
    app = models.ForeignKey(WorkspaceApp, on_delete=models.CASCADE, related_name=r'commands')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = r'workspace_slash_command'
        unique_together = [r'workspace', 'command']

class WorkflowTrigger(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'workflow_triggers')
    name = models.CharField(max_length=100)
    trigger_type = models.CharField(max_length=50)
    schedule = models.CharField(max_length=100, blank=True)
    webhook_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    last_triggered = models.DateTimeField(null=True)
    created_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'workspace_workflow_trigger'

class DataImport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'imports')
    source = models.CharField(max_length=50, choices=[(r'slack','Slack'),('teams','Microsoft Teams'),('notion','Notion'),('jira','Jira'),('csv','CSV'),('json','JSON')])
    status = models.CharField(max_length=20, default=r'pending')
    total_records = models.PositiveIntegerField(default=0)
    imported_records = models.PositiveIntegerField(default=0)
    failed_records = models.PositiveIntegerField(default=0)
    error_log = models.TextField(blank=True)
    initiated_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True)
    class Meta: db_table = r'workspace_data_import'

class DataExport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name=r'data_exports')
    export_type = models.CharField(max_length=50, choices=[(r'messages','Messages'),('files','Files'),('tasks','Tasks'),('users','Users'),('full','Full Workspace')])
    format = models.CharField(max_length=10, choices=[(r'json','JSON'),('csv','CSV'),('zip','ZIP')])
    status = models.CharField(max_length=20, default=r'pending')
    file_cid = models.TextField(blank=True)
    size_bytes = models.BigIntegerField(default=0)
    requested_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True)
    class Meta: db_table = r'workspace_data_export'

# Extended models
from apps.workspace.models_extended import *
