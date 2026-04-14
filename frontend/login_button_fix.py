# Script untuk fix tombol GitHub di Login.tsx
# Jalankan: python login_button_fix.py

import re

filepath = '/data/data/com.termux/files/home/django-api/blackmess/frontend/src/pages/Login.tsx'

with open(filepath, 'r') as f:
    content = f.read()

# Fix semua variasi warna tombol GitHub
fixes = [
    # Background putih
    ("background: '#1a1a1a', color: 'white'", "background: '#ffffff', color: '#000000'"),
    ("background: '#1a1a2e', color: 'white'", "background: '#ffffff', color: '#000000'"),
    # Border visible
    ("border: '1px solid rgba(255,255,255,0.15)'", "border: '1px solid #d0d7de'"),
    ("border: '1px solid rgba(255,255,255,0.1)'", "border: '1px solid #d0d7de'"),
    # Hover states
    ("e.currentTarget.style.background='#222222'", "e.currentTarget.style.background='#f3f4f6'"),
    ("e.currentTarget.style.background='#1a1a1a'", "e.currentTarget.style.background='#ffffff'"),
    ("e.currentTarget.style.background='#1a1a2e'", "e.currentTarget.style.background='#ffffff'"),
    # SVG icon color
    ('fill="white"', 'fill="currentColor"'),
    ('fill="white" viewBox', 'fill="currentColor" viewBox'),
]

for old, new in fixes:
    content = content.replace(old, new)

with open(filepath, 'w') as f:
    f.write(content)

print("✓ Login.tsx GitHub button fixed")
