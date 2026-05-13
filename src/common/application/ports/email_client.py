from abc import ABC, abstractmethod


class IEmailClient(ABC):
    @abstractmethod
    def send_email(self, to: list[str], subject: str, body: str) -> None:
        raise NotImplementedError
