# app/notifications/email_sender.py
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv
load_dotenv()

SMTP_EMAIL = os.environ.get("SMTP_EMAIL", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

def send_email(to_address: str, subject: str, body: str, html_body: str = None) -> None:
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print("SMTP credentials missing, skipping email delivery.")
        return

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"Nisaab Finance <{SMTP_EMAIL}>"
        msg["To"] = to_address

        # Attach plain text version
        msg.attach(MIMEText(body, "plain", "utf-8"))

        # Build clean HTML email template if not explicitly provided
        if not html_body:
            formatted_content = body.replace("\n", "<br>")
            html_body = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f7f8f5; color: #1a231e; margin: 0; padding: 24px; }}
    .email-container {{ max-width: 580px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8e3; border-radius: 16px; padding: 32px; box-shadow: 0 4px 16px rgba(15,21,18,0.03); }}
    .email-header {{ font-size: 22px; font-weight: 800; color: #132219; margin-bottom: 20px; letter-spacing: -0.03em; }}
    .email-header span {{ color: #e5a93c; }}
    .email-body {{ font-size: 14.5px; line-height: 1.6; color: #3b4740; }}
    .email-footer {{ margin-top: 28px; padding-top: 16px; border-top: 1px solid #edf1ee; font-size: 12px; color: #7c8982; text-align: center; }}
  </style>
</head>
<body>
  <div class="email-container">
    <div class="email-header">Nisaab<span>.</span></div>
    <div class="email-body">{formatted_content}</div>
    <div class="email-footer">
      Sent by Nisaab Personal Finance Assistant • Managing your wealth wisely
    </div>
  </div>
</body>
</html>"""

        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, to_address, msg.as_string())
    except Exception as err:
        print(f"Error sending email to {to_address}: {err}")