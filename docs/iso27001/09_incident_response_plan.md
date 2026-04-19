# Incident Response Plan
**Organization:** BlackMess Research
**Version:** 1.0
**Date:** April 2026

## 1. Incident Classification
| Level | Description | Response Time |
|-------|-------------|---------------|
| P1 Critical | Data breach, system compromise | Immediate |
| P2 High | Unauthorized access attempt | < 1 hour |
| P3 Medium | Suspicious activity | < 4 hours |
| P4 Low | Policy violation | < 24 hours |

## 2. Response Procedure
### P1 Critical:
1. Isolate affected system
2. Revoke all active JWT tokens
3. Rotate all cryptographic keys (ML-DSA-65 + ML-KEM-1024)
4. Notify affected users
5. GDPR breach notification to DPC within 72 hours (Article 33)
6. Document in compliance_incident_report
7. Post-mortem within 48 hours

## 3. Key Revocation Process
- Automated via key_rotation_protocol.py
- 14-entry audit trail generated
- Partners notified to re-establish E2EE sessions
- Total revocation time: < 5ms

## 4. GDPR Notification
- DPC notification: within 72 hours
- User notification: without undue delay
- Template: available in compliance_gdpr_request
