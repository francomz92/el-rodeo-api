from abc import ABC, abstractmethod


class IEmailClient(ABC):
    """Transport-level seam for delivering one email message."""

    @abstractmethod
    def send_email(self, to: list[str], subject: str, body: str) -> None:
        raise NotImplementedError
