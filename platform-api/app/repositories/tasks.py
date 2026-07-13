"""Compatibility import for the canonical TaskRepository.

New code must import from ``app.db.repositories``. This module remains only to
preserve older imports during the M1/M2 migration.
"""

from app.db.repositories import TaskRepository

__all__ = ["TaskRepository"]
