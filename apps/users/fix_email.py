with open(r'apps/users/email_service.py', 'r') as f:
    c = f.read()

# Fix FROM_EMAIL ke domain sendiri
c = c.replace(
    "FROM_EMAIL = r'blackmessage312415@gmail.com'",
    "FROM_EMAIL = r'noreply@blackmess.app'"
)

# Fix subject OTP - jangan expose kode di subject
c = c.replace(
    "return _send(to_email, fr'Kode masuk BlackMess Anda: {otp[:2]}****', html, plain)",
    "return _send(to_email, r'BlackMess — Verifikasi Login Anda', html, plain)"
)

# Fix footer - ganti Ternate ke Jakarta
c = c.replace(
    r'© 2026 BlackMess Enterprise · Ternate, Maluku Utara, Indonesia',
    r'© 2026 BlackMess Enterprise · Jakarta, Indonesia'
)

with open(r'apps/users/email_service.py', 'w') as f:
    f.write(c)

print("Done!")
