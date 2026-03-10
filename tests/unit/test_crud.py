"""
CRUD-тесты на in-memory SQLite.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from database.models import Base, Team
from schemas.team import TeamCreate


@pytest_asyncio.fixture
async def session():
    """In-memory SQLite, таблицы пересоздаются на каждый тест."""
    engine = create_async_engine('sqlite+aiosqlite:///:memory:', future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        yield s

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


def _team(**overrides) -> Team:
    data = dict(
        telegram_id=111,
        tg_username='cap',
        phone='+79001234567',
        team_name='Балтика',
        captain_name='Иван Иванов',
        player2='Пётр Петров',
        player3='Сидор Сидоров',
        substitute='Алексей Алексеев',
        confirmed=False,
    )
    data.update(overrides)
    return Team(**data)


async def _add(session, **overrides) -> Team:
    t = _team(**overrides)
    session.add(t)
    await session.commit()
    await session.refresh(t)
    return t


@pytest.mark.asyncio
async def test_add_team(session):
    t = await _add(session)
    assert t.id is not None
    assert t.team_name == 'Балтика'


@pytest.mark.asyncio
async def test_unique_telegram_id(session):
    await _add(session, telegram_id=111, team_name='А', phone='+70000000001')
    t2 = _team(telegram_id=111, team_name='Б', phone='+70000000002')
    session.add(t2)
    with pytest.raises(Exception):  # IntegrityError
        await session.commit()


@pytest.mark.asyncio
async def test_unique_phone(session):
    await _add(session, telegram_id=111, phone='+79001234567')
    t2 = _team(telegram_id=222, phone='+79001234567', team_name='Другая')
    session.add(t2)
    with pytest.raises(Exception):
        await session.commit()


@pytest.mark.asyncio
async def test_unique_team_name(session):
    await _add(session, telegram_id=111, team_name='Балтика', phone='+70000000001')
    t2 = _team(telegram_id=222, team_name='Балтика', phone='+70000000002')
    session.add(t2)
    with pytest.raises(Exception):
        await session.commit()


@pytest.mark.asyncio
async def test_confirm_team(session):
    t = await _add(session)
    assert t.confirmed is False
    t.confirmed = True
    await session.commit()
    await session.refresh(t)
    assert t.confirmed is True


@pytest.mark.asyncio
async def test_delete_team(session):
    from sqlalchemy import select

    t = await _add(session)
    await session.delete(t)
    await session.commit()
    result = await session.execute(select(Team).where(Team.id == t.id))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_confirm_msg_id_default_none(session):
    t = await _add(session)
    assert t.confirm_msg_id is None


@pytest.mark.asyncio
async def test_confirm_msg_id_set(session):
    t = await _add(session)
    t.confirm_msg_id = 9999
    await session.commit()
    await session.refresh(t)
    assert t.confirm_msg_id == 9999
