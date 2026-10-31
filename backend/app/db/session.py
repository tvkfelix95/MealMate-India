from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


@lru_cache
def get_engine():
    """Create an engine lazily; this does not connect or create tables."""
    return create_engine(get_settings().database_url, pool_pre_ping=True)


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    """Return a session factory for future database-backed routes."""
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    """Yield a database session for routes that explicitly need one."""
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()


def check_database_connectivity(engine: Engine | None = None) -> bool:
    """Run a minimal database probe without exposing connection details."""
    active_engine = engine or get_engine()
    try:
        with active_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False
