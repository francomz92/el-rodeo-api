from typing import Annotated, AsyncGenerator

from fastapi import Depends

from src.common.infrastructure.persistence.connections.db import (
    async_sessionmaker,
    AsyncSession,
    AsyncSessionMaker,
)


async def _get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides a database session."""
    db = AsyncSessionMaker()
    try:
        yield db
    finally:
        await db.close()


GetSession = Annotated[async_sessionmaker, Depends(_get_db)]
