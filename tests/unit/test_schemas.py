"""Тесты схем — валидация данных команды до БД."""

import pytest
from pydantic import ValidationError
from schemas.team import TeamCreate, _validate_ru_name


def _base(**overrides) -> dict:
    """Минимально валидный payload команды."""
    data = dict(
        telegram_id=123456,
        tg_username='cap',
        phone='+79001234567',
        team_name='Балтика',
        captain_name='Иван Иванов',
        player2='Пётр Петров',
        player3='Сидор Сидоров',
        substitute='Алексей Алексеев',
    )
    data.update(overrides)
    return data


class TestRuNameValidator:
    def test_two_words_ok(self):
        assert _validate_ru_name('Иван Иванов') == 'Иван Иванов'

    def test_three_words_ok(self):
        assert _validate_ru_name('Иван Иванович Иванов') == 'Иван Иванович Иванов'

    def test_strips_spaces(self):
        assert _validate_ru_name('  Иван Иванов  ') == 'Иван Иванов'

    def test_one_word_fails(self):
        with pytest.raises(ValueError):
            _validate_ru_name('Иван')

    def test_latin_fails(self):
        with pytest.raises(ValueError):
            _validate_ru_name('Ivan Ivanov')

    def test_four_words_fails(self):
        with pytest.raises(ValueError):
            _validate_ru_name('А Б В Г')


class TestTeamCreate:
    def test_valid_payload(self):
        team = TeamCreate(**_base())
        assert team.team_name == 'Балтика'

    def test_strips_whitespace_in_team_name(self):
        team = TeamCreate(**_base(team_name='  Балтика  '))
        assert team.team_name == 'Балтика'

    def test_empty_team_name_fails(self):
        with pytest.raises(ValidationError):
            TeamCreate(**_base(team_name=''))

    def test_latin_captain_fails(self):
        with pytest.raises(ValidationError):
            TeamCreate(**_base(captain_name='Ivan Ivanov'))

    def test_short_phone_fails(self):
        with pytest.raises(ValidationError):
            TeamCreate(**_base(phone='123'))

    def test_tg_username_optional(self):
        team = TeamCreate(**_base(tg_username=None))
        assert team.tg_username is None
