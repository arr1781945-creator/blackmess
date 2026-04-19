# Operational Planning & Control
**Organization:** BlackMess Research
**Version:** 1.0
**Date:** April 2026

## 1. Secure Development Lifecycle
- Threat modeling before development
- Security requirements defined
- Code review (self-review + automated)
- Dependency vulnerability scanning
- Secure deployment via CI/CD

## 2. Change Management
All changes to production:
1. Tested in development
2. Committed to git with descriptive message
3. Deployed via Railway/Vercel pipeline
4. Post-deployment verification

## 3. Capacity Planning
- Current: Railway free tier
- Planned: On-premise data center 8x5m
- Budget: Rp 1.8 Billion
- Timeline: Post-contract Goldman Sachs / PayPal

## 4. Security Monitoring
- Automated alerts for anomalies
- Django Axes for brute force detection
- Audit trail for all user actions
- Compliance dashboard real-time
