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
    <section>
      <h2>Departments</h2>
      <form onSubmit={submit} className="form-grid">
        <input
          placeholder="Department Name"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          required
        />
        <input
          placeholder="Description"
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
        />
        <button type="submit">Add Department</button>
      </form>
      <ul>
        {departments.map((department) => (
          <li key={department.id}>
            <strong>{department.name}</strong> — {department.description || 'No description'}
          </li>
        ))}
      </ul>
    </section>
  )
}

export default DepartmentsPage
