from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.tasks.schemas import (
    ChildItemBulkCreateRequest,
    ChildItemCreateRequest,
    ChildItemRead,
    ChildItemReorderRequest,
    ChildItemResponse,
    ChildItemStatusRequest,
    ParticipantSubmitRequest,
    ParticipantSubmitResponse,
    TaskAssignBulkRequest,
    TaskAssignRequest,
    TaskAssignResponse,
    TaskCreateRequest,
    TaskCreateResponse,
    TaskParticipantsRequest,
    TaskParticipantsResponse,
    TaskRead,
    TaskStatusBulkRequest,
    TaskStatusTransitionRequest,
    TaskStatusTransitionResponse,
)
from app.modules.tasks.service import TaskService

router = APIRouter(prefix="/wm/tasks", tags=["Work Management - Tasks"])


@router.post("", response_model=TaskCreateResponse)
def create_task(payload: TaskCreateRequest, db: Session = Depends(get_db)):
    return TaskService(db).create_task(payload)


@router.get("", response_model=list[TaskRead])
def get_tasks(db: Session = Depends(get_db)):
    return TaskService(db).list_tasks()


@router.post("/{task_id}/assign", response_model=TaskAssignResponse)
def assign_users(task_id: int, payload: TaskAssignRequest, db: Session = Depends(get_db)):
    return TaskService(db).assign_users(task_id=task_id, payload=payload)


@router.post("/assign/bulk", response_model=TaskAssignResponse)
def bulk_assign(payload: TaskAssignBulkRequest, db: Session = Depends(get_db)):
    return TaskService(db).bulk_assign(task_ids=payload.task_ids, assignment=payload.assignment)


@router.post("/{task_id}/participants", response_model=TaskParticipantsResponse)
def configure_participants(task_id: int, payload: TaskParticipantsRequest, db: Session = Depends(get_db)):
    return TaskService(db).configure_participants(task_id=task_id, payload=payload)


@router.post("/{task_id}/participants/{participant_id}/submit", response_model=ParticipantSubmitResponse)
def submit_participant_work(task_id: int, participant_id: int, payload: ParticipantSubmitRequest, db: Session = Depends(get_db)):
    return TaskService(db).submit_participant_work(task_id=task_id, participant_id=participant_id, payload=payload)


@router.post("/{task_id}/submissions/{submission_id}/decision", response_model=SubmissionDecisionResponse)
def decide_submission(task_id: int, submission_id: int, payload: SubmissionDecisionRequest, db: Session = Depends(get_db)):
    return TaskService(db).decide_submission(task_id=task_id, submission_id=submission_id, payload=payload)


@router.post("/{task_id}/status-transition", response_model=TaskStatusTransitionResponse)
def status_transition(task_id: int, payload: TaskStatusTransitionRequest, db: Session = Depends(get_db)):
    return TaskService(db).transition_status(task_id=task_id, payload=payload)


@router.post("/status-transition/bulk", response_model=TaskStatusTransitionResponse)
def bulk_status_transition(payload: TaskStatusBulkRequest, db: Session = Depends(get_db)):
    return TaskService(db).bulk_transition_status(task_ids=payload.task_ids, payload=payload.transition)


@router.post("/{task_id}/child-items", response_model=ChildItemResponse)
def create_child_item(task_id: int, payload: ChildItemCreateRequest, db: Session = Depends(get_db)):
    return TaskService(db).create_child_item(task_id=task_id, payload=payload)


@router.post("/{task_id}/child-items/bulk", response_model=list[ChildItemResponse])
def bulk_create_child_items(task_id: int, payload: ChildItemBulkCreateRequest, db: Session = Depends(get_db)):
    return TaskService(db).bulk_create_child_items(task_id=task_id, items=payload.items)


@router.get("/{task_id}/child-items", response_model=list[ChildItemRead])
def get_child_items(task_id: int, db: Session = Depends(get_db)):
    return TaskService(db).list_child_items(task_id=task_id)


@router.post("/{task_id}/child-items/{child_item_id}/convert-to-subtask", response_model=ChildItemResponse)
def convert_child_item(task_id: int, child_item_id: int, db: Session = Depends(get_db)):
    return TaskService(db).convert_checklist_to_subtask(task_id=task_id, child_item_id=child_item_id)


@router.post("/{task_id}/child-items/{child_item_id}/status", response_model=ChildItemResponse)
def update_child_item_status(task_id: int, child_item_id: int, payload: ChildItemStatusRequest, db: Session = Depends(get_db)):
    return TaskService(db).update_child_item_status(task_id=task_id, child_item_id=child_item_id, payload=payload)


@router.post("/{task_id}/child-items/reorder", response_model=TaskAssignResponse)
def reorder_child_items(task_id: int, payload: ChildItemReorderRequest, db: Session = Depends(get_db)):
    return TaskService(db).reorder_child_items(task_id=task_id, payload=payload)
    SubmissionDecisionRequest,
    SubmissionDecisionResponse,
