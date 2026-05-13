from src.common.application.ports.email_client import IEmailClient


class EmailService:
    def __init__(self, client: IEmailClient):
        self.email_client = client

    def send_email(
        self,
        to: list[str],
        subject: str,
        body: str,
    ) -> None:
        #! Implement email notification logic
        self.email_client.send_email(to, subject, body)
