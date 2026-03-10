from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove


def phone_keyboard() -> ReplyKeyboardMarkup:
    """Единственная кнопка — шаринг контакта. После нажатия исчезает."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text='📱 Отправить номер', request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def main_menu(is_admin: bool, can_register: bool) -> ReplyKeyboardMarkup:
    """Главное меню. Кнопки появляются по роли и статусу регистрации."""
    rows = []
    if can_register:
        rows.append([KeyboardButton(text='📝 Регистрация')])
    else:
        rows.append([KeyboardButton(text='📋 Моя команда')])
    if is_admin:
        rows.append([KeyboardButton(text='⚙️ Админ-панель')])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def registered_menu() -> ReplyKeyboardMarkup:
    """Меню для уже зарегистрированного пользователя."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text='📋 Моя команда')]],
        resize_keyboard=True,
    )


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()
