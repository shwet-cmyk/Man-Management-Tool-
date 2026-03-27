import { useEffect, useState } from 'react'

import api from '../../api/client'

const initialForm = {
  employee_id: '',
  work_date: '',
  status: 'Present',
  remarks: '',
}

function AttendancePage() {
  const [attendance, setAttendance] = useState([])
  const [employees, setEmployees] = useState([])
  const [form, setForm] = useState(initialForm)

  const loadData = async () => {
    const [attendanceResponse, employeeResponse] = await Promise.all([
      api.get('/attendance'),
      api.get('/employees'),
    ])
    setAttendance(attendanceResponse.data)
    setEmployees(employeeResponse.data)
  }

  useEffect(() => {
    loadData()
  }, [])

  const submit = async (event) => {
    event.preventDefault()
    await api.post('/attendance', {
      ...form,
      employee_id: Number(form.employee_id),
    })
    setForm(initialForm)
    await loadData()
  }

  return (
    <section>
      <h2>Attendance</h2>
      <form onSubmit={submit} className="form-grid">
        <select
          value={form.employee_id}
          onChange={(e) => setForm({ ...form, employee_id: e.target.value })}
          required
        >
          <option value="">Select Employee</option>
          {employees.map((employee) => (
            <option key={employee.id} value={employee.id}>
              {employee.full_name}
            </option>
          ))}
        </select>
        <input
          type="date"
          value={form.work_date}
          onChange={(e) => setForm({ ...form, work_date: e.target.value })}
          required
        />
        <select
          value={form.status}
          onChange={(e) => setForm({ ...form, status: e.target.value })}
        >
          <option>Present</option>
          <option>Absent</option>
          <option>Leave</option>
          <option>WFH</option>
        </select>
        <input
          placeholder="Remarks"
          value={form.remarks}
          onChange={(e) => setForm({ ...form, remarks: e.target.value })}
        />
        <button type="submit">Mark Attendance</button>
      </form>
      <ul>
        {attendance.map((item) => (
          <li key={item.id}>
            Employee #{item.employee_id} — {item.work_date} — {item.status}
          </li>
        ))}
      </ul>
    </section>
  )
}

export default AttendancePage
