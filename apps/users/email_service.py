import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'chudorifirman@gmail.com')

LOGO_SVG = """
<div style="display:inline-flex;align-items:center;gap:10px;">
  <svg width="36" height="36" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="24" cy="6" r="3" fill="white"/>
    <circle cx="24" cy="42" r="3" fill="white"/>
    <circle cx="6" cy="24" r="3" fill="white"/>
    <circle cx="42" cy="24" r="3" fill="white"/>
    <circle cx="11" cy="11" r="2.5" fill="white" opacity="0.7"/>
    <circle cx="37" cy="11" r="2.5" fill="white" opacity="0.7"/>
    <circle cx="11" cy="37" r="2.5" fill="white" opacity="0.7"/>
    <circle cx="37" cy="37" r="2.5" fill="white" opacity="0.7"/>
    <circle cx="24" cy="24" r="3" fill="white" opacity="0.3"/>
  </svg>
  <span style="font-size:22px;font-weight:800;color:white;letter-spacing:-0.5px;">BlackMess</span>
</div>
"""

def _base_template(content_html: str) -> str:
    return f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background:#0f0f0f;font-family:'Inter',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0f0f0f;padding:40px 20px;">
    <tr>
      <td align="center">
        <table width="520" cellpadding="0" cellspacing="0" style="background:#1a1a1a;border-radius:20px;overflow:hidden;border:1px solid #2a2a2a;">
          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#1a0a2e 0%,#2d1a4e 50%,#1a0a2e 100%);padding:32px 40px;text-align:center;">
              {LOGO_SVG}
              <p style="color:#a78bda;font-size:12px;margin:8px 0 0;letter-spacing:2px;text-transform:uppercase;">Enterprise Communication Platform</p>
            </td>
          </tr>
          <!-- Content -->
          <tr>
            <td style="padding:40px;">
              {content_html}
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="background:#111;padding:24px 40px;border-top:1px solid #2a2a2a;">
              <p style="color:#555;font-size:12px;margin:0;text-align:center;">
                © 2026 BlackMess Enterprise Platform · Ternate, Indonesia<br>
                <span style="color:#444;">Email ini dikirim secara otomatis, harap tidak membalas.</span>
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

def send_otp_email(to_email: str, otp: str, name: str = '') -> bool:
    display_name = name or to_email.split('@')[0]
    content_html = f"""
      <h2 style="color:#fff;font-size:22px;margin:0 0 8px;">Verifikasi Email Anda</h2>
      <p style="color:#888;font-size:15px;margin:0 0 28px;">Halo <strong style="color:#c4b5fd;">{display_name}</strong>, gunakan kode berikut untuk memverifikasi akun BlackMess Anda.</p>
      
      <div style="background:#0f0f0f;border:2px solid #4A154B;border-radius:16px;padding:32px;text-align:center;margin-bottom:28px;">
        <p style="color:#888;font-size:13px;margin:0 0 12px;letter-spacing:1px;text-transform:uppercase;">Kode Verifikasi</p>
        <div style="font-size:48px;font-weight:900;letter-spacing:16px;color:#fff;font-family:monospace;">{otp}</div>
        <p style="color:#555;font-size:13px;margin:12px 0 0;">⏱ Berlaku selama <strong style="color:#a78bda;">10 menit</strong></p>
      </div>

      <div style="background:#1e1e1e;border-radius:12px;padding:16px;border-left:3px solid #4A154B;">
        <p style="color:#888;font-size:13px;margin:0;">🔒 <strong style="color:#c4b5fd;">Tips Keamanan:</strong> BlackMess tidak akan pernah meminta kode ini melalui telepon atau chat. Jangan bagikan kode ini kepada siapapun.</p>
      </div>

      <p style="color:#555;font-size:12px;margin:24px 0 0;text-align:center;">Jika Anda tidak mendaftar di BlackMess, abaikan email ini dengan aman.</p>
    """
    message = Mail(
        from_email=(FROM_EMAIL, 'BlackMess Security'),
        to_emails=to_email,
        subject='[BlackMess] Kode Verifikasi Anda',
        html_content=_base_template(content_html)
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
        return True
    except Exception as e:
        print(f"SendGrid error: {e}")
        return False

def send_invite_email(to_email: str, from_name: str, invite_link: str, workspace: str = 'BlackMess') -> bool:
    content_html = f"""
      <h2 style="color:#fff;font-size:22px;margin:0 0 8px;">Anda Mendapat Undangan! 🎉</h2>
      <p style="color:#888;font-size:15px;margin:0 0 24px;"><strong style="color:#c4b5fd;">{from_name}</strong> mengundang Anda untuk bergabung ke workspace <strong style="color:#c4b5fd;">{workspace}</strong> di BlackMess.</p>

      <div style="background:#0f0f0f;border:1px solid #2a2a2a;border-radius:16px;padding:24px;margin-bottom:28px;">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
          <div style="width:48px;height:48px;background:linear-gradient(135deg,#4A154B,#7c3aed);border-radius:12px;display:flex;align-items:center;justify-content:center;">
            <span style="color:white;font-size:20px;font-weight:800;">{workspace[0].upper()}</span>
          </div>
          <div>
            <p style="color:#fff;font-weight:700;margin:0;font-size:16px;">{workspace}</p>
            <p style="color:#888;margin:0;font-size:13px;">Platform Komunikasi Enterprise</p>
          </div>
        </div>
        <div style="border-top:1px solid #2a2a2a;padding-top:16px;">
          <p style="color:#888;font-size:13px;margin:0;">✅ Enkripsi End-to-End (E2EE)</p>
          <p style="color:#888;font-size:13px;margin:8px 0 0;">✅ Post-Quantum Cryptography (PQC)</p>
          <p style="color:#888;font-size:13px;margin:8px 0 0;">✅ Standar Keamanan OJK/BI</p>
        </div>
      </div>

      <div style="text-align:center;margin-bottom:28px;">
        <a href="{invite_link}" style="display:inline-block;background:linear-gradient(135deg,#4A154B,#7c3aed);color:white;padding:16px 48px;border-radius:12px;font-weight:700;font-size:16px;text-decoration:none;letter-spacing:0.5px;">
          Terima Undangan →
        </a>
        <p style="color:#555;font-size:12px;margin:12px 0 0;">atau copy link: <span style="color:#a78bda;">{invite_link}</span></p>
      </div>

      <div style="background:#1e1e1e;border-radius:12px;padding:16px;border-left:3px solid #7c3aed;">
        <p style="color:#888;font-size:13px;margin:0;">⏱ Link undangan ini berlaku selama <strong style="color:#c4b5fd;">7 hari</strong>. Jika Anda tidak mengenal pengirim, abaikan email ini.</p>
      </div>
    """
    message = Mail(
        from_email=(FROM_EMAIL, 'BlackMess Team'),
        to_emails=to_email,
        subject=f'[BlackMess] {from_name} mengundang Anda ke {workspace}',
        html_content=_base_template(content_html)
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
        return True
    except Exception as e:
        print(f"SendGrid error: {e}")
        return False
