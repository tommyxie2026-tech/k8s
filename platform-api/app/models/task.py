"""Compatibility imports for the canonical Task persistence model.

New code must import TaskModel and TaskPhase from ``app.db.models``.
This module remains temporarily so existing imports do not break while M1/M2
migrate consumers to the canonical persistence package.
"""

from app.db.models import TaskModel, TaskPhase

__all__ = ["TaskModel", "TaskPhase"]
