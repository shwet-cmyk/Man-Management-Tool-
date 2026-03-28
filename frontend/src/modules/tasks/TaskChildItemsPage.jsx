import { useEffect, useState } from 'react'

import api from '../../api/client'

const initial = {
  task_id: '',
  item_type: 'CHECKLIST',
  title: '',
  assignee_emp_id: '',
  due_at: '',
  estimated_hours: '',
}

function TaskChildItemsPage() {
  const [tasks, setTasks] = useState([])
  const [childItems, setChildItems] = useState([])
  const [form, setForm] = useState(initial)
  const [message, setMessage] = useState('')

  const loadTasks = async () => {
    const { data } = await api.get('/wm/tasks')
    setTasks(data)
  }

  const loadChildItems = async (taskId) => {
    if (!taskId) return
    const { data } = await api.get(`/wm/tasks/${taskId}/child-items`)
    setChildItems(data)
  }

  useEffect(() => {
    loadTasks()
  }, [])

  const submit = async (event) => {
    event.preventDefault()
    setMessage('')
    try {
      await api.post(`/wm/tasks/${form.task_id}/child-items`, {
        item_type: form.item_type,
        title: form.title,
        assignee_emp_id: form.assignee_emp_id ? Number(form.assignee_emp_id) : null,
        due_at: form.due_at || null,
        estimated_hours: form.estimated_hours ? Number(form.estimated_hours) : null,
        source_type: 'MANUAL',
      })
      setMessage('Child item created')
      await loadChildItems(form.task_id)
      setForm({ ...form, title: '', assignee_emp_id: '', due_at: '', estimated_hours: '' })
    } catch (error) {
      setMessage(error.response?.data?.detail || 'Failed to create child item')
    }
  }

  const statusClass = message.toLowerCase().includes('failed') ? 'status-message status-error' : 'status-message status-success'

  return (
    <section className="page">
      <div className="page-heading">
        <h2>Add Subtask / Checklist / To-Do (UC-TASK-004)</h2>
        <p>Create child work items and monitor status progression.</p>
      </div>
      <div className="page-actions">
        <button className="btn-secondary" type="button" onClick={loadTasks}>Refresh</button>
      </div>

      <div className="card">
        <h3 className="card-title">Create Child Item</h3>
        <form onSubmit={submit} className="form-grid">
          <div className="field form-grid-full">
            <label>Task</label>
            <select
              value={form.task_id}
              onChange={(e) => {
                setForm({ ...form, task_id: e.target.value })
                loadChildItems(e.target.value)
              }}
              required
            >
              <option value="">Select Task</option>
              {tasks.map((task) => (
                <option key={task.task_id} value={task.task_id}>
                  {task.task_no} - {task.title}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label>Item Type</label>
            <select value={form.item_type} onChange={(e) => setForm({ ...form, item_type: e.target.value })}>
              <option>CHECKLIST</option>
              <option>SUBTASK</option>
              <option>TODO</option>
            </select>
          </div>

          <div className="field">
            <label>Title</label>
            <input placeholder="Title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
          </div>

          <div className="field">
            <label>Assignee Employee ID</label>
            <input
              type="number"
              placeholder="Assignee Employee ID"
              value={form.assignee_emp_id}
              onChange={(e) => setForm({ ...form, assignee_emp_id: e.target.value })}
            />
          </div>

          <div className="field">
            <label>Due At</label>
            <input type="datetime-local" value={form.due_at} onChange={(e) => setForm({ ...form, due_at: e.target.value })} />
          </div>

          <div className="field">
            <label>Estimated Hours</label>
            <input
              type="number"
              step="0.25"
              placeholder="Estimated Hours"
              value={form.estimated_hours}
              onChange={(e) => setForm({ ...form, estimated_hours: e.target.value })}
            />
          </div>

          <div className="form-grid-full button-row">
            <button className="btn-primary" type="submit">Add Child Item</button>
          </div>
        </form>
      </div>

      {message ? <p className={statusClass}>{message}</p> : null}

      <div className="card">
        <h3 className="card-title">Child Items</h3>
        {childItems.length ? (
          <table className="data-table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Title</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {childItems.map((item) => (
                <tr key={item.child_item_id}>
                  <td>{item.item_type}</td>
                  <td>{item.title}</td>
                  <td><span className="badge badge-neutral">{item.status_code}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="empty-state">No child items available for selected task.</p>
        )}
      </div>
    </section>
  )
}

export default TaskChildItemsPage
