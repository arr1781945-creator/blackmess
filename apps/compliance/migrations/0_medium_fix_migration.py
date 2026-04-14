"""
apps/compliance/migrations/0_medium_fix_migration.py

PETUNJUK: Rename file ini sesuai urutan migration yang ada.
Cek migration terakhir di apps/compliance/migrations/ lalu nama file
jadi: 00XX_medium_severity_fixes.py (XX = nomor berikutnya)

Atau jalankan:
  python manage.py makemigrations compliance --name medium_severity_fixes
"""
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        # Sesuaikan dengan migration terakhir compliance yang ada
        ('compliance', '0001_initial'),   # <-- SESUAIKAN
        ('workspace', '0001_initial'),
        ('users', '0001_initial'),
    ]

    operations = [

        # ── FIX #1: Hapus log_retention_wipe dari ForensicsBlock ──────────
        migrations.RemoveField(
            model_name='forensicsblock',
            name='log_retention_wipe',
        ),

        # ── FIX #1: Rename ForensicsBlock → DataProtectionPolicy ──────────
        migrations.RenameModel(
            old_name='ForensicsBlock',
            new_name='DataProtectionPolicy',
        ),
        migrations.AlterModelTable(
            name='dataprotectionpolicy',
            table='compliance_data_protection',
        ),

        # ── FIX #2: Hapus access_log JSONField dari RegulatorAccess ───────
        migrations.RemoveField(
            model_name='regulatoraccess',
            name='access_log',
        ),

        # ── FIX #2: Buat tabel RegulatorAccessLog ─────────────────────────
        migrations.CreateModel(
            name='RegulatorAccessLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False,
                                        primary_key=True, serialize=False)),
                ('action', models.CharField(max_length=50)),
                ('resource', models.CharField(blank=True, max_length=255)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('accessed_at', models.DateTimeField(auto_now_add=True)),
                ('access', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='access_logs',
                    to='compliance.regulatoraccess',
                )),
            ],
            options={
                'db_table': 'compliance_regulator_access_log',
                'ordering': ['-accessed_at'],
            },
        ),
        migrations.AddIndex(
            model_name='regulatoraccesslog',
            index=models.Index(
                fields=['access', 'accessed_at'],
                name='reg_access_log_idx',
            ),
        ),

        # ── FIX #3: Tambah field timestamp eksplisit ke ImmutableAuditLog ─
        migrations.AddField(
            model_name='immutableauditlog',
            name='timestamp',
            field=models.DateTimeField(
                null=True,
                db_index=True,
                help_text='Explicit timestamp untuk chain hash — bukan auto_now_add',
            ),
        ),

        # ── FIX #4: EmergencyAccessLog — FK fields baru ───────────────────
        migrations.AddField(
            model_name='emergencyaccesslog',
            name='workspace',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='emergency_access_logs',
                to='workspace.workspace',
            ),
        ),
        migrations.AddField(
            model_name='emergencyaccesslog',
            name='approver_1_fk',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='emergency_approvals_1',
                to='users.bankuser',
            ),
        ),
        migrations.AddField(
            model_name='emergencyaccesslog',
            name='approver_1_at',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='emergencyaccesslog',
            name='approver_2_fk',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='emergency_approvals_2',
                to='users.bankuser',
            ),
        ),
        migrations.AddField(
            model_name='emergencyaccesslog',
            name='approver_2_at',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='emergencyaccesslog',
            name='requested_by_fk',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='emergency_requests',
                to='users.bankuser',
            ),
        ),
        migrations.AddField(
            model_name='emergencyaccesslog',
            name='target_user_fk',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='emergency_access_targets',
                to='users.bankuser',
            ),
        ),
        migrations.AddField(
            model_name='emergencyaccesslog',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending Approval'),
                    ('approved', 'Approved'),
                    ('rejected', 'Rejected'),
                    ('expired', 'Expired'),
                ],
                default='pending',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='emergencyaccesslog',
            name='expires_at',
            field=models.DateTimeField(null=True, blank=True),
        ),

        # SETELAH backfill data lama, buat migration kedua untuk hapus CharField lama:
        # migrations.RemoveField('emergencyaccesslog', 'approver_1'),
        # migrations.RemoveField('emergencyaccesslog', 'approver_2'),
        # migrations.RemoveField('emergencyaccesslog', 'requested_by'),
        # migrations.RemoveField('emergencyaccesslog', 'target_user_id'),
    ]
