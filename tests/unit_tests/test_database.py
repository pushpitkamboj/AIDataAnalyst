import sqlite3

from utils.database import extract_schema_context, normalize_database_url, read_query


def test_normalize_database_url_aliases() -> None:
    assert (
        normalize_database_url("postgres://user:pass@localhost:5432/app")
        == "postgresql+psycopg2://user:pass@localhost:5432/app"
    )
    assert (
        normalize_database_url("mysql://user:pass@localhost:3306/app")
        == "mysql+pymysql://user:pass@localhost:3306/app"
    )


def test_sqlite_schema_and_query(tmp_path) -> None:
    db_path = tmp_path / "sales.db"
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "CREATE TABLE sales (id INTEGER PRIMARY KEY, region TEXT, revenue REAL)"
        )
        connection.executemany(
            "INSERT INTO sales (region, revenue) VALUES (?, ?)",
            [("North", 1200.0), ("South", 950.0)],
        )

    database_url = f"sqlite:///{db_path}"
    schema_context, dialect = extract_schema_context(database_url)
    result = read_query(database_url, "SELECT SUM(revenue) AS total_revenue FROM sales")

    assert dialect == "sqlite"
    assert schema_context["sales"]["columns"][1]["name"] == "region"
    assert result.to_dict(orient="records") == [{"total_revenue": 2150.0}]
