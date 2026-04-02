import { useEffect, useMemo, useState } from 'react'
import { NavLink, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom'

const ROLE = 'Admin'
const PRODUCT_NAME = 'TEZ Execution System'
const COMPANY_NAME = 'TEZ Global'
const FY = '2026-27'

const SCREEN_KEY_BY_PATH = {
  '/dashboard': 'dashboard_main',
  '/projects': 'project_list',
  '/tasks': 'task_list',
  '/jobs': 'job_list',
  '/timesheets': 'timesheet_list',
  '/approvals': 'approval_inbox',
  '/audit': 'audit_log_list',
  '/interconnect': 'interconnect_grid',
  '/reports': 'report_run',
  '/analytics': 'analytics_prebuilt',
  '/chat': 'chat_home',
  '/notifications': 'notification_center',
}

const menuTree = [
  { key: 'dashboard', label: 'Dashboard', roles: ['Admin', 'Manager', 'User'], children: [{ label: 'Main', path: '/dashboard' }] },
  { key: 'projects', label: 'Projects', roles: ['Admin', 'Manager'], children: [{ label: 'Project List', path: '/projects' }, { label: 'Tasks', path: '/tasks' }] },
  { key: 'execution', label: 'Execution', roles: ['Admin', 'Manager'], children: [{ label: 'Jobs', path: '/jobs' }, { label: 'Timesheets', path: '/timesheets' }, { label: 'Approvals', path: '/approvals' }] },
  { key: 'collaboration', label: 'Collaboration', roles: ['Admin', 'Manager', 'User'], children: [{ label: 'Chat', path: '/chat' }, { label: 'Notifications', path: '/notifications' }] },
  { key: 'governance', label: 'Governance', roles: ['Admin'], children: [{ label: 'Interconnect', path: '/interconnect' }, { label: 'Reports', path: '/reports' }, { label: 'Analytics', path: '/analytics' }, { label: 'Audit', path: '/audit' }] },
]

const defaultPanel = { open: false, mode: null, module: null, data: null }

const sampleData = {
  projects: [{ id: 1, name: 'SAP Rollout', client: 'Acme', status: 'ACTIVE', sla: 'OK', progress: 45 }],
  tasks: [{ id: 11, task: 'Design API', project: 'SAP', phase: 'Build', status: 'IN_PROGRESS', dependency: 'T-8', sla: 'OK', progress: 65 }],
  jobs: [{ id: 101, job: 'Backend Task', assignee: 'Aarav', status: 'IN_PROGRESS', sla: 'OK', spent: 8 }],
  timesheets: [{ id: 201, date: '2026-04-01', employee: 'Aarav', task: 'Design API', job: 'Backend Task', time: '09:00-11:00', overlap: true }],
  approvals: [{ id: 301, module: 'TIMESHEET', reference: 'TS-88', level: 'L1', status: 'PENDING', pendingWith: 'Manager' }],
  audit: [{ id: 401, user: 'Admin', action: 'UPDATE', module: 'TASK', field: 'status', timestamp: '2026-04-02T09:00:00Z' }],
}

function App() {
  const [expanded, setExpanded] = useState(['projects'])
  const [selection, setSelection] = useState([])
  const [panel, setPanel] = useState(defaultPanel)
  const [bulkMode, setBulkMode] = useState(false)
  const [filters, setFilters] = useState({})
  const [data, setData] = useState(sampleData)
  const [chat, setChat] = useState([{ id: 1, user: 'system', text: 'Welcome to execution chat' }])
  const [helpOpen, setHelpOpen] = useState(false)
  const [helpLoading, setHelpLoading] = useState(false)
  const [helpContent, setHelpContent] = useState(null)

  const location = useLocation()
  const navigate = useNavigate()
  const visibleMenu = useMemo(() => menuTree.filter((item) => item.roles.includes(ROLE)), [])

  useEffect(() => {
    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8080/ws'
    const ws = new WebSocket(`${wsUrl}/web-user`)
    ws.onmessage = (evt) => {
      try {
        const parsed = JSON.parse(evt.data)
        if (parsed.type === 'CHAT') setChat((curr) => [...curr, { id: Date.now(), user: parsed.from || 'peer', text: parsed.payload?.message || '' }])
      } catch {
        // ignore malformed data
      }
    }
    return () => ws.close()
  }, [])

  const openHelp = async () => {
    const key = SCREEN_KEY_BY_PATH[location.pathname] || 'dashboard_main'
    setHelpOpen(true)
    setHelpLoading(true)
    const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api/v1'
    try {
      const resp = await fetch(`${apiBase}/help/${key}`)
      const data = await resp.json()
      setHelpContent(data)
    } catch {
      setHelpContent({ title: 'Help unavailable', description: 'Help content not yet configured for this screen', steps_json: [], rules_json: [], errors_json: [], tips_json: [] })
    } finally {
      setHelpLoading(false)
    }
  }

  return (
    <div style={{ display: 'grid', gridTemplateRows: '64px 1fr', height: '100vh', fontFamily: 'Inter, sans-serif' }}>
      <GlobalHeader onHelp={openHelp} onQuickAdd={(module) => { navigate(`/${module}`); setPanel({ open: true, mode: 'create', module: `/${module}`, data: null }) }} onOpenNotifications={() => navigate('/notifications')} onHome={() => navigate('/dashboard')} />

      <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr auto' }}>
        <Sidebar visibleMenu={visibleMenu} expanded={expanded} setExpanded={setExpanded} />

        <div style={{ display: 'grid', gridTemplateRows: 'auto 1fr auto', background: '#f1f5f9' }}>
          <ActionBar onAdd={() => setPanel({ open: true, mode: 'create', module: location.pathname, data: null })} onExport={() => alert('Export API called')} onFilter={() => alert('Filter panel (module specific)')} onBulk={() => setBulkMode((v) => !v)} onAnalytics={() => setPanel({ open: true, mode: 'analytics', module: location.pathname, data: null })} bulkMode={bulkMode} />
          <div style={{ padding: 12, overflow: 'auto' }}>
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" />} />
              <Route path="/dashboard" element={<SimplePage title="Dashboard" />} />
              <Route path="/projects" element={<GridModule title="Projects" rows={data.projects} columns={projectColumns(setPanel)} selection={selection} setSelection={setSelection} />} />
              <Route path="/tasks" element={<GridModule title="Tasks" rows={data.tasks} columns={taskColumns(setPanel)} selection={selection} setSelection={setSelection} />} />
              <Route path="/jobs" element={<GridModule title="Jobs" rows={data.jobs} columns={jobColumns(setPanel)} selection={selection} setSelection={setSelection} />} />
              <Route path="/timesheets" element={<GridModule title="Timesheets" rows={data.timesheets} columns={timesheetColumns(setPanel)} selection={selection} setSelection={setSelection} />} />
              <Route path="/approvals" element={<GridModule title="Approvals" rows={data.approvals} columns={approvalColumns(setPanel)} selection={selection} setSelection={setSelection} />} />
              <Route path="/audit" element={<GridModule title="Audit Logs" rows={data.audit} columns={auditColumns(setPanel)} selection={selection} setSelection={setSelection} />} />
              <Route path="/chat" element={<ChatModule chat={chat} setChat={setChat} />} />
              <Route path="*" element={<SimplePage title={location.pathname} />} />
            </Routes>
          </div>
          <BottomPanel />
        </div>

        <ContextPanel panel={panel} close={() => setPanel(defaultPanel)} />
      </div>

      {helpOpen && <HelpPanel loading={helpLoading} content={helpContent} onClose={() => setHelpOpen(false)} />}
    </div>
  )
}

function GlobalHeader({ onHelp, onQuickAdd, onOpenNotifications, onHome }) {
  const [quickOpen, setQuickOpen] = useState(false)
  const [profileOpen, setProfileOpen] = useState(false)
  return (
    <header style={{ background: '#0f172a', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 16px', borderBottom: '1px solid #1e293b' }}>
      <button onClick={onHome} style={{ background: 'none', border: 'none', color: '#fff', fontWeight: 700, cursor: 'pointer' }}>{PRODUCT_NAME} ({COMPANY_NAME} : {FY})</button>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, position: 'relative' }}>
        <div style={{ position: 'relative' }}>
          <button onClick={() => setQuickOpen((v) => !v)}>＋</button>
          {quickOpen && <Dropdown items={[['Create Task', () => onQuickAdd('tasks')], ['Create Job', () => onQuickAdd('jobs')], ['Create Ticket', () => onQuickAdd('tickets')], ['Create Project', () => onQuickAdd('projects')]]} onClose={() => setQuickOpen(false)} />}
        </div>
        <button onClick={onHelp}>?</button>
        <button onClick={onOpenNotifications}>🔔<span style={{ color: '#f59e0b', marginLeft: 4 }}>3</span></button>
        <div style={{ position: 'relative' }}>
          <button onClick={() => setProfileOpen((v) => !v)}>Admin ▾</button>
          {profileOpen && <Dropdown items={[['My Profile', () => {}], ['Settings', () => {}], ['Security Settings', () => {}], ['Logout', () => {}]]} onClose={() => setProfileOpen(false)} />}
        </div>
      </div>
    </header>
  )
}

function HelpPanel({ loading, content, onClose }) {
  return (
    <aside style={{ position: 'fixed', right: 0, top: 64, width: 420, bottom: 0, background: '#fff', borderLeft: '1px solid #cbd5e1', padding: 16, overflow: 'auto', zIndex: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}><h3>Contextual Help</h3><button onClick={onClose}>✕</button></div>
      {loading ? <p>Loading help...</p> : (
        <>
          <h4>{content?.title}</h4>
          <p><strong>Purpose:</strong> {content?.description}</p>
          <p><strong>When to use:</strong> {content?.when_to_use}</p>
          <Section title="Step-by-step" items={content?.steps_json || []} />
          <Section title="Key rules / validations" items={content?.rules_json || []} />
          <Section title="Common mistakes" items={content?.errors_json || []} />
          <Section title="Tips / best practices" items={content?.tips_json || []} />
        </>
      )}
    </aside>
  )
}

function Section({ title, items }) { return <div><h5>{title}</h5>{items.length ? <ol>{items.map((i) => <li key={i}>{i}</li>)}</ol> : <p>—</p>}</div> }
function Dropdown({ items, onClose }) { return <div style={{ position: 'absolute', right: 0, top: '110%', background: '#fff', color: '#0f172a', border: '1px solid #cbd5e1', borderRadius: 6, minWidth: 180, zIndex: 30 }}>{items.map(([label, fn]) => <button key={label} onClick={() => { fn(); onClose() }} style={{ display: 'block', width: '100%', textAlign: 'left', padding: 8, background: 'white', border: 'none' }}>{label}</button>)}</div> }

function Sidebar({ visibleMenu, expanded, setExpanded }) {
  return <aside style={{ background: '#0b1220', color: '#fff', padding: 12 }}>{visibleMenu.map((menu) => { const open = expanded.includes(menu.key); return <div key={menu.key}><button onClick={() => setExpanded((c) => open ? c.filter((x) => x !== menu.key) : [...c, menu.key])} style={{ width: '100%', textAlign: 'left' }}>{open ? '▾' : '▸'} {menu.label}</button>{open && menu.children.map((child) => <NavLink key={child.path} to={child.path} style={({ isActive }) => ({ display: 'block', color: '#fff', padding: '6px 10px', background: isActive ? '#1d4ed8' : 'transparent' })}>{child.label}</NavLink>)}</div> })}</aside>
}

function ActionBar({ onAdd, onExport, onFilter, onBulk, onAnalytics, bulkMode }) { return <div style={{ display: 'flex', gap: 8, padding: 8, background: '#fff', borderBottom: '1px solid #e2e8f0' }}><button onClick={onAdd}>Add</button><button onClick={onExport}>Export</button><button onClick={onFilter}>Filter</button><button onClick={onBulk}>{bulkMode ? 'Bulk ON' : 'Bulk Action'}</button><button style={{ marginLeft: 'auto' }} onClick={onAnalytics}>Analytics</button></div> }

function GridModule({ title, rows, columns, selection, setSelection }) { return <><h3>{title}</h3><DataGrid rows={rows} columns={columns} selection={selection} setSelection={setSelection} /></> }
function DataGrid({ rows, columns, selection, setSelection }) { return <table width="100%" cellPadding="8" style={{ background: '#fff' }}><thead><tr><th><input type="checkbox" onChange={(e) => setSelection(e.target.checked ? rows.map((r) => r.id) : [])} /></th>{columns.map((c) => <th key={c.key}>{c.label}</th>)}<th>Action</th></tr></thead><tbody>{rows.map((r) => <tr key={r.id} onDoubleClick={() => columns[0].onView?.(r)}><td><input type="checkbox" checked={selection.includes(r.id)} onChange={() => setSelection((c) => c.includes(r.id) ? c.filter((x) => x !== r.id) : [...c, r.id])} /></td>{columns.map((c) => <td key={c.key}>{c.render ? c.render(r[c.key], r) : r[c.key]}</td>)}<td><select onChange={(e) => e.target.value && ({ view: columns[0].onView, edit: columns[0].onEdit }[e.target.value]?.(r))}><option value="">Select</option><option value="view">View</option><option value="edit">Edit</option></select></td></tr>)}</tbody></table> }

function ContextPanel({ panel, close }) { if (!panel.open) return <aside style={{ width: 0 }} />; return <aside style={{ width: 340, background: '#fff', borderLeft: '1px solid #cbd5e1', padding: 12 }}><h3>Context Panel</h3><h4>{panel.mode} - {panel.module}</h4><button onClick={close}>Close</button></aside> }
function BottomPanel() { return <div style={{ background: '#fff', borderTop: '1px solid #e2e8f0', padding: 8 }}>Bottom Panel: Comments | Audit | Notes | Attachments</div> }
function SimplePage({ title }) { return <div style={{ background: '#fff', padding: 16 }}>{title}</div> }
function ChatModule({ chat, setChat }) { const [msg, setMsg] = useState(''); return <div style={{ background: '#fff', padding: 12 }}><h3>Chat</h3>{chat.map((m) => <div key={m.id}><b>{m.user}:</b> {m.text}</div>)}<input value={msg} onChange={(e) => setMsg(e.target.value)} /><button onClick={() => { if (!msg.trim()) return; setChat((c) => [...c, { id: Date.now(), user: 'me', text: msg }]); setMsg('') }}>Send</button></div> }

const projectColumns = (setPanel) => [{ key: 'name', label: 'Project', onView: (r) => setPanel({ open: true, mode: 'view', module: '/projects', data: r }), onEdit: (r) => setPanel({ open: true, mode: 'edit', module: '/projects', data: r }) }, { key: 'client', label: 'Client' }, { key: 'status', label: 'Status' }, { key: 'sla', label: 'SLA' }, { key: 'progress', label: 'Progress' }]
const taskColumns = (setPanel) => [{ key: 'task', label: 'Task', onView: (r) => setPanel({ open: true, mode: 'view', module: '/tasks', data: r }), onEdit: (r) => setPanel({ open: true, mode: 'edit', module: '/tasks', data: r }) }, { key: 'project', label: 'Project' }, { key: 'phase', label: 'Phase' }, { key: 'status', label: 'Status' }, { key: 'dependency', label: 'Dependency' }, { key: 'sla', label: 'SLA' }]
const jobColumns = (setPanel) => [{ key: 'job', label: 'Job', onView: (r) => setPanel({ open: true, mode: 'view', module: '/jobs', data: r }), onEdit: (r) => setPanel({ open: true, mode: 'edit', module: '/jobs', data: r }) }, { key: 'assignee', label: 'Assignee' }, { key: 'status', label: 'Status' }, { key: 'sla', label: 'SLA' }, { key: 'spent', label: 'Spent' }]
const timesheetColumns = (setPanel) => [{ key: 'date', label: 'Date', onView: (r) => setPanel({ open: true, mode: 'view', module: '/timesheets', data: r }), onEdit: (r) => setPanel({ open: true, mode: 'edit', module: '/timesheets', data: r }) }, { key: 'employee', label: 'Employee' }, { key: 'task', label: 'Task' }, { key: 'job', label: 'Job' }, { key: 'time', label: 'Time' }, { key: 'overlap', label: 'Overlap', render: (v) => v ? '⚠️' : 'OK' }]
const approvalColumns = (setPanel) => [{ key: 'module', label: 'Module', onView: (r) => setPanel({ open: true, mode: 'view', module: '/approvals', data: r }), onEdit: (r) => setPanel({ open: true, mode: 'edit', module: '/approvals', data: r }) }, { key: 'reference', label: 'Reference' }, { key: 'level', label: 'Level' }, { key: 'status', label: 'Status' }, { key: 'pendingWith', label: 'Pending With' }]
const auditColumns = (setPanel) => [{ key: 'user', label: 'User', onView: (r) => setPanel({ open: true, mode: 'view', module: '/audit', data: r }), onEdit: (r) => setPanel({ open: true, mode: 'edit', module: '/audit', data: r }) }, { key: 'action', label: 'Action' }, { key: 'module', label: 'Module' }, { key: 'field', label: 'Field' }, { key: 'timestamp', label: 'Timestamp' }]

export default App
