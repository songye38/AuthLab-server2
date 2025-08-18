"""make hashed_password nullable

Revision ID: 8f7ecb9aa467
Revises: 
Create Date: 2025-08-18 21:26:17.074547

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f7ecb9aa467'
down_revision: Union[str, Sequence[str], None] = None  # 🔑 나중에 이전 revision id 넣어야 함
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        'users',
        'hashed_password',
        existing_type=sa.VARCHAR(),
        nullable=True
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        'users',
        'hashed_password',
        existing_type=sa.VARCHAR(),
        nullable=False
    )
