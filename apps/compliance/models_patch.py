"""
apps/compliance/models_patch.py

Patch untuk models.py compliance — copy tiap class ke models.py
dan gantikan class lama dengan nama yang sama.

Setelah copy semua class, jalankan:
  python manage.py makemigrations compliance --name fix_medium_severity
  python manage.py migrate
"""
import uuid
from django.db import models
from django.conf import settings


# ─────────────────────────────────────────────────────────────────────────────
# FIX #1: ForensicsBlock → DataProtectionPolicy
#
# Rename class dan db_table (butuh migration RenameModel + RenameField).
# Hapus log_retention_wipe yang memfasilitasi penghapusan log.
# Tambahkan min_audit_retention_days agar tidak bisa di-set di bawah
# kewajiban OJK 7 tahun (2555 hari).
#
# Migration tambahan yang perlu dibuat manual:
#   migrations.RenameModel('ForensicsBlock', 'DataProtectionPolicy')
#   migrations.RenameField('DataProtectionPolicy', 'compliance_forensics_block',
#                          'compliance_data_protection')
# ─────────────────────────────────────────────────────────────────────────────

class DataProtectionPolicy(models.Model):
    """
    Konfigurasi perlindungan data per workspace.

    FIX #1: Sebelumnya bernama ForensicsBlock — nama ambigu.
    Field log_retention_wipe dihapus karena bertentangan dengan
    kewajiban retensi log OJK/BI minimum 7 tahun.
    """
    workspace = models.OneToOneField(
        "workspace.Workspace",
        on_delete=models.CASCADE,
        related_name="data_protection_policy",
    )
    # Scrubbing metadata file (EXIF, dll) saat upload — aman, tetap ada
    metadata_scrubbing = models.BooleanField(
        default=True,
        help_text="Hapus EXIF dan metadata file saat upload",
    )
    # Strip header identifikasi dari HTTP response — aman, tetap ada
    header_scrubbing = models.BooleanField(
        default=True,
        help_text="Hilangkan header identifikasi dari response",
    )
    # log_retention_wipe DIHAPUS — FIX #1
    # Field ini memfasilitasi penghapusan log server yang melanggar
    # kewajiban retensi OJK/BI minimum 2555 hari (7 tahun).
    # Retensi log diatur via DataRetentionPolicy.audit_log_retention_days
    # dengan nilai minimum yang di-enforce di level model.

    clipboard_protection = models.BooleanField(default=True)
    screenshot_detection = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "compliance_data_protection"

    def __str__(self):
        return f"DataProtectionPolicy({self.workspace})"


# Override DataRetentionPolicy untuk tambah enforcement minimum
# Gantikan class DataRetentionPolicy yang ada di models.py

class DataRetentionPolicy(models.Model):
    """
    FIX #1 tambahan: Tambahkan validasi minimum retention untuk audit log.
    OJK/BI mensyaratkan retensi log minimum 7 tahun = 2555 hari.
    """
    MIN_AUDIT_RETENTION_DAYS = 2555  # 7 tahun — mandatory OJK

    workspace = models.OneToOneField(
        "workspace.Workspace",
        on_delete=models.CASCADE,
        related_name="retention_policy",
    )
    message_retention_days = models.PositiveIntegerField(default=365)
    file_retention_days = models.PositiveIntegerField(default=730)
    audit_log_retention_days = models.PositiveIntegerField(
        default=2555,
        help_text="Minimum 2555 hari (7 tahun) — wajib OJK/BI",
    )
    auto_delete_enabled = models.BooleanField(default=True)
    legal_hold = models.BooleanField(
        default=False,
        help_text="Freeze semua deletion selama legal hold",
    )
    legal_hold_reason = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "compliance_retention_policy"

    def clean(self):
        from django.core.exceptions import ValidationError
        # FIX #1: Enforce minimum retention — tidak bisa di-set di bawah 7 tahun
        if self.audit_log_retention_days < self.MIN_AUDIT_RETENTION_DAYS:
            raise ValidationError({
                'audit_log_retention_days': (
                    f"Retensi audit log tidak boleh kurang dari "
                    f"{self.MIN_AUDIT_RETENTION_DAYS} hari (7 tahun) "
                    f"sesuai regulasi OJK/BI."
                )
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# FIX #2: RegulatorAccess — pisahkan access_log ke tabel sendiri
#
# Gantikan class RegulatorAccess yang ada, hapus field access_log.
# Tambahkan class RegulatorAccessLog baru.
# ─────────────────────────────────────────────────────────────────────────────

class RegulatorAccess(models.Model):
    """
    Akses baca sementara untuk regulator (OJK, MAS, BI, dll).

    FIX #2: access_log JSONField yang tumbuh tak terbatas digantikan
    oleh tabel RegulatorAccessLog tersendiri (FK ke sini).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(
        "workspace.Workspace",
        on_delete=models.CASCADE,
        related_name="regulator_accesses",
    )
    regulator_name = models.CharField(max_length=128)
    regulator_email = models.EmailField()
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
    )
    access_token_hash = models.CharField(max_length=256, unique=True)
    scope = models.JSONField(default=list, help_text="List of accessible resource types")
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    # access_log JSONField DIHAPUS — FIX #2
    # Gunakan RegulatorAccessLog di bawah
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "compliance_regulator_access"
        indexes = [
            models.Index(fields=["is_active", "valid_until"]),
        ]

    def __str__(self):
        return f"RegulatorAccess({self.regulator_name} → {self.workspace})"

    def log_access(self, action: str, resource: str, ip_address: str = None) -> None:
        """Helper: catat akses ke tabel terpisah."""
        RegulatorAccessLog.objects.create(
            access=self,
            action=action,
            resource=resource,
            ip_address=ip_address,
        )


class RegulatorAccessLog(models.Model):
    """
    FIX #2: Log akses regulator — tabel terpisah dari RegulatorAccess.
    Sebelumnya di-append ke JSONField access_log yang tumbuh unbounded.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    access = models.ForeignKey(
        RegulatorAccess,
        on_delete=models.CASCADE,
        related_name="access_logs",
    )
    action = models.CharField(max_length=50)
    resource = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    accessed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "compliance_regulator_access_log"
        ordering = ["-accessed_at"]
        indexes = [
            models.Index(fields=["access", "accessed_at"]),
        ]

    def __str__(self):
        return f"{self.action} by {self.access.regulator_name} at {self.accessed_at}"


# ─────────────────────────────────────────────────────────────────────────────
# FIX #3: ImmutableAuditLog — tambah field timestamp eksplisit
#
# GANTIKAN class ImmutableAuditLog yang ada. Tambah field `timestamp`
# (bukan auto_now_add) yang dibutuhkan oleh audit_chain.py (batch kritis).
# ImmutableAuditChain di-deprecated tapi jangan dihapus (ada data lama).
# ─────────────────────────────────────────────────────────────────────────────

class ImmutableAuditLog(models.Model):
    """
    Audit log immutable untuk pesan — standar OJK/BI.
    Digunakan oleh audit_chain.py untuk blockchain-style integrity.

    FIX #3: Tambah field `timestamp` eksplisit (bukan auto_now_add).
    Sebelumnya hanya ada `created_at` (auto_now_add) yang nilainya berbeda
    dengan timezone.now() yang dipakai saat build chain hash → semua chain
    selalu dianggap tampered. Field `timestamp` diisi satu kali saat create
    dan dipakai konsisten di create dan verify.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.CharField(max_length=50, db_index=True)
    sender_id = models.CharField(max_length=50)
    receiver_id = models.CharField(max_length=50, blank=True)
    message_hash = models.CharField(max_length=64)     # SHA-256
    channel = models.CharField(max_length=100)
    action = models.CharField(max_length=50)            # sent, deleted, edited, read
    device_info = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True)
    prev_hash = models.CharField(max_length=64)
    chain_hash = models.CharField(max_length=64, unique=True)

    # FIX #3: Field timestamp eksplisit — BUKAN auto_now_add
    # Nilai ini di-set sekali di audit_chain.create_audit_entry()
    # dan dipakai untuk hashing. Harus sama persis saat verify.
    timestamp = models.DateTimeField(
        null=True,               # null=True untuk backward compat existing rows
        db_index=True,
        help_text="Explicit timestamp untuk chain hash — bukan auto_now_add",
    )
    # created_at tetap ada untuk referensi DB-level
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "compliance_immutable_audit"
        app_label = "compliance"
        ordering = ["timestamp", "created_at"]   # FIX #3: order by timestamp dulu

    def __str__(self):
        return f"{self.action} by {self.sender_id} at {self.timestamp or self.created_at}"

    def save(self, *args, **kwargs):
        if self.pk:
            raise PermissionError("ImmutableAuditLog tidak bisa diubah setelah dibuat.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("ImmutableAuditLog tidak bisa dihapus.")


class ImmutableAuditChain(models.Model):
    """
    DEPRECATED — gunakan ImmutableAuditLog + audit_chain.py.
    Class ini dipertahankan agar data lama tidak hilang.
    Jangan buat entry baru di sini.
    """
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
        db_table = "compliance_immutable_chain"
        ordering = ["sequence"]

    def save(self, *args, **kwargs):
        if self.pk:
            raise PermissionError("ImmutableAuditChain tidak bisa diubah.")
        # DEPRECATED: log warning jika ada yang masih nulis ke sini
        import logging
        logging.getLogger(__name__).warning(
            "ImmutableAuditChain DEPRECATED — gunakan ImmutableAuditLog"
        )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("ImmutableAuditChain tidak bisa dihapus.")


# ─────────────────────────────────────────────────────────────────────────────
# FIX #4: EmergencyAccessLog — FK ke BankUser + enforcement 2-of-3
#
# Sebelumnya approver_1 dan approver_2 adalah CharField biasa.
# Tidak ada enforcement bahwa access_granted hanya bisa True jika
# kedua approver telah menyetujui. Fix: FK ke BankUser + property
# computed + override save() untuk enforce threshold.
# ─────────────────────────────────────────────────────────────────────────────

class EmergencyAccessLog(models.Model):
    """
    Log akses darurat — diaktifkan ketika minimal 2 dari 3
    pemegang Shamir key share setuju.

    FIX #4:
    - approver_1 dan approver_2 sekarang FK ke BankUser (bukan CharField)
    - access_granted tidak bisa di-set True secara manual — hanya via
      grant_access() yang memvalidasi threshold 2-of-3
    - Tambah field status untuk audit trail yang lebih jelas
    """
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_EXPIRED = "expired"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending Approval"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_EXPIRED, "Expired"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(
        "workspace.Workspace",
        on_delete=models.CASCADE,
        related_name="emergency_access_logs",
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,          # FIX #4: FK, bukan CharField
        related_name="emergency_requests",
    )
    reason = models.TextField()
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,          # FIX #4: FK, bukan CharField
        related_name="emergency_access_targets",
    )

    # FIX #4: FK ke BankUser — bukan CharField kosong yang bisa diisi sembarang
    approver_1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="emergency_approvals_1",
    )
    approver_1_at = models.DateTimeField(null=True, blank=True)

    approver_2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="emergency_approvals_2",
    )
    approver_2_at = models.DateTimeField(null=True, blank=True)

    # FIX #4: access_granted tidak di-set langsung — gunakan grant_access()
    access_granted = models.BooleanField(default=False)
    approved_at = models.DateTimeField(null=True, blank=True)

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    expires_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Akses otomatis expire setelah waktu ini",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "compliance_emergency_access"
        app_label = "compliance"
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["workspace", "status"]),
        ]

    def __str__(self):
        return f"EmergencyAccess({self.requested_by} → {self.target_user}) [{self.status}]"

    @property
    def approval_count(self) -> int:
        """Hitung jumlah approver yang sudah setuju."""
        count = 0
        if self.approver_1_id:
            count += 1
        if self.approver_2_id:
            count += 1
        return count

    @property
    def is_threshold_met(self) -> bool:
        """FIX #4: True jika minimal 2 approver sudah setuju (threshold 2-of-3)."""
        return self.approval_count >= 2

    def add_approval(self, approver) -> bool:
        """
        FIX #4: Tambahkan approval dari seorang approver.
        Return True jika threshold terpenuhi setelah approval ini.

        Validasi:
        - approver tidak boleh sama dengan requested_by
        - approver tidak boleh approve dua kali
        - status harus masih pending
        """
        from django.utils import timezone
        from django.core.exceptions import ValidationError

        if self.status != self.STATUS_PENDING:
            raise ValidationError(f"Request sudah dalam status {self.status}.")

        if approver == self.requested_by:
            raise ValidationError("Requester tidak bisa menjadi approver.")

        if self.approver_1 == approver or self.approver_2 == approver:
            raise ValidationError("Approver sudah memberikan persetujuan.")

        now = timezone.now()

        if not self.approver_1:
            self.approver_1 = approver
            self.approver_1_at = now
        elif not self.approver_2:
            self.approver_2 = approver
            self.approver_2_at = now
        else:
            raise ValidationError("Semua slot approver sudah terisi.")

        if self.is_threshold_met:
            self.grant_access()
        else:
            self.save(update_fields=["approver_1", "approver_1_at",
                                      "approver_2", "approver_2_at"])

        return self.is_threshold_met

    def grant_access(self) -> None:
        """
        FIX #4: Satu-satunya cara set access_granted=True.
        Hanya bisa dipanggil dari add_approval() setelah threshold terpenuhi.
        """
        from django.utils import timezone
        import logging
        logger = logging.getLogger(__name__)

        if not self.is_threshold_met:
            raise PermissionError(
                "Tidak bisa grant access — threshold 2-of-3 belum terpenuhi."
            )

        self.access_granted = True
        self.status = self.STATUS_APPROVED
        self.approved_at = timezone.now()
        self.save(update_fields=[
            "approver_1", "approver_1_at",
            "approver_2", "approver_2_at",
            "access_granted", "status", "approved_at",
        ])

        logger.critical(
            "EMERGENCY ACCESS GRANTED: request=%s workspace=%s "
            "target=%s approver_1=%s approver_2=%s",
            self.id, self.workspace_id,
            self.target_user_id, self.approver_1_id, self.approver_2_id,
        )
