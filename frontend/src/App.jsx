import { useMemo, useState } from 'react'
import { NavLink, Route, Routes, useLocation, useNavigate } from 'react-router-dom'

import HomePage from './pages/HomePage'
import DepartmentsPage from './modules/departments/DepartmentsPage'
import EmployeesPage from './modules/employees/EmployeesPage'
import AttendancePage from './modules/attendance/AttendancePage'
import EmployeeSyncPage from './modules/masterSync/EmployeeSyncPage'
import CreateTaskPage from './modules/tasks/CreateTaskPage'
import TaskAssignmentPage from './modules/tasks/TaskAssignmentPage'
import TaskStatusPage from './modules/tasks/TaskStatusPage'
import TaskChildItemsPage from './modules/tasks/TaskChildItemsPage'
import CreateJobPage from './modules/jobs/CreateJobPage'
import WorkWorkspacePage from './modules/workspace/WorkWorkspacePage'
import MyWorkPage from './modules/workspace/MyWorkPage'
import ProjectCollabPage from './modules/workspace/ProjectCollabPage'
import StrategicOpsPage from './modules/workspace/StrategicOpsPage'
import { seedWorkItems } from './modules/workspace/workData'

const navSections = [
  {
    title: 'Execution',
    items: [
      { path: '/', label: 'Workstream' },
      { path: '/my-work', label: 'My Work' },
      { path: '/projects/collaboration', label: 'Project Collaboration' },
      { path: '/strategic-ops', label: 'Strategic Ops' },
      { path: '/dashboard', label: 'Analytics Dashboard' },
    ],
  },
  {
    title: 'Master Data',
    items: [
      { path: '/departments', label: 'Departments' },
      { path: '/employees', label: 'Employees' },
      { path: '/attendance', label: 'Attendance' },
      { path: '/master-sync', label: 'Employee Sync' },
    ],
  },
  {
    title: 'Task Operations',
    items: [
      { path: '/tasks/create', label: 'Create Task' },
      { path: '/tasks/assign', label: 'Task Participants' },
      { path: '/tasks/status', label: 'Task Status' },
      { path: '/tasks/child-items', label: 'Child Items' },
      { path: '/jobs/create', label: 'Create Job' },
    ],
  },
]

const pageTitles = {
  '/': 'Workstream Execution Center',
  '/my-work': 'My Work',
  '/dashboard': 'Dashboard',
  '/projects/collaboration': 'Project Collaboration',
  '/strategic-ops': 'Strategic Operations',
  '/departments': 'Departments',
  '/employees': 'Employees',
  '/attendance': 'Attendance',
  '/master-sync': 'Employee Sync',
  '/tasks/create': 'Create Task',
  '/tasks/assign': 'Task Participants',
  '/tasks/status': 'Task Status',
  '/tasks/child-items': 'Task Child Items',
  '/jobs/create': 'Create Job',
}

function App() {
  const location = useLocation()
  const navigate = useNavigate()
  const [workItems, setWorkItems] = useState(seedWorkItems)
  const headerTitle = pageTitles[location.pathname] || 'Operations Workspace'
  const selectedSummary = useMemo(
    () => ({
      open: workItems.filter((item) => item.status !== 'Done').length,
      blocked: workItems.filter((item) => item.status === 'Blocked').length,
      dueSoon: workItems.filter((item) => item.dueDate <= '2026-03-31' && item.status !== 'Done').length,
    }),
    [workItems],
  )

  const updateWorkItem = (itemId, patch) => {
    setWorkItems((curr) => curr.map((item) => (item.id === itemId ? { ...item, ...patch } : item)))
  }

  const createWorkItem = (quickAdd) => {
    const nextNum = 1000 + workItems.length + 1
    const type = quickAdd.title?.toLowerCase().includes('job') ? 'Job' : 'Task'
    const id = `${type === 'Job' ? 'JOB' : 'TASK'}-${nextNum}`
    setWorkItems((curr) => [
      ...curr,
      {
        id,
        type,
        title: quickAdd.title,
        status: 'Backlog',
        assignee: quickAdd.assignee || 'Unassigned',
        manager: 'Unassigned',
        client: 'Internal',
        priority: 'Medium',
        dueDate: quickAdd.dueDate || '2026-04-04',
        startDate: '2026-03-28',
        plannedHours: 4,
        actualHours: 0,
        freeCapacityHours: 4,
        dependency: '-',
        billable: false,
        rollover: 0,
        critical: false,
        section: 'New Intake',
        comments: ['Created from quick add'],
      },
    ])
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">IESL Man Management</div>
        <nav className="sidebar-nav" aria-label="Primary navigation">
          {navSections.map((section) => (
            <div key={section.title} className="nav-section">
              <p className="nav-section-title">{section.title}</p>
              {section.items.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) => `nav-link ${isActive ? 'nav-link-active' : ''}`}
                  end={item.path === '/'}
                >
                  {item.label}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
      </aside>

      <div className="main-shell">
        <header className="top-header">
          <div>
            <h1>{headerTitle}</h1>
            <p>Structured execution for teams, tasks, and delivery workflows.</p>
          </div>
          <div className="header-actions">
            <div className="summary-pills">
              <span>Open {selectedSummary.open}</span>
              <span>Blocked {selectedSummary.blocked}</span>
              <span>Due soon {selectedSummary.dueSoon}</span>
            </div>
            <button className="btn-text" type="button">Notifications</button>
            <div className="user-pill">OPS Admin</div>
          </div>
        </header>

        <main className="content-area">
          <Routes>
            <Route
              path="/"
              element={<WorkWorkspacePage workItems={workItems} onUpdateItem={updateWorkItem} onCreateItem={createWorkItem} />}
            />
            <Route
              path="/my-work"
              element={<MyWorkPage workItems={workItems} onOpenItem={() => navigate('/')} />}
            />
            <Route path="/projects/collaboration" element={<ProjectCollabPage workItems={workItems} />} />
            <Route path="/strategic-ops" element={<StrategicOpsPage workItems={workItems} />} />
            <Route path="/dashboard" element={<HomePage />} />
            <Route path="/departments" element={<DepartmentsPage />} />
            <Route path="/employees" element={<EmployeesPage />} />
            <Route path="/attendance" element={<AttendancePage />} />
            <Route path="/master-sync" element={<EmployeeSyncPage />} />
            <Route path="/tasks/create" element={<CreateTaskPage />} />
            <Route path="/tasks/assign" element={<TaskAssignmentPage />} />
            <Route path="/tasks/status" element={<TaskStatusPage />} />
            <Route path="/tasks/child-items" element={<TaskChildItemsPage />} />
            <Route path="/jobs/create" element={<CreateJobPage />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}

export default App
