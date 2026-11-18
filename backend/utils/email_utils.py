import smtplib
from email.message import EmailMessage
from config import Config

def send_email(to_email, subject, html_body):
    if not Config.SMTP_HOST or not Config.SMTP_FROM:
        return {"sent": False, "reason": "SMTP is not configured"}
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = subject, Config.SMTP_FROM, to_email
    msg.set_content("This message contains HTML content.")
    msg.add_alternative(html_body, subtype="html")
    try:
        with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=15) as server:
            server.starttls()
            if Config.SMTP_USERNAME:
                server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
            server.send_message(msg)
        return {"sent": True}
    except Exception as exc:
        return {"sent": False, "reason": str(exc)}
