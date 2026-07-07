from smtplib import SMTPException

from celery import shared_task

from src.common.application.services.email_service import EmailService
from src.common.infrastructure.adapters.clients.smtp_email_client import SMTPClient


@shared_task(
    autoretry_for=(SMTPException, OSError),
    max_retries=3,
    default_retry_delay=60,
)
def send_email(to: list[str], subject: str, body: str) -> None:
    email_service = EmailService(client=SMTPClient())
    email_service.send_email(to, subject, body)
