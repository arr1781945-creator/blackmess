"""
apps/users/models.py
User domain — 11 tables covering identity, MFA, sessions, roles, devices.

Tables:
  1.  BankUser          — Extended AbstractUser
  2.  UserProfile       — PII & KYC metadata
  3.  UserRole          — RBAC role catalogue
  4.  UserRoleAssignment— User ↔ Role M2M with scope
  5.  MFADevice         — TOTP / FIDO2 devices
  6.  LoginSession      — Tracked login sessions
  7.  DeviceFingerprint — Anti-replay device registry
  8.  PasswordHistory   — Prevent password reuse (last 12)
  9.  InviteToken       — Workspace invitation tokens
  10. APIKey            — Per-user API key management
  11. UserPublicKey     — PQC & classical public keys
"""

import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from simple_history.models import HistoricalRecords


class BankUser(AbstractUser):
    groups = models.ManyToManyField("auth.Group", related_name="bankuser_groups_set", blank=True)
    user_permissions = models.ManyToManyField("auth.Permission", related_name="bankuser_permissions_set", blank=True)
    """
    Primary user model. Extends Django AbstractUser with banking-grade fields.
    UUID primary key — no sequential ID exposure.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee_id = models.CharField(max_length=32, unique=True, db_index=True)
    department = models.CharField(max_length=128, blank=True)
    clearance_level = models.PositiveSmallIntegerField(
        default=1,
        choices=[(i, f"Level {i}") for i in range(1, 6)],
        help_text="1=Basic, 5=Executive. Controls vault access.",
    )
    is_mfa_enforced = models.BooleanField(default=True)
    is_mfa_verified = models.BooleanField(default=False)
    pqc_public_key_kyber = models.TextField(blank=True, help_text="Kyber-1024 public key (base64)")
    pqc_public_key_dilithium = models.TextField(blank=True, help_text="Dilithium3 verify key (base64)")
    avatar_ipfs_cid = models.CharField(max_length=128, blank=True)
    last_ip = models.GenericIPAddressField(null=True, blank=True)
    last_active = models.DateTimeField(null=True, blank=True)
    is_locked = models.BooleanField(default=False, help_text="Admin/Axes hard lock")
    deactivated_at = models.DateTimeField(null=True, blank=True)

    history = HistoricalRecords()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email", "employee_id"]

    class Meta:
        db_table = "users_bankuser"
        indexes = [
            models.Index(fields=["employee_id"]),
            models.Index(fields=["clearance_level"]),
            models.Index(fields=["last_active"]),
        ]
        verbose_name = "Bank User"
        verbose_name_plural = "Bank Users"

    def __str__(self):
        return f"{self.username} [{self.employee_id}]"

    @property
    def display_name(self):
        return self.get_full_name() or self.username


class UserProfile(models.Model):
    """Extended PII stored separately — minimise blast radius on breach."""
    user = models.OneToOneField(BankUser, on_delete=models.CASCADE, related_name="profile")
    phone_encrypted = models.TextField(blank=True, help_text="AES-256-GCM encrypted phone")
    title = models.CharField(max_length=64, blank=True)
    bio_encrypted = models.TextField(blank=True)
    timezone = models.CharField(max_length=64, default="UTC")
    locale = models.CharField(max_length=16, default="en-US")
    notification_prefs = models.JSONField(default=dict)
    theme = models.CharField(max_length=16, default="dark", choices=[("dark", "Dark"), ("light", "Light")])

    class Meta:
        db_table = "users_profile"


class UserRole(models.Model):
    """RBAC role catalogue — static definitions."""
    ROLE_CHOICES = [
        ("super_admin",       "Super Administrator"),
        ("compliance_officer","Compliance Officer"),
        ("branch_manager",    "Branch Manager"),
        ("senior_analyst",    "Senior Analyst"),
        ("analyst",           "Analyst"),
        ("trader",            "Trader"),
        ("support",           "Support Staff"),
        ("auditor",           "Auditor (Read-Only)"),
        ("external_counsel",  "External Counsel"),
        ("guest",             "Guest"),
    ]
    name = models.CharField(max_length=32, unique=True, choices=ROLE_CHOICES)
    display_name = models.CharField(max_length=64)
    permissions = models.JSONField(default=list, help_text="List of permission codenames")
    max_clearance = models.PositiveSmallIntegerField(default=3)
    can_access_vault = models.BooleanField(default=False)
    can_export_messages = models.BooleanField(default=False)

    class Meta:
        db_table = "users_role"

    def __str__(self):
        return self.display_name


class UserRoleAssignment(models.Model):
    """M2M: user ↔ role with workspace scope and validity window."""
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name="role_assignments")
    role = models.ForeignKey(UserRole, on_delete=models.PROTECT, related_name="assignments")
    workspace = models.ForeignKey(
        "workspace.Workspace", on_delete=models.CASCADE,
        null=True, blank=True,
        help_text="Null = global role",
    )
    granted_by = models.ForeignKey(BankUser, on_delete=models.SET_NULL, null=True, related_name="granted_roles")
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "users_role_assignment"
        unique_together = [("user", "role", "workspace")]
        indexes = [models.Index(fields=["user", "is_active"])]


class MFADevice(models.Model):
    """TOTP / FIDO2 / backup-code devices per user."""
    DEVICE_TYPE_CHOICES = [
        ("totp", "TOTP (Authenticator App)"),
        ("fido2", "FIDO2 / WebAuthn"),
        ("sms", "SMS OTP"),
        ("hardware_key", "USB Hardware Key"),
        ("backup", "Backup Codes"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name="mfa_devices")
    device_type = models.CharField(max_length=16, choices=DEVICE_TYPE_CHOICES)
    name = models.CharField(max_length=64, help_text="User-visible label e.g. r'iPhone 15'")
    secret_encrypted = models.TextField(help_text="AES-GCM encrypted TOTP secret or FIDO2 credential")
    is_primary = models.BooleanField(default=False)
    is_confirmed = models.BooleanField(default=False)
    last_used = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    failure_count = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "users_mfa_device"
        ordering = ["-is_primary", "-created_at"]


class LoginSession(models.Model):
    """Tracked login sessions — one row per device login."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name="sessions")
    refresh_jti = models.CharField(max_length=255, unique=True, db_index=True, default="", blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=512, blank=True)
    device_fingerprint = models.CharField(max_length=128, blank=True)
    country_code = models.CharField(max_length=4, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True, )
    is_revoked = models.BooleanField(default=False)
    revoked_reason = models.CharField(max_length=64, blank=True)

    class Meta:
        db_table = "users_login_session"
        indexes = [
            models.Index(fields=["user", "is_revoked"]),
            models.Index(fields=["expires_at"]),
        ]


class DeviceFingerprint(models.Model):
    """Anti-replay: trusted device registry per user."""
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name="trusted_devices")
    fingerprint_hash = models.CharField(max_length=128, db_index=True)
    device_label = models.CharField(max_length=128, blank=True)
    trust_level = models.PositiveSmallIntegerField(default=1, choices=[(1, "Partial"), (2, "Full")])
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    is_blocked = models.BooleanField(default=False)

    class Meta:
        db_table = "users_device_fingerprint"
        unique_together = [("user", "fingerprint_hash")]


class PasswordHistory(models.Model):
    """Last 12 password hashes — enforce no reuse."""
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name="password_history")
    password_hash = models.CharField(max_length=256)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "users_password_history"
        ordering = ["-created_at"]


class InviteToken(models.Model):
    """Workspace invitation tokens — single-use, expiring."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey("workspace.Workspace", on_delete=models.CASCADE, related_name="invites")
    created_by = models.ForeignKey(BankUser, on_delete=models.SET_NULL, null=True)
    email = models.EmailField()
    role = models.ForeignKey(UserRole, on_delete=models.PROTECT)
    token_hash = models.CharField(max_length=256, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True, )
    used_at = models.DateTimeField(null=True, blank=True)
    used_by = models.ForeignKey(BankUser, on_delete=models.SET_NULL, null=True, related_name="used_invites")

    class Meta:
        db_table = "users_invite_token"


class APIKey(models.Model):
    """Per-user service API keys (for integrations)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name="api_keys")
    name = models.CharField(max_length=64)
    key_prefix = models.CharField(max_length=12, db_index=True)   # First 8 chars — for lookup
    key_hash = models.CharField(max_length=256, unique=True)        # SHA-512 hash — never store raw
    scopes = models.JSONField(default=list, help_text="e.g. [r'read:messages', 'write:messages']")
    is_active = models.BooleanField(default=True)
    last_used = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "users_api_key"


class UserPublicKey(models.Model):
    """Stores classical (RSA/EC) and PQC public keys for E2EE key exchange."""
    KEY_TYPE_CHOICES = [
        ("rsa_4096",    "RSA-4096"),
        ("ec_p384",     "ECDH P-384"),
        ("kyber_1024",  "Kyber-1024 (PQC KEM)"),
        ("ml_dsa_65",  "Dilithium3 (PQC Sig)"),
    ]
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name="public_keys")
    key_type = models.CharField(max_length=16, choices=KEY_TYPE_CHOICES)
    public_key_b64 = models.TextField(help_text="Base64-encoded DER/raw key")
    fingerprint = models.CharField(max_length=128, db_index=True)
    is_current = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    rotated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "users_public_key"
        unique_together = [("user", "key_type", "is_current")]


# ─── User Expansion Tables ───────────────────────────────────────────────────

class UserDevice(models.Model):
    """Multi-device support per user."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'devices')
    device_name = models.CharField(max_length=100)
    device_type = models.CharField(max_length=20, choices=[(r'mobile','Mobile'),('desktop','Desktop'),('tablet','Tablet')])
    device_fingerprint = models.CharField(max_length=255, unique=True)
    push_token = models.TextField(blank=True)
    is_trusted = models.BooleanField(default=False)
    last_active = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'users_device'


class UserNotification(models.Model):
    """Push notifications."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'notifications')
    title = models.CharField(max_length=255)
    body = models.TextField()
    notification_type = models.CharField(max_length=50)
    is_read = models.BooleanField(default=False)
    data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'users_notification'


class UserActivityLog(models.Model):
    """Track user activity."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'activity_logs')
    action = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'users_activity_log'


class UserBlocked(models.Model):
    """Block list."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    blocker = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'blocking')
    blocked = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'blocked_by')
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'users_blocked'
        unique_together = [r'blocker', 'blocked']


class UserContact(models.Model):
    """Contact list."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'contacts')
    contact = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'contact_of')
    nickname = models.CharField(max_length=100, blank=True)
    is_favourite = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'users_contact'
        unique_together = [r'user', 'contact']


class UserCustomStatus(models.Model):
    """Custom user status."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(BankUser, on_delete=models.CASCADE, related_name=r'custom_status')
    text = models.CharField(max_length=100, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = r'users_custom_status'


class UserPreference(models.Model):
    """UI/UX preferences."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(BankUser, on_delete=models.CASCADE, related_name=r'preferences')
    theme = models.CharField(max_length=20, default=r'dark')
    language = models.CharField(max_length=10, default=r'en')
    notification_sound = models.BooleanField(default=True)
    compact_mode = models.BooleanField(default=False)
    settings = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = r'users_preference'


class UserBadge(models.Model):
    """Achievement badges."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'badges')
    badge_type = models.CharField(max_length=50)
    awarded_at = models.DateTimeField(auto_now_add=True)
    awarded_by = models.ForeignKey(BankUser, on_delete=models.SET_NULL, null=True, related_name=r'awarded_badges')

    class Meta:
        db_table = r'users_badge'


class RBACPolicy(models.Model):
    """Role-based access control policies."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    permissions = models.JSONField(default=list)
    resources = models.JSONField(default=list)
    conditions = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(r'BankUser', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = r'users_rbac_policy'


class RBACPolicyAssignment(models.Model):
    """Assign RBAC policies to users."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(r'BankUser', on_delete=models.CASCADE, related_name='rbac_policies')
    policy = models.ForeignKey(RBACPolicy, on_delete=models.CASCADE)
    granted_by = models.ForeignKey(r'BankUser', on_delete=models.SET_NULL, null=True, related_name='granted_policies')
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'users_rbac_assignment'
        unique_together = [r'user', 'policy']


class CurrencyRate(models.Model):
    """Multi-currency exchange rates."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    base_currency = models.CharField(max_length=3)
    target_currency = models.CharField(max_length=3)
    rate = models.DecimalField(max_digits=20, decimal_places=8)
    source = models.CharField(max_length=50, default=r'BI')
    is_active = models.BooleanField(default=True)
    effective_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'users_currency_rate'
        unique_together = [r'base_currency', 'target_currency', 'effective_at']


class BiometricAuth(models.Model):
    """Biometric authentication data."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'biometrics')
    biometric_type = models.CharField(max_length=30, choices=[
        (r'fingerprint','Fingerprint'),
        (r'face','Face Recognition'),
        (r'voice','Voice Print'),
        (r'iris','Iris Scan'),
    ])
    template_hash = models.CharField(max_length=64)
    encrypted_template_b64 = models.TextField()
    is_active = models.BooleanField(default=True)
    last_used = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'users_biometric_auth'


class AccessTimeRestriction(models.Model):
    """Time-based access restrictions."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'time_restrictions')
    allowed_days = models.JSONField(default=list)
    allowed_hours_start = models.TimeField()
    allowed_hours_end = models.TimeField()
    timezone = models.CharField(max_length=50, default=r'Asia/Jakarta')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(BankUser, on_delete=models.SET_NULL, null=True, related_name=r'created_restrictions')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'users_access_time_restriction'


class IPWhitelist(models.Model):
    """IP whitelist per user/workspace."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'ip_whitelist', null=True, blank=True)
    workspace = models.ForeignKey(r'workspace.Workspace', on_delete=models.CASCADE, related_name='ip_whitelist', null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    ip_range = models.CharField(max_length=50, blank=True)
    label = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(BankUser, on_delete=models.SET_NULL, null=True, related_name=r'created_whitelists')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = r'users_ip_whitelist'


class SecurityIncident(models.Model):
    """Security incident tracking."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    incident_number = models.CharField(max_length=50, unique=True)
    incident_type = models.CharField(max_length=50, choices=[
        (r'unauthorized_access','Unauthorized Access'),
        (r'data_breach','Data Breach'),
        (r'brute_force','Brute Force'),
        (r'insider_threat','Insider Threat'),
        (r'malware','Malware'),
        (r'phishing','Phishing'),
        (r'ddos','DDoS'),
    ])
    severity = models.CharField(max_length=20, choices=[
        (r'low','Low'), ('medium','Medium'),
        (r'high','High'), ('critical','Critical'),
    ])
    affected_users = models.ManyToManyField(BankUser, related_name=r'security_incidents', blank=True)
    description = models.TextField()
    remediation = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[
        (r'open','Open'), ('investigating','Investigating'),
        (r'contained','Contained'), ('resolved','Resolved'),
    ], default=r'open')
    detected_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    assigned_to = models.ForeignKey(BankUser, on_delete=models.SET_NULL, null=True, related_name=r'assigned_incidents')

    class Meta:
        db_table = r'users_security_incident'


class DataClassification(models.Model):
    """Data classification labels."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(r'workspace.Workspace', on_delete=models.CASCADE)
    resource_type = models.CharField(max_length=50)
    resource_id = models.CharField(max_length=50)
    classification = models.CharField(max_length=30, choices=[
        (r'public','Public'),
        (r'internal','Internal'),
        (r'confidential','Confidential'),
        (r'restricted','Restricted'),
        (r'top_secret','Top Secret'),
    ])
    classified_by = models.ForeignKey(BankUser, on_delete=models.SET_NULL, null=True)
    classified_at = models.DateTimeField(auto_now_add=True)
    review_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = r'users_data_classification'


class EmployeeOnboarding(models.Model):
    """Employee onboarding workflow."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(BankUser, on_delete=models.CASCADE, related_name=r'onboarding')
    department = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    manager = models.ForeignKey(BankUser, on_delete=models.SET_NULL, null=True, related_name=r'managed_onboardings')
    steps_completed = models.JSONField(default=list)
    background_check_passed = models.BooleanField(default=False)
    nda_signed = models.BooleanField(default=False)
    security_training_done = models.BooleanField(default=False)
    systems_access_granted = models.BooleanField(default=False)
    is_complete = models.BooleanField(default=False)
    start_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'users_employee_onboarding'


class EmployeeOffboarding(models.Model):
    """Employee offboarding — revoke all access."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(BankUser, on_delete=models.CASCADE, related_name=r'offboarding')
    reason = models.CharField(max_length=50, choices=[
        (r'resignation','Resignation'),
        (r'termination','Termination'),
        (r'retirement','Retirement'),
        (r'transfer','Transfer'),
    ])
    access_revoked = models.BooleanField(default=False)
    keys_rotated = models.BooleanField(default=False)
    data_archived = models.BooleanField(default=False)
    equipment_returned = models.BooleanField(default=False)
    exit_interview_done = models.BooleanField(default=False)
    last_day = models.DateField(null=True, blank=True)
    processed_by = models.ForeignKey(BankUser, on_delete=models.SET_NULL, null=True, related_name=r'processed_offboardings')
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'users_employee_offboarding'


class TrainingRecord(models.Model):
    """Security + compliance training records."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'training_records')
    training_type = models.CharField(max_length=100, choices=[
        (r'aml_awareness','AML Awareness'),
        (r'data_privacy','Data Privacy'),
        (r'cybersecurity','Cybersecurity'),
        (r'code_of_conduct','Code of Conduct'),
        (r'insider_trading','Insider Trading Policy'),
        (r'gdpr','GDPR Compliance'),
        (r'iso27001','ISO 27001'),
    ])
    status = models.CharField(max_length=20, choices=[
        (r'pending','Pending'), ('in_progress','In Progress'),
        (r'completed','Completed'), ('expired','Expired'),
    ], default=r'pending')
    score = models.FloatField(null=True, blank=True)
    passed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'users_training_record'


class VPNSession(models.Model):
    """VPN session tracking."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'vpn_sessions')
    vpn_ip = models.GenericIPAddressField()
    real_ip = models.GenericIPAddressField(null=True)
    protocol = models.CharField(max_length=20, choices=[
        (r'wireguard','WireGuard'),
        (r'openvpn','OpenVPN'),
        (r'ipsec','IPSec'),
    ], default=r'wireguard')
    is_active = models.BooleanField(default=True)
    connected_at = models.DateTimeField(auto_now_add=True)
    disconnected_at = models.DateTimeField(null=True, blank=True)
    bytes_sent = models.BigIntegerField(default=0)
    bytes_received = models.BigIntegerField(default=0)

    class Meta:
        db_table = r'users_vpn_session'


class ZeroTrustPolicy(models.Model):
    """Zero Trust Network Access policies."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    conditions = models.JSONField(default=dict)
    actions = models.JSONField(default=dict)
    priority = models.PositiveIntegerField(default=100)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(BankUser, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = r'users_zero_trust_policy'
        ordering = [r'priority']


class AdaptiveAuthPolicy(models.Model):
    """Adaptive authentication policies."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    trigger_conditions = models.JSONField(default=dict)
    auth_requirements = models.JSONField(default=list)
    risk_threshold = models.FloatField(default=0.7)
    action = models.CharField(max_length=50, choices=[
        (r'allow','Allow'),
        (r'step_up_mfa','Step-Up MFA'),
        (r'block','Block'),
        (r'notify','Notify Only'),
        (r'challenge','Challenge'),
    ], default=r'step_up_mfa')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(BankUser, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'users_adaptive_auth_policy'


class SessionRiskScore(models.Model):
    """Real-time session risk scoring."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'risk_scores')
    session_id = models.CharField(max_length=100)
    risk_score = models.FloatField(default=0.0)
    risk_factors = models.JSONField(default=dict)
    action_taken = models.CharField(max_length=50, blank=True)
    ip_address = models.GenericIPAddressField(null=True)
    device_fingerprint = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'users_session_risk_score'


class PrivilegedAccessManagement(models.Model):
    """PAM — Privileged access management."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'pam_sessions')
    resource = models.CharField(max_length=100)
    access_type = models.CharField(max_length=50, choices=[
        (r'database','Database'),
        (r'server','Server'),
        (r'network','Network Device'),
        (r'application','Application'),
        (r'cloud','Cloud Console'),
    ])
    justification = models.TextField()
    approved_by = models.ForeignKey(BankUser, on_delete=models.SET_NULL, null=True, related_name=r'pam_approvals')
    session_recording_cid = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[
        (r'pending','Pending'), ('approved','Approved'),
        (r'active','Active'), ('completed','Completed'),
        (r'revoked','Revoked'),
    ], default=r'pending')
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = r'users_pam_session'


class UserSkill(models.Model):
    """User skills and expertise."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'skills')
    skill_name = models.CharField(max_length=100)
    proficiency = models.CharField(max_length=20, choices=[
        (r'beginner','Beginner'),
        (r'intermediate','Intermediate'),
        (r'advanced','Advanced'),
        (r'expert','Expert'),
    ])
    years_experience = models.PositiveSmallIntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'users_skill'
        unique_together = [r'user', 'skill_name']


class UserAvailability(models.Model):
    """User availability schedule."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'availability')
    day_of_week = models.PositiveSmallIntegerField(choices=[(i,i) for i in range(7)])
    start_time = models.TimeField()
    end_time = models.TimeField()
    timezone = models.CharField(max_length=50, default=r'Asia/Jakarta')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = r'users_availability'
        unique_together = [r'user', 'day_of_week']


class UserPerformanceReview(models.Model):
    """Performance reviews."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'performance_reviews')
    reviewer = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'reviews_given')
    period = models.CharField(max_length=20)
    overall_score = models.FloatField(default=0.0)
    strengths = models.TextField(blank=True)
    improvements = models.TextField(blank=True)
    goals_next_period = models.TextField(blank=True)
    is_acknowledged = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'users_performance_review'


class UserCertification(models.Model):
    """Professional certifications."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'certifications')
    name = models.CharField(max_length=255)
    issuer = models.CharField(max_length=100)
    credential_id = models.CharField(max_length=100, blank=True)
    issued_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    certificate_cid = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'users_certification'


class UserFeedback(models.Model):
    """360-degree feedback."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    from_user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'feedback_given')
    to_user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'feedback_received')
    feedback_type = models.CharField(max_length=20, choices=[
        (r'praise','Praise'),
        (r'suggestion','Suggestion'),
        (r'constructive','Constructive'),
    ])
    content_encrypted_b64 = models.TextField()
    nonce_b64 = models.TextField()
    auth_tag_b64 = models.TextField()
    is_anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'users_feedback'


class UserWorkload(models.Model):
    """User workload tracking."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'workloads')
    week_start = models.DateField()
    planned_hours = models.FloatField(default=40.0)
    actual_hours = models.FloatField(default=0.0)
    task_count = models.PositiveIntegerField(default=0)
    completed_count = models.PositiveIntegerField(default=0)
    workload_score = models.FloatField(default=0.0)

    class Meta:
        db_table = r'users_workload'
        unique_together = [r'user', 'week_start']


class TeamMembership(models.Model):
    """Team memberships."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(r'workspace.Workspace', on_delete=models.CASCADE, related_name='teams')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    team_lead = models.ForeignKey(BankUser, on_delete=models.SET_NULL, null=True, related_name=r'led_teams')
    members = models.ManyToManyField(BankUser, related_name=r'teams', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'users_team'


class UserGoal(models.Model):
    """Personal goals."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'personal_goals')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    goal_type = models.CharField(max_length=20, choices=[
        (r'skill','Skill Development'),
        (r'career','Career Growth'),
        (r'project','Project Goal'),
        (r'personal','Personal'),
    ])
    progress = models.FloatField(default=0.0)
    due_date = models.DateField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'users_goal'


class UserAnalytics(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'analytics')
    date = models.DateField()
    messages_sent = models.PositiveIntegerField(default=0)
    tasks_completed = models.PositiveIntegerField(default=0)
    meeting_minutes = models.PositiveIntegerField(default=0)
    focus_minutes = models.PositiveIntegerField(default=0)
    login_count = models.PositiveIntegerField(default=0)
    class Meta:
        db_table = r'users_analytics'
        unique_together = [r'user', 'date']

class UserMentor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mentor = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'mentees')
    mentee = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'mentors')
    workspace = models.ForeignKey(r'workspace.Workspace', on_delete=models.CASCADE)
    focus_areas = models.JSONField(default=list)
    meeting_frequency = models.CharField(max_length=20, default=r'weekly')
    is_active = models.BooleanField(default=True)
    started_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = r'users_mentor'
        unique_together = [r'mentor', 'mentee']

class UserReward(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'rewards')
    reward_type = models.CharField(max_length=50, choices=[(r'kudos','Kudos'),('star','Star Employee'),('innovation','Innovation Award'),('teamwork','Teamwork Award')])
    points = models.PositiveIntegerField(default=0)
    message = models.TextField(blank=True)
    given_by = models.ForeignKey(BankUser, on_delete=models.SET_NULL, null=True, related_name=r'rewards_given')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'users_reward'

class UserLanguage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'languages')
    language = models.CharField(max_length=50)
    proficiency = models.CharField(max_length=20, choices=[(r'basic','Basic'),('conversational','Conversational'),('fluent','Fluent'),('native','Native')])
    class Meta:
        db_table = r'users_language'
        unique_together = [r'user', 'language']

class UserEducation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'education')
    institution = models.CharField(max_length=255)
    degree = models.CharField(max_length=100)
    field_of_study = models.CharField(max_length=100)
    start_year = models.PositiveSmallIntegerField()
    end_year = models.PositiveSmallIntegerField(null=True)
    is_current = models.BooleanField(default=False)
    class Meta: db_table = r'users_education'

class UserWorkHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'work_history')
    company = models.CharField(max_length=255)
    position = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True)
    is_current = models.BooleanField(default=False)
    class Meta: db_table = r'users_work_history'

class UserPortfolio(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'portfolio')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    url = models.URLField(blank=True)
    file_cid = models.TextField(blank=True)
    tags = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'users_portfolio'

class UserTimeOff(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'time_off')
    leave_type = models.CharField(max_length=20, choices=[(r'annual','Annual'),('sick','Sick'),('personal','Personal'),('parental','Parental'),('unpaid','Unpaid')])
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, default=r'pending')
    approved_by = models.ForeignKey(BankUser, on_delete=models.SET_NULL, null=True, related_name=r'approved_leaves')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'users_time_off'

class UserLeaveBalance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'leave_balance')
    year = models.PositiveSmallIntegerField()
    annual_total = models.FloatField(default=12.0)
    annual_used = models.FloatField(default=0.0)
    sick_total = models.FloatField(default=12.0)
    sick_used = models.FloatField(default=0.0)
    class Meta:
        db_table = r'users_leave_balance'
        unique_together = [r'user', 'year']

class Payslip(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'payslips')
    period = models.CharField(max_length=20)
    gross_salary = models.DecimalField(max_digits=15, decimal_places=2)
    deductions = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    net_salary = models.DecimalField(max_digits=15, decimal_places=2)
    payslip_cid = models.TextField(blank=True)
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'users_payslip'


class UserSearchHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'search_history')
    query = models.CharField(max_length=255)
    result_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'users_search_history'

class UserReadStatus(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'read_statuses')
    channel = models.ForeignKey(r'workspace.Channel', on_delete=models.CASCADE)
    last_read_message_id = models.CharField(max_length=50, blank=True)
    last_read_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = r'users_read_status'
        unique_together = [r'user', 'channel']

class UserPushToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'push_tokens')
    token = models.TextField(unique=True)
    platform = models.CharField(max_length=10, choices=[(r'ios','iOS'),('android','Android'),('web','Web')])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'users_push_token'

class UserEmailPreference(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(BankUser, on_delete=models.CASCADE, related_name=r'email_prefs')
    mentions = models.BooleanField(default=True)
    direct_messages = models.BooleanField(default=True)
    task_assignments = models.BooleanField(default=True)
    weekly_digest = models.BooleanField(default=True)
    security_alerts = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: db_table = r'users_email_pref'

class UserTheme(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(BankUser, on_delete=models.CASCADE, related_name=r'theme')
    mode = models.CharField(max_length=10, choices=[(r'dark','Dark'),('light','Light'),('system','System')], default='dark')
    accent_color = models.CharField(max_length=7, default=r'#6366f1')
    font_size = models.CharField(max_length=10, choices=[(r'small','Small'),('medium','Medium'),('large','Large')], default='medium')
    compact_mode = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: db_table = r'users_theme'

class UserShortcut(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'shortcuts')
    shortcut_type = models.CharField(max_length=20, choices=[(r'channel','Channel'),('dm','Direct Message'),('file','File'),('task','Task')])
    target_id = models.CharField(max_length=50)
    label = models.CharField(max_length=100)
    order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'users_shortcut'

class UserActivity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'activities')
    activity_type = models.CharField(max_length=50)
    description = models.TextField()
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'users_activity'

class UserStreak(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(BankUser, on_delete=models.CASCADE, related_name=r'streak')
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_active = models.DateField(null=True)
    total_active_days = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: db_table = r'users_streak'

class UserAchievement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'achievements')
    achievement_type = models.CharField(max_length=50, choices=[(r'first_message','First Message'),('100_messages','100 Messages'),('task_master','Task Master'),('early_bird','Early Bird'),('night_owl','Night Owl'),('helper','Team Helper')])
    earned_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = r'users_achievement'
        unique_together = [r'user', 'achievement_type']

class UserSavedItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'saved_items')
    item_type = models.CharField(max_length=20, choices=[(r'message','Message'),('file','File'),('task','Task'),('wiki','Wiki Page')])
    item_id = models.CharField(max_length=50)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'users_saved_item'

class UserFollower(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    follower = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'following')
    following = models.ForeignKey(BankUser, on_delete=models.CASCADE, related_name=r'followers')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = r'users_follower'
        unique_together = [r'follower', 'following']
