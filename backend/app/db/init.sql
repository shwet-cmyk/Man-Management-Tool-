
IF NOT EXISTS (SELECT 1 FROM Roles WHERE RoleName='Admin') INSERT INTO Roles(RoleName) VALUES ('Admin');
IF NOT EXISTS (SELECT 1 FROM Roles WHERE RoleName='Manager') INSERT INTO Roles(RoleName) VALUES ('Manager');

DECLARE @AdminRoleId INT = (SELECT TOP 1 RoleID FROM Roles WHERE RoleName='Admin');
DECLARE @ManagerRoleId INT = (SELECT TOP 1 RoleID FROM Roles WHERE RoleName='Manager');

IF NOT EXISTS (SELECT 1 FROM Users WHERE Email='admin@tez.local')
INSERT INTO Users (FirstName, LastName, Email, PasswordHash, RoleID, EmployeeGroup, HourlyCost)
VALUES ('System','Admin','admin@tez.local','hashed-demo-password',@AdminRoleId,'Management',0);

IF NOT EXISTS (SELECT 1 FROM Users WHERE Email='manager@tez.local')
INSERT INTO Users (FirstName, LastName, Email, PasswordHash, RoleID, EmployeeGroup, HourlyCost)
VALUES ('Project','Manager','manager@tez.local','hashed-demo-password',@ManagerRoleId,'Operations',1200);

DECLARE @ManagerId INT = (SELECT TOP 1 UserID FROM Users WHERE Email='manager@tez.local');
DECLARE @AdminId INT = (SELECT TOP 1 UserID FROM Users WHERE Email='admin@tez.local');

IF NOT EXISTS (SELECT 1 FROM Projects WHERE Name='Sample Execution Project')
INSERT INTO Projects (Name, ClientName, ManagerID, StartDate, EndDate, Status, EstimatedCost, EstimatedHours)
VALUES ('Sample Execution Project','Demo Client',@ManagerId,GETDATE(),DATEADD(day, 30, GETDATE()),'ACTIVE',120000,160);

DECLARE @ProjectId INT = (SELECT TOP 1 ProjectID FROM Projects WHERE Name='Sample Execution Project');

IF NOT EXISTS (SELECT 1 FROM Tasks WHERE Name='Initial Discovery')
INSERT INTO Tasks (ProjectID, Name, Priority, Status, EstimatedHours, EstimatedCost, CreatedBy)
VALUES (@ProjectId,'Initial Discovery','HIGH','IN_PROGRESS',16,12000,@AdminId);

IF NOT EXISTS (SELECT 1 FROM Tasks WHERE Name='Implementation Sprint 1')
INSERT INTO Tasks (ProjectID, Name, Priority, Status, EstimatedHours, EstimatedCost, CreatedBy)
VALUES (@ProjectId,'Implementation Sprint 1','MEDIUM','NOT_STARTED',40,40000,@ManagerId);

DECLARE @Task1 INT = (SELECT TOP 1 TaskID FROM Tasks WHERE Name='Initial Discovery');
DECLARE @Task2 INT = (SELECT TOP 1 TaskID FROM Tasks WHERE Name='Implementation Sprint 1');

IF NOT EXISTS (SELECT 1 FROM Jobs WHERE TaskID=@Task1)
INSERT INTO Jobs (TaskID, AssignedUserID, Status, SLADeadline)
VALUES (@Task1,@ManagerId,'IN_PROGRESS',DATEADD(day,2,GETDATE()));

IF NOT EXISTS (SELECT 1 FROM Jobs WHERE TaskID=@Task2)
INSERT INTO Jobs (TaskID, AssignedUserID, Status, SLADeadline)
VALUES (@Task2,@AdminId,'PENDING',DATEADD(day,5,GETDATE()));

IF NOT EXISTS (SELECT 1 FROM chatbot_quick_prompts)
BEGIN
INSERT INTO chatbot_quick_prompts (module_name, screen_key, priority_level, condition_type, condition_query, prompt_text_en, prompt_text_hi, prompt_text_gu, prompt_text_mr, intent_code, action_type, route_path, display_order)
VALUES
('global', NULL, 'HIGH', 'CONTEXT_DRIVEN', NULL, 'Explain this screen', NULL, NULL, NULL, 'EXPLAIN_SCREEN', 'QUERY', NULL, 1),
('global', NULL, 'MEDIUM', 'CONTEXT_DRIVEN', NULL, 'What can I do here?', NULL, NULL, NULL, 'FEATURE_DISCOVERY', 'QUERY', NULL, 2),
('global', NULL, 'HIGH', 'DATA_DRIVEN', 'pending_approvals > 0', 'Show my pending approvals', N'मेरे pending approvals दिखाओ', N'મારા pending approvals બતાવો', N'माझे pending approvals दाखवा', 'GET_PENDING_APPROVALS', 'QUERY', '/approvals', 3),
('global', NULL, 'HIGH', 'DATA_DRIVEN', 'delayed_tasks > 0', 'Show delayed tasks', NULL, NULL, NULL, 'GET_DELAYED_TASKS', 'QUERY', '/tasks', 4),
('dashboard', 'dashboard_main', 'MEDIUM', 'CONTEXT_DRIVEN', NULL, 'Show today''s tasks', NULL, NULL, NULL, 'SHOW_TODAYS_TASKS', 'QUERY', '/dashboard', 1),
('dashboard', 'dashboard_main', 'MEDIUM', 'CONTEXT_DRIVEN', NULL, 'Show my workload', NULL, NULL, NULL, 'SHOW_WORKLOAD', 'QUERY', '/dashboard', 2),
('dashboard', 'dashboard_main', 'HIGH', 'DATA_DRIVEN', 'sla_breaches > 0', 'Show SLA breaches', NULL, NULL, NULL, 'SHOW_SLA_BREACHES', 'QUERY', '/dashboard', 3),
('dashboard', 'dashboard_main', 'HIGH', 'DATA_DRIVEN', 'pending_approvals > 0', 'Show pending approvals', NULL, NULL, NULL, 'GET_PENDING_APPROVALS', 'QUERY', '/approvals', 4),
('projects', 'project_detail', 'HIGH', 'DATA_DRIVEN', 'delayed_tasks > 0', 'Show delayed tasks in this project', NULL, NULL, NULL, 'PROJECT_DELAYED_TASKS', 'QUERY', '/projects', 1),
('projects', 'project_detail', 'MEDIUM', 'CONTEXT_DRIVEN', NULL, 'Show project budget vs actual', NULL, NULL, NULL, 'PROJECT_BUDGET_VS_ACTUAL', 'QUERY', '/projects', 2),
('projects', 'project_detail', 'MEDIUM', 'CONTEXT_DRIVEN', NULL, 'Show project completion %', NULL, NULL, NULL, 'PROJECT_COMPLETION', 'QUERY', '/projects', 3),
('projects', 'project_detail', 'HIGH', 'DATA_DRIVEN', 'pending_approvals > 0', 'Show pending approvals for this project', NULL, NULL, NULL, 'PROJECT_PENDING_APPROVALS', 'QUERY', '/approvals', 4),
('tasks', 'task_detail', 'HIGH', 'DATA_DRIVEN', 'delayed_tasks > 0', 'Why is this task delayed?', NULL, NULL, NULL, 'TASK_DELAY_REASON', 'QUERY', '/tasks', 1),
('tasks', 'task_detail', 'MEDIUM', 'CONTEXT_DRIVEN', NULL, 'Show dependency status', NULL, NULL, NULL, 'TASK_DEPENDENCY_STATUS', 'QUERY', '/tasks', 2),
('tasks', 'task_detail', 'MEDIUM', 'CONTEXT_DRIVEN', NULL, 'Show all jobs under this task', NULL, NULL, NULL, 'TASK_CHILD_JOBS', 'QUERY', '/tasks', 3),
('tasks', 'task_detail', 'MEDIUM', 'CONTEXT_DRIVEN', NULL, 'Who changed this deadline?', NULL, NULL, NULL, 'TASK_DEADLINE_AUDIT', 'QUERY', '/audit', 4),
('jobs', 'job_detail', 'MEDIUM', 'CONTEXT_DRIVEN', NULL, 'Show timesheet for this job', NULL, NULL, NULL, 'JOB_TIMESHEET', 'QUERY', '/timesheets', 1),
('jobs', 'job_detail', 'MEDIUM', 'CONTEXT_DRIVEN', NULL, 'Show job cost analysis', NULL, NULL, NULL, 'JOB_COST_ANALYSIS', 'QUERY', '/jobs', 2),
('jobs', 'job_detail', 'HIGH', 'DATA_DRIVEN', 'delayed_tasks > 0', 'Why is this job delayed?', NULL, NULL, NULL, 'JOB_DELAY_REASON', 'QUERY', '/jobs', 3),
('jobs', 'job_detail', 'HIGH', 'DATA_DRIVEN', 'sla_breaches > 0', 'Show SLA status', NULL, NULL, NULL, 'JOB_SLA_STATUS', 'QUERY', '/jobs', 4),
('approvals', 'approval_inbox', 'MEDIUM', 'CONTEXT_DRIVEN', NULL, 'What am I approving?', NULL, NULL, NULL, 'APPROVAL_CONTEXT', 'QUERY', '/approvals', 1),
('approvals', 'approval_inbox', 'MEDIUM', 'CONTEXT_DRIVEN', NULL, 'Show full task details', NULL, NULL, NULL, 'APPROVAL_TASK_DETAILS', 'QUERY', '/tasks', 2),
('approvals', 'approval_inbox', 'MEDIUM', 'CONTEXT_DRIVEN', NULL, 'Show approval history', NULL, NULL, NULL, 'APPROVAL_HISTORY', 'QUERY', '/approvals', 3),
('approvals', 'approval_inbox', 'MEDIUM', 'CONTEXT_DRIVEN', NULL, 'Why was this sent back?', NULL, NULL, NULL, 'APPROVAL_SENT_BACK_REASON', 'QUERY', '/approvals', 4),
('tickets', 'ticket_detail', 'MEDIUM', 'CONTEXT_DRIVEN', NULL, 'Show ticket history', NULL, NULL, NULL, 'TICKET_HISTORY', 'QUERY', '/tickets', 1),
('tickets', 'ticket_detail', 'MEDIUM', 'CONTEXT_DRIVEN', NULL, 'Show last follow-up', NULL, NULL, NULL, 'TICKET_LAST_FOLLOWUP', 'QUERY', '/tickets', 2),
('tickets', 'ticket_detail', 'HIGH', 'DATA_DRIVEN', 'sla_breaches > 0', 'What is SLA status?', NULL, NULL, NULL, 'TICKET_SLA_STATUS', 'QUERY', '/tickets', 3),
('tickets', 'ticket_detail', 'MEDIUM', 'CONTEXT_DRIVEN', NULL, 'Show customer details', NULL, NULL, NULL, 'TICKET_CUSTOMER_DETAILS', 'QUERY', '/tickets', 4),
('timesheets', 'timesheet_list', 'MEDIUM', 'CONTEXT_DRIVEN', NULL, 'Show my today''s time entries', NULL, NULL, NULL, 'TIMESHEET_TODAY_ENTRIES', 'QUERY', '/timesheets', 1),
('timesheets', 'timesheet_list', 'HIGH', 'DATA_DRIVEN', 'timesheet_overlaps > 0', 'Show overlaps', NULL, NULL, NULL, 'TIMESHEET_OVERLAPS', 'QUERY', '/timesheets', 2),
('timesheets', 'timesheet_list', 'MEDIUM', 'CONTEXT_DRIVEN', NULL, 'Show total hours today', NULL, NULL, NULL, 'TIMESHEET_TOTAL_HOURS', 'QUERY', '/timesheets', 3),
('timesheets', 'timesheet_list', 'MEDIUM', 'CONTEXT_DRIVEN', NULL, 'Show billable vs non-billable', NULL, NULL, NULL, 'TIMESHEET_BILLABLE_SPLIT', 'QUERY', '/timesheets', 4),
('audit', 'audit_log_list', 'MEDIUM', 'CONTEXT_DRIVEN', NULL, 'Who changed this record?', NULL, NULL, NULL, 'AUDIT_WHO_CHANGED', 'QUERY', '/audit', 1),
('audit', 'audit_log_list', 'MEDIUM', 'CONTEXT_DRIVEN', NULL, 'Show field changes', NULL, NULL, NULL, 'AUDIT_FIELD_CHANGES', 'QUERY', '/audit', 2),
('audit', 'audit_log_list', 'MEDIUM', 'CONTEXT_DRIVEN', NULL, 'Show yesterday changes', NULL, NULL, NULL, 'AUDIT_YESTERDAY', 'QUERY', '/audit', 3),
('audit', 'audit_log_list', 'MEDIUM', 'CONTEXT_DRIVEN', NULL, 'Show user activity', NULL, NULL, NULL, 'AUDIT_USER_ACTIVITY', 'QUERY', '/audit', 4);
END
