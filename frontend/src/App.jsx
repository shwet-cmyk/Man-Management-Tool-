import { useEffect, useMemo, useState } from 'react'
import { NavLink, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom'

const ROLE = 'Admin'

const menuTree = [
  {
    key: 'dashboard',
    label: 'Dashboard',
    roles: ['Admin', 'Manager', 'User'],
    children: [
      { label: 'Role Dashboard', path: '/dashboard' },
      { label: 'Custom Dashboard', path: '/dashboard/custom' },
    ],
  },
  {
    key: 'projects',
    label: 'Projects',
    roles: ['Admin', 'Manager'],
    children: [
      { label: 'Project List', path: '/projects' },
      { label: 'Project Dashboard', path: '/projects/dashboard' },
      { label: 'Phases', path: '/projects/phases' },
      { label: 'Tasks', path: '/tasks' },
    ],
  },
  {
    key: 'masters',
    label: 'Masters',
    roles: ['Admin'],
    children: [
      { label: 'RBAC', path: '/masters/rbac' },
      { label: 'Users', path: '/masters/users' },
      { label: 'Company', path: '/masters/company' },
    ],
  },
  { key: 'interconnect', label: 'Interconnect', roles: ['Admin', 'Manager'], children: [{ label: 'Mappings', path: '/interconnect' }] },
  { key: 'reports', label: 'Reports', roles: ['Admin', 'Manager'], children: [{ label: 'Reports', path: '/reports' }] },
  { key: 'analytics', label: 'Analytics', roles: ['Admin', 'Manager'], children: [{ label: 'Analytics', path: '/analytics' }] },
  { key: 'jobs', label: 'Jobs', roles: ['Admin', 'Manager'], children: [{ label: 'Job List', path: '/jobs' }] },
  { key: 'timesheets', label: 'Timesheets', roles: ['Admin', 'Manager', 'User'], children: [{ label: 'Timesheet List', path: '/timesheets' }] },
  { key: 'approvals', label: 'Approvals', roles: ['Admin', 'Manager'], children: [{ label: 'Approval Queue', path: '/approvals' }] },
  { key: 'audit', label: 'Audit', roles: ['Admin'], children: [{ label: 'Audit Logs', path: '/audit' }] },
  { key: 'chat', label: 'Chat', roles: ['Admin', 'Manager', 'User'], children: [{ label: 'Channels', path: '/chat' }] },
]

const projectRows = [
  { id: 1, name: 'SAP Rollout', client: 'Acme', status: 'ACTIVE', sla: 'OK', progress: 45 },
  { id: 2, name: 'Revamp', client: 'Globex', status: 'DELAYED', sla: 'BREACH', progress: 72 },
]
const taskRows = [
  { id: 11, task: 'Design API', project: 'SAP Rollout', phase: 'Build', status: 'IN_PROGRESS', dependency: 'T-8', sla: 'OK', progress: 65 },
  { id: 12, task: 'UAT', project: 'Revamp', phase: 'QA', status: 'BLOCKED', dependency: 'T-11', sla: 'BREACH', progress: 20 },
]
const jobRows = [
  { id: 101, job: 'Backend Task', assignee: 'Aarav', status: 'IN_PROGRESS', sla: 'OK', spent: 8 },
  { id: 102, job: 'Migration', assignee: 'Nina', status: 'PENDING', sla: 'BREACH', spent: 11 },
]
const timesheetRows = [
  { id: 201, date: '2026-04-01', employee: 'Aarav', task: 'Design API', job: 'Backend Task', time: '09:00-11:00', overlap: false },
  { id: 202, date: '2026-04-01', employee: 'Aarav', task: 'UAT', job: 'Migration', time: '10:30-12:00', overlap: true },
]
const approvalRows = [
  { id: 301, module: 'TIMESHEET', reference: 'TS-88', level: 'L1', status: 'PENDING', pendingWith: 'Manager' },
]
const auditRows = [
  { id: 401, user: 'Admin', action: 'UPDATE', module: 'TASK', field: 'status', timestamp: '2026-04-02T09:00:00Z' },
]

const defaultPanel = { open: false, mode: null, module: null, data: null }

const statusColor = (status) => ({ ACTIVE: '#16a34a', DELAYED: '#dc2626', IN_PROGRESS: '#2563eb', BLOCKED: '#b45309', PENDING: '#475569' }[status] || '#334155')

function App() {
  const [expanded, setExpanded] = useState(['projects'])
  const [selection, setSelection] = useState([])
  const [filters, setFilters] = useState({})
  const [panel, setPanel] = useState(defaultPanel)
  const [bulkMode, setBulkMode] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [data, setData] = useState({ projects: projectRows, tasks: taskRows, jobs: jobRows, timesheets: timesheetRows, approvals: approvalRows, audit: auditRows })
  const [chat, setChat] = useState([{ id: 1, user: 'system', text: 'Welcome to execution chat' }])
  const [typing, setTyping] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()

  const visibleMenu = useMemo(() => menuTree.filter((item) => item.roles.includes(ROLE)), [])

  useEffect(() => {
    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8080/ws'
    const ws = new WebSocket(`${wsUrl}/web-user`)
    ws.onmessage = (evt) => {
      try {
        const parsed = JSON.parse(evt.data)
        if (parsed.type === 'CHAT') setChat((curr) => [...curr, { id: Date.now(), user: parsed.from || 'peer', text: parsed.payload?.message || '' }])
      } catch {
        // ignore malformed messages
      }
    }
    return () => ws.close()
  }, [])

  const openPanel = (mode, module, row = null) => setPanel({ open: true, mode, module, data: row })

  const onAdd = () => openPanel('create', location.pathname)
  const onExport = () => alert(`Export API triggered for ${location.pathname}`)
  const onFilter = () => setModalOpen(true)
  const onBulk = () => setBulkMode((v) => !v)
  const onAnalytics = () => openPanel('analytics', location.pathname)

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr auto', height: '100vh', fontFamily: 'Inter, sans-serif' }}>
      <Sidebar visibleMenu={visibleMenu} expanded={expanded} setExpanded={setExpanded} />
      <div style={{ display: 'grid', gridTemplateRows: 'auto 1fr auto', background: '#f1f5f9' }}>
        <ActionBar onAdd={onAdd} onExport={onExport} onFilter={onFilter} onBulk={onBulk} onAnalytics={onAnalytics} bulkMode={bulkMode} />
        <div style={{ padding: 12, overflow: 'auto' }}>
          <Routes>
            <Route path="/" element={<Navigate to="/projects" />} />
            <Route path="/projects" element={<GridModule title="Projects" module="projects" rows={data.projects} columns={projectColumns(openPanel)} selection={selection} setSelection={setSelection} />} />
            <Route path="/tasks" element={<GridModule title="Tasks" module="tasks" rows={data.tasks} columns={taskColumns(openPanel)} selection={selection} setSelection={setSelection} />} />
            <Route path="/jobs" element={<GridModule title="Jobs" module="jobs" rows={data.jobs} columns={jobColumns(openPanel)} selection={selection} setSelection={setSelection} />} />
            <Route path="/timesheets" element={<GridModule title="Timesheets" module="timesheets" rows={data.timesheets} columns={timesheetColumns(openPanel)} selection={selection} setSelection={setSelection} />} />
            <Route path="/approvals" element={<GridModule title="Approvals" module="approvals" rows={data.approvals} columns={approvalColumns(openPanel)} selection={selection} setSelection={setSelection} />} />
            <Route path="/audit" element={<GridModule title="Audit Logs" module="audit" rows={data.audit} columns={auditColumns(openPanel)} selection={selection} setSelection={setSelection} />} />
            <Route path="/chat" element={<ChatModule chat={chat} setChat={setChat} setTyping={setTyping} typing={typing} />} />
            <Route path="*" element={<SimplePage title={location.pathname.replace('/', '') || 'Module'} />} />
          </Routes>
        </div>
        <BottomPanel />
      </div>

      <ContextPanel panel={panel} close={() => setPanel(defaultPanel)} onSave={(payload) => handleSave(payload, panel, setData, setPanel)} />

      {modalOpen && <FilterModal filters={filters} setFilters={setFilters} onClose={() => setModalOpen(false)} />}
    </div>
  )
}

function Sidebar({ visibleMenu, expanded, setExpanded }) {
  return (
    <aside style={{ background: '#0f172a', color: 'white', padding: 12, overflow: 'auto' }}>
      <h3>TEZ OS</h3>
      {visibleMenu.map((menu) => {
        const isOpen = expanded.includes(menu.key)
        return (
          <div key={menu.key} style={{ marginBottom: 8 }}>
            <button onClick={() => setExpanded((curr) => (isOpen ? curr.filter((x) => x !== menu.key) : [...curr, menu.key]))} style={sidebarBtn}>{isOpen ? '▾' : '▸'} {menu.label}</button>
            {isOpen && menu.children.map((child) => (
              <NavLink key={child.path} to={child.path} style={({ isActive }) => ({ ...subLink, background: isActive ? '#1d4ed8' : 'transparent' })}>{child.label}</NavLink>
            ))}
          </div>
        )
      })}
    </aside>
  )
}

function ActionBar({ onAdd, onExport, onFilter, onBulk, onAnalytics, bulkMode }) {
  return (
    <div style={{ display: 'flex', gap: 8, padding: 12, borderBottom: '1px solid #cbd5e1', background: '#fff' }}>
      <button onClick={onAdd}>Add</button>
      <button onClick={onExport}>Export</button>
      <button onClick={onFilter}>Filter</button>
      <button onClick={onBulk}>{bulkMode ? 'Bulk ON' : 'Bulk Action'}</button>
      <button style={{ marginLeft: 'auto' }} onClick={onAnalytics}>Analytics</button>
    </div>
  )
}

function GridModule({ title, module, rows, columns, selection, setSelection }) {
  return <><h3>{title}</h3><DataGrid rows={rows} columns={columns} module={module} selection={selection} setSelection={setSelection} /></>
}

function DataGrid({ rows, columns, selection, setSelection, module }) {
  const [sort, setSort] = useState({ key: columns[0].key, dir: 'asc' })
  const [page, setPage] = useState(1)
  const pageSize = 5

  const sorted = useMemo(() => [...rows].sort((a, b) => `${a[sort.key]}`.localeCompare(`${b[sort.key]}`) * (sort.dir === 'asc' ? 1 : -1)), [rows, sort])
  const paged = sorted.slice((page - 1) * pageSize, page * pageSize)
  const toggleOne = (id) => setSelection((curr) => (curr.includes(id) ? curr.filter((x) => x !== id) : [...curr, id]))

  return (
    <div style={{ background: '#fff', border: '1px solid #cbd5e1', borderRadius: 8 }}>
      <table width="100%" cellPadding="8" style={{ borderCollapse: 'collapse' }}>
        <thead><tr>
          <th><input type="checkbox" onChange={(e) => setSelection(e.target.checked ? rows.map((r) => r.id) : [])} /></th>
          {columns.map((c) => <th key={c.key} onClick={() => setSort((s) => ({ key: c.key, dir: s.dir === 'asc' ? 'desc' : 'asc' }))} style={{ cursor: 'pointer', textAlign: 'left' }}>{c.label}</th>)}
          <th>Actions</th>
        </tr></thead>
        <tbody>
          {paged.map((r) => (
            <tr key={r.id} onDoubleClick={() => columns[0].onView?.(r)} style={{ borderTop: '1px solid #e2e8f0', cursor: 'pointer' }}>
              <td><input type="checkbox" checked={selection.includes(r.id)} onChange={() => toggleOne(r.id)} /></td>
              {columns.map((c) => <td key={c.key} onClick={() => c.onView?.(r)}>{c.render ? c.render(r[c.key], r) : r[c.key]}</td>)}
              <td>
                <select onChange={(e) => e.target.value && ({ view: columns[0].onView, edit: columns[0].onEdit, delete: columns[0].onDelete }[e.target.value]?.(r))}>
                  <option value="">Select</option>
                  <option value="view">View</option><option value="edit">Edit</option><option value="delete">Delete</option>
                </select>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div style={{ display: 'flex', justifyContent: 'space-between', padding: 8 }}>
        <span>{module}: {rows.length} rows</span>
        <div><button onClick={() => setPage((p) => Math.max(1, p - 1))}>Prev</button> <span>{page}</span> <button onClick={() => setPage((p) => (p * pageSize < rows.length ? p + 1 : p))}>Next</button></div>
      </div>
    </div>
  )
}

function ContextPanel({ panel, close, onSave }) {
  const [form, setForm] = useState({})
  const [error, setError] = useState('')
  useEffect(() => { setForm(panel.data || {}) }, [panel])
  if (!panel.open) return <aside style={{ width: 0 }} />
  const header = `${panel.mode?.toUpperCase()} • ${panel.module}`.replace('/', '')
  const save = () => {
    if (panel.mode === 'create' && !form.name && !form.task && !form.job) return setError('Name/Task/Job is required')
    setError('')
    onSave(form)
  }

  return (
    <aside style={{ width: 360, borderLeft: '1px solid #cbd5e1', background: '#fff', padding: 12 }}>
      <h3>Context Panel</h3>
      <h4>{header}</h4>
      <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
        {['Details', 'Jobs', 'Dependencies', 'Timesheets', 'Audit', 'Notes'].map((t) => <button key={t}>{t}</button>)}
      </div>
      {panel.mode === 'analytics' ? <p>Analytics panel opened for current module.</p> : (
        <>
          <label>Title</label>
          <input value={form.name || form.task || form.job || ''} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} style={{ width: '100%' }} />
          <label>Status</label>
          <input value={form.status || ''} onChange={(e) => setForm((f) => ({ ...f, status: e.target.value }))} style={{ width: '100%' }} />
          {error && <p style={{ color: 'crimson' }}>{error}</p>}
          <button onClick={save}>Save</button> <button onClick={close}>Close</button>
        </>
      )}
    </aside>
  )
}

function FilterModal({ filters, setFilters, onClose }) {
  const keys = ['company', 'branch', 'department', 'employee', 'client', 'project', 'dateFrom', 'dateTo', 'priority']
  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,.25)', display: 'grid', placeItems: 'center' }}>
      <div style={{ background: '#fff', padding: 16, borderRadius: 8, width: 400 }}>
        <h3>Filter Engine</h3>
        {keys.map((k) => <div key={k}><label>{k}</label><input value={filters[k] || ''} onChange={(e) => setFilters((f) => ({ ...f, [k]: e.target.value }))} style={{ width: '100%', marginBottom: 6 }} /></div>)}
        <button onClick={onClose}>Apply</button>
      </div>
    </div>
  )
}

function BottomPanel() {
  return <div style={{ background: '#fff', padding: 8, borderTop: '1px solid #cbd5e1' }}>Bottom Panel Tabs: Comments | Audit | Notes | Attachments</div>
}

function SimplePage({ title }) { return <div style={{ background: '#fff', border: '1px solid #cbd5e1', padding: 16 }}>{title} module route is active.</div> }

function ChatModule({ chat, setChat, typing, setTyping }) {
  const [msg, setMsg] = useState('')
  const send = () => {
    if (!msg.trim()) return
    setChat((curr) => [...curr, { id: Date.now(), user: 'me', text: msg }])
    setMsg('')
    setTyping(false)
  }
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '220px 1fr 280px', height: '100%', gap: 8 }}>
      <div style={box}><h4>Channels</h4><div># general</div><div># projects</div></div>
      <div style={box}><h4>Chat</h4>{chat.map((m) => <div key={m.id}><strong>{m.user}:</strong> {m.text}</div>)}<input value={msg} onChange={(e) => { setMsg(e.target.value); setTyping(true) }} style={{ width: '100%' }} /><button onClick={send}>Send</button>{typing && <small>typing...</small>}</div>
      <div style={box}><h4>Thread / Info</h4><p>Read receipts and thread details.</p></div>
    </div>
  )
}

function handleSave(payload, panel, setData, setPanel) {
  const module = panel.module?.split('/')[1]
  if (!module || !['projects', 'tasks', 'jobs', 'timesheets', 'approvals', 'audit'].includes(module)) return setPanel(defaultPanel)
  setData((curr) => {
    const rows = [...curr[module]]
    if (panel.mode === 'edit' && panel.data?.id) return { ...curr, [module]: rows.map((r) => (r.id === panel.data.id ? { ...r, ...payload } : r)) }
    if (panel.mode === 'create') return { ...curr, [module]: [...rows, { id: Date.now(), ...payload }] }
    return curr
  })
  setPanel(defaultPanel)
}

const sidebarBtn = { width: '100%', textAlign: 'left', border: 'none', background: '#1e293b', color: 'white', padding: 8, borderRadius: 6 }
const subLink = { display: 'block', color: 'white', textDecoration: 'none', padding: '6px 10px', marginTop: 4, borderRadius: 6, fontSize: 14 }
const box = { background: '#fff', border: '1px solid #cbd5e1', padding: 8, borderRadius: 8 }

const projectColumns = (open) => [
  { key: 'name', label: 'Project', onView: (r) => open('view', '/projects', r), onEdit: (r) => open('edit', '/projects', r), onDelete: () => alert('Delete project') },
  { key: 'client', label: 'Client' },
  { key: 'status', label: 'Status', render: (v, r) => <span style={{ color: statusColor(v), textDecoration: 'underline' }} onClick={() => open('view', '/projects/status-history', r)}>{v}</span> },
  { key: 'sla', label: 'SLA', render: (v) => <span style={{ color: v === 'BREACH' ? '#dc2626' : '#16a34a' }}>{v}</span> },
  { key: 'progress', label: 'Progress' },
]
const taskColumns = (open) => [
  { key: 'task', label: 'Task Name', onView: (r) => open('view', '/tasks', r), onEdit: (r) => open('edit', '/tasks', r), onDelete: () => alert('Delete task') },
  { key: 'project', label: 'Project' }, { key: 'phase', label: 'Phase' },
  { key: 'status', label: 'Status', render: (v) => <span style={{ color: statusColor(v) }}>{v}</span> },
  { key: 'dependency', label: 'Dependency', render: (v) => <button onClick={() => alert(`Dependency graph: ${v}`)}>🔗 {v}</button> },
  { key: 'sla', label: 'SLA', render: (v) => <span style={{ color: v === 'BREACH' ? '#dc2626' : '#16a34a' }}>{v}</span> },
  { key: 'progress', label: 'Progress' },
]
const jobColumns = (open) => [
  { key: 'job', label: 'Job Name', onView: (r) => open('view', '/jobs', r), onEdit: (r) => open('edit', '/jobs', r), onDelete: () => alert('Delete job') },
  { key: 'assignee', label: 'Assigned User' }, { key: 'status', label: 'Status', render: (v) => <span style={{ color: statusColor(v) }}>{v}</span> },
  { key: 'sla', label: 'SLA', render: (v) => <span style={{ color: v === 'BREACH' ? '#dc2626' : '#16a34a' }}>{v}</span> }, { key: 'spent', label: 'Time Spent' },
]
const timesheetColumns = (open) => [
  { key: 'date', label: 'Date', onView: (r) => open('view', '/timesheets', r), onEdit: (r) => open('edit', '/timesheets', r), onDelete: () => alert('Delete timesheet') },
  { key: 'employee', label: 'Employee' }, { key: 'task', label: 'Task' }, { key: 'job', label: 'Job' }, { key: 'time', label: 'Time' },
  { key: 'overlap', label: 'Overlap', render: (v, r) => v ? <button onClick={() => alert(`Conflicts for ${r.employee}`)}>⚠️ Overlap</button> : 'OK' },
]
const approvalColumns = (open) => [
  { key: 'module', label: 'Module', onView: (r) => open('view', '/approvals', r), onEdit: (r) => open('edit', '/approvals', r), onDelete: () => alert('Delete approval') },
  { key: 'reference', label: 'Reference' }, { key: 'level', label: 'Level' }, { key: 'status', label: 'Status' }, { key: 'pendingWith', label: 'Pending With' },
]
const auditColumns = (open) => [
  { key: 'user', label: 'User', onView: (r) => open('view', '/audit', r), onEdit: (r) => open('edit', '/audit', r), onDelete: () => alert('Delete audit') },
  { key: 'action', label: 'Action' }, { key: 'module', label: 'Module' }, { key: 'field', label: 'Field Changed' }, { key: 'timestamp', label: 'Timestamp' },
]

export default App
