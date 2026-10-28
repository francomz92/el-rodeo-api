from src.common.application.ports.email_notifier import IEmailNotifier
from src.common.domain.events.base import DomainEvent


class EmailNotificationHandler:
    def __init__(self, notifier: IEmailNotifier):
        self.notifier = notifier

    def __call__(self, event: DomainEvent):
        data = event.metadata
        emails = data.get("emails", [])
        self.notifier.send(
            to=emails if isinstance(emails, list) else [emails],
            subject=data.get("title", ""),
            body=data.get("body", ""),
        )
