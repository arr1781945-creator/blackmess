"""
apps/compliance/optimizations.py
Optimized queries untuk Banking Compliance reporting.
"""
from django.db import connection
from django.db.models import Count, Sum, Avg, Q, Prefetch
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


def get_aml_ppatk_report(days=30):
    """
    Optimized AML/PPATK report query.
    Single query dengan annotation — hindari N+1.
    """
    from .models import AMLAlert, TransactionMonitor

    since = timezone.now() - timedelta(days=days)

    # Single optimized query
    report = AMLAlert.objects.filter(
        created_at__gte=since
    ).select_related(
        r'user', 'transaction', 'resolved_by'
    ).prefetch_related(
        r'sar_reports'
    ).values(
        r'alert_type', 'severity'
    ).annotate(
        total=Count(r'id'),
        resolved=Count(r'id', filter=Q(is_resolved=True)),
        pending=Count(r'id', filter=Q(is_resolved=False)),
        avg_transaction_amount=Avg(r'transaction__amount'),
        total_transaction_value=Sum(r'transaction__amount'),
    ).order_by(r'-total')

    return list(report)


def get_transaction_risk_summary(user_id=None, days=7):
    """
    Real-time transaction risk summary.
    Pakai raw SQL untuk performa maksimal.
    """
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                t.transaction_type,
                COUNT(*) as total,
                SUM(t.amount) as total_amount,
                AVG(t.risk_score) as avg_risk,
                COUNT(CASE WHEN t.is_flagged THEN 1 END) as flagged,
                COUNT(CASE WHEN t.status = r'blocked' THEN 1 END) as blocked
            FROM compliance_transaction_monitor t
            WHERE t.created_at >= NOW() - INTERVAL r'%s days'
            AND (%s IS NULL OR t.user_id = %s::uuid)
            GROUP BY t.transaction_type
            ORDER BY total_amount DESC
        """, [days, user_id, user_id])
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def get_high_risk_users(threshold=0.7, limit=50):
    """
    Get high risk users dengan composite query.
    """
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                u.id,
                u.username,
                u.employee_id,
                COUNT(DISTINCT t.id) as transaction_count,
                COUNT(DISTINCT a.id) as alert_count,
                MAX(t.risk_score) as max_risk_score,
                SUM(t.amount) as total_amount
            FROM users_bankuser u
            LEFT JOIN compliance_transaction_monitor t
                ON t.user_id = u.id
                AND t.created_at >= NOW() - INTERVAL r'30 days'
            LEFT JOIN compliance_aml_alert a
                ON a.user_id = u.id
                AND a.is_resolved = FALSE
            WHERE t.risk_score >= %s
                OR a.severity IN (r'high', 'critical')
            GROUP BY u.id, u.username, u.employee_id
            ORDER BY alert_count DESC, max_risk_score DESC
            LIMIT %s
        """, [threshold, limit])
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def add_missing_indexes():
    """
    Add composite indexes yang missing.
    Run sekali saat startup.
    """
    indexes = [
        # Transaction monitor — most queried
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_txn_user_date ON compliance_transaction_monitor(user_id, created_at DESC)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_txn_risk_flagged ON compliance_transaction_monitor(risk_score DESC, is_flagged) WHERE is_flagged = TRUE",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_txn_status ON compliance_transaction_monitor(status, created_at DESC)",

        # AML alerts
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_aml_user_severity ON compliance_aml_alert(user_id, severity, is_resolved)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_aml_unresolved ON compliance_aml_alert(created_at DESC) WHERE is_resolved = FALSE",

        # Immutable chain
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chain_hash ON compliance_immutable_chain(chain_hash)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chain_seq ON compliance_immutable_chain(sequence DESC)",

        # Messages
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_msg_channel_date ON messaging_message(channel_id, created_at DESC) WHERE is_deleted = FALSE",

        # Users
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_clearance ON users_bankuser(clearance_level, is_active)",
    ]

    with connection.cursor() as cursor:
        for idx in indexes:
            try:
                cursor.execute(idx)
                logger.info("Index created: %s", idx[:60])
            except Exception as e:
                logger.warning("Index skip: %s", e)
