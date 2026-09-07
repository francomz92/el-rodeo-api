from abc import abstractmethod

from src.common.application.ports.email_notifier import IEmailNotifier


class IEmailClient(IEmailNotifier):
    @abstractmethod
    def send_email(self, to: list[str], subject: str, body: str) -> None:
        raise NotImplementedError

    def send(self, to: list[str], subject: str, body: str) -> None:
        """Concrete delegate to send_email for IEmailNotifier compatibility."""
        return self.send_email(to, subject, body)
