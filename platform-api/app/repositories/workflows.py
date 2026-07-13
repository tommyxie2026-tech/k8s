"""Compatibility import for the canonical WorkflowRepository.

New code must import from ``app.db.repositories``. This module remains only to
preserve older imports during the M1/M2 migration.
"""

from app.db.repositories import WorkflowRepository

__all__ = ["WorkflowRepository"]
