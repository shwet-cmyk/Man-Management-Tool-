from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import Base
from app.models.wm_rbac_permission_node import WmRbacPermissionNode
from app.modules.rbac.schemas import EffectiveAccessRequest, UserAccessProfileRequest, UserScopeMapRequest
from app.modules.rbac.service import RbacService


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def test_permission_tree_seed_matches_required_modules_and_children():
    db = setup_db()
    svc = RbacService(db)

    seed = svc.seed_permission_tree()
    assert seed["created"] > 0

    modules = {x.permission_label for x in db.query(WmRbacPermissionNode).filter(WmRbacPermissionNode.is_module_flag.is_(True)).all()}
    assert {"Jobs", "TimeSheet", "MasterCustomer", "MasterCompany", "MasterBranch", "MasterDepartment", "MasterEmployee"}.issubset(modules)

    jobs_children = {x.permission_label for x in db.query(WmRbacPermissionNode).filter(WmRbacPermissionNode.module_code == "JOBS", WmRbacPermissionNode.is_action_flag.is_(True)).all()}
    assert {"Add new entry", "Edit entry", "Delete entry", "Time Sheet", "Add Time Sheet", "Manual Voucher No", "Manual Date", "Send Email", "Attach Document", "Print voucher", "Reports", "Create Invoice", "Create Proforma", "View Amount", "Import Excel", "Assign MultiJobs To Employee", "Dowload data in Excel"}.issubset(jobs_children)


def test_permission_tree_and_user_scope_profile():
    db = setup_db()
    svc = RbacService(db)

    svc.seed_permission_tree()
    svc.upsert_user_access_profile(5001, UserAccessProfileRequest(entries_of_self_and_downline=True, entries_of_self_only=False, agent_level="SELF_AND_DOWNLINE"))
    scope = svc.set_user_scope(5001, UserScopeMapRequest(scope_type="COMPANY", scope_ids=[1, 2]))
    assert scope["count"] == 2

    effective = svc.effective_permission(EffectiveAccessRequest(user_id=5001, module_code="JOBS", permission_code="JOBS_VIEW_AMOUNT", company_id=1, creator_user_id=5001))
    assert "allowed" in effective
