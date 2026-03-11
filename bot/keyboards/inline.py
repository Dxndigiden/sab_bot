from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


_SAB_URL = 'https://t.me/souze_ab'


def confirm_keyboard() -> InlineKeyboardMarkup:
    """Кнопки подтверждения/отказа для участника."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='✅ Подтверждаю', callback_data='confirm_yes'),
                InlineKeyboardButton(text='❌ Отказываюсь', callback_data='confirm_no'),
            ]
        ]
    )


def admin_panel_keyboard() -> InlineKeyboardMarkup:
    """Главная панель админа."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='📊 Статистика', callback_data='admin_stats')],
            [InlineKeyboardButton(text='💌 Рассылка', callback_data='admin_broadcast')],
            [
                InlineKeyboardButton(
                    text='📩 Запросить подтверждения', callback_data='admin_request_confirm'
                )
            ],
            [InlineKeyboardButton(text='📥 Скачать Excel', callback_data='admin_export_excel')],
            [InlineKeyboardButton(text='🔍 Найти команду', callback_data='admin_search')],
            [InlineKeyboardButton(text='🗑 Удалить команду', callback_data='admin_delete_team')],
        ]
    )


def delete_team_keyboard(teams) -> InlineKeyboardMarkup:
    """Список команд для удаления — каждая кнопка = одна команда."""
    rows = [
        [
            InlineKeyboardButton(
                text=f'🗑 {t.team_name} ({t.captain_name})',
                callback_data=f'delete_team_{t.id}',
            )
        ]
        for t in teams
    ]
    rows.append([InlineKeyboardButton(text='↩️ Назад', callback_data='admin_back')])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def sab_link_keyboard() -> InlineKeyboardMarkup:
    """Inline-кнопка со ссылкой на паблик — появляется под карточкой команды."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='📣 Актуальная инфа в SAB', url=_SAB_URL),
            ]
        ]
    )
