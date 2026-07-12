"""Compatibility layer for the canonical database package.

New code must import from ``app.db.base`` and ``app.db.session``. This module
remains temporarily to preserve existing imports during the M1/M2 migration.
"""

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import SessionLocal, engine


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


__all__ = ["Base", "SessionLocal", "engine", "get_session"]
