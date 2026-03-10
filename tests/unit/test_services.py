"""
Тесты сервисного слоя — мокаем CRUD и Bot, проверяем бизнес-логику.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from schemas.team import TeamCreate, TeamRead
from services.team_service import build_excel, RegistrationClosedError


class TestBuildExcel:
    def _make_team(self, **kw):
        t = MagicMock()
        t.team_name = kw.get('team_name', 'Балтика')
        t.captain_name = kw.get('captain_name', 'Иван Иванов')
        t.player2 = 'Пётр Петров'
        t.player3 = 'Сидор Сидоров'
        t.substitute = 'Алексей Алексеев'
        t.phone = '+79001234567'
        t.tg_username = 'cap'
        t.confirmed = kw.get('confirmed', False)
        return t

    def test_returns_bytes(self):
        data = build_excel([self._make_team()])
        assert isinstance(data, bytes)
        assert len(data) > 0

    def test_empty_list(self):
        data = build_excel([])
        assert isinstance(data, bytes)

    def test_confirmed_team(self):
        data = build_excel([self._make_team(confirmed=True)])
        assert isinstance(data, bytes)

    def test_no_tg_username(self):
        t = self._make_team()
        t.tg_username = None
        data = build_excel([t])
        assert isinstance(data, bytes)


@pytest.fixture
def valid_team_data():
    return TeamCreate(
        telegram_id=123,
        tg_username='cap',
        phone='+79001234567',
        team_name='Балтика',
        captain_name='Иван Иванов',
        player2='Пётр Петров',
        player3='Сидор Сидоров',
        substitute='Алексей Алексеев',
    )


@pytest.mark.asyncio
async def test_register_team_success(valid_team_data):
    mock_team = MagicMock()
    mock_team.id = 1
    mock_team.telegram_id = 123
    mock_team.tg_username = 'cap'
    mock_team.phone = '+79001234567'
    mock_team.team_name = 'Балтика'
    mock_team.captain_name = 'Иван Иванов'
    mock_team.player2 = 'Пётр Петров'
    mock_team.player3 = 'Сидор Сидоров'
    mock_team.substitute = 'Алексей Алексеев'
    mock_team.confirmed = False

    with (
        patch('services.team_service.crud.create_team', new=AsyncMock(return_value=mock_team)),
        patch(
            'services.team_service.crud.get_stats',
            new=AsyncMock(return_value={'total': 0, 'confirmed': 0, 'pending': 0}),
        ),
        patch('services.team_service.settings') as mock_settings,
    ):
        mock_settings.MAX_TEAMS = 0
        from services.team_service import register_team

        result = await register_team(valid_team_data)
    assert result is not None
    assert result.team_name == 'Балтика'


@pytest.mark.asyncio
async def test_register_team_duplicate(valid_team_data):
    with (
        patch('services.team_service.crud.create_team', new=AsyncMock(return_value=None)),
        patch(
            'services.team_service.crud.get_stats',
            new=AsyncMock(return_value={'total': 0, 'confirmed': 0, 'pending': 0}),
        ),
        patch('services.team_service.settings') as mock_settings,
    ):
        mock_settings.MAX_TEAMS = 0
        from services.team_service import register_team

        result = await register_team(valid_team_data)
    assert result is None


@pytest.mark.asyncio
async def test_register_team_limit_reached(valid_team_data):
    with (
        patch(
            'services.team_service.crud.get_stats',
            new=AsyncMock(return_value={'total': 16, 'confirmed': 0, 'pending': 0}),
        ),
        patch('services.team_service.settings') as mock_settings,
    ):
        mock_settings.MAX_TEAMS = 16
        from services.team_service import register_team

        with pytest.raises(RegistrationClosedError):
            await register_team(valid_team_data)


@pytest.mark.asyncio
async def test_broadcast_counts():
    mock_team = MagicMock()
    mock_team.telegram_id = 111

    bot = AsyncMock()
    bot.send_message = AsyncMock(side_effect=[None, Exception('blocked')])

    teams = [MagicMock(telegram_id=111), MagicMock(telegram_id=222)]
    with patch('services.team_service.crud.get_all_teams', new=AsyncMock(return_value=teams)):
        from services.team_service import broadcast

        sent, failed = await broadcast(bot, 'Привет!')
    assert sent == 1
    assert failed == 1
