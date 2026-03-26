from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.database.session import Base
from app.models.ref_employee import RefEmployee
from app.models.wm_task import WmTask
from app.models.wm_task_child_item import WmTaskChildItem
from app.models.wm_task_participant import WmTaskParticipant
from app.models.wm_task_participant_dependency import WmTaskParticipantDependency
from app.models.wm_task_participant_handoff import WmTaskParticipantHandoff
from app.models.wm_task_participant_submission import WmTaskParticipantSubmission
from app.modules.tasks.schemas import ChildItemCreateRequest, ChildItemReorderRequest, ChildItemStatusRequest, ParticipantSubmitRequest, SubmissionDecisionRequest, TaskCreateRequest, TaskParticipantsRequest, TaskStatusTransitionRequest
from app.modules.tasks.service import TaskService


@pytest.fixture(autouse=True)
def disable_strict_master_validation():
    previous = settings.strict_master_validation
    settings.strict_master_validation = False
    yield
    settings.strict_master_validation = previous


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def seed_employee(db, emp_id: int, active: bool = True):
    db.add(
        RefEmployee(
            emp_id=emp_id,
            employee_name=f"Emp {emp_id}",
            company_id=1,
            monthly_ctc=Decimal("100000"),
            hourly_cost=Decimal("625"),
            is_active=active,
            last_synced_at=datetime.utcnow(),
        )
    )
    db.commit()


def base_payload() -> TaskCreateRequest:
    now = datetime.utcnow()
    return TaskCreateRequest(
        company_id=1,
        title="Prepare GST Review",
        task_type="Task",
        priority_code="Medium",
        primary_owner_emp_id=100,
        contributor_emp_ids=[101],
        manager_emp_id=102,
        reviewer_emp_id=201,
        billable_flag=False,
        billed_amount=Decimal("0"),
        estimated_hours=Decimal("6"),
        planned_start=now,
        due_at=now + timedelta(days=2),
        save_mode="SUBMIT",
    )


def create_task_fixture(db):
    for emp_id in [100, 101, 102, 201]:
        seed_employee(db, emp_id)
    task_id = TaskService(db).create_task(base_payload(), user_id=100)["task_id"]
    task = db.query(WmTask).filter(WmTask.task_id == task_id).first()
    task.job_id = 9001
    db.commit()
    return task_id


def test_add_checklist_item_success():
    db = setup_db()
    task_id = create_task_fixture(db)
    res = TaskService(db).create_child_item(task_id, ChildItemCreateRequest(item_type="CHECKLIST", title="Collect docs"), user_id=100)
    assert res["status"] == "SUCCESS"


def test_add_subtask_with_estimate_success():
    db = setup_db()
    task_id = create_task_fixture(db)
    res = TaskService(db).create_child_item(
        task_id,
        ChildItemCreateRequest(item_type="SUBTASK", title="Prepare workings", estimated_hours=Decimal("2.5"), assignee_emp_id=101),
        user_id=100,
    )
    assert res["item_type"] == "SUBTASK"


def test_add_child_to_closed_parent_fails():
    db = setup_db()
    task_id = create_task_fixture(db)
    service = TaskService(db)
    service.transition_status(task_id, TaskStatusTransitionRequest(new_status="In Progress", changed_by=100))
    service.transition_status(task_id, TaskStatusTransitionRequest(new_status="Done", changed_by=100))
    service.transition_status(task_id, TaskStatusTransitionRequest(new_status="Closed", changed_by=201))

    with pytest.raises(HTTPException):
        service.create_child_item(task_id, ChildItemCreateRequest(item_type="CHECKLIST", title="Late add"), user_id=100)


def test_invalid_assignee_fails():
    db = setup_db()
    task_id = create_task_fixture(db)
    with pytest.raises(HTTPException):
        TaskService(db).create_child_item(task_id, ChildItemCreateRequest(item_type="TODO", title="Call client", assignee_emp_id=999), user_id=100)


def test_convert_checklist_to_subtask_success():
    db = setup_db()
    task_id = create_task_fixture(db)
    service = TaskService(db)
    child = service.create_child_item(task_id, ChildItemCreateRequest(item_type="CHECKLIST", title="Prepare summary"), user_id=100)
    converted = service.convert_checklist_to_subtask(task_id, child["child_item_id"], user_id=100)
    assert converted["item_type"] == "SUBTASK"


def test_mark_child_done_and_block_parent_completion_until_all_done():
    db = setup_db()
    task_id = create_task_fixture(db)
    service = TaskService(db)
    c1 = service.create_child_item(task_id, ChildItemCreateRequest(item_type="CHECKLIST", title="Step 1"), user_id=100)
    c2 = service.create_child_item(task_id, ChildItemCreateRequest(item_type="CHECKLIST", title="Step 2"), user_id=100)

    service.transition_status(task_id, TaskStatusTransitionRequest(new_status="In Progress", changed_by=100))
    service.update_child_item_status(task_id, c1["child_item_id"], ChildItemStatusRequest(status_code="Done", updated_by=100))

    with pytest.raises(HTTPException):
        service.transition_status(task_id, TaskStatusTransitionRequest(new_status="Done", changed_by=100))

    service.update_child_item_status(task_id, c2["child_item_id"], ChildItemStatusRequest(status_code="Done", updated_by=100))
    result = service.transition_status(task_id, TaskStatusTransitionRequest(new_status="Done", changed_by=100))
    assert result["new_status"] == "Done"


def test_reorder_child_items_success():
    db = setup_db()
    task_id = create_task_fixture(db)
    service = TaskService(db)
    c1 = service.create_child_item(task_id, ChildItemCreateRequest(item_type="CHECKLIST", title="Step A", sequence_no=1), user_id=100)
    c2 = service.create_child_item(task_id, ChildItemCreateRequest(item_type="CHECKLIST", title="Step B", sequence_no=2), user_id=100)

    service.reorder_child_items(task_id, ChildItemReorderRequest(item_orders=[
        {"child_item_id": c1["child_item_id"], "sequence_no": 2},
        {"child_item_id": c2["child_item_id"], "sequence_no": 1},
    ], updated_by=100))

    rows = db.query(WmTaskChildItem).filter(WmTaskChildItem.parent_task_id == task_id).all()
    order_map = {r.child_item_id: r.sequence_no for r in rows}
    assert order_map[c1["child_item_id"]] == 2
    assert order_map[c2["child_item_id"]] == 1


def test_configure_parallel_participants_success():
    db = setup_db()
    task_id = create_task_fixture(db)
    service = TaskService(db)
    now = datetime.utcnow()
    result = service.configure_participants(
        task_id=task_id,
        payload=TaskParticipantsRequest(
            participants=[
                {
                    "emp_id": 100,
                    "role_code": "EXECUTOR",
                    "planned_start": now,
                    "planned_due": now + timedelta(days=1),
                    "dependency_type": "NONE",
                    "submission_required": True,
                    "is_mandatory": True,
                },
                {
                    "emp_id": 101,
                    "role_code": "CONTRIBUTOR",
                    "planned_start": now,
                    "planned_due": now + timedelta(days=2),
                    "dependency_type": "NONE",
                    "is_mandatory": True,
                },
            ]
        ),
        user_id=100,
    )
    assert result["status"] == "SUCCESS"
    assert result["participant_count"] == 2


def test_configure_sequential_participants_with_dependency_success():
    db = setup_db()
    task_id = create_task_fixture(db)
    service = TaskService(db)
    now = datetime.utcnow()
    result = service.configure_participants(
        task_id=task_id,
        payload=TaskParticipantsRequest(
            participants=[
                {
                    "emp_id": 100,
                    "role_code": "EXECUTOR",
                    "planned_start": now,
                    "planned_due": now + timedelta(days=1),
                    "sequence_no": 1,
                    "dependency_type": "NONE",
                    "submission_required": True,
                },
                {
                    "emp_id": 201,
                    "role_code": "REVIEWER",
                    "planned_start": now + timedelta(days=1),
                    "planned_due": now + timedelta(days=2),
                    "sequence_no": 2,
                    "predecessor_sequence_no": 1,
                    "dependency_type": "ACCEPTANCE_BASED",
                    "acceptance_required": True,
                },
            ]
        ),
        user_id=100,
    )
    assert result["status"] == "SUCCESS"
    deps = db.query(WmTaskParticipantDependency).filter(WmTaskParticipantDependency.task_id == task_id).all()
    assert len(deps) == 1


def test_circular_dependency_fails():
    db = setup_db()
    task_id = create_task_fixture(db)
    service = TaskService(db)
    now = datetime.utcnow()
    with pytest.raises(HTTPException):
        service.configure_participants(
            task_id=task_id,
            payload=TaskParticipantsRequest(
                participants=[
                    {
                        "emp_id": 100,
                        "role_code": "EXECUTOR",
                        "planned_start": now,
                        "planned_due": now + timedelta(days=1),
                        "sequence_no": 1,
                        "predecessor_sequence_no": 2,
                        "dependency_type": "FINISH_TO_START",
                    },
                    {
                        "emp_id": 101,
                        "role_code": "REVIEWER",
                        "planned_start": now + timedelta(hours=2),
                        "planned_due": now + timedelta(days=1, hours=4),
                        "sequence_no": 2,
                        "predecessor_sequence_no": 1,
                        "dependency_type": "FINISH_TO_START",
                    },
                ]
            ),
            user_id=100,
        )


def test_duplicate_participant_role_fails():
    db = setup_db()
    task_id = create_task_fixture(db)
    service = TaskService(db)
    now = datetime.utcnow()
    with pytest.raises(HTTPException):
        service.configure_participants(
            task_id=task_id,
            payload=TaskParticipantsRequest(
                participants=[
                    {
                        "emp_id": 100,
                        "role_code": "EXECUTOR",
                        "planned_start": now,
                        "planned_due": now + timedelta(days=1),
                    },
                    {
                        "emp_id": 100,
                        "role_code": "EXECUTOR",
                        "planned_start": now + timedelta(hours=1),
                        "planned_due": now + timedelta(days=1, hours=1),
                    },
                ]
            ),
            user_id=100,
        )


def test_task_dates_rollup_from_participants():
    db = setup_db()
    task_id = create_task_fixture(db)
    service = TaskService(db)
    now = datetime.utcnow()
    earliest = now + timedelta(days=3)
    latest = now + timedelta(days=7)
    service.configure_participants(
        task_id=task_id,
        payload=TaskParticipantsRequest(
            participants=[
                {
                    "emp_id": 100,
                    "role_code": "EXECUTOR",
                    "planned_start": earliest,
                    "planned_due": now + timedelta(days=4),
                },
                {
                    "emp_id": 101,
                    "role_code": "CONTRIBUTOR",
                    "planned_start": now + timedelta(days=5),
                    "planned_due": latest,
                },
            ]
        ),
        user_id=100,
    )
    task = db.query(WmTask).filter(WmTask.task_id == task_id).first()
    assert task.planned_start == earliest
    assert task.due_at == latest
    participants = db.query(WmTaskParticipant).filter(WmTaskParticipant.task_id == task_id, WmTaskParticipant.is_active.is_(True)).all()
    assert len(participants) == 2


def _configure_submission_chain(service: TaskService, db, task_id: int):
    now = datetime.utcnow()
    service.configure_participants(
        task_id=task_id,
        payload=TaskParticipantsRequest(
            participants=[
                {
                    "emp_id": 100,
                    "role_code": "EXECUTOR",
                    "planned_start": now,
                    "planned_due": now + timedelta(days=1),
                    "sequence_no": 1,
                    "submission_required": True,
                },
                {
                    "emp_id": 201,
                    "role_code": "REVIEWER",
                    "planned_start": now + timedelta(days=1),
                    "planned_due": now + timedelta(days=2),
                    "sequence_no": 2,
                    "predecessor_sequence_no": 1,
                    "dependency_type": "FINISH_TO_START",
                },
            ]
        ),
        user_id=100,
    )
    p1 = db.query(WmTaskParticipant).filter(WmTaskParticipant.task_id == task_id, WmTaskParticipant.sequence_no == 1).first()
    p2 = db.query(WmTaskParticipant).filter(WmTaskParticipant.task_id == task_id, WmTaskParticipant.sequence_no == 2).first()
    return p1, p2


def test_submit_participant_work_to_successor_success():
    db = setup_db()
    task_id = create_task_fixture(db)
    service = TaskService(db)
    p1, p2 = _configure_submission_chain(service, db, task_id)

    response = service.submit_participant_work(
        task_id=task_id,
        participant_id=p1.task_participant_id,
        payload=ParticipantSubmitRequest(
            submission_note="Completed work package.",
            completion_pct=100,
            remarks="Ready for next stage",
        ),
        user_id=100,
    )
    assert response["status"] == "SUCCESS"
    assert response["handoff_status"] == "Submitted"
    submission = db.query(WmTaskParticipantSubmission).filter(WmTaskParticipantSubmission.task_id == task_id).first()
    handoff = db.query(WmTaskParticipantHandoff).filter(WmTaskParticipantHandoff.task_id == task_id).first()
    assert submission is not None
    assert handoff is not None
    db.refresh(p2)
    assert p2.participant_status == "Not Started"


def test_submit_participant_work_acceptance_required_success():
    db = setup_db()
    task_id = create_task_fixture(db)
    service = TaskService(db)
    now = datetime.utcnow()
    service.configure_participants(
        task_id=task_id,
        payload=TaskParticipantsRequest(
            participants=[
                {
                    "emp_id": 100,
                    "role_code": "EXECUTOR",
                    "planned_start": now,
                    "planned_due": now + timedelta(days=1),
                    "sequence_no": 1,
                    "submission_required": True,
                },
                {
                    "emp_id": 201,
                    "role_code": "REVIEWER",
                    "planned_start": now + timedelta(days=1),
                    "planned_due": now + timedelta(days=2),
                    "sequence_no": 2,
                    "predecessor_sequence_no": 1,
                    "dependency_type": "ACCEPTANCE_BASED",
                    "acceptance_required": True,
                },
            ]
        ),
        user_id=100,
    )
    p1 = db.query(WmTaskParticipant).filter(WmTaskParticipant.task_id == task_id, WmTaskParticipant.sequence_no == 1).first()
    p2 = db.query(WmTaskParticipant).filter(WmTaskParticipant.task_id == task_id, WmTaskParticipant.sequence_no == 2).first()

    response = service.submit_participant_work(
        task_id=task_id,
        participant_id=p1.task_participant_id,
        payload=ParticipantSubmitRequest(submission_note="Please accept", completion_pct=100),
        user_id=100,
    )
    assert response["handoff_status"] == "Awaiting Acceptance"
    db.refresh(p2)
    assert p2.participant_status == "Planned"


def test_submit_participant_work_unauthorized_fails():
    db = setup_db()
    task_id = create_task_fixture(db)
    service = TaskService(db)
    p1, _ = _configure_submission_chain(service, db, task_id)
    with pytest.raises(HTTPException):
        service.submit_participant_work(
            task_id=task_id,
            participant_id=p1.task_participant_id,
            payload=ParticipantSubmitRequest(submission_note="attempt", completion_pct=100),
            user_id=101,
        )


def test_submit_participant_work_on_closed_task_fails():
    db = setup_db()
    task_id = create_task_fixture(db)
    service = TaskService(db)
    p1, _ = _configure_submission_chain(service, db, task_id)
    service.transition_status(task_id, TaskStatusTransitionRequest(new_status="In Progress", changed_by=100))
    service.transition_status(task_id, TaskStatusTransitionRequest(new_status="Done", changed_by=100))
    service.transition_status(task_id, TaskStatusTransitionRequest(new_status="Closed", changed_by=201))

    with pytest.raises(HTTPException):
        service.submit_participant_work(
            task_id=task_id,
            participant_id=p1.task_participant_id,
            payload=ParticipantSubmitRequest(submission_note="late submit", completion_pct=100),
            user_id=100,
        )


def test_submit_participant_work_duplicate_conflict_fails():
    db = setup_db()
    task_id = create_task_fixture(db)
    service = TaskService(db)
    p1, _ = _configure_submission_chain(service, db, task_id)
    service.submit_participant_work(
        task_id=task_id,
        participant_id=p1.task_participant_id,
        payload=ParticipantSubmitRequest(submission_note="first submit", completion_pct=100),
        user_id=100,
    )

    with pytest.raises(HTTPException):
        service.submit_participant_work(
            task_id=task_id,
            participant_id=p1.task_participant_id,
            payload=ParticipantSubmitRequest(submission_note="second submit", completion_pct=100),
            user_id=100,
        )


def _create_submission_for_decision(service: TaskService, db, task_id: int):
    p1, p2 = _configure_submission_chain(service, db, task_id)
    submit_response = service.submit_participant_work(
        task_id=task_id,
        participant_id=p1.task_participant_id,
        payload=ParticipantSubmitRequest(submission_note="ready", completion_pct=100),
        user_id=100,
    )
    return p1, p2, submit_response["submission_id"]


def test_decide_submission_accept_success():
    db = setup_db()
    task_id = create_task_fixture(db)
    service = TaskService(db)
    p1, p2, submission_id = _create_submission_for_decision(service, db, task_id)

    response = service.decide_submission(
        task_id=task_id,
        submission_id=submission_id,
        payload=SubmissionDecisionRequest(decision="ACCEPT", decision_note="Looks good"),
        user_id=p2.emp_id,
    )
    assert response["decision"] == "ACCEPT"
    assert response["handoff_status"] == "Accepted"

    pred = db.query(WmTaskParticipant).filter(WmTaskParticipant.task_participant_id == p1.task_participant_id).first()
    sub = db.query(WmTaskParticipantSubmission).filter(WmTaskParticipantSubmission.submission_id == submission_id).first()
    assert pred.participant_status == "Accepted"
    assert sub.submission_status == "Accepted"


def test_decide_submission_reject_with_note_success():
    db = setup_db()
    task_id = create_task_fixture(db)
    service = TaskService(db)
    p1, p2, submission_id = _create_submission_for_decision(service, db, task_id)

    response = service.decide_submission(
        task_id=task_id,
        submission_id=submission_id,
        payload=SubmissionDecisionRequest(decision="REJECT", decision_note="Please fix mismatch"),
        user_id=p2.emp_id,
    )
    assert response["handoff_status"] == "Rejected"

    pred = db.query(WmTaskParticipant).filter(WmTaskParticipant.task_participant_id == p1.task_participant_id).first()
    assert pred.participant_status == "Rework Required"


def test_decide_submission_reject_without_note_fails():
    db = setup_db()
    task_id = create_task_fixture(db)
    service = TaskService(db)
    _, p2, submission_id = _create_submission_for_decision(service, db, task_id)

    with pytest.raises(HTTPException):
        service.decide_submission(
            task_id=task_id,
            submission_id=submission_id,
            payload=SubmissionDecisionRequest(decision="REJECT", decision_note=""),
            user_id=p2.emp_id,
        )


def test_decide_submission_unauthorized_user_fails():
    db = setup_db()
    task_id = create_task_fixture(db)
    service = TaskService(db)
    _, _, submission_id = _create_submission_for_decision(service, db, task_id)

    with pytest.raises(HTTPException):
        service.decide_submission(
            task_id=task_id,
            submission_id=submission_id,
            payload=SubmissionDecisionRequest(decision="ACCEPT"),
            user_id=101,
        )


def test_decide_submission_duplicate_decision_fails():
    db = setup_db()
    task_id = create_task_fixture(db)
    service = TaskService(db)
    _, p2, submission_id = _create_submission_for_decision(service, db, task_id)
    service.decide_submission(
        task_id=task_id,
        submission_id=submission_id,
        payload=SubmissionDecisionRequest(decision="ACCEPT"),
        user_id=p2.emp_id,
    )

    with pytest.raises(HTTPException):
        service.decide_submission(
            task_id=task_id,
            submission_id=submission_id,
            payload=SubmissionDecisionRequest(decision="ACCEPT"),
            user_id=p2.emp_id,
        )


def test_decide_submission_override_requires_reason():
    db = setup_db()
    task_id = create_task_fixture(db)
    service = TaskService(db)
    _, _, submission_id = _create_submission_for_decision(service, db, task_id)

    with pytest.raises(HTTPException):
        service.decide_submission(
            task_id=task_id,
            submission_id=submission_id,
            payload=SubmissionDecisionRequest(decision="ACCEPT", override_flag=True, override_reason=""),
            user_id=102,
        )
