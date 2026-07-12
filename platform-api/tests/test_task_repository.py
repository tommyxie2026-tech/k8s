from sqlalchemy.orm import Session

from app.core.database import Base as LegacyBase
from app.db.base import Base
from app.db.models import TaskModel, TaskPhase
from app.db.session import create_database_engine
from app.models.task import TaskModel as LegacyTaskModel
from app.repositories.task import TaskRepository


def test_legacy_task_imports_point_to_canonical_model() -> None:
    assert LegacyBase is Base
    assert LegacyTaskModel is TaskModel


def test_task_repository_lifecycle_on_sqlite() -> None:
    engine = create_database_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        repository = TaskRepository(session)
        task = repository.create(
            task_id="018f0000-0000-7000-8000-000000000001",
            name="test-task",
            executor_type="ansible",
            command_ref="0092-velero-preflight.yml",
            spec={"extra_vars": {}},
        )

        assert task.kind == "Task"
        assert task.phase == TaskPhase.pending.value
        assert task.status["phase"] == TaskPhase.pending.value

        running = repository.update_phase(task, TaskPhase.running, log_path="/tmp/test-task.log")
        assert running.phase == TaskPhase.running.value
        assert running.started_at is not None
        assert running.log_path == "/tmp/test-task.log"

        completed = repository.update_phase(
            running,
            TaskPhase.succeeded,
            return_code=0,
            stdout="ok",
            stderr="",
        )
        assert completed.phase == TaskPhase.succeeded.value
        assert completed.finished_at is not None
        assert completed.return_code == 0
        assert completed.stdout == "ok"

        fetched = repository.get(completed.id)
        assert fetched is not None
        assert fetched.id == completed.id

        deleted = repository.soft_delete(completed)
        assert deleted.deleted_at is not None
        assert repository.get(deleted.id) is None
        assert repository.get(deleted.id, include_deleted=True) is not None
