from src.common.application.ports.email_notifier import IEmailNotifier
from src.common.infrastructure.workers.email_tasks import send_email


class EmailNotifier(IEmailNotifier):
    def send(self, to: list[str], subject: str, body: str) -> None:
        send_email.apply_async(
            kwargs={
                "to": to,
                "subject": subject,
                "body": body,
            },
        )
