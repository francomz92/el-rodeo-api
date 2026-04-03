from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from src.common.infrastructure.core import settings


engine = create_async_engine(
    url=settings.DB_URL,
    echo=False,
    echo_pool=False,
    pool_size=5,
    max_overflow=10,
)


AsyncSessionMaker = async_sessionmaker(  # type: ignore
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

BaseDBModel = declarative_base()
