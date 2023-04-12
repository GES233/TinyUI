import asyncio
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from alembic.config import Config as AlembicConfig
from alembic.script import write_hooks

try:
    import black
    from black.mode import Mode
    from black.report import Report

    BLACK_FORMATTER_INSTALLED = True
except (ModuleNotFoundError, ImportError):
    BLACK_FORMATTER_INSTALLED = False

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config: AlembicConfig = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add MetaData object here
# for 'autogenerate' support
from tinyui.infra.deps.database.dao import tiny_sqlite_metadata

target_metadata = tiny_sqlite_metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.
# TODO: Add sqlalchemy url to here.
# sqlalchemy.url reseted every time if you set here.
# config.set_main_option("sqlalchemy.url", get_sqlalchemy_url())


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()


# Use formatter in here is better.
@write_hooks.register("black")
def format_script_with_black(filename: str, option) -> None:
    if not BLACK_FORMATTER_INSTALLED:
        pass
    else:
        black.reformat_one(
            src=Path(filename),
            fast=True,
            write_back=black.WriteBack.YES,
            mode=Mode(
                line_length=79,  # Same as alembic.
            ),
            report=Report(),
        )