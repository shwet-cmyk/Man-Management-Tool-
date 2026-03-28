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

  const statusClass = (status) => {
    if (status === 'Present' || status === 'WFH') return 'badge badge-success'
    if (status === 'Leave') return 'badge badge-warning'
    if (status === 'Absent') return 'badge badge-danger'
    return 'badge badge-neutral'
  }

  return (
    <section className="page">
      <div className="page-heading">
        <h2>Attendance</h2>
        <p>Capture daily attendance and monitor status quickly.</p>
      </div>
      <div className="page-actions">
        <button className="btn-secondary" type="button" onClick={loadData}>Refresh</button>
      </div>

      <div className="card">
        <h3 className="card-title">Mark Attendance</h3>
        <form onSubmit={submit} className="form-grid">
          <div className="field">
            <label>Employee</label>
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
          </div>

          <div className="field">
            <label>Work Date</label>
            <input
              type="date"
              value={form.work_date}
              onChange={(e) => setForm({ ...form, work_date: e.target.value })}
              required
            />
          </div>

          <div className="field">
            <label>Status</label>
            <select
              value={form.status}
              onChange={(e) => setForm({ ...form, status: e.target.value })}
            >
              <option>Present</option>
              <option>Absent</option>
              <option>Leave</option>
              <option>WFH</option>
            </select>
          </div>

          <div className="field">
            <label>Remarks</label>
            <input
              placeholder="Remarks"
              value={form.remarks}
              onChange={(e) => setForm({ ...form, remarks: e.target.value })}
            />
          </div>

          <div className="form-grid-full">
            <button className="btn-primary" type="submit">Mark Attendance</button>
          </div>
        </form>
      </div>

      <div className="card">
        <h3 className="card-title">Recent Attendance</h3>
        {attendance.length ? (
          <table className="data-table">
            <thead>
              <tr>
                <th>Employee ID</th>
                <th>Date</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {attendance.map((item) => (
                <tr key={item.id}>
                  <td>{item.employee_id}</td>
                  <td>{item.work_date}</td>
                  <td><span className={statusClass(item.status)}>{item.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="empty-state">No attendance records available.</p>
        )}
      </div>
    </section>
  )
}

export default AttendancePage
