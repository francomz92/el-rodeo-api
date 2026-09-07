from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from src.auth.domain.entities._user_role import UserRole
from src.common.domain.exceptions import BusinessValidationError
from src.common.domain.services.security import ISecurityService


@dataclass
class UserEntity:
    id: UUID
    name: str
    dni: str
    email: str
    created_at: datetime
    role: UserRole = UserRole.VIEWER
    _hashed_password: str = field(default_factory=str, repr=False)
    tenant_id: UUID | None = field(default=None)
    is_active: bool = True

    @property
    def hashed_password(self) -> str:
        """Public read-only access to the hashed password for persistence."""
        return self._hashed_password

    async def passwords_match(self, security_service: ISecurityService, password: str) -> bool:
        return await security_service.verify_password(password, self._hashed_password)

    async def update_password(
        self,
        security_service: ISecurityService,
        password: str,
        new_password: str,
        confirmed_password: str,
    ):
        if new_password != confirmed_password:
            raise BusinessValidationError("Las contraseñas deben coincidir")
        if password == new_password:
            raise BusinessValidationError("La nueva contraseña debe ser diferente")
        self._hashed_password = await security_service.hash_password(new_password)
