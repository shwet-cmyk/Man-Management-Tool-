from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import date, datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.wm_job import WmJob
from app.models.wm_notification_queue import WmNotificationQueue
from app.models.wm_project import WmProject
from app.models.wm_project_audit_event import WmProjectAuditEvent
from app.models.wm_project_chat_message import WmProjectChatMessage
from app.models.wm_project_file_link import WmProjectFileLink
from app.models.wm_project_team_member import WmProjectTeamMember
from app.models.wm_project_watcher import WmProjectWatcher
from app.models.wm_task import WmTask
from app.modules.project_collab.schemas import (
    ProjectAccessRequest,
    ProjectCreateRequest,
    ProjectFileLinkRequest,
    ProjectListFilterRequest,
    ProjectMessageCreateRequest,
    ProjectReportRequest,
    ProjectStatusUpdateRequest,
    ProjectTeamMemberCreateRequest,
    ProjectTeamMemberUpdateRequest,
    ProjectWatcherRequest,
)


class ProjectAuditService:
    def __init__(self, db: Session):
        self.db = db

    def log(self, project_id: int, event_type: str, actor_user_id: int, actor_name: str, entity_type: str, entity_id: int | None, details: dict | None = None):
        event = WmProjectAuditEvent(
            project_id=project_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_user_id=actor_user_id,
            actor_name=actor_name,
            details_json=json.dumps(details or {}),
        )
        self.db.add(event)
        return event


class ProjectNotificationService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, event_type: str, project_id: int, recipient_employee_id: int, message: str, linked_entity_type: str = "PROJECT", linked_entity_id: int | None = None):
        notif = WmNotificationQueue(
            task_id=linked_entity_id or 0,
            recipient_emp_id=recipient_employee_id,
            channel="IN_APP",
            payload=json.dumps({
                "event_type": event_type,
                "project_id": project_id,
                "message": message,
                "linked_entity_type": linked_entity_type,
                "linked_entity_id": linked_entity_id,
            }),
            status="PENDING",
        )
        self.db.add(notif)
        return notif


class ProjectAccessService:
    FINANCIAL_ROLES = {"Owner", "Manager", "Finance"}

    def resolve_access(self, payload: ProjectAccessRequest) -> dict:
        can_collaborate = payload.is_project_member or payload.scope_mode in {"downline", "all"}
        can_view_project = payload.is_project_member or payload.scope_mode == "all"
        can_view_financials = payload.can_view_financials and (payload.employee_role in self.FINANCIAL_ROLES)
        return {
            "project_id": payload.project_id,
            "employee_id": payload.employee_id,
            "can_view_project": can_view_project,
            "can_collaborate": can_collaborate,
            "can_view_financials": can_view_financials,
        }


class ProjectService:
    VALID_TYPES = {"Client Project", "Internal Project", "Ticket-based Project", "Strategic Project", "Operational Project"}

    def __init__(self, db: Session):
        self.db = db
        self.audit = ProjectAuditService(db)

    def create_project(self, payload: ProjectCreateRequest) -> dict:
        if payload.project_type not in self.VALID_TYPES:
            raise ValueError("Unsupported project type")
        row = WmProject(**payload.model_dump())
        self.db.add(row)
        self.db.flush()
        self.audit.log(row.project_id, "PROJECT_CREATED", payload.created_by, payload.owner_name, "PROJECT", row.project_id, payload.model_dump())
        self.db.commit()
        return {"status": "success", "project_id": row.project_id, "project_code": row.project_code}

    def list_projects(self, filters: ProjectListFilterRequest) -> list[dict]:
        q = self.db.query(WmProject).filter(WmProject.active_flag.is_(True))
        if filters.status:
            q = q.filter(WmProject.status == filters.status)
        if filters.project_type:
            q = q.filter(WmProject.project_type == filters.project_type)
        if filters.owner_id:
            q = q.filter(WmProject.owner_id == filters.owner_id)
        if filters.manager_id:
            q = q.filter(WmProject.manager_id == filters.manager_id)
        if filters.billable_flag is not None:
            q = q.filter(WmProject.billable_flag.is_(filters.billable_flag))
        return [self._to_dict(row) for row in q.order_by(WmProject.project_id.desc()).all()]

    def get_project(self, project_id: int) -> dict:
        row = self.db.query(WmProject).filter(WmProject.project_id == project_id).first()
        if not row:
            raise ValueError("Project not found")
        snapshot = self._to_dict(row)
        snapshot["derived_status_signals"] = self._derive_status_signals(project_id, row)
        return snapshot

    def update_status(self, project_id: int, payload: ProjectStatusUpdateRequest) -> dict:
        row = self.db.query(WmProject).filter(WmProject.project_id == project_id).first()
        if not row:
            raise ValueError("Project not found")
        old = row.status
        row.status = payload.status
        row.updated_by = payload.updated_by
        row.updated_at = datetime.utcnow()
        self.audit.log(project_id, "PROJECT_STATUS_CHANGED", payload.updated_by, payload.updated_by_name, "PROJECT", project_id, {"old": old, "new": payload.status})
        self.db.commit()
        return {"status": "success", "project_id": project_id, "old_status": old, "new_status": payload.status}

    def _derive_status_signals(self, project_id: int, project_row: WmProject) -> dict:
        today = date.today()
        task_overdue = self.db.query(WmTask).filter(
            WmTask.project_id == project_id,
            WmTask.is_active.is_(True),
            WmTask.due_at < datetime.combine(today, datetime.max.time()),
            WmTask.status_code != "Completed",
        ).count()
        critical_jobs = self.db.query(WmJob).filter(
            WmJob.parent_task_id.in_(self.db.query(WmTask.task_id).filter(WmTask.project_id == project_id)),
            WmJob.critical_flag.is_(True),
            WmJob.is_active.is_(True),
        ).count()
        financial_loss = float(project_row.profit_or_loss_rollup or 0) < 0
        at_risk = bool(task_overdue or critical_jobs or financial_loss)
        return {
            "task_overdue_count": task_overdue,
            "critical_job_count": critical_jobs,
            "financial_loss_flag": financial_loss,
            "at_risk_recommended": at_risk,
        }

    def _to_dict(self, row: WmProject) -> dict:
        return {
            "project_id": row.project_id,
            "project_code": row.project_code,
            "project_name": row.project_name,
            "project_type": row.project_type,
            "description": row.description,
            "client_id": row.client_id,
            "client_name": row.client_name,
            "billable_flag": row.billable_flag,
            "status": row.status,
            "priority": row.priority,
            "owner_id": row.owner_id,
            "owner_name": row.owner_name,
            "manager_id": row.manager_id,
            "manager_name": row.manager_name,
            "company_id": row.company_id,
            "branch_id": row.branch_id,
            "department_id": row.department_id,
            "planned_start_date": row.planned_start_date,
            "planned_end_date": row.planned_end_date,
            "actual_start_date": row.actual_start_date,
            "actual_end_date": row.actual_end_date,
            "budget_amount": float(row.budget_amount or 0),
            "billed_amount_rollup": float(row.billed_amount_rollup or 0),
            "cost_to_company_rollup": float(row.cost_to_company_rollup or 0),
            "profit_or_loss_rollup": float(row.profit_or_loss_rollup or 0),
            "progress_percent": float(row.progress_percent or 0),
            "task_count": int(row.task_count or 0),
            "job_count": int(row.job_count or 0),
            "active_flag": row.active_flag,
            "created_by": row.created_by,
            "created_at": row.created_at,
            "updated_by": row.updated_by,
            "updated_at": row.updated_at,
        }


class ProjectTeamService:
    def __init__(self, db: Session):
        self.db = db
        self.audit = ProjectAuditService(db)
        self.notify = ProjectNotificationService(db)

    def add_member(self, project_id: int, payload: ProjectTeamMemberCreateRequest) -> dict:
        row = WmProjectTeamMember(project_id=project_id, **payload.model_dump())
        self.db.add(row)
        self.db.flush()
        self.audit.log(project_id, "PROJECT_MEMBER_ADDED", payload.added_by, payload.employee_name, "PROJECT_TEAM_MEMBER", row.project_team_member_id, payload.model_dump())
        self.notify.create("PROJECT_MEMBER_ADDED", project_id, payload.employee_id, f"You were added to project {project_id}")
        self.db.commit()
        return {"status": "success", "project_team_member_id": row.project_team_member_id}

    def update_member(self, project_team_member_id: int, payload: ProjectTeamMemberUpdateRequest, actor_user_id: int, actor_name: str) -> dict:
        row = self.db.query(WmProjectTeamMember).filter(WmProjectTeamMember.project_team_member_id == project_team_member_id).first()
        if not row:
            raise ValueError("Team member not found")
        before = {"role_type": row.role_type, "participation_type": row.participation_type, "notification_preference": row.notification_preference, "active_flag": row.active_flag}
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(row, field, value)
        row.updated_at = datetime.utcnow()
        self.audit.log(row.project_id, "PROJECT_MEMBER_UPDATED", actor_user_id, actor_name, "PROJECT_TEAM_MEMBER", row.project_team_member_id, {"before": before, "after": payload.model_dump(exclude_none=True)})
        self.db.commit()
        return {"status": "success"}

    def list_members(self, project_id: int) -> list[dict]:
        rows = self.db.query(WmProjectTeamMember).filter(WmProjectTeamMember.project_id == project_id, WmProjectTeamMember.active_flag.is_(True)).all()
        return [{
            "project_team_member_id": r.project_team_member_id,
            "employee_id": r.employee_id,
            "employee_name": r.employee_name,
            "role_type": r.role_type,
            "participation_type": r.participation_type,
            "notification_preference": r.notification_preference,
            "visible_in_team_list_flag": r.visible_in_team_list_flag,
            "joined_at": r.joined_at,
        } for r in rows]


class MentionService:
    @staticmethod
    def extract_mentions(message_text: str) -> list[str]:
        return [token[1:] for token in message_text.split() if token.startswith("@") and len(token) > 1]


class ProjectChatService:
    def __init__(self, db: Session):
        self.db = db
        self.audit = ProjectAuditService(db)
        self.notify = ProjectNotificationService(db)
        self.mention = MentionService()

    def post_message(self, payload: ProjectMessageCreateRequest) -> dict:
        row = WmProjectChatMessage(
            project_id=payload.project_id,
            entity_type=payload.entity_type,
            entity_id=payload.entity_id,
            message_type=payload.message_type,
            message_text=payload.message_text,
            sender_user_id=payload.sender_user_id,
            sender_name=payload.sender_name,
            reply_to_message_id=payload.reply_to_message_id,
            attachment_refs=json.dumps(payload.attachment_refs),
            visibility_scope=payload.visibility_scope,
            system_generated_flag=payload.system_generated_flag,
        )
        self.db.add(row)
        self.db.flush()
        mentions = self.mention.extract_mentions(payload.message_text)
        recipients = self._notification_recipients(payload, row, mentions)
        for target in recipients:
            self.notify.create(
                target["event_type"],
                payload.project_id,
                target["recipient_employee_id"],
                target["message"],
                payload.entity_type,
                payload.entity_id,
            )
        self.audit.log(payload.project_id, "MESSAGE_POSTED", payload.sender_user_id, payload.sender_name, payload.entity_type, payload.entity_id, {"message_id": row.message_id, "mentions": mentions})
        self.db.commit()
        return {"status": "success", "message_id": row.message_id, "mentions": mentions, "notifications_created": len(recipients)}

    def pin_message(self, message_id: int, actor_user_id: int, actor_name: str, pinned: bool = True) -> dict:
        row = self.db.query(WmProjectChatMessage).filter(WmProjectChatMessage.message_id == message_id).first()
        if not row:
            raise ValueError("Message not found")
        row.pinned_flag = pinned
        row.updated_at = datetime.utcnow()
        self.audit.log(row.project_id, "MESSAGE_PINNED" if pinned else "MESSAGE_UNPINNED", actor_user_id, actor_name, row.entity_type, row.entity_id, {"message_id": message_id})
        self.db.commit()
        return {"status": "success", "message_id": message_id, "pinned": pinned}

    def list_messages(self, project_id: int, entity_type: str | None = None, entity_id: int | None = None) -> list[dict]:
        q = self.db.query(WmProjectChatMessage).filter(WmProjectChatMessage.project_id == project_id, WmProjectChatMessage.deleted_flag.is_(False))
        if entity_type:
            q = q.filter(WmProjectChatMessage.entity_type == entity_type)
        if entity_id:
            q = q.filter(WmProjectChatMessage.entity_id == entity_id)
        rows = q.order_by(WmProjectChatMessage.created_at.asc()).all()
        return [{
            "message_id": r.message_id,
            "project_id": r.project_id,
            "entity_type": r.entity_type,
            "entity_id": r.entity_id,
            "message_type": r.message_type,
            "message_text": r.message_text,
            "sender_user_id": r.sender_user_id,
            "sender_name": r.sender_name,
            "reply_to_message_id": r.reply_to_message_id,
            "attachment_refs": json.loads(r.attachment_refs) if r.attachment_refs else [],
            "visibility_scope": r.visibility_scope,
            "message_style": "system" if r.system_generated_flag else "human",
            "pinned_flag": r.pinned_flag,
            "system_generated_flag": r.system_generated_flag,
            "created_at": r.created_at,
        } for r in rows]

    def _notification_recipients(self, payload: ProjectMessageCreateRequest, row: WmProjectChatMessage, mentions: list[str]) -> list[dict]:
        dedupe: set[tuple[str, int]] = set()
        notifications: list[dict] = []

        def _add(event_type: str, emp_id: int | None, message: str):
            if not emp_id or emp_id == payload.sender_user_id:
                return
            key = (event_type, int(emp_id))
            if key in dedupe:
                return
            dedupe.add(key)
            notifications.append({"event_type": event_type, "recipient_employee_id": int(emp_id), "message": message})

        for mention in mentions:
            if mention.isdigit():
                _add("MENTION", int(mention), f"{payload.sender_name} mentioned you: {payload.message_text[:80]}")

        if payload.reply_to_message_id:
            parent = self.db.query(WmProjectChatMessage).filter(WmProjectChatMessage.message_id == payload.reply_to_message_id).first()
            if parent:
                _add("MESSAGE_REPLY", parent.sender_user_id, f"{payload.sender_name} replied in {payload.entity_type} thread")

        if payload.message_type.lower() == "announcement":
            team_rows = self.db.query(WmProjectTeamMember).filter(
                WmProjectTeamMember.project_id == payload.project_id,
                WmProjectTeamMember.active_flag.is_(True),
            ).all()
            for member in team_rows:
                _add("PROJECT_ANNOUNCEMENT", member.employee_id, f"Announcement in project {payload.project_id}")

        if payload.entity_type == "TASK" and payload.entity_id:
            task = self.db.query(WmTask).filter(WmTask.task_id == payload.entity_id).first()
            if task:
                _add("TASK_COMMENT_ASSIGNEE", task.primary_owner_emp_id, f"New task comment on {task.task_no}")
                _add("TASK_COMMENT_MANAGER", task.manager_emp_id, f"Task update requires attention: {task.task_no}")
        if payload.entity_type == "JOB" and payload.entity_id:
            job = self.db.query(WmJob).filter(WmJob.job_id == payload.entity_id).first()
            if job:
                _add("JOB_COMMENT_ASSIGNEE", job.assigned_employee_id, f"New job comment on {job.job_no}")
                _add("JOB_COMMENT_MANAGER", job.manager_id, f"Job update requires attention: {job.job_no}")

        return notifications


class FileLinkService:
    def __init__(self, db: Session):
        self.db = db
        self.audit = ProjectAuditService(db)

    def add(self, payload: ProjectFileLinkRequest) -> dict:
        row = WmProjectFileLink(**payload.model_dump())
        self.db.add(row)
        self.db.flush()
        self.audit.log(payload.project_id, "FILE_LINKED", payload.uploaded_by, "System", payload.linked_entity_type, payload.linked_entity_id, payload.model_dump())
        self.db.commit()
        return {"status": "success", "file_id": row.file_id}

    def list(self, project_id: int, linked_entity_type: str | None = None) -> list[dict]:
        q = self.db.query(WmProjectFileLink).filter(WmProjectFileLink.project_id == project_id)
        if linked_entity_type:
            q = q.filter(WmProjectFileLink.linked_entity_type == linked_entity_type)
        rows = q.order_by(WmProjectFileLink.uploaded_at.desc()).all()
        return [{
            "file_id": r.file_id,
            "linked_entity_type": r.linked_entity_type,
            "linked_entity_id": r.linked_entity_id,
            "file_name": r.file_name,
            "file_type": r.file_type,
            "file_size": r.file_size,
            "uploaded_by": r.uploaded_by,
            "uploaded_at": r.uploaded_at,
            "visibility_scope": r.visibility_scope,
        } for r in rows]


class WatcherService:
    def __init__(self, db: Session):
        self.db = db

    def follow(self, payload: ProjectWatcherRequest) -> dict:
        existing = self.db.query(WmProjectWatcher).filter(
            WmProjectWatcher.project_id == payload.project_id,
            WmProjectWatcher.entity_type == payload.entity_type,
            WmProjectWatcher.entity_id == payload.entity_id,
            WmProjectWatcher.employee_id == payload.employee_id,
        ).first()
        if existing:
            existing.active_flag = True
            existing.muted_flag = payload.muted_flag
            existing.auto_follow_flag = payload.auto_follow_flag
            self.db.commit()
            return {"status": "success", "watcher_id": existing.watcher_id}
        row = WmProjectWatcher(**payload.model_dump())
        self.db.add(row)
        self.db.commit()
        return {"status": "success", "watcher_id": row.watcher_id}

    def unfollow(self, watcher_id: int) -> dict:
        row = self.db.query(WmProjectWatcher).filter(WmProjectWatcher.watcher_id == watcher_id).first()
        if not row:
            raise ValueError("Watcher not found")
        row.active_flag = False
        self.db.commit()
        return {"status": "success"}


class ProjectViewService:
    def __init__(self, db: Session):
        self.db = db

    def work_records(self, project_id: int) -> list[dict]:
        tasks = self.db.query(WmTask).filter(WmTask.project_id == project_id, WmTask.is_active.is_(True)).all()
        task_ids = [t.task_id for t in tasks]
        jobs = self.db.query(WmJob).filter(WmJob.parent_task_id.in_(task_ids) if task_ids else False).all() if task_ids else []
        job_by_task: dict[int, list[WmJob]] = defaultdict(list)
        for job in jobs:
            if job.parent_task_id:
                job_by_task[job.parent_task_id].append(job)
        rows = []
        for task in tasks:
            rows.append({
                "record_type": "TASK",
                "record_id": task.task_id,
                "record_code": task.task_no,
                "title": task.title,
                "status": task.status_code,
                "assignee_id": task.primary_owner_emp_id,
                "manager_id": task.manager_emp_id,
                "priority": task.priority_code,
                "due_date": task.due_at.date() if task.due_at else None,
                "rollover_count": int(task.rollover_count_rollup or 0),
                "billable_flag": bool(task.billable_flag),
                "dependency_state": None,
                "child_job_count": len(job_by_task.get(task.task_id, [])),
            })
            for job in job_by_task.get(task.task_id, []):
                rows.append({
                    "record_type": "JOB",
                    "record_id": job.job_id,
                    "record_code": job.job_no,
                    "title": job.job_name,
                    "status": job.execution_status,
                    "assignee_id": job.assigned_employee_id,
                    "manager_id": job.manager_id,
                    "priority": job.priority,
                    "due_date": job.due_date,
                    "rollover_count": int(job.rollover_count or 0),
                    "billable_flag": bool(job.is_billable),
                    "dependency_state": job.dependency_status,
                    "critical_flag": bool(job.critical_flag),
                    "parent_task_id": job.parent_task_id,
                })
        return rows

    def multi_view_payload(self, project_id: int) -> dict:
        records = self.work_records(project_id)
        board = defaultdict(list)
        calendar = defaultdict(list)
        timeline = []
        for r in records:
            board[r.get("status") or "Unknown"].append(r)
            if r.get("due_date"):
                calendar[str(r["due_date"])].append(r)
            timeline.append({
                "record_code": r["record_code"],
                "title": r["title"],
                "due_date": r.get("due_date"),
                "priority": r.get("priority"),
                "status": r.get("status"),
                "dependency_state": r.get("dependency_state"),
            })
        return {
            "project_id": project_id,
            "list": records,
            "board": dict(board),
            "timeline": timeline,
            "calendar": dict(calendar),
        }


class ProjectAnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def overview(self, project_id: int, can_view_financials: bool = False) -> dict:
        project = self.db.query(WmProject).filter(WmProject.project_id == project_id).first()
        if not project:
            raise ValueError("Project not found")
        task_q = self.db.query(WmTask).filter(WmTask.project_id == project_id, WmTask.is_active.is_(True))
        tasks = task_q.all()
        task_ids = [t.task_id for t in tasks]
        jobs = self.db.query(WmJob).filter(WmJob.parent_task_id.in_(task_ids)).all() if task_ids else []
        approvals_pending = sum(1 for t in tasks if (t.status_code or "") in {"PENDING_APPROVAL", "IN_REVIEW"})
        overdue_tasks = sum(1 for t in tasks if t.due_at and t.due_at.date() < date.today() and t.status_code != "Completed")
        overdue_jobs = sum(1 for j in jobs if j.due_date and j.due_date < date.today() and j.execution_status != "Completed")
        critical_jobs = sum(1 for j in jobs if j.critical_flag)

        activity_count = self.db.query(func.count(WmProjectChatMessage.message_id)).filter(WmProjectChatMessage.project_id == project_id).scalar() or 0
        pinned = self.db.query(WmProjectChatMessage).filter(WmProjectChatMessage.project_id == project_id, WmProjectChatMessage.pinned_flag.is_(True)).order_by(WmProjectChatMessage.created_at.desc()).limit(3).all()

        out = {
            "project_id": project_id,
            "project_name": project.project_name,
            "status": project.status,
            "progress_percent": float(project.progress_percent or 0),
            "owner_name": project.owner_name,
            "manager_name": project.manager_name,
            "task_count": len(tasks),
            "job_count": len(jobs),
            "overdue_tasks": overdue_tasks,
            "overdue_jobs": overdue_jobs,
            "critical_jobs": critical_jobs,
            "pending_approvals": approvals_pending,
            "recent_activity_count": int(activity_count),
            "pinned_messages": [p.message_text for p in pinned],
            "files_count": int(self.db.query(func.count(WmProjectFileLink.file_id)).filter(WmProjectFileLink.project_id == project_id).scalar() or 0),
            "dependencies_open": sum(1 for j in jobs if (j.dependency_status or "") in {"Blocked", "Pending"}),
        }
        if can_view_financials:
            out.update({
                "cost_to_company_rollup": float(project.cost_to_company_rollup or 0),
                "billed_amount_rollup": float(project.billed_amount_rollup or 0),
                "profit_or_loss_rollup": float(project.profit_or_loss_rollup or 0),
            })
        return out

    def widgets(self) -> dict:
        projects = self.db.query(WmProject).filter(WmProject.active_flag.is_(True)).all()
        project_ids = [p.project_id for p in projects]
        msg_count = Counter()
        if project_ids:
            rows = self.db.query(WmProjectChatMessage.project_id).filter(WmProjectChatMessage.project_id.in_(project_ids)).all()
            msg_count.update(pid for (pid,) in rows)

        return {
            "active_projects": sum(1 for p in projects if p.status in {"Draft", "Active", "On Hold", "At Risk"}),
            "at_risk_projects": sum(1 for p in projects if p.status == "At Risk"),
            "projects_completed_this_month": sum(1 for p in projects if p.status in {"Completed", "Closed"} and p.updated_at and p.updated_at.month == date.today().month),
            "projects_by_type": Counter(p.project_type for p in projects),
            "projects_by_owner": Counter(p.owner_name for p in projects),
            "projects_with_pending_approvals": sum(1 for p in projects if self.db.query(WmTask).filter(WmTask.project_id == p.project_id, WmTask.status_code == "PENDING_APPROVAL").count() > 0),
            "high_communication_activity": [
                {"project_id": p.project_id, "project_name": p.project_name, "message_count": msg_count.get(p.project_id, 0)}
                for p in sorted(projects, key=lambda x: msg_count.get(x.project_id, 0), reverse=True)[:10]
            ],
            "project_wise_cost_vs_billed": [
                {"project_id": p.project_id, "cost": float(p.cost_to_company_rollup or 0), "billed": float(p.billed_amount_rollup or 0)}
                for p in projects
            ],
        }

    def reports(self, payload: ProjectReportRequest) -> dict:
        q = self.db.query(WmProject)
        if payload.start_date:
            q = q.filter(WmProject.created_at >= datetime.combine(payload.start_date, datetime.min.time()))
        if payload.end_date:
            q = q.filter(WmProject.created_at <= datetime.combine(payload.end_date, datetime.max.time()))
        projects = q.all()
        project_ids = [p.project_id for p in projects]

        team_rows = self.db.query(WmProjectTeamMember).filter(WmProjectTeamMember.project_id.in_(project_ids)).all() if project_ids else []
        chat_rows = self.db.query(WmProjectChatMessage).filter(WmProjectChatMessage.project_id.in_(project_ids)).all() if project_ids else []
        file_rows = self.db.query(WmProjectFileLink).filter(WmProjectFileLink.project_id.in_(project_ids)).all() if project_ids else []

        return {
            "project_register": [
                {"project_id": p.project_id, "project_code": p.project_code, "project_name": p.project_name, "status": p.status, "project_type": p.project_type}
                for p in projects
            ],
            "project_team_report": [
                {"project_id": t.project_id, "employee_id": t.employee_id, "employee_name": t.employee_name, "role_type": t.role_type, "participation_type": t.participation_type}
                for t in team_rows
            ],
            "project_status_report": Counter(p.status for p in projects),
            "project_progress_report": [{"project_id": p.project_id, "progress_percent": float(p.progress_percent or 0)} for p in projects],
            "project_cost_profit_report": [{"project_id": p.project_id, "cost": float(p.cost_to_company_rollup or 0), "billed": float(p.billed_amount_rollup or 0), "profit_or_loss": float(p.profit_or_loss_rollup or 0)} for p in projects],
            "team_member_allocation_by_project": Counter(t.employee_id for t in team_rows),
            "project_activity_report": Counter(c.project_id for c in chat_rows),
            "project_chat_activity_report": Counter(c.message_type for c in chat_rows),
            "mention_activity_report": Counter(m for c in chat_rows for m in [token[1:] for token in (c.message_text or "").split() if token.startswith("@")]),
            "file_usage_report": Counter(f.project_id for f in file_rows),
            "project_risk_report": [{"project_id": p.project_id, "at_risk": p.status == "At Risk" or float(p.profit_or_loss_rollup or 0) < 0} for p in projects],
            "project_delay_report": [{"project_id": p.project_id, "delay_days": max((date.today() - p.planned_end_date).days, 0) if p.planned_end_date else 0} for p in projects],
            "project_approval_summary": Counter(t.status_code for t in self.db.query(WmTask).filter(WmTask.project_id.in_(project_ids)).all()) if project_ids else {},
            "project_communication_volume_report": [{"project_id": pid, "message_count": count} for pid, count in Counter(c.project_id for c in chat_rows).items()],
        }


class ProjectScenarioService:
    def __init__(self, db: Session):
        self.db = db

    def seed(self, created_by: int = 1) -> dict:
        project_service = ProjectService(self.db)
        team_service = ProjectTeamService(self.db)
        chat_service = ProjectChatService(self.db)

        scenarios = [
            ProjectCreateRequest(project_code="PRJ-CLI-001", project_name="Client implementation rollout", project_type="Client Project", client_id=501, client_name="Client Alpha", billable_flag=True, status="Active", owner_id=10, owner_name="Owner One", manager_id=11, manager_name="Manager One", company_id=1, created_by=created_by),
            ProjectCreateRequest(project_code="PRJ-INT-002", project_name="Internal process transformation", project_type="Internal Project", billable_flag=False, status="Active", owner_id=20, owner_name="Owner Two", manager_id=21, manager_name="Manager Two", company_id=1, created_by=created_by),
        ]
        created_projects = []
        for p in scenarios:
            created = project_service.create_project(p)
            created_projects.append(created["project_id"])
            team_service.add_member(created["project_id"], ProjectTeamMemberCreateRequest(employee_id=p.owner_id, employee_name=p.owner_name, role_type="Owner", participation_type="Responsible", added_by=created_by))
            team_service.add_member(created["project_id"], ProjectTeamMemberCreateRequest(employee_id=p.manager_id or p.owner_id, employee_name=p.manager_name or p.owner_name, role_type="Manager", participation_type="Collaborator", added_by=created_by))
            chat_service.post_message(ProjectMessageCreateRequest(project_id=created["project_id"], message_text="Weekly update posted @11", sender_user_id=p.owner_id, sender_name=p.owner_name, message_type="announcement"))
        self.db.commit()
        return {"status": "success", "project_ids": created_projects}
