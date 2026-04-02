from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.dependency_enforcement.schemas import DependencyActionRequest, DependencyCheckRequest, DependencyCreateRequest
from app.modules.dependency_enforcement.service import DependencyEnforcementService

router = APIRouter(prefix="/tasks", tags=["Dependency Enforcement"])


@router.post("/dependencies")
def create_dependency(payload: DependencyCreateRequest, db: Session = Depends(get_db)):
    return DependencyEnforcementService(db).create_dependency(payload)


@router.post("/check-dependency")
def check_dependency(payload: DependencyCheckRequest, db: Session = Depends(get_db)):
    return DependencyEnforcementService(db).check_dependency(payload)


@router.post("/dependency-action")
def dependency_action(payload: DependencyActionRequest, db: Session = Depends(get_db)):
    return DependencyEnforcementService(db).transition_dependency(payload)
