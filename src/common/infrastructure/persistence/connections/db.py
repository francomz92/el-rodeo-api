from math import floor

from sqlalchemy import AsyncAdaptedQueuePool, NullPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.common.infrastructure.core import settings

engine = create_async_engine(
    url=settings.DB_URL,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=max(floor(50 / settings.WORKERS), 2),
    max_overflow=max(floor(20 / settings.WORKERS), 1),
    pool_pre_ping=True,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_timeout=10,
    pool_use_lifo=True,
    echo=False,
    echo_pool=False,
)


AsyncSessionMaker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

worker_session_engine = create_async_engine(
    url=settings.DB_URL,
    poolclass=NullPool,
    echo=False,
    echo_pool=False,
)

WorkerSessionMaker = async_sessionmaker(
    bind=worker_session_engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)
