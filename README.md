<div align="center">

<svg width="64" height="64" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
  <circle cx="24" cy="6" r="3" fill="white"/>
  <circle cx="24" cy="42" r="3" fill="white"/>
  <circle cx="6" cy="24" r="3" fill="white"/>
  <circle cx="42" cy="24" r="3" fill="white"/>
  <circle cx="11" cy="11" r="2.5" fill="white" opacity="0.7"/>
  <circle cx="37" cy="11" r="2.5" fill="white" opacity="0.7"/>
  <circle cx="11" cy="37" r="2.5" fill="white" opacity="0.7"/>
  <circle cx="37" cy="37" r="2.5" fill="white" opacity="0.7"/>
</svg>

# BlackMess

**Enterprise Remote Work Platform with Post-Quantum Cryptography**

[

![License](https://img.shields.io/badge/License-Enterprise-purple.svg)

]()
[

![Python](https://img.shields.io/badge/Python-3.12-blue.svg)

]()
[

![Django](https://img.shields.io/badge/Django-6.0-green.svg)

]()
[

![React](https://img.shields.io/badge/React-18-61dafb.svg)

]()
[

![PQC](https://img.shields.io/badge/PQC-ML--KEM--1024-red.svg)

]()
[

![OJK](https://img.shields.io/badge/Compliant-OJK%2FBI-orange.svg)

]()

*Built by a 13-year-old developer from Ternate, Indonesia*

[Live Demo](https://black-message.vercel.app) · [API Docs](https://black-message-production.up.railway.app/api/docs/admin/)

</div>

---

## Overview

BlackMess is an enterprise-grade secure messaging platform designed for Indonesian banks, fintech companies, and government institutions. It implements **Post-Quantum Cryptography (PQC)** standards as specified by NIST FIPS 203/204, making it ready for the post-quantum era.

> **Research submitted to BSI Germany (Bundesamt für Sicherheit in der Informationstechnik)**

## Key Features

### Security Architecture
- **Post-Quantum Cryptography** — Hybrid KEM: X25519 + ML-KEM-1024 (NIST FIPS 203)
- **Digital Signatures** — ML-DSA-65 (NIST FIPS 204) as additional layer over WebAuthn
- **End-to-End Encryption** — AES-256-GCM with zero-knowledge architecture
- **Anti-Forensic** — Self-destructing messages with secure memory wiping
- **Replay Attack Prevention** — One-time nonce + TTL mechanism
- **Side-Channel Resistance** — Constant-time operations via liboqs

### Authentication
- **WebAuthn/FIDO2** — Hardware security keys (YubiKey compatible)
- **Multi-Factor Authentication** — TOTP (Google Authenticator) + FIDO2
- **JWT** — Short-lived access tokens with refresh rotation
- **RBAC** — Role-based access control with clearance levels
- **Django Axes** — Brute-force protection
- **OAuth** — GitHub, Google

### Performance Benchmarks
| Algorithm | Operation | Speed |
|-----------|-----------|-------|
| ML-KEM-1024 | Key Generation | **673x faster than RSA-3072** |
| AES-256-GCM | Encryption (1KB) | 11.43ms |
| SHA-256 | Hash (1000x) | 9.14ms |
| ML-DSA-65 | Sign + Verify | ~50ms |

### Compliance
- **OJK** — POJK No.11/POJK.03/2022
- **Bank Indonesia** — PBI No.23/6/PBI/2021
- **Immutable Audit Log** — Blockchain-style SHA-256 chain
- **Shamir Secret Sharing** — 2-of-3 key escrow for emergency access
- **Data Retention** — Configurable 5-10 years per OJK requirements
- **Export for Audit** — PDF, Excel, JSON formats

### Infrastructure
- **IPFS** — Encrypted file storage (private network)
- **WebSockets** — Real-time messaging via Django Channels
- **Redis** — Caching and WebSocket channel layer
- **Celery** — Async task processing
- **PostgreSQL** — 520 tables, enterprise-grade schema

## Technical Stack
Backend:    Django 6.0 + DRF + Django Channels
Frontend:   React 18 + Vite + TypeScript + Tailwind CSS
Database:   PostgreSQL (520 tables)
Cache:      Redis
Queue:      Celery
Storage:    IPFS (private network)
PQC:        liboqs (ML-KEM-1024, ML-DSA-65)
Crypto:     AES-256-GCM, X25519, SHA-256
Auth:       WebAuthn/FIDO2, TOTP, JWT, OAuth
Deploy:     Railway (backend) + Vercel (frontend)
## Architecture
┌─────────────────────────────────────────────────────────┐
│                    Client (Browser)                      │
│  React + WebAuthn + TOTP + E2EE (client-side)           │
└──────────────────────┬──────────────────────────────────┘
│ HTTPS + WSS
┌──────────────────────▼──────────────────────────────────┐
│                  Django Backend                           │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐   │
│  │  Auth   │ │Messaging │ │Compliance│ │   Vault   │   │
│  │WebAuthn │ │WebSocket │ │ Audit    │ │PQC Keys   │   │
│  │FIDO2    │ │E2EE      │ │OJK/BI    │ │Shamir     │   │
│  └─────────┘ └──────────┘ └──────────┘ └───────────┘   │
└──────────────────────┬──────────────────────────────────┘
│
┌──────────────────────▼──────────────────────────────────┐
│              Infrastructure Layer                         │
│  PostgreSQL │ Redis │ IPFS │ Celery                      │
└─────────────────────────────────────────────────────────┘
## PQC Research

This project implements NIST Post-Quantum Cryptography standards ahead of the 2030 migration deadline:

### Hybrid KEM Design
```python
# X25519 + ML-KEM-1024 hybrid encapsulation
def hybrid_encapsulate(kyber_pk, x25519_pk):
    kyber_ct, kyber_ss = ml_kem_1024.encap(kyber_pk)
    x25519_ss = x25519_ephemeral.exchange(x25519_pk)
    # HKDF-SHA512 combines both shared secrets
    combined = HKDF(SHA512).derive(kyber_ss + x25519_ss)
    return combined  # 256-bit combined secret
Why Hybrid?
Classical X25519 protects against current attacks
ML-KEM-1024 protects against quantum computer attacks
Neither alone is sufficient during the transition period
Bug Bounty
Active security research on major platforms:
HackerOne — 7 critical vulnerabilities found
Slack — 1 critical vulnerability found
Compliance Architecture
┌─────────────────────────────────┐
│      OJK/BI Compliance Layer    │
│                                 │
│  Immutable Audit Chain          │
│  (SHA-256 blockchain-style)     │
│           ↓                     │
│  Shamir Secret Sharing          │
│  (2-of-3 key escrow)            │
│           ↓                     │
│  Channel Policy Engine          │
│  (self-destruct rules)          │
│           ↓                     │
│  Emergency Access Protocol      │
│  (dual approval required)       │
└─────────────────────────────────┘
API Endpoints
Category
Endpoints
Authentication
Register, Login, MFA, WebAuthn, OAuth
Messaging
Send, Receive, E2EE, Self-Destruct, IPFS
Workspace
Channels, Members, Permissions
Compliance
Audit Log, Export PDF/Excel/JSON, OJK Dashboard
Vault
PQC Keys, Shamir Shares, Emergency Access
Full API documentation: Swagger UI
Deployment
# Backend (Railway)
railway up

# Frontend (Vercel)
vercel --prod
Developer
Built by a 13-year-old self-taught developer from Ternate, North Maluku, Indonesia.
Working entirely on Android (Termux)
No formal computer science education
Bug bounty hunter (HackerOne, Bugcrowd)
Research submitted to BSI Germany
�

BlackMess — Securing Indonesian Enterprise Communications with Post-Quantum Cryptography
"The next generation of threats requires the next generation of security"
�
