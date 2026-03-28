from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
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
from app.modules.strategic_ops.service import (
    GoalRollupService,
    GoalService,
    IntakeService,
    LaunchReadinessService,
    LaunchService,
    ResourceAllocationService,
    StrategicDashboardService,
    StrategicReportService,
)

router = APIRouter(prefix="/strategic-ops", tags=["Strategic Operations"])


@router.post("/goals")
def create_goal(payload: GoalCreateRequest, db: Session = Depends(get_db)):
    return GoalService(db).create(payload)


@router.post("/goals/{goal_id}/link")
def link_goal(goal_id: int, payload: GoalLinkRequest, db: Session = Depends(get_db)):
    return GoalService(db).link(goal_id, payload)


@router.post("/goals/{goal_id}/progress")
def update_goal_progress(goal_id: int, payload: GoalProgressUpdateRequest, db: Session = Depends(get_db)):
    return GoalService(db).update_progress(goal_id, payload)


@router.post("/goals/{goal_id}/rollup")
def rollup_goal(goal_id: int, db: Session = Depends(get_db)):
    return GoalRollupService(db).compute(goal_id)


@router.get("/goals")
def list_goals(db: Session = Depends(get_db)):
    return {"rows": GoalService(db).list()}


@router.post("/intake")
def submit_intake(payload: IntakeRequestCreate, db: Session = Depends(get_db)):
    return IntakeService(db).submit(payload)


@router.post("/intake/{intake_id}/status")
def intake_status(intake_id: int, payload: IntakeStatusUpdateRequest, db: Session = Depends(get_db)):
    return IntakeService(db).update_status(intake_id, payload)


@router.post("/intake/{intake_id}/convert")
def intake_convert(intake_id: int, payload: IntakeConvertRequest, db: Session = Depends(get_db)):
    return IntakeService(db).convertor.convert(intake_id, payload)


@router.get("/intake")
def intake_register(db: Session = Depends(get_db)):
    return {"rows": IntakeService(db).register()}


@router.post("/launch")
def create_launch(payload: LaunchCreateRequest, db: Session = Depends(get_db)):
    return LaunchService(db).create(payload)


@router.post("/launch/{launch_id}/milestone")
def add_milestone(launch_id: int, payload: LaunchMilestoneRequest, db: Session = Depends(get_db)):
    return LaunchService(db).add_milestone(launch_id, payload)


@router.post("/launch/{launch_id}/status")
def launch_status(launch_id: int, payload: LaunchStatusUpdateRequest, db: Session = Depends(get_db)):
    return LaunchService(db).update_status(launch_id, payload)


@router.post("/launch/{launch_id}/readiness")
def launch_readiness(launch_id: int, db: Session = Depends(get_db)):
    return LaunchReadinessService(db).recompute(launch_id)


@router.get("/launch")
def launch_register(db: Session = Depends(get_db)):
    return {"rows": LaunchService(db).register()}


@router.post("/resource/allocation")
def allocate_resource(payload: ResourceAllocationRequest, db: Session = Depends(get_db)):
    return ResourceAllocationService(db).allocate(payload)


@router.post("/resource/views")
def resource_views(payload: ResourceViewFilter, db: Session = Depends(get_db)):
    return ResourceAllocationService(db).capacity_views(payload)


@router.get("/widgets")
def strategic_widgets(db: Session = Depends(get_db)):
    return StrategicDashboardService(db).widgets()


@router.post("/reports")
def strategic_reports(payload: StrategicReportRequest, db: Session = Depends(get_db)):
    return StrategicReportService(db).reports(payload)
