from collections.abc import Mapping
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.exc import NoSuchModuleError


DATABASE_DRIVER_HINTS = {
    "postgres": "Use a PostgreSQL URL like postgresql://user:pass@host:5432/db.",
    "postgresql": "Install psycopg2-binary or use postgresql+psycopg2://user:pass@host:5432/db.",
    "mysql": "Install pymysql or use mysql+pymysql://user:pass@host:3306/db.",
    "mariadb": "Install pymysql or use mariadb+pymysql://user:pass@host:3306/db.",
}

DATABASE_URL_ALIASES = {
    "postgres://": "postgresql+psycopg2://",
    "postgresql://": "postgresql+psycopg2://",
    "mysql://": "mysql+pymysql://",
    "mariadb://": "mariadb+pymysql://",
}


def normalize_database_url(database_url: str) -> str:
    """Normalize common database URL aliases for SQLAlchemy."""
    url = database_url.strip()
    if not url:
        raise ValueError("Database URL is empty")

    lowered = url.lower()
    for alias, replacement in DATABASE_URL_ALIASES.items():
        if lowered.startswith(alias):
            return replacement + url[len(alias):]
    return url


def create_database_engine(database_url: str) -> Engine:
    """Create a SQLAlchemy engine from a user-provided URL."""
    try:
        return create_engine(
            normalize_database_url(database_url),
            pool_pre_ping=True,
            future=True,
        )
    except NoSuchModuleError as exc:
        dialect = database_url.split(":", 1)[0].lower()
        hint = DATABASE_DRIVER_HINTS.get(
            dialect,
            "Install the SQLAlchemy driver for this database type.",
        )
        raise ValueError(f"Unsupported database URL or missing driver. {hint}") from exc


def read_query(database_url: str, query: str) -> pd.DataFrame:
    """Run a SQL query with pandas using a short-lived engine."""
    engine = create_database_engine(database_url)
    try:
        with engine.connect() as connection:
            return pd.read_sql_query(query, connection)
    finally:
        engine.dispose()


def extract_schema_context(database_url: str) -> tuple[dict[str, Any], str]:
    """Extract table metadata using SQLAlchemy's inspection API."""
    engine = create_database_engine(database_url)
    try:
        inspector = inspect(engine)

        schema_context = {}
        for table_name in inspector.get_table_names():
            columns = inspector.get_columns(table_name)
            primary_keys = inspector.get_pk_constraint(table_name)
            foreign_keys = inspector.get_foreign_keys(table_name)
            indexes = inspector.get_indexes(table_name)

            column_info = [_column_context(column) for column in columns]
            schema_context[table_name] = {
                "columns": column_info,
                "primary_keys": primary_keys.get("constrained_columns", []),
                "foreign_keys": [
                    {
                        "constrained_columns": key["constrained_columns"],
                        "referred_table": key["referred_table"],
                        "referred_columns": key["referred_columns"],
                    }
                    for key in foreign_keys
                ],
                "indexes": [
                    {
                        "name": index["name"],
                        "columns": index["column_names"],
                        "unique": index["unique"],
                    }
                    for index in indexes
                ],
                "create_statement": _create_statement(table_name, column_info),
            }

        return schema_context, engine.dialect.name
    finally:
        engine.dispose()


def _column_context(column: Mapping[str, Any]) -> dict[str, Any]:
    default = column.get("default")
    return {
        "name": column["name"],
        "type": str(column["type"]),
        "nullable": column.get("nullable", True),
        "default": str(default) if default else None,
    }


def _create_statement(table_name: str, columns: list[dict[str, Any]]) -> str:
    column_defs = [f"{column['name']} {column['type']}" for column in columns]
    return f"CREATE TABLE {table_name} ({', '.join(column_defs)})"
