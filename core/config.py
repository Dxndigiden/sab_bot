from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BOT_TOKEN: str = 'test_token'

    # Postgres-параметры — используются когда USE_POSTGRES=true
    POSTGRES_USER: str = 'sab'
    POSTGRES_PASSWORD: str = 'sab_secret'
    POSTGRES_HOST: str = 'localhost'
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = 'sab_tournament'
    POSTGRES_SSL: bool = False

    # Если true — собираем URL для Postgres, иначе SQLite
    USE_POSTGRES: bool = False

    ADMIN_IDS: str = ''
    MAX_TEAMS: int = 0

    @property
    def db_url(self) -> str:
        """SQLite локально, Postgres в Docker или в облаке (Neon и т.п.)."""
        if self.USE_POSTGRES:
            url = (
                f'postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}'
                f'@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}'
            )
            if self.POSTGRES_SSL:
                url += '?ssl=require'
            return url
        return 'sqlite+aiosqlite:///./sab.db'

    @property
    def admin_ids(self) -> list[int]:
        return [int(x.strip()) for x in self.ADMIN_IDS.split(',') if x.strip()]

    model_config = {'env_file': '.env', 'env_file_encoding': 'utf-8', 'extra': 'ignore'}


settings = Settings()