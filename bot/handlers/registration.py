"""
Регистрация команды — пошаговый FSM.
Каждый шаг валидирует ввод и либо переходит дальше, либо просит повторить.
"""

import re
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from loguru import logger

from bot.keyboards import phone_keyboard, main_menu, registered_menu, sab_link_keyboard
from bot.states import RegistrationState
from core.config import settings
from database.crud import (
    get_team_by_telegram_id,
    get_team_by_name,
    get_team_by_phone,
)
from schemas.team import TeamCreate
from services.team_service import register_team, RegistrationClosedError

router = Router()

_RU_NAME = re.compile(r'^([а-яёА-ЯЁ]+ ){1,2}[а-яёА-ЯЁ]+$')


def _fmt_team_card(team) -> str:
    confirmed = '✅ Подтверждено' if team.confirmed else '⏳ Ожидает подтверждения'
    return (
        f'📋 <b>Данные команды:</b>\n\n'
        f'🏀 <b>Команда:</b> {team.team_name}\n'
        f'👤 <b>Капитан:</b> {team.captain_name}\n'
        f'👥 <b>Игрок 2:</b> {team.player2}\n'
        f'👥 <b>Игрок 3:</b> {team.player3}\n'
        f'🔄 <b>Запасной:</b> {team.substitute}\n'
        f'📱 <b>Телефон:</b> {team.phone}\n'
        f'💬 <b>Telegram:</b> @{team.tg_username or "—"}\n\n'
        f'Статус: {confirmed}'
    )


async def _err(message: Message, text: str) -> None:
    await message.answer(f'⚠️ {text}')


@router.message(F.text == '📝 Регистрация')
async def start_registration(message: Message, state: FSMContext) -> None:
    await state.clear()

    team = await get_team_by_telegram_id(message.from_user.id)
    if team:
        await message.answer(
            f'Вы уже зарегистрированы ✅\n\n{_fmt_team_card(team)}',
            reply_markup=registered_menu(),
            parse_mode='HTML',
        )
        return

    await state.update_data(
        telegram_id=message.from_user.id,
        tg_username=message.from_user.username,
    )
    await state.set_state(RegistrationState.phone)
    await message.answer(
        '📱 Для регистрации сначала поделитесь номером телефона.\nНажмите кнопку ниже 👇',
        reply_markup=phone_keyboard(),
    )


@router.message(RegistrationState.phone)
async def handle_phone(message: Message, state: FSMContext) -> None:
    if not (message.contact and message.contact.phone_number):
        await _err(
            message,
            'Пожалуйста, используйте кнопку «📱 Отправить номер»,\nа не вводите телефон вручную.',
        )
        return

    phone = message.contact.phone_number
    if await get_team_by_phone(phone):
        await _err(
            message, 'Этот номер уже зарегистрирован.\nОбратитесь к организаторам, если это ошибка.'
        )
        return

    await state.update_data(phone=phone)
    await state.set_state(RegistrationState.team_name)
    await message.answer('✏️ Введите <b>название команды</b>:', parse_mode='HTML')


@router.message(RegistrationState.team_name)
async def handle_team_name(message: Message, state: FSMContext) -> None:
    name = (message.text or '').strip()
    if not name or len(name) < 2:
        await _err(message, 'Название должно быть не короче 2 символов.')
        return
    if len(name) > 50:
        await _err(message, 'Название слишком длинное (макс. 50 символов).')
        return
    if await get_team_by_name(name):
        await _err(message, f'Команда «{name}» уже зарегистрирована.\nПридумайте другое название.')
        return

    await state.update_data(team_name=name)
    await state.set_state(RegistrationState.captain_name)
    await message.answer(
        '👤 Введите <b>имя и фамилию капитана</b> (2–3 слова на русском):', parse_mode='HTML'
    )


async def _handle_player(
    message: Message,
    state: FSMContext,
    field: str,
    next_state,
    next_prompt: str,
) -> None:
    value = (message.text or '').strip()
    if not _RU_NAME.match(value):
        await _err(message, 'Введите 2 или 3 слова на русском языке.\nНапример: <i>Иван Иванов</i>')
        return

    await state.update_data({field: value})

    if next_state:
        await state.set_state(next_state)
        await message.answer(next_prompt, parse_mode='HTML')
        return

    data = await state.get_data()
    try:
        team = await register_team(TeamCreate(**data))
    except RegistrationClosedError:
        logger.warning(
            'Регистрация закрыта — лимит команд достигнут (user_id={})', message.from_user.id
        )
        await message.answer('😔 Регистрация закрыта — достигнут лимит команд.')
        await state.clear()
        return

    if team is None:
        logger.warning('Дубликат при регистрации (user_id={})', message.from_user.id)
        await message.answer(
            '❌ Не удалось сохранить данные — возможно, телефон или название команды уже заняты.\n'
            'Попробуйте ещё раз или обратитесь к организаторам.'
        )
        await state.clear()
        return

    logger.info(
        "Новая команда зарегистрирована: '{}' (user_id={})", team.team_name, message.from_user.id
    )
    is_admin = message.from_user.id in settings.admin_ids
    await message.answer(
        f'🎉 <b>Регистрация завершена!</b>\n\n{_fmt_team_card(team)}',
        reply_markup=main_menu(is_admin=is_admin, can_register=False),
        parse_mode='HTML',
    )
    await message.answer('👇 Следите за новостями турнира:', reply_markup=sab_link_keyboard())
    await state.clear()


@router.message(RegistrationState.captain_name)
async def handle_captain(message: Message, state: FSMContext) -> None:
    await _handle_player(
        message,
        state,
        'captain_name',
        RegistrationState.player2,
        '👥 Введите <b>имя и фамилию Игрока 2</b>:',
    )


@router.message(RegistrationState.player2)
async def handle_player2(message: Message, state: FSMContext) -> None:
    await _handle_player(
        message,
        state,
        'player2',
        RegistrationState.player3,
        '👥 Введите <b>имя и фамилию Игрока 3</b>:',
    )


@router.message(RegistrationState.player3)
async def handle_player3(message: Message, state: FSMContext) -> None:
    await _handle_player(
        message,
        state,
        'player3',
        RegistrationState.substitute,
        '🔄 Введите <b>имя и фамилию запасного игрока</b>:',
    )


@router.message(RegistrationState.substitute)
async def handle_substitute(message: Message, state: FSMContext) -> None:
    await _handle_player(message, state, 'substitute', None, '')


@router.message(F.text == '📋 Моя команда')
async def my_team(message: Message) -> None:
    team = await get_team_by_telegram_id(message.from_user.id)
    if not team:
        await message.answer('Вы ещё не зарегистрированы. Нажмите «📝 Регистрация».')
        return
    await message.answer(_fmt_team_card(team), parse_mode='HTML')
    await message.answer('👇 Следите за новостями турнира:', reply_markup=sab_link_keyboard())
