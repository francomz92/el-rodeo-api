from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from src.common.domain.services.security import ISecurityService


@dataclass
class UserEntity:
    id: UUID
    name: str
    dni: str
    email: str
    created_at: datetime
    is_admin: bool
    _hashed_password: str = field(default_factory=str)

    def passwords_match(self, security_service: ISecurityService, password: str) -> bool:
        return security_service.verify_password(password, self._hashed_password)

    def update_password(
        self,
        security_service: ISecurityService,
        password: str,
        new_password: str,
        confirmed_password: str,
    ):
        if new_password != confirmed_password:
            raise ValueError("Las contraseñas deben coincidir")
        if password == new_password:
            raise ValueError("La nueva contraseña debe ser diferente")
        self._hashed_password = security_service.hash_password(new_password)
