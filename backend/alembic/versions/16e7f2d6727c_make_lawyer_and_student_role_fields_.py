"""make lawyer and student role fields nullable

Revision ID: 16e7f2d6727c
Revises: 2b7806a018fc
Create Date: 2026-09-14 16:51:12.019304

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '16e7f2d6727c'
down_revision: Union[str, None] = '2b7806a018fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('lawyers', 'bar_license_no', existing_type=sa.String(length=50), nullable=True)
    op.alter_column('lawyers', 'specialization', existing_type=sa.String(length=120), nullable=True)
    op.alter_column('lawyers', 'bar_year', existing_type=sa.Integer(), nullable=True)
    op.alter_column('students', 'university_id', existing_type=sa.String(length=50), nullable=True)
    op.alter_column('students', 'university_name', existing_type=sa.String(length=150), nullable=True)
    op.alter_column('students', 'current_year', existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    op.alter_column('students', 'current_year', existing_type=sa.Integer(), nullable=False)
    op.alter_column('students', 'university_name', existing_type=sa.String(length=150), nullable=False)
    op.alter_column('students', 'university_id', existing_type=sa.String(length=50), nullable=False)
    op.alter_column('lawyers', 'bar_year', existing_type=sa.Integer(), nullable=False)
    op.alter_column('lawyers', 'specialization', existing_type=sa.String(length=120), nullable=False)
    op.alter_column('lawyers', 'bar_license_no', existing_type=sa.String(length=50), nullable=False)
