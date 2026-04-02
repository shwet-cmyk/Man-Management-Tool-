import { useEffect, useMemo, useState } from 'react'
import { NavLink, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { useActionSoundEngine } from './mascot/ActionSoundEngine'
import { MascotAvatar } from './mascot/MascotAvatar'
import { MascotEmptyState } from './mascot/MascotEmptyState'
import { MascotErrorState } from './mascot/MascotErrorState'
import { MascotLoadingPanel } from './mascot/MascotLoadingPanel'
import { MascotStateRenderer } from './mascot/MascotStateRenderer'
import { MascotSuccessToast } from './mascot/MascotSuccessToast'
import { useMotionPreferences } from './mascot/MotionPreferenceProvider'

const ROLE = 'Admin'
const USER_ID = 1
const LANGUAGE = 'en'
const PRODUCT_NAME = 'TEZ Execution System'
const COMPANY_NAME = 'TEZ Global'
const FY = '2026-27'

const menuTree = [
  { key: 'dashboard', label: 'Dashboard', roles: ['Admin', 'Manager', 'User'], children: [{ label: 'Main', path: '/dashboard' }] },
  { key: 'projects', label: 'Projects', roles: ['Admin', 'Manager'], children: [{ label: 'Project List', path: '/projects' }, { label: 'Tasks', path: '/tasks' }] },
  { key: 'execution', label: 'Execution', roles: ['Admin', 'Manager'], children: [{ label: 'Jobs', path: '/jobs' }, { label: 'Timesheets', path: '/timesheets' }, { label: 'Approvals', path: '/approvals' }] },
  { key: 'collaboration', label: 'Collaboration', roles: ['Admin', 'Manager', 'User'], children: [{ label: 'Notifications', path: '/notifications' }] },
  { key: 'governance', label: 'Governance', roles: ['Admin'], children: [{ label: 'Interconnect', path: '/interconnect' }, { label: 'Reports', path: '/reports' }, { label: 'Analytics', path: '/analytics' }, { label: 'Compliance Matrix', path: '/governance/compliance' }] },
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
  const [data, setData] = useState(sampleData)
  const [helpOpen, setHelpOpen] = useState(false)
  const [helpLoading, setHelpLoading] = useState(false)
  const [helpContent, setHelpContent] = useState(null)
  const [helpCache, setHelpCache] = useState({})
  const [settingsOpen, setSettingsOpen] = useState(false)

  const location = useLocation()
  const navigate = useNavigate()
  const visibleMenu = useMemo(() => menuTree.filter((item) => item.roles.includes(ROLE)), [])
  const currentModuleKey = location.pathname.replace('/', '') || 'dashboard'

  const handleExport = () => {
    const rows = data[currentModuleKey]
    if (!rows?.length) {
      setPanel({ open: true, mode: 'export', module: location.pathname, data: { message: 'No records available to export.' } })
      return
    }
    const headers = Object.keys(rows[0])
    const csv = [
      headers.join(','),
      ...rows.map((row) => headers.map((h) => JSON.stringify(row[h] ?? '')).join(',')),
    ].join('\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `${currentModuleKey || 'module'}_export.csv`
    link.click()
    URL.revokeObjectURL(link.href)
    setPanel({ open: true, mode: 'export', module: location.pathname, data: { message: `Exported ${rows.length} records.` } })
  }

  const handleFilter = () => {
    setPanel({ open: true, mode: 'filter', module: location.pathname, data: { filters: ['status', 'owner', 'date_range'] } })
  }

  const openHelp = async () => {
    setHelpOpen(true)
    const cacheKey = location.pathname
    if (helpCache[cacheKey]) {
      setHelpContent(helpCache[cacheKey])
      return
    }
    setHelpLoading(true)
    const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api/v1'
    try {
      const resolver = await fetch(`${apiBase}/help/route/resolve?path=${encodeURIComponent(location.pathname)}`)
      let responseData
      if (resolver.ok) {
        responseData = await resolver.json()
      } else {
        responseData = await (await fetch(`${apiBase}/help/dashboard_main`)).json()
      }
      setHelpContent(responseData)
      setHelpCache((curr) => ({ ...curr, [cacheKey]: responseData }))
    } catch {
      setHelpContent({ title: 'Help unavailable', description: 'Help content not yet configured for this screen', steps_json: [], rules_json: [], errors_json: [], tips_json: [] })
    } finally {
      setHelpLoading(false)
    }
  }

  return (
    <div style={{ display: 'grid', gridTemplateRows: '64px 1fr', height: '100vh', fontFamily: 'Inter, sans-serif' }}>
      <GlobalHeader onHelp={openHelp} onOpenSettings={() => setSettingsOpen(true)} onQuickAdd={(module) => { navigate(`/${module}`); setPanel({ open: true, mode: 'create', module: `/${module}`, data: null }) }} onOpenNotifications={() => navigate('/notifications')} onHome={() => navigate('/dashboard')} />

      <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr auto' }}>
        <Sidebar visibleMenu={visibleMenu} expanded={expanded} setExpanded={setExpanded} />

        <div style={{ display: 'grid', gridTemplateRows: 'auto 1fr auto', background: '#f1f5f9' }}>
          <ActionBar onAdd={() => setPanel({ open: true, mode: 'create', module: location.pathname, data: null })} onExport={handleExport} onFilter={handleFilter} onBulk={() => setBulkMode((v) => !v)} onAnalytics={() => setPanel({ open: true, mode: 'analytics', module: location.pathname, data: null })} bulkMode={bulkMode} />
          <div style={{ padding: 12, overflow: 'auto' }}>
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" />} />
              <Route path="/dashboard" element={<SimplePage title="Dashboard" />} />
              <Route path="/projects" element={<GridModule title="Projects" rows={data.projects} columns={projectColumns(setPanel)} selection={selection} setSelection={setSelection} />} />
              <Route path="/tasks" element={<GridModule title="Tasks" rows={data.tasks} columns={taskColumns(setPanel)} selection={selection} setSelection={setSelection} />} />
              <Route path="/jobs" element={<GridModule title="Jobs" rows={data.jobs} columns={jobColumns(setPanel)} selection={selection} setSelection={setSelection} />} />
              <Route path="/timesheets" element={<GridModule title="Timesheets" rows={data.timesheets} columns={timesheetColumns(setPanel)} selection={selection} setSelection={setSelection} />} />
              <Route path="/approvals" element={<GridModule title="Approvals" rows={data.approvals} columns={approvalColumns(setPanel)} selection={selection} setSelection={setSelection} />} />
              <Route path="/governance/compliance" element={<ModuleCompliancePage />} />
              <Route path="/settings/profile/new-features" element={<NewFeaturesPage />} />
              <Route path="*" element={<SimplePage title={location.pathname} />} />
            </Routes>
          </div>
          <BottomPanel />
        </div>

        <ContextPanel panel={panel} close={() => setPanel(defaultPanel)} />
      </div>

      <FloatingAssistant currentPath={location.pathname} />
      {helpOpen && <HelpPanel loading={helpLoading} content={helpContent} onClose={() => setHelpOpen(false)} />}
      {settingsOpen && <AssistantSettingsModal onClose={() => setSettingsOpen(false)} />}
    </div>
  )
}

function FloatingAssistant({ currentPath }) {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([])
  const [draft, setDraft] = useState('')
  const [sessionId, setSessionId] = useState(null)
  const [loading, setLoading] = useState(false)
  const [quickPrompts, setQuickPrompts] = useState([])
  const [showAllPrompts, setShowAllPrompts] = useState(false)
  const [mascotState, setMascotState] = useState('idle')
  const [chatError, setChatError] = useState('')
  const [successOpen, setSuccessOpen] = useState(false)

  const { preferences } = useMotionPreferences()
  const { play } = useActionSoundEngine()
  const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api/v1'
  const moduleName = currentPath.split('/')[1] || 'dashboard'
  const screenKey = `${moduleName}_${currentPath.split('/')[2] || 'main'}`

  useEffect(() => {
    if (open && messages.length === 0) {
      setMessages([{ id: 1, role: 'assistant', text: 'Welcome. I am here to help you move faster.' }])
      setMascotState('waiting')
    }
  }, [open, messages.length])

  useEffect(() => {
    if (!open) return
    const loadPrompts = async () => {
      try {
        const url = `${apiBase}/chatbot/quick-prompts?module_name=${encodeURIComponent(moduleName)}&screen_key=${encodeURIComponent(screenKey)}&user_id=${USER_ID}&language=${LANGUAGE}&limit=7`
        const resp = await fetch(url)
        if (!resp.ok) return
        const payload = await resp.json()
        setQuickPrompts(payload.prompts || [])
      } catch {
        setQuickPrompts([])
      }
    }
    loadPrompts()
  }, [open, moduleName, screenKey, currentPath, apiBase])

  const send = async (prefilledText = null, promptId = null) => {
    const sourceText = prefilledText ?? draft
    if (!sourceText.trim() || loading) return
    const nextMessage = sourceText.trim()
    setChatError('')
    setDraft('')
    setMessages((curr) => [...curr, { id: Date.now(), role: 'user', text: nextMessage }])
    setMascotState('listening')
    setLoading(true)
    try {
      setMascotState('thinking')
      const response = await fetch(`${apiBase}/chatbot/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: nextMessage,
          session_id: sessionId,
          context: {
            route_path: currentPath,
            screen_key: screenKey,
            module_name: moduleName,
          },
          actor: { user_id: USER_ID, role: ROLE },
        }),
      })
      if (!response.ok) throw new Error('query failed')
      const payload = await response.json()
      setSessionId(payload.session_id)
      setMessages((curr) => [...curr, { id: Date.now() + 1, role: 'assistant', text: payload.reply }])
      setMascotState('happy')
      setSuccessOpen(true)
      play('message_received')

      if (promptId) {
        fetch(`${apiBase}/chatbot/quick-prompts/usage`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: USER_ID, prompt_id: promptId }),
        }).catch(() => null)
      }
    } catch {
      setMascotState('sad')
      setChatError('Oh no. I couldn’t complete that request. Please try again in a moment.')
      play('error')
      setMessages((curr) => [...curr, { id: Date.now() + 1, role: 'assistant', text: 'Oh no. Something didn’t go as planned.' }])
    } finally {
      setLoading(false)
    }
  }

  const displayedPrompts = showAllPrompts ? quickPrompts : quickPrompts.slice(0, 5)

  return (
    <>
      {preferences.showMascotAssistant && <MascotSuccessToast open={successOpen} message="That worked." onClose={() => setSuccessOpen(false)} />}
      <button onClick={() => { const next = !open; setOpen(next); setMascotState(next ? 'waiting' : 'idle') }} style={{ position: 'fixed', right: 24, bottom: 24, borderRadius: 999, width: 56, height: 56, border: 'none', background: '#1d4ed8', color: '#fff', fontSize: 22, cursor: 'pointer', zIndex: 40 }} aria-label="Open assistant">💬</button>
      {open && (
        <section style={{ position: 'fixed', right: 24, bottom: 90, width: 410, height: 520, background: '#fff', border: '1px solid #cbd5e1', borderRadius: 12, boxShadow: '0 10px 35px rgba(15, 23, 42, 0.2)', display: 'grid', gridTemplateRows: 'auto auto 1fr auto auto', zIndex: 41 }}>
          <header style={{ padding: '10px 12px', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            {preferences.showMascotAssistant ? <MascotStateRenderer state={mascotState} subtitle={currentPath} /> : <strong>Execution Assistant</strong>}
          </header>

          {loading && preferences.showMascotAssistant && <div style={{ padding: '8px 10px' }}><MascotLoadingPanel message="Thinking through your request…" /></div>}

          <div style={{ padding: 10, overflowY: 'auto', background: '#f8fafc' }}>
            {!loading && chatError && preferences.showMascotAssistant && <MascotErrorState message={chatError} />}
            {!loading && messages.length === 0 && preferences.showMascotAssistant && <MascotEmptyState message="No conversation yet. Start with a smart prompt." />}
            {messages.map((m) => (
              <div key={m.id} style={{ marginBottom: 8, textAlign: m.role === 'user' ? 'right' : 'left' }}>
                <span style={{ display: 'inline-block', maxWidth: '90%', background: m.role === 'user' ? '#dbeafe' : '#fff', border: '1px solid #e2e8f0', borderRadius: 8, padding: '8px 10px' }}>{m.text}</span>
              </div>
            ))}
          </div>

          <div style={{ borderTop: '1px solid #e2e8f0', padding: '8px 10px', background: '#fff' }}>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {displayedPrompts.map((prompt) => (
                <button key={prompt.prompt_id} onClick={() => send(prompt.text, prompt.prompt_id)} style={{ borderRadius: 999, border: '1px solid #bfdbfe', background: '#eff6ff', color: '#1e3a8a', padding: '6px 10px', cursor: 'pointer', fontSize: 12 }} title={prompt.intent_code}>{prompt.text}</button>
              ))}
            </div>
            {quickPrompts.length > 5 && <button onClick={() => setShowAllPrompts((v) => !v)} style={{ marginTop: 6, fontSize: 12, border: 'none', background: 'none', color: '#2563eb', cursor: 'pointer' }}>{showAllPrompts ? 'View less' : 'View more'}</button>}
          </div>

          <footer style={{ display: 'flex', gap: 6, padding: 10, borderTop: '1px solid #e2e8f0' }}>
            <input value={draft} onChange={(e) => { setDraft(e.target.value); if (preferences.showMascotAssistant && e.target.value) setMascotState('listening') }} onKeyDown={(e) => e.key === 'Enter' && send()} placeholder="Ask about this screen..." style={{ flex: 1 }} />
            <button onClick={() => send()} disabled={loading}>{loading ? '...' : 'Send'}</button>
          </footer>
        </section>
      )}
    </>
  )
}

function GlobalHeader({ onHelp, onQuickAdd, onOpenNotifications, onHome, onOpenSettings }) {
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
          {profileOpen && <Dropdown items={[['Assistant Settings', onOpenSettings], ['New Features', () => window.location.assign('/settings/profile/new-features')], ['My Profile', () => {}], ['Logout', () => {}]]} onClose={() => setProfileOpen(false)} />}
        </div>
      </div>
    </header>
  )
}

function AssistantSettingsModal({ onClose }) {
  const { preferences, updatePreference } = useMotionPreferences()
  return (
    <aside style={{ position: 'fixed', right: 20, top: 80, width: 340, background: '#fff', border: '1px solid #cbd5e1', borderRadius: 10, padding: 14, zIndex: 70 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h4 style={{ margin: 0 }}>Assistant Settings</h4>
        <button onClick={onClose}>✕</button>
      </div>
      <SettingToggle label="Assistant Sounds" checked={preferences.assistantSounds} onChange={(v) => updatePreference('assistantSounds', v)} />
      <SettingToggle label="Notification Sounds" checked={preferences.notificationSounds} onChange={(v) => updatePreference('notificationSounds', v)} />
      <SettingToggle label="Reduce Animations" checked={preferences.reduceAnimations} onChange={(v) => updatePreference('reduceAnimations', v)} />
      <SettingToggle label="Show Mascot Assistant" checked={preferences.showMascotAssistant} onChange={(v) => updatePreference('showMascotAssistant', v)} />
    </aside>
  )
}

function SettingToggle({ label, checked, onChange }) {
  return (
    <label style={{ display: 'flex', justifyContent: 'space-between', marginTop: 10, fontSize: 14 }}>
      {label}
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />
    </label>
  )
}

function ModuleCompliancePage() {
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)
  const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api/v1'

  const load = async () => {
    setLoading(true)
    try {
      const resp = await fetch(`${apiBase}/governance/module-compliance`)
      if (resp.ok) setReport(await resp.json())
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  return (
    <div style={{ background: '#fff', padding: 12 }}>
      <h3>Module Compliance Matrix</h3>
      <button onClick={load}>Refresh</button>
      {loading && <p>Loading...</p>}
      {!loading && report && (
        <table width="100%" cellPadding="8" style={{ marginTop: 8 }}>
          <thead><tr><th>Module</th><th>Status</th><th>Missing Capabilities</th></tr></thead>
          <tbody>
            {report.modules.map((m) => (
              <tr key={m.module_name}>
                <td>{m.module_name}</td>
                <td>{m.compliant ? '✅ Complete' : '⚠️ Needs update'}</td>
                <td>{m.missing_capabilities.length ? m.missing_capabilities.join(', ') : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

function NewFeaturesPage() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)
  const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api/v1'

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      try {
        const res = await fetch(`${apiBase}/product-intelligence/release-notes/latest`, { headers: { 'x-role': 'admin' } })
        if (res.ok) setItems(await res.json())
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  return (
    <div style={{ background: '#fff', padding: 12 }}>
      <h3>New Features</h3>
      {loading && <p>Loading release notes...</p>}
      {!loading && items.map((item) => (
        <article key={item.release_note_id} style={{ border: '1px solid #e2e8f0', borderRadius: 8, padding: 10, marginBottom: 8 }}>
          <strong>{item.release_title}</strong>
          <div style={{ fontSize: 12, color: '#64748b' }}>{item.release_version} · {new Date(item.release_date).toLocaleDateString()}</div>
          <p>{item.release_summary}</p>
        </article>
      ))}
      {!loading && !items.length && <p>No release notes published yet.</p>}
    </div>
  )
}

function HelpPanel({ loading, content, onClose }) {
  return (
    <aside style={{ position: 'fixed', right: 0, top: 64, width: 420, bottom: 0, background: '#fff', borderLeft: '1px solid #cbd5e1', padding: 16, overflow: 'auto', zIndex: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}><h3>Contextual Help</h3><button onClick={onClose}>✕</button></div>
      {loading ? <MascotLoadingPanel message="Loading help..." /> : (
        <>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}><MascotAvatar state="idle" size={48} /><h4>{content?.title}</h4></div>
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

function ContextPanel({ panel, close }) {
  if (!panel.open) return <aside style={{ width: 0 }} />
  return (
    <aside style={{ width: 340, background: '#fff', borderLeft: '1px solid #cbd5e1', padding: 12 }}>
      <h3>Context Panel</h3>
      <h4>{panel.mode} - {panel.module}</h4>
      {panel.data && <pre style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 6, padding: 8, overflow: 'auto', maxHeight: 360 }}>{JSON.stringify(panel.data, null, 2)}</pre>}
      <button onClick={close}>Close</button>
    </aside>
  )
}
function BottomPanel() { return <div style={{ background: '#fff', borderTop: '1px solid #e2e8f0', padding: 8 }}>Bottom Panel: Comments | Audit | Notes | Attachments</div> }
function SimplePage({ title }) { return <div style={{ background: '#fff', padding: 16 }}>{title}</div> }

const projectColumns = (setPanel) => [{ key: 'name', label: 'Project', onView: (r) => setPanel({ open: true, mode: 'view', module: '/projects', data: r }), onEdit: (r) => setPanel({ open: true, mode: 'edit', module: '/projects', data: r }) }, { key: 'client', label: 'Client' }, { key: 'status', label: 'Status' }, { key: 'sla', label: 'SLA' }, { key: 'progress', label: 'Progress' }]
const taskColumns = (setPanel) => [{ key: 'task', label: 'Task', onView: (r) => setPanel({ open: true, mode: 'view', module: '/tasks', data: r }), onEdit: (r) => setPanel({ open: true, mode: 'edit', module: '/tasks', data: r }) }, { key: 'project', label: 'Project' }, { key: 'phase', label: 'Phase' }, { key: 'status', label: 'Status' }, { key: 'dependency', label: 'Dependency' }, { key: 'sla', label: 'SLA' }]
const jobColumns = (setPanel) => [{ key: 'job', label: 'Job', onView: (r) => setPanel({ open: true, mode: 'view', module: '/jobs', data: r }), onEdit: (r) => setPanel({ open: true, mode: 'edit', module: '/jobs', data: r }) }, { key: 'assignee', label: 'Assignee' }, { key: 'status', label: 'Status' }, { key: 'sla', label: 'SLA' }, { key: 'spent', label: 'Spent' }]
const timesheetColumns = (setPanel) => [{ key: 'date', label: 'Date', onView: (r) => setPanel({ open: true, mode: 'view', module: '/timesheets', data: r }), onEdit: (r) => setPanel({ open: true, mode: 'edit', module: '/timesheets', data: r }) }, { key: 'employee', label: 'Employee' }, { key: 'task', label: 'Task' }, { key: 'job', label: 'Job' }, { key: 'time', label: 'Time' }, { key: 'overlap', label: 'Overlap', render: (v) => v ? '⚠️' : 'OK' }]
const approvalColumns = (setPanel) => [{ key: 'module', label: 'Module', onView: (r) => setPanel({ open: true, mode: 'view', module: '/approvals', data: r }), onEdit: (r) => setPanel({ open: true, mode: 'edit', module: '/approvals', data: r }) }, { key: 'reference', label: 'Reference' }, { key: 'level', label: 'Level' }, { key: 'status', label: 'Status' }, { key: 'pendingWith', label: 'Pending With' }]

export default App
