from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import date, datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.wm_goal import WmGoal
from app.models.wm_goal_link import WmGoalLink
from app.models.wm_intake_request import WmIntakeRequest
from app.models.wm_job import WmJob
from app.models.wm_launch import WmLaunch
from app.models.wm_launch_milestone import WmLaunchMilestone
from app.models.wm_project import WmProject
from app.models.wm_project_audit_event import WmProjectAuditEvent
from app.models.wm_resource_allocation import WmResourceAllocation
from app.models.wm_task import WmTask
from app.modules.performance_engine.service import CapacityCalendarService
from app.modules.strategic_ops.schemas import (
    GoalCreateRequest,
    GoalLinkRequest,
    GoalProgressUpdateRequest,
    IntakeConvertRequest,
    IntakeRequestCreate,
    IntakeStatusUpdateRequest,
    LaunchCreateRequest,
    LaunchMilestoneRequest,
    LaunchStatusUpdateRequest,
    ResourceAllocationRequest,
    ResourceViewFilter,
    StrategicReportRequest,
)


class StrategicAuditService:
    def __init__(self, db: Session):
        self.db = db

    def log(self, project_id: int, actor_user_id: int, actor_name: str, event_type: str, entity_type: str, entity_id: int | None, details: dict | None = None):
        self.db.add(WmProjectAuditEvent(
            project_id=project_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_user_id=actor_user_id,
            actor_name=actor_name,
            details_json=json.dumps(details or {}),
        ))


class GoalRollupService:
    def __init__(self, db: Session):
        self.db = db

    def compute(self, goal_id: int) -> dict:
        goal = self.db.query(WmGoal).filter(WmGoal.goal_id == goal_id).first()
        if not goal:
            raise ValueError("Goal not found")
        links = self.db.query(WmGoalLink).filter(WmGoalLink.goal_id == goal_id).all()

        current_value = float(goal.current_value or 0)
        if goal.update_mode == "Rollup Projects":
            project_ids = [l.linked_entity_id for l in links if l.linked_entity_type == "PROJECT"]
            current_value = float(sum(float(p.progress_percent or 0) for p in self.db.query(WmProject).filter(WmProject.project_id.in_(project_ids)).all()) / (len(project_ids) or 1))
        elif goal.update_mode == "Rollup TasksJobs":
            task_ids = [l.linked_entity_id for l in links if l.linked_entity_type == "TASK"]
            job_ids = [l.linked_entity_id for l in links if l.linked_entity_type == "JOB"]
            task_completion = [100 if t.status_code == "Completed" else float(t.progress_percent or 0) for t in self.db.query(WmTask).filter(WmTask.task_id.in_(task_ids)).all()]
            job_completion = [100 if j.execution_status == "Completed" else float(j.progress_percent or 0) for j in self.db.query(WmJob).filter(WmJob.job_id.in_(job_ids)).all()]
            values = task_completion + job_completion
            current_value = float(sum(values) / (len(values) or 1))
        elif goal.update_mode == "Rollup Financial":
            project_ids = [l.linked_entity_id for l in links if l.linked_entity_type == "PROJECT"]
            projects = self.db.query(WmProject).filter(WmProject.project_id.in_(project_ids)).all()
            current_value = float(sum(float(p.billed_amount_rollup or 0) - float(p.cost_to_company_rollup or 0) for p in projects))
        elif goal.update_mode == "Rollup SLA":
            task_ids = [l.linked_entity_id for l in links if l.linked_entity_type == "TASK"]
            tasks = self.db.query(WmTask).filter(WmTask.task_id.in_(task_ids)).all()
            non_overdue = sum(1 for t in tasks if not t.due_at or t.due_at.date() >= date.today())
            current_value = round((non_overdue / (len(tasks) or 1)) * 100, 2)
        elif goal.update_mode == "Rollup Capacity":
            employee_links = [l.linked_entity_id for l in links if l.linked_entity_type == "MANAGER"]
            if employee_links:
                cal = CapacityCalendarService(self.db)
                util_values = []
                for emp_id in employee_links:
                    month = cal.month_view(emp_id, date.today())
                    available = month["totals"]["available_hours"]
                    actual = month["totals"]["actual_hours"]
                    util_values.append((actual / available * 100) if available else 0)
                current_value = round(sum(util_values) / (len(util_values) or 1), 2)

        target = float(goal.target_value or 0)
        progress = round((current_value / target * 100), 2) if target else float(goal.progress_percent or 0)
        risk = "On Track" if progress >= 80 else "At Risk" if progress >= 50 else "Off Track"

        goal.current_value = current_value
        goal.progress_percent = progress
        goal.risk_status = risk
        goal.updated_at = datetime.utcnow()
        self.db.commit()
        return {"goal_id": goal_id, "current_value": current_value, "progress_percent": progress, "risk_status": risk}


class GoalService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, payload: GoalCreateRequest) -> dict:
        row = WmGoal(**payload.model_dump())
        self.db.add(row)
        self.db.commit()
        return {"status": "success", "goal_id": row.goal_id}

    def link(self, goal_id: int, payload: GoalLinkRequest) -> dict:
        row = WmGoalLink(goal_id=goal_id, **payload.model_dump())
        self.db.add(row)
        self._refresh_link_counts(goal_id)
        self.db.commit()
        return {"status": "success", "goal_link_id": row.goal_link_id}

    def update_progress(self, goal_id: int, payload: GoalProgressUpdateRequest) -> dict:
        row = self.db.query(WmGoal).filter(WmGoal.goal_id == goal_id).first()
        if not row:
            raise ValueError("Goal not found")
        row.current_value = payload.current_value
        if payload.progress_percent is not None:
            row.progress_percent = payload.progress_percent
        elif row.target_value:
            row.progress_percent = round(float(payload.current_value) / float(row.target_value) * 100, 2)
        row.risk_status = "On Track" if float(row.progress_percent or 0) >= 80 else "At Risk" if float(row.progress_percent or 0) >= 50 else "Off Track"
        row.updated_by = payload.updated_by
        row.updated_at = datetime.utcnow()
        self.db.commit()
        return {"status": "success", "goal_id": goal_id, "progress_percent": float(row.progress_percent or 0), "risk_status": row.risk_status}

    def list(self) -> list[dict]:
        rows = self.db.query(WmGoal).filter(WmGoal.active_flag.is_(True)).order_by(WmGoal.goal_id.desc()).all()
        return [{
            "goal_id": r.goal_id,
            "goal_code": r.goal_code,
            "goal_name": r.goal_name,
            "goal_type": r.goal_type,
            "status": r.status,
            "priority": r.priority,
            "progress_percent": float(r.progress_percent or 0),
            "risk_status": r.risk_status,
            "owner_name": r.owner_name,
            "linked_project_count": int(r.linked_project_count or 0),
            "linked_task_count": int(r.linked_task_count or 0),
        } for r in rows]

    def _refresh_link_counts(self, goal_id: int):
        goal = self.db.query(WmGoal).filter(WmGoal.goal_id == goal_id).first()
        if not goal:
            return
        links = self.db.query(WmGoalLink).filter(WmGoalLink.goal_id == goal_id).all()
        goal.linked_project_count = sum(1 for l in links if l.linked_entity_type == "PROJECT")
        goal.linked_task_count = sum(1 for l in links if l.linked_entity_type == "TASK")


class IntakeConversionService:
    def __init__(self, db: Session):
        self.db = db

    def convert(self, intake_id: int, payload: IntakeConvertRequest) -> dict:
        row = self.db.query(WmIntakeRequest).filter(WmIntakeRequest.intake_request_id == intake_id).first()
        if not row:
            raise ValueError("Intake request not found")
        row.converted_entity_type = payload.target_entity_type
        row.converted_entity_id = payload.target_entity_id
        row.status = f"Converted to {payload.target_entity_type}"
        row.updated_by = payload.updated_by
        row.updated_at = datetime.utcnow()
        self.db.commit()
        return {"status": "success", "intake_request_id": intake_id, "converted_entity_type": row.converted_entity_type, "converted_entity_id": row.converted_entity_id}


class IntakeService:
    def __init__(self, db: Session):
        self.db = db
        self.convertor = IntakeConversionService(db)

    def submit(self, payload: IntakeRequestCreate) -> dict:
        row = WmIntakeRequest(
            **payload.model_dump(exclude={"custom_fields"}),
            custom_fields_json=json.dumps(payload.custom_fields),
        )
        self.db.add(row)
        self.db.commit()
        return {"status": "success", "intake_request_id": row.intake_request_id}

    def update_status(self, intake_id: int, payload: IntakeStatusUpdateRequest) -> dict:
        row = self.db.query(WmIntakeRequest).filter(WmIntakeRequest.intake_request_id == intake_id).first()
        if not row:
            raise ValueError("Intake request not found")
        row.status = payload.status
        row.triage_owner_id = payload.triage_owner_id
        row.triage_owner_name = payload.triage_owner_name
        row.updated_by = payload.updated_by
        row.updated_at = datetime.utcnow()
        self.db.commit()
        return {"status": "success", "intake_request_id": intake_id, "new_status": row.status}

    def register(self) -> list[dict]:
        rows = self.db.query(WmIntakeRequest).filter(WmIntakeRequest.active_flag.is_(True)).order_by(WmIntakeRequest.intake_request_id.desc()).all()
        return [{
            "intake_request_id": r.intake_request_id,
            "request_code": r.request_code,
            "title": r.title,
            "request_type": r.request_type,
            "status": r.status,
            "urgency": r.urgency,
            "requester_name": r.requester_name,
            "approval_required": r.approval_required,
            "converted_entity_type": r.converted_entity_type,
        } for r in rows]


class LaunchReadinessService:
    def __init__(self, db: Session):
        self.db = db

    def recompute(self, launch_id: int) -> dict:
        launch = self.db.query(WmLaunch).filter(WmLaunch.launch_id == launch_id).first()
        if not launch:
            raise ValueError("Launch not found")
        milestones = self.db.query(WmLaunchMilestone).filter(WmLaunchMilestone.launch_id == launch_id, WmLaunchMilestone.active_flag.is_(True)).all()
        done = sum(1 for m in milestones if m.status in {"Completed", "Done"})
        readiness = round(done / (len(milestones) or 1) * 100, 2)
        launch.readiness_percent = readiness
        launch.risk_status = "On Track" if readiness >= 80 else "At Risk" if readiness >= 50 else "Off Track"
        launch.dependency_health = "Blocked" if any(m.dependency_health == "Blocked" for m in milestones) else "Healthy"
        launch.updated_at = datetime.utcnow()
        self.db.commit()
        return {"launch_id": launch_id, "readiness_percent": readiness, "risk_status": launch.risk_status, "dependency_health": launch.dependency_health}


class LaunchService:
    def __init__(self, db: Session):
        self.db = db
        self.readiness = LaunchReadinessService(db)

    def create(self, payload: LaunchCreateRequest) -> dict:
        row = WmLaunch(**payload.model_dump())
        self.db.add(row)
        self.db.commit()
        return {"status": "success", "launch_id": row.launch_id}

    def add_milestone(self, launch_id: int, payload: LaunchMilestoneRequest) -> dict:
        row = WmLaunchMilestone(launch_id=launch_id, **payload.model_dump())
        self.db.add(row)
        self.db.commit()
        self.readiness.recompute(launch_id)
        return {"status": "success", "launch_milestone_id": row.launch_milestone_id}

    def update_status(self, launch_id: int, payload: LaunchStatusUpdateRequest) -> dict:
        row = self.db.query(WmLaunch).filter(WmLaunch.launch_id == launch_id).first()
        if not row:
            raise ValueError("Launch not found")
        row.launch_status = payload.launch_status
        if payload.readiness_percent is not None:
            row.readiness_percent = payload.readiness_percent
        if payload.risk_status is not None:
            row.risk_status = payload.risk_status
        if payload.dependency_health is not None:
            row.dependency_health = payload.dependency_health
        row.updated_by = payload.updated_by
        row.updated_at = datetime.utcnow()
        self.db.commit()
        return {"status": "success", "launch_id": launch_id, "launch_status": row.launch_status}

    def register(self) -> list[dict]:
        rows = self.db.query(WmLaunch).filter(WmLaunch.active_flag.is_(True)).order_by(WmLaunch.launch_id.desc()).all()
        return [{
            "launch_id": r.launch_id,
            "launch_code": r.launch_code,
            "launch_name": r.launch_name,
            "launch_status": r.launch_status,
            "launch_priority": r.launch_priority,
            "readiness_percent": float(r.readiness_percent or 0),
            "risk_status": r.risk_status,
            "dependency_health": r.dependency_health,
            "target_launch_date": r.target_launch_date,
        } for r in rows]


class ResourceAllocationService:
    def __init__(self, db: Session):
        self.db = db

    def allocate(self, payload: ResourceAllocationRequest) -> dict:
        available_hours = 9
        variance = payload.actual_hours - payload.planned_hours
        util = round((payload.actual_hours / available_hours) * 100, 2) if available_hours else 0
        row = WmResourceAllocation(
            **payload.model_dump(),
            variance_hours=variance,
            utilization_percent=util,
            overload_flag=payload.planned_hours > available_hours,
        )
        self.db.add(row)
        self.db.commit()
        return {"status": "success", "resource_allocation_id": row.resource_allocation_id}

    def capacity_views(self, payload: ResourceViewFilter) -> dict:
        q = self.db.query(WmResourceAllocation).filter(
            WmResourceAllocation.allocation_date >= payload.start_date,
            WmResourceAllocation.allocation_date <= payload.end_date,
            WmResourceAllocation.active_flag.is_(True),
        )
        if payload.manager_id:
            q = q.filter(WmResourceAllocation.manager_id == payload.manager_id)
        if payload.department_id:
            q = q.filter(WmResourceAllocation.department_id == payload.department_id)

        rows = q.all()
        by_emp = defaultdict(lambda: {"planned": 0.0, "actual": 0.0, "overloaded": False})
        for r in rows:
            by_emp[r.employee_id]["planned"] += float(r.planned_hours or 0)
            by_emp[r.employee_id]["actual"] += float(r.actual_hours or 0)
            by_emp[r.employee_id]["overloaded"] = by_emp[r.employee_id]["overloaded"] or bool(r.overload_flag)

        register = []
        for emp_id, values in by_emp.items():
            free = max(0.0, 9 * ((payload.end_date - payload.start_date).days + 1) - values["planned"])
            register.append({
                "employee_id": emp_id,
                "planned_hours": round(values["planned"], 2),
                "actual_hours": round(values["actual"], 2),
                "variance_hours": round(values["actual"] - values["planned"], 2),
                "free_capacity_hours": round(free, 2),
                "overloaded": values["overloaded"],
            })

        return {
            "employee_capacity_calendar": register,
            "team_capacity_calendar": register,
            "capacity_heatmap": [{"employee_id": r["employee_id"], "intensity": "high" if r["overloaded"] else "normal"} for r in register],
            "assignment_board": rows,
            "resource_allocation_register": register,
            "planned_vs_actual_utilization": register,
            "free_capacity_view": [r for r in register if r["free_capacity_hours"] > 0],
            "overload_view": [r for r in register if r["overloaded"]],
        }


class StrategicDashboardService:
    def __init__(self, db: Session):
        self.db = db

    def widgets(self) -> dict:
        goals = self.db.query(WmGoal).filter(WmGoal.active_flag.is_(True)).all()
        intake = self.db.query(WmIntakeRequest).filter(WmIntakeRequest.active_flag.is_(True)).all()
        launches = self.db.query(WmLaunch).filter(WmLaunch.active_flag.is_(True)).all()
        allocations = self.db.query(WmResourceAllocation).filter(WmResourceAllocation.active_flag.is_(True)).all()

        return {
            "goal_widgets": {
                "active_goals": len(goals),
                "goals_on_track": sum(1 for g in goals if g.risk_status == "On Track"),
                "goals_at_risk": sum(1 for g in goals if g.risk_status == "At Risk"),
                "goals_off_track": sum(1 for g in goals if g.risk_status == "Off Track"),
                "goal_progress_by_department": Counter(g.department_id for g in goals),
            },
            "intake_widgets": {
                "new_requests": sum(1 for i in intake if i.status == "New"),
                "intake_backlog": sum(1 for i in intake if i.status in {"New", "Under Review", "Awaiting Approval"}),
                "requests_awaiting_approval": sum(1 for i in intake if i.status == "Awaiting Approval"),
                "request_volume_by_type": Counter(i.request_type for i in intake),
            },
            "launch_widgets": {
                "active_launches": len(launches),
                "launches_at_risk": sum(1 for l in launches if l.risk_status in {"At Risk", "Off Track"}),
                "upcoming_launch_dates": [str(l.target_launch_date) for l in launches if l.target_launch_date],
                "launch_readiness_percent": [float(l.readiness_percent or 0) for l in launches],
            },
            "resource_widgets": {
                "free_capacity_today_week": sum(max(0.0, 9 - float(a.planned_hours or 0)) for a in allocations),
                "overloaded_employees": len({a.employee_id for a in allocations if a.overload_flag}),
                "underutilized_employees": len({a.employee_id for a in allocations if float(a.utilization_percent or 0) < 60}),
                "planned_vs_actual_hours": {
                    "planned": round(sum(float(a.planned_hours or 0) for a in allocations), 2),
                    "actual": round(sum(float(a.actual_hours or 0) for a in allocations), 2),
                },
                "capacity_by_manager": Counter(a.manager_id for a in allocations),
            },
        }


class StrategicReportService:
    def __init__(self, db: Session):
        self.db = db

    def reports(self, payload: StrategicReportRequest) -> dict:
        goals = self.db.query(WmGoal).all()
        intake = self.db.query(WmIntakeRequest).all()
        launches = self.db.query(WmLaunch).all()
        allocations = self.db.query(WmResourceAllocation).all()

        return {
            "goal_reports": {
                "goal_register": [{"goal_id": g.goal_id, "goal_name": g.goal_name, "status": g.status} for g in goals],
                "goal_progress_report": [{"goal_id": g.goal_id, "progress_percent": float(g.progress_percent or 0)} for g in goals],
                "goal_risk_report": Counter(g.risk_status for g in goals),
                "goal_contribution_report": Counter(g.goal_type for g in goals),
                "goal_performance_by_department_manager": Counter((g.department_id, g.owner_id) for g in goals),
            },
            "intake_reports": {
                "intake_register": [{"intake_request_id": i.intake_request_id, "status": i.status, "request_type": i.request_type} for i in intake],
                "intake_aging_report": [{"intake_request_id": i.intake_request_id, "age_days": (date.today() - i.created_at.date()).days} for i in intake],
                "intake_conversion_report": Counter(i.converted_entity_type or "Not Converted" for i in intake),
                "intake_approval_turnaround_report": [{"intake_request_id": i.intake_request_id, "status": i.status} for i in intake],
                "intake_rejection_report": sum(1 for i in intake if i.status == "Rejected"),
            },
            "launch_reports": {
                "launch_register": [{"launch_id": l.launch_id, "launch_name": l.launch_name, "status": l.launch_status} for l in launches],
                "launch_readiness_report": [{"launch_id": l.launch_id, "readiness_percent": float(l.readiness_percent or 0)} for l in launches],
                "launch_milestone_report": Counter(m.launch_id for m in self.db.query(WmLaunchMilestone).all()),
                "launch_cost_vs_budget_report": [{"launch_id": l.launch_id, "budget": float(l.budget_amount or 0), "cost": float(l.cost_to_company_rollup or 0)} for l in launches],
                "launch_delay_report": [{"launch_id": l.launch_id, "delay_days": max((date.today() - l.target_launch_date).days, 0) if l.target_launch_date else 0} for l in launches],
            },
            "resource_reports": {
                "employee_capacity_report": Counter(a.employee_id for a in allocations),
                "team_capacity_report": Counter(a.manager_id for a in allocations),
                "planned_vs_actual_utilization_report": [{"employee_id": a.employee_id, "planned": float(a.planned_hours or 0), "actual": float(a.actual_hours or 0)} for a in allocations],
                "free_capacity_report": [{"employee_id": a.employee_id, "free": max(0.0, 9 - float(a.planned_hours or 0))} for a in allocations],
                "overload_report": [{"employee_id": a.employee_id, "overload": a.overload_flag} for a in allocations],
                "resource_allocation_by_project_launch_client": Counter((a.project_id, a.launch_id) for a in allocations),
            },
        }
