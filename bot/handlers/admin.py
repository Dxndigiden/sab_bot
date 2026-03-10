"""
Админ-панель: статистика, рассылка, запрос подтверждений,
экспорт Excel, поиск команды, удаление команды.
Доступ — только по ADMIN_IDS из config.
"""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from loguru import logger

from bot.keyboards import admin_panel_keyboard, delete_team_keyboard
from bot.states import AdminState
from core.config import settings
from database.crud import get_all_teams, get_stats, search_teams, delete_team_by_id
from services.team_service import broadcast, send_confirmation_requests, build_excel

router = Router()


def _is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids


@router.message(F.text == '⚙️ Админ-панель')
async def show_admin_panel(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        await message.answer('❌ Доступ запрещён.')
        return
    stats = await get_stats()
    await message.answer(
        f'⚙️ <b>Админ-панель</b>\n\n'
        f'📊 Зарегистрировано: <b>{stats["total"]}</b>\n'
        f'✅ Подтверждено: <b>{stats["confirmed"]}</b>\n'
        f'⏳ Ожидает: <b>{stats["pending"]}</b>',
        reply_markup=admin_panel_keyboard(),
        parse_mode='HTML',
    )


@router.callback_query(F.data == 'admin_stats')
async def admin_stats(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id):
        return await callback.answer('Нет доступа', show_alert=True)
    stats = await get_stats()
    await callback.message.edit_text(
        f'📊 <b>Статистика турнира</b>\n\n'
        f'👥 Всего команд: <b>{stats["total"]}</b>\n'
        f'✅ Подтверждено: <b>{stats["confirmed"]}</b>\n'
        f'⏳ Ожидает подтверждения: <b>{stats["pending"]}</b>',
        reply_markup=admin_panel_keyboard(),
        parse_mode='HTML',
    )
    await callback.answer()


@router.callback_query(F.data == 'admin_broadcast')
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id):
        return await callback.answer('Нет доступа', show_alert=True)
    await state.set_state(AdminState.broadcast_text)
    await callback.message.answer('✏️ Введите сообщение для рассылки всем командам:')
    await callback.answer()


@router.message(AdminState.broadcast_text)
async def admin_broadcast_send(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer('⚠️ Текст не может быть пустым.')
        return
    sent, failed = await broadcast(message.bot, message.text)
    logger.info(
        'Рассылка: отправлено={}, не доставлено={} (admin={})', sent, failed, message.from_user.id
    )
    await message.answer(
        f'📢 <b>Рассылка завершена</b>\n\n'
        f'✅ Доставлено: <b>{sent}</b>\n'
        f'❌ Не доставлено: <b>{failed}</b>',
        parse_mode='HTML',
    )
    await state.clear()


@router.callback_query(F.data == 'admin_request_confirm')
async def admin_request_confirm(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id):
        return await callback.answer('Нет доступа', show_alert=True)
    await callback.answer('Отправляю запросы…')
    sent = await send_confirmation_requests(callback.bot)
    logger.info(
        'Запросы подтверждения отправлены: {} команд (admin={})', sent, callback.from_user.id
    )
    await callback.message.answer(
        f'📩 Запрос подтверждения отправлен <b>{sent}</b> командам.\n'
        f'(Уже подтверждённые — пропущены)',
        parse_mode='HTML',
    )


@router.callback_query(F.data == 'admin_export_excel')
async def admin_export_excel(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id):
        return await callback.answer('Нет доступа', show_alert=True)
    teams = await get_all_teams()
    if not teams:
        await callback.answer('Нет зарегистрированных команд.', show_alert=True)
        return
    xlsx_bytes = build_excel(teams)
    file = BufferedInputFile(file=xlsx_bytes, filename='teams.xlsx')
    logger.info('Excel выгружен: {} команд (admin={})', len(teams), callback.from_user.id)
    await callback.message.answer_document(file, caption=f'📊 Команд в базе: {len(teams)}')
    await callback.answer()


@router.callback_query(F.data == 'admin_search')
async def admin_search_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id):
        return await callback.answer('Нет доступа', show_alert=True)
    await state.set_state(AdminState.search_query)
    await callback.message.answer('🔍 Введите название команды или имя капитана:')
    await callback.answer()


@router.message(AdminState.search_query)
async def admin_search_result(message: Message, state: FSMContext) -> None:
    query = (message.text or '').strip()
    if not query:
        await message.answer('⚠️ Введите запрос.')
        return
    teams = await search_teams(query)
    await state.clear()
    if not teams:
        await message.answer(f'🔍 По запросу «{query}» ничего не найдено.')
        return
    lines = [f'🔍 Найдено команд: {len(teams)}\n']
    for t in teams:
        status = '✅' if t.confirmed else '⏳'
        lines.append(
            f'{status} <b>{t.team_name}</b>\n'
            f'   Капитан: {t.captain_name}\n'
            f'   Телефон: {t.phone}\n'
            f'   @{t.tg_username or "—"}'
        )
    await message.answer('\n\n'.join(lines), parse_mode='HTML')


@router.callback_query(F.data == 'admin_delete_team')
async def admin_delete_team_list(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id):
        return await callback.answer('Нет доступа', show_alert=True)
    teams = await get_all_teams()
    if not teams:
        await callback.answer('Команд нет.', show_alert=True)
        return
    await callback.message.edit_text(
        '🗑 Выберите команду для удаления:',
        reply_markup=delete_team_keyboard(teams),
    )
    await callback.answer()


@router.callback_query(F.data.startswith('delete_team_'))
async def admin_delete_team_confirm(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id):
        return await callback.answer('Нет доступа', show_alert=True)
    team_id = int(callback.data.removeprefix('delete_team_'))
    deleted = await delete_team_by_id(team_id)
    if deleted:
        logger.info('Команда id={} удалена админом (admin={})', team_id, callback.from_user.id)
        await callback.answer('✅ Команда удалена.', show_alert=True)
    else:
        await callback.answer('⚠️ Команда не найдена — возможно, уже удалена.', show_alert=True)
    teams = await get_all_teams()
    if teams:
        await callback.message.edit_reply_markup(reply_markup=delete_team_keyboard(teams))
    else:
        await callback.message.edit_text('✅ Все команды удалены.')


@router.callback_query(F.data == 'admin_back')
async def admin_back(callback: CallbackQuery) -> None:
    stats = await get_stats()
    await callback.message.edit_text(
        f'⚙️ <b>Админ-панель</b>\n\n'
        f'📊 Зарегистрировано: <b>{stats["total"]}</b>\n'
        f'✅ Подтверждено: <b>{stats["confirmed"]}</b>\n'
        f'⏳ Ожидает: <b>{stats["pending"]}</b>',
        reply_markup=admin_panel_keyboard(),
        parse_mode='HTML',
    )
    await callback.answer()
