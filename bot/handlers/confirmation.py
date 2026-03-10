"""
Хендлер confirm_yes / confirm_no — приходит от участников.
Сообщение с кнопками удаляется после ответа, повторное нажатие не сработает.
"""

from aiogram import Router
from aiogram.types import CallbackQuery
from loguru import logger

from database.crud import get_team_by_telegram_id
from services.team_service import confirm_participation, decline_participation

router = Router()


@router.callback_query(lambda c: c.data in ('confirm_yes', 'confirm_no'))
async def handle_confirmation(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    team = await get_team_by_telegram_id(user_id)

    if not team:
        await callback.answer('Команда не найдена.', show_alert=True)
        try:
            await callback.message.delete()
        except Exception:
            pass
        return

    if team.confirmed and callback.data == 'confirm_yes':
        await callback.answer('Вы уже подтвердили участие ✅', show_alert=True)
        return

    msg_id = callback.message.message_id
    chat_id = callback.message.chat.id

    if callback.data == 'confirm_yes':
        await confirm_participation(user_id, callback.bot, chat_id, msg_id)
        logger.info("Участие подтверждено: '{}' (user_id={})", team.team_name, user_id)
        await callback.bot.send_message(
            chat_id,
            '✅ <b>Участие подтверждено!</b>\n\nДо встречи на турнире 🏀',
            parse_mode='HTML',
        )
    else:
        await decline_participation(user_id, callback.bot, chat_id, msg_id)
        logger.info("Отказ от участия: '{}' (user_id={})", team.team_name, user_id)
        await callback.bot.send_message(
            chat_id,
            '❌ Вы отказались от участия.\nВаша заявка удалена.',
        )

    await callback.answer()
