from langchain_community.utilities import SQLDatabase

from utils.settings import get_settings


def get_database() -> SQLDatabase:
    settings = get_settings()
    if not settings.database_url:
        raise ValueError("DATABASE_URL is not configured")
    return SQLDatabase.from_uri(settings.database_url)
