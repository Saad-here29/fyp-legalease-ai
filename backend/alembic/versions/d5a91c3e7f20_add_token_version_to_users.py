"""add token_version to users

Per-user token version carried in every JWT as "tv". Logout bumps it, so
the access and refresh tokens issued before it stop working.

Revision ID: d5a91c3e7f20
Revises: c41e7d2b9a10
Create Date: 2026-10-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd5a91c3e7f20'
down_revision: Union[str, None] = 'c41e7d2b9a10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('token_version', sa.Integer(), server_default='0', nullable=False),
    )


def downgrade() -> None:
    op.drop_column('users', 'token_version')
