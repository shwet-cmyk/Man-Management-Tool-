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

  return (
    <section>
      <h2>Add Subtask / Checklist / To-Do (UC-TASK-004)</h2>
      <form onSubmit={submit} className="form-grid">
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

        <select value={form.item_type} onChange={(e) => setForm({ ...form, item_type: e.target.value })}>
          <option>CHECKLIST</option>
          <option>SUBTASK</option>
          <option>TODO</option>
        </select>

        <input placeholder="Title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
        <input
          type="number"
          placeholder="Assignee Employee ID"
          value={form.assignee_emp_id}
          onChange={(e) => setForm({ ...form, assignee_emp_id: e.target.value })}
        />
        <input type="datetime-local" value={form.due_at} onChange={(e) => setForm({ ...form, due_at: e.target.value })} />
        <input
          type="number"
          step="0.25"
          placeholder="Estimated Hours"
          value={form.estimated_hours}
          onChange={(e) => setForm({ ...form, estimated_hours: e.target.value })}
        />

        <button type="submit">Add Child Item</button>
      </form>

      {message ? <p>{message}</p> : null}

      <h3>Child Items</h3>
      <ul>
        {childItems.map((item) => (
          <li key={item.child_item_id}>
            {item.item_type} - {item.title} [{item.status_code}]
          </li>
        ))}
      </ul>
    </section>
  )
}

export default TaskChildItemsPage
