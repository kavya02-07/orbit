"""
SQLAlchemy engine, session factory, and declarative base for SQLite.
Fast, reliable in-process database management.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def get_engine():
    settings = get_settings()
    url = settings.database_url
    if "+aiosqlite" in url:
        url = url.replace("+aiosqlite", "")
    return create_engine(
        url,
        connect_args={"check_same_thread": False},
        echo=False,
    )


# Module-level singletons
_engine = None
_session_factory = None


def init_db_engine():
    global _engine, _session_factory
    _engine = get_engine()
    _session_factory = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return _engine


def get_db():
    global _session_factory
    if _session_factory is None:
        init_db_engine()
    db = _session_factory()
    try:
        yield db
    finally:
        db.close()
