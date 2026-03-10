from aiogram.fsm.state import StatesGroup, State


class RegistrationState(StatesGroup):
    phone = State()
    team_name = State()
    captain_name = State()
    player2 = State()
    player3 = State()
    substitute = State()


class AdminState(StatesGroup):
    broadcast_text = State()  # ждём текст рассылки
    search_query = State()  # ждём поисковый запрос
    delete_confirm = State()  # ждём выбора команды для удаления
