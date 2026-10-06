"""scraping prototype: scraped_documents and scrape_runs

Additive only: two new tables, nothing existing is touched. Branch
"scraping"; not applied to the shared database until the merge is approved.

Revision ID: a3c5e7f90b12
Revises: e7b3c9d14a02
Create Date: 2026-10-06 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.db.types import JSONBType, UUIDType

revision: str = 'a3c5e7f90b12'
down_revision: Union[str, None] = 'e7b3c9d14a02'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'scraped_documents',
        sa.Column('id', UUIDType, primary_key=True),
        sa.Column('source_name', sa.String(120), nullable=False),
        sa.Column('source_url', sa.String(1000), nullable=False),
        sa.Column('pdf_url', sa.String(1000), nullable=True),
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('content_type', sa.String(20), nullable=False),
        sa.Column('content_hash', sa.String(64), nullable=True),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('fetched_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('first_seen_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='staged'),
        sa.Column('change_kind', sa.String(20), nullable=True),
        sa.Column('in_corpus', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_latest', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('run_id', UUIDType, nullable=True),
        sa.CheckConstraint("status IN ('staged', 'approved', 'rejected')", name='ck_scraped_documents_status'),
    )
    op.create_index('ix_scraped_documents_url_latest', 'scraped_documents', ['source_url', 'is_latest'])
    op.create_table(
        'scrape_runs',
        sa.Column('id', UUIDType, primary_key=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('pages_checked', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('new_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('changed_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('per_source', JSONBType, nullable=True),
        sa.Column('dry_run', sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_table('scrape_runs')
    op.drop_index('ix_scraped_documents_url_latest', table_name='scraped_documents')
    op.drop_table('scraped_documents')
