
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
