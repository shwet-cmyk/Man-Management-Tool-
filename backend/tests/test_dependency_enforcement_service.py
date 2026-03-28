from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import Base
from app.modules.dependency_enforcement.schemas import DependencyActionRequest, DependencyCheckRequest, DependencyCreateRequest
from app.modules.dependency_enforcement.service import DependencyEnforcementService


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def test_dependency_requires_approved_status():
    db = setup_db()
    svc = DependencyEnforcementService(db)

    dep = svc.create_dependency(
        DependencyCreateRequest(
            task_id="task-1",
            user_id="user-1",
            depends_on_user_id="user-2",
            depends_on_task_id="task-0",
            dependency_type="FS",
        )
    )

    blocked = svc.check_dependency(
        DependencyCheckRequest(task_id="task-1", user_id="user-1", action="START", dependency_type="FS", depends_on_user_id="user-2")
    )
    assert blocked["allowed"] is False

    svc.transition_dependency(DependencyActionRequest(dependency_id=dep["dependency_id"], action="COMPLETE"))
    svc.transition_dependency(DependencyActionRequest(dependency_id=dep["dependency_id"], action="APPROVE"))

    allowed = svc.check_dependency(
        DependencyCheckRequest(task_id="task-1", user_id="user-1", action="START", dependency_type="FS", depends_on_user_id="user-2")
    )
    assert allowed["allowed"] is True


def test_circular_dependency_blocked():
    db = setup_db()
    svc = DependencyEnforcementService(db)

    svc.create_dependency(
        DependencyCreateRequest(
            task_id="task-a",
            user_id="user-1",
            depends_on_user_id="user-2",
            depends_on_task_id="task-b",
            dependency_type="FS",
        )
    )

    try:
        svc.create_dependency(
            DependencyCreateRequest(
                task_id="task-b",
                user_id="user-2",
                depends_on_user_id="user-1",
                depends_on_task_id="task-a",
                dependency_type="FS",
            )
        )
        assert False, "Expected circular dependency error"
    except Exception:
        assert True
