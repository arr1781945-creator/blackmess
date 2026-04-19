# Data Retention Policy
**Organization:** BlackMess Research
**Version:** 1.0
**Date:** April 2026

## 1. Retention Schedule

| Data Type | Retention Period | Basis |
|-----------|-----------------|-------|
| Messages (default) | 24 hours (configurable) | User preference |
| Financial communications | 5 years | OJK/BI requirement |
| Audit logs | 7 years | ISO 27001 + OJK/BI |
| User account data | Duration of account + 30 days | GDPR |
| GDPR requests | 5 years | Legal obligation |
| Incident reports | 7 years | ISO 27001 |
| Compliance reports | 7 years | OJK/BI |

## 2. Deletion Procedures
- Automated wipe: daily at 03:00 WIT
- GDPR erasure requests: within 30 days
- Secure deletion: overwrite + audit log

## 3. Legal Hold
Data under legal hold exempt from standard retention schedule.
