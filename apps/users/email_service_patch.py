"""
apps/users/email_service_patch.py

Patch untuk email_service.py — dua fungsi yang perlu diupdate.
Salin _send() dan send_invite_email() ke email_service.py,
gantikan yang lama.

LOW FIX #1 — _send(): error logging pakai print() bukan logger
  print() ke stdout tidak termonitor di production (Sentry, ELK, dll).
  Ganti ke logger.error() dengan exc_info=True.

LOW FIX #2 — send_invite_email(): input tidak di-escape → XSS di email
  from_name, workspace, dan invite_link dimasukkan langsung ke HTML
  tanpa escaping. Jika workspace berisi HTML tag atau invite_link
  berisi javascript: URL, ini akan di-render oleh email client.
"""
import logging
import os
from urllib.parse import urlparse

from django.utils.html import escape
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Content

logger = logging.getLogger(__name__)

FROM_EMAIL = "blackmessage312415@gmail.com"
FROM_NAME = "BlackMess"
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")


def _send(to_email: str, subject: str, html: str, plain: str) -> bool:
    """
    FIX #1: Ganti print() ke logger.error() dengan exc_info=True
    agar error email masuk ke monitoring system (Sentry, ELK, dll).
    """
    try:
        msg = Mail()
        msg.from_email = (FROM_EMAIL, FROM_NAME)
        msg.to = to_email
        msg.subject = subject
        msg.content = [
            Content("text/plain", plain),
            Content("text/html", html),
        ]
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        r = sg.send(msg)
        return r.status_code == 202
    except Exception:
        # FIX #1: logger.error dengan exc_info=True agar stack trace tercatat
        logger.error(
            "Gagal kirim email ke %s (subject: %s)",
            to_email, subject,
            exc_info=True,
        )
        return False


def send_invite_email(
    to_email: str,
    from_name: str,
    invite_link: str,
    workspace: str = "BlackMess",
) -> bool:
    """
    FIX #2: Escape semua input user sebelum masuk ke HTML template.
    Validasi invite_link hanya boleh pakai scheme https://.
    """
    # FIX #2a: Validasi URL scheme — tolak javascript: dan scheme lain
    try:
        parsed = urlparse(invite_link)
        if parsed.scheme not in ("https", "http"):
            logger.error(
                "send_invite_email: invite_link scheme tidak valid: %s",
                parsed.scheme,
            )
            return False
    except Exception:
        logger.error("send_invite_email: invite_link tidak valid", exc_info=True)
        return False

    # FIX #2b: Escape semua input sebelum masuk HTML
    safe_from_name = escape(from_name)
    safe_workspace = escape(workspace)
    safe_invite_link = escape(invite_link)   # escape < > & " '
    initial = escape(workspace[0].upper()) if workspace else "?"

    # Template HTML menggunakan safe_ variables saja
    content = f"""
<h2 style="color:#ffffff;font-size:22px;font-weight:800;margin:0 0 8px;text-align:center;">Undangan Bergabung 🎉</h2>
<p style="color:#6b7280;font-size:14px;text-align:center;margin:0 0 32px;">
  <strong style="color:#c4b5fd;">{safe_from_name}</strong> mengundang Anda bergabung ke workspace <strong style="color:#c4b5fd;">{safe_workspace}</strong>
</p>

<table cellpadding="0" cellspacing="0" width="100%" style="background:#0f0f1a;border:1px solid #1e1e3a;border-radius:16px;margin-bottom:28px;">
  <tr>
    <td style="padding:24px;">
      <table cellpadding="0" cellspacing="0">
        <tr>
          <td style="width:56px;height:56px;background:linear-gradient(135deg,#4c1d95,#7c3aed);border-radius:14px;text-align:center;vertical-align:middle;font-size:24px;font-weight:900;color:white;">{initial}</td>
          <td style="padding-left:16px;">
            <div style="color:#ffffff;font-size:18px;font-weight:700;">{safe_workspace}</div>
            <div style="color:#6b7280;font-size:13px;margin-top:3px;">BlackMess Enterprise Workspace</div>
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>

<table cellpadding="0" cellspacing="0" style="margin:0 auto 28px;">
  <tr>
    <td style="background:linear-gradient(135deg,#4c1d95,#7c3aed);border-radius:14px;padding:1px;">
      <table cellpadding="0" cellspacing="0">
        <tr>
          <td style="background:linear-gradient(135deg,#5b21b6,#7c3aed);border-radius:13px;padding:16px 48px;text-align:center;">
            <a href="{safe_invite_link}" style="color:#ffffff;font-size:16px;font-weight:700;text-decoration:none;">Terima Undangan &rarr;</a>
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>

<p style="color:#4b5563;font-size:12px;text-align:center;margin:0 0 24px;">
  Atau copy link berikut ke browser:<br>
  <a href="{safe_invite_link}" style="color:#7c3aed;word-break:break-all;">{safe_invite_link}</a>
</p>

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

    # Import _template dari email_service.py yang sudah ada
    from .email_service import _template
    html_full, plain_full = _template(content, plain)

    subject = f"{from_name} mengundang Anda ke {workspace} di BlackMess"
    return _send(to_email, subject, html_full, plain_full)
