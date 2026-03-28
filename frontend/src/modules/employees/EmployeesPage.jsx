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
    <section className="page">
      <div className="page-heading">
        <h2>Employees</h2>
        <p>Maintain employee records and department mapping.</p>
      </div>
      <div className="page-actions">
        <button className="btn-secondary" type="button" onClick={loadData}>Refresh</button>
      </div>

      <div className="card">
        <h3 className="card-title">Add Employee</h3>
        <form onSubmit={submit} className="form-grid">
          <div className="field">
            <label>Employee Code</label>
            <input
              placeholder="Employee Code"
              value={form.employee_code}
              onChange={(e) => setForm({ ...form, employee_code: e.target.value })}
              required
            />
          </div>
          <div className="field">
            <label>Full Name</label>
            <input
              placeholder="Full Name"
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              required
            />
          </div>
          <div className="field">
            <label>Email</label>
            <input
              placeholder="Email"
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              required
            />
          </div>
          <div className="field">
            <label>Job Title</label>
            <input
              placeholder="Job Title"
              value={form.job_title}
              onChange={(e) => setForm({ ...form, job_title: e.target.value })}
              required
            />
          </div>
          <div className="field">
            <label>Join Date</label>
            <input
              type="date"
              value={form.join_date}
              onChange={(e) => setForm({ ...form, join_date: e.target.value })}
              required
            />
          </div>
          <div className="field">
            <label>Department</label>
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
          </div>
          <div className="form-grid-full">
            <button className="btn-primary" type="submit">Add Employee</button>
          </div>
        </form>
      </div>

      <div className="card">
        <h3 className="card-title">Employee List</h3>
        {employees.length ? (
          <table className="data-table">
            <thead>
              <tr>
                <th>Code</th>
                <th>Name</th>
                <th>Job Title</th>
              </tr>
            </thead>
            <tbody>
              {employees.map((employee) => (
                <tr key={employee.id}>
                  <td>{employee.employee_code}</td>
                  <td>{employee.full_name}</td>
                  <td>{employee.job_title}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="empty-state">No employees found.</p>
        )}
      </div>
    </section>
  )
}

export default EmployeesPage
