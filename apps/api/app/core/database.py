from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings


class Base(DeclarativeBase):
    pass


connect_args: dict = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
elif "pooler.supabase.com:6543" in settings.DATABASE_URL or "pgbouncer" in settings.DATABASE_URL:
    connect_args = {"statement_cache_size": 0}

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=not settings.DATABASE_URL.startswith("sqlite"),
    connect_args=connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    # Ensure all models are imported before create_all
    from app.models import clarification, project, research, settings as ws_settings, vault  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
