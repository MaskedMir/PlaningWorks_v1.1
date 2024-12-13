"""Add role to user

Revision ID: e003ce86499f
Revises: 460e223d6839
Create Date: 2024-12-13 06:11:33.777026

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e003ce86499f'
down_revision: Union[str, None] = '460e223d6839'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Добавление колонки 'role' в таблицу 'users'
    op.add_column('users', sa.Column('role', sa.String(length=50), nullable=False, default='user'))

def downgrade() -> None:
    # Удаление колонки 'role' из таблицы 'users'
    op.drop_column('users', 'role')
