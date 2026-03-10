"""create teams table

Revision ID: 0001
Revises:
Create Date: 2026-03-11
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'teams',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('tg_username', sa.String(64), nullable=True),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('team_name', sa.String(50), nullable=False),
        sa.Column('captain_name', sa.String(50), nullable=False),
        sa.Column('player2', sa.String(50), nullable=False),
        sa.Column('player3', sa.String(50), nullable=False),
        sa.Column('substitute', sa.String(50), nullable=False),
        sa.Column('confirmed', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('confirm_msg_id', sa.Integer(), nullable=True),
        sa.UniqueConstraint('telegram_id', name='uq_teams_telegram_id'),
        sa.UniqueConstraint('phone', name='uq_teams_phone'),
        sa.UniqueConstraint('team_name', name='uq_teams_team_name'),
    )
    op.create_index('ix_teams_telegram_id', 'teams', ['telegram_id'])


def downgrade() -> None:
    op.drop_index('ix_teams_telegram_id', table_name='teams')
    op.drop_table('teams')
