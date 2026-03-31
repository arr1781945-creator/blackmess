"""apps/compliance/views.py — Compliance, OJK, DLP, Helpdesk, Remote Wipe"""
import re
import secrets
import hashlib
import logging
from django.utils import timezone
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import (
    OJKIncidentReport, InformationBarrier, RemoteWipeRequest,
    SecureFileLink, DLPRule, HelpdeskTicket, HelpdeskComment,
    InstitutionBadge, AuditLog,
)

logger = logging.getLogger(__name__)

# ─── DLP Engine ───────────────────────────────────────────────────────────────

DLP_PATTERNS = {
    'credit_card': r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
    'nik': r'\b\d{16}\b',
    'account_number': r'\b\d{10,16}\b',
    'phone': r'\b(?:\+62|08)\d{8,11}\b',
}

def check_dlp(content: str, workspace) -> dict:
    """Cek konten terhadap DLP rules. Return {'blocked': bool, 'reason': str}"""
    # Built-in patterns
    for data_type, pattern in DLP_PATTERNS.items():
        if re.search(pattern, content):
            return {'blocked': True, 'reason': f'Konten mengandung {data_type.replace("_"," ")} yang tidak boleh dikirim.'}

    # Custom workspace rules
    for rule in DLPRule.objects.filter(workspace=workspace, is_active=True):
        try:
            if re.search(rule.pattern, content):
                if rule.action == 'block':
                    return {'blocked': True, 'reason': f'DLP: {rule.name}'}
                elif rule.action == 'warn':
                    return {'blocked': False, 'warning': f'Peringatan DLP: {rule.name}'}
        except re.error:
            pass

    return {'blocked': False}


def check_info_barrier(sender, receiver, workspace) -> bool:
    """Cek apakah komunikasi antara sender dan receiver diblokir."""
    sender_dept = getattr(sender, 'department', '')
    receiver_dept = getattr(receiver, 'department', '')
    if not sender_dept or not receiver_dept:
        return False

    for barrier in InformationBarrier.objects.filter(workspace=workspace, is_active=True):
        pairs = barrier.blocked_departments
        for pair in pairs:
            if isinstance(pair, list) and len(pair) == 2:
                if (sender_dept in pair and receiver_dept in pair):
                    return True
    return False


# ─── OJK Incident Report ──────────────────────────────────────────────────────

class OJKIncidentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return OJKIncidentReport.objects.filter(
            workspace__members=self.request.user
        ).order_by('-created_at')

    def perform_create(self, serializer):
        from datetime import timedelta
        detected_at = serializer.validated_data.get('detected_at', timezone.now())
        serializer.save(
            reported_by=self.request.user,
            deadline_at=detected_at + timedelta(hours=24),
        )

    @action(detail=True, methods=['post'])
    def submit_to_ojk(self, request, pk=None):
        """Submit laporan ke OJK. Deadline 24 jam."""
        report = self.get_object()

        if report.status == 'submitted':
            return Response({'detail': 'Sudah pernah disubmit.'}, status=400)

        if timezone.now() > report.deadline_at:
            return Response({'detail': 'PERINGATAN: Sudah melewati deadline 24 jam OJK!'}, status=400)

        # Kirim ke OJK API (simulasi — ganti dengan endpoint OJK asli)
        ojk_payload = {
            'institution_code': request.data.get('institution_code', ''),
            'incident_type': report.incident_type,
            'severity': report.severity,
            'description': report.description,
            'affected_systems': report.affected_systems,
            'affected_users': report.affected_users_count,
            'detected_at': report.detected_at.isoformat(),
            'reported_at': timezone.now().isoformat(),
        }

        # TODO: ganti URL dengan endpoint OJK resmi
        # import requests
        # response = requests.post(settings.OJK_API_URL, json=ojk_payload,
        #     headers={'Authorization': f'Bearer {settings.OJK_API_KEY}'})

        # Untuk sekarang: simulasi sukses
        ref_number = f"OJK-{timezone.now().strftime('%Y%m%d')}-{secrets.token_hex(4).upper()}"
        report.status = 'submitted'
        report.ojk_reference_number = ref_number
        report.submitted_at = timezone.now()
        report.save(update_fields=['status', 'ojk_reference_number', 'submitted_at'])

        AuditLog.objects.create(
            event_type='OJK_INCIDENT_SUBMITTED',
            severity='critical',
            actor=request.user,
            description=f'OJK incident report submitted: {ref_number}',
            metadata=ojk_payload,
        )

        return Response({
            'detail': 'Laporan berhasil dikirim ke OJK.',
            'reference_number': ref_number,
            'submitted_at': report.submitted_at.isoformat(),
        })


# ─── Information Barrier ──────────────────────────────────────────────────────

class InformationBarrierViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return InformationBarrier.objects.filter(
            workspace__members=self.request.user
        )

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['post'])
    def check(self, request):
        """Cek apakah dua user bisa berkomunikasi."""
        from apps.users.models import BankUser
        from apps.workspace.models import Workspace

        sender_id = request.data.get('sender_id')
        receiver_id = request.data.get('receiver_id')
        workspace_id = request.data.get('workspace_id')

        try:
            sender = BankUser.objects.get(id=sender_id)
            receiver = BankUser.objects.get(id=receiver_id)
            workspace = Workspace.objects.get(id=workspace_id)
        except Exception as e:
            return Response({'detail': str(e)}, status=404)

        blocked = check_info_barrier(sender, receiver, workspace)
        return Response({
            'blocked': blocked,
            'reason': 'Information barrier aktif antara divisi ini.' if blocked else None,
        })


# ─── Remote Wipe ──────────────────────────────────────────────────────────────

class RemoteWipeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.clearance_level >= 4:
            return RemoteWipeRequest.objects.all()
        return RemoteWipeRequest.objects.filter(target_user=self.request.user)

    def perform_create(self, serializer):
        if self.request.user.clearance_level < 4:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Clearance Level 4+ diperlukan untuk remote wipe.")
        serializer.save(requested_by=self.request.user)

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        wipe = self.get_object()
        if wipe.status != 'pending':
            return Response({'detail': 'Wipe sudah dieksekusi atau dibatalkan.'}, status=400)

        # Invalidate semua session target user
        from apps.users.models import LoginSession
        LoginSession.objects.filter(user=wipe.target_user).update(is_revoked=True)

        wipe.status = 'executed'
        wipe.executed_at = timezone.now()
        wipe.save(update_fields=['status', 'executed_at'])

        AuditLog.objects.create(
            event_type='REMOTE_WIPE_EXECUTED',
            severity='critical',
            actor=request.user,
            description=f'Remote wipe executed for user {wipe.target_user.username}',
            metadata={'reason': wipe.reason, 'device_token': wipe.device_token},
        )

        return Response({'detail': f'Remote wipe berhasil. Semua sesi {wipe.target_user.username} dinonaktifkan.'})


# ─── Secure File Link ─────────────────────────────────────────────────────────

class SecureFileLinkViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SecureFileLink.objects.filter(uploaded_by=self.request.user)

    def perform_create(self, serializer):
        import hashlib
        raw_token = secrets.token_urlsafe(48)
        token_hash = hashlib.sha512(raw_token.encode()).hexdigest()

        password = serializer.validated_data.pop('password', None)
        password_hash = ''
        if password:
            password_hash = hashlib.sha256(password.encode()).hexdigest()

        link = serializer.save(
            uploaded_by=self.request.user,
            token_hash=token_hash,
            password_hash=password_hash,
        )

        # Return raw token sekali saja
        link._raw_token = raw_token

    @action(detail=False, methods=['post'])
    def access(self, request):
        """Akses file via token + password."""
        raw_token = request.data.get('token')
        password = request.data.get('password', '')

        token_hash = hashlib.sha512(raw_token.encode()).hexdigest()
        try:
            link = SecureFileLink.objects.get(token_hash=token_hash, is_active=True)
        except SecureFileLink.DoesNotExist:
            return Response({'detail': 'Link tidak valid atau sudah expired.'}, status=404)

        if timezone.now() > link.expires_at:
            link.is_active = False
            link.save(update_fields=['is_active'])
            return Response({'detail': 'Link sudah expired.'}, status=410)

        if link.download_count >= link.max_downloads:
            return Response({'detail': 'Batas download tercapai.'}, status=410)

        if link.password_hash:
            if hashlib.sha256(password.encode()).hexdigest() != link.password_hash:
                return Response({'detail': 'Password salah.'}, status=403)

        # Log akses
        link.access_log.append({
            'user': str(request.user.id),
            'ip': request.META.get('REMOTE_ADDR', ''),
            'at': timezone.now().isoformat(),
        })
        link.download_count += 1
        link.save(update_fields=['access_log', 'download_count'])

        return Response({
            'filename': link.filename,
            'ipfs_cid': link.ipfs_cid,
            'size_bytes': link.file_size_bytes,
        })


# ─── DLP ──────────────────────────────────────────────────────────────────────

class DLPRuleViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DLPRule.objects.filter(workspace__members=self.request.user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['post'])
    def scan(self, request):
        """Scan konten sebelum dikirim."""
        from apps.workspace.models import Workspace
        content = request.data.get('content', '')
        workspace_id = request.data.get('workspace_id')
        try:
            workspace = Workspace.objects.get(id=workspace_id)
        except Workspace.DoesNotExist:
            return Response({'detail': 'Workspace tidak ditemukan.'}, status=404)

        result = check_dlp(content, workspace)
        return Response(result)


# ─── Helpdesk ─────────────────────────────────────────────────────────────────

class HelpdeskTicketViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.clearance_level >= 3:
            return HelpdeskTicket.objects.filter(workspace__members=user)
        return HelpdeskTicket.objects.filter(created_by=user)

    def perform_create(self, serializer):
        # Generate nomor tiket
        count = HelpdeskTicket.objects.count() + 1
        ticket_number = f"TKT-{timezone.now().strftime('%Y%m')}-{count:04d}"
        serializer.save(
            created_by=self.request.user,
            ticket_number=ticket_number,
        )

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        ticket = self.get_object()
        new_status = request.data.get('status')
        valid = [s[0] for s in HelpdeskTicket.STATUS]
        if new_status not in valid:
            return Response({'detail': f'Status harus salah satu dari: {valid}'}, status=400)

        ticket.status = new_status
        if new_status == 'resolved':
            ticket.resolved_at = timezone.now()
        ticket.save(update_fields=['status', 'resolved_at', 'updated_at'])
        return Response({'detail': f'Status tiket diubah ke {new_status}.'})

    @action(detail=True, methods=['post'])
    def comment(self, request, pk=None):
        ticket = self.get_object()
        content = request.data.get('content', '')
        if not content:
            return Response({'detail': 'Komentar tidak boleh kosong.'}, status=400)

        HelpdeskComment.objects.create(
            ticket=ticket,
            author=request.user,
            content=content,
            is_internal=request.data.get('is_internal', False),
        )
        return Response({'detail': 'Komentar ditambahkan.'})

    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        ticket = self.get_object()
        comments = ticket.comments.select_related('author').order_by('created_at')
        data = [{
            'id': str(c.id),
            'author': c.author.username,
            'content': c.content,
            'is_internal': c.is_internal,
            'created_at': c.created_at.isoformat(),
        } for c in comments if not c.is_internal or request.user.clearance_level >= 3]
        return Response(data)


# ─── Institution Badge ────────────────────────────────────────────────────────

class InstitutionBadgeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return InstitutionBadge.objects.filter(is_active=True)
