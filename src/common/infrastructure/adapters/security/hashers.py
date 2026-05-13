from secrets import choice
from string import printable

import bcrypt

from src.common.domain.services.security import ISecurityService


class SecurityService(ISecurityService):
    def hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed_password.decode("utf-8")

    def verify_password(self, password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(
            password=password.encode("utf-8"),
            hashed_password=hashed_password.encode("utf-8"),
        )

    def generate_random_str(self, length: int) -> str:
        chrs = (choice(printable) for _ in range(length))
        return "".join(chrs)
