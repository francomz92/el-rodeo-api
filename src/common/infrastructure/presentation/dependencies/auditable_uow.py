"""GetAuditableUnitOfWork dependency — UoW with current_user set.

This module lives in its own file to avoid circular imports:
  - uow.py exports GetUnitOfWork (used by auth_dependencies.py)
  - auditable_uow.py imports GetCurrentUser from auth_dependencies.py
  - auth_dependencies.py imports GetUnitOfWork from uow.py (no cycle)
"""

from typing import Annotated

from fastapi import Depends

from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
    GetCurrentUser,
)
from src.common.application.ports.uow import IUoW
from src.common.infrastructure.persistence.uow import UnitOfWork

from .db import GetSession


async def _get_auditable_uow(
    session_maker: GetSession,
    current_user: GetCurrentUser,
) -> IUoW:  # type: ignore[reportInvalidTypeForm]
    """Return a UnitOfWork with the authenticated user set for audit logging."""
    return UnitOfWork(session=session_maker, current_user=current_user)


GetAuditableUnitOfWork = Annotated[IUoW, Depends(_get_auditable_uow)]
