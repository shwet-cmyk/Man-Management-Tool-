from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/masters", tags=["Masters"])


class CompanyRequest(BaseModel):
    name: str


@router.get("/companies")
def list_companies():
    return [{"company_id": 1, "name": "TEZ"}]


@router.post("/companies")
def add_company(payload: CompanyRequest):
    return {"company_id": 2, "name": payload.name}
