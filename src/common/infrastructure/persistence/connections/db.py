from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.common.infrastructure.core import settings

# ── Connection Pool Tuning ─────────────────────────────────────────────────
# Rationale for default values:
#   pool_size=10       — Supports ~50 concurrent requests (10 workers × 5
#                         queries each) without queueing. Matches typical
#                         uvicorn worker counts (4-8) with headroom.
#   max_overflow=20    — Allows burst traffic up to 30 total connections
#                         (10 + 20) without blocking. Prevents connection
#                         starvation during traffic spikes.
#   pool_recycle=3600  — Recycles connections after 1 hour. Postgres
#                         default idle timeout is typically 5-10 minutes
#                         behind PgBouncer or cloud proxies; 3600s avoids
#                         unnecessary reconnect churn while staying well
#                         below common LB/proxy idle-drop thresholds.
#   pool_pre_ping=True — Tests connection before checkout. Catches
#                         dropped connections (network blip, proxy restart)
#                         without waiting for a failed query.
# All values are overridable via env vars (DB_POOL_SIZE, DB_POOL_OVERFLOW,
# DB_POOL_RECYCLE) set in Settings.
engine = create_async_engine(
    url=settings.DB_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_POOL_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=settings.DB_POOL_RECYCLE,
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
