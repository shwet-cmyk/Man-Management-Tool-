from types import SimpleNamespace

from app.modules.project_collab.schemas import ProjectAccessRequest, ProjectMessageCreateRequest
from app.modules.project_collab.service import MentionService, ProjectAccessService, ProjectChatService


class FakeQuery:
    def __init__(self, rows):
        self.rows = rows

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.rows[0] if self.rows else None

    def all(self):
        return self.rows


class FakeDB:
    def __init__(self):
        self.payload = {
            "WmProjectChatMessage": [SimpleNamespace(sender_user_id=77)],
            "WmProjectTeamMember": [SimpleNamespace(employee_id=11), SimpleNamespace(employee_id=12)],
            "WmTask": [SimpleNamespace(primary_owner_emp_id=21, manager_emp_id=31, task_no="TASK-01")],
            "WmJob": [SimpleNamespace(assigned_employee_id=22, manager_id=32, job_no="JOB-01")],
        }

    def query(self, model):
        model_name = getattr(model, "__name__", str(model).split(".")[0])
        return FakeQuery(self.payload.get(model_name, []))


def test_mention_extract():
    text = "Please review @12 and @34 on blocker"
    mentions = MentionService.extract_mentions(text)
    assert mentions == ["12", "34"]


def test_project_access_resolution_financial_gate():
    payload = ProjectAccessRequest(
        project_id=1,
        employee_id=101,
        employee_role="Contributor",
        is_project_member=True,
        scope_mode="self",
        can_view_financials=True,
    )
    result = ProjectAccessService().resolve_access(payload)
    assert result["can_view_project"] is True
    assert result["can_collaborate"] is True
    assert result["can_view_financials"] is False


def test_project_access_manager_financial():
    payload = ProjectAccessRequest(
        project_id=2,
        employee_id=201,
        employee_role="Manager",
        is_project_member=False,
        scope_mode="all",
        can_view_financials=True,
    )
    result = ProjectAccessService().resolve_access(payload)
    assert result["can_view_project"] is True
    assert result["can_collaborate"] is True
    assert result["can_view_financials"] is True


def test_chat_notification_target_rules():
    service = ProjectChatService(FakeDB())
    payload = ProjectMessageCreateRequest(
        project_id=9,
        entity_type="TASK",
        entity_id=101,
        message_type="announcement",
        message_text="Please review @12",
        sender_user_id=11,
        sender_name="Owner",
        reply_to_message_id=6,
    )
    recipients = service._notification_recipients(payload, row=SimpleNamespace(message_id=9), mentions=["12"])
    recipient_ids = {row["recipient_employee_id"] for row in recipients}
    assert 12 in recipient_ids  # mention + announcement dedupe
    assert 77 in recipient_ids  # reply
    assert 21 in recipient_ids  # task assignee
    assert 31 in recipient_ids  # task manager
