import { useEffect, useState } from 'react'

import api from '../../api/client'

function DepartmentsPage() {
  const [departments, setDepartments] = useState([])
  const [form, setForm] = useState({ name: '', description: '' })

  const loadDepartments = async () => {
    const { data } = await api.get('/departments')
    setDepartments(data)
  }

  useEffect(() => {
    loadDepartments()
  }, [])

  const submit = async (event) => {
    event.preventDefault()
    await api.post('/departments', form)
    setForm({ name: '', description: '' })
    await loadDepartments()
  }

  return (
    <section className="page">
      <div className="page-heading">
        <h2>Departments</h2>
        <p>Manage department master data and structure.</p>
      </div>
      <div className="page-actions">
        <button className="btn-secondary" type="button" onClick={loadDepartments}>Refresh</button>
      </div>

      <div className="card">
        <h3 className="card-title">Add Department</h3>
        <form onSubmit={submit} className="form-grid">
          <div className="field">
            <label>Department Name</label>
            <input
              placeholder="Department Name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              required
            />
          </div>
          <div className="field">
            <label>Description</label>
            <input
              placeholder="Description"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
          </div>
          <div className="form-grid-full">
            <button className="btn-primary" type="submit">Add Department</button>
          </div>
        </form>
      </div>

      <div className="card">
        <h3 className="card-title">Department List</h3>
        {departments.length ? (
          <table className="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              {departments.map((department) => (
                <tr key={department.id}>
                  <td>{department.name}</td>
                  <td>{department.description || 'No description'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="empty-state">No departments found.</p>
        )}
      </div>
    </section>
  )
}

export default DepartmentsPage
