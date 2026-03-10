"""Весь доступ к БД — только отсюда. Никакого SQLAlchemy снаружи."""

from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Team
from database.session import Session
from schemas.team import TeamCreate


async def _get_by(field, value, session: AsyncSession) -> Team | None:
    result = await session.execute(select(Team).where(field == value))
    return result.scalar_one_or_none()


async def get_team_by_id(team_id: int) -> Team | None:
    async with Session() as s:
        return await _get_by(Team.id, team_id, s)


async def get_team_by_telegram_id(telegram_id: int) -> Team | None:
    async with Session() as s:
        return await _get_by(Team.telegram_id, telegram_id, s)


async def get_team_by_name(team_name: str) -> Team | None:
    async with Session() as s:
        return await _get_by(Team.team_name, team_name, s)


async def get_team_by_phone(phone: str) -> Team | None:
    async with Session() as s:
        return await _get_by(Team.phone, phone, s)


async def get_all_teams() -> list[Team]:
    async with Session() as s:
        result = await s.execute(select(Team).order_by(Team.id))
        return list(result.scalars().all())


async def get_unconfirmed_teams() -> list[Team]:
    """Только те, кому ещё не отправили запрос подтверждения."""
    async with Session() as s:
        result = await s.execute(select(Team).where(Team.confirmed.is_(False)))
        return list(result.scalars().all())


async def search_teams(query: str) -> list[Team]:
    """Поиск по названию команды или имени капитана."""
    q = f'%{query.lower()}%'
    async with Session() as s:
        result = await s.execute(
            select(Team).where(
                func.lower(Team.team_name).like(q) | func.lower(Team.captain_name).like(q)
            )
        )
        return list(result.scalars().all())


async def get_stats() -> dict:
    """Быстрая сводка: всего / подтверждено / не подтверждено."""
    async with Session() as s:
        total = (await s.execute(select(func.count()).select_from(Team))).scalar_one()
        confirmed = (
            await s.execute(select(func.count()).select_from(Team).where(Team.confirmed.is_(True)))
        ).scalar_one()
    return {'total': total, 'confirmed': confirmed, 'pending': total - confirmed}


async def create_team(team: TeamCreate) -> Team | None:
    """Создаёт команду. None — если нарушена уникальность."""
    async with Session() as s:
        clash = await s.execute(
            select(Team).where(
                (Team.telegram_id == team.telegram_id)
                | (Team.phone == team.phone)
                | (Team.team_name == team.team_name)
            )
        )
        if clash.scalar_one_or_none():
            return None

        obj = Team(**team.model_dump())
        s.add(obj)
        try:
            await s.commit()
        except IntegrityError:
            await s.rollback()
            return None
        await s.refresh(obj)
        return obj


async def confirm_team(telegram_id: int) -> bool:
    """Ставит confirmed=True. False если команда не найдена."""
    async with Session() as s:
        team = await _get_by(Team.telegram_id, telegram_id, s)
        if not team:
            return False
        team.confirmed = True
        await s.commit()
        return True


async def set_confirm_msg_id(telegram_id: int, msg_id: int) -> None:
    """Сохраняем id сообщения с кнопками — потом удалим его."""
    async with Session() as s:
        team = await _get_by(Team.telegram_id, telegram_id, s)
        if team:
            team.confirm_msg_id = msg_id
            await s.commit()


async def delete_team(telegram_id: int) -> bool:
    """Удаляет команду по telegram_id. False если не найдена."""
    async with Session() as s:
        team = await _get_by(Team.telegram_id, telegram_id, s)
        if not team:
            return False
        await s.delete(team)
        await s.commit()
        return True


async def delete_team_by_id(team_id: int) -> bool:
    """Ручное удаление конкретной команды по id (для админа)."""
    async with Session() as s:
        team = await _get_by(Team.id, team_id, s)
        if not team:
            return False
        await s.delete(team)
        await s.commit()
        return True
