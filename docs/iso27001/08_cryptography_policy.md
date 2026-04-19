# Cryptography Policy
**Organization:** BlackMess Research
**Version:** 1.0
**Date:** April 2026

## 1. Approved Algorithms

| Use Case | Algorithm | Standard |
|----------|-----------|----------|
| Key Exchange | ML-KEM-1024 + X25519 (Hybrid) | FIPS 203 + BSI TR-02102-1 |
| Digital Signature | ML-DSA-65 | FIPS 204 |
| Symmetric Encryption | AES-256-GCM | FIPS 197 |
| Hashing | SHA-256/SHA-512 | FIPS 180-4 |
| Key Derivation | HKDF-SHA512 | RFC 5869 |
| MFA | ML-DSA-65 (WebAuthn replacement) | FIPS 204 |

## 2. Prohibited Algorithms
- RSA < 3072 bits
- ECDSA (vulnerable to quantum)
- MD5, SHA-1
- DES, 3DES
- RC4

## 3. Key Management
- Private keys never written to disk
- Key rotation: ML-DSA-65 < 1ms overhead
- Compromise response: immediate revocation + JWT blacklist
- Audit trail for all key operations
