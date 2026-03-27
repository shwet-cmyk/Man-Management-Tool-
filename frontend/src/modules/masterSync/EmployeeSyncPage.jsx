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

  return (
    <section>
      <h2>Employee Master Sync Dashboard</h2>

      <div className="summary-grid">
        <article className="card">
          <h3>Total Employees</h3>
          <p>{summary.total_employees}</p>
        </article>
        <article className="card">
          <h3>Active Employees</h3>
          <p>{summary.active_employees}</p>
        </article>
        <article className="card">
          <h3>Last Sync Time</h3>
          <p>{summary.last_sync_time || 'Never synced'}</p>
        </article>
      </div>

      <div className="actions">
        <button onClick={() => triggerSync('FULL')} disabled={busy}>
          {busy ? 'Syncing...' : 'Full Sync'}
        </button>
        <button onClick={() => triggerSync('INCREMENTAL')} disabled={busy}>
          {busy ? 'Syncing...' : 'Incremental Sync'}
        </button>
      </div>

      <h3>Recent Sync Logs</h3>
      <table className="sync-table">
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
              <td>{log.status}</td>
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
    </section>
  )
}

export default EmployeeSyncPage
