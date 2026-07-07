from dataclasses import dataclass
from uuid import UUID

from src.auth.domain.entities._user_role import UserRole
from src.common.domain.types import Sentinel


@dataclass
class UserCreationValueObject:
    name: str
    dni: str
    email: str
    role: UserRole = UserRole.VIEWER
    tenant_id: UUID | None = None


@dataclass
class UserUpdateValueObject:
    name: str | type[Sentinel] = Sentinel
    email: str | type[Sentinel] = Sentinel
    password: str | type[Sentinel] = Sentinel
    role: UserRole | type[Sentinel] = Sentinel
    is_active: bool | type[Sentinel] = Sentinel
