"""
apps/compliance/compliance_views.py

FIX #1 — compliance_dashboard, verify_chain, channel_policies:
  Hanya IsAuthenticated — semua user bisa akses audit log workspace manapun
  hanya dengan mengganti workspace_id di query param.
  Fix: tambah permission check bahwa user adalah member workspace tersebut,
  dan untuk dashboard/verify_chain harus compliance officer atau superuser.

FIX #2 — request_emergency_access: bypass fix EmergencyAccessLog
  View lama membuat EmergencyAccessLog dengan CharField lama,
  bypass seluruh enforcement 2-of-3 yang sudah diperbaiki.
  Fix: gunakan model baru dengan FK + add_approval() method.

FIX #3 — bare except: pass menyembunyikan error axes
  `except:` tanpa spesifikasi menangkap semua exception termasuk
  SystemExit dan KeyboardInterrupt. Ganti ke `except Exception`.
"""
import datetime
import logging

from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound

from .audit_chain import verify_audit_chain
from .models import ImmutableAuditLog, ChannelPolicy, EmergencyAccessLog

logger = logging.getLogger(__name__)


def _get_workspace_or_403(workspace_id: str, user):
    """
    FIX #1 helper: Validasi user adalah member workspace.
    Raise PermissionDenied jika bukan member.
    Raise NotFound jika workspace tidak ada.
    """
    from apps.workspace.models import Workspace, WorkspaceMember

    if not workspace_id or workspace_id == 'default':
        raise PermissionDenied("workspace_id diperlukan.")

    try:
        workspace = Workspace.objects.get(id=workspace_id)
    except (Workspace.DoesNotExist, Exception):
        raise NotFound("Workspace tidak ditemukan.")

    if not WorkspaceMember.objects.filter(
        workspace=workspace, user=user, status='active'
    ).exists():
        raise PermissionDenied("Anda bukan member workspace ini.")

    return workspace


def _is_compliance_officer(user) -> bool:
    """Cek apakah user adalah compliance officer atau superuser."""
    if user.is_superuser:
        return True
    return user.role_assignments.filter(
        role__name__in=["compliance_officer", "super_admin", "auditor"],
        is_active=True,
    ).exists()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def compliance_dashboard(request):
    """
    Dashboard compliance officer — standar OJK/BI.

    FIX #1: Wajib compliance officer atau superuser.
    FIX #3: bare except → except Exception.
    """
    if not _is_compliance_officer(request.user):
        raise PermissionDenied("Hanya compliance officer yang bisa akses dashboard ini.")

    workspace_id = request.query_params.get('workspace_id', '')
    workspace = _get_workspace_or_403(workspace_id, request.user)

    chain_status = verify_audit_chain(workspace_id)

    thirty_days = timezone.now() - datetime.timedelta(days=30)
    recent_logs = ImmutableAuditLog.objects.filter(
        workspace_id=workspace_id,
        created_at__gte=thirty_days,
    )

    brute_force = 0
    try:
        from axes.models import AccessAttempt
        brute_force = AccessAttempt.objects.filter(
            attempt_time__gte=thirty_days
        ).count()
    except Exception:   # FIX #3: bukan bare except
        pass

    return Response({
        'audit_chain': chain_status,
        'workspace': str(workspace.id),
        'stats': {
            'total_messages': recent_logs.filter(action='sent').count(),
            'deleted_messages': recent_logs.filter(action='deleted').count(),
            'edited_messages': recent_logs.filter(action='edited').count(),
            'unique_senders': recent_logs.values('sender_id').distinct().count(),
            'brute_force_attempts': brute_force,
        },
        'ipfs_status': {
            'network': 'private',
            'nodes': ['127.0.0.1:4001'],
            'encrypted': True,
        },
        # FIX #1: Batasi 20 log terbaru — bukan expose semua
        'recent_logs': list(
            recent_logs.order_by('-created_at')[:20].values(
                'sender_id', 'action', 'channel',
                'ip_address', 'created_at', 'chain_hash',
            )
        ),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verify_chain(request):
    """
    Verifikasi integritas audit chain.
    FIX #1: Hanya compliance officer yang bisa verify chain.
    """
    if not _is_compliance_officer(request.user):
        raise PermissionDenied("Hanya compliance officer yang bisa verifikasi chain.")

    workspace_id = request.query_params.get('workspace_id', '')
    _get_workspace_or_403(workspace_id, request.user)

    result = verify_audit_chain(workspace_id)
    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def channel_policies(request):
    """
    Ambil kebijakan channel.
    FIX #1: Cek membership workspace sebelum return policies.
    """
    workspace_id = request.query_params.get('workspace_id', '')
    _get_workspace_or_403(workspace_id, request.user)

    policies = ChannelPolicy.objects.filter(workspace_id=workspace_id)
    return Response([{
        'channel': p.channel_name,
        'type': p.channel_type,
        'allow_self_destruct': p.allow_self_destruct,
        'retention_days': p.retention_days,
        'require_audit': p.require_audit,
    } for p in policies])


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_emergency_access(request):
    """
    Request akses darurat — butuh 2 dari 3 approval.

    FIX #2: Pakai model EmergencyAccessLog yang sudah diperbaiki
    dengan FK ke BankUser dan enforcement 2-of-3 via add_approval().
    Tidak lagi pakai CharField raw string.
    """
    workspace_id = request.data.get('workspace_id', '').strip()
    target_user_id = request.data.get('target_user_id', '').strip()
    reason = request.data.get('reason', '').strip()

    if not workspace_id or not target_user_id or not reason:
        return Response(
            {'detail': 'workspace_id, target_user_id, dan reason diperlukan.'},
            status=400,
        )

    # Validasi workspace
    workspace = _get_workspace_or_403(workspace_id, request.user)

    # Validasi target user
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        target_user = User.objects.get(id=target_user_id)
    except (User.DoesNotExist, Exception):
        return Response({'detail': 'Target user tidak ditemukan.'}, status=404)

    if target_user == request.user:
        return Response(
            {'detail': 'Tidak bisa request akses ke akun sendiri.'},
            status=400,
        )

    # FIX #2: Buat dengan model baru yang menggunakan FK
    log = EmergencyAccessLog.objects.create(
        workspace=workspace,
        requested_by=request.user,       # FK ke BankUser
        reason=reason,
        target_user=target_user,         # FK ke BankUser
        status=EmergencyAccessLog.STATUS_PENDING,
    )

    logger.warning(
        "Emergency access requested: id=%s requester=%s target=%s workspace=%s",
        log.id, request.user.id, target_user.id, workspace_id,
    )

    return Response({
        'id': str(log.id),
        'message': 'Emergency access request dibuat. Menunggu 2 persetujuan.',
        'status': log.status,
        'approval_count': log.approval_count,
        'threshold_required': 2,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_emergency_access(request, log_id):
    """
    Approve emergency access request.
    Menggunakan EmergencyAccessLog.add_approval() yang enforce 2-of-3.
    """
    if not _is_compliance_officer(request.user):
        raise PermissionDenied("Hanya compliance officer yang bisa approve.")

    try:
        log = EmergencyAccessLog.objects.get(id=log_id)
    except EmergencyAccessLog.DoesNotExist:
        return Response({'detail': 'Request tidak ditemukan.'}, status=404)

    try:
        threshold_met = log.add_approval(request.user)
    except Exception as e:
        return Response({'detail': str(e)}, status=400)

    return Response({
        'id': str(log.id),
        'status': log.status,
        'approval_count': log.approval_count,
        'access_granted': log.access_granted,
        'threshold_met': threshold_met,
    })
