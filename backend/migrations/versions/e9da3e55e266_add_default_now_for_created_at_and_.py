"""Add default now() for created_at and updated_at on users table

Revision ID: e9da3e55e266
Revises: 1e72c2ea6c6a
Create Date: 2025-02-24 00:01:27.897490

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e9da3e55e266'
down_revision: Union[str, None] = '1e72c2ea6c6a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure created_at and updated_at have a default of now()
    op.alter_column(
        'users', 'created_at',
        existing_type=sa.DateTime(timezone=True),
        server_default=sa.text('now()'),
        existing_nullable=False
    )
    op.alter_column(
        'users', 'updated_at',
        existing_type=sa.DateTime(timezone=True),
        server_default=sa.text('now()'),
        existing_nullable=False
    )

def downgrade() -> None:    
    # Remove the server defaults if needed.
    op.alter_column(
        'users', 'created_at',
        existing_type=sa.DateTime(timezone=True),
        server_default=None,
        existing_nullable=False
    )
    op.alter_column(
        'users', 'updated_at',
        existing_type=sa.DateTime(timezone=True),
        server_default=None,
        existing_nullable=False
    )
