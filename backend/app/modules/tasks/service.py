from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException

from app.core.config import settings
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.task_audit_log import TaskAuditLog
from app.models.wm_gamification_event import WmGamificationEvent
from app.models.wm_task import WmTask
from app.models.wm_task_assignment import WmTaskAssignment
from app.models.wm_task_child_item import WmTaskChildItem
from app.models.wm_task_child_item_conversion import WmTaskChildItemConversion
from app.models.wm_task_participant import WmTaskParticipant
from app.models.wm_task_participant_dependency import WmTaskParticipantDependency
from app.models.wm_task_participant_handoff import WmTaskParticipantHandoff
from app.models.wm_task_participant_submission import WmTaskParticipantSubmission
from app.models.wm_task_status_history import WmTaskStatusHistory
from app.models.wm_task_workflow_state import WmTaskWorkflowState
from app.modules.tasks.master_validation import MasterValidationService
from app.modules.tasks.notification_service import NotificationService
from app.modules.tasks.schemas import ChildItemCreateRequest, ChildItemReorderRequest, ChildItemStatusRequest, ParticipantSubmitRequest, SubmissionDecisionRequest, TaskAssignRequest, TaskCreateRequest, TaskParticipantsRequest, TaskStatusTransitionRequest

COMPLETION_STATUSES = {"Done", "Closed"}
REOPEN_STATUSES = {"Reopened"}
ALLOWED_TRANSITIONS = {
    "Draft": {"Open", "Cancelled"},
    "Open": {"In Progress", "On Hold", "Cancelled"},
    "In Progress": {"On Hold", "Waiting for Review", "Done", "Cancelled"},
    "On Hold": {"In Progress", "Cancelled"},
    "Waiting for Review": {"Approved", "In Progress", "Rejected"},
    "Approved": {"Done", "Closed"},
    "Done": {"Closed", "Reopened"},
    "Closed": {"Reopened"},
    "Cancelled": {"Reopened"},
    "Reopened": {"In Progress", "On Hold", "Cancelled"},
}


class TaskService:
    def __init__(self, db: Session):
        self.db = db
        self.master_validation = MasterValidationService(db)
        self.notification_service = NotificationService(db)

    def create_task(self, payload: TaskCreateRequest, user_id: int = 1) -> dict:
        existing = self._handle_idempotency(payload)
        if existing:
            return {
                "status": "SUCCESS",
                "task_id": existing.task_id,
                "task_no": existing.task_no,
                "workflow_state": existing.workflow_state_code or existing.status_code,
                "message": "Task already exists for source reference",
            }

        payload = payload.model_copy(update=self.master_validation.derive_from_project(
            payload.project_id,
            payload.company_id,
            payload.branch_id,
            payload.department_id,
            payload.customer_id,
            payload.manager_emp_id,
        ))

        self._validate(payload)

        task_no = self._generate_task_no()
        workflow_state = self.master_validation.validate_workflow(payload.workflow_id, payload.save_mode)
        status_code = "Draft" if payload.save_mode == "DRAFT" else workflow_state

        task = WmTask(
            task_no=task_no,
            company_id=payload.company_id,
            branch_id=payload.branch_id,
            department_id=payload.department_id,
            customer_id=payload.customer_id,
            project_id=payload.project_id,
            cost_center_id=payload.cost_center_id,
            title=payload.title.strip(),
            description=payload.description,
            task_type=payload.task_type,
            priority_code=payload.priority_code,
            status_code=status_code,
            primary_owner_emp_id=payload.primary_owner_emp_id,
            manager_emp_id=payload.manager_emp_id,
            reviewer_emp_id=payload.reviewer_emp_id,
            billable_flag=bool(payload.billable_flag),
            billed_amount=payload.billed_amount,
            estimated_hours=payload.estimated_hours or Decimal("0"),
            planned_start=payload.planned_start or datetime.utcnow(),
            due_at=payload.due_at or datetime.utcnow(),
            workflow_id=payload.workflow_id,
            workflow_state_code=workflow_state,
            source_type=payload.source_type,
            source_reference=payload.source_reference,
            created_by=user_id,
            last_activity_at=datetime.utcnow(),
        )

        try:
            self.db.add(task)
            self.db.flush()
            self.db.add(
                WmTaskWorkflowState(
                    task_id=task.task_id,
                    workflow_id=payload.workflow_id,
                    state_code=workflow_state,
                    entered_by=user_id,
                )
            )
            self._apply_assignments(
                task=task,
                assignment=TaskAssignRequest(
                    primary_owner_emp_id=payload.primary_owner_emp_id,
                    contributors=payload.contributor_emp_ids,
                    reviewer_emp_id=payload.reviewer_emp_id,
                    manager_emp_id=payload.manager_emp_id,
                ),
                user_id=user_id,
                from_creation=True,
            )
            self.db.commit()
            self.db.refresh(task)
        except Exception as exc:  # noqa: BLE001
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Task creation failed: {exc}") from exc

        return {
            "status": "SUCCESS",
            "task_id": task.task_id,
            "task_no": task.task_no,
            "workflow_state": workflow_state,
            "message": "Task created successfully",
        }

    def transition_status(self, task_id: int, payload: TaskStatusTransitionRequest) -> dict:
        task = self.db.query(WmTask).filter(WmTask.task_id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        if not task.is_active:
            raise HTTPException(status_code=422, detail="Inactive/archived task cannot be updated")

        old_status = task.status_code
        new_status = payload.new_status

        self._validate_status_transition(task, payload)

        completed_at = task.completed_at
        if new_status in COMPLETION_STATUSES:
            completed_at = datetime.utcnow()
        elif new_status in REOPEN_STATUSES:
            completed_at = None

        try:
            task.status_code = new_status
            task.workflow_state_code = new_status
            task.completed_at = completed_at
            task.last_activity_at = datetime.utcnow()
            task.updated_by = payload.changed_by
            task.updated_on = datetime.utcnow()

            self.db.add(
                WmTaskStatusHistory(
                    task_id=task_id,
                    old_status_code=old_status,
                    new_status_code=new_status,
                    action_code=payload.action_code,
                    remarks=payload.remarks,
                    changed_by=payload.changed_by,
                )
            )

            self.db.add(
                WmTaskWorkflowState(
                    task_id=task_id,
                    workflow_id=task.workflow_id,
                    state_code=new_status,
                    entered_by=payload.changed_by,
                )
            )

            self.db.add(
                TaskAuditLog(
                    entity_name="wm_task",
                    entity_id=task_id,
                    action="STATUS_CHANGE",
                    details=f"old={old_status};new={new_status};source={payload.source};remarks={payload.remarks}",
                    created_by=payload.changed_by,
                )
            )

            recipients = [x for x in [task.primary_owner_emp_id, task.manager_emp_id, task.reviewer_emp_id] if x]
            self.notification_service.queue_task_notifications(
                task_id=task_id,
                recipients=recipients,
                message=f"Task {task.task_no} moved {old_status} -> {new_status}",
            )

            if new_status in COMPLETION_STATUSES and task.due_at and completed_at and completed_at > task.due_at:
                self.db.add(
                    WmGamificationEvent(
                        task_id=task_id,
                        event_code="LATE_COMPLETION",
                        event_value=f"Delayed by {(completed_at - task.due_at).total_seconds()} seconds",
                    )
                )

            self.db.commit()
        except Exception as exc:  # noqa: BLE001
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Status transition failed: {exc}") from exc

        return {
            "status": "SUCCESS",
            "task_id": task_id,
            "old_status": old_status,
            "new_status": new_status,
            "completed_at": completed_at,
            "message": "Task status updated successfully",
        }

    def bulk_transition_status(self, task_ids: list[int], payload: TaskStatusTransitionRequest) -> dict:
        results = []
        failures = []
        for task_id in task_ids:
            try:
                results.append(self.transition_status(task_id, payload))
            except HTTPException as exc:
                failures.append({"task_id": task_id, "error": exc.detail})
        return {
            "status": "PARTIAL_SUCCESS" if failures else "SUCCESS",
            "task_id": 0,
            "old_status": "MIXED",
            "new_status": payload.new_status,
            "completed_at": None,
            "message": f"updated={len(results)}, failed={len(failures)}",
        }

    def assign_users(self, task_id: int, payload: TaskAssignRequest, user_id: int = 1) -> dict:
        task = self.db.query(WmTask).filter(WmTask.task_id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        if task.status_code in {"Closed", "Archived"}:
            raise HTTPException(status_code=422, detail="Assignment not allowed for locked task")

        self._validate_assignment(payload)

        try:
            old_assignments = self.db.query(WmTaskAssignment).filter(
                WmTaskAssignment.task_id == task_id,
                WmTaskAssignment.is_active.is_(True),
            ).all()
            old_snapshot = [f"{a.emp_id}:{a.role_code}" for a in old_assignments]

            for assignment in old_assignments:
                assignment.is_active = False

            self._apply_assignments(task=task, assignment=payload, user_id=user_id, from_creation=False)

            task.primary_owner_emp_id = payload.primary_owner_emp_id
            task.manager_emp_id = payload.manager_emp_id
            task.reviewer_emp_id = payload.reviewer_emp_id
            task.updated_by = user_id
            task.updated_on = datetime.utcnow()

            self.db.add(
                TaskAuditLog(
                    entity_name="wm_task",
                    entity_id=task.task_id,
                    action="ASSIGN_UPDATE",
                    details=f"old={old_snapshot}; new_owner={payload.primary_owner_emp_id}",
                    created_by=user_id,
                )
            )
            self.db.commit()
        except Exception as exc:  # noqa: BLE001
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Assignment update failed: {exc}") from exc

        return {"status": "SUCCESS", "message": "Assignment updated", "task_id": task_id}

    def bulk_assign(self, task_ids: list[int], assignment: TaskAssignRequest, user_id: int = 1) -> dict:
        for task_id in task_ids:
            self.assign_users(task_id=task_id, payload=assignment, user_id=user_id)
        return {"status": "SUCCESS", "message": f"Assignments updated for {len(task_ids)} tasks", "task_id": 0}

    def configure_participants(self, task_id: int, payload: TaskParticipantsRequest, user_id: int = 1) -> dict:
        task = self.db.query(WmTask).filter(WmTask.task_id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        if task.status_code in {"Closed", "Cancelled", "Archived"}:
            raise HTTPException(status_code=422, detail="Participant modification is not allowed for locked task")
        if not payload.participants:
            raise HTTPException(status_code=422, detail="At least one participant is required")

        sequence_to_participant: dict[int, object] = {}
        seen_employee_role: set[tuple[int, str]] = set()

        for participant in payload.participants:
            if not self.master_validation.employee_is_active(participant.emp_id):
                raise HTTPException(status_code=422, detail=f"Invalid employee: {participant.emp_id}")
            if participant.planned_due < participant.planned_start:
                raise HTTPException(status_code=422, detail=f"Invalid date range for employee: {participant.emp_id}")
            if participant.allocation_pct is not None and (participant.allocation_pct < 0 or participant.allocation_pct > 100):
                raise HTTPException(status_code=422, detail="Allocation percentage must be between 0 and 100")

            emp_role_key = (participant.emp_id, participant.role_code)
            if emp_role_key in seen_employee_role:
                raise HTTPException(status_code=409, detail=f"Duplicate participant for employee {participant.emp_id} and role {participant.role_code}")
            seen_employee_role.add(emp_role_key)

            if participant.sequence_no is not None:
                if participant.sequence_no in sequence_to_participant:
                    raise HTTPException(status_code=422, detail=f"Duplicate sequence number: {participant.sequence_no}")
                sequence_to_participant[participant.sequence_no] = participant

        for participant in payload.participants:
            if participant.predecessor_sequence_no is not None:
                if participant.predecessor_sequence_no not in sequence_to_participant:
                    raise HTTPException(status_code=422, detail=f"Invalid predecessor sequence: {participant.predecessor_sequence_no}")
                if participant.sequence_no is None:
                    raise HTTPException(status_code=422, detail="Successor sequence_no is required when predecessor_sequence_no is provided")
            if participant.acceptance_required and participant.dependency_type == "NONE":
                raise HTTPException(status_code=422, detail="Acceptance-required participant must define a dependency type")
            if participant.dependency_type == "ACCEPTANCE_BASED":
                if participant.predecessor_sequence_no is None:
                    raise HTTPException(status_code=422, detail="Acceptance-based dependency requires predecessor sequence")
                predecessor = sequence_to_participant.get(participant.predecessor_sequence_no)
                if predecessor and not predecessor.submission_required:
                    raise HTTPException(status_code=422, detail="Acceptance-based dependency requires submission_required for predecessor participant")

        self._validate_no_circular_dependency(payload)

        try:
            existing_participant_ids = [
                row.task_participant_id
                for row in self.db.query(WmTaskParticipant.task_participant_id)
                .filter(WmTaskParticipant.task_id == task_id, WmTaskParticipant.is_active.is_(True))
                .all()
            ]
            if existing_participant_ids:
                self.db.query(WmTaskParticipantDependency).filter(
                    WmTaskParticipantDependency.task_id == task_id,
                ).delete(synchronize_session=False)
                self.db.query(WmTaskParticipant).filter(
                    WmTaskParticipant.task_id == task_id,
                    WmTaskParticipant.is_active.is_(True),
                ).update({"is_active": False, "updated_by": user_id, "updated_on": datetime.utcnow()}, synchronize_session=False)

            created_by_sequence: dict[int, int] = {}
            created_participants: list[WmTaskParticipant] = []
            for participant in payload.participants:
                row = WmTaskParticipant(
                    task_id=task_id,
                    emp_id=participant.emp_id,
                    role_code=participant.role_code,
                    planned_start=participant.planned_start,
                    planned_due=participant.planned_due,
                    sequence_no=participant.sequence_no,
                    submission_required=participant.submission_required,
                    acceptance_required=participant.acceptance_required,
                    allocation_pct=participant.allocation_pct,
                    is_mandatory=participant.is_mandatory,
                    remarks=participant.remarks,
                    created_by=user_id,
                    participant_status="Planned",
                )
                self.db.add(row)
                self.db.flush()
                created_participants.append(row)
                if participant.sequence_no is not None:
                    created_by_sequence[participant.sequence_no] = row.task_participant_id

            for participant in payload.participants:
                if participant.predecessor_sequence_no is not None and participant.sequence_no is not None:
                    self.db.add(
                        WmTaskParticipantDependency(
                            task_id=task_id,
                            predecessor_participant_id=created_by_sequence[participant.predecessor_sequence_no],
                            successor_participant_id=created_by_sequence[participant.sequence_no],
                            dependency_type=participant.dependency_type,
                            created_by=user_id,
                        )
                    )

            task_start = min(row.planned_start for row in created_participants)
            task_due = max(row.planned_due for row in created_participants)
            task.planned_start = task_start
            task.due_at = task_due
            task.updated_by = user_id
            task.updated_on = datetime.utcnow()

            self.db.add(
                TaskAuditLog(
                    entity_name="wm_task",
                    entity_id=task_id,
                    action="PARTICIPANT_CONFIGURE",
                    details=f"participant_count={len(created_participants)};task_start={task_start.isoformat()};task_due={task_due.isoformat()}",
                    created_by=user_id,
                )
            )
            recipients = [p.emp_id for p in created_participants]
            if task.manager_emp_id:
                recipients.append(task.manager_emp_id)
            self.notification_service.queue_task_notifications(
                task_id=task_id,
                recipients=recipients,
                message=f"Task {task.task_no} participants configured",
            )
            self.db.commit()
        except Exception as exc:  # noqa: BLE001
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Participant configuration failed: {exc}") from exc

        return {
            "status": "SUCCESS",
            "task_id": task_id,
            "participant_count": len(payload.participants),
            "task_start_date": task_start,
            "task_due_date": task_due,
            "message": "Participants configured successfully",
        }

    def list_tasks(self) -> list[WmTask]:
        return self.db.query(WmTask).order_by(desc(WmTask.created_on)).all()

    def submit_participant_work(self, task_id: int, participant_id: int, payload: ParticipantSubmitRequest, user_id: int = 1) -> dict:
        task = self.db.query(WmTask).filter(WmTask.task_id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        if task.status_code in {"Closed", "Cancelled", "Archived"}:
            raise HTTPException(status_code=422, detail="Task does not allow submission")
        if task.job_id is None:
            raise HTTPException(status_code=422, detail="Task is not mapped to a job")

        participant = (
            self.db.query(WmTaskParticipant)
            .filter(
                WmTaskParticipant.task_participant_id == participant_id,
                WmTaskParticipant.task_id == task_id,
                WmTaskParticipant.is_active.is_(True),
            )
            .first()
        )
        if not participant:
            raise HTTPException(status_code=404, detail="Participant not found for task")
        if user_id != participant.emp_id and user_id != task.manager_emp_id and user_id != task.created_by:
            raise HTTPException(status_code=403, detail="User is not allowed to submit this stage")
        if participant.participant_status in {"Submitted", "Completed", "Cancelled", "Accepted"}:
            raise HTTPException(status_code=409, detail="Participant stage is already submitted/completed")
        if payload.completion_pct is not None and (payload.completion_pct < 0 or payload.completion_pct > 100):
            raise HTTPException(status_code=422, detail="Completion percentage must be between 0 and 100")
        if payload.completion_pct is not None and payload.completion_pct < 100 and not (payload.submission_note or "").strip():
            raise HTTPException(status_code=422, detail="Submission note is required for partial submission")

        open_required_items = self.db.query(WmTaskChildItem).filter(
            WmTaskChildItem.parent_task_id == task_id,
            WmTaskChildItem.assignee_emp_id == participant.emp_id,
            WmTaskChildItem.status_code.notin_(["Done", "Cancelled"]),
            WmTaskChildItem.is_active.is_(True),
        ).count()
        if open_required_items > 0:
            raise HTTPException(status_code=422, detail="Required child items are pending for this participant")

        dependency = (
            self.db.query(WmTaskParticipantDependency)
            .filter(
                WmTaskParticipantDependency.task_id == task_id,
                WmTaskParticipantDependency.predecessor_participant_id == participant_id,
            )
            .order_by(WmTaskParticipantDependency.task_participant_dependency_id.asc())
            .first()
        )
        successor = None
        acceptance_required = bool(payload.acceptance_required) or bool(participant.acceptance_required)
        handoff_type = "FINAL_SUBMISSION"
        if dependency:
            successor = (
                self.db.query(WmTaskParticipant)
                .filter(
                    WmTaskParticipant.task_participant_id == dependency.successor_participant_id,
                    WmTaskParticipant.task_id == task_id,
                    WmTaskParticipant.is_active.is_(True),
                )
                .first()
            )
            if successor is None:
                raise HTTPException(status_code=422, detail="Successor mapping is invalid/inactive")
            handoff_type = "DIRECT_SUCCESSOR"
            if dependency.dependency_type == "ACCEPTANCE_BASED":
                acceptance_required = True

        duplicate_active = self.db.query(WmTaskParticipantSubmission).filter(
            WmTaskParticipantSubmission.task_id == task_id,
            WmTaskParticipantSubmission.from_participant_id == participant_id,
            WmTaskParticipantSubmission.is_active.is_(True),
            WmTaskParticipantSubmission.submission_status.in_(["Submitted", "Awaiting Acceptance"]),
        ).first()
        if duplicate_active:
            raise HTTPException(status_code=409, detail="Conflicting active submission already exists")

        submission_status = "Awaiting Acceptance" if acceptance_required else "Submitted"
        participant_status = "Submitted"

        try:
            submission = WmTaskParticipantSubmission(
                job_id=task.job_id,
                task_id=task_id,
                from_participant_id=participant_id,
                to_participant_id=successor.task_participant_id if successor else None,
                handoff_type=handoff_type,
                submission_status=submission_status,
                submission_note=payload.submission_note,
                deliverable_link=payload.deliverable_link,
                attachment_ref=payload.attachment_ref,
                completion_pct=payload.completion_pct,
                acceptance_required=acceptance_required,
                submitted_by=user_id,
                remarks=payload.remarks,
            )
            self.db.add(submission)
            self.db.flush()

            participant.participant_status = participant_status
            participant.updated_by = user_id
            participant.updated_on = datetime.utcnow()

            if successor:
                self.db.add(
                    WmTaskParticipantHandoff(
                        submission_id=submission.submission_id,
                        task_id=task_id,
                        from_participant_id=participant_id,
                        to_participant_id=successor.task_participant_id,
                        handoff_status="Awaiting Acceptance" if acceptance_required else "Pending",
                        unlocked_on=None if acceptance_required else datetime.utcnow(),
                    )
                )
                if not acceptance_required and successor.participant_status in {"Planned", "Blocked"}:
                    successor.participant_status = "Not Started"
                    successor.updated_by = user_id
                    successor.updated_on = datetime.utcnow()

            self.db.add(
                TaskAuditLog(
                    entity_name="wm_task_participant_submission",
                    entity_id=submission.submission_id,
                    action="CREATE",
                    details=f"task_id={task_id};participant_id={participant_id};successor={successor.task_participant_id if successor else None};acceptance_required={acceptance_required}",
                    created_by=user_id,
                )
            )
            recipients: list[int] = []
            if successor:
                recipients.append(successor.emp_id)
            if task.manager_emp_id:
                recipients.append(task.manager_emp_id)
            if recipients:
                self.notification_service.queue_task_notifications(
                    task_id=task_id,
                    recipients=recipients,
                    message=f"Participant {participant.emp_id} submitted work for task {task.task_no}",
                )
            self.db.commit()
        except Exception as exc:  # noqa: BLE001
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Participant submission failed: {exc}") from exc

        return {
            "status": "SUCCESS",
            "submission_id": submission.submission_id,
            "task_id": task_id,
            "participant_id": participant_id,
            "participant_status": participant_status,
            "handoff_status": submission_status,
            "message": "Work submitted successfully",
        }

    def decide_submission(self, task_id: int, submission_id: int, payload: SubmissionDecisionRequest, user_id: int = 1) -> dict:
        task = self.db.query(WmTask).filter(WmTask.task_id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        if task.status_code in {"Closed", "Cancelled", "Archived"}:
            raise HTTPException(status_code=422, detail="Task does not allow submission decisions")

        submission = self.db.query(WmTaskParticipantSubmission).filter(
            WmTaskParticipantSubmission.submission_id == submission_id,
            WmTaskParticipantSubmission.task_id == task_id,
            WmTaskParticipantSubmission.is_active.is_(True),
        ).first()
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")

        handoff = self.db.query(WmTaskParticipantHandoff).filter(
            WmTaskParticipantHandoff.submission_id == submission_id,
            WmTaskParticipantHandoff.task_id == task_id,
        ).order_by(WmTaskParticipantHandoff.handoff_id.desc()).first()
        if not handoff:
            raise HTTPException(status_code=404, detail="Active handoff not found")
        if handoff.handoff_status not in {"Pending", "Awaiting Acceptance"}:
            raise HTTPException(status_code=409, detail="Submission is not pending decision")

        successor = self.db.query(WmTaskParticipant).filter(
            WmTaskParticipant.task_participant_id == handoff.to_participant_id,
            WmTaskParticipant.task_id == task_id,
            WmTaskParticipant.is_active.is_(True),
        ).first()
        if successor is None:
            raise HTTPException(status_code=422, detail="Mapped acceptor participant is not active")

        if payload.override_flag:
            if user_id not in [task.manager_emp_id, task.created_by]:
                raise HTTPException(status_code=403, detail="Only manager/creator can use override decision")
            if not (payload.override_reason or "").strip():
                raise HTTPException(status_code=422, detail="Override reason is required")
        elif user_id != successor.emp_id:
            raise HTTPException(status_code=403, detail="User is not allowed to decide this submission")

        if payload.decision == "REJECT" and not (payload.decision_note or "").strip():
            raise HTTPException(status_code=422, detail="Decision note is required for rejection")

        predecessor = self.db.query(WmTaskParticipant).filter(
            WmTaskParticipant.task_participant_id == handoff.from_participant_id,
            WmTaskParticipant.task_id == task_id,
            WmTaskParticipant.is_active.is_(True),
        ).first()
        if not predecessor:
            raise HTTPException(status_code=422, detail="Predecessor participant not active")

        try:
            if payload.decision == "ACCEPT":
                submission.submission_status = "Accepted"
                submission.accepted_on = datetime.utcnow()
                submission.accepted_by = user_id
                submission.decision_note = payload.decision_note
                submission.override_flag = payload.override_flag
                submission.override_reason = payload.override_reason

                handoff.handoff_status = "Accepted"
                handoff.unlocked_on = datetime.utcnow()

                predecessor.participant_status = "Accepted"
                predecessor.updated_by = user_id
                predecessor.updated_on = datetime.utcnow()

                if successor.participant_status in {"Planned", "Blocked"}:
                    successor.participant_status = "Not Started"
                    successor.updated_by = user_id
                    successor.updated_on = datetime.utcnow()

                handoff_status = "Accepted"
                predecessor_status = "Accepted"
            else:
                submission.submission_status = "Rejected"
                submission.rejected_on = datetime.utcnow()
                submission.rejected_by = user_id
                submission.decision_note = payload.decision_note
                submission.override_flag = payload.override_flag
                submission.override_reason = payload.override_reason

                handoff.handoff_status = "Rejected"

                predecessor.participant_status = "Rework Required"
                predecessor.updated_by = user_id
                predecessor.updated_on = datetime.utcnow()

                handoff_status = "Rejected"
                predecessor_status = "Rework Required"

            self.db.add(
                TaskAuditLog(
                    entity_name="wm_task_participant_submission",
                    entity_id=submission_id,
                    action="DECISION",
                    details=f"decision={payload.decision};handoff_id={handoff.handoff_id};override_flag={payload.override_flag}",
                    created_by=user_id,
                )
            )

            recipients = [predecessor.emp_id]
            if task.manager_emp_id:
                recipients.append(task.manager_emp_id)
            self.notification_service.queue_task_notifications(
                task_id=task_id,
                recipients=recipients,
                message=f"Submission {submission_id} {handoff_status.lower()} for task {task.task_no}",
            )
            self.db.commit()
        except Exception as exc:  # noqa: BLE001
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Submission decision failed: {exc}") from exc

        return {
            "status": "SUCCESS",
            "submission_id": submission_id,
            "decision": payload.decision,
            "handoff_status": handoff_status,
            "predecessor_status": predecessor_status,
            "message": f"Submission {handoff_status.lower()} successfully",
        }


    def create_child_item(self, task_id: int, payload: ChildItemCreateRequest, user_id: int = 1) -> dict:
        parent = self.db.query(WmTask).filter(WmTask.task_id == task_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent task not found")
        if parent.status_code in {"Closed", "Cancelled"}:
            raise HTTPException(status_code=422, detail="Cannot add child item to closed/cancelled parent task")
        if not payload.title.strip():
            raise HTTPException(status_code=422, detail="Title is required")
        if payload.assignee_emp_id and not self.master_validation.employee_is_active(payload.assignee_emp_id):
            raise HTTPException(status_code=422, detail="Invalid assignee")
        if payload.item_type == "SUBTASK" and (payload.estimated_hours is None or payload.estimated_hours <= 0):
            raise HTTPException(status_code=422, detail="Estimated hours must be > 0 for subtask")
        if payload.due_at and parent.due_at and payload.due_at > parent.due_at:
            raise HTTPException(status_code=422, detail="Child due date cannot exceed parent due date")

        duplicate = self.db.query(WmTaskChildItem).filter(
            WmTaskChildItem.parent_task_id == task_id,
            func.lower(WmTaskChildItem.title) == payload.title.strip().lower(),
            WmTaskChildItem.is_active.is_(True),
        ).first()
        if duplicate and payload.item_type == "CHECKLIST":
            raise HTTPException(status_code=409, detail="Duplicate checklist line detected")

        child = WmTaskChildItem(
            parent_task_id=task_id,
            item_type=payload.item_type,
            title=payload.title.strip(),
            description=payload.description,
            assignee_emp_id=payload.assignee_emp_id,
            due_at=payload.due_at,
            priority_code=payload.priority_code,
            estimated_hours=payload.estimated_hours,
            sequence_no=payload.sequence_no,
            source_type=payload.source_type,
            created_by=user_id,
            status_code="Open",
        )
        try:
            self.db.add(child)
            self.db.flush()
            self.db.add(TaskAuditLog(entity_name="wm_task_child_item", entity_id=child.child_item_id, action="CREATE", details=f"parent={task_id};type={payload.item_type}", created_by=user_id))
            if payload.assignee_emp_id:
                self.notification_service.queue_task_notifications(task_id=task_id, recipients=[payload.assignee_emp_id], message=f"Child item assigned: {payload.title}")
            self.db.commit()
        except Exception as exc:  # noqa: BLE001
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Child item creation failed: {exc}") from exc

        return {"status": "SUCCESS", "child_item_id": child.child_item_id, "parent_task_id": task_id, "item_type": payload.item_type, "message": "Child item created successfully"}

    def bulk_create_child_items(self, task_id: int, items: list[ChildItemCreateRequest], user_id: int = 1) -> list[dict]:
        responses = []
        for item in items:
            if not item.title.strip():
                continue
            responses.append(self.create_child_item(task_id, item, user_id=user_id))
        return responses

    def list_child_items(self, task_id: int) -> list[WmTaskChildItem]:
        return self.db.query(WmTaskChildItem).filter(WmTaskChildItem.parent_task_id == task_id, WmTaskChildItem.is_active.is_(True)).order_by(WmTaskChildItem.sequence_no.asc().nullslast(), WmTaskChildItem.child_item_id.asc()).all()

    def convert_checklist_to_subtask(self, task_id: int, child_item_id: int, user_id: int = 1) -> dict:
        item = self.db.query(WmTaskChildItem).filter(WmTaskChildItem.child_item_id == child_item_id, WmTaskChildItem.parent_task_id == task_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Child item not found")
        old_type = item.item_type
        item.item_type = "SUBTASK"
        if item.estimated_hours is None:
            item.estimated_hours = Decimal("1")
        self.db.add(WmTaskChildItemConversion(source_child_item_id=child_item_id, target_task_id=task_id, conversion_type="CHECKLIST_TO_SUBTASK", converted_by=user_id))
        self.db.add(TaskAuditLog(entity_name="wm_task_child_item", entity_id=child_item_id, action="CONVERT", details=f"{old_type}->SUBTASK", created_by=user_id))
        self.db.commit()
        return {"status": "SUCCESS", "child_item_id": child_item_id, "parent_task_id": task_id, "item_type": "SUBTASK", "message": "Child item converted to subtask"}

    def update_child_item_status(self, task_id: int, child_item_id: int, payload: ChildItemStatusRequest) -> dict:
        item = self.db.query(WmTaskChildItem).filter(WmTaskChildItem.child_item_id == child_item_id, WmTaskChildItem.parent_task_id == task_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Child item not found")
        item.status_code = payload.status_code
        item.updated_by = payload.updated_by
        item.updated_on = datetime.utcnow()
        self.db.add(TaskAuditLog(entity_name="wm_task_child_item", entity_id=child_item_id, action="STATUS_CHANGE", details=f"new={payload.status_code}", created_by=payload.updated_by))
        self.db.commit()
        return {"status": "SUCCESS", "child_item_id": child_item_id, "parent_task_id": task_id, "item_type": item.item_type, "message": "Child item status updated"}

    def reorder_child_items(self, task_id: int, payload: ChildItemReorderRequest) -> dict:
        for row in payload.item_orders:
            item = self.db.query(WmTaskChildItem).filter(WmTaskChildItem.child_item_id == row.get("child_item_id"), WmTaskChildItem.parent_task_id == task_id).first()
            if item:
                item.sequence_no = int(row.get("sequence_no"))
                item.updated_by = payload.updated_by
                item.updated_on = datetime.utcnow()
        self.db.add(TaskAuditLog(entity_name="wm_task_child_item", entity_id=task_id, action="REORDER", details=f"count={len(payload.item_orders)}", created_by=payload.updated_by))
        self.db.commit()
        return {"status": "SUCCESS", "message": "Child item sequence updated", "task_id": task_id}


    def _validate_status_transition(self, task: WmTask, payload: TaskStatusTransitionRequest) -> None:
        old_status = task.status_code
        new_status = payload.new_status

        if new_status not in {"Draft", "Open", "In Progress", "On Hold", "Waiting for Review", "Approved", "Done", "Closed", "Cancelled", "Reopened"}:
            raise HTTPException(status_code=422, detail="Invalid target status")

        allowed = ALLOWED_TRANSITIONS.get(old_status, set())
        if new_status not in allowed:
            raise HTTPException(status_code=422, detail=f"Invalid transition {old_status} -> {new_status}")

        # role/permission checks
        if payload.changed_by not in [task.primary_owner_emp_id, task.manager_emp_id, task.reviewer_emp_id, task.created_by]:
            active_assigned = self.db.query(WmTaskAssignment).filter(
                WmTaskAssignment.task_id == task.task_id,
                WmTaskAssignment.emp_id == payload.changed_by,
                WmTaskAssignment.is_active.is_(True),
            ).first()
            if not active_assigned:
                raise HTTPException(status_code=403, detail="User is not allowed to change task status")

        if new_status in {"Done", "Closed"}:
            open_subtasks = self.db.query(WmTask).filter(
                WmTask.parent_task_id == task.task_id,
                WmTask.status_code.notin_(["Done", "Closed", "Cancelled"]),
                WmTask.is_active.is_(True),
            ).count()
            if open_subtasks > 0:
                raise HTTPException(status_code=422, detail="Cannot complete task with open dependencies/subtasks")

            open_child_items = self.db.query(WmTaskChildItem).filter(
                WmTaskChildItem.parent_task_id == task.task_id,
                WmTaskChildItem.status_code.notin_(["Done", "Cancelled"]),
                WmTaskChildItem.is_active.is_(True),
            ).count()
            if open_child_items > 0:
                raise HTTPException(status_code=422, detail="Cannot complete task with open checklist/subtask items")

            if task.reviewer_emp_id and new_status == "Closed" and payload.changed_by != task.reviewer_emp_id:
                raise HTTPException(status_code=422, detail="Reviewer approval required before closing task")

        if new_status in {"On Hold", "Cancelled"} and (payload.remarks is None or not payload.remarks.strip()):
            raise HTTPException(status_code=422, detail="Remarks are required for hold/cancel transitions")

    def _apply_assignments(self, task: WmTask, assignment: TaskAssignRequest, user_id: int, from_creation: bool) -> None:
        recipients: list[int] = [assignment.primary_owner_emp_id]

        self.db.add(
            WmTaskAssignment(
                task_id=task.task_id,
                emp_id=assignment.primary_owner_emp_id,
                role_code="OWNER",
                assigned_by=user_id,
                is_active=True,
            )
        )

        contributors = set(assignment.contributors)
        if assignment.primary_owner_emp_id in contributors:
            contributors.remove(assignment.primary_owner_emp_id)

        if not from_creation and assignment.keep_previous_owner_as_contributor:
            previous_owner = task.primary_owner_emp_id
            if previous_owner and previous_owner != assignment.primary_owner_emp_id:
                contributors.add(previous_owner)

        for contributor in contributors:
            recipients.append(contributor)
            self.db.add(
                WmTaskAssignment(
                    task_id=task.task_id,
                    emp_id=contributor,
                    role_code="CONTRIBUTOR",
                    assigned_by=user_id,
                    is_active=True,
                )
            )

        if assignment.reviewer_emp_id and assignment.reviewer_emp_id != assignment.primary_owner_emp_id:
            recipients.append(assignment.reviewer_emp_id)
            self.db.add(
                WmTaskAssignment(
                    task_id=task.task_id,
                    emp_id=assignment.reviewer_emp_id,
                    role_code="REVIEWER",
                    assigned_by=user_id,
                    is_active=True,
                )
            )

        for watcher in set(assignment.watchers):
            if watcher == assignment.primary_owner_emp_id:
                continue
            recipients.append(watcher)
            self.db.add(
                WmTaskAssignment(
                    task_id=task.task_id,
                    emp_id=watcher,
                    role_code="WATCHER",
                    assigned_by=user_id,
                    is_active=True,
                )
            )

        if assignment.manager_emp_id:
            recipients.append(assignment.manager_emp_id)

        self.db.add(
            TaskAuditLog(
                entity_name="wm_task",
                entity_id=task.task_id,
                action="ASSIGN_CREATE" if from_creation else "ASSIGN_REPLACE",
                details=f"owner={assignment.primary_owner_emp_id}",
                created_by=user_id,
            )
        )

        self.notification_service.queue_task_notifications(
            task_id=task.task_id,
            recipients=recipients,
            message=f"Task {task.task_no} assignment updated",
        )

    def _validate_assignment(self, payload: TaskAssignRequest) -> None:
        if payload.primary_owner_emp_id is None:
            raise HTTPException(status_code=422, detail="Primary owner is required")

        role_map: dict[tuple[int, str], bool] = {}

        def ensure_active(emp_id: int, role: str):
            if not self.master_validation.employee_is_active(emp_id):
                raise HTTPException(status_code=422, detail=f"Inactive/invalid employee {emp_id} for role {role}")
            key = (emp_id, role)
            if key in role_map:
                raise HTTPException(status_code=409, detail=f"Duplicate assignment for employee {emp_id} and role {role}")
            role_map[key] = True

        ensure_active(payload.primary_owner_emp_id, "OWNER")

        for contributor in payload.contributors:
            if contributor == payload.primary_owner_emp_id:
                continue
            ensure_active(contributor, "CONTRIBUTOR")

        if payload.reviewer_emp_id:
            ensure_active(payload.reviewer_emp_id, "REVIEWER")

        for watcher in payload.watchers:
            if watcher == payload.primary_owner_emp_id:
                continue
            ensure_active(watcher, "WATCHER")

        if payload.manager_emp_id and not self.master_validation.employee_is_active(payload.manager_emp_id):
            raise HTTPException(status_code=422, detail="Invalid manager")

    def _validate(self, payload: TaskCreateRequest) -> None:
        if payload.save_mode == "DRAFT":
            if not payload.title.strip():
                raise HTTPException(status_code=422, detail="Task title is required even for draft")
            return

        if not payload.title.strip():
            raise HTTPException(status_code=422, detail="Task title is required")
        if payload.estimated_hours is None or payload.estimated_hours <= 0:
            raise HTTPException(status_code=422, detail="Estimated hours must be greater than zero")
        if payload.planned_start is None:
            raise HTTPException(status_code=422, detail="Planned start is required")
        if payload.due_at is None:
            raise HTTPException(status_code=422, detail="Due date is required")
        if payload.due_at < payload.planned_start:
            raise HTTPException(status_code=422, detail="Due date cannot be before planned start")
        if payload.billable_flag is None:
            raise HTTPException(status_code=422, detail="Billable flag is required")
        if payload.billable_flag and payload.billed_amount <= Decimal("0"):
            raise HTTPException(status_code=422, detail="Billed amount must be greater than zero for billable task")
        if (not payload.billable_flag) and payload.billed_amount < 0:
            raise HTTPException(status_code=422, detail="Billed amount cannot be negative")
        if payload.primary_owner_emp_id is None:
            raise HTTPException(status_code=422, detail="Primary owner is required")
        if payload.priority_code.upper() in {"HIGH", "CRITICAL"} and payload.manager_emp_id is None:
            raise HTTPException(status_code=422, detail="Manager is required for high priority tasks")

        self.master_validation.validate_org_masters(payload.company_id, payload.branch_id, payload.department_id)
        self.master_validation.validate_customer(payload.customer_id, required=bool(payload.billable_flag))

        if payload.cost_center_id is not None and settings.strict_master_validation:
            if not self.master_validation.tez_client.master_exists("cost_center", payload.cost_center_id):
                raise HTTPException(status_code=422, detail=f"Invalid or inactive cost_center: {payload.cost_center_id}")

        if not self.master_validation.employee_is_active(payload.primary_owner_emp_id):
            raise HTTPException(status_code=422, detail="Invalid primary owner")
        if payload.manager_emp_id and not self.master_validation.employee_is_active(payload.manager_emp_id):
            raise HTTPException(status_code=422, detail="Invalid manager")
        if payload.reviewer_emp_id and not self.master_validation.employee_is_active(payload.reviewer_emp_id):
            raise HTTPException(status_code=422, detail="Invalid reviewer")

        inactive_contributors = [emp for emp in payload.contributor_emp_ids if not self.master_validation.employee_is_active(emp)]
        if inactive_contributors:
            raise HTTPException(status_code=422, detail=f"Invalid contributors: {inactive_contributors}")

        if not payload.allow_duplicate:
            duplicate_check = (
                self.db.query(WmTask)
                .filter(
                    func.lower(WmTask.title) == payload.title.strip().lower(),
                    WmTask.customer_id == payload.customer_id,
                    WmTask.primary_owner_emp_id == payload.primary_owner_emp_id,
                    WmTask.due_at == payload.due_at,
                    WmTask.is_active.is_(True),
                )
                .first()
            )
            if duplicate_check:
                raise HTTPException(status_code=409, detail="Similar task already exists for owner/customer/due date")

    def _handle_idempotency(self, payload: TaskCreateRequest) -> WmTask | None:
        if not payload.source_reference:
            return None
        return self.db.query(WmTask).filter(WmTask.source_reference == payload.source_reference).first()

    def _generate_task_no(self) -> str:
        year = datetime.utcnow().year
        prefix = f"TSK-{year}-"
        latest = (
            self.db.query(WmTask)
            .filter(WmTask.task_no.like(f"{prefix}%"))
            .order_by(desc(WmTask.task_id))
            .first()
        )
        next_seq = (int(latest.task_no.split("-")[-1]) + 1) if latest else 1
        return f"{prefix}{next_seq:06d}"

    def _validate_no_circular_dependency(self, payload: TaskParticipantsRequest) -> None:
        graph: dict[int, list[int]] = {}
        for participant in payload.participants:
            if participant.sequence_no is None:
                continue
            graph.setdefault(participant.sequence_no, [])
        for participant in payload.participants:
            if participant.sequence_no is None or participant.predecessor_sequence_no is None:
                continue
            graph.setdefault(participant.predecessor_sequence_no, []).append(participant.sequence_no)

        visited: set[int] = set()
        stack: set[int] = set()

        def visit(node: int) -> bool:
            if node in stack:
                return True
            if node in visited:
                return False
            visited.add(node)
            stack.add(node)
            for nxt in graph.get(node, []):
                if visit(nxt):
                    return True
            stack.remove(node)
            return False

        for node in graph:
            if visit(node):
                raise HTTPException(status_code=422, detail="Circular dependency detected in participant chain")
