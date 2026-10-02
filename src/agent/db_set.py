from utils.database import create_database_engine
from utils.settings import get_settings


def get_database():
    settings = get_settings()
    if not settings.database_url:
        raise ValueError("DATABASE_URL is not configured")
    return create_database_engine(settings.database_url)
