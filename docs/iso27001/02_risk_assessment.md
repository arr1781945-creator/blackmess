# Risk Assessment & Treatment Plan
**Organization:** BlackMess Research
**Owner:** Akbar Ramadhan
**Version:** 1.0
**Date:** April 2026

## 1. Risk Assessment Methodology
Risk Score = Likelihood × Impact (Scale 1-5)

## 2. Risk Register
| ID | Risk | Likelihood | Impact | Score | Treatment |
|----|------|-----------|--------|-------|-----------|
| R1 | Unauthorized access | 2 | 5 | 10 | MFA + JWT + RBAC |
| R2 | Data breach | 2 | 5 | 10 | E2EE + PQC + AES-256-GCM |
| R3 | Quantum attack | 1 | 5 | 5 | ML-KEM-1024 + ML-DSA-65 |
| R4 | DDoS attack | 3 | 4 | 12 | Cloudflare + Django Axes |
| R5 | SQL Injection | 2 | 5 | 10 | Django ORM + parameterized queries |
| R6 | XSS | 2 | 4 | 8 | CSP + input sanitization |
| R7 | Insider threat | 1 | 5 | 5 | RBAC + audit trail |
| R8 | Data loss | 2 | 5 | 10 | Backup + IPFS redundancy |
| R9 | Compliance violation | 2 | 4 | 8 | GDPR + OJK/BI controls |
| R10 | Key compromise | 1 | 5 | 5 | Key rotation protocol |

## 3. Risk Treatment
- **Accept:** R3 (quantum attack — mitigated by PQC)
- **Mitigate:** All others via technical controls
- **Transfer:** DDoS via Cloudflare
- **Avoid:** No storage of plaintext sensitive data
