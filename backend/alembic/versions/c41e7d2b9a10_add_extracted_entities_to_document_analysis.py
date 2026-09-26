"""add extracted_entities to document_analysis

Legal NER output for /documents/{id}/analyze, grouped by entity type.

Revision ID: c41e7d2b9a10
Revises: aab3307a5ca9
Create Date: 2026-09-26 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c41e7d2b9a10'
down_revision: Union[str, None] = 'aab3307a5ca9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'document_analysis',
        sa.Column('extracted_entities', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('document_analysis', 'extracted_entities')
