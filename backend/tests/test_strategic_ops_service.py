from datetime import date
from types import SimpleNamespace

from app.modules.strategic_ops.schemas import ResourceViewFilter
from app.modules.strategic_ops.service import ResourceAllocationService, StrategicDashboardService


class FakeQuery:
    def __init__(self, rows):
        self.rows = rows

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def all(self):
        return self.rows


class FakeDB:
    def __init__(self):
        self.map = {
            "WmResourceAllocation": [
                SimpleNamespace(employee_id=1, manager_id=10, department_id=100, planned_hours=10, actual_hours=9, overload_flag=True, utilization_percent=100, active_flag=True, allocation_date=date(2026, 3, 28)),
                SimpleNamespace(employee_id=2, manager_id=10, department_id=100, planned_hours=4, actual_hours=3, overload_flag=False, utilization_percent=33, active_flag=True, allocation_date=date(2026, 3, 28)),
            ],
            "WmGoal": [SimpleNamespace(active_flag=True, risk_status="At Risk", department_id=100, goal_type="Delivery")],
            "WmIntakeRequest": [SimpleNamespace(active_flag=True, status="New", request_type="Project")],
            "WmLaunch": [SimpleNamespace(active_flag=True, risk_status="At Risk", target_launch_date=date(2026, 4, 1), readiness_percent=75)],
        }

    def query(self, model):
        key = getattr(model, "__name__", str(model).split(".")[0])
        return FakeQuery(self.map.get(key, []))


def test_resource_capacity_views():
    service = ResourceAllocationService(FakeDB())
    out = service.capacity_views(ResourceViewFilter(start_date=date(2026, 3, 28), end_date=date(2026, 3, 28)))
    assert len(out["resource_allocation_register"]) == 2
    assert len(out["overload_view"]) == 1


def test_dashboard_widget_shapes():
    out = StrategicDashboardService(FakeDB()).widgets()
    assert "goal_widgets" in out
    assert "intake_widgets" in out
    assert "launch_widgets" in out
    assert "resource_widgets" in out
