from app.models.attendance import Attendance
from app.models.department import Department
from app.models.employee import Employee
from app.models.ref_employee import RefEmployee
from app.models.sync_log import SyncLog
from app.models.task_audit_log import TaskAuditLog
from app.models.wm_gamification_event import WmGamificationEvent
from app.models.wm_billing_configuration import WmBillingConfiguration
from app.models.wm_dashboard import WmDashboard
from app.models.wm_dashboard_widget import WmDashboardWidget
from app.models.wm_billing_document_link import WmBillingDocumentLink
from app.models.wm_billing_status_history import WmBillingStatusHistory
from app.models.wm_billing_readiness import WmBillingReadiness
from app.models.wm_exception_history import WmExceptionHistory
from app.models.wm_exception_instance import WmExceptionInstance
from app.models.wm_exception_rule import WmExceptionRule
from app.models.wm_expense_claim import WmExpenseClaim
from app.models.wm_widget_query import WmWidgetQuery
from app.models.wm_expense_claim_approval_history import WmExpenseClaimApprovalHistory
from app.models.wm_expense_claim_attachment import WmExpenseClaimAttachment
from app.models.wm_expense_claim_conversion_log import WmExpenseClaimConversionLog
from app.models.wm_job import WmJob
from app.models.wm_notification_queue import WmNotificationQueue
from app.models.wm_task import WmTask
from app.models.wm_task_assignment import WmTaskAssignment
from app.models.wm_task_child_item import WmTaskChildItem
from app.models.wm_task_child_item_conversion import WmTaskChildItemConversion
from app.models.wm_task_participant import WmTaskParticipant
from app.models.wm_task_participant_dependency import WmTaskParticipantDependency
from app.models.wm_task_participant_handoff import WmTaskParticipantHandoff
from app.models.wm_task_participant_submission import WmTaskParticipantSubmission
from app.models.wm_task_status_history import WmTaskStatusHistory
from app.models.wm_task_workflow_state import WmTaskWorkflowState
from app.models.wm_timesheet import WmTimesheet
from app.models.wm_timesheet_approval_history import WmTimesheetApprovalHistory

from app.models.wm_report import WmReport
from app.models.wm_report_config import WmReportConfig
from app.models.wm_report_schedule import WmReportSchedule
from app.models.wm_api_key import WmApiKey
from app.models.wm_api_log import WmApiLog
from app.models.wm_webhook import WmWebhook
from app.models.wm_webhook_log import WmWebhookLog
from app.models.wm_ai_prediction import WmAiPrediction
from app.models.wm_ai_recommendation import WmAiRecommendation
from app.models.wm_rbac_role import WmRbacRole
from app.models.wm_rbac_user_role import WmRbacUserRole
from app.models.wm_rbac_module import WmRbacModule
from app.models.wm_rbac_feature import WmRbacFeature
from app.models.wm_rbac_action import WmRbacAction
from app.models.wm_rbac_permission import WmRbacPermission
from app.models.wm_rbac_permission_scope import WmRbacPermissionScope
from app.models.wm_rbac_role_inheritance import WmRbacRoleInheritance
from app.models.wm_rbac_user_permission_override import WmRbacUserPermissionOverride
from app.models.wm_rbac_approval_limit import WmRbacApprovalLimit
from app.models.wm_rbac_access_log import WmRbacAccessLog
from app.models.wm_rbac_permission_node import WmRbacPermissionNode
from app.models.wm_rbac_user_access_profile import WmRbacUserAccessProfile
from app.models.wm_rbac_user_scope_map import WmRbacUserScopeMap
from app.models.wm_workflow import WmWorkflow
from app.models.wm_workflow_node import WmWorkflowNode
from app.models.wm_workflow_edge import WmWorkflowEdge
from app.models.wm_workflow_instance import WmWorkflowInstance
from app.models.wm_workflow_log import WmWorkflowLog
from app.models.wm_sla_rule import WmSlaRule
from app.models.wm_sla_log import WmSlaLog
from app.models.wm_workflow_approval import WmWorkflowApproval
from app.models.wm_approval_workflow import WmApprovalWorkflow
from app.models.wm_approval_step import WmApprovalStep
from app.models.wm_approval_rule import WmApprovalRule
from app.models.wm_approval_transaction import WmApprovalTransaction
from app.models.wm_approval_log import WmApprovalLog
from app.models.wm_document import WmDocument
from app.models.wm_document_link import WmDocumentLink
from app.models.wm_document_audit import WmDocumentAudit
from app.models.wm_audit_field_change import WmAuditFieldChange
from app.models.wm_entity_version import WmEntityVersion
from app.models.wm_crm_lead import WmCrmLead
from app.models.wm_crm_opportunity import WmCrmOpportunity
from app.models.wm_crm_deal import WmCrmDeal
from app.models.wm_crm_followup import WmCrmFollowup
from app.models.wm_customer_lifecycle import WmCustomerLifecycle
from app.models.wm_sales_history import WmSalesHistory
from app.models.wm_forecast import WmForecast
from app.models.wm_customer_score import WmCustomerScore
from app.models.wm_rule import WmRule
from app.models.wm_rule_execution_log import WmRuleExecutionLog
from app.models.wm_sla_policy import WmSlaPolicy
from app.models.wm_sla_instance import WmSlaInstance
from app.models.wm_sla_escalation import WmSlaEscalation
from app.models.wm_business_holiday import WmBusinessHoliday
from app.models.wm_shift_master import WmShiftMaster
from app.models.wm_holiday_calendar import WmHolidayCalendar
from app.models.wm_ticket import WmTicket
from app.models.wm_ticket_user import WmTicketUser
from app.models.wm_ticket_comment import WmTicketComment
from app.models.wm_ticket_history import WmTicketHistory
from app.models.wm_ticket_followup import WmTicketFollowup
from app.models.wm_ticket_pause_history import WmTicketPauseHistory
from app.models.wm_ticket_escalation_log import WmTicketEscalationLog
from app.models.wm_task_rollover_history import WmTaskRolloverHistory
from app.models.wm_ticket_task_link import WmTicketTaskLink
from app.models.wm_employee_group import WmEmployeeGroup
from app.models.wm_employee_group_member import WmEmployeeGroupMember
from app.models.wm_job_task_line import WmJobTaskLine
from app.models.wm_timesheet_expense_line import WmTimesheetExpenseLine
from app.models.wm_timesheet_reimbursement_line import WmTimesheetReimbursementLine
from app.models.wm_attachment import WmAttachment
from app.models.wm_man_management_setting import WmManManagementSetting
from app.models.wm_man_approval import WmManApproval
from app.models.wm_alert_setting import WmAlertSetting
from app.models.wm_alert_template import WmAlertTemplate
from app.models.wm_alert_log import WmAlertLog
from app.models.wm_alert_recipient_matrix import WmAlertRecipientMatrix
from app.models.wm_points_event import WmPointsEvent
from app.models.wm_increment_config import WmIncrementConfig
from app.models.wm_project import WmProject
from app.models.wm_project_team_member import WmProjectTeamMember
from app.models.wm_project_chat_message import WmProjectChatMessage
from app.models.wm_project_file_link import WmProjectFileLink
from app.models.wm_project_watcher import WmProjectWatcher
from app.models.wm_project_audit_event import WmProjectAuditEvent
from app.models.wm_goal import WmGoal
from app.models.wm_goal_link import WmGoalLink
from app.models.wm_intake_request import WmIntakeRequest
from app.models.wm_launch import WmLaunch
from app.models.wm_launch_milestone import WmLaunchMilestone
from app.models.wm_resource_allocation import WmResourceAllocation
from app.models.task_dependencies import TaskDependency
from app.models.audit_logs_v2 import AuditLogV2
from app.models.sla_tracking import SlaTracking
__all__ = [
    "Department",
    "Employee",
    "Attendance",
    "RefEmployee",
    "SyncLog",
    "WmTask",
    "WmTaskAssignment",
    "TaskAuditLog",
    "WmTaskWorkflowState",
    "WmNotificationQueue",
    "WmTaskStatusHistory",
    "WmGamificationEvent",
    "WmJob",
    "WmTaskChildItem",
    "WmTaskChildItemConversion",
    "WmTaskParticipant",
    "WmTaskParticipantDependency",
    "WmTaskParticipantSubmission",
    "WmTaskParticipantHandoff",
    "WmTimesheet",
    "WmTimesheetApprovalHistory",
    "WmBillingConfiguration",
    "WmDashboard",
    "WmDashboardWidget",
    "WmBillingDocumentLink",
    "WmBillingStatusHistory",
    "WmBillingReadiness",
    "WmExceptionRule",
    "WmExceptionInstance",
    "WmExceptionHistory",
    "WmExpenseClaim",
    "WmWidgetQuery",
    "WmExpenseClaimApprovalHistory",
    "WmExpenseClaimAttachment",
    "WmExpenseClaimConversionLog",
    "WmReport",
    "WmReportConfig",
    "WmReportSchedule",
    "WmAiRecommendation",
    "WmAiPrediction",
    "WmWebhookLog",
    "WmWebhook",
    "WmApiLog",
    "WmApiKey",
    "WmRbacUserPermissionOverride",
    "WmRbacRoleInheritance",
    "WmRbacPermissionScope",
    "WmRbacPermission",
    "WmRbacAction",
    "WmRbacFeature",
    "WmRbacModule",
    "WmRbacUserRole",
    "WmRbacRole",
    "WmRbacPermissionNode",
    "WmRbacUserAccessProfile",
    "WmRbacUserScopeMap",
    "WmWorkflowApproval",
    "WmSlaLog",
    "WmSlaRule",
    "WmWorkflowLog",
    "WmWorkflowInstance",
    "WmWorkflowEdge",
    "WmWorkflowNode",
    "WmWorkflow",
    "WmBusinessHoliday",
    "WmShiftMaster",
    "WmHolidayCalendar",
    "WmSlaEscalation",
    "WmSlaInstance",
    "WmSlaPolicy",
    "WmTicketHistory",
    "WmTicketComment",
    "WmTicketUser",
    "WmTicket",
    "WmTicketFollowup",
    "WmTicketPauseHistory",
    "WmTicketEscalationLog",
    "WmTaskRolloverHistory",
    "WmTicketTaskLink",
    "WmEmployeeGroup",
    "WmEmployeeGroupMember",
    "WmJobTaskLine",
    "WmTimesheetExpenseLine",
    "WmTimesheetReimbursementLine",
    "WmAttachment",
    "WmManManagementSetting",
    "WmManApproval",
    "WmAlertSetting",
    "WmAlertTemplate",
    "WmAlertLog",
    "WmAlertRecipientMatrix",
    "WmPointsEvent",
    "WmIncrementConfig",
    "WmProject",
    "WmProjectTeamMember",
    "WmProjectChatMessage",
    "WmProjectFileLink",
    "WmProjectWatcher",
    "WmProjectAuditEvent",
    "WmGoal",
    "WmGoalLink",
    "WmIntakeRequest",
    "WmLaunch",
    "WmLaunchMilestone",
    "WmResourceAllocation",
    "TaskDependency",
    "AuditLogV2",
    "SlaTracking",
]
