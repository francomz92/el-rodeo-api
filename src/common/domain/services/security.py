from abc import ABC, abstractmethod


class ISecurityService(ABC):
    @abstractmethod
    def hash_password(self, password: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def verify_password(self, password: str, hashed_password: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def generate_random_str(self, length: int) -> str:
        raise NotImplementedError
