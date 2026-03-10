from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import BigInteger, String, Boolean


class Base(DeclarativeBase):
    pass


class Team(Base):
    __tablename__ = 'teams'

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    tg_username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    team_name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    captain_name: Mapped[str] = mapped_column(String(50), nullable=False)
    player2: Mapped[str] = mapped_column(String(50), nullable=False)
    player3: Mapped[str] = mapped_column(String(50), nullable=False)
    substitute: Mapped[str] = mapped_column(String(50), nullable=False)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    confirm_msg_id: Mapped[int | None] = mapped_column(nullable=True)
