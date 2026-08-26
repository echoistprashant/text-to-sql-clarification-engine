from sqlalchemy import create_engine, text

from app.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
)


def check_database_connection() -> None:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))