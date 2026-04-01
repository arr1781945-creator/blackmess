import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Content

FROM_EMAIL = 'blackmessage312415@gmail.com'
FROM_NAME = 'BlackMess'

SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY', '')

LOGO = """
<table cellpadding="0" cellspacing="0" style="margin:0 auto;">
  <tr>
    <td style="padding-right:12px;">
      <svg width="40" height="40" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="24" cy="6" r="3.5" fill="#c4b5fd"/>
        <circle cx="24" cy="42" r="3.5" fill="#c4b5fd"/>
        <circle cx="6" cy="24" r="3.5" fill="#c4b5fd"/>
        <circle cx="42" cy="24" r="3.5" fill="#c4b5fd"/>
        <circle cx="11" cy="11" r="2.5" fill="#a78bda" opacity="0.8"/>
        <circle cx="37" cy="11" r="2.5" fill="#a78bda" opacity="0.8"/>
        <circle cx="11" cy="37" r="2.5" fill="#a78bda" opacity="0.8"/>
        <circle cx="37" cy="37" r="2.5" fill="#a78bda" opacity="0.8"/>
        <circle cx="24" cy="24" r="5" fill="#7c3aed" opacity="0.6"/>
        <line x1="24" y1="9.5" x2="24" y2="19" stroke="#c4b5fd" stroke-width="1.5" opacity="0.4"/>
        <line x1="24" y1="29" x2="24" y2="38.5" stroke="#c4b5fd" stroke-width="1.5" opacity="0.4"/>
        <line x1="9.5" y1="24" x2="19" y2="24" stroke="#c4b5fd" stroke-width="1.5" opacity="0.4"/>
        <line x1="29" y1="24" x2="38.5" y2="24" stroke="#c4b5fd" stroke-width="1.5" opacity="0.4"/>
      </svg>
    </td>
    <td>
      <span style="font-size:26px;font-weight:900;color:#ffffff;letter-spacing:-0.5px;font-family:Arial,sans-serif;">Black<span style="color:#a78bda;">Mess</span></span>
      <div style="font-size:10px;color:#6b7280;letter-spacing:3px;text-transform:uppercase;margin-top:1px;">Enterprise Platform</div>
    </td>
  </tr>
</table>
"""

def _template(content_html: str, plain_text: str) -> tuple:
    html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta name="color-scheme" content="dark">
</head>
<body style="margin:0;padding:0;background-color:#0a0a0f;font-family:Arial,'Helvetica Neue',sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0a0f;padding:32px 16px;">
<tr><td align="center">

<!-- Outer card -->
<table width="540" cellpadding="0" cellspacing="0" style="max-width:540px;width:100%;background:#111118;border-radius:24px;overflow:hidden;border:1px solid #1e1e2e;">

  <!-- Top accent bar -->
  <tr><td style="background:linear-gradient(90deg,#4c1d95,#7c3aed,#4c1d95);height:3px;font-size:0;">&nbsp;</td></tr>

  <!-- Header -->
  <tr>
    <td style="background:linear-gradient(135deg,#0f0720 0%,#1a0a3e 50%,#0f0720 100%);padding:36px 40px;text-align:center;">
      {LOGO}
    </td>
  </tr>

  <!-- Divider -->
  <tr><td style="background:linear-gradient(90deg,transparent,#7c3aed40,transparent);height:1px;font-size:0;">&nbsp;</td></tr>

  <!-- Content -->
  <tr>
    <td style="padding:40px 40px 32px;">
      {content_html}
    </td>
  </tr>

  <!-- Footer -->
  <tr>
    <td style="background:#0d0d15;padding:24px 40px;border-top:1px solid #1e1e2e;text-align:center;">
      <p style="color:#374151;font-size:12px;margin:0 0 6px;">
        © 2026 BlackMess Enterprise · Ternate, Maluku Utara, Indonesia
      </p>
      <p style="color:#374151;font-size:11px;margin:0;">
        Email ini dikirim otomatis. Harap tidak membalas email ini.
      </p>
      <table cellpadding="0" cellspacing="0" style="margin:12px auto 0;">
        <tr>
          <td style="padding:0 8px;">
            <a href="https://black-message.vercel.app" style="color:#6d28d9;font-size:11px;text-decoration:none;">Website</a>
          </td>
          <td style="color:#374151;font-size:11px;">·</td>
          <td style="padding:0 8px;">
            <a href="https://black-message.vercel.app/privacy" style="color:#6d28d9;font-size:11px;text-decoration:none;">Privasi</a>
          </td>
          <td style="color:#374151;font-size:11px;">·</td>
          <td style="padding:0 8px;">
            <a href="https://black-message.vercel.app/help" style="color:#6d28d9;font-size:11px;text-decoration:none;">Bantuan</a>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- Bottom accent bar -->
  <tr><td style="background:linear-gradient(90deg,#4c1d95,#7c3aed,#4c1d95);height:3px;font-size:0;">&nbsp;</td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""
    return html, plain_text


def _send(to_email: str, subject: str, html: str, plain: str) -> bool:
    try:
        msg = Mail()
        msg.from_email = (FROM_EMAIL, FROM_NAME)
        msg.to = to_email
        msg.subject = subject
        msg.content = [
            Content('text/plain', plain),
            Content('text/html', html),
        ]
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        r = sg.send(msg)
        return r.status_code == 202
    except Exception as e:
        print(f"Email error: {e}")
        return False


def send_otp_email(to_email: str, otp: str, name: str = '') -> bool:
    display = name or to_email.split('@')[0]
    digits = ''.join([
        f'<td style="width:48px;height:64px;background:#0f0f1a;border:2px solid #7c3aed;border-radius:12px;text-align:center;vertical-align:middle;font-size:32px;font-weight:900;color:#ffffff;font-family:monospace;letter-spacing:0;">{d}</td>'
        f'<td style="width:8px;"></td>'
        for d in otp
    ])

    content = f"""
<h2 style="color:#ffffff;font-size:22px;font-weight:800;margin:0 0 8px;text-align:center;">Verifikasi Identitas Anda</h2>
<p style="color:#6b7280;font-size:14px;text-align:center;margin:0 0 32px;">Halo <strong style="color:#c4b5fd;">{display}</strong>, gunakan kode di bawah untuk masuk ke BlackMess.</p>

<!-- OTP digits -->
<table cellpadding="0" cellspacing="0" style="margin:0 auto 32px;">
  <tr>{digits}</tr>
</table>

<!-- Timer badge -->
<table cellpadding="0" cellspacing="0" style="margin:0 auto 32px;">
  <tr>
    <td style="background:#1a0a3e;border:1px solid #4c1d95;border-radius:20px;padding:8px 20px;text-align:center;">
      <span style="color:#a78bda;font-size:13px;">⏱&nbsp; Berlaku <strong style="color:#c4b5fd;">10 menit</strong> sejak email ini dikirim</span>
    </td>
  </tr>
</table>

<!-- Warning box -->
<table cellpadding="0" cellspacing="0" width="100%">
  <tr>
    <td style="background:#1a1a2e;border-left:3px solid #7c3aed;border-radius:0 8px 8px 0;padding:14px 16px;">
      <p style="color:#9ca3af;font-size:13px;margin:0;">
        🔒 <strong style="color:#c4b5fd;">Peringatan Keamanan:</strong> BlackMess tidak akan pernah meminta kode ini melalui telepon, chat, atau email lain. Jangan bagikan kode ini kepada siapapun termasuk tim IT.
      </p>
    </td>
  </tr>
</table>

<p style="color:#4b5563;font-size:12px;text-align:center;margin:24px 0 0;">
  Jika Anda tidak mencoba masuk ke BlackMess, abaikan email ini dengan aman.
</p>
"""

    plain = f"""BlackMess — Kode Verifikasi

Halo {display},

Kode verifikasi BlackMess Anda: {otp}

Berlaku 10 menit. Jangan bagikan ke siapapun.

Jika Anda tidak mencoba masuk, abaikan email ini.

— Tim BlackMess
https://black-message.vercel.app
"""

    html, plain = _template(content, plain)
    return _send(to_email, f'Kode masuk BlackMess Anda: {otp[:2]}****', html, plain)


def send_invite_email(to_email: str, from_name: str, invite_link: str, workspace: str = 'BlackMess') -> bool:
    initial = workspace[0].upper()
    content = f"""
<h2 style="color:#ffffff;font-size:22px;font-weight:800;margin:0 0 8px;text-align:center;">Undangan Bergabung 🎉</h2>
<p style="color:#6b7280;font-size:14px;text-align:center;margin:0 0 32px;">
  <strong style="color:#c4b5fd;">{from_name}</strong> mengundang Anda untuk bergabung ke workspace <strong style="color:#c4b5fd;">{workspace}</strong>
</p>

<!-- Workspace card -->
<table cellpadding="0" cellspacing="0" width="100%" style="background:#0f0f1a;border:1px solid #1e1e3a;border-radius:16px;margin-bottom:28px;">
  <tr>
    <td style="padding:24px;">
      <table cellpadding="0" cellspacing="0">
        <tr>
          <td style="width:56px;height:56px;background:linear-gradient(135deg,#4c1d95,#7c3aed);border-radius:14px;text-align:center;vertical-align:middle;font-size:24px;font-weight:900;color:white;">{initial}</td>
          <td style="padding-left:16px;">
            <div style="color:#ffffff;font-size:18px;font-weight:700;">{workspace}</div>
            <div style="color:#6b7280;font-size:13px;margin-top:3px;">BlackMess Enterprise Workspace</div>
          </td>
        </tr>
      </table>
      <table cellpadding="0" cellspacing="0" style="margin-top:20px;border-top:1px solid #1e1e3a;padding-top:20px;width:100%;">
        <tr>
          <td style="color:#9ca3af;font-size:13px;padding:4px 0;">✅&nbsp; Enkripsi End-to-End (E2EE)</td>
        </tr>
        <tr>
          <td style="color:#9ca3af;font-size:13px;padding:4px 0;">✅&nbsp; Post-Quantum Cryptography (PQC Kyber-1024)</td>
        </tr>
        <tr>
          <td style="color:#9ca3af;font-size:13px;padding:4px 0;">✅&nbsp; Standar Kepatuhan OJK & Bank Indonesia</td>
        </tr>
      </table>
    </td>
  </tr>
</table>

<!-- CTA Button -->
<table cellpadding="0" cellspacing="0" style="margin:0 auto 28px;">
  <tr>
    <td style="background:linear-gradient(135deg,#4c1d95,#7c3aed);border-radius:14px;padding:1px;">
      <table cellpadding="0" cellspacing="0">
        <tr>
          <td style="background:linear-gradient(135deg,#5b21b6,#7c3aed);border-radius:13px;padding:16px 48px;text-align:center;">
            <a href="{invite_link}" style="color:#ffffff;font-size:16px;font-weight:700;text-decoration:none;letter-spacing:0.3px;">Terima Undangan &rarr;</a>
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>

<!-- Link fallback -->
<p style="color:#4b5563;font-size:12px;text-align:center;margin:0 0 24px;">
  Atau copy link berikut ke browser:<br>
  <a href="{invite_link}" style="color:#7c3aed;word-break:break-all;">{invite_link}</a>
</p>

<!-- Info box -->
<table cellpadding="0" cellspacing="0" width="100%">
  <tr>
    <td style="background:#1a1a2e;border-left:3px solid #4c1d95;border-radius:0 8px 8px 0;padding:14px 16px;">
      <p style="color:#9ca3af;font-size:13px;margin:0;">
        ⏱ Link undangan berlaku <strong style="color:#c4b5fd;">7 hari</strong>. Jika Anda tidak mengenal pengirim, abaikan email ini.
      </p>
    </td>
  </tr>
</table>
"""

    plain = f"""BlackMess — Undangan Workspace

{from_name} mengundang Anda bergabung ke workspace "{workspace}" di BlackMess.

Klik link berikut untuk menerima undangan:
{invite_link}

Link berlaku 7 hari.

Jika tidak mengenal pengirim, abaikan email ini.

— Tim BlackMess
https://black-message.vercel.app
"""

    html, plain = _template(content, plain)
    return _send(to_email, f'{from_name} mengundang Anda ke {workspace} di BlackMess', html, plain)
