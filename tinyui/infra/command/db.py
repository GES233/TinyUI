import click
from typing import Any

from . import manage
from ..deps.database.settings import database_dev, database_test, database_prod


@manage.group
def database():
    """Command reated to database(if you are not developer, do not run this)."""

    ...


def initializedb(mode: str) -> None:
    """Initialize database."""

    import sqlite3
    from pathlib import Path
    from alembic import command as alembic_command
    from alembic.config import Config as AlembicConfig
    from alembic.util.exc import AutogenerateDiffsDetected, CommandError

    from ..helpers.path import PROJECT_PATH

    if mode == "dev":
        database_config = database_dev
    elif mode == "test":
        database_config = database_test
    else:
        database_config = database_prod

    config = AlembicConfig(str(Path(PROJECT_PATH / "alembic.ini")))
    config.set_main_option("sqlalchemy.url", database_config.uri)
    config.set_section_option(
        config.config_ini_section, "sqlalchemy.url", database_config.uri
    )

    if mode == "dev":
        # Create database.
        conn = sqlite3.connect("." + database_config.uri.split("//")[-1])
        del conn  # Only used to create database.

        try:
            alembic_command.check(config)
        except AutogenerateDiffsDetected as autogenerate_exc:
            click.secho(
                "[ERROR]   AutogenerateDiffsDetected raised:\n"
                + autogenerate_exc.args[0],
                fg="red",
            )
            click.secho(
                "[INFO]    Now will generate migrate scripts and upgrade to database.",
                fg="green",
            )
            alembic_command.revision(
                config, message="Generating migrate scripts.", autogenerate=True
            )
            alembic_command.upgrade(config, "head")
        except CommandError:
            # alembic.autogenerate.api._run_environment
            # raise util.CommandError("Target database is not up to date.")
            try:
                alembic_command.upgrade(config, "head")
            except CommandError:
                click.secho(
                    f"[ERROR]   Can't locate revision identified in database {config.get_main_option('sqlalchemy.url')}.",
                    fg="red",
                )
            else:
                click.secho("[INFO]    OK.", fg="green")
        else:
            click.secho("[INFO]    OK.", fg="green")
    else:
        # Create database.
        conn = sqlite3.connect("." + database_config.uri.split("//")[-1])
        del conn  # Only used to create database.
        # Best may is to let it crash.
        try:
            alembic_command.check(config)
        except AutogenerateDiffsDetected as autogenerate_exc:
            click.secho(
                "[ERROR]   AutogenerateDiffsDetected raised:\n"
                + autogenerate_exc.args[0],
                fg="red",
            )
            click.secho(
                "[INFO]    Now will generate migrate scripts and upgrade to database.",
                fg="green",
            )
            alembic_command.revision(
                config, message="Generating migrate scripts.", autogenerate=True
            )
            click.secho(
                "[WARINING] The following operation will change the contents of the "
                "database and may cause data loss.",
                fg="yellow",
            )
            loss = click.confirm(click.style("Do you still want to operate it?", fg="red"), default=False)
            # TODO: Drop all.
            # click.secho("[INFO]    OK.", fg="green")
        except CommandError:
            # database not followed script.
            click.secho(
                "[WARINING] The following operation will change the contents of the "
                "database and may cause data loss.",
                fg="yellow",
            )
            loss = click.confirm(click.style("Do you still want to operate it?", fg="red"), abort=True)
            if loss:
                alembic_command.upgrade(config, "head")
                click.secho("[INFO]    OK.", fg="green")
        else:
            click.secho("[INFO]    OK.", fg="green")


click.option("--dev", "mode", flag_value="dev", default=True)(
    click.option("--pro", "mode", flag_value="prod")(
        database.command("init")(initializedb)
    )
)


@database.command("docs")
@click.option("--dev", "mode", flag_value="dev", default=True)
@click.option("--pro", "mode", flag_value="prod")
def updatedocs(mode: str) -> None:
    """Update fixed document into databse."""

    # TODO: Replace code at here to:
    # - CLI: adapter
    # - Application: Usecase of convert md to md(file path to route).
    # - Implement: infra/deps/database
    # Flowchart:
    # check database => fetch dir => work, parse and load

    import asyncio
    from sqlalchemy import Table
    from sqlalchemy.sql import delete, update
    from sqlalchemy.ext.asyncio import AsyncEngine
    from ..deps.database.service import enginefromconfig
    from ..deps.document.dir import build_index
    from ..deps.document.settings import document as docconf
    from ..deps.database.dao.document import document_table

    # Same as init.
    if mode == "dev":
        database_config = database_dev
    elif mode == "test":
        database_config = database_test
    else:
        database_config = database_prod

    async_engine = enginefromconfig(database_config)

    docs_index = build_index(docconf.path, True)

    # TODO: Update link here.
    # Name with language in link => link to route with name.

    async def loaddocsdata(
        engine: AsyncEngine, table: Table, data: Any, delete_table: bool = True
    ) -> None:
        async with engine.begin() as conn:
            if delete_table:
                stmt_del = delete(table)
                await conn.execute(stmt_del)
            ...

        await engine.dispose()

    try:
        asyncio.run(loaddocsdata(async_engine, document_table, docs_index))
    except Exception as e:
        click.secho(
            "[ERROR]   Here's a error raised:\n" + str(e),
            fg="red",
        )
    else:
        click.secho("[INFO]    OK.", fg="green")
