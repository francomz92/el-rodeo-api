from abc import ABC, abstractmethod


class IEmailNotifier(ABC):
    @abstractmethod
    def send(self, to: list[str], subject: str, body: str) -> None:
        raise NotImplementedError
