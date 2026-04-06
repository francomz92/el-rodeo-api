from abc import ABC, abstractmethod


class ITokenService(ABC):
    @abstractmethod
    def generate(self, data: dict, exp_minutes: int) -> str:
        raise NotImplemented

    @abstractmethod
    def decode(self, token: str):
        raise NotImplemented
