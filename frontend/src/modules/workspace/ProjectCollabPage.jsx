import { useMemo, useState } from 'react'

const projectTypes = ['Client Project', 'Internal Project', 'Ticket-based Project', 'Strategic Project', 'Operational Project']
const projectStatuses = ['Draft', 'Active', 'On Hold', 'At Risk', 'Completed', 'Closed', 'Cancelled', 'Archived']

const seedProject = {
  project_code: 'PRJ-CLI-001',
  project_name: 'Client implementation rollout',
  project_type: 'Client Project',
  status: 'Active',
  priority: 'High',
  owner_name: 'Owner One',
  manager_name: 'Manager One',
  billable_flag: true,
  progress_percent: 54,
  budget_amount: 125000,
  billed_amount_rollup: 62000,
  cost_to_company_rollup: 48500,
  profit_or_loss_rollup: 13500,
}

const seedTeam = [
  { employee_name: 'Owner One', role_type: 'Owner', participation_type: 'Responsible', notification_preference: 'all' },
  { employee_name: 'Manager One', role_type: 'Manager', participation_type: 'Collaborator', notification_preference: 'all' },
  { employee_name: 'Contributor A', role_type: 'Contributor', participation_type: 'Collaborator', notification_preference: 'mentions' },
]

const seedMessages = [
  {
    id: 1,
    entity_type: 'PROJECT',
    record_code: 'PRJ-CLI-001',
    message_type: 'announcement',
    sender_name: 'Owner One',
    text: 'Weekly rollout update shared with team.',
    pinned: true,
    system: false,
    created_at: '2026-03-28 09:15',
  },
  {
    id: 2,
    entity_type: 'JOB',
    record_code: 'JOB-8821',
    message_type: 'blocker',
    sender_name: 'Contributor A',
    text: 'Dependency on transfer acceptance. @11 please review.',
    pinned: false,
    system: false,
    created_at: '2026-03-28 09:22',
  },
  {
    id: 3,
    entity_type: 'TASK',
    record_code: 'TASK-1042',
    message_type: 'system event',
    sender_name: 'System',
    text: 'Task status moved from In Progress to Review.',
    pinned: false,
    system: true,
    created_at: '2026-03-28 09:30',
  },
]

const seedFiles = [
  { file_name: 'kickoff-plan.pdf', linked_entity_type: 'PROJECT', visibility_scope: 'project_team_only' },
  { file_name: 'job-clarification.docx', linked_entity_type: 'JOB', visibility_scope: 'internal_team_only' },
]

const messageTypes = ['discussion', 'blocker', 'clarification', 'approval', 'transfer note', 'completion note', 'financial note', 'announcement', 'system event']

function highlightMentions(text) {
  return text.split(' ').map((token, idx) => (
    <span key={`${token}-${idx}`} className={token.startsWith('@') ? 'mention-chip' : ''}>
      {token}{' '}
    </span>
  ))
}

function ProjectCollabPage({ workItems }) {
  const [activeTab, setActiveTab] = useState('Overview')
  const [project, setProject] = useState(seedProject)
  const [teamMembers, setTeamMembers] = useState(seedTeam)
  const [messages, setMessages] = useState(seedMessages)
  const [files] = useState(seedFiles)
  const [newMessage, setNewMessage] = useState('')
  const [compose, setCompose] = useState({ entity_type: 'PROJECT', record_code: 'PRJ-CLI-001', message_type: 'discussion', pinned: false })
  const [newMember, setNewMember] = useState({ employee_name: '', role_type: 'Contributor', participation_type: 'Collaborator' })

  const tabs = ['Overview', 'List View', 'Board View', 'Timeline View', 'Calendar View', 'Team', 'Chat / Activity', 'Files', 'Dashboard', 'Approvals', 'Billing / Costing']

  const boardByStatus = useMemo(() => {
    const group = {}
    workItems.forEach((item) => {
      if (!group[item.status]) group[item.status] = []
      group[item.status].push(item)
    })
    return group
  }, [workItems])

  const workCodes = ['PRJ-CLI-001', ...workItems.map((item) => item.id)]

  const postMessage = (event) => {
    event.preventDefault()
    if (!newMessage.trim()) return
    setMessages((curr) => [
      ...curr,
      {
        id: curr.length + 1,
        entity_type: compose.entity_type,
        record_code: compose.record_code,
        message_type: compose.message_type,
        sender_name: 'OPS Admin',
        text: newMessage,
        pinned: compose.pinned,
        system: compose.message_type === 'system event',
        created_at: '2026-03-28 10:00',
      },
    ])
    setNewMessage('')
  }

  const addMember = (event) => {
    event.preventDefault()
    if (!newMember.employee_name.trim()) return
    setTeamMembers((curr) => [...curr, { ...newMember, notification_preference: 'all' }])
    setNewMember({ employee_name: '', role_type: 'Contributor', participation_type: 'Collaborator' })
  }

  return (
    <section className="page">
      <header className="card workspace-header">
        <div>
          <h2>Project Collaboration Hub</h2>
          <p>Execution-linked communication across project, task, and job records.</p>
        </div>
      </header>

      <section className="card workspace-controls">
        <div className="segmented-controls">
          {tabs.map((tab) => (
            <button key={tab} type="button" className={`segmented-btn ${tab === activeTab ? 'segmented-btn-active' : ''}`} onClick={() => setActiveTab(tab)}>
              {tab}
            </button>
          ))}
        </div>
      </section>

      {activeTab === 'Overview' && (
        <section className="card">
          <div className="summary-grid">
            <div><p className="muted">Project</p><h3>{project.project_name}</h3><p>{project.project_code} · {project.project_type}</p></div>
            <div><p className="muted">Owner / Manager</p><h3>{project.owner_name}</h3><p>{project.manager_name}</p></div>
            <div><p className="muted">Status / Progress</p><h3>{project.status}</h3><p>{project.progress_percent}% complete</p></div>
          </div>
          <div className="summary-grid" style={{ marginTop: '0.75rem' }}>
            <div><p className="muted">Budget</p><h3>${project.budget_amount.toLocaleString()}</h3></div>
            <div><p className="muted">Billed</p><h3>${project.billed_amount_rollup.toLocaleString()}</h3></div>
            <div><p className="muted">Cost / P&L</p><h3>${project.cost_to_company_rollup.toLocaleString()} / ${project.profit_or_loss_rollup.toLocaleString()}</h3></div>
          </div>
        </section>
      )}

      {activeTab === 'List View' && (
        <section className="card">
          <table className="dense-table">
            <thead><tr><th>Record</th><th>Title</th><th>Status</th><th>Assignee</th><th>Manager</th><th>Due</th><th>Priority</th></tr></thead>
            <tbody>{workItems.map((item) => <tr key={item.id}><td>{item.id}</td><td>{item.title}</td><td>{item.status}</td><td>{item.assignee}</td><td>{item.manager}</td><td>{item.dueDate}</td><td>{item.priority}</td></tr>)}</tbody>
          </table>
        </section>
      )}

      {activeTab === 'Board View' && (
        <section className="board-view-grid">
          {Object.entries(boardByStatus).map(([status, items]) => (
            <article key={status} className="card board-lane">
              <header className="board-lane-header"><h3>{status}</h3><span>{items.length}</span></header>
              <div className="board-cards">{items.map((item) => <div key={item.id} className="board-card"><strong>{item.title}</strong><p>{item.id}</p></div>)}</div>
            </article>
          ))}
        </section>
      )}

      {activeTab === 'Timeline View' && <section className="card"><p className="muted">Timeline aligned to task/job schedule and dependency readiness (planned and due dates).</p></section>}
      {activeTab === 'Calendar View' && <section className="card"><p className="muted">Calendar drilldown surfaces planned work, due dates, and execution hotspots by project context.</p></section>}

      {activeTab === 'Team' && (
        <section className="card">
          <form className="quick-add-form" onSubmit={addMember}>
            <input placeholder="Employee name" value={newMember.employee_name} onChange={(e) => setNewMember((c) => ({ ...c, employee_name: e.target.value }))} />
            <select value={newMember.role_type} onChange={(e) => setNewMember((c) => ({ ...c, role_type: e.target.value }))}>{['Owner', 'Manager', 'Contributor', 'Reviewer', 'Approver', 'Viewer', 'Finance'].map((role) => <option key={role}>{role}</option>)}</select>
            <select value={newMember.participation_type} onChange={(e) => setNewMember((c) => ({ ...c, participation_type: e.target.value }))}>{['Responsible', 'Collaborator', 'Watcher', 'Approver', 'Stakeholder'].map((type) => <option key={type}>{type}</option>)}</select>
            <button type="submit" className="btn-primary">Add Member</button>
          </form>
          <table className="dense-table" style={{ marginTop: '0.75rem' }}><thead><tr><th>Name</th><th>Role</th><th>Participation</th><th>Notifications</th></tr></thead><tbody>{teamMembers.map((row, idx) => <tr key={`${row.employee_name}-${idx}`}><td>{row.employee_name}</td><td>{row.role_type}</td><td>{row.participation_type}</td><td>{row.notification_preference}</td></tr>)}</tbody></table>
        </section>
      )}

      {activeTab === 'Chat / Activity' && (
        <section className="card">
          <form onSubmit={postMessage} className="quick-add-form">
            <select value={compose.entity_type} onChange={(e) => setCompose((curr) => ({ ...curr, entity_type: e.target.value }))}>{['PROJECT', 'TASK', 'JOB', 'APPROVAL'].map((opt) => <option key={opt}>{opt}</option>)}</select>
            <select value={compose.record_code} onChange={(e) => setCompose((curr) => ({ ...curr, record_code: e.target.value }))}>{workCodes.map((code) => <option key={code}>{code}</option>)}</select>
            <select value={compose.message_type} onChange={(e) => setCompose((curr) => ({ ...curr, message_type: e.target.value }))}>{messageTypes.map((type) => <option key={type}>{type}</option>)}</select>
            <label className="muted"><input type="checkbox" checked={compose.pinned} onChange={(e) => setCompose((curr) => ({ ...curr, pinned: e.target.checked }))} /> Pin</label>
            <input value={newMessage} onChange={(e) => setNewMessage(e.target.value)} placeholder="Post blocker / clarification / approval / transfer note…" />
            <button type="submit" className="btn-primary">Post</button>
          </form>

          <div className="compact-thread" style={{ marginTop: '0.75rem' }}>
            {messages.map((msg) => (
              <article key={msg.id} className={`thread-row ${msg.system ? 'thread-row-system' : ''}`}>
                <div className="thread-meta">
                  <strong>{msg.sender_name}</strong>
                  <span>{msg.created_at}</span>
                  <span className="thread-tag">{msg.message_type}</span>
                  <button type="button" className="btn-text">Jump {msg.record_code}</button>
                  {msg.pinned ? <span className="thread-pin">Pinned</span> : null}
                </div>
                <p>{highlightMentions(msg.text)}</p>
              </article>
            ))}
          </div>
        </section>
      )}

      {activeTab === 'Files' && <section className="card"><table className="dense-table"><thead><tr><th>File</th><th>Entity</th><th>Visibility</th></tr></thead><tbody>{files.map((f) => <tr key={f.file_name}><td>{f.file_name}</td><td>{f.linked_entity_type}</td><td>{f.visibility_scope}</td></tr>)}</tbody></table></section>}
      {activeTab === 'Dashboard' && <section className="card"><p className="muted">Project KPI widgets: overdue, critical, approvals, workload, communication activity, cost/billed/profit.</p></section>}
      {activeTab === 'Approvals' && <section className="card"><p className="muted">Approval context remains linked to project records and chat trails for auditability.</p></section>}

      {activeTab === 'Billing / Costing' && (
        <section className="card">
          <div className="quick-add-form">
            <select value={project.status} onChange={(e) => setProject((curr) => ({ ...curr, status: e.target.value }))}>{projectStatuses.map((status) => <option key={status}>{status}</option>)}</select>
            <select value={project.project_type} onChange={(e) => setProject((curr) => ({ ...curr, project_type: e.target.value }))}>{projectTypes.map((type) => <option key={type}>{type}</option>)}</select>
          </div>
          <p className="muted" style={{ marginTop: '0.7rem' }}>Finance-sensitive notes and billing discussions are permission-controlled by backend visibility scope + RBAC.</p>
        </section>
      )}
    </section>
  )
}

export default ProjectCollabPage
