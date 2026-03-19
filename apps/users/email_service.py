import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
FROM_EMAIL = 'noreply@blackmess.app'

def send_otp_email(to_email: str, otp: str, name: str = '') -> bool:
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=to_email,
        subject='Kode Verifikasi BlackMess',
        html_content=f'''
        <div style="font-family:Inter,sans-serif;max-width:480px;margin:0 auto;background:#0a0a0f;color:white;padding:40px;border-radius:16px;">
            <div style="text-align:center;margin-bottom:32px;">
                <div style="width:60px;height:60px;background:#1a1a2e;border-radius:16px;display:inline-flex;align-items:center;justify-content:center;margin-bottom:16px;">
                    <span style="font-size:24px;font-weight:900;color:white;">BM</span>
                </div>
                <h1 style="margin:0;font-size:24px;font-weight:700;">BlackMess</h1>
            </div>
            <h2 style="font-size:18px;margin-bottom:8px;">Verifikasi Email Kamu</h2>
            <p style="color:#94a3b8;margin-bottom:24px;">Halo {name or to_email.split('@')[0]}, gunakan kode berikut:</p>
            <div style="background:#1a1a2e;border:1px solid #2d2d44;border-radius:12px;padding:24px;text-align:center;margin-bottom:24px;">
                <div style="font-size:40px;font-weight:900;letter-spacing:12px;color:white;">{otp}</div>
                <p style="color:#64748b;font-size:12px;margin-top:8px;">Kode berlaku 10 menit</p>
            </div>
            <p style="color:#64748b;font-size:12px;text-align:center;">Jika kamu tidak mendaftar di BlackMess, abaikan email ini.</p>
        </div>
        '''
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
        return True
    except Exception as e:
        print(f"SendGrid error: {e}")
        return False

def send_invite_email(to_email: str, from_name: str, invite_link: str, workspace: str = 'BlackMess') -> bool:
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=to_email,
        subject=f'{from_name} mengundang kamu ke {workspace}',
        html_content=f'''
        <div style="font-family:Inter,sans-serif;max-width:480px;margin:0 auto;background:#0a0a0f;color:white;padding:40px;border-radius:16px;">
            <div style="text-align:center;margin-bottom:32px;">
                <div style="width:60px;height:60px;background:#1a1a2e;border-radius:16px;display:inline-flex;align-items:center;justify-content:center;margin-bottom:16px;">
                    <span style="font-size:24px;font-weight:900;color:white;">BM</span>
                </div>
                <h1 style="margin:0;font-size:24px;font-weight:700;">BlackMess</h1>
            </div>
            <h2 style="font-size:18px;margin-bottom:8px;">Kamu Diundang! 🎉</h2>
            <p style="color:#94a3b8;margin-bottom:24px;"><strong style="color:white;">{from_name}</strong> mengundang kamu bergabung ke <strong style="color:white;">{workspace}</strong>.</p>
            <div style="text-align:center;margin-bottom:24px;">
                <a href="{invite_link}" style="display:inline-block;background:white;color:black;padding:14px 32px;border-radius:12px;font-weight:700;font-size:15px;text-decoration:none;">
                    Terima Undangan
                </a>
            </div>
            <p style="color:#64748b;font-size:12px;text-align:center;">Link berlaku 7 hari.</p>
        </div>
        '''
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
        return True
    except Exception as e:
        print(f"SendGrid error: {e}")
        return False
