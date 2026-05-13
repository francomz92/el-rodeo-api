from celery import shared_task, Task

from src.common.application.services.email_service import EmailService
from src.common.infrastructure.adapters.clients.smtp_email_client import SMTPClient


@shared_task
def send_email(to: list[str], subject: str, body: str) -> None:
    email_service = EmailService(client=SMTPClient())
    email_service.send_email(to, subject, body)


send_email: Task = send_email
