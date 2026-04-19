# Statement of Applicability (SoA)
**Organization:** BlackMess Research
**Version:** 1.0
**Date:** April 2026

## ISO 27001:2022 Controls

| Control | Title | Applicable | Implemented | Justification |
|---------|-------|-----------|-------------|---------------|
| 5.1 | Policies for information security | Yes | Yes | ISMS Policy documented |
| 5.2 | Information security roles | Yes | Yes | CISO assigned |
| 5.7 | Threat intelligence | Yes | Yes | Threat model generator |
| 5.15 | Access control | Yes | Yes | RBAC implemented |
| 5.16 | Identity management | Yes | Yes | JWT + WebAuthn |
| 5.17 | Authentication | Yes | Yes | MFA + FIDO2 |
| 5.23 | Cloud services security | Yes | Yes | Railway + Vercel |
| 6.1 | Screening | No | No | Solo operation |
| 8.1 | User endpoint devices | Yes | Yes | Anti-forensics |
| 8.2 | Privileged access | Yes | Yes | Admin RBAC |
| 8.5 | Secure authentication | Yes | Yes | PQ MFA |
| 8.7 | Malware protection | Yes | Yes | DLP + CSP |
| 8.9 | Configuration management | Yes | Yes | Django settings |
| 8.11 | Data masking | Yes | Yes | AES-256-GCM field-level |
| 8.12 | Data leakage prevention | Yes | Yes | DLP rules |
| 8.15 | Logging | Yes | Yes | Audit trail 520 tables |
| 8.16 | Monitoring | Yes | Yes | compliance_system_log |
| 8.24 | Cryptography | Yes | Yes | PQC FIPS 203/204 |
| 8.25 | Secure development | Yes | Yes | Django ORM + CSP |
| 8.28 | Secure coding | Yes | Yes | Input validation + DLP |
