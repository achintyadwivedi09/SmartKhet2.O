"""
SmartKhet 2.0 — Database Setup
SQLAlchemy engine, session factory, and Base for ORM models.
"""
from __future__ import annotations
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from typing import Generator
from app.config import DATABASE_URL


class Base(DeclarativeBase):
    pass


# SQLite: enable WAL mode for better concurrent read performance
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create all tables (safe to call multiple times)."""
    # Import models so they register with Base before create_all
    from models import db_models  # noqa: F401
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yields a SQLAlchemy session and closes it after."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
