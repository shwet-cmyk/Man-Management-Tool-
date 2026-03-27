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

  return (
    <section>
      <h2>Update Task Status (UC-TASK-003)</h2>
      <form onSubmit={submit} className="form-grid">
        <select value={taskId} onChange={(e) => setTaskId(e.target.value)} required>
          <option value="">Select Task</option>
          {tasks.map((task) => (
            <option key={task.task_id} value={task.task_id}>
              {task.task_no} - {task.title} [{task.status_code}]
            </option>
          ))}
        </select>

        <select value={newStatus} onChange={(e) => setNewStatus(e.target.value)}>
          {statusOptions.map((status) => (
            <option key={status}>{status}</option>
          ))}
        </select>

        <input placeholder="Action code" value={actionCode} onChange={(e) => setActionCode(e.target.value)} />
        <input placeholder="Remarks" value={remarks} onChange={(e) => setRemarks(e.target.value)} />
        <input type="number" placeholder="Changed by employee ID" value={changedBy} onChange={(e) => setChangedBy(e.target.value)} />
        <button type="submit">Update Status</button>
      </form>

      {message ? <p>{message}</p> : null}
    </section>
  )
}

export default TaskStatusPage
