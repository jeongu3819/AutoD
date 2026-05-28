"""
MySQL (HeidiSQL-managed) DB connection.

Expected DATABASE_URL format:
    mysql+pymysql://root:<password>@127.0.0.1:3306/autoD

If the password contains special characters (@, #, %, !, ...), URL-encode them.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings

load_dotenv()

_engine: Engine | None = None
SessionLocal = None


def _resolve_database_url() -> str | None:
    url = get_settings().DATABASE_URL or os.getenv("DATABASE_URL")
    return url or None


def _init() -> None:
    """Build engine + SessionLocal lazily once DATABASE_URL is available."""
    global _engine, SessionLocal
    if _engine is not None:
        return
    url = _resolve_database_url()
    if not url:
        return
    _engine = create_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=3600,
        future=True,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def get_engine() -> Engine | None:
    """Return the MySQL engine. None if DATABASE_URL is not configured yet."""
    _init()
    return _engine


def get_db():
    """FastAPI dependency yielding a SQLAlchemy session."""
    _init()
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL is not configured")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
