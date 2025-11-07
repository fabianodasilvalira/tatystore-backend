from fastapi import BackgroundTasks
from jinja2 import Template
from app.core.config import get_settings
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
settings = get_settings()
def render_template(path: str, **kwargs):
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    return Template(html).render(**kwargs)
async def send_email_async(to: str, subject: str, html: str):
    msg = MIMEText(html, "html", "utf-8")
    msg["Subject"] = subject
    msg["From"] = formataddr((settings.email_from_name, settings.email_from))
    msg["To"] = to
    server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
    if settings.smtp_tls:
        server.starttls()
    if settings.smtp_username:
        server.login(settings.smtp_username, settings.smtp_password)
    server.sendmail(settings.email_from, [to], msg.as_string())
    server.quit()
def send_email_background(background: BackgroundTasks, to: str, subject: str, template: str, **context):
    html = render_template(f"app/templates/email/{template}.html", **context)
    background.add_task(send_email_async, to, subject, html)

