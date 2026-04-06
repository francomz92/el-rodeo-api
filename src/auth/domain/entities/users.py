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
