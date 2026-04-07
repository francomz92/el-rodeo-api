from secrets import choice
from string import printable

from passlib.context import CryptContext

from src.common.domain.services.security import ISecurityService


context = CryptContext(schemes=["bcrypt"])


class SecurityService(ISecurityService):
    def hash_password(self, password: str) -> str:
        return context.hash(password)

    def verify_password(self, password: str, hashed_password: str) -> bool:
        return context.verify(password, hashed_password)

    def generate_random_str(self, length: int) -> str:
        chrs = (choice(printable) for _ in range(length))
        return "".join(chrs)
