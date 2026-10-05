"""general case types; case number, parties, next hearing

Adds the non-family case types (civil, criminal, commercial, property,
service) to the case_type enum, and nullable case fields: case number,
petitioner, respondent, next hearing date. Existing rows are unchanged:
the enum only gains values and every new column is nullable. The court
(court_code) and the short summary (description) already exist.

Downgrade refuses while any case uses a new type, rather than losing data.

Revision ID: e7b3c9d14a02
Revises: d5a91c3e7f20
Create Date: 2026-10-06 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'e7b3c9d14a02'
down_revision: Union[str, None] = 'd5a91c3e7f20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OLD_TYPES = ('custody', 'inheritance', 'divorce', 'maintenance')
NEW_TYPES = ('civil', 'criminal', 'commercial', 'property', 'service')


def upgrade() -> None:
    # PostgreSQL 12+ allows ADD VALUE inside a transaction (the new values
    # just can't be used until it commits; this migration doesn't use them).
    for value in NEW_TYPES:
        op.execute(f"ALTER TYPE case_type ADD VALUE IF NOT EXISTS '{value}'")
    op.add_column('cases', sa.Column('case_number', sa.String(length=64), nullable=True))
    op.add_column('cases', sa.Column('petitioner', sa.String(length=200), nullable=True))
    op.add_column('cases', sa.Column('respondent', sa.String(length=200), nullable=True))
    op.add_column('cases', sa.Column('next_hearing_date', sa.Date(), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    in_use = conn.execute(sa.text(
        "SELECT count(*) FROM cases WHERE case_type::text IN :types"
    ).bindparams(sa.bindparam('types', expanding=True)), {'types': list(NEW_TYPES)}).scalar()
    if in_use:
        raise RuntimeError(
            f"{in_use} case(s) use the new case types; change them before downgrading."
        )
    op.drop_column('cases', 'next_hearing_date')
    op.drop_column('cases', 'respondent')
    op.drop_column('cases', 'petitioner')
    op.drop_column('cases', 'case_number')
    # PostgreSQL can't drop enum values: rebuild the type with the old ones.
    op.execute("ALTER TYPE case_type RENAME TO case_type_old")
    op.execute(f"CREATE TYPE case_type AS ENUM ({', '.join(repr(v) for v in OLD_TYPES)})")
    op.execute(
        "ALTER TABLE cases ALTER COLUMN case_type TYPE case_type "
        "USING case_type::text::case_type"
    )
    op.execute("DROP TYPE case_type_old")
