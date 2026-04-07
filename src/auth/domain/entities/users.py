from datetime import datetime
from uuid import UUID
from dataclasses import dataclass, field

from src.common.domain.services.security import ISecurityService


@dataclass
class UserEntity:
    id: UUID
    dni: str
    created_at: datetime
    _hashed_password: str = field(default_factory=str)

    def passwords_match(self, security_service: ISecurityService, password: str) -> bool:
        return security_service.verify_password(password, self._hashed_password)

    def validate_changed_password(
        self,
        password: str,
        new_password: str,
        confirmed_password: str,
    ):
        if new_password != confirmed_password:
            raise ValueError("Passwords miss matches")
        if password == new_password:
            raise ValueError("The new password must be different")
