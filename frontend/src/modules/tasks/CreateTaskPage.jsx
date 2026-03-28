import { useEffect, useMemo, useState } from 'react'

import api from '../../api/client'

const initialForm = {
  company_id: 1,
  branch_id: '',
  department_id: '',
  customer_id: '',
  project_id: '',
  cost_center_id: '',
  title: '',
  description: '',
  task_type: 'Task',
  priority_code: 'Medium',
  primary_owner_emp_id: '',
  contributor_emp_ids: [],
  manager_emp_id: '',
  reviewer_emp_id: '',
  billable_flag: false,
  billed_amount: 0,
  estimated_hours: '',
  planned_start: '',
  due_at: '',
  workflow_id: '',
  tags: [],
  source_type: 'MANUAL',
  source_reference: '',
  allow_duplicate: false,
}

function CreateTaskPage() {
  const [employees, setEmployees] = useState([])
  const [tasks, setTasks] = useState([])
  const [form, setForm] = useState(initialForm)
  const [message, setMessage] = useState('')

  const employeeOptions = useMemo(() => employees.filter((e) => e.is_active), [employees])

  const loadData = async () => {
    const [empResponse, taskResponse] = await Promise.all([
      api.get('/sync/employees/cache'),
      api.get('/wm/tasks'),
    ])
    setEmployees(empResponse.data)
    setTasks(taskResponse.data)
  }

  useEffect(() => {
    loadData()
  }, [])

  const parseNum = (value) => (value === '' || value === null ? null : Number(value))

  const submit = async (event, saveMode = 'SUBMIT') => {
    event.preventDefault()
    setMessage('')
    try {
      const payload = {
        ...form,
        branch_id: parseNum(form.branch_id),
        department_id: parseNum(form.department_id),
        customer_id: parseNum(form.customer_id),
        project_id: parseNum(form.project_id),
        cost_center_id: parseNum(form.cost_center_id),
        primary_owner_emp_id: parseNum(form.primary_owner_emp_id),
        manager_emp_id: parseNum(form.manager_emp_id),
        reviewer_emp_id: parseNum(form.reviewer_emp_id),
        billable_flag: Boolean(form.billable_flag),
        billed_amount: Number(form.billed_amount || 0),
        estimated_hours: form.estimated_hours === '' ? null : Number(form.estimated_hours),
        workflow_id: parseNum(form.workflow_id),
        save_mode: saveMode,
      }
      const { data } = await api.post('/wm/tasks', payload)
      setMessage(`${data.message} (${data.task_no})`)
      setForm(initialForm)
      await loadData()
    } catch (error) {
      setMessage(error.response?.data?.detail || 'Task creation failed')
    }
  }

  const statusClass = message.toLowerCase().includes('failed') ? 'status-message status-error' : 'status-message status-success'

  return (
    <section className="page">
      <div className="page-heading">
        <h2>Create Task (UC-TASK-001)</h2>
        <p>Define task details and submit into the workflow queue.</p>
      </div>
      <div className="page-actions">
        <button className="btn-secondary" type="button" onClick={loadData}>Refresh</button>
      </div>

      <div className="card">
        <h3 className="card-title">Task Details</h3>
        <form className="form-grid">
          <div className="field">
            <label>Title</label>
            <input placeholder="Title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
          </div>

          <div className="field">
            <label>Description</label>
            <input
              placeholder="Description"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
          </div>

          <div className="field">
            <label>Company ID</label>
            <input
              type="number"
              placeholder="Company ID"
              value={form.company_id}
              onChange={(e) => setForm({ ...form, company_id: e.target.value })}
              required
            />
          </div>

          <div className="field">
            <label>Task Type</label>
            <select value={form.task_type} onChange={(e) => setForm({ ...form, task_type: e.target.value })}>
              <option>Task</option>
              <option>Bug</option>
              <option>Ticket</option>
              <option>Milestone</option>
              <option>Approval</option>
              <option>Internal Work</option>
            </select>
          </div>

          <div className="field">
            <label>Priority</label>
            <select value={form.priority_code} onChange={(e) => setForm({ ...form, priority_code: e.target.value })}>
              <option>Low</option>
              <option>Medium</option>
              <option>High</option>
              <option>Critical</option>
            </select>
          </div>

          <div className="field">
            <label>Primary Owner</label>
            <select
              value={form.primary_owner_emp_id}
              onChange={(e) => setForm({ ...form, primary_owner_emp_id: e.target.value })}
              required
            >
              <option value="">Primary Owner</option>
              {employeeOptions.map((employee) => (
                <option key={employee.emp_id} value={employee.emp_id}>
                  {employee.employee_name} ({employee.emp_id})
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label>Manager</label>
            <select value={form.manager_emp_id} onChange={(e) => setForm({ ...form, manager_emp_id: e.target.value })}>
              <option value="">Manager (required for High/Critical)</option>
              {employeeOptions.map((employee) => (
                <option key={employee.emp_id} value={employee.emp_id}>
                  {employee.employee_name}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label>Customer ID</label>
            <input
              type="number"
              placeholder="Customer ID (required if billable)"
              value={form.customer_id}
              onChange={(e) => setForm({ ...form, customer_id: e.target.value })}
            />
          </div>

          <div className="field">
            <label>Billed Amount</label>
            <input
              type="number"
              step="0.01"
              placeholder="Billed Amount"
              value={form.billed_amount}
              onChange={(e) => setForm({ ...form, billed_amount: e.target.value })}
            />
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

          <div className="field">
            <label>Planned Start</label>
            <input
              type="datetime-local"
              value={form.planned_start}
              onChange={(e) => setForm({ ...form, planned_start: e.target.value })}
            />
          </div>

          <div className="field">
            <label>Due At</label>
            <input type="datetime-local" value={form.due_at} onChange={(e) => setForm({ ...form, due_at: e.target.value })} />
          </div>

          <div className="field">
            <label>Source Type</label>
            <select value={form.source_type} onChange={(e) => setForm({ ...form, source_type: e.target.value })}>
              <option>MANUAL</option>
              <option>API</option>
              <option>WORKFLOW</option>
              <option>RECURRING</option>
              <option>SYSTEM</option>
            </select>
          </div>

          <div className="field">
            <label>Source Reference</label>
            <input
              placeholder="Source Reference (idempotency key)"
              value={form.source_reference}
              onChange={(e) => setForm({ ...form, source_reference: e.target.value })}
            />
          </div>

          <div className="field">
            <label>
              <input
                type="checkbox"
                checked={form.billable_flag}
                onChange={(e) => setForm({ ...form, billable_flag: e.target.checked })}
              />{' '}
              Billable
            </label>
          </div>

          <div className="field">
            <label>
              <input
                type="checkbox"
                checked={form.allow_duplicate}
                onChange={(e) => setForm({ ...form, allow_duplicate: e.target.checked })}
              />{' '}
              Allow duplicate similar task
            </label>
          </div>

          <div className="form-grid-full button-row">
            <button className="btn-secondary" type="button" onClick={(e) => submit(e, 'DRAFT')}>Save Draft</button>
            <button className="btn-primary" type="button" onClick={(e) => submit(e, 'SUBMIT')}>Save & Assign</button>
          </div>
        </form>
      </div>

      {message ? <p className={statusClass}>{message}</p> : null}

      <div className="card">
        <h3 className="card-title">Recent Tasks</h3>
        {tasks.length ? (
          <table className="data-table">
            <thead>
              <tr>
                <th>Task No</th>
                <th>Title</th>
                <th>Priority</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {tasks.slice(0, 8).map((task) => (
                <tr key={task.task_id}>
                  <td>{task.task_no}</td>
                  <td>{task.title}</td>
                  <td>{task.priority_code}</td>
                  <td><span className="badge badge-neutral">{task.status_code}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="empty-state">No tasks found.</p>
        )}
      </div>
    </section>
  )
}

export default CreateTaskPage
