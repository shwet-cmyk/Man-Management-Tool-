CREATE DATABASE IESLManManagement;
GO

USE IESLManManagement;
GO

CREATE TABLE departments (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(100) NOT NULL UNIQUE,
    description NVARCHAR(255) NULL
);
GO

CREATE TABLE employees (
    id INT IDENTITY(1,1) PRIMARY KEY,
    employee_code NVARCHAR(20) NOT NULL UNIQUE,
    full_name NVARCHAR(120) NOT NULL,
    email NVARCHAR(120) NOT NULL UNIQUE,
    job_title NVARCHAR(100) NOT NULL,
    join_date DATE NOT NULL,
    department_id INT NOT NULL,
    CONSTRAINT fk_employees_department FOREIGN KEY (department_id) REFERENCES departments(id)
);
GO

CREATE TABLE attendance (
    id INT IDENTITY(1,1) PRIMARY KEY,
    employee_id INT NOT NULL,
    work_date DATE NOT NULL,
    status NVARCHAR(20) NOT NULL,
    remarks NVARCHAR(255) NULL,
    CONSTRAINT uq_attendance_employee_date UNIQUE (employee_id, work_date),
    CONSTRAINT fk_attendance_employee FOREIGN KEY (employee_id) REFERENCES employees(id)
);
GO

CREATE TABLE ref_employee (
    emp_id BIGINT PRIMARY KEY,
    employee_name NVARCHAR(255) NOT NULL,
    company_id BIGINT NOT NULL,
    branch_id BIGINT NULL,
    department_id BIGINT NULL,
    monthly_ctc DECIMAL(14,2) NOT NULL DEFAULT 0,
    hourly_cost DECIMAL(12,2) NULL,
    is_active BIT NOT NULL,
    last_synced_at DATETIME2 NOT NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE sync_log (
    id INT IDENTITY(1,1) PRIMARY KEY,
    entity NVARCHAR(50) NOT NULL,
    sync_mode NVARCHAR(20) NOT NULL,
    status NVARCHAR(20) NOT NULL,
    total_fetched INT NOT NULL DEFAULT 0,
    inserted INT NOT NULL DEFAULT 0,
    updated INT NOT NULL DEFAULT 0,
    skipped INT NOT NULL DEFAULT 0,
    failed INT NOT NULL DEFAULT 0,
    error_details NVARCHAR(MAX) NULL,
    started_at DATETIME2 NOT NULL,
    completed_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_task (
    task_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    task_no NVARCHAR(50) NOT NULL UNIQUE,
    company_id BIGINT NOT NULL,
    branch_id BIGINT NULL,
    department_id BIGINT NULL,
    customer_id BIGINT NULL,
    job_id BIGINT NULL,
    project_id BIGINT NULL,
    cost_center_id BIGINT NULL,
    parent_task_id BIGINT NULL,
    title NVARCHAR(500) NOT NULL,
    description NVARCHAR(MAX) NULL,
    task_type NVARCHAR(30) NOT NULL,
    priority_code NVARCHAR(20) NOT NULL,
    status_code NVARCHAR(30) NOT NULL,
    primary_owner_emp_id BIGINT NOT NULL,
    manager_emp_id BIGINT NULL,
    reviewer_emp_id BIGINT NULL,
    billable_flag BIT NOT NULL,
    billed_amount DECIMAL(14,2) NOT NULL DEFAULT 0,
    estimated_hours DECIMAL(12,2) NOT NULL,
    planned_start DATETIME2 NOT NULL,
    due_at DATETIME2 NOT NULL,
    completed_at DATETIME2 NULL,
    last_activity_at DATETIME2 NULL,
    workflow_id BIGINT NULL,
    workflow_state_code NVARCHAR(30) NULL,
    source_type NVARCHAR(20) NOT NULL DEFAULT 'MANUAL',
    source_reference NVARCHAR(100) NULL,
    created_by BIGINT NOT NULL,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    updated_by BIGINT NULL,
    updated_on DATETIME2 NULL,
    is_active BIT NOT NULL DEFAULT 1
);
GO

CREATE TABLE wm_task_assignment (
    task_assignment_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    task_id BIGINT NOT NULL,
    emp_id BIGINT NOT NULL,
    role_code NVARCHAR(20) NOT NULL,
    allocation_pct DECIMAL(5,2) NULL,
    assigned_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    assigned_by BIGINT NOT NULL,
    is_active BIT NOT NULL DEFAULT 1,
    CONSTRAINT fk_wm_task_assignment_task FOREIGN KEY (task_id) REFERENCES wm_task(task_id)
);
GO

CREATE TABLE wm_task_participant (
    task_participant_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    task_id BIGINT NOT NULL,
    emp_id BIGINT NOT NULL,
    role_code NVARCHAR(30) NOT NULL,
    planned_start DATETIME2 NOT NULL,
    planned_due DATETIME2 NOT NULL,
    actual_start DATETIME2 NULL,
    actual_due DATETIME2 NULL,
    sequence_no INT NULL,
    submission_required BIT NOT NULL DEFAULT 0,
    acceptance_required BIT NOT NULL DEFAULT 0,
    allocation_pct DECIMAL(5,2) NULL,
    is_mandatory BIT NOT NULL DEFAULT 1,
    participant_status NVARCHAR(30) NOT NULL DEFAULT 'Planned',
    remarks NVARCHAR(1000) NULL,
    created_by BIGINT NOT NULL,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    updated_by BIGINT NULL,
    updated_on DATETIME2 NULL,
    is_active BIT NOT NULL DEFAULT 1,
    CONSTRAINT fk_wm_task_participant_task FOREIGN KEY (task_id) REFERENCES wm_task(task_id)
);
GO

CREATE TABLE wm_task_participant_dependency (
    task_participant_dependency_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    task_id BIGINT NOT NULL,
    predecessor_participant_id BIGINT NOT NULL,
    successor_participant_id BIGINT NOT NULL,
    dependency_type NVARCHAR(30) NOT NULL,
    lag_hours DECIMAL(10,2) NULL,
    created_by BIGINT NOT NULL,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT fk_wm_task_participant_dependency_task FOREIGN KEY (task_id) REFERENCES wm_task(task_id),
    CONSTRAINT fk_wm_task_participant_dependency_predecessor FOREIGN KEY (predecessor_participant_id) REFERENCES wm_task_participant(task_participant_id),
    CONSTRAINT fk_wm_task_participant_dependency_successor FOREIGN KEY (successor_participant_id) REFERENCES wm_task_participant(task_participant_id)
);
GO

CREATE TABLE wm_task_participant_submission (
    submission_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    job_id BIGINT NOT NULL,
    task_id BIGINT NOT NULL,
    from_participant_id BIGINT NOT NULL,
    to_participant_id BIGINT NULL,
    handoff_type NVARCHAR(30) NOT NULL,
    submission_status NVARCHAR(30) NOT NULL,
    submission_note NVARCHAR(MAX) NULL,
    deliverable_link NVARCHAR(1000) NULL,
    attachment_ref NVARCHAR(1000) NULL,
    completion_pct DECIMAL(5,2) NULL,
    acceptance_required BIT NOT NULL DEFAULT 0,
    submitted_by BIGINT NOT NULL,
    submitted_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    accepted_on DATETIME2 NULL,
    accepted_by BIGINT NULL,
    rejected_on DATETIME2 NULL,
    rejected_by BIGINT NULL,
    decision_note NVARCHAR(MAX) NULL,
    override_flag BIT NOT NULL DEFAULT 0,
    override_reason NVARCHAR(1000) NULL,
    remarks NVARCHAR(1000) NULL,
    is_active BIT NOT NULL DEFAULT 1,
    CONSTRAINT fk_wm_task_participant_submission_task FOREIGN KEY (task_id) REFERENCES wm_task(task_id),
    CONSTRAINT fk_wm_task_participant_submission_from FOREIGN KEY (from_participant_id) REFERENCES wm_task_participant(task_participant_id),
    CONSTRAINT fk_wm_task_participant_submission_to FOREIGN KEY (to_participant_id) REFERENCES wm_task_participant(task_participant_id)
);
GO

CREATE TABLE wm_task_participant_handoff (
    handoff_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    submission_id BIGINT NOT NULL,
    task_id BIGINT NOT NULL,
    from_participant_id BIGINT NOT NULL,
    to_participant_id BIGINT NOT NULL,
    handoff_status NVARCHAR(30) NOT NULL,
    unlocked_on DATETIME2 NULL,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT fk_wm_task_participant_handoff_submission FOREIGN KEY (submission_id) REFERENCES wm_task_participant_submission(submission_id),
    CONSTRAINT fk_wm_task_participant_handoff_task FOREIGN KEY (task_id) REFERENCES wm_task(task_id),
    CONSTRAINT fk_wm_task_participant_handoff_from FOREIGN KEY (from_participant_id) REFERENCES wm_task_participant(task_participant_id),
    CONSTRAINT fk_wm_task_participant_handoff_to FOREIGN KEY (to_participant_id) REFERENCES wm_task_participant(task_participant_id)
);
GO

CREATE TABLE wm_timesheet (
    timesheet_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    company_id BIGINT NOT NULL,
    branch_id BIGINT NULL,
    department_id BIGINT NULL,
    customer_id BIGINT NULL,
    job_id BIGINT NOT NULL,
    task_id BIGINT NULL,
    task_participant_id BIGINT NULL,
    emp_id BIGINT NOT NULL,
    work_date DATE NOT NULL,
    start_time DATETIME2 NULL,
    end_time DATETIME2 NULL,
    hours DECIMAL(10,2) NOT NULL,
    billable_hours DECIMAL(10,2) NOT NULL DEFAULT 0,
    overtime_hours DECIMAL(10,2) NOT NULL DEFAULT 0,
    activity_type NVARCHAR(50) NULL,
    remarks NVARCHAR(1000) NULL,
    attachment_ref NVARCHAR(1000) NULL,
    expense_link_id BIGINT NULL,
    reimbursement_link_id BIGINT NULL,
    approval_status NVARCHAR(20) NOT NULL DEFAULT 'Draft',
    submitted_by BIGINT NULL,
    submitted_on DATETIME2 NULL,
    approved_by BIGINT NULL,
    approved_on DATETIME2 NULL,
    rejected_by BIGINT NULL,
    rejected_on DATETIME2 NULL,
    rejection_reason NVARCHAR(1000) NULL,
    entered_for_emp_id BIGINT NULL,
    created_by BIGINT NOT NULL,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    updated_by BIGINT NULL,
    updated_on DATETIME2 NULL,
    is_active BIT NOT NULL DEFAULT 1,
    CONSTRAINT fk_wm_timesheet_job FOREIGN KEY (job_id) REFERENCES wm_job(job_id),
    CONSTRAINT fk_wm_timesheet_task FOREIGN KEY (task_id) REFERENCES wm_task(task_id),
    CONSTRAINT fk_wm_timesheet_participant FOREIGN KEY (task_participant_id) REFERENCES wm_task_participant(task_participant_id)
);
GO

CREATE INDEX IX_wm_timesheet_emp_date
ON wm_timesheet(emp_id, work_date, start_time, end_time);
GO

CREATE INDEX IX_wm_timesheet_job_task_participant
ON wm_timesheet(job_id, task_id, task_participant_id);
GO

CREATE TABLE wm_timesheet_approval_history (
    timesheet_approval_history_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    timesheet_id BIGINT NOT NULL,
    old_status NVARCHAR(20) NOT NULL,
    new_status NVARCHAR(20) NOT NULL,
    action_code NVARCHAR(20) NOT NULL,
    decision_note NVARCHAR(1000) NULL,
    acted_by BIGINT NOT NULL,
    acted_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    override_flag BIT NOT NULL DEFAULT 0,
    override_reason NVARCHAR(1000) NULL,
    CONSTRAINT fk_wm_timesheet_approval_history_timesheet FOREIGN KEY (timesheet_id) REFERENCES wm_timesheet(timesheet_id)
);
GO

CREATE TABLE wm_expense_claim (
    claim_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    claim_no NVARCHAR(50) NOT NULL UNIQUE,
    claim_type NVARCHAR(30) NOT NULL,
    expense_type NVARCHAR(50) NOT NULL,
    company_id BIGINT NOT NULL,
    branch_id BIGINT NULL,
    department_id BIGINT NULL,
    emp_id BIGINT NOT NULL,
    entered_for_emp_id BIGINT NULL,
    job_id BIGINT NULL,
    task_id BIGINT NULL,
    task_participant_id BIGINT NULL,
    timesheet_id BIGINT NULL,
    customer_id BIGINT NULL,
    cost_center_id BIGINT NULL,
    expense_date DATE NOT NULL,
    amount DECIMAL(14,2) NOT NULL,
    tax_amount DECIMAL(14,2) NOT NULL DEFAULT 0,
    total_amount DECIMAL(14,2) NOT NULL,
    recoverable_flag BIT NOT NULL DEFAULT 0,
    vendor_payee_name NVARCHAR(255) NULL,
    remarks NVARCHAR(1000) NULL,
    approval_status NVARCHAR(20) NOT NULL DEFAULT 'Draft',
    submitted_by BIGINT NULL,
    submitted_on DATETIME2 NULL,
    approved_by BIGINT NULL,
    approved_on DATETIME2 NULL,
    rejected_by BIGINT NULL,
    rejected_on DATETIME2 NULL,
    rejection_reason NVARCHAR(1000) NULL,
    voucher_id BIGINT NULL,
    conversion_status NVARCHAR(30) NOT NULL DEFAULT 'Not Converted',
    converted_by BIGINT NULL,
    converted_on DATETIME2 NULL,
    conversion_error NVARCHAR(MAX) NULL,
    created_by BIGINT NOT NULL,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    updated_by BIGINT NULL,
    updated_on DATETIME2 NULL,
    is_active BIT NOT NULL DEFAULT 1,
    CONSTRAINT fk_wm_expense_claim_job FOREIGN KEY (job_id) REFERENCES wm_job(job_id),
    CONSTRAINT fk_wm_expense_claim_task FOREIGN KEY (task_id) REFERENCES wm_task(task_id),
    CONSTRAINT fk_wm_expense_claim_participant FOREIGN KEY (task_participant_id) REFERENCES wm_task_participant(task_participant_id),
    CONSTRAINT fk_wm_expense_claim_timesheet FOREIGN KEY (timesheet_id) REFERENCES wm_timesheet(timesheet_id)
);
GO

CREATE TABLE wm_expense_claim_attachment (
    claim_attachment_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    claim_id BIGINT NOT NULL,
    file_ref NVARCHAR(1000) NOT NULL,
    file_name NVARCHAR(255) NULL,
    uploaded_by BIGINT NOT NULL,
    uploaded_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT fk_wm_expense_claim_attachment_claim FOREIGN KEY (claim_id) REFERENCES wm_expense_claim(claim_id)
);
GO

CREATE TABLE wm_expense_claim_approval_history (
    expense_claim_approval_history_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    claim_id BIGINT NOT NULL,
    old_status NVARCHAR(20) NOT NULL,
    new_status NVARCHAR(20) NOT NULL,
    action_code NVARCHAR(20) NOT NULL,
    decision_note NVARCHAR(1000) NULL,
    acted_by BIGINT NOT NULL,
    acted_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    override_flag BIT NOT NULL DEFAULT 0,
    override_reason NVARCHAR(1000) NULL,
    CONSTRAINT fk_wm_expense_claim_approval_history_claim FOREIGN KEY (claim_id) REFERENCES wm_expense_claim(claim_id)
);
GO

CREATE TABLE wm_expense_claim_conversion_log (
    claim_conversion_log_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    claim_id BIGINT NOT NULL,
    old_conversion_status NVARCHAR(30) NOT NULL,
    new_conversion_status NVARCHAR(30) NOT NULL,
    voucher_id BIGINT NULL,
    voucher_no NVARCHAR(100) NULL,
    request_payload NVARCHAR(MAX) NULL,
    response_payload NVARCHAR(MAX) NULL,
    conversion_error NVARCHAR(MAX) NULL,
    converted_by BIGINT NOT NULL,
    converted_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    override_flag BIT NOT NULL DEFAULT 0,
    override_reason NVARCHAR(1000) NULL,
    CONSTRAINT fk_wm_expense_claim_conversion_log_claim FOREIGN KEY (claim_id) REFERENCES wm_expense_claim(claim_id)
);
GO

CREATE TABLE wm_audit_log (
    id INT IDENTITY(1,1) PRIMARY KEY,
    entity_name NVARCHAR(50) NOT NULL,
    entity_id BIGINT NOT NULL,
    action NVARCHAR(30) NOT NULL,
    details NVARCHAR(MAX) NULL,
    created_by BIGINT NOT NULL,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    ip_address NVARCHAR(64) NULL,
    device_info NVARCHAR(255) NULL,
    source NVARCHAR(30) NULL
);
GO

CREATE TABLE wm_audit_field_change (
    audit_field_change_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    audit_log_id BIGINT NOT NULL,
    field_name NVARCHAR(100) NOT NULL,
    old_value NVARCHAR(MAX) NULL,
    new_value NVARCHAR(MAX) NULL,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_entity_version (
    entity_version_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    entity_type NVARCHAR(100) NOT NULL,
    entity_id BIGINT NOT NULL,
    version_no BIGINT NOT NULL,
    snapshot_json NVARCHAR(MAX) NOT NULL,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO


CREATE TABLE wm_task_workflow_state (
    id INT IDENTITY(1,1) PRIMARY KEY,
    task_id BIGINT NOT NULL,
    workflow_id BIGINT NULL,
    state_code NVARCHAR(30) NOT NULL,
    entered_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    entered_by BIGINT NOT NULL,
    CONSTRAINT fk_wm_task_wf_state_task FOREIGN KEY (task_id) REFERENCES wm_task(task_id)
);
GO

CREATE TABLE wm_notification_queue (
    id INT IDENTITY(1,1) PRIMARY KEY,
    task_id BIGINT NOT NULL,
    recipient_emp_id BIGINT NOT NULL,
    channel NVARCHAR(20) NOT NULL DEFAULT 'IN_APP',
    status NVARCHAR(20) NOT NULL DEFAULT 'PENDING',
    payload NVARCHAR(MAX) NULL,
    error_message NVARCHAR(MAX) NULL,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT fk_wm_notification_task FOREIGN KEY (task_id) REFERENCES wm_task(task_id)
);
GO


CREATE TABLE wm_task_status_history (
    status_history_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    task_id BIGINT NOT NULL,
    old_status_code NVARCHAR(30) NOT NULL,
    new_status_code NVARCHAR(30) NOT NULL,
    action_code NVARCHAR(30) NULL,
    remarks NVARCHAR(1000) NULL,
    changed_by BIGINT NOT NULL,
    changed_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT fk_wm_status_history_task FOREIGN KEY (task_id) REFERENCES wm_task(task_id)
);
GO

CREATE TABLE wm_gamification_event (
    id INT IDENTITY(1,1) PRIMARY KEY,
    task_id BIGINT NOT NULL,
    event_code NVARCHAR(50) NOT NULL,
    event_value NVARCHAR(200) NULL,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT fk_wm_gamification_task FOREIGN KEY (task_id) REFERENCES wm_task(task_id)
);
GO


CREATE TABLE wm_task_child_item (
    child_item_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    parent_task_id BIGINT NOT NULL,
    item_type NVARCHAR(20) NOT NULL,
    title NVARCHAR(500) NOT NULL,
    description NVARCHAR(MAX) NULL,
    assignee_emp_id BIGINT NULL,
    due_at DATETIME2 NULL,
    priority_code NVARCHAR(20) NULL,
    estimated_hours DECIMAL(12,2) NULL,
    status_code NVARCHAR(30) NOT NULL DEFAULT 'Open',
    sequence_no INT NULL,
    source_type NVARCHAR(20) NOT NULL DEFAULT 'MANUAL',
    created_by BIGINT NOT NULL,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    updated_by BIGINT NULL,
    updated_on DATETIME2 NULL,
    is_active BIT NOT NULL DEFAULT 1,
    CONSTRAINT fk_wm_task_child_parent FOREIGN KEY (parent_task_id) REFERENCES wm_task(task_id)
);
GO

CREATE TABLE wm_task_child_item_conversion (
    conversion_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    source_child_item_id BIGINT NOT NULL,
    target_task_id BIGINT NULL,
    conversion_type NVARCHAR(30) NOT NULL,
    converted_by BIGINT NOT NULL,
    converted_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT fk_wm_child_conversion_item FOREIGN KEY (source_child_item_id) REFERENCES wm_task_child_item(child_item_id),
    CONSTRAINT fk_wm_child_conversion_target FOREIGN KEY (target_task_id) REFERENCES wm_task(task_id)
);
GO


CREATE TABLE wm_job (
    job_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    job_no NVARCHAR(50) NOT NULL UNIQUE,
    company_id BIGINT NOT NULL,
    branch_id BIGINT NULL,
    department_id BIGINT NULL,
    customer_id BIGINT NOT NULL,
    service_id BIGINT NULL,
    job_name NVARCHAR(255) NOT NULL,
    priority NVARCHAR(20) NULL,
    start_date DATE NULL,
    due_date DATE NULL,
    planned_hours DECIMAL(10,2) NULL,
    planned_minutes INT NULL,
    planned_amount DECIMAL(18,2) NULL,
    is_billable BIT NOT NULL DEFAULT 1,
    manager_id BIGINT NULL,
    execution_status NVARCHAR(20) NOT NULL DEFAULT 'Open',
    billing_status NVARCHAR(20) NOT NULL DEFAULT 'Not Billed',
    remarks NVARCHAR(1000) NULL,
    is_recurring BIT NOT NULL DEFAULT 0,
    created_by BIGINT NOT NULL,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    updated_by BIGINT NULL,
    updated_on DATETIME2 NULL,
    is_active BIT NOT NULL DEFAULT 1
);
GO

CREATE TABLE wm_billing_configuration (
    billing_configuration_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    entity_type NVARCHAR(30) NOT NULL,
    job_id BIGINT NULL,
    task_id BIGINT NULL,
    customer_id BIGINT NOT NULL,
    billable_flag BIT NOT NULL DEFAULT 0,
    billing_model NVARCHAR(30) NOT NULL,
    fixed_billing_amount DECIMAL(14,2) NULL,
    billing_status NVARCHAR(30) NOT NULL DEFAULT 'Not Billable',
    billing_remarks NVARCHAR(1000) NULL,
    created_by BIGINT NOT NULL,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    updated_by BIGINT NULL,
    updated_on DATETIME2 NULL,
    is_active BIT NOT NULL DEFAULT 1
);
GO

CREATE TABLE wm_billing_readiness (
    billing_readiness_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    entity_type NVARCHAR(30) NOT NULL,
    job_id BIGINT NULL,
    task_id BIGINT NULL,
    ready_for_billing_flag BIT NOT NULL DEFAULT 0,
    ready_for_billing_date DATETIME2 NULL,
    included_billable_hours DECIMAL(14,2) NOT NULL DEFAULT 0,
    included_recoverable_expense DECIMAL(14,2) NOT NULL DEFAULT 0,
    billing_status NVARCHAR(30) NOT NULL DEFAULT 'Billable',
    billing_remarks NVARCHAR(1000) NULL,
    marked_by BIGINT NOT NULL,
    marked_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    updated_by BIGINT NULL,
    updated_on DATETIME2 NULL,
    is_active BIT NOT NULL DEFAULT 1
);
GO

CREATE TABLE wm_billing_document_link (
    billing_document_link_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    entity_type NVARCHAR(30) NOT NULL,
    job_id BIGINT NULL,
    task_id BIGINT NULL,
    billing_reference_type NVARCHAR(30) NOT NULL,
    billing_reference_id BIGINT NULL,
    billing_reference_no NVARCHAR(100) NULL,
    billed_amount DECIMAL(14,2) NOT NULL DEFAULT 0,
    billed_date DATE NULL,
    billing_status NVARCHAR(30) NOT NULL,
    included_billable_hours DECIMAL(14,2) NOT NULL DEFAULT 0,
    included_recoverable_expense DECIMAL(14,2) NOT NULL DEFAULT 0,
    billing_remarks NVARCHAR(1000) NULL,
    created_by BIGINT NOT NULL,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    is_active BIT NOT NULL DEFAULT 1
);
GO

CREATE TABLE wm_billing_status_history (
    billing_status_history_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    entity_type NVARCHAR(30) NOT NULL,
    job_id BIGINT NULL,
    task_id BIGINT NULL,
    old_billing_status NVARCHAR(30) NOT NULL,
    new_billing_status NVARCHAR(30) NOT NULL,
    action_code NVARCHAR(30) NOT NULL,
    billing_reference_no NVARCHAR(100) NULL,
    billed_amount DECIMAL(14,2) NULL,
    acted_by BIGINT NOT NULL,
    acted_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    remarks NVARCHAR(1000) NULL
);
GO

CREATE OR ALTER VIEW vw_wm_profitability_base AS
WITH approved_time AS (
    SELECT
        t.job_id,
        t.task_id,
        t.task_participant_id,
        t.emp_id,
        SUM(t.hours) AS approved_hours,
        SUM(t.billable_hours) AS approved_billable_hours,
        SUM((t.hours * ISNULL(e.hourly_cost, 0)) + (t.overtime_hours * ISNULL(e.hourly_cost, 0))) AS labor_cost
    FROM wm_timesheet t
    LEFT JOIN ref_employee e ON e.emp_id = t.emp_id
    WHERE t.approval_status = 'Approved'
      AND t.is_active = 1
    GROUP BY t.job_id, t.task_id, t.task_participant_id, t.emp_id
),
approved_expense AS (
    SELECT
        e.job_id,
        e.task_id,
        e.task_participant_id,
        e.emp_id,
        SUM(e.total_amount) AS non_labor_cost
    FROM wm_expense_claim e
    WHERE e.approval_status IN ('Approved', 'Converted')
      AND e.is_active = 1
    GROUP BY e.job_id, e.task_id, e.task_participant_id, e.emp_id
),
billing_value AS (
    SELECT
        b.job_id,
        b.task_id,
        SUM(b.billed_amount) AS billed_amount
    FROM wm_billing_document_link b
    WHERE b.is_active = 1
      AND b.billing_reference_type LIKE '%_INVOICE'
    GROUP BY b.job_id, b.task_id
)
SELECT
    COALESCE(atm.job_id, aex.job_id, bv.job_id) AS job_id,
    COALESCE(atm.task_id, aex.task_id, bv.task_id) AS task_id,
    COALESCE(atm.task_participant_id, aex.task_participant_id) AS task_participant_id,
    COALESCE(atm.emp_id, aex.emp_id) AS emp_id,
    ISNULL(atm.approved_hours, 0) AS approved_hours,
    ISNULL(atm.approved_billable_hours, 0) AS approved_billable_hours,
    ISNULL(atm.labor_cost, 0) AS labor_cost,
    ISNULL(aex.non_labor_cost, 0) AS non_labor_cost,
    ISNULL(atm.labor_cost, 0) + ISNULL(aex.non_labor_cost, 0) AS total_cost,
    ISNULL(bv.billed_amount, 0) AS billed_amount
FROM approved_time atm
FULL OUTER JOIN approved_expense aex
    ON atm.job_id = aex.job_id
   AND ISNULL(atm.task_id, 0) = ISNULL(aex.task_id, 0)
   AND ISNULL(atm.task_participant_id, 0) = ISNULL(aex.task_participant_id, 0)
   AND ISNULL(atm.emp_id, 0) = ISNULL(aex.emp_id, 0)
FULL OUTER JOIN billing_value bv
    ON COALESCE(atm.job_id, aex.job_id) = bv.job_id
   AND ISNULL(COALESCE(atm.task_id, aex.task_id), 0) = ISNULL(bv.task_id, 0);
GO

CREATE TABLE wm_exception_rule (
    exception_rule_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    exception_type NVARCHAR(50) NOT NULL,
    threshold_value DECIMAL(14,2) NULL,
    threshold_unit NVARCHAR(20) NULL,
    severity_low NVARCHAR(100) NULL,
    severity_medium NVARCHAR(100) NULL,
    severity_high NVARCHAR(100) NULL,
    severity_critical NVARCHAR(100) NULL,
    calendar_aware BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,
    created_by BIGINT NOT NULL,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_exception_instance (
    exception_instance_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    exception_type NVARCHAR(50) NOT NULL,
    severity NVARCHAR(20) NOT NULL,
    entity_type NVARCHAR(30) NOT NULL,
    entity_id BIGINT NOT NULL,
    company_id BIGINT NULL,
    branch_id BIGINT NULL,
    department_id BIGINT NULL,
    customer_id BIGINT NULL,
    job_id BIGINT NULL,
    task_id BIGINT NULL,
    task_participant_id BIGINT NULL,
    emp_id BIGINT NULL,
    manager_id BIGINT NULL,
    planned_start DATETIME2 NULL,
    planned_due DATETIME2 NULL,
    actual_completion DATETIME2 NULL,
    planned_hours DECIMAL(14,2) NULL,
    actual_hours DECIMAL(14,2) NULL,
    billed_amount DECIMAL(14,2) NULL,
    total_cost DECIMAL(14,2) NULL,
    days_delayed INT NULL,
    exception_age_days INT NULL,
    exception_message NVARCHAR(1000) NOT NULL,
    recommended_action NVARCHAR(1000) NULL,
    first_detected_on DATETIME2 NOT NULL,
    last_evaluated_on DATETIME2 NOT NULL,
    is_active BIT NOT NULL DEFAULT 1,
    resolved_on DATETIME2 NULL,
    resolved_by BIGINT NULL
);
GO

CREATE TABLE wm_exception_history (
    exception_history_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    exception_instance_id BIGINT NOT NULL,
    old_is_active BIT NULL,
    new_is_active BIT NULL,
    old_severity NVARCHAR(20) NULL,
    new_severity NVARCHAR(20) NULL,
    action_code NVARCHAR(30) NOT NULL,
    action_note NVARCHAR(1000) NULL,
    acted_by BIGINT NULL,
    acted_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_dashboard (
    dashboard_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(200) NOT NULL,
    user_id BIGINT NOT NULL,
    role_id BIGINT NULL,
    is_default BIT NOT NULL DEFAULT 0,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_dashboard_widget (
    widget_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    dashboard_id BIGINT NOT NULL,
    widget_type NVARCHAR(50) NOT NULL,
    title NVARCHAR(200) NOT NULL,
    position_x INT NOT NULL,
    position_y INT NOT NULL,
    width INT NOT NULL,
    height INT NOT NULL,
    config_json NVARCHAR(MAX) NOT NULL,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_widget_query (
    widget_query_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    widget_id BIGINT NOT NULL,
    data_source NVARCHAR(50) NOT NULL,
    dimension_field NVARCHAR(100) NULL,
    measure_field NVARCHAR(100) NOT NULL,
    aggregation NVARCHAR(20) NOT NULL,
    filter_json NVARCHAR(MAX) NULL,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_report (
    report_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(200) NOT NULL,
    created_by BIGINT NOT NULL,
    is_public BIT NOT NULL DEFAULT 0,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_report_config (
    config_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    report_id BIGINT NOT NULL,
    data_source NVARCHAR(50) NOT NULL,
    columns_json NVARCHAR(MAX) NOT NULL,
    filters_json NVARCHAR(MAX) NULL,
    group_by NVARCHAR(250) NULL,
    aggregation NVARCHAR(250) NULL,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_report_schedule (
    schedule_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    report_id BIGINT NOT NULL,
    frequency NVARCHAR(20) NOT NULL,
    recipients NVARCHAR(MAX) NOT NULL,
    next_run DATETIME2 NOT NULL,
    export_format NVARCHAR(20) NOT NULL DEFAULT 'CSV',
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_api_key (
    api_key_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    client_name NVARCHAR(200) NOT NULL,
    api_key NVARCHAR(500) NOT NULL,
    is_active BIT NOT NULL DEFAULT 1,
    rate_limit_per_minute BIGINT NOT NULL DEFAULT 1000,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_api_log (
    log_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    api_key_id BIGINT NULL,
    endpoint NVARCHAR(200) NOT NULL,
    request NVARCHAR(MAX) NULL,
    response NVARCHAR(MAX) NULL,
    status_code INT NOT NULL,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_webhook (
    webhook_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    event_name NVARCHAR(100) NOT NULL,
    url NVARCHAR(500) NOT NULL,
    secret NVARCHAR(200) NULL,
    is_active BIT NOT NULL DEFAULT 1,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_webhook_log (
    log_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    webhook_id BIGINT NOT NULL,
    event_name NVARCHAR(100) NOT NULL,
    payload NVARCHAR(MAX) NOT NULL,
    status NVARCHAR(50) NOT NULL,
    http_status_code BIGINT NULL,
    error_message NVARCHAR(1000) NULL,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_ai_prediction (
    prediction_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    entity_type NVARCHAR(50) NOT NULL,
    entity_id BIGINT NOT NULL,
    prediction_type NVARCHAR(50) NOT NULL,
    predicted_value DECIMAL(18,2) NOT NULL,
    probability DECIMAL(5,2) NOT NULL,
    model_version NVARCHAR(30) NOT NULL DEFAULT 'rule-v1',
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_ai_recommendation (
    rec_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    entity_id BIGINT NOT NULL,
    recommendation_type NVARCHAR(100) NOT NULL,
    recommendation_text NVARCHAR(MAX) NOT NULL,
    priority INT NOT NULL DEFAULT 3,
    is_applied BIT NOT NULL DEFAULT 0,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_rbac_role (
    role_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(120) NOT NULL,
    description NVARCHAR(MAX) NULL,
    is_system_role BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_rbac_user_role (
    user_role_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    user_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    assigned_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_rbac_module (
    module_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(100) NOT NULL
);
GO

CREATE TABLE wm_rbac_feature (
    feature_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    module_id BIGINT NOT NULL,
    name NVARCHAR(120) NOT NULL
);
GO

CREATE TABLE wm_rbac_action (
    action_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(40) NOT NULL
);
GO

CREATE TABLE wm_rbac_permission (
    permission_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    role_id BIGINT NOT NULL,
    feature_id BIGINT NOT NULL,
    action_id BIGINT NOT NULL,
    is_allowed BIT NOT NULL DEFAULT 1,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_rbac_permission_scope (
    scope_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    permission_id BIGINT NOT NULL,
    company_id BIGINT NULL,
    branch_id BIGINT NULL,
    department_id BIGINT NULL
);
GO

CREATE TABLE wm_rbac_role_inheritance (
    role_inheritance_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    parent_role_id BIGINT NOT NULL,
    child_role_id BIGINT NOT NULL
);
GO

CREATE TABLE wm_rbac_user_permission_override (
    override_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    user_id BIGINT NOT NULL,
    permission_id BIGINT NOT NULL,
    is_allowed BIT NOT NULL
);
GO

CREATE TABLE wm_rbac_approval_limit (
    approval_limit_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    user_id BIGINT NOT NULL,
    module_name NVARCHAR(100) NOT NULL,
    max_amount DECIMAL(18,2) NOT NULL,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_rbac_access_log (
    access_log_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    user_id BIGINT NOT NULL,
    module_name NVARCHAR(100) NOT NULL,
    feature_name NVARCHAR(100) NOT NULL,
    action_name NVARCHAR(100) NOT NULL,
    entity_id BIGINT NULL,
    is_allowed BIT NOT NULL,
    reason NVARCHAR(200) NOT NULL,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_approval_workflow (
    approval_workflow_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    module_name NVARCHAR(100) NOT NULL,
    name NVARCHAR(200) NOT NULL,
    is_active BIT NOT NULL DEFAULT 1,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_approval_step (
    approval_step_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    approval_workflow_id BIGINT NOT NULL,
    step_order BIGINT NOT NULL,
    approver_type NVARCHAR(20) NOT NULL,
    approver_id BIGINT NOT NULL,
    is_parallel BIT NOT NULL DEFAULT 0,
    dependency_step_id BIGINT NULL,
    condition_json NVARCHAR(MAX) NULL
);
GO

CREATE TABLE wm_approval_rule (
    approval_rule_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    approval_workflow_id BIGINT NOT NULL,
    condition_type NVARCHAR(20) NOT NULL,
    operator NVARCHAR(10) NOT NULL,
    value NVARCHAR(200) NOT NULL,
    field_name NVARCHAR(100) NULL
);
GO

CREATE TABLE wm_approval_transaction (
    approval_transaction_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    entity_type NVARCHAR(100) NOT NULL,
    entity_id BIGINT NOT NULL,
    approval_workflow_id BIGINT NOT NULL,
    status NVARCHAR(30) NOT NULL,
    current_step BIGINT NULL,
    snapshot_json NVARCHAR(MAX) NOT NULL,
    accounting_triggered BIT NOT NULL DEFAULT 0,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    completed_on DATETIME2 NULL
);
GO

CREATE TABLE wm_approval_log (
    approval_log_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    approval_transaction_id BIGINT NOT NULL,
    approval_step_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    action NVARCHAR(20) NOT NULL,
    remarks NVARCHAR(MAX) NULL,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_document (
    document_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    file_name NVARCHAR(255) NOT NULL,
    file_url NVARCHAR(MAX) NOT NULL,
    file_type NVARCHAR(100) NOT NULL,
    file_tag NVARCHAR(100) NULL,
    file_hash NVARCHAR(128) NULL,
    uploaded_by BIGINT NOT NULL,
    version BIGINT NOT NULL DEFAULT 1,
    parent_document_id BIGINT NULL,
    is_active BIT NOT NULL DEFAULT 1,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_document_link (
    document_link_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    document_id BIGINT NOT NULL,
    entity_type NVARCHAR(100) NOT NULL,
    entity_id BIGINT NOT NULL,
    is_primary BIT NOT NULL DEFAULT 0,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_document_audit (
    document_audit_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    document_id BIGINT NOT NULL,
    action NVARCHAR(50) NOT NULL,
    user_id BIGINT NOT NULL,
    remarks NVARCHAR(MAX) NULL,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_crm_lead (
    lead_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(200) NOT NULL,
    source NVARCHAR(100) NOT NULL,
    status NVARCHAR(30) NOT NULL DEFAULT 'LEAD',
    assigned_users_json NVARCHAR(MAX) NOT NULL,
    estimated_value BIGINT NULL,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_crm_opportunity (
    opportunity_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    lead_id BIGINT NOT NULL,
    value BIGINT NOT NULL,
    probability BIGINT NOT NULL DEFAULT 30,
    expected_close_date DATETIME2 NULL,
    status NVARCHAR(30) NOT NULL DEFAULT 'OPEN',
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_crm_deal (
    deal_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    opportunity_id BIGINT NOT NULL,
    negotiated_value BIGINT NOT NULL,
    status NVARCHAR(30) NOT NULL DEFAULT 'NEGOTIATION',
    customer_name NVARCHAR(200) NULL,
    invoice_voucher_no NVARCHAR(100) NULL,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_crm_followup (
    followup_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    entity_type NVARCHAR(30) NOT NULL,
    entity_id BIGINT NOT NULL,
    next_followup_date DATETIME2 NOT NULL,
    remarks NVARCHAR(MAX) NULL,
    assigned_to BIGINT NOT NULL,
    status NVARCHAR(20) NOT NULL DEFAULT 'PENDING',
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_customer_lifecycle (
    customer_lifecycle_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    customer_id BIGINT NOT NULL,
    stage NVARCHAR(30) NOT NULL DEFAULT 'NEW',
    last_activity_date DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    churn_risk_score BIGINT NOT NULL DEFAULT 0
);
GO

CREATE TABLE wm_sales_history (
    sales_history_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    sales_date DATETIME2 NOT NULL,
    product_id BIGINT NOT NULL,
    customer_id BIGINT NOT NULL,
    quantity DECIMAL(18,2) NOT NULL,
    revenue DECIMAL(18,2) NOT NULL,
    branch_id BIGINT NOT NULL,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_forecast (
    forecast_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    entity_type NVARCHAR(30) NOT NULL,
    entity_id BIGINT NOT NULL,
    forecast_date DATETIME2 NOT NULL,
    predicted_value DECIMAL(18,2) NOT NULL,
    model_used NVARCHAR(50) NOT NULL,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_customer_score (
    customer_score_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    customer_id BIGINT NOT NULL,
    churn_score DECIMAL(6,4) NOT NULL,
    repeat_probability DECIMAL(6,4) NOT NULL,
    lifetime_value DECIMAL(18,2) NOT NULL,
    updated_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_rule (
    rule_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    module NVARCHAR(100) NOT NULL,
    condition_json NVARCHAR(MAX) NOT NULL,
    action_json NVARCHAR(MAX) NOT NULL,
    priority BIGINT NOT NULL DEFAULT 100,
    status NVARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_rule_execution_log (
    rule_execution_log_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    rule_id BIGINT NOT NULL,
    module NVARCHAR(100) NOT NULL,
    matched NVARCHAR(5) NOT NULL,
    context_json NVARCHAR(MAX) NULL,
    result_json NVARCHAR(MAX) NULL,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_workflow (
    workflow_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(200) NOT NULL,
    module NVARCHAR(100) NOT NULL,
    trigger_event NVARCHAR(100) NOT NULL,
    is_active BIT NOT NULL DEFAULT 1,
    version BIGINT NOT NULL DEFAULT 1,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_workflow_node (
    node_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    workflow_id BIGINT NOT NULL,
    node_type NVARCHAR(30) NOT NULL,
    name NVARCHAR(120) NOT NULL,
    sequence_no BIGINT NOT NULL DEFAULT 1,
    config_json NVARCHAR(MAX) NULL
);
GO

CREATE TABLE wm_workflow_edge (
    edge_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    workflow_id BIGINT NOT NULL,
    from_node_id BIGINT NOT NULL,
    to_node_id BIGINT NOT NULL,
    edge_condition NVARCHAR(50) NULL
);
GO

CREATE TABLE wm_workflow_instance (
    instance_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    workflow_id BIGINT NOT NULL,
    entity_type NVARCHAR(100) NOT NULL,
    entity_id BIGINT NOT NULL,
    status NVARCHAR(30) NOT NULL,
    context_json NVARCHAR(MAX) NULL,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    completed_on DATETIME2 NULL
);
GO

CREATE TABLE wm_workflow_log (
    workflow_log_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    instance_id BIGINT NOT NULL,
    node_id BIGINT NULL,
    action NVARCHAR(100) NOT NULL,
    status NVARCHAR(30) NOT NULL,
    remarks NVARCHAR(MAX) NULL,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_sla_rule (
    sla_rule_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    workflow_id BIGINT NOT NULL,
    time_limit_minutes BIGINT NOT NULL,
    escalation_user_id BIGINT NOT NULL
);
GO

CREATE TABLE wm_sla_log (
    sla_log_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    instance_id BIGINT NOT NULL,
    start_time DATETIME2 NOT NULL,
    breach_time DATETIME2 NOT NULL,
    status NVARCHAR(30) NOT NULL
);
GO

CREATE TABLE wm_workflow_approval (
    approval_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    instance_id BIGINT NOT NULL,
    node_id BIGINT NOT NULL,
    approver_user_id BIGINT NOT NULL,
    status NVARCHAR(30) NOT NULL,
    remarks NVARCHAR(MAX) NULL,
    decided_on DATETIME2 NULL
);
GO

ALTER TABLE wm_workflow_instance ADD workflow_version BIGINT NOT NULL DEFAULT 1;
GO
ALTER TABLE wm_sla_log ADD paused_on DATETIME2 NULL;
GO
ALTER TABLE wm_sla_log ADD total_pause_seconds BIGINT NOT NULL DEFAULT 0;
GO
ALTER TABLE wm_workflow_approval ADD decision_group NVARCHAR(40) NULL;
GO

CREATE TABLE wm_sla_policy (
    sla_policy_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    module NVARCHAR(50) NOT NULL,
    condition_json NVARCHAR(MAX) NULL,
    response_time_minutes BIGINT NOT NULL,
    resolution_time_minutes BIGINT NOT NULL,
    escalation_config_json NVARCHAR(MAX) NOT NULL,
    company_id BIGINT NULL,
    branch_id BIGINT NULL,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_sla_instance (
    sla_instance_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    sla_policy_id BIGINT NOT NULL,
    entity_type NVARCHAR(50) NOT NULL,
    entity_id BIGINT NOT NULL,
    assignee_user_id BIGINT NULL,
    status NVARCHAR(30) NOT NULL,
    start_time DATETIME2 NOT NULL,
    due_time DATETIME2 NOT NULL,
    breach_time DATETIME2 NULL,
    paused_on DATETIME2 NULL,
    total_pause_seconds BIGINT NOT NULL DEFAULT 0,
    timezone NVARCHAR(50) NOT NULL DEFAULT 'UTC',
    context_json NVARCHAR(MAX) NULL
);
GO

CREATE TABLE wm_sla_escalation (
    sla_escalation_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    sla_instance_id BIGINT NOT NULL,
    escalation_level BIGINT NOT NULL,
    escalated_to BIGINT NOT NULL,
    channel NVARCHAR(30) NOT NULL,
    escalated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_business_holiday (
    holiday_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    holiday_date DATE NOT NULL,
    name NVARCHAR(100) NOT NULL,
    company_id BIGINT NULL,
    branch_id BIGINT NULL
);
GO

CREATE TABLE wm_ticket (
    ticket_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    ticket_no NVARCHAR(50) NOT NULL,
    customer_id BIGINT NULL,
    subject NVARCHAR(300) NOT NULL,
    description NVARCHAR(MAX) NOT NULL,
    priority NVARCHAR(20) NOT NULL,
    status NVARCHAR(30) NOT NULL,
    channel NVARCHAR(30) NOT NULL,
    created_by BIGINT NOT NULL,
    company_id BIGINT NULL,
    branch_id BIGINT NULL,
    department_id BIGINT NULL,
    resolution_note NVARCHAR(MAX) NULL,
    created_on DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    updated_on DATETIME2 NULL
);
GO

CREATE TABLE wm_ticket_user (
    ticket_user_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    ticket_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    role NVARCHAR(30) NOT NULL,
    assigned_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_ticket_comment (
    comment_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    ticket_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    message NVARCHAR(MAX) NOT NULL,
    is_internal BIT NOT NULL DEFAULT 0,
    attachments NVARCHAR(MAX) NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_ticket_history (
    history_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    ticket_id BIGINT NOT NULL,
    field NVARCHAR(100) NOT NULL,
    old_value NVARCHAR(MAX) NULL,
    new_value NVARCHAR(MAX) NULL,
    changed_by BIGINT NOT NULL,
    changed_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE task_dependencies (
    id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    task_id UNIQUEIDENTIFIER NOT NULL,
    user_id UNIQUEIDENTIFIER NOT NULL,
    depends_on_user_id UNIQUEIDENTIFIER NOT NULL,
    depends_on_task_id UNIQUEIDENTIFIER NULL,
    dependency_type NVARCHAR(2) NOT NULL,
    status NVARCHAR(20) NOT NULL DEFAULT 'PENDING',
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT chk_task_dependencies_type CHECK (dependency_type IN ('FS','SS','FF')),
    CONSTRAINT chk_task_dependencies_status CHECK (status IN ('PENDING','COMPLETED','APPROVED'))
);
GO

CREATE TABLE audit_logs (
    id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    entity_type NVARCHAR(60) NOT NULL,
    entity_id UNIQUEIDENTIFIER NOT NULL,
    action NVARCHAR(40) NOT NULL,
    old_data NVARCHAR(MAX) NULL,
    new_data NVARCHAR(MAX) NULL,
    user_id UNIQUEIDENTIFIER NOT NULL,
    ip_address NVARCHAR(64) NULL,
    attempt_status NVARCHAR(20) NOT NULL DEFAULT 'AUTHORIZED',
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE sla_tracking (
    id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    ticket_id UNIQUEIDENTIFIER NOT NULL,
    priority NVARCHAR(10) NOT NULL,
    start_time DATETIME2 NOT NULL,
    deadline DATETIME2 NOT NULL,
    status NVARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    escalation_level INT NOT NULL DEFAULT 0,
    paused INT NOT NULL DEFAULT 0,
    pause_reason NVARCHAR(50) NULL,
    timezone NVARCHAR(40) NOT NULL DEFAULT 'UTC',
    CONSTRAINT chk_sla_tracking_priority CHECK (priority IN ('HIGH','LOW','CUSTOM')),
    CONSTRAINT chk_sla_tracking_status CHECK (status IN ('ACTIVE','BREACHED','COMPLETED'))
);
GO

CREATE TABLE wm_ticket_followup (
    followup_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    ticket_id BIGINT NOT NULL,
    action_type NVARCHAR(30) NOT NULL,
    previous_status NVARCHAR(30) NULL,
    new_status NVARCHAR(30) NULL,
    note NVARCHAR(MAX) NOT NULL,
    created_by BIGINT NOT NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    is_customer_visible BIT NOT NULL DEFAULT 1,
    attachment_refs NVARCHAR(MAX) NULL
);
GO

CREATE TABLE wm_ticket_pause_history (
    pause_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    ticket_id BIGINT NOT NULL,
    pause_start DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    pause_end DATETIME2 NULL,
    pause_reason NVARCHAR(120) NOT NULL,
    paused_by BIGINT NOT NULL,
    total_minutes BIGINT NULL,
    remarks NVARCHAR(MAX) NULL
);
GO

CREATE TABLE wm_ticket_escalation_log (
    escalation_log_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    ticket_id BIGINT NOT NULL,
    escalation_level BIGINT NOT NULL,
    trigger_key NVARCHAR(80) NOT NULL,
    recipients NVARCHAR(MAX) NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE wm_task_rollover_history (
    rollover_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    task_id BIGINT NOT NULL,
    previous_due_at DATETIME2 NOT NULL,
    revised_due_at DATETIME2 NOT NULL,
    changed_by BIGINT NOT NULL,
    changed_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    reason NVARCHAR(MAX) NOT NULL,
    approval_required BIT NOT NULL DEFAULT 0,
    approval_status NVARCHAR(20) NOT NULL DEFAULT 'NOT_REQUIRED',
    approved_by BIGINT NULL,
    approval_at DATETIME2 NULL,
    remarks NVARCHAR(MAX) NULL
);
GO

CREATE TABLE wm_ticket_task_link (
    ticket_task_link_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    ticket_id BIGINT NOT NULL,
    task_id BIGINT NOT NULL,
    source NVARCHAR(20) NOT NULL DEFAULT 'TICKET',
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO
