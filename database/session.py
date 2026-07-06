from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.config import settings
from database.models import Base

engine = create_async_engine(
    settings.db_url,
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_recycle=300,
)

Session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def init_db(base=Base) -> None:
    """Создаём таблицы при старте."""
    async with engine.begin() as conn:
        await conn.run_sync(base.metadata.create_all)


async def close_engine() -> None:
    await engine.dispose()