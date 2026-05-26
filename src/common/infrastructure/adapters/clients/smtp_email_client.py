from email.message import EmailMessage
from smtplib import SMTP_SSL

from src.common.application.ports.email_client import IEmailClient
from src.common.infrastructure.core import settings


class SMTPClient(IEmailClient):
    def __get_client(self):
        return SMTP_SSL(
            host=settings.SMTP_SERVER,
            port=settings.SMTP_PORT,
        )

    def send_email(self, to: list[str], subject: str, body: str):
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_USER
        with self.__get_client() as client:
            client.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            client.send_message(msg=msg, to_addrs=to)
