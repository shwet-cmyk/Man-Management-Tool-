import { useEffect, useState } from 'react'

import api from '../../api/client'

const initialForm = {
  employee_code: '',
  full_name: '',
  email: '',
  job_title: '',
  join_date: '',
  department_id: '',
}

function EmployeesPage() {
  const [employees, setEmployees] = useState([])
  const [departments, setDepartments] = useState([])
  const [form, setForm] = useState(initialForm)

  const loadData = async () => {
    const [employeeResponse, departmentResponse] = await Promise.all([
      api.get('/employees'),
      api.get('/departments'),
    ])
    setEmployees(employeeResponse.data)
    setDepartments(departmentResponse.data)
  }

  useEffect(() => {
    loadData()
  }, [])

  const submit = async (event) => {
    event.preventDefault()
    await api.post('/employees', {
      ...form,
      department_id: Number(form.department_id),
    })
    setForm(initialForm)
    await loadData()
  }

  return (
    <section>
      <h2>Employees</h2>
      <form onSubmit={submit} className="form-grid">
        <input
          placeholder="Employee Code"
          value={form.employee_code}
          onChange={(e) => setForm({ ...form, employee_code: e.target.value })}
          required
        />
        <input
          placeholder="Full Name"
          value={form.full_name}
          onChange={(e) => setForm({ ...form, full_name: e.target.value })}
          required
        />
        <input
          placeholder="Email"
          type="email"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          required
        />
        <input
          placeholder="Job Title"
          value={form.job_title}
          onChange={(e) => setForm({ ...form, job_title: e.target.value })}
          required
        />
        <input
          type="date"
          value={form.join_date}
          onChange={(e) => setForm({ ...form, join_date: e.target.value })}
          required
        />
        <select
          value={form.department_id}
          onChange={(e) => setForm({ ...form, department_id: e.target.value })}
          required
        >
          <option value="">Select Department</option>
          {departments.map((department) => (
            <option key={department.id} value={department.id}>
              {department.name}
            </option>
          ))}
        </select>
        <button type="submit">Add Employee</button>
      </form>
      <ul>
        {employees.map((employee) => (
          <li key={employee.id}>
            {employee.employee_code} — {employee.full_name} ({employee.job_title})
          </li>
        ))}
      </ul>
    </section>
  )
}

export default EmployeesPage
