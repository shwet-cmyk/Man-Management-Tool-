from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
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
    ScenarioSeedRequest,
)
from app.modules.project_collab.service import (
    FileLinkService,
    ProjectAccessService,
    ProjectAnalyticsService,
    ProjectChatService,
    ProjectScenarioService,
    ProjectService,
    ProjectTeamService,
    ProjectViewService,
    WatcherService,
)

router = APIRouter(prefix="/project-collab", tags=["Project Collaboration"])


@router.post("/project")
def create_project(payload: ProjectCreateRequest, db: Session = Depends(get_db)):
    return ProjectService(db).create_project(payload)


@router.post("/project/list")
def list_projects(payload: ProjectListFilterRequest, db: Session = Depends(get_db)):
    return {"rows": ProjectService(db).list_projects(payload)}


@router.get("/project/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db)):
    return ProjectService(db).get_project(project_id)


@router.post("/project/{project_id}/status")
def update_status(project_id: int, payload: ProjectStatusUpdateRequest, db: Session = Depends(get_db)):
    return ProjectService(db).update_status(project_id, payload)


@router.post("/project/{project_id}/team")
def add_member(project_id: int, payload: ProjectTeamMemberCreateRequest, db: Session = Depends(get_db)):
    return ProjectTeamService(db).add_member(project_id, payload)


@router.patch("/team-member/{project_team_member_id}")
def update_member(project_team_member_id: int, payload: ProjectTeamMemberUpdateRequest, actor_user_id: int = Query(1), actor_name: str = Query("System"), db: Session = Depends(get_db)):
    return ProjectTeamService(db).update_member(project_team_member_id, payload, actor_user_id, actor_name)


@router.get("/project/{project_id}/team")
def list_team(project_id: int, db: Session = Depends(get_db)):
    return {"rows": ProjectTeamService(db).list_members(project_id)}


@router.post("/chat/message")
def post_message(payload: ProjectMessageCreateRequest, db: Session = Depends(get_db)):
    return ProjectChatService(db).post_message(payload)


@router.get("/chat/{project_id}")
def list_messages(project_id: int, entity_type: str | None = None, entity_id: int | None = None, db: Session = Depends(get_db)):
    return {"rows": ProjectChatService(db).list_messages(project_id, entity_type, entity_id)}


@router.post("/chat/{message_id}/pin")
def pin_message(message_id: int, actor_user_id: int = Query(1), actor_name: str = Query("System"), pinned: bool = Query(True), db: Session = Depends(get_db)):
    return ProjectChatService(db).pin_message(message_id, actor_user_id, actor_name, pinned)


@router.post("/file")
def add_file(payload: ProjectFileLinkRequest, db: Session = Depends(get_db)):
    return FileLinkService(db).add(payload)


@router.get("/file/{project_id}")
def list_files(project_id: int, linked_entity_type: str | None = None, db: Session = Depends(get_db)):
    return {"rows": FileLinkService(db).list(project_id, linked_entity_type)}


@router.post("/watch/follow")
def follow(payload: ProjectWatcherRequest, db: Session = Depends(get_db)):
    return WatcherService(db).follow(payload)


@router.post("/watch/{watcher_id}/unfollow")
def unfollow(watcher_id: int, db: Session = Depends(get_db)):
    return WatcherService(db).unfollow(watcher_id)


@router.post("/access/resolve")
def resolve_access(payload: ProjectAccessRequest):
    return ProjectAccessService().resolve_access(payload)


@router.get("/project/{project_id}/views")
def multi_views(project_id: int, db: Session = Depends(get_db)):
    return ProjectViewService(db).multi_view_payload(project_id)


@router.get("/project/{project_id}/overview")
def overview(project_id: int, can_view_financials: bool = False, db: Session = Depends(get_db)):
    return ProjectAnalyticsService(db).overview(project_id, can_view_financials)


@router.get("/widgets")
def widgets(db: Session = Depends(get_db)):
    return ProjectAnalyticsService(db).widgets()


@router.post("/reports")
def reports(payload: ProjectReportRequest, db: Session = Depends(get_db)):
    return ProjectAnalyticsService(db).reports(payload)


@router.post("/scenarios/seed")
def seed_scenarios(payload: ScenarioSeedRequest, db: Session = Depends(get_db)):
    return ProjectScenarioService(db).seed(payload.created_by)
