import re
from pydantic import BaseModel, Field, field_validator

# 2 или 3 слова на русском, любой регистр
_RU_NAME = re.compile(r'^([а-яёА-ЯЁ]+ ){1,2}[а-яёА-ЯЁ]+$')


def _validate_ru_name(v: str) -> str:
    v = v.strip()
    if not _RU_NAME.match(v):
        raise ValueError('Нужно 2–3 слова на русском языке')
    return v


class TeamCreate(BaseModel):
    telegram_id: int
    tg_username: str | None = None
    phone: str = Field(min_length=5, max_length=20)
    team_name: str = Field(min_length=2, max_length=50)
    captain_name: str = Field(min_length=2, max_length=50)
    player2: str = Field(min_length=2, max_length=50)
    player3: str = Field(min_length=2, max_length=50)
    substitute: str = Field(min_length=2, max_length=50)

    @field_validator('*', mode='before')
    @classmethod
    def strip_strings(cls, v):
        return v.strip() if isinstance(v, str) else v

    @field_validator('captain_name', 'player2', 'player3', 'substitute')
    @classmethod
    def validate_ru_name(cls, v: str) -> str:
        return _validate_ru_name(v)


class TeamRead(BaseModel):
    id: int
    telegram_id: int
    tg_username: str | None
    phone: str
    team_name: str
    captain_name: str
    player2: str
    player3: str
    substitute: str
    confirmed: bool

    model_config = {'from_attributes': True}
