import { useEffect, useState } from 'react'

import api from '../../api/client'

function EmployeeSyncPage() {
  const [summary, setSummary] = useState({ total_employees: 0, active_employees: 0, last_sync_time: null })
  const [logs, setLogs] = useState([])
  const [busy, setBusy] = useState(false)

  const load = async () => {
    const [summaryResponse, logsResponse] = await Promise.all([
      api.get('/sync/employees/summary'),
      api.get('/sync/employees/logs?limit=20'),
    ])
    setSummary(summaryResponse.data)
    setLogs(logsResponse.data)
  }

  useEffect(() => {
    load()
  }, [])

  const triggerSync = async (sync_mode) => {
    setBusy(true)
    try {
      await api.post('/sync/employees', { sync_mode })
      await load()
    } finally {
      setBusy(false)
    }
  }

  const syncStatusClass = (status) => {
    if (status === 'SUCCESS' || status === 'COMPLETED') return 'badge badge-success'
    if (status === 'FAILED') return 'badge badge-danger'
    return 'badge badge-warning'
  }

  return (
    <section className="page">
      <div className="page-heading">
        <h2>Employee Master Sync Dashboard</h2>
        <p>Monitor sync health and trigger controlled sync operations.</p>
      </div>
      <div className="page-actions">
        <button className="btn-primary" onClick={() => triggerSync('FULL')} disabled={busy}>
          {busy ? 'Syncing...' : 'Full Sync'}
        </button>
        <button className="btn-secondary" onClick={() => triggerSync('INCREMENTAL')} disabled={busy}>
          {busy ? 'Syncing...' : 'Incremental Sync'}
        </button>
      </div>

      <div className="summary-grid">
        <article className="card">
          <h3 className="card-title">Total Employees</h3>
          <p className="metric-value">{summary.total_employees}</p>
        </article>
        <article className="card">
          <h3 className="card-title">Active Employees</h3>
          <p className="metric-value">{summary.active_employees}</p>
        </article>
        <article className="card">
          <h3 className="card-title">Last Sync Time</h3>
          <p className="metric-value" style={{ fontSize: '1rem' }}>{summary.last_sync_time || 'Never synced'}</p>
        </article>
      </div>

      <div className="card">
        <h3 className="card-title">Recent Sync Logs</h3>
        {logs.length ? (
          <table className="data-table">
            <thead>
              <tr>
                <th>Status</th>
                <th>Mode</th>
                <th>Fetched</th>
                <th>Inserted</th>
                <th>Updated</th>
                <th>Skipped</th>
                <th>Failed</th>
                <th>Completed At</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td><span className={syncStatusClass(log.status)}>{log.status}</span></td>
                  <td>{log.sync_mode}</td>
                  <td>{log.total_fetched}</td>
                  <td>{log.inserted}</td>
                  <td>{log.updated}</td>
                  <td>{log.skipped}</td>
                  <td>{log.failed}</td>
                  <td>{log.completed_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="empty-state">No sync logs yet.</p>
        )}
      </div>
    </section>
  )
}

export default EmployeeSyncPage
