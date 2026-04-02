import { useMemo, useState } from 'react'

const moduleTree = [
  { label: 'Dashboard', children: ['Role Dashboard', 'Custom Dashboard'] },
  { label: 'Project Module', children: ['Project List', 'Project Dashboard', 'Phases', 'Steps'] },
  { label: 'Masters', children: ['RBAC / Rules', 'User Master', 'Company Master', 'Branch Master', 'Department Master'] },
  { label: 'Interconnect Master', children: ['Grid', 'Coverage Matrix'] },
  { label: 'Reports', children: ['Templates', 'Run', 'Export', 'Schedules'] },
  { label: 'Analytics', children: ['Pre-built Charts', 'Saved Views', 'Alert Rules'] },
]

const datasets = [
  { code: 'TASK_EXECUTION', fields: ['task_id', 'status', 'assignee', 'planned_hours', 'actual_hours'] },
  { code: 'JOB_COMMERCIAL', fields: ['job_id', 'client', 'billable_hours', 'cost', 'margin'] },
  { code: 'USER_PRODUCTIVITY', fields: ['user_id', 'department', 'completed_tasks', 'utilization_pct'] },
]

const seedProjects = [
  { id: 1, name: 'SAP Rollout', client: 'Acme', manager: 'Aarav', status: 'ACTIVE', health: 'ON_TRACK', progress: 42, estimatedCost: 500000, actualCost: 212000 },
  { id: 2, name: 'Support Revamp', client: 'Globex', manager: 'Nina', status: 'ON_HOLD', health: 'AT_RISK', progress: 55, estimatedCost: 220000, actualCost: 188000 },
]

const seedWidgets = [
  { id: 1, title: 'Phase Progress', dataset: 'TASK_EXECUTION', x: 'status', y: 'task_id', chartType: 'BAR' },
  { id: 2, title: 'Cost vs Budget', dataset: 'JOB_COMMERCIAL', x: 'client', y: 'cost', chartType: 'LINE' },
]

const seedInterconnects = [
  { id: 1, source: 'TASKS', target: 'JOBS', trigger: 'Task Approved', status: 'ACTIVE', coverage: 'COVERED' },
  { id: 2, source: 'JOBS', target: 'TIMESHEETS', trigger: 'Job In Progress', status: 'ACTIVE', coverage: 'PENDING' },
  { id: 3, source: 'PROJECT', target: 'TASKS', trigger: 'Project Activated', status: 'ACTIVE', coverage: 'PENDING' },
]

function App() {
  const [selectedModule, setSelectedModule] = useState('Dashboard')
  const [search, setSearch] = useState('')
  const [projects, setProjects] = useState(seedProjects)
  const [widgets, setWidgets] = useState(seedWidgets)
  const [interconnects, setInterconnects] = useState(seedInterconnects)
  const [widgetForm, setWidgetForm] = useState({ title: 'New Widget', dataset: 'TASK_EXECUTION', x: 'status', y: 'task_id', agg: 'COUNT', chartType: 'BAR' })
  const [projectForm, setProjectForm] = useState({ projectName: 'New Project', client: 'Client', manager: 'Manager', estimatedCost: 0, estimatedHours: 0, managementPoc: '', operationsPoc: '', implementationPoc: '', supportPoc: '', developmentPoc: '', accountsPoc: '' })
  const [interconnectForm, setInterconnectForm] = useState({ source: 'PROJECT', target: 'TASKS', trigger: 'Project Activated', validation: 'RBAC + scope + status check', failure: 'Retry + alert + audit' })
  const [analyticsForm, setAnalyticsForm] = useState({ company: '', branch: '', department: '', employee: '', client: '', project: '', date_from: '', date_to: '', priority: '' })
  const [savedViews, setSavedViews] = useState([])
  const [reportFields, setReportFields] = useState(['company_id', 'name', 'status'])

  const filteredInterconnects = useMemo(() => interconnects.filter((r) => `${r.source} ${r.target} ${r.trigger} ${r.coverage}`.toLowerCase().includes(search.toLowerCase())), [interconnects, search])
  const filteredProjects = useMemo(() => projects.filter((p) => `${p.name} ${p.client} ${p.manager} ${p.status}`.toLowerCase().includes(search.toLowerCase())), [projects, search])
  const currentDataset = datasets.find((d) => d.code === widgetForm.dataset)

  const saveWidget = () => setWidgets((curr) => [...curr, { id: curr.length + 1, ...widgetForm }])
  const saveProject = () => setProjects((curr) => [...curr, { id: curr.length + 1, name: projectForm.projectName, client: projectForm.client, manager: projectForm.manager, status: 'DRAFT', health: 'ON_TRACK', progress: 0, estimatedCost: Number(projectForm.estimatedCost), actualCost: 0 }])
  const saveInterconnect = () => setInterconnects((curr) => [...curr, { id: curr.length + 1, ...interconnectForm, status: 'ACTIVE', coverage: 'PENDING' }])
  const saveAnalyticsView = () => setSavedViews((curr) => [...curr, { id: curr.length + 1, name: `View ${curr.length + 1}`, ...analyticsForm }])

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr 420px', height: '100vh', fontFamily: 'Inter, sans-serif' }}>
      <aside style={{ borderRight: '1px solid #d9e0ea', padding: 12, background: '#0f172a', color: '#fff', overflow: 'auto' }}>
        <h3>TEZ Execution System</h3>
        <p style={{ fontSize: 12, opacity: 0.8 }}>RBAC-controlled module tree</p>
        {moduleTree.map((node) => (
          <div key={node.label} style={{ marginBottom: 8 }}>
            <button onClick={() => setSelectedModule(node.label)} style={{ width: '100%', textAlign: 'left', padding: 8, border: 'none', borderRadius: 6, background: selectedModule === node.label ? '#1d4ed8' : '#1e293b', color: '#fff' }}>{node.label}</button>
            <div style={{ marginLeft: 12, marginTop: 4, fontSize: 12, opacity: 0.85 }}>{node.children.map((child) => <div key={child}>• {child}</div>)}</div>
          </div>
        ))}
      </aside>

      <main style={{ padding: 16, background: '#f3f5f8', overflow: 'auto' }}>
        <h2>{selectedModule}</h2>
        <div style={{ background: '#fff', border: '1px solid #d9e0ea', borderRadius: 8, padding: 12, marginTop: 12, display: 'flex', gap: 8 }}>
          <button>Add</button><button>Export</button><button>Filter</button><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search" /><button>Bulk Action</button>
          <button style={{ marginLeft: 'auto' }}>Analytics</button>
        </div>

        {selectedModule === 'Dashboard' && (
          <div style={{ marginTop: 12, display: 'grid', gridTemplateColumns: 'repeat(2,minmax(0,1fr))', gap: 12 }}>
            {widgets.map((w) => (
              <div key={w.id} style={{ background: '#fff', border: '1px solid #d9e0ea', borderRadius: 8, padding: 12 }}>
                <strong>{w.title}</strong>
                <p style={{ margin: 0, fontSize: 13 }}>Dataset: {w.dataset}</p>
                <p style={{ margin: 0, fontSize: 13 }}>X: {w.x} | Y: {w.y} | Type: {w.chartType}</p>
                <div style={{ marginTop: 8, height: 70, background: 'linear-gradient(90deg,#dbeafe,#e2e8f0)', borderRadius: 6 }} />
              </div>
            ))}
          </div>
        )}

        {selectedModule === 'Project Module' && (
          <div style={{ marginTop: 12, background: '#fff', border: '1px solid #d9e0ea', borderRadius: 8, padding: 12 }}>
            <h4>Project List</h4>
            <table width="100%" cellPadding="8" style={{ borderCollapse: 'collapse' }}>
              <thead><tr style={{ textAlign: 'left', borderBottom: '1px solid #e5e7eb' }}><th>Name</th><th>Client</th><th>Manager</th><th>Status</th><th>Health</th><th>Progress</th><th>Budget</th></tr></thead>
              <tbody>{filteredProjects.map((p) => <tr key={p.id} style={{ borderBottom: '1px solid #f3f4f6' }}><td>{p.name}</td><td>{p.client}</td><td>{p.manager}</td><td>{p.status}</td><td>{p.health}</td><td>{p.progress}%</td><td>{p.actualCost}/{p.estimatedCost}</td></tr>)}</tbody>
            </table>
          </div>
        )}

        {selectedModule === 'Interconnect Master' && (
          <div style={{ background: '#fff', border: '1px solid #d9e0ea', borderRadius: 8, padding: 12, marginTop: 12 }}>
            <h4>Interconnect Grid</h4>
            <table width="100%" cellPadding="8" style={{ borderCollapse: 'collapse' }}>
              <thead><tr style={{ textAlign: 'left', borderBottom: '1px solid #e5e7eb' }}><th>Source</th><th>Target</th><th>Trigger</th><th>Status</th><th>Coverage</th></tr></thead>
              <tbody>{filteredInterconnects.map((r) => <tr key={r.id} style={{ borderBottom: '1px solid #f3f4f6' }}><td>{r.source}</td><td>{r.target}</td><td>{r.trigger}</td><td>{r.status}</td><td>{r.coverage}</td></tr>)}</tbody>
            </table>
          </div>
        )}

        {selectedModule === 'Analytics' && (
          <div style={{ background: '#fff', border: '1px solid #d9e0ea', borderRadius: 8, padding: 12, marginTop: 12 }}>
            <h4>Global Analytics (RBAC + Scope Aware)</h4>
            <div style={{ marginTop: 10, height: 110, borderRadius: 8, background: 'linear-gradient(120deg,#111827,#d4af37)' }} />
            <p style={{ marginTop: 8 }}>Saved views: {savedViews.length}</p>
          </div>
        )}

        {selectedModule === 'Reports' && (
          <div style={{ background: '#fff', border: '1px solid #d9e0ea', borderRadius: 8, padding: 12, marginTop: 12 }}>
            <h4>Reporting Builder</h4>
            <p>Field toggling and export formats (Excel/PDF).</p>
            <p>Selected fields: {reportFields.join(', ')}</p>
          </div>
        )}
      </main>

      <aside style={{ borderLeft: '1px solid #d9e0ea', padding: 16, background: '#fff', overflow: 'auto' }}>
        <h3>Right Drawer</h3>

        {selectedModule === 'Dashboard' && (
          <>
            <h4>Create Widget</h4>
            <label>Dataset</label><select value={widgetForm.dataset} onChange={(e) => setWidgetForm((c) => ({ ...c, dataset: e.target.value }))} style={{ width: '100%', marginBottom: 8 }}>{datasets.map((d) => <option key={d.code}>{d.code}</option>)}</select>
            <label>X-Axis</label><select value={widgetForm.x} onChange={(e) => setWidgetForm((c) => ({ ...c, x: e.target.value }))} style={{ width: '100%', marginBottom: 8 }}>{currentDataset?.fields.map((f) => <option key={f}>{f}</option>)}</select>
            <label>Y-Axis</label><select value={widgetForm.y} onChange={(e) => setWidgetForm((c) => ({ ...c, y: e.target.value }))} style={{ width: '100%', marginBottom: 8 }}>{currentDataset?.fields.map((f) => <option key={f}>{f}</option>)}</select>
            <label>Aggregation</label><select value={widgetForm.agg} onChange={(e) => setWidgetForm((c) => ({ ...c, agg: e.target.value }))} style={{ width: '100%', marginBottom: 8 }}>{['SUM','COUNT','AVG','MIN','MAX'].map((a) => <option key={a}>{a}</option>)}</select>
            <label>Chart Type</label><select value={widgetForm.chartType} onChange={(e) => setWidgetForm((c) => ({ ...c, chartType: e.target.value }))} style={{ width: '100%', marginBottom: 8 }}>{['BAR','LINE','SCATTER','PIE','TABLE','KPI'].map((c) => <option key={c}>{c}</option>)}</select>
            <button onClick={saveWidget}>Preview</button> <button onClick={saveWidget}>Save Widget</button>
          </>
        )}

        {selectedModule === 'Project Module' && (
          <>
            <h4>Create Project</h4>
            <label>Project Name</label><input value={projectForm.projectName} onChange={(e) => setProjectForm((c) => ({ ...c, projectName: e.target.value }))} style={{ width: '100%', marginBottom: 8 }} />
            <label>Client</label><input value={projectForm.client} onChange={(e) => setProjectForm((c) => ({ ...c, client: e.target.value }))} style={{ width: '100%', marginBottom: 8 }} />
            <label>Project Manager</label><input value={projectForm.manager} onChange={(e) => setProjectForm((c) => ({ ...c, manager: e.target.value }))} style={{ width: '100%', marginBottom: 8 }} />
            <label>Estimated Cost</label><input type="number" value={projectForm.estimatedCost} onChange={(e) => setProjectForm((c) => ({ ...c, estimatedCost: e.target.value }))} style={{ width: '100%', marginBottom: 8 }} />
            <label>Estimated Hours</label><input type="number" value={projectForm.estimatedHours} onChange={(e) => setProjectForm((c) => ({ ...c, estimatedHours: e.target.value }))} style={{ width: '100%', marginBottom: 8 }} />
            <p style={{ fontSize: 12 }}>Mandatory group POCs: Management, Operations, Implementation, Support, Development, Accounts</p>
            <button onClick={saveProject}>Save Project</button>
          </>
        )}

        {selectedModule === 'Interconnect Master' && (
          <>
            <h4>Add/Edit Interconnect</h4>
            <label>Source</label><input value={interconnectForm.source} onChange={(e) => setInterconnectForm((c) => ({ ...c, source: e.target.value }))} style={{ width: '100%', marginBottom: 8 }} />
            <label>Target</label><input value={interconnectForm.target} onChange={(e) => setInterconnectForm((c) => ({ ...c, target: e.target.value }))} style={{ width: '100%', marginBottom: 8 }} />
            <label>Trigger</label><input value={interconnectForm.trigger} onChange={(e) => setInterconnectForm((c) => ({ ...c, trigger: e.target.value }))} style={{ width: '100%', marginBottom: 8 }} />
            <label>Validation</label><textarea value={interconnectForm.validation} onChange={(e) => setInterconnectForm((c) => ({ ...c, validation: e.target.value }))} style={{ width: '100%', marginBottom: 8 }} />
            <label>Failure Handling</label><textarea value={interconnectForm.failure} onChange={(e) => setInterconnectForm((c) => ({ ...c, failure: e.target.value }))} style={{ width: '100%', marginBottom: 8 }} />
            <button onClick={saveInterconnect}>Save</button>
          </>
        )}

        {selectedModule === 'Analytics' && (
          <>
            <h4>Analytics Filters</h4>
            {Object.keys(analyticsForm).map((key) => (<div key={key}><label>{key}</label><input value={analyticsForm[key]} onChange={(e) => setAnalyticsForm((c) => ({ ...c, [key]: e.target.value }))} style={{ width: '100%', marginBottom: 8 }} /></div>))}
            <button onClick={saveAnalyticsView}>Save View</button><button style={{ marginLeft: 6 }}>Run Analytics</button>
          </>
        )}

        {selectedModule === 'Reports' && (
          <>
            <h4>Report Builder</h4>
            <label><input type="checkbox" checked={reportFields.includes('company_id')} onChange={() => setReportFields((f) => f.includes('company_id') ? f.filter((x) => x !== 'company_id') : [...f, 'company_id'])} /> company_id</label><br />
            <label><input type="checkbox" checked={reportFields.includes('name')} onChange={() => setReportFields((f) => f.includes('name') ? f.filter((x) => x !== 'name') : [...f, 'name'])} /> name</label><br />
            <label><input type="checkbox" checked={reportFields.includes('status')} onChange={() => setReportFields((f) => f.includes('status') ? f.filter((x) => x !== 'status') : [...f, 'status'])} /> status</label>
            <div style={{ marginTop: 8 }}><button>Preview</button> <button>Export Excel</button> <button>Export PDF</button></div>
          </>
        )}

        <hr />
        <h4>Bottom Panel</h4>
        <p>Comments · Audit logs · Notes · Attachments</p>
      </aside>
    </div>
  )
}

export default App
