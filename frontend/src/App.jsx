import { Link, Route, Routes } from 'react-router-dom'

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

const navItems = [
  { path: '/', label: 'Dashboard' },
  { path: '/departments', label: 'Departments' },
  { path: '/employees', label: 'Employees' },
  { path: '/attendance', label: 'Attendance' },
  { path: '/master-sync', label: 'Employee Sync' },
  { path: '/tasks/create', label: 'Create Task' },
  { path: '/tasks/assign', label: 'Task Participants' },
  { path: '/tasks/status', label: 'Task Status' },
  { path: '/tasks/child-items', label: 'Child Items' },
  { path: '/jobs/create', label: 'Create Job' },
]

function App() {
  return (
    <div className="container">
      <header>
        <h1>IESL Man Management Tool</h1>
        <nav>
          {navItems.map((item) => (
            <Link key={item.path} to={item.path} className="nav-link">
              {item.label}
            </Link>
          ))}
        </nav>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<HomePage />} />
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
  )
}

export default App
