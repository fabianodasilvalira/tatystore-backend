from fastapi import BackgroundTasks
from app.services.email_service import send_email_background
def company_admin_email(company) -> str:
    return "admin@local"
async def notify_company_admin(background: BackgroundTasks, company, user, endpoint: str):
    to = company_admin_email(company)
    send_email_background(background, to, "Alerta de segurança", "company_security_alert",
                          company=company.name, user=user.email, endpoint=endpoint)

