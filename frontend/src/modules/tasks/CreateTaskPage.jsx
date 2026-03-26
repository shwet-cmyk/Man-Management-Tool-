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

  return (
    <section>
      <h2>Create Task (UC-TASK-001)</h2>
      <form className="form-grid">
        <input placeholder="Title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
        <input
          placeholder="Description"
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
        />

        <input
          type="number"
          placeholder="Company ID"
          value={form.company_id}
          onChange={(e) => setForm({ ...form, company_id: e.target.value })}
          required
        />

        <select value={form.task_type} onChange={(e) => setForm({ ...form, task_type: e.target.value })}>
          <option>Task</option>
          <option>Bug</option>
          <option>Ticket</option>
          <option>Milestone</option>
          <option>Approval</option>
          <option>Internal Work</option>
        </select>

        <select value={form.priority_code} onChange={(e) => setForm({ ...form, priority_code: e.target.value })}>
          <option>Low</option>
          <option>Medium</option>
          <option>High</option>
          <option>Critical</option>
        </select>

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

        <select value={form.manager_emp_id} onChange={(e) => setForm({ ...form, manager_emp_id: e.target.value })}>
          <option value="">Manager (required for High/Critical)</option>
          {employeeOptions.map((employee) => (
            <option key={employee.emp_id} value={employee.emp_id}>
              {employee.employee_name}
            </option>
          ))}
        </select>

        <input
          type="number"
          placeholder="Customer ID (required if billable)"
          value={form.customer_id}
          onChange={(e) => setForm({ ...form, customer_id: e.target.value })}
        />

        <label>
          <input
            type="checkbox"
            checked={form.billable_flag}
            onChange={(e) => setForm({ ...form, billable_flag: e.target.checked })}
          />
          Billable
        </label>

        <input
          type="number"
          step="0.01"
          placeholder="Billed Amount"
          value={form.billed_amount}
          onChange={(e) => setForm({ ...form, billed_amount: e.target.value })}
        />

        <input
          type="number"
          step="0.25"
          placeholder="Estimated Hours"
          value={form.estimated_hours}
          onChange={(e) => setForm({ ...form, estimated_hours: e.target.value })}
        />

        <input
          type="datetime-local"
          value={form.planned_start}
          onChange={(e) => setForm({ ...form, planned_start: e.target.value })}
        />

        <input type="datetime-local" value={form.due_at} onChange={(e) => setForm({ ...form, due_at: e.target.value })} />

        <select value={form.source_type} onChange={(e) => setForm({ ...form, source_type: e.target.value })}>
          <option>MANUAL</option>
          <option>API</option>
          <option>WORKFLOW</option>
          <option>RECURRING</option>
          <option>SYSTEM</option>
        </select>

        <input
          placeholder="Source Reference (idempotency key)"
          value={form.source_reference}
          onChange={(e) => setForm({ ...form, source_reference: e.target.value })}
        />

        <label>
          <input
            type="checkbox"
            checked={form.allow_duplicate}
            onChange={(e) => setForm({ ...form, allow_duplicate: e.target.checked })}
          />
          Allow duplicate similar task
        </label>

        <button type="button" onClick={(e) => submit(e, 'DRAFT')}>Save Draft</button>
        <button type="button" onClick={(e) => submit(e, 'SUBMIT')}>Save & Assign</button>
      </form>

      {message ? <p>{message}</p> : null}

      <h3>Recent Tasks</h3>
      <ul>
        {tasks.slice(0, 8).map((task) => (
          <li key={task.task_id}>
            {task.task_no} - {task.title} ({task.priority_code}) [{task.status_code}]
          </li>
        ))}
      </ul>
    </section>
  )
}

export default CreateTaskPage
