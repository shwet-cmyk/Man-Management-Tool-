-- TEZ Execution System - MSSQL schema baseline

CREATE TABLE Roles (
    RoleID INT IDENTITY(1,1) PRIMARY KEY,
    RoleName NVARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE Users (
    UserID INT IDENTITY(1,1) PRIMARY KEY,
    FirstName NVARCHAR(100) NOT NULL,
    LastName NVARCHAR(100) NULL,
    Email NVARCHAR(200) NOT NULL UNIQUE,
    Mobile NVARCHAR(30) NULL,
    PasswordHash NVARCHAR(255) NOT NULL,
    RoleID INT NOT NULL,
    ReportsTo INT NULL,
    EmployeeGroup NVARCHAR(100) NULL,
    HourlyCost DECIMAL(12,2) NOT NULL DEFAULT 0,
    ApprovalRequired BIT NOT NULL DEFAULT 0,
    CompanyID INT NULL,
    BranchID INT NULL,
    DepartmentID INT NULL,
    IsActive BIT NOT NULL DEFAULT 1,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_Users_Roles FOREIGN KEY (RoleID) REFERENCES Roles(RoleID)
);

CREATE TABLE Projects (
    ProjectID INT IDENTITY(1,1) PRIMARY KEY,
    Name NVARCHAR(200) NOT NULL,
    ClientName NVARCHAR(200) NOT NULL,
    ManagerID INT NOT NULL,
    StartDate DATE NOT NULL,
    EndDate DATE NOT NULL,
    Status NVARCHAR(50) NOT NULL,
    EstimatedCost DECIMAL(14,2) NOT NULL DEFAULT 0,
    EstimatedHours DECIMAL(10,2) NOT NULL DEFAULT 0,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_Projects_Manager FOREIGN KEY (ManagerID) REFERENCES Users(UserID)
);

CREATE TABLE Tasks (
    TaskID INT IDENTITY(1,1) PRIMARY KEY,
    ProjectID INT NOT NULL,
    Name NVARCHAR(200) NOT NULL,
    Priority NVARCHAR(20) NOT NULL,
    StartDate DATE NULL,
    EndDate DATE NULL,
    Status NVARCHAR(50) NOT NULL,
    EstimatedHours DECIMAL(10,2) NOT NULL DEFAULT 0,
    EstimatedCost DECIMAL(14,2) NOT NULL DEFAULT 0,
    Billable BIT NOT NULL DEFAULT 1,
    BillingAmount DECIMAL(14,2) NOT NULL DEFAULT 0,
    CreatedBy INT NOT NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_Tasks_Project FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID),
    CONSTRAINT FK_Tasks_User FOREIGN KEY (CreatedBy) REFERENCES Users(UserID)
);

CREATE TABLE Jobs (
    JobID INT IDENTITY(1,1) PRIMARY KEY,
    TaskID INT NOT NULL,
    AssignedUserID INT NOT NULL,
    StartDate DATE NULL,
    EndDate DATE NULL,
    Status NVARCHAR(50) NOT NULL,
    SLADeadline DATETIME2 NULL,
    CONSTRAINT FK_Jobs_Task FOREIGN KEY (TaskID) REFERENCES Tasks(TaskID),
    CONSTRAINT FK_Jobs_User FOREIGN KEY (AssignedUserID) REFERENCES Users(UserID)
);

CREATE TABLE Timesheets (
    TimesheetID INT IDENTITY(1,1) PRIMARY KEY,
    UserID INT NOT NULL,
    TaskID INT NULL,
    JobID INT NULL,
    [Date] DATE NOT NULL,
    StartTime TIME NULL,
    EndTime TIME NULL,
    Duration DECIMAL(10,2) NOT NULL DEFAULT 0,
    Remarks NVARCHAR(500) NULL,
    IsOverlap BIT NOT NULL DEFAULT 0,
    CONSTRAINT FK_Timesheets_User FOREIGN KEY (UserID) REFERENCES Users(UserID),
    CONSTRAINT FK_Timesheets_Task FOREIGN KEY (TaskID) REFERENCES Tasks(TaskID),
    CONSTRAINT FK_Timesheets_Job FOREIGN KEY (JobID) REFERENCES Jobs(JobID)
);

CREATE TABLE Approvals (
    ApprovalID INT IDENTITY(1,1) PRIMARY KEY,
    Module NVARCHAR(100) NOT NULL,
    ReferenceID INT NOT NULL,
    [Level] TINYINT NOT NULL,
    ApproverID INT NOT NULL,
    Status NVARCHAR(30) NOT NULL,
    Remarks NVARCHAR(500) NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    ActionAt DATETIME2 NULL,
    CONSTRAINT FK_Approvals_Approver FOREIGN KEY (ApproverID) REFERENCES Users(UserID)
);

CREATE TABLE Notifications (
    NotificationID INT IDENTITY(1,1) PRIMARY KEY,
    UserID INT NOT NULL,
    Module NVARCHAR(100) NOT NULL,
    ReferenceID INT NOT NULL,
    Channel NVARCHAR(30) NOT NULL,
    TemplateName NVARCHAR(100) NULL,
    Message NVARCHAR(MAX) NOT NULL,
    SentAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    DeliveredAt DATETIME2 NULL,
    ReadAt DATETIME2 NULL,
    Status NVARCHAR(30) NOT NULL,
    CONSTRAINT FK_Notifications_User FOREIGN KEY (UserID) REFERENCES Users(UserID)
);

CREATE TABLE AuditLogs (
    AuditID INT IDENTITY(1,1) PRIMARY KEY,
    UserID INT NULL,
    Module NVARCHAR(100) NOT NULL,
    ReferenceID NVARCHAR(100) NOT NULL,
    ActionType NVARCHAR(100) NOT NULL,
    FieldName NVARCHAR(100) NULL,
    OldValue NVARCHAR(MAX) NULL,
    NewValue NVARCHAR(MAX) NULL,
    [Timestamp] DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE TABLE HelpContent (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    ScreenKey NVARCHAR(150) NOT NULL UNIQUE,
    Title NVARCHAR(200) NOT NULL,
    Description NVARCHAR(MAX) NOT NULL,
    WhenToUse NVARCHAR(MAX) NOT NULL,
    StepsJson NVARCHAR(MAX) NOT NULL,
    RulesJson NVARCHAR(MAX) NOT NULL,
    ErrorsJson NVARCHAR(MAX) NOT NULL,
    TipsJson NVARCHAR(MAX) NOT NULL,
    ModuleName NVARCHAR(120) NOT NULL,
    SubmoduleName NVARCHAR(120) NOT NULL,
    RoutePath NVARCHAR(200) NOT NULL,
    IsActive BIT NOT NULL DEFAULT 1,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE TABLE ChatbotSessions (
    SessionID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    UserID INT NULL,
    RoleName NVARCHAR(80) NULL,
    CurrentRoutePath NVARCHAR(260) NOT NULL,
    CurrentScreenKey NVARCHAR(180) NULL,
    CurrentModuleName NVARCHAR(120) NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    UpdatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_ChatbotSessions_User FOREIGN KEY (UserID) REFERENCES Users(UserID)
);

CREATE TABLE ChatbotMessages (
    MessageID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    SessionID UNIQUEIDENTIFIER NOT NULL,
    SenderRole NVARCHAR(20) NOT NULL,
    MessageText NVARCHAR(MAX) NOT NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_ChatbotMessages_Session FOREIGN KEY (SessionID) REFERENCES ChatbotSessions(SessionID)
);

CREATE INDEX IX_ChatbotSessions_UserID ON ChatbotSessions(UserID);
CREATE INDEX IX_ChatbotMessages_SessionCreatedAt ON ChatbotMessages(SessionID, CreatedAt);

CREATE TABLE chatbot_quick_prompts (
    prompt_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    module_name NVARCHAR(100) NOT NULL,
    screen_key NVARCHAR(200) NULL,
    role_id BIGINT NULL,
    priority_level NVARCHAR(20) NULL,
    condition_type NVARCHAR(50) NULL,
    condition_query NVARCHAR(MAX) NULL,
    prompt_text_en NVARCHAR(500) NOT NULL,
    prompt_text_hi NVARCHAR(500) NULL,
    prompt_text_gu NVARCHAR(500) NULL,
    prompt_text_mr NVARCHAR(500) NULL,
    intent_code NVARCHAR(100) NOT NULL,
    action_type NVARCHAR(50) NOT NULL,
    route_path NVARCHAR(300) NULL,
    display_order INT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,
    created_at DATETIME2 DEFAULT SYSDATETIME()
);

CREATE INDEX IX_chatbot_quick_prompts_module_screen_role ON chatbot_quick_prompts(module_name, screen_key, role_id, is_active);

CREATE TABLE device_master (
    device_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    device_uuid NVARCHAR(200) NOT NULL UNIQUE,
    device_name NVARCHAR(200) NOT NULL,
    device_type NVARCHAR(100) NULL,
    os_name NVARCHAR(100) NULL,
    os_version NVARCHAR(100) NULL,
    employee_user_id BIGINT NOT NULL,
    company_id BIGINT NOT NULL,
    branch_id BIGINT NULL,
    department_id BIGINT NULL,
    agent_version NVARCHAR(50) NULL,
    registration_status NVARCHAR(30) NOT NULL DEFAULT 'ACTIVE',
    last_heartbeat_at DATETIME2 NULL,
    registered_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    is_active BIT NOT NULL DEFAULT 1,
    created_by BIGINT NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    updated_by BIGINT NULL,
    updated_at DATETIME2 NULL
);

CREATE TABLE agent_registration (
    registration_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    device_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    registration_token NVARCHAR(500) NOT NULL,
    token_expires_at DATETIME2 NULL,
    agent_status NVARCHAR(30) NOT NULL DEFAULT 'ACTIVE',
    last_sync_at DATETIME2 NULL,
    last_error NVARCHAR(MAX) NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    updated_at DATETIME2 NULL
);

CREATE TABLE productivity_policy (
    policy_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    policy_name NVARCHAR(200) NOT NULL,
    scope_type NVARCHAR(30) NOT NULL,
    scope_reference_id BIGINT NULL,
    idle_threshold_minutes INT NOT NULL,
    productive_target_hours DECIMAL(10,2) NOT NULL,
    borderline_lower_hours DECIMAL(10,2) NOT NULL,
    underproductive_lower_hours DECIMAL(10,2) NOT NULL,
    screenshot_capture_enabled BIT NOT NULL DEFAULT 0,
    screenshot_frequency_minutes INT NULL,
    raw_retention_days INT NOT NULL DEFAULT 90,
    screenshot_retention_days INT NOT NULL DEFAULT 90,
    summary_retention_type NVARCHAR(30) NOT NULL DEFAULT 'PERPETUAL',
    warn_on_blacklisted_url BIT NOT NULL DEFAULT 1,
    block_blacklisted_url BIT NOT NULL DEFAULT 0,
    effective_from DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    effective_to DATETIME2 NULL,
    is_active BIT NOT NULL DEFAULT 1,
    created_by BIGINT NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    updated_by BIGINT NULL,
    updated_at DATETIME2 NULL
);

CREATE TABLE app_classification_master (
    app_classification_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    app_name NVARCHAR(200) NOT NULL,
    executable_name NVARCHAR(200) NULL,
    app_category NVARCHAR(100) NULL,
    classification_type NVARCHAR(30) NOT NULL,
    notes NVARCHAR(MAX) NULL,
    is_active BIT NOT NULL DEFAULT 1,
    created_by BIGINT NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    updated_by BIGINT NULL,
    updated_at DATETIME2 NULL
);

CREATE TABLE url_classification_master (
    url_classification_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    domain_name NVARCHAR(300) NOT NULL,
    url_pattern NVARCHAR(500) NULL,
    browser_scope NVARCHAR(100) NULL,
    classification_type NVARCHAR(30) NOT NULL,
    notes NVARCHAR(MAX) NULL,
    is_active BIT NOT NULL DEFAULT 1,
    created_by BIGINT NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    updated_by BIGINT NULL,
    updated_at DATETIME2 NULL
);

CREATE TABLE raw_activity_log (
    activity_log_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    device_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    event_type NVARCHAR(50) NOT NULL,
    event_timestamp DATETIME2 NOT NULL,
    active_app_name NVARCHAR(300) NULL,
    active_executable NVARCHAR(300) NULL,
    active_window_title NVARCHAR(MAX) NULL,
    active_domain NVARCHAR(500) NULL,
    active_url NVARCHAR(MAX) NULL,
    classification_type NVARCHAR(30) NULL,
    is_idle BIT NOT NULL DEFAULT 0,
    is_locked BIT NOT NULL DEFAULT 0,
    is_hibernated BIT NOT NULL DEFAULT 0,
    input_source NVARCHAR(50) NULL,
    duration_seconds INT NULL,
    metadata_json NVARCHAR(MAX) NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);

CREATE TABLE daily_productivity_summary (
    daily_summary_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    summary_date DATE NOT NULL,
    user_id BIGINT NOT NULL,
    device_id BIGINT NULL,
    company_id BIGINT NOT NULL,
    branch_id BIGINT NULL,
    department_id BIGINT NULL,
    present_minutes INT NOT NULL DEFAULT 0,
    active_minutes INT NOT NULL DEFAULT 0,
    productive_minutes INT NOT NULL DEFAULT 0,
    neutral_minutes INT NOT NULL DEFAULT 0,
    unproductive_minutes INT NOT NULL DEFAULT 0,
    idle_minutes INT NOT NULL DEFAULT 0,
    locked_minutes INT NOT NULL DEFAULT 0,
    hibernate_minutes INT NOT NULL DEFAULT 0,
    offline_minutes INT NOT NULL DEFAULT 0,
    shutdown_count INT NOT NULL DEFAULT 0,
    reboot_count INT NOT NULL DEFAULT 0,
    productivity_status NVARCHAR(30) NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    updated_at DATETIME2 NULL
);

CREATE TABLE monthly_productivity_summary (
    monthly_summary_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    summary_month INT NOT NULL,
    summary_year INT NOT NULL,
    user_id BIGINT NOT NULL,
    company_id BIGINT NOT NULL,
    branch_id BIGINT NULL,
    department_id BIGINT NULL,
    present_minutes INT NOT NULL DEFAULT 0,
    active_minutes INT NOT NULL DEFAULT 0,
    productive_minutes INT NOT NULL DEFAULT 0,
    neutral_minutes INT NOT NULL DEFAULT 0,
    unproductive_minutes INT NOT NULL DEFAULT 0,
    idle_minutes INT NOT NULL DEFAULT 0,
    locked_minutes INT NOT NULL DEFAULT 0,
    hibernate_minutes INT NOT NULL DEFAULT 0,
    offline_minutes INT NOT NULL DEFAULT 0,
    shutdown_count INT NOT NULL DEFAULT 0,
    reboot_count INT NOT NULL DEFAULT 0,
    productivity_status NVARCHAR(30) NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    updated_at DATETIME2 NULL
);

CREATE TABLE policy_breach_log (
    breach_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    user_id BIGINT NOT NULL,
    device_id BIGINT NOT NULL,
    breach_timestamp DATETIME2 NOT NULL,
    breach_type NVARCHAR(50) NOT NULL,
    app_name NVARCHAR(300) NULL,
    domain_name NVARCHAR(500) NULL,
    url_value NVARCHAR(MAX) NULL,
    policy_id BIGINT NULL,
    action_taken NVARCHAR(100) NULL,
    screenshot_captured BIT NOT NULL DEFAULT 0,
    metadata_json NVARCHAR(MAX) NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);

CREATE TABLE screenshot_evidence (
    screenshot_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    user_id BIGINT NOT NULL,
    device_id BIGINT NOT NULL,
    captured_at DATETIME2 NOT NULL,
    trigger_type NVARCHAR(50) NOT NULL,
    storage_path NVARCHAR(MAX) NOT NULL,
    file_name NVARCHAR(500) NULL,
    linked_breach_id BIGINT NULL,
    expires_at DATETIME2 NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);

CREATE TABLE underproductive_flag_log (
    flag_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    user_id BIGINT NOT NULL,
    summary_date DATE NOT NULL,
    productive_minutes INT NOT NULL,
    target_minutes INT NOT NULL,
    productivity_status NVARCHAR(30) NOT NULL,
    manager_notified BIT NOT NULL DEFAULT 0,
    employee_notified BIT NOT NULL DEFAULT 0,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);

CREATE TABLE productivity_audit_log (
    audit_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    user_id BIGINT NULL,
    action_type NVARCHAR(100) NOT NULL,
    target_entity NVARCHAR(100) NOT NULL,
    target_id BIGINT NULL,
    field_name NVARCHAR(200) NULL,
    old_value NVARCHAR(MAX) NULL,
    new_value NVARCHAR(MAX) NULL,
    remarks NVARCHAR(MAX) NULL,
    action_timestamp DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);

CREATE INDEX IX_raw_activity_log_user_date ON raw_activity_log (user_id, event_timestamp);
CREATE INDEX IX_daily_productivity_summary_user_date ON daily_productivity_summary (user_id, summary_date);
CREATE INDEX IX_policy_breach_log_user_date ON policy_breach_log (user_id, breach_timestamp);
CREATE INDEX IX_device_master_employee ON device_master (employee_user_id, is_active);
