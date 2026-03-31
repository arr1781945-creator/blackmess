"""
apps/compliance/models.py
Compliance domain — 8 tables for audit, reporting, forensics prevention.

Tables:
  1. AuditLog          — Immutable system-wide audit trail
  2. SecurityEvent     — Security-specific event log
  3. ComplianceReport  — Generated regulatory reports
  4. DataRetentionPolicy — Per-workspace retention config
  5. UserConsent       — GDPR/regulatory consent records
  6. ExportRequest     — Message/data export requests with approval workflow
  7. ForensicsBlock    — Anti-forensics metadata control
  8. RegulatorAccess   — Temporary regulator read-only access grants
"""

import uuid
from django.db import models
from django.conf import settings


class AuditLog(models.Model):
    """
    Immutable, append-only audit trail.
    DO NOT add update() or delete() capability to this model.
    """
    SEVERITY_CHOICES = [
        ("info",     "Info"),
        ("warning",  "Warning"),
        ("critical", "Critical"),
        ("alert",    "Security Alert"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=64, db_index=True)
    severity = models.CharField(max_length=16, choices=SEVERITY_CHOICES, default="info")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="audit_logs"
    )
    actor_ip = models.GenericIPAddressField(null=True, blank=True)
    actor_user_agent = models.CharField(max_length=512, blank=True)
    workspace = models.ForeignKey(
        "workspace.Workspace", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="system_audit_logs"
    )
    target_type = models.CharField(max_length=32, blank=True, db_index=True)
    target_id = models.CharField(max_length=64, blank=True)
    description = models.TextField()
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "compliance_audit_log"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["event_type", "created_at"]),
            models.Index(fields=["actor", "created_at"]),
            models.Index(fields=["severity", "created_at"]),
        ]
        # IMPORTANT: Make model append-only at DB level via migrations
        # (no UPDATE privileges for app DB user)

    def save(self, *args, **kwargs):
        if self.pk:
            raise PermissionError("AuditLog records are immutable and cannot be updated.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("AuditLog records cannot be deleted.")


class SecurityEvent(models.Model):
    EVENT_TYPE_CHOICES = [
        ("LOGIN_SUCCESS", "Successful Login"),
        ("LOGIN_FAIL", "Failed Login"),
        ("ACCOUNT_LOCKED", "Account Locked"),
        ("MFA_VERIFIED", "MFA Verified"),
        ("MFA_FAIL", "MFA Failure"),
        ("PASSWORD_CHANGED", "Password Changed"),
        ("VAULT_OPENED", "Vault Session Opened"),
        ("VAULT_ACCESS_DENIED", "Vault Access Denied"),
        ("HW_KEY_REGISTERED", "Hardware Key Registered"),
        ("SUSPICIOUS_ACTIVITY", "Suspicious Activity"),
        ("DATA_EXPORT", "Data Export"),
        ("TTL_WIPE", "Message TTL Wipe"),
        ("SESSION_REVOKED", "Session Revoked"),
        ("INVALID_SIGNATURE", "Invalid Message Signature"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=32, choices=EVENT_TYPE_CHOICES, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="security_events"
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    is_suspicious = models.BooleanField(default=False, db_index=True)
    detail = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "compliance_security_event"
        ordering = ["-created_at"]


class ComplianceReport(models.Model):
    REPORT_TYPE_CHOICES = [
        ("daily_audit",   "Daily Audit Summary"),
        ("user_activity", "User Activity Report"),
        ("vault_access",  "Vault Access Report"),
        ("message_retention", "Message Retention Report"),
        ("security_incidents", "Security Incidents Report"),
        ("regulatory",    "Regulatory Submission"),
    ]
    STATUS_CHOICES = [("pending", "Pending"), ("generating", "Generating"), ("ready", "Ready"), ("failed", "Failed")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_type = models.CharField(max_length=32, choices=REPORT_TYPE_CHOICES)
    title = models.CharField(max_length=256)
    workspace = models.ForeignKey(
        "workspace.Workspace", on_delete=models.CASCADE,
        null=True, blank=True, related_name="compliance_reports"
    )
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    date_from = models.DateTimeField()
    date_to = models.DateTimeField()
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending")
    report_ipfs_cid = models.CharField(max_length=128, blank=True, help_text="IPFS CID of encrypted PDF report")
    generated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "compliance_report"


class DataRetentionPolicy(models.Model):
    workspace = models.OneToOneField("workspace.Workspace", on_delete=models.CASCADE, related_name="retention_policy")
    message_retention_days = models.PositiveIntegerField(default=365)
    file_retention_days = models.PositiveIntegerField(default=730)
    audit_log_retention_days = models.PositiveIntegerField(default=2555, help_text="7 years for banking compliance")
    auto_delete_enabled = models.BooleanField(default=True)
    legal_hold = models.BooleanField(default=False, help_text="Freeze all deletions during legal hold")
    legal_hold_reason = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "compliance_retention_policy"


class UserConsent(models.Model):
    CONSENT_TYPE_CHOICES = [
        ("data_processing", "Data Processing"),
        ("message_monitoring", "Message Monitoring"),
        ("audit_logging", "Audit Logging"),
        ("cross_border_transfer", "Cross-Border Data Transfer"),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="consents")
    consent_type = models.CharField(max_length=32, choices=CONSENT_TYPE_CHOICES)
    version = models.CharField(max_length=16, help_text="Policy version e.g. v2.3")
    consented = models.BooleanField(default=False)
    consented_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = "compliance_user_consent"
        unique_together = [("user", "consent_type", "version")]


class ExportRequest(models.Model):
    STATUS_CHOICES = [("pending", "Pending"), ("approved", "Approved"), ("denied", "Denied"), ("completed", "Completed")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="export_requests")
    workspace = models.ForeignKey("workspace.Workspace", on_delete=models.CASCADE)
    export_type = models.CharField(max_length=32, choices=[("messages", "Messages"), ("audit_logs", "Audit Logs"), ("user_data", "User Data")])
    justification = models.TextField()
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending")
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_exports")
    approved_at = models.DateTimeField(null=True, blank=True)
    export_ipfs_cid = models.CharField(max_length=128, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "compliance_export_request"


class ForensicsBlock(models.Model):
    """Track anti-forensics policies per workspace/channel."""
    workspace = models.ForeignKey("workspace.Workspace", on_delete=models.CASCADE)
    metadata_scrubbing = models.BooleanField(default=True, help_text="Remove EXIF and file metadata on upload")
    header_scrubbing = models.BooleanField(default=True, help_text="Strip identifying headers from responses")
    log_retention_wipe = models.BooleanField(default=False, help_text="Wipe server logs after 30 days")
    clipboard_protection = models.BooleanField(default=True)
    screenshot_detection = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "compliance_forensics_block"


class RegulatorAccess(models.Model):
    """Temporary read-only vault access for regulators (e.g. MAS, OJK)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey("workspace.Workspace", on_delete=models.CASCADE)
    regulator_name = models.CharField(max_length=128)
    regulator_email = models.EmailField()
    granted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    access_token_hash = models.CharField(max_length=256, unique=True)
    scope = models.JSONField(default=list, help_text="List of accessible resource types")
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    access_log = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "compliance_regulator_access"


class SystemHealthLog(models.Model):
    """System health monitoring log."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=[('healthy','Healthy'),('degraded','Degraded'),('down','Down')])
    response_time_ms = models.PositiveIntegerField(default=0)
    details = models.JSONField(default=dict)
    checked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compliance_system_health'


class ThreatIntelligence(models.Model):
    """Threat intelligence feed."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    threat_type = models.CharField(max_length=50)
    indicator = models.CharField(max_length=255)
    severity = models.CharField(max_length=20, choices=[('low','Low'),('medium','Medium'),('high','High'),('critical','Critical')])
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    source = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'compliance_threat_intel'


# ─── Transaction Monitoring ───────────────────────────────────────────────────

class TransactionMonitor(models.Model):
    """Real-time transaction monitoring."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('users.BankUser', on_delete=models.CASCADE, related_name='transactions')
    transaction_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    currency = models.CharField(max_length=10, default='IDR')
    transaction_type = models.CharField(max_length=50, choices=[
        ('transfer','Transfer'), ('payment','Payment'),
        ('withdrawal','Withdrawal'), ('deposit','Deposit'),
        ('fx','Foreign Exchange'), ('swift','SWIFT'),
    ])
    sender_account = models.CharField(max_length=100, blank=True)
    receiver_account = models.CharField(max_length=100, blank=True)
    risk_score = models.FloatField(default=0.0)
    is_flagged = models.BooleanField(default=False)
    flag_reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[
        ('pending','Pending'), ('cleared','Cleared'),
        ('flagged','Flagged'), ('blocked','Blocked'),
    ], default='pending')
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'compliance_transaction_monitor'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['is_flagged', 'status']),
            models.Index(fields=['risk_score']),
        ]


class AMLAlert(models.Model):
    """Anti-Money Laundering alerts."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.ForeignKey(TransactionMonitor, on_delete=models.CASCADE, related_name='aml_alerts')
    user = models.ForeignKey('users.BankUser', on_delete=models.CASCADE, related_name='aml_alerts')
    alert_type = models.CharField(max_length=50, choices=[
        ('structuring','Structuring'),
        ('layering','Layering'),
        ('smurfing','Smurfing'),
        ('rapid_movement','Rapid Movement'),
        ('unusual_pattern','Unusual Pattern'),
        ('pep_match','PEP Match'),
        ('sanctions_match','Sanctions Match'),
    ])
    severity = models.CharField(max_length=20, choices=[
        ('low','Low'), ('medium','Medium'),
        ('high','High'), ('critical','Critical'),
    ])
    description = models.TextField()
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey('users.BankUser', on_delete=models.SET_NULL, null=True, related_name='resolved_alerts')
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compliance_aml_alert'


class SARReport(models.Model):
    """Suspicious Activity Report — wajib dilaporkan ke PPATK."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alert = models.ForeignKey(AMLAlert, on_delete=models.CASCADE, related_name='sar_reports')
    report_number = models.CharField(max_length=50, unique=True)
    narrative = models.TextField()
    submitted_to = models.CharField(max_length=50, default='PPATK')
    submitted_at = models.DateTimeField(null=True, blank=True)
    is_submitted = models.BooleanField(default=False)
    created_by = models.ForeignKey('users.BankUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compliance_sar_report'


class RegulatoryReport(models.Model):
    """Laporan otomatis ke OJK/BI/PPATK."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_type = models.CharField(max_length=50, choices=[
        ('ojk_daily','OJK Daily'),
        ('bi_weekly','BI Weekly'),
        ('ppatk_monthly','PPATK Monthly'),
        ('lkd_quarterly','LKD Quarterly'),
        ('swift_annual','SWIFT Annual'),
    ])
    regulator = models.CharField(max_length=50)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    total_transactions = models.PositiveIntegerField(default=0)
    total_alerts = models.PositiveIntegerField(default=0)
    total_sar = models.PositiveIntegerField(default=0)
    report_data = models.JSONField(default=dict)
    file_path = models.TextField(blank=True)
    is_submitted = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey('users.BankUser', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compliance_regulatory_report'


class FraudPattern(models.Model):
    """Machine learning fraud pattern detection."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pattern_name = models.CharField(max_length=100)
    pattern_type = models.CharField(max_length=50, choices=[
        ('velocity','Velocity Check'),
        ('geolocation','Geolocation Anomaly'),
        ('device','Device Fingerprint'),
        ('behavioral','Behavioral Analysis'),
        ('network','Network Analysis'),
    ])
    rules = models.JSONField(default=dict)
    threshold = models.FloatField(default=0.8)
    is_active = models.BooleanField(default=True)
    true_positive_rate = models.FloatField(default=0.0)
    false_positive_rate = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'compliance_fraud_pattern'


class FraudCase(models.Model):
    """Fraud investigation cases."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case_number = models.CharField(max_length=50, unique=True)
    user = models.ForeignKey('users.BankUser', on_delete=models.CASCADE, related_name='fraud_cases')
    pattern = models.ForeignKey(FraudPattern, on_delete=models.SET_NULL, null=True)
    transaction = models.ForeignKey(TransactionMonitor, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=[
        ('open','Open'), ('investigating','Investigating'),
        ('confirmed','Confirmed Fraud'), ('dismissed','Dismissed'),
    ], default='open')
    evidence = models.JSONField(default=dict)
    assigned_to = models.ForeignKey('users.BankUser', on_delete=models.SET_NULL, null=True, related_name='assigned_cases')
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compliance_fraud_case'


class KYCVerificationFlow(models.Model):
    """KYC verification workflow."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('users.BankUser', on_delete=models.CASCADE, related_name='kyc_flows')
    step = models.CharField(max_length=50, choices=[
        ('identity','Identity Verification'),
        ('liveness','Liveness Check'),
        ('document','Document Scan'),
        ('address','Address Verification'),
        ('pep_check','PEP Screening'),
        ('sanctions','Sanctions Check'),
        ('approved','Approved'),
        ('rejected','Rejected'),
    ])
    status = models.CharField(max_length=20, choices=[
        ('pending','Pending'), ('processing','Processing'),
        ('passed','Passed'), ('failed','Failed'),
    ], default='pending')
    provider = models.CharField(max_length=50, blank=True)
    result_data = models.JSONField(default=dict)
    confidence_score = models.FloatField(default=0.0)
    reviewed_by = models.ForeignKey('users.BankUser', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'compliance_kyc_flow'


class ImmutableAuditChain(models.Model):
    """Blockchain-style immutable audit chain."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sequence = models.BigIntegerField(unique=True, default=0)
    event_type = models.CharField(max_length=100)
    actor_id = models.CharField(max_length=50)
    resource_type = models.CharField(max_length=50)
    resource_id = models.CharField(max_length=50)
    action = models.CharField(max_length=50)
    data_hash = models.CharField(max_length=64)
    previous_hash = models.CharField(max_length=64)
    chain_hash = models.CharField(max_length=64, unique=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True)

    class Meta:
        db_table = 'compliance_immutable_chain'
        ordering = ['sequence']

    def save(self, *args, **kwargs):
        if self.pk:
            raise PermissionError("Immutable audit chain cannot be modified!")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("Immutable audit chain cannot be deleted!")


class PEPScreening(models.Model):
    """Politically Exposed Person screening."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('users.BankUser', on_delete=models.CASCADE, related_name='pep_screenings')
    is_pep = models.BooleanField(default=False)
    pep_category = models.CharField(max_length=50, blank=True)
    pep_country = models.CharField(max_length=50, blank=True)
    risk_level = models.CharField(max_length=20, choices=[
        ('low','Low'), ('medium','Medium'), ('high','High'),
    ], default='low')
    screened_by = models.CharField(max_length=50, default='automated')
    screened_at = models.DateTimeField(auto_now_add=True)
    next_review = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'compliance_pep_screening'


class SanctionsCheck(models.Model):
    """OFAC/UN sanctions screening."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('users.BankUser', on_delete=models.CASCADE, related_name='sanctions_checks')
    is_sanctioned = models.BooleanField(default=False)
    sanctions_list = models.CharField(max_length=50, blank=True)
    match_score = models.FloatField(default=0.0)
    match_details = models.JSONField(default=dict)
    screened_at = models.DateTimeField(auto_now_add=True)
    screened_by = models.CharField(max_length=50, default='automated')

    class Meta:
        db_table = 'compliance_sanctions_check'


class StressTestScenario(models.Model):
    """Bank stress test scenarios — Basel III compliance."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scenario_name = models.CharField(max_length=100)
    scenario_type = models.CharField(max_length=50, choices=[
        ('credit_risk','Credit Risk'),
        ('market_risk','Market Risk'),
        ('liquidity_risk','Liquidity Risk'),
        ('operational_risk','Operational Risk'),
        ('systemic_risk','Systemic Risk'),
    ])
    parameters = models.JSONField(default=dict)
    assumptions = models.TextField(blank=True)
    is_regulatory = models.BooleanField(default=False)
    regulator = models.CharField(max_length=50, blank=True)
    created_by = models.ForeignKey('users.BankUser', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compliance_stress_test_scenario'


class StressTestResult(models.Model):
    """Stress test results."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scenario = models.ForeignKey(StressTestScenario, on_delete=models.CASCADE, related_name='results')
    capital_ratio = models.FloatField(default=0.0)
    liquidity_ratio = models.FloatField(default=0.0)
    npv_impact = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    passed = models.BooleanField(default=False)
    result_data = models.JSONField(default=dict)
    run_by = models.ForeignKey('users.BankUser', on_delete=models.SET_NULL, null=True)
    run_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compliance_stress_test_result'


class WatchlistEntry(models.Model):
    """Regulatory watchlist entries."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('users.BankUser', on_delete=models.CASCADE, related_name='watchlist_entries')
    watchlist_type = models.CharField(max_length=50, choices=[
        ('aml','AML Watchlist'),
        ('fraud','Fraud Watchlist'),
        ('sanctions','Sanctions List'),
        ('pep','PEP List'),
        ('internal','Internal Watchlist'),
    ])
    reason = models.TextField()
    risk_score = models.FloatField(default=0.0)
    added_by = models.ForeignKey('users.BankUser', on_delete=models.SET_NULL, null=True, related_name='watchlist_additions')
    review_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    removed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'compliance_watchlist'


class DataRetentionExecution(models.Model):
    """Track data retention policy executions."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    policy_name = models.CharField(max_length=100)
    records_deleted = models.PositiveIntegerField(default=0)
    bytes_freed = models.BigIntegerField(default=0)
    execution_time_ms = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=[
        ('running','Running'), ('completed','Completed'),
        ('failed','Failed'), ('partial','Partial'),
    ], default='running')
    error_log = models.TextField(blank=True)
    executed_by = models.CharField(max_length=50, default='celery')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'compliance_retention_execution'


class NDARecord(models.Model):
    """Non-Disclosure Agreement records."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('users.BankUser', on_delete=models.CASCADE, related_name='ndas')
    deal_room = models.ForeignKey('workspace.DealRoom', on_delete=models.CASCADE, related_name='ndas', null=True)
    document_hash = models.CharField(max_length=64)
    document_cid = models.TextField(blank=True)
    signature_b64 = models.TextField()
    signed_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'compliance_nda_record'


class RegulatoryDeadline(models.Model):
    """Track regulatory submission deadlines."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    regulator = models.CharField(max_length=50, choices=[
        ('ojk','OJK'), ('bi','Bank Indonesia'),
        ('ppatk','PPATK'), ('basel','Basel Committee'),
        ('swift','SWIFT'), ('fatf','FATF'),
    ])
    requirement = models.CharField(max_length=255)
    deadline = models.DateTimeField()
    is_recurring = models.BooleanField(default=False)
    recurrence = models.CharField(max_length=20, blank=True)
    assigned_to = models.ForeignKey('users.BankUser', on_delete=models.SET_NULL, null=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compliance_regulatory_deadline'


class AIComplianceAlert(models.Model):
    """AI-powered compliance alerts."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alert_source = models.CharField(max_length=50, choices=[
        ('nlp_scan','NLP Message Scan'),
        ('behavior_analysis','Behavior Analysis'),
        ('pattern_match','Pattern Matching'),
        ('anomaly_detection','Anomaly Detection'),
        ('sentiment_analysis','Sentiment Analysis'),
    ])
    severity = models.CharField(max_length=20, choices=[
        ('low','Low'), ('medium','Medium'),
        ('high','High'), ('critical','Critical'),
    ])
    confidence_score = models.FloatField(default=0.0)
    affected_user = models.ForeignKey('users.BankUser', on_delete=models.CASCADE, related_name='ai_alerts')
    resource_type = models.CharField(max_length=50, blank=True)
    resource_id = models.CharField(max_length=50, blank=True)
    description = models.TextField()
    raw_signal = models.JSONField(default=dict)
    is_false_positive = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey('users.BankUser', on_delete=models.SET_NULL, null=True, related_name='reviewed_ai_alerts')
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'compliance_ai_alert'


class MLModelRegistry(models.Model):
    """ML model registry for fraud/AML detection."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model_name = models.CharField(max_length=100)
    model_type = models.CharField(max_length=50, choices=[
        ('fraud_detection','Fraud Detection'),
        ('aml_detection','AML Detection'),
        ('sentiment','Sentiment Analysis'),
        ('anomaly','Anomaly Detection'),
        ('kyc_verification','KYC Verification'),
        ('risk_scoring','Risk Scoring'),
    ])
    version = models.CharField(max_length=20)
    model_hash = models.CharField(max_length=64)
    accuracy = models.FloatField(default=0.0)
    precision = models.FloatField(default=0.0)
    recall = models.FloatField(default=0.0)
    f1_score = models.FloatField(default=0.0)
    is_active = models.BooleanField(default=False)
    deployed_at = models.DateTimeField(null=True, blank=True)
    trained_by = models.ForeignKey('users.BankUser', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compliance_ml_model'


class CommunicationSurveillance(models.Model):
    """MiFID II/FINRA communication surveillance."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey('workspace.Channel', on_delete=models.CASCADE)
    scan_type = models.CharField(max_length=50, choices=[
        ('keyword','Keyword Scan'),
        ('nlp','NLP Analysis'),
        ('sentiment','Sentiment Analysis'),
        ('insider_trading','Insider Trading Detection'),
        ('market_manipulation','Market Manipulation'),
    ])
    flagged_keywords = models.JSONField(default=list)
    risk_score = models.FloatField(default=0.0)
    messages_scanned = models.PositiveIntegerField(default=0)
    messages_flagged = models.PositiveIntegerField(default=0)
    scan_period_start = models.DateTimeField()
    scan_period_end = models.DateTimeField()
    reviewed_by = models.ForeignKey('users.BankUser', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compliance_comm_surveillance'


class RiskMatrix(models.Model):
    """Enterprise risk matrix."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    risk_category = models.CharField(max_length=50, choices=[
        ('credit','Credit Risk'),
        ('market','Market Risk'),
        ('liquidity','Liquidity Risk'),
        ('operational','Operational Risk'),
        ('reputational','Reputational Risk'),
        ('compliance','Compliance Risk'),
        ('cyber','Cyber Risk'),
        ('strategic','Strategic Risk'),
    ])
    risk_name = models.CharField(max_length=255)
    likelihood = models.PositiveSmallIntegerField(choices=[(i,i) for i in range(1,6)])
    impact = models.PositiveSmallIntegerField(choices=[(i,i) for i in range(1,6)])
    risk_score = models.FloatField(default=0.0)
    mitigation = models.TextField(blank=True)
    owner = models.ForeignKey('users.BankUser', on_delete=models.SET_NULL, null=True)
    review_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('identified','Identified'), ('mitigating','Mitigating'),
        ('accepted','Accepted'), ('resolved','Resolved'),
    ], default='identified')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'compliance_risk_matrix'


class BaselCapitalReport(models.Model):
    """Basel III/IV capital adequacy reports."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_date = models.DateField()
    tier1_capital = models.DecimalField(max_digits=20, decimal_places=2)
    tier2_capital = models.DecimalField(max_digits=20, decimal_places=2)
    total_capital = models.DecimalField(max_digits=20, decimal_places=2)
    risk_weighted_assets = models.DecimalField(max_digits=20, decimal_places=2)
    car_ratio = models.FloatField()
    lcr_ratio = models.FloatField()
    nsfr_ratio = models.FloatField()
    leverage_ratio = models.FloatField()
    is_compliant = models.BooleanField(default=True)
    submitted_to_ojk = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey('users.BankUser', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compliance_basel_capital'


class LiquidityReport(models.Model):
    """Daily liquidity monitoring — LCR/NSFR."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_date = models.DateField()
    hqla_amount = models.DecimalField(max_digits=20, decimal_places=2)
    net_cash_outflow = models.DecimalField(max_digits=20, decimal_places=2)
    lcr = models.FloatField()
    available_stable_funding = models.DecimalField(max_digits=20, decimal_places=2)
    required_stable_funding = models.DecimalField(max_digits=20, decimal_places=2)
    nsfr = models.FloatField()
    is_compliant = models.BooleanField(default=True)
    alert_triggered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compliance_liquidity_report'


class InsiderTradingMonitor(models.Model):
    """Insider trading detection and monitoring."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('users.BankUser', on_delete=models.CASCADE, related_name='insider_monitors')
    instrument = models.CharField(max_length=50)
    isin = models.CharField(max_length=12, blank=True)
    action = models.CharField(max_length=20, choices=[
        ('buy','Buy'), ('sell','Sell'),
        ('short','Short'), ('option','Option'),
    ])
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    currency = models.CharField(max_length=3, default='IDR')
    is_during_blackout = models.BooleanField(default=False)
    has_material_info = models.BooleanField(default=False)
    risk_score = models.FloatField(default=0.0)
    is_flagged = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey('users.BankUser', on_delete=models.SET_NULL, null=True, related_name='reviewed_insider')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compliance_insider_trading'


class BlackoutPeriod(models.Model):
    """Trading blackout periods."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey('workspace.Workspace', on_delete=models.CASCADE)
    reason = models.CharField(max_length=255)
    affected_roles = models.JSONField(default=list)
    affected_instruments = models.JSONField(default=list)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey('users.BankUser', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compliance_blackout_period'


class GDPRRequest(models.Model):
    """GDPR data subject requests."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('users.BankUser', on_delete=models.CASCADE, related_name='gdpr_requests')
    request_type = models.CharField(max_length=50, choices=[
        ('access','Right to Access'),
        ('erasure','Right to Erasure'),
        ('portability','Data Portability'),
        ('rectification','Rectification'),
        ('restriction','Restriction'),
        ('objection','Objection'),
    ])
    status = models.CharField(max_length=20, choices=[
        ('received','Received'), ('processing','Processing'),
        ('completed','Completed'), ('rejected','Rejected'),
    ], default='received')
    due_date = models.DateTimeField()
    response_data_cid = models.TextField(blank=True)
    processed_by = models.ForeignKey('users.BankUser', on_delete=models.SET_NULL, null=True, related_name='processed_gdpr')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'compliance_gdpr_request'


class AuditFinding(models.Model):
    """Internal/external audit findings."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    audit_type = models.CharField(max_length=50, choices=[
        ('internal','Internal Audit'),
        ('external','External Audit'),
        ('regulatory','Regulatory Examination'),
        ('penetration_test','Penetration Test'),
        ('iso_27001','ISO 27001 Audit'),
    ])
    finding_number = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=[
        ('observation','Observation'),
        ('minor','Minor'),
        ('major','Major'),
        ('critical','Critical'),
    ])
    recommendation = models.TextField()
    management_response = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[
        ('open','Open'), ('in_remediation','In Remediation'),
        ('resolved','Resolved'), ('accepted','Risk Accepted'),
    ], default='open')
    due_date = models.DateTimeField(null=True)
    owner = models.ForeignKey('users.BankUser', on_delete=models.SET_NULL, null=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compliance_audit_finding'


class CyberIncidentResponse(models.Model):
    """Cyber incident response tracking."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    incident_id = models.CharField(max_length=50, unique=True)
    incident_type = models.CharField(max_length=50, choices=[
        ('ransomware','Ransomware'),
        ('data_breach','Data Breach'),
        ('ddos','DDoS Attack'),
        ('apt','Advanced Persistent Threat'),
        ('insider','Insider Threat'),
        ('zero_day','Zero Day Exploit'),
        ('supply_chain','Supply Chain Attack'),
    ])
    severity = models.CharField(max_length=20, choices=[
        ('low','Low'), ('medium','Medium'),
        ('high','High'), ('critical','Critical'),
    ])
    affected_systems = models.JSONField(default=list)
    affected_users_count = models.PositiveIntegerField(default=0)
    containment_steps = models.JSONField(default=list)
    eradication_steps = models.JSONField(default=list)
    recovery_steps = models.JSONField(default=list)
    lessons_learned = models.TextField(blank=True)
    reported_to_ojk = models.BooleanField(default=False)
    reported_to_bssn = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=[
        ('detected','Detected'), ('contained','Contained'),
        ('eradicated','Eradicated'), ('recovered','Recovered'),
        ('closed','Closed'),
    ], default='detected')
    detected_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    lead_responder = models.ForeignKey('users.BankUser', on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = 'compliance_cyber_incident'


class PrivacyImpactAssessment(models.Model):
    """DPIA — Data Protection Impact Assessment."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project_name = models.CharField(max_length=255)
    data_types = models.JSONField(default=list)
    processing_purpose = models.TextField()
    legal_basis = models.CharField(max_length=100)
    risks_identified = models.JSONField(default=list)
    mitigations = models.JSONField(default=list)
    residual_risk = models.CharField(max_length=20, choices=[
        ('low','Low'), ('medium','Medium'), ('high','High'),
    ], default='low')
    dpo_approved = models.BooleanField(default=False)
    dpo_approved_by = models.ForeignKey('users.BankUser', on_delete=models.SET_NULL, null=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    review_date = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey('users.BankUser', on_delete=models.SET_NULL, null=True, related_name='created_dpias')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compliance_dpia'


class IncidentReport(models.Model):
    """Incident reports for remote work."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey('workspace.Workspace', on_delete=models.CASCADE, related_name='incidents')
    title = models.CharField(max_length=255)
    description = models.TextField()
    incident_type = models.CharField(max_length=50, choices=[
        ('bug','Bug'),
        ('outage','Service Outage'),
        ('security','Security Issue'),
        ('data_loss','Data Loss'),
        ('performance','Performance Issue'),
        ('other','Other'),
    ])
    severity = models.CharField(max_length=20, choices=[
        ('low','Low'), ('medium','Medium'),
        ('high','High'), ('critical','Critical'),
    ])
    status = models.CharField(max_length=20, choices=[
        ('open','Open'), ('investigating','Investigating'),
        ('resolved','Resolved'), ('closed','Closed'),
    ], default='open')
    reporter = models.ForeignKey('users.BankUser', on_delete=models.CASCADE, related_name='reported_incidents')
    assignee = models.ForeignKey('users.BankUser', on_delete=models.SET_NULL, null=True, related_name='assigned_incidents_rw')
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compliance_incident_report'


class IncidentTimeline(models.Model):
    """Timeline for incident resolution."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    incident = models.ForeignKey(IncidentReport, on_delete=models.CASCADE, related_name='timeline')
    action = models.TextField()
    actor = models.ForeignKey('users.BankUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compliance_incident_timeline'


class PostMortem(models.Model):
    """Post-mortem analysis."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    incident = models.OneToOneField(IncidentReport, on_delete=models.CASCADE, related_name='post_mortem')
    root_cause = models.TextField()
    impact = models.TextField()
    timeline = models.TextField()
    action_items = models.JSONField(default=list)
    lessons_learned = models.TextField()
    written_by = models.ForeignKey('users.BankUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compliance_post_mortem'


class OnCallSchedule(models.Model):
    """On-call schedule for remote teams."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey('workspace.Workspace', on_delete=models.CASCADE, related_name='oncall_schedules')
    user = models.ForeignKey('users.BankUser', on_delete=models.CASCADE, related_name='oncall_shifts')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_primary = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compliance_oncall_schedule'


class RunBook(models.Model):
    """Operational runbooks."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey('workspace.Workspace', on_delete=models.CASCADE, related_name='runbooks')
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=[
        ('deployment','Deployment'),
        ('incident','Incident Response'),
        ('onboarding','Onboarding'),
        ('maintenance','Maintenance'),
        ('security','Security'),
    ])
    steps = models.JSONField(default=list)
    content_encrypted_b64 = models.TextField()
    nonce_b64 = models.TextField()
    auth_tag_b64 = models.TextField()
    version = models.PositiveIntegerField(default=1)
    created_by = models.ForeignKey('users.BankUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'compliance_runbook'


class AuditExport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey('workspace.Workspace', on_delete=models.CASCADE, related_name='audit_exports')
    export_type = models.CharField(max_length=50)
    date_from = models.DateField()
    date_to = models.DateField()
    file_cid = models.TextField(blank=True)
    status = models.CharField(max_length=20, default='pending')
    requested_by = models.ForeignKey('users.BankUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = 'compliance_audit_export'

class PolicyDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey('workspace.Workspace', on_delete=models.CASCADE, related_name='policies')
    title = models.CharField(max_length=255)
    policy_type = models.CharField(max_length=50, choices=[('privacy','Privacy Policy'),('security','Security Policy'),('acceptable_use','Acceptable Use'),('data_retention','Data Retention'),('remote_work','Remote Work Policy')])
    content_encrypted_b64 = models.TextField()
    nonce_b64 = models.TextField()
    auth_tag_b64 = models.TextField()
    version = models.CharField(max_length=20, default='1.0')
    effective_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey('users.BankUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = 'compliance_policy'

class PolicyAcknowledgement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    policy = models.ForeignKey(PolicyDocument, on_delete=models.CASCADE, related_name='acknowledgements')
    user = models.ForeignKey('users.BankUser', on_delete=models.CASCADE)
    acknowledged_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'compliance_policy_ack'
        unique_together = ['policy', 'user']

class ComplianceChecklist(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey('workspace.Workspace', on_delete=models.CASCADE, related_name='checklists')
    title = models.CharField(max_length=255)
    items = models.JSONField(default=list)
    frequency = models.CharField(max_length=20, choices=[('daily','Daily'),('weekly','Weekly'),('monthly','Monthly'),('quarterly','Quarterly')])
    last_completed = models.DateTimeField(null=True)
    next_due = models.DateTimeField(null=True)
    assigned_to = models.ForeignKey('users.BankUser', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = 'compliance_checklist'

class ComplianceChecklistRun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    checklist = models.ForeignKey(ComplianceChecklist, on_delete=models.CASCADE, related_name='runs')
    completed_items = models.JSONField(default=list)
    notes = models.TextField(blank=True)
    completed_by = models.ForeignKey('users.BankUser', on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = 'compliance_checklist_run'

class DataAccessRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey('workspace.Workspace', on_delete=models.CASCADE)
    requester = models.ForeignKey('users.BankUser', on_delete=models.CASCADE, related_name='data_requests')
    request_type = models.CharField(max_length=50, choices=[('export','Data Export'),('deletion','Data Deletion'),('correction','Data Correction'),('access','Data Access')])
    description = models.TextField()
    status = models.CharField(max_length=20, default='pending')
    processed_by = models.ForeignKey('users.BankUser', on_delete=models.SET_NULL, null=True, related_name='processed_requests')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True)
    class Meta: db_table = 'compliance_data_request'

class SecurityScan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey('workspace.Workspace', on_delete=models.CASCADE, related_name='security_scans')
    scan_type = models.CharField(max_length=50, choices=[('vulnerability','Vulnerability'),('penetration','Penetration Test'),('code_review','Code Review'),('config_audit','Config Audit')])
    status = models.CharField(max_length=20, default='running')
    findings = models.JSONField(default=list)
    score = models.FloatField(default=0.0)
    initiated_by = models.ForeignKey('users.BankUser', on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True)
    class Meta: db_table = 'compliance_security_scan'

class NotificationRule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey('workspace.Workspace', on_delete=models.CASCADE, related_name='notification_rules')
    name = models.CharField(max_length=100)
    trigger_type = models.CharField(max_length=50)
    conditions = models.JSONField(default=dict)
    channels = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey('users.BankUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = 'compliance_notification_rule'

class SystemLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey('workspace.Workspace', on_delete=models.CASCADE, null=True)
    level = models.CharField(max_length=10, choices=[('DEBUG','DEBUG'),('INFO','INFO'),('WARNING','WARNING'),('ERROR','ERROR'),('CRITICAL','CRITICAL')])
    service = models.CharField(max_length=50)
    message = models.TextField()
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = 'compliance_system_log'

class AlertRule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey('workspace.Workspace', on_delete=models.CASCADE, related_name='alert_rules')
    name = models.CharField(max_length=100)
    metric = models.CharField(max_length=50)
    threshold = models.FloatField()
    comparison = models.CharField(max_length=10, choices=[('gt','Greater Than'),('lt','Less Than'),('eq','Equal')])
    severity = models.CharField(max_length=20, default='warning')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey('users.BankUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = 'compliance_alert_rule'

class AlertInstance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE, related_name='instances')
    value = models.FloatField()
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = 'compliance_alert_instance'


class ImmutableAuditLog(models.Model):
    """Audit log yang tidak bisa dimanipulasi - standar OJK/BI"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50, db_index=True)
    sender_id = models.CharField(max_length=50)
    receiver_id = models.CharField(max_length=50, blank=True)
    message_hash = models.CharField(max_length=64)  # SHA-256
    channel = models.CharField(max_length=100)
    action = models.CharField(max_length=50)  # sent, deleted, edited, read
    device_info = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True)
    prev_hash = models.CharField(max_length=64)  # Hash dari log sebelumnya
    chain_hash = models.CharField(max_length=64, unique=True)  # Hash entry ini
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'compliance_immutable_audit'
        app_label = 'compliance'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.action} by {self.sender_id} at {self.created_at}"

class ShamirKeyShare(models.Model):
    """Shamir's Secret Sharing - pecah master key jadi 3 bagian"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    share_index = models.PositiveSmallIntegerField()  # 1, 2, atau 3
    share_holder = models.CharField(max_length=100)  # Direktur Kepatuhan, Head IT, dll
    share_holder_id = models.CharField(max_length=50)
    encrypted_share = models.TextField()  # Share terenkripsi
    threshold = models.PositiveSmallIntegerField(default=2)  # Minimal 2 dari 3
    total_shares = models.PositiveSmallIntegerField(default=3)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'compliance_shamir_share'
        app_label = 'compliance'
        unique_together = ['workspace_id', 'share_index']

class ChannelPolicy(models.Model):
    """Kebijakan channel - self-destruct boleh/tidak"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    channel_name = models.CharField(max_length=100)
    channel_type = models.CharField(max_length=20, choices=[
        ('general', 'General Chat'),
        ('official', 'Official Instruction'),
        ('operational', 'Operational'),
    ], default='general')
    allow_self_destruct = models.BooleanField(default=True)
    retention_days = models.PositiveIntegerField(default=365)  # Retensi data
    require_audit = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'compliance_channel_policy'
        app_label = 'compliance'
        unique_together = ['workspace_id', 'channel_name']

class EmergencyAccessLog(models.Model):
    """Log akses darurat - ketika 2 dari 3 pemegang kunci setuju"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50)
    requested_by = models.CharField(max_length=50)
    reason = models.TextField()
    approver_1 = models.CharField(max_length=50, blank=True)
    approver_2 = models.CharField(max_length=50, blank=True)
    approved_at = models.DateTimeField(null=True)
    target_user_id = models.CharField(max_length=50)
    access_granted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'compliance_emergency_access'
        app_label = 'compliance'
import uuid
from django.db import models
from django.conf import settings


class OJKIncidentReport(models.Model):
    """Auto-report insiden siber ke OJK maksimal 24 jam."""
    SEVERITY = [('low','Low'),('medium','Medium'),('high','High'),('critical','Critical')]
    STATUS = [('draft','Draft'),('submitted','Submitted'),('acknowledged','Acknowledged'),('failed','Failed')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey('workspace.Workspace', on_delete=models.CASCADE, related_name='ojk_reports')
    incident_type = models.CharField(max_length=100)
    severity = models.CharField(max_length=20, choices=SEVERITY)
    description = models.TextField()
    affected_systems = models.JSONField(default=list)
    affected_users_count = models.PositiveIntegerField(default=0)
    detected_at = models.DateTimeField()
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS, default='draft')
    ojk_reference_number = models.CharField(max_length=100, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    deadline_at = models.DateTimeField(help_text="24 jam sejak detected_at")
    auto_submitted = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compliance_ojk_incident'
        ordering = ['-created_at']


class InformationBarrier(models.Model):
    """Ethical walls — blokir komunikasi antar divisi."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey('workspace.Workspace', on_delete=models.CASCADE, related_name='info_barriers')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    blocked_departments = models.JSONField(default=list, help_text="Pasangan divisi yang diblokir")
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compliance_info_barrier'


class RemoteWipeRequest(models.Model):
    """Admin bisa wipe data app di device karyawan dari jauh."""
    STATUS = [('pending','Pending'),('executed','Executed'),('cancelled','Cancelled')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    target_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wipe_requests')
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='issued_wipes')
    reason = models.TextField()
    device_token = models.CharField(max_length=256, blank=True, help_text="Target device token")
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    executed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compliance_remote_wipe'


class SecureFileLink(models.Model):
    """File link terenkripsi dengan expiry + password."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='secure_links')
    workspace = models.ForeignKey('workspace.Workspace', on_delete=models.CASCADE)
    filename = models.CharField(max_length=256)
    file_size_bytes = models.BigIntegerField(default=0)
    ipfs_cid = models.CharField(max_length=128, blank=True)
    token_hash = models.CharField(max_length=256, unique=True)
    password_hash = models.CharField(max_length=256, blank=True)
    expires_at = models.DateTimeField()
    max_downloads = models.PositiveIntegerField(default=1)
    download_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    access_log = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compliance_secure_file_link'


class DLPRule(models.Model):
    """Data Loss Prevention rules."""
    ACTIONS = [('block','Block'),('warn','Warn'),('log','Log Only')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey('workspace.Workspace', on_delete=models.CASCADE, related_name='dlp_rules')
    name = models.CharField(max_length=100)
    pattern = models.TextField(help_text="Regex pattern untuk deteksi data sensitif")
    data_type = models.CharField(max_length=50, choices=[
        ('credit_card','Credit Card'),('nik','NIK'),('account_number','Account Number'),
        ('phone','Phone Number'),('custom','Custom'),
    ])
    action = models.CharField(max_length=10, choices=ACTIONS, default='block')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compliance_dlp_rule'


class HelpdeskTicket(models.Model):
    """Helpdesk ticketing terintegrasi."""
    PRIORITY = [('low','Low'),('medium','Medium'),('high','High'),('critical','Critical')]
    STATUS = [('open','Open'),('in_progress','In Progress'),('resolved','Resolved'),('closed','Closed')]
    CATEGORY = [('hardware','Hardware'),('software','Software'),('network','Network'),('security','Security'),('other','Other')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket_number = models.CharField(max_length=20, unique=True)
    workspace = models.ForeignKey('workspace.Workspace', on_delete=models.CASCADE, related_name='tickets')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tickets')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')
    title = models.CharField(max_length=256)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY, default='other')
    priority = models.CharField(max_length=10, choices=PRIORITY, default='medium')
    status = models.CharField(max_length=20, choices=STATUS, default='open')
    channel_id = models.CharField(max_length=100, blank=True, help_text="Linked messaging channel")
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'compliance_helpdesk_ticket'
        ordering = ['-created_at']


class HelpdeskComment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(HelpdeskTicket, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    is_internal = models.BooleanField(default=False, help_text="Internal IT note, tidak terlihat user")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compliance_helpdesk_comment'


class InstitutionBadge(models.Model):
    """Verified Institution Badge untuk inter-bank."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.OneToOneField('workspace.Workspace', on_delete=models.CASCADE, related_name='institution_badge')
    institution_name = models.CharField(max_length=200)
    institution_code = models.CharField(max_length=20, unique=True, help_text="Kode bank BI")
    verified_by = models.CharField(max_length=100, help_text="OJK/BI verifier name")
    verified_at = models.DateTimeField()
    badge_level = models.CharField(max_length=20, choices=[
        ('verified','Verified'),('premium','Premium Institution'),('regulator','Regulator'),
    ], default='verified')
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compliance_institution_badge'
