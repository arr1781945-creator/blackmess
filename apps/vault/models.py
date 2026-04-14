"""
apps/vault/models.py
VAULT — 5 isolated tables for ultra-sensitive banking data.
Each table uses separate DB schema isolation where possible.
Row-level encryption: every sensitive field is AES-256-GCM encrypted
before storage. The vault app uses a separate database connection.

TABLES:
  1. UserKYCVault          — Encrypted KYC documents & identity data
  2. CorporateIDVault      — Corporate identity & registration docs
  3. HardwareKeyRegistry   — USB hardware key registrations (2 keys per user)
  4. EncryptedBlobStore    — Generic encrypted binary blobs (IPFS-backed)
  5. AccessSession         — Vault access sessions (TTL-bound, hardware-keyed)
"""

import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class UserKYCVault(models.Model):
    """
    Encrypted KYC record for each bank user.
    Clearance Level 3+ required to access.
    All PII fields encrypted at the application layer before DB write.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="kyc_vault"
    )

    # All text fields = AES-256-GCM(base64) — never plaintext
    full_name_enc = models.TextField(help_text="Encrypted legal full name")
    date_of_birth_enc = models.TextField(help_text="Encrypted DOB (ISO format)")
    nationality_enc = models.TextField(help_text="Encrypted nationality code")
    id_type = models.CharField(
        max_length=16,
        choices=[("passport", "Passport"), ("national_id", "National ID"), ("driving_license", "Driving License")],
    )
    id_number_enc = models.TextField(help_text="Encrypted ID number")
    id_expiry_enc = models.TextField(help_text="Encrypted expiry date")
    id_document_ipfs_cid = models.CharField(max_length=128, blank=True, help_text="Encrypted scan stored on IPFS")
    address_enc = models.TextField(blank=True, help_text="Encrypted residential address")
    tax_id_enc = models.TextField(blank=True, help_text="Encrypted tax identification number")

    # Status
    kyc_status = models.CharField(
        max_length=16, default="pending",
        choices=[("pending", "Pending"), ("verified", "Verified"), ("rejected", "Rejected"), ("expired", "Expired")]
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="kyc_verifications"
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Encryption metadata
    key_version = models.PositiveSmallIntegerField(default=1, help_text="AES key rotation version")

    class Meta:
        db_table = "vault_kyc"
        verbose_name = "KYC Vault Record"
        indexes = [
            models.Index(fields=["kyc_status"]),
            models.Index(fields=["verified_at"]),
        ]


class CorporateIDVault(models.Model):
    """
    Corporate identity vault — for institutional/corporate users.
    Contains encrypted registration documents and authorised signatories.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.OneToOneField(
        "workspace.Workspace", on_delete=models.CASCADE, related_name="corporate_vault"
    )

    company_name_enc = models.TextField()
    registration_number_enc = models.TextField()
    registration_country_enc = models.TextField()
    registration_date_enc = models.TextField()
    registered_address_enc = models.TextField()
    tax_number_enc = models.TextField(blank=True)

    # Authorised signatories (JSON array of encrypted user IDs + roles)
    authorised_signatories_enc = models.TextField(help_text="Encrypted JSON array")

    # Documents (IPFS CIDs for encrypted files)
    certificate_of_incorporation_cid = models.CharField(max_length=128, blank=True)
    memorandum_of_association_cid = models.CharField(max_length=128, blank=True)
    board_resolution_cid = models.CharField(max_length=128, blank=True)

    verification_status = models.CharField(
        max_length=16, default="pending",
        choices=[("pending", "Pending"), ("verified", "Verified"), ("under_review", "Under Review")]
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="corporate_verifications"
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    key_version = models.PositiveSmallIntegerField(default=1)

    class Meta:
        db_table = "vault_corporate_id"
        verbose_name = "Corporate ID Vault"


class HardwareKeyRegistry(models.Model):
    """
    USB Hardware Security Key registry.
    Each user may register up to 2 hardware keys.
    Used as the second factor for vault access (beyond TOTP).
    Supports FIDO2/WebAuthn and PIV smart card formats.
    """
    KEY_TYPE_CHOICES = [
        ("fido2_yubikey",  "FIDO2 YubiKey"),
        ("fido2_generic",  "FIDO2 Generic"),
        ("piv_smart_card", "PIV Smart Card"),
        ("pkcs11_token",   "PKCS#11 Token"),
    ]
    SLOT_CHOICES = [(1, "Primary Key"), (2, "Backup Key")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="hardware_keys"
    )
    slot = models.PositiveSmallIntegerField(choices=SLOT_CHOICES)
    key_type = models.CharField(max_length=16, choices=KEY_TYPE_CHOICES)
    label = models.CharField(max_length=64, help_text="User-visible label e.g. r'YubiKey 5C NFC'")

    # FIDO2 credential data (encrypted)
    credential_id_enc = models.TextField(help_text="Encrypted FIDO2 credential ID")
    public_key_enc = models.TextField(help_text="Encrypted COSE public key")
    aaguid = models.CharField(max_length=64, blank=True, help_text="Authenticator AAGUID")

    # USB device identifiers
    vendor_id = models.CharField(max_length=8, blank=True, help_text="USB Vendor ID hex e.g. 0x1050")
    product_id = models.CharField(max_length=8, blank=True, help_text="USB Product ID hex e.g. 0x0407")
    serial_number_enc = models.TextField(blank=True, help_text="Encrypted device serial number")

    sign_count = models.PositiveBigIntegerField(default=0, help_text="FIDO2 signature counter — detects cloning")
    is_active = models.BooleanField(default=True)
    registered_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "vault_hardware_key"
        unique_together = [("user", "slot")]
        verbose_name = "Hardware Key Registry"
        indexes = [models.Index(fields=["user", "is_active"])]

    def __str__(self):
        return f"{self.user.username} — Slot {self.slot}: {self.label}"


class EncryptedBlobStore(models.Model):
    """
    Generic encrypted binary blob storage — backed by IPFS.
    Used for: signed documents, certificates, audit evidence, secure notes.
    Access requires vault session + clearance level 3+.
    """
    BLOB_TYPE_CHOICES = [
        ("document",    "Document"),
        ("certificate", "Certificate"),
        ("evidence",    "Audit Evidence"),
        ("secure_note", "Secure Note"),
        ("key_backup",  "Key Backup"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="vault_blobs"
    )
    workspace = models.ForeignKey(
        "workspace.Workspace", on_delete=models.CASCADE,
        null=True, blank=True, related_name="vault_blobs"
    )
    blob_type = models.CharField(max_length=16, choices=BLOB_TYPE_CHOICES)
    label = models.CharField(max_length=128)
    description_enc = models.TextField(blank=True, help_text="Encrypted description")

    # Storage
    ipfs_cid = models.CharField(max_length=128, db_index=True, help_text="IPFS CID of encrypted blob")
    content_type = models.CharField(max_length=128)
    size_bytes = models.PositiveBigIntegerField()

    # Per-blob encryption (separate key from message E2EE)
    blob_key_enc = models.TextField(help_text="Blob AES key, encrypted with owner's Kyber public key")
    blob_nonce_b64 = models.CharField(max_length=32)
    blob_tag_b64 = models.CharField(max_length=32)
    checksum_sha256 = models.CharField(max_length=64)

    # Access control
    min_clearance = models.PositiveSmallIntegerField(default=3)
    shared_with = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="shared_vault_blobs"
    )

    # Lifecycle
    ttl_seconds = models.PositiveIntegerField(null=True, blank=True)
    destroy_at = models.DateTimeField(null=True, blank=True, db_index=True)
    is_destroyed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    key_version = models.PositiveSmallIntegerField(default=1)

    class Meta:
        db_table = "vault_blob_store"
        verbose_name = "Encrypted Blob Store"
        indexes = [
            models.Index(fields=["owner", "blob_type"]),
            models.Index(fields=["destroy_at"]),
        ]


class AccessSession(models.Model):
    """
    Vault Access Session — created when a user opens the vault.
    Requires:
      - MFA verified
      - Hardware key challenge-response
      - Clearance Level ≥ 3
    Session is TTL-bound (default 1 hour). All vault actions require
    a valid AccessSession token.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="vault_sessions"
    )
    hardware_key = models.ForeignKey(
        HardwareKeyRegistry, on_delete=models.SET_NULL,
        null=True, related_name="vault_sessions"
    )

    session_token_hash = models.CharField(max_length=256, unique=True, db_index=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=512, blank=True)

    # FIDO2 assertion for session opening
    fido2_challenge_b64 = models.TextField(blank=True)
    fido2_assertion_b64 = models.TextField(blank=True)

    opened_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)
    last_action_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True)
    closed_reason = models.CharField(max_length=64, blank=True)

    # Audit: list of actions performed during this session
    action_log = models.JSONField(default=list)

    class Meta:
        db_table = "vault_access_session"
        verbose_name = "Vault Access Session"
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["expires_at"]),
        ]

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    def append_action(self, action: str, detail: dict = None):
        self.action_log.append({
            "action": action,
            "at": timezone.now().isoformat(),
            "detail": detail or {},
        })
        self.save(update_fields=["action_log", "last_action_at"])


# ─── Key Management Tables ───────────────────────────────────────────────────

class KeyRotationLog(models.Model):
    """Track key rotation history."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE, related_name='key_rotations')
    key_type = models.CharField(max_length=50)
    old_key_fingerprint = models.CharField(max_length=64)
    new_key_fingerprint = models.CharField(max_length=64)
    reason = models.CharField(max_length=100, default=r'scheduled')
    rotated_by = models.ForeignKey(r'users.BankUser', on_delete=models.SET_NULL, null=True, related_name='rotations_performed')
    rotated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'vault_key_rotation_log'


class KeyEscrow(models.Model):
    """Encrypted key backup for compliance."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE, related_name='key_escrows')
    key_type = models.CharField(max_length=50)
    encrypted_key_b64 = models.TextField()
    escrow_nonce_b64 = models.TextField()
    escrow_tag_b64 = models.TextField()
    custodian = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'vault_key_escrow'


class MasterKeyVersion(models.Model):
    """Master key versioning."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    version = models.PositiveIntegerField(unique=True)
    key_fingerprint = models.CharField(max_length=64)
    algorithm = models.CharField(max_length=50, default=r'AES-256-GCM')
    is_active = models.BooleanField(default=False)
    activated_at = models.DateTimeField(null=True, blank=True)
    retired_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'vault_master_key_version'


class KeyAccessLog(models.Model):
    """Audit log for key access."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE, related_name='key_access_logs')
    key_type = models.CharField(max_length=50)
    action = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField(null=True)
    success = models.BooleanField(default=True)
    accessed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'vault_key_access_log'


class KeyDerivationParams(models.Model):
    """HKDF derivation parameters per channel."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.OneToOneField(r'workspace.Channel', on_delete=models.CASCADE, related_name='key_params')
    salt_b64 = models.TextField()
    info_b64 = models.TextField()
    algorithm = models.CharField(max_length=50, default=r'HKDF-SHA512')
    created_at = models.DateTimeField(auto_now_add=True)
    rotated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = r'vault_key_derivation_params'


# ─── Digital Signature ───────────────────────────────────────────────────────

class DocumentSignature(models.Model):
    """Digital signature untuk dokumen kontrak."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document_hash = models.CharField(max_length=64)
    document_name = models.CharField(max_length=255)
    document_cid = models.TextField(blank=True)
    signer = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE, related_name='signatures')
    signature_b64 = models.TextField()
    signature_algorithm = models.CharField(max_length=50, default=r'Dilithium3')
    public_key_fingerprint = models.CharField(max_length=64)
    is_valid = models.BooleanField(default=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    signed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'vault_document_signature'


class MultiPartySignature(models.Model):
    """Multi-party document signing — kontrak multi pihak."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document_hash = models.CharField(max_length=64)
    document_name = models.CharField(max_length=255)
    required_signers = models.ManyToManyField(r'users.BankUser', related_name='pending_signatures')
    completed_signatures = models.ManyToManyField(DocumentSignature, related_name=r'multi_party')
    is_complete = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    deadline = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'vault_multi_party_signature'


class SWIFTMessage(models.Model):
    """SWIFT MT/MX message integration."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message_type = models.CharField(max_length=10)
    sender_bic = models.CharField(max_length=11)
    receiver_bic = models.CharField(max_length=11)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    currency = models.CharField(max_length=3)
    reference = models.CharField(max_length=50, unique=True)
    encrypted_payload_b64 = models.TextField()
    status = models.CharField(max_length=20, choices=[
        (r'pending','Pending'), ('sent','Sent'),
        (r'acknowledged','Acknowledged'), ('rejected','Rejected'),
    ], default=r'pending')
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = r'vault_swift_message'


class HSMKeySlot(models.Model):
    """Hardware Security Module key slots."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slot_id = models.PositiveIntegerField(unique=True)
    label = models.CharField(max_length=100)
    key_type = models.CharField(max_length=50, choices=[
        (r'rsa_4096','RSA-4096'),
        (r'ecdsa_p384','ECDSA-P384'),
        (r'aes_256','AES-256'),
        (r'kyber_1024','Kyber-1024'),
        (r'ml_dsa_65','Dilithium3'),
    ])
    key_fingerprint = models.CharField(max_length=64, blank=True)
    is_active = models.BooleanField(default=True)
    usage_count = models.BigIntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = r'vault_hsm_key_slot'


class SecureEnvelope(models.Model):
    """Encrypted envelope untuk dokumen sensitif."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE, related_name='sent_envelopes')
    recipient = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE, related_name='received_envelopes')
    subject_encrypted_b64 = models.TextField()
    content_cid = models.TextField()
    kyber_ciphertext_b64 = models.TextField()
    nonce_b64 = models.TextField()
    auth_tag_b64 = models.TextField()
    dilithium_signature_b64 = models.TextField(blank=True)
    is_opened = models.BooleanField(default=False)
    opened_at = models.DateTimeField(null=True, blank=True)
    destroy_after_read = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'vault_secure_envelope'


class CertificateAuthority(models.Model):
    """Internal CA for issuing certificates."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    certificate_pem = models.TextField()
    public_key_b64 = models.TextField()
    is_root = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    issued_by = models.ForeignKey(r'self', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'vault_certificate_authority'


class IssuedCertificate(models.Model):
    """Certificates issued to users/services."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ca = models.ForeignKey(CertificateAuthority, on_delete=models.CASCADE, related_name=r'issued_certs')
    user = models.ForeignKey(r'users.BankUser', on_delete=models.SET_NULL, null=True, related_name='certificates')
    serial_number = models.CharField(max_length=50, unique=True)
    subject = models.CharField(max_length=255)
    certificate_pem = models.TextField()
    public_key_b64 = models.TextField()
    is_revoked = models.BooleanField(default=False)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoke_reason = models.CharField(max_length=100, blank=True)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'vault_issued_certificate'


class TokenVault(models.Model):
    """Tokenization vault — simpan data sensitif sebagai token."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.CharField(max_length=64, unique=True)
    data_type = models.CharField(max_length=50, choices=[
        (r'card_number','Card Number'),
        (r'account_number','Account Number'),
        (r'swift_bic','SWIFT BIC'),
        (r'iban','IBAN'),
        (r'ssn','SSN/NIK'),
    ])
    encrypted_value_b64 = models.TextField()
    nonce_b64 = models.TextField()
    auth_tag_b64 = models.TextField()
    user = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE, related_name='tokens')
    usage_count = models.PositiveIntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'vault_token'


class SecureNotepad(models.Model):
    """Encrypted secure notepad per user."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE, related_name='secure_notes')
    title_encrypted_b64 = models.TextField()
    content_encrypted_b64 = models.TextField()
    nonce_b64 = models.TextField()
    auth_tag_b64 = models.TextField()
    category = models.CharField(max_length=50, choices=[
        (r'credentials','Credentials'),
        (r'meeting_notes','Meeting Notes'),
        (r'deal_notes','Deal Notes'),
        (r'personal','Personal'),
        (r'compliance','Compliance'),
    ], default=r'personal')
    is_pinned = models.BooleanField(default=False)
    destroy_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = r'vault_secure_notepad'


class VaultAccessPolicy(models.Model):
    """Fine-grained vault access policies."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    resource_type = models.CharField(max_length=50, choices=[
        (r'kyc','KYC Records'),
        (r'blob','Blob Store'),
        (r'signature','Digital Signatures'),
        (r'certificate','Certificates'),
        (r'token','Token Vault'),
        (r'notepad','Secure Notepad'),
    ])
    allowed_roles = models.JSONField(default=list)
    min_clearance = models.PositiveSmallIntegerField(default=1)
    requires_mfa = models.BooleanField(default=True)
    requires_hardware_key = models.BooleanField(default=False)
    time_restrictions = models.JSONField(default=dict)
    ip_restrictions = models.JSONField(default=list)
    created_by = models.ForeignKey(r'users.BankUser', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'vault_access_policy'


class DisasterRecoveryPlan(models.Model):
    """Disaster recovery and BCP plans."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan_name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=50, choices=[
        (r'bcp','Business Continuity Plan'),
        (r'drp','Disaster Recovery Plan'),
        (r'irp','Incident Response Plan'),
        (r'crisis','Crisis Management'),
    ])
    rto_minutes = models.PositiveIntegerField(default=60)
    rpo_minutes = models.PositiveIntegerField(default=30)
    steps = models.JSONField(default=list)
    contacts = models.JSONField(default=list)
    last_tested = models.DateTimeField(null=True, blank=True)
    next_test = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    approved_by = models.ForeignKey(r'users.BankUser', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = r'vault_disaster_recovery'


class SecureSharing(models.Model):
    """Secure time-limited file sharing."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shared_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE, related_name='shared_items')
    shared_with = models.ManyToManyField(r'users.BankUser', related_name='received_shares')
    resource_type = models.CharField(max_length=50)
    resource_id = models.CharField(max_length=50)
    access_token = models.CharField(max_length=64, unique=True)
    max_access_count = models.PositiveIntegerField(default=1)
    access_count = models.PositiveIntegerField(default=0)
    requires_mfa = models.BooleanField(default=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'vault_secure_sharing'


class DigitalAssetCustody(models.Model):
    """Digital asset custody — crypto/CBDC."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE, related_name='digital_assets')
    asset_type = models.CharField(max_length=50, choices=[
        (r'bitcoin','Bitcoin'),
        (r'ethereum','Ethereum'),
        (r'cbdc','CBDC'),
        (r'stablecoin','Stablecoin'),
        (r'tokenized_asset','Tokenized Asset'),
    ])
    wallet_address_encrypted_b64 = models.TextField()
    private_key_encrypted_b64 = models.TextField()
    nonce_b64 = models.TextField()
    auth_tag_b64 = models.TextField()
    balance = models.DecimalField(max_digits=30, decimal_places=18, default=0)
    is_cold_storage = models.BooleanField(default=True)
    custodian = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = r'vault_digital_asset'


class CBDCTransaction(models.Model):
    """Central Bank Digital Currency transactions."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE, related_name='cbdc_sent')
    receiver = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE, related_name='cbdc_received')
    amount = models.DecimalField(max_digits=30, decimal_places=8)
    currency = models.CharField(max_length=10, default=r'e-IDR')
    transaction_hash = models.CharField(max_length=64, unique=True)
    block_number = models.BigIntegerField(null=True)
    smart_contract_address = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=[
        (r'pending','Pending'), ('confirmed','Confirmed'),
        (r'failed','Failed'), ('reversed','Reversed'),
    ], default=r'pending')
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = r'vault_cbdc_transaction'


class SmartContractAudit(models.Model):
    """Smart contract audit records."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract_address = models.CharField(max_length=100)
    contract_name = models.CharField(max_length=100)
    audit_type = models.CharField(max_length=50, choices=[
        (r'security','Security Audit'),
        (r'compliance','Compliance Audit'),
        (r'functional','Functional Audit'),
    ])
    vulnerabilities_found = models.PositiveIntegerField(default=0)
    critical_issues = models.PositiveIntegerField(default=0)
    audit_report_cid = models.TextField(blank=True)
    audited_by = models.ForeignKey(r'users.BankUser', on_delete=models.SET_NULL, null=True)
    passed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'vault_smart_contract_audit'


class QuantumKeyDistribution(models.Model):
    """QKD — Quantum Key Distribution sessions."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    initiator = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE, related_name='qkd_initiated')
    responder = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE, related_name='qkd_responded')
    protocol = models.CharField(max_length=50, choices=[
        (r'bb84','BB84'),
        (r'e91','E91'),
        (r'b92','B92'),
        (r'sarg04','SARG04'),
    ], default=r'bb84')
    key_length_bits = models.PositiveIntegerField(default=256)
    qber = models.FloatField(default=0.0)
    is_secure = models.BooleanField(default=True)
    session_key_hash = models.CharField(max_length=64, blank=True)
    established_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = r'vault_quantum_key_distribution'


class PostQuantumMigration(models.Model):
    """Track PQC migration status per user/service."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE, related_name='pqc_migrations')
    migration_type = models.CharField(max_length=50, choices=[
        (r'key_generation','Key Generation'),
        (r'key_exchange','Key Exchange'),
        (r'signature','Signature'),
        (r'encryption','Encryption'),
    ])
    from_algorithm = models.CharField(max_length=50)
    to_algorithm = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=[
        (r'pending','Pending'), ('in_progress','In Progress'),
        (r'completed','Completed'), ('failed','Failed'),
    ], default=r'pending')
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'vault_pqc_migration'


class PasswordVault(models.Model):
    """Encrypted password vault."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE, related_name='passwords')
    service_name = models.CharField(max_length=100)
    username_encrypted_b64 = models.TextField()
    password_encrypted_b64 = models.TextField()
    url = models.URLField(blank=True)
    nonce_b64 = models.TextField()
    auth_tag_b64 = models.TextField()
    notes_encrypted_b64 = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=[
        (r'work','Work'),
        (r'personal','Personal'),
        (r'social','Social'),
        (r'finance','Finance'),
        (r'other','Other'),
    ], default=r'work')
    last_used = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = r'vault_password'


class SSHKey(models.Model):
    """Encrypted SSH keys."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE, related_name='ssh_keys')
    name = models.CharField(max_length=100)
    public_key = models.TextField()
    private_key_encrypted_b64 = models.TextField()
    nonce_b64 = models.TextField()
    auth_tag_b64 = models.TextField()
    key_type = models.CharField(max_length=20, choices=[
        (r'rsa','RSA'),
        (r'ed25519','Ed25519'),
        (r'ecdsa','ECDSA'),
    ], default=r'ed25519')
    passphrase_hint = models.CharField(max_length=100, blank=True)
    servers = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'vault_ssh_key'


class APIKeyVault(models.Model):
    """Encrypted API keys."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE, related_name='api_keys_vault')
    service = models.CharField(max_length=100)
    key_name = models.CharField(max_length=100)
    api_key_encrypted_b64 = models.TextField()
    nonce_b64 = models.TextField()
    auth_tag_b64 = models.TextField()
    environment = models.CharField(max_length=20, choices=[
        (r'production','Production'),
        (r'staging','Staging'),
        (r'development','Development'),
    ], default=r'development')
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'vault_api_key'


class EnvironmentSecret(models.Model):
    """Team environment secrets."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(r'workspace.Workspace', on_delete=models.CASCADE, related_name='env_secrets')
    key_name = models.CharField(max_length=100)
    value_encrypted_b64 = models.TextField()
    nonce_b64 = models.TextField()
    auth_tag_b64 = models.TextField()
    environment = models.CharField(max_length=20, choices=[
        (r'production','Production'),
        (r'staging','Staging'),
        (r'development','Development'),
    ])
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = r'vault_env_secret'
        unique_together = [r'workspace', 'key_name', 'environment']


class SharedSecret(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(r'workspace.Workspace', on_delete=models.CASCADE, related_name='shared_secrets')
    name = models.CharField(max_length=100)
    value_encrypted_b64 = models.TextField()
    nonce_b64 = models.TextField()
    auth_tag_b64 = models.TextField()
    shared_with = models.ManyToManyField(r'users.BankUser', related_name='shared_secrets_access', blank=True)
    created_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    expires_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'vault_shared_secret'

class VaultAuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE, related_name='vault_audit')
    action = models.CharField(max_length=50)
    resource_type = models.CharField(max_length=50)
    resource_id = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'vault_audit'

class WorkspaceBackup(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(r'workspace.Workspace', on_delete=models.CASCADE, related_name='backups')
    backup_type = models.CharField(max_length=20, choices=[(r'full','Full'),('incremental','Incremental'),('messages','Messages Only'),('files','Files Only')])
    size_bytes = models.BigIntegerField(default=0)
    storage_cid = models.TextField(blank=True)
    status = models.CharField(max_length=20, default=r'pending')
    created_by = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True)
    class Meta: db_table = r'vault_workspace_backup'

class TwoFactorBackupCode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE, related_name='backup_codes')
    code_hash = models.CharField(max_length=64)
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'vault_2fa_backup_code'

class TrustedDevice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(r'users.BankUser', on_delete=models.CASCADE, related_name='vault_trusted_devices')
    device_name = models.CharField(max_length=100)
    device_token_hash = models.CharField(max_length=64, unique=True)
    last_used = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = r'vault_trusted_device'
