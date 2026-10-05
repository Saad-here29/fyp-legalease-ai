"""Alembic environment file — points to SQLAlchemy metadata."""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from app.core.config import settings
from app.db.base import Base

# Import all models here so Alembic sees them
from app.models import *  # noqa: F401,F403

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    # `alembic -x schema=NAME ...` runs the migrations inside that schema
    # (tables, enum types and alembic_version), e.g. to test a migration up
    # and down on a throwaway schema before touching the real tables.
    schema = context.get_x_argument(as_dictionary=True).get("schema")
    with connectable.connect() as connection:
        if schema:
            from sqlalchemy import text
            connection.execute(text(f'SET search_path TO "{schema}"'))
            connection.commit()  # session setting; Alembic then opens its own transaction
        context.configure(connection=connection, target_metadata=target_metadata,
                          version_table_schema=schema)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
