from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import Base
from app.models.ref_employee import RefEmployee
from app.models.sync_log import SyncLog
from app.modules.master_sync.service import EmployeeSyncService


class FakeERPClient:
    def __init__(self, payload):
        self.payload = payload

    def get_employees(self):
        return self.payload


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return TestingSessionLocal()


def test_fresh_sync_inserts_rows():
    db = setup_db()
    client = FakeERPClient(
        [
            {"empId": 1, "employeeName": "Alice", "active": 1, "monthlyCTC": 160000, "companyId": 10},
            {"empId": 2, "employeeName": "Bob", "active": 1, "monthlyCTC": 0, "companyId": 10},
        ]
    )

    result = EmployeeSyncService(db=db, erp_client=client).sync_employees(sync_mode="FULL")

    assert result["inserted"] == 2
    assert result["updated"] == 0
    assert db.query(RefEmployee).count() == 2


def test_second_sync_updates_existing_and_skips_duplicate_record():
    db = setup_db()
    seed_client = FakeERPClient(
        [{"empId": 5, "employeeName": "Charlie", "active": 1, "monthlyCTC": 100000, "companyId": 99}]
    )
    EmployeeSyncService(db=db, erp_client=seed_client).sync_employees(sync_mode="FULL")

    update_client = FakeERPClient(
        [
            {"empId": 5, "employeeName": "Charlie Updated", "active": 1, "monthlyCTC": 120000, "companyId": 99},
            {"empId": 5, "employeeName": "Duplicate", "active": 1, "monthlyCTC": 120000, "companyId": 99},
        ]
    )

    result = EmployeeSyncService(db=db, erp_client=update_client).sync_employees(sync_mode="FULL")

    assert result["updated"] == 1
    assert result["skipped"] == 1
    assert db.query(RefEmployee).filter(RefEmployee.emp_id == 5).one().employee_name == "Charlie Updated"


def test_full_sync_marks_missing_employee_inactive():
    db = setup_db()
    initial_client = FakeERPClient(
        [
            {"empId": 11, "employeeName": "Keep", "active": 1, "monthlyCTC": 80000, "companyId": 1},
            {"empId": 12, "employeeName": "Drop", "active": 1, "monthlyCTC": 80000, "companyId": 1},
        ]
    )
    EmployeeSyncService(db=db, erp_client=initial_client).sync_employees(sync_mode="FULL")

    second_client = FakeERPClient(
        [{"empId": 11, "employeeName": "Keep", "active": 1, "monthlyCTC": 80000, "companyId": 1}]
    )
    EmployeeSyncService(db=db, erp_client=second_client).sync_employees(sync_mode="FULL")

    dropped = db.query(RefEmployee).filter(RefEmployee.emp_id == 12).one()
    assert dropped.is_active is False


def test_sync_writes_logs():
    db = setup_db()
    client = FakeERPClient([{"empId": 40, "employeeName": "Log User", "active": 1, "monthlyCTC": 70000, "companyId": 4}])

    EmployeeSyncService(db=db, erp_client=client).sync_employees(sync_mode="INCREMENTAL")

    logs = db.query(SyncLog).all()
    assert len(logs) == 1
    assert logs[0].status == "SUCCESS"
