"""Email delivery — SMTP send for OTP and other transactional mail.

Uses smtplib synchronously inside a background thread so FastAPI routes
don't block on SMTP latency. We deliberately don't use asyncio.create_task
from the sync route handlers because the event loop closes when the
response is returned, silently dropping the in-flight task.
"""

from __future__ import annotations

import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings
from app.core.logging import logger


_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>LegalEase AI verification</title>
</head>
<body style="margin:0;padding:0;background:#0B1B2B;font-family:'Inter',Arial,sans-serif;color:#F4F1EA;">
  <table role="presentation" cellpadding="0" cellspacing="0" width="100%"
         style="background:#0B1B2B;padding:40px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" cellpadding="0" cellspacing="0"
               style="max-width:520px;background:#0E1726;border:1px solid rgba(201,169,97,0.25);border-radius:12px;padding:32px;">
          <tr>
            <td align="center" style="padding-bottom:24px;">
              <div style="font-family:'Georgia',serif;font-weight:700;font-size:22px;
                          color:#C9A961;letter-spacing:0.5px;">
                LegalEase AI
              </div>
              <div style="font-size:11px;letter-spacing:0.18em;text-transform:uppercase;
                          color:#9AA5B8;margin-top:4px;">
                Verify your email
              </div>
            </td>
          </tr>
          <tr>
            <td style="color:#D7D2C5;font-size:15px;line-height:1.6;padding-bottom:24px;">
              Hello {recipient},<br /><br />
              Use the following 6-digit code to confirm your email and finish
              creating your LegalEase AI account.
            </td>
          </tr>
          <tr>
            <td align="center" style="padding:8px 0 24px 0;">
              <div style="display:inline-block;font-family:'JetBrains Mono','Courier New',monospace;
                          font-size:34px;letter-spacing:10px;font-weight:700;color:#0B1B2B;
                          background:linear-gradient(135deg,#C9A961 0%,#E5C880 50%,#C9A961 100%);
                          padding:18px 28px;border-radius:10px;">
                {otp}
              </div>
            </td>
          </tr>
          <tr>
            <td style="color:#9AA5B8;font-size:13px;line-height:1.6;padding-bottom:24px;">
              The code expires in <strong style="color:#F4F1EA;">10 minutes</strong>.
              If you did not request this, you can safely ignore this email — no
              account will be created.
            </td>
          </tr>
          <tr>
            <td style="border-top:1px solid rgba(255,255,255,0.08);
                       padding-top:16px;color:#6B7587;font-size:11px;line-height:1.5;">
              This is an automated message from LegalEase AI — Pakistan's
              AI-powered legal assistance platform. Please do not reply.
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

_TEXT_FALLBACK = (
    "LegalEase AI — Email verification\n\n"
    "Hello {recipient},\n\n"
    "Your verification code is: {otp}\n\n"
    "It expires in 10 minutes. If you didn't request this, ignore this email.\n"
)


def _smtp_configured() -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_USERNAME and settings.SMTP_PASSWORD)


def _send_sync(to_email: str, subject: str, html: str, text: str) -> None:
    """Blocking SMTP send — runs in a worker thread to avoid blocking
    FastAPI request handlers."""
    if not _smtp_configured():
        logger.warning(
            f"SMTP not configured — would have emailed {to_email}. Subject: {subject}"
        )
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM or settings.SMTP_USERNAME
    msg["To"] = to_email
    msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        if settings.SMTP_PORT == 465:
            client = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20)
        else:
            client = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20)
            if settings.SMTP_TLS:
                client.starttls()
        with client:
            client.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            client.send_message(msg)
        logger.info(f"Email sent to {to_email} — subject: {subject}")
    except Exception as e:  # noqa: BLE001
        logger.error(f"SMTP send to {to_email} failed: {type(e).__name__}: {e}")


def send_email_async(to_email: str, subject: str, html: str, text: str) -> None:
    """Fire-and-forget email send. Returns immediately; delivery happens
    in a daemon thread so request latency isn't bound by SMTP."""
    thread = threading.Thread(
        target=_send_sync,
        args=(to_email, subject, html, text),
        daemon=True,
    )
    thread.start()


def send_otp_email(email: str, otp: str, *, recipient_name: str | None = None) -> None:
    """Send the OTP verification email. Synchronous return — actual delivery
    runs on a background thread."""
    recipient = (recipient_name or email.split("@")[0]).strip() or "there"
    html = _HTML_TEMPLATE.format(otp=otp, recipient=recipient)
    text = _TEXT_FALLBACK.format(otp=otp, recipient=recipient)
    send_email_async(
        to_email=email,
        subject="LegalEase AI - Email Verification Code",
        html=html,
        text=text,
    )
    # Belt-and-braces: always log the OTP in development so demos work even
    # if SMTP isn't configured. Filtered out in prod via log level.
    logger.info(f"[dev] OTP for {email}: {otp}")


def send_password_reset_email(email: str, otp: str) -> None:
    recipient = email.split("@")[0]
    html = _HTML_TEMPLATE.format(otp=otp, recipient=recipient).replace(
        "Verify your email", "Reset your password"
    ).replace(
        "Use the following 6-digit code to confirm your email and finish "
        "creating your LegalEase AI account.",
        "Use this 6-digit code to reset your LegalEase AI password.",
    )
    text = _TEXT_FALLBACK.format(otp=otp, recipient=recipient).replace(
        "Email verification", "Password reset"
    )
    send_email_async(
        to_email=email,
        subject="LegalEase AI - Password Reset Code",
        html=html,
        text=text,
    )
    logger.info(f"[dev] Password-reset OTP for {email}: {otp}")
