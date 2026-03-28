import { useEffect, useState } from 'react'

import api from '../../api/client'

const statusOptions = [
  'Draft',
  'Open',
  'In Progress',
  'On Hold',
  'Waiting for Review',
  'Approved',
  'Done',
  'Closed',
  'Cancelled',
  'Reopened',
]

function TaskStatusPage() {
  const [tasks, setTasks] = useState([])
  const [taskId, setTaskId] = useState('')
  const [newStatus, setNewStatus] = useState('In Progress')
  const [actionCode, setActionCode] = useState('')
  const [remarks, setRemarks] = useState('')
  const [changedBy, setChangedBy] = useState('1')
  const [message, setMessage] = useState('')

  const load = async () => {
    const { data } = await api.get('/wm/tasks')
    setTasks(data)
  }

  useEffect(() => {
    load()
  }, [])

  const submit = async (event) => {
    event.preventDefault()
    setMessage('')
    try {
      const { data } = await api.post(`/wm/tasks/${taskId}/status-transition`, {
        new_status: newStatus,
        action_code: actionCode || null,
        remarks: remarks || null,
        changed_by: Number(changedBy),
        source: 'UI',
      })
      setMessage(`Updated: ${data.old_status} -> ${data.new_status}`)
      await load()
    } catch (error) {
      setMessage(error.response?.data?.detail || 'Status transition failed')
    }
  }

  const statusClass = message.toLowerCase().includes('failed') ? 'status-message status-error' : 'status-message status-success'

  return (
    <section className="page">
      <div className="page-heading">
        <h2>Update Task Status (UC-TASK-003)</h2>
        <p>Submit lifecycle changes with audit-ready transition details.</p>
      </div>
      <div className="page-actions">
        <button className="btn-secondary" type="button" onClick={load}>Refresh</button>
      </div>

      <div className="card">
        <h3 className="card-title">Status Transition</h3>
        <form onSubmit={submit} className="form-grid">
          <div className="field form-grid-full">
            <label>Task</label>
            <select value={taskId} onChange={(e) => setTaskId(e.target.value)} required>
              <option value="">Select Task</option>
              {tasks.map((task) => (
                <option key={task.task_id} value={task.task_id}>
                  {task.task_no} - {task.title} [{task.status_code}]
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label>New Status</label>
            <select value={newStatus} onChange={(e) => setNewStatus(e.target.value)}>
              {statusOptions.map((status) => (
                <option key={status}>{status}</option>
              ))}
            </select>
          </div>

          <div className="field">
            <label>Action Code</label>
            <input placeholder="Action code" value={actionCode} onChange={(e) => setActionCode(e.target.value)} />
          </div>

          <div className="field">
            <label>Remarks</label>
            <input placeholder="Remarks" value={remarks} onChange={(e) => setRemarks(e.target.value)} />
          </div>

          <div className="field">
            <label>Changed By</label>
            <input type="number" placeholder="Changed by employee ID" value={changedBy} onChange={(e) => setChangedBy(e.target.value)} />
          </div>

          <div className="form-grid-full button-row">
            <button className="btn-primary" type="submit">Update Status</button>
          </div>
        </form>
      </div>

      {message ? <p className={statusClass}>{message}</p> : null}
    </section>
  )
}

export default TaskStatusPage
