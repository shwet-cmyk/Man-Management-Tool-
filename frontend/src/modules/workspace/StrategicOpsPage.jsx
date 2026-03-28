import { useMemo, useState } from 'react'

function StrategicOpsPage({ workItems }) {
  const [tab, setTab] = useState('Goal Management')
  const [goalProgress, setGoalProgress] = useState(62)

  const overdueCount = useMemo(() => workItems.filter((item) => item.status !== 'Done' && item.dueDate < '2026-03-28').length, [workItems])

  return (
    <section className="page">
      <header className="card workspace-header">
        <div>
          <h2>Strategic Operations Suite</h2>
          <p>Integrated Goal, Intake, Launch, and Resource planning layers aligned to existing execution records.</p>
        </div>
      </header>

      <section className="card workspace-controls">
        <div className="segmented-controls">
          {['Goal Management', 'Project Intake', 'Product Launch', 'Resource Planning'].map((name) => (
            <button key={name} type="button" className={`segmented-btn ${tab === name ? 'segmented-btn-active' : ''}`} onClick={() => setTab(name)}>
              {name}
            </button>
          ))}
        </div>
      </section>

      {tab === 'Goal Management' && (
        <section className="card">
          <div className="summary-grid">
            <div><p className="muted">Goal</p><h3>Reduce overdue jobs by 30%</h3></div>
            <div><p className="muted">Linked records</p><h3>2 Projects · 10 Tasks</h3></div>
            <div><p className="muted">Risk</p><h3>{goalProgress >= 80 ? 'On Track' : 'At Risk'}</h3></div>
          </div>
          <div style={{ marginTop: '0.75rem' }}>
            <label className="muted">Progress {goalProgress}%</label>
            <input type="range" min="0" max="100" value={goalProgress} onChange={(e) => setGoalProgress(Number(e.target.value))} />
          </div>
        </section>
      )}

      {tab === 'Project Intake' && (
        <section className="card">
          <p className="muted">Intake queue is designed to triage and convert requests into Ticket / Project / Task / Job with approval and SLA governance.</p>
          <table className="dense-table" style={{ marginTop: '0.7rem' }}>
            <thead><tr><th>Request</th><th>Type</th><th>Status</th><th>Conversion</th></tr></thead>
            <tbody>
              <tr><td>INT-221</td><td>Project Request</td><td>Under Review</td><td>-</td></tr>
              <tr><td>INT-222</td><td>Support Request</td><td>Approved</td><td>Ticket</td></tr>
              <tr><td>INT-223</td><td>Enhancement</td><td>Converted to Project</td><td>PRJ-CLI-001</td></tr>
            </tbody>
          </table>
        </section>
      )}

      {tab === 'Product Launch' && (
        <section className="card">
          <div className="summary-grid">
            <div><p className="muted">Launch</p><h3>LCH-2026-04</h3><p>Cross-functional rollout</p></div>
            <div><p className="muted">Readiness</p><h3>68%</h3><p>QA + Marketing pending</p></div>
            <div><p className="muted">Risk</p><h3>{overdueCount > 2 ? 'At Risk' : 'On Track'}</h3><p>{overdueCount} overdue linked items</p></div>
          </div>
        </section>
      )}

      {tab === 'Resource Planning' && (
        <section className="card">
          <p className="muted">Planned vs actual staffing aligned to capacity calendar and timesheets.</p>
          <table className="dense-table" style={{ marginTop: '0.7rem' }}>
            <thead><tr><th>Employee</th><th>Planned</th><th>Actual</th><th>Free</th><th>Status</th></tr></thead>
            <tbody>
              <tr><td>Aisha M</td><td>36h</td><td>32h</td><td>4h</td><td>Balanced</td></tr>
              <tr><td>Vikas R</td><td>46h</td><td>41h</td><td>0h</td><td>Overloaded</td></tr>
              <tr><td>Meera L</td><td>22h</td><td>14h</td><td>18h</td><td>Underutilized</td></tr>
            </tbody>
          </table>
        </section>
      )}
    </section>
  )
}

export default StrategicOpsPage
