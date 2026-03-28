from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.rules.schemas import RuleCreateRequest, RuleEvaluateRequest
from app.modules.rules.service import RuleService

router = APIRouter(prefix="/rule", tags=["Work Management - Rule Engine"])


@router.post("")
def create_rule(payload: RuleCreateRequest, db: Session = Depends(get_db)):
    return RuleService(db).create_rule(payload)


@router.get("/evaluate")
def evaluate(module: str, context_json: str = "{}", db: Session = Depends(get_db)):
    import json

    return RuleService(db).evaluate(RuleEvaluateRequest(module=module, context=json.loads(context_json)))
