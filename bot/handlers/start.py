"""Старт — приветствие, показ меню по роли."""

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.keyboards import main_menu
from core.config import settings
from database.crud import get_team_by_telegram_id

router = Router()

_WELCOME = (
    '👋 Добро пожаловать на регистрацию в турнире 3х3 <b>AB STREETBALL CUP 5</b>\n\n'
    '🏀 Для участия нужно собрать команду из <b>трёх</b> человек\n' 
    '(при желании найти <b>четвёртого</b> в запас),\n'
    'а также быть в отличной форме\n' 
    '<b>22 августа</b> в <b>г. Бийск</b> на 18 школе</b>'
)

_WELCOME_BACK = (
    '👋 С возвращением, <b>{name}</b>!\n\n'
    'Ваша команда <b>{team}</b> уже зарегистрирована.\n'
    'Используйте меню ниже.'
)


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext) -> None:
    await state.clear()

    user_id = message.from_user.id
    is_admin = user_id in settings.admin_ids
    team = await get_team_by_telegram_id(user_id)

    if team:
        text = _WELCOME_BACK.format(
            name=message.from_user.first_name,
            team=team.team_name,
        )
    else:
        text = _WELCOME

    await message.answer(
        text,
        reply_markup=main_menu(is_admin=is_admin, can_register=team is None),
        parse_mode='HTML',
    )
