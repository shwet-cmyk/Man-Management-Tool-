import { useEffect, useState } from 'react'

import api from '../../api/client'

const defaultParticipantsJson = JSON.stringify(
  [
    {
      emp_id: 100,
      role_code: 'EXECUTOR',
      planned_start: '2026-04-01T10:00:00',
      planned_due: '2026-04-02T18:00:00',
      sequence_no: 1,
      dependency_type: 'NONE',
      submission_required: true,
      acceptance_required: false,
      allocation_pct: 50,
      is_mandatory: true,
    },
    {
      emp_id: 201,
      role_code: 'REVIEWER',
      planned_start: '2026-04-03T10:00:00',
      planned_due: '2026-04-03T18:00:00',
      sequence_no: 2,
      predecessor_sequence_no: 1,
      dependency_type: 'ACCEPTANCE_BASED',
      submission_required: false,
      acceptance_required: true,
      allocation_pct: 20,
      is_mandatory: true,
    },
  ],
  null,
  2,
)

function TaskAssignmentPage() {
  const [tasks, setTasks] = useState([])
  const [taskId, setTaskId] = useState('')
  const [participantsJson, setParticipantsJson] = useState(defaultParticipantsJson)
  const [message, setMessage] = useState('')

  const load = async () => {
    const taskResponse = await api.get('/wm/tasks')
    setTasks(taskResponse.data)
  }

  useEffect(() => {
    load()
  }, [])

  const submit = async (event) => {
    event.preventDefault()
    setMessage('')
    try {
      const participants = JSON.parse(participantsJson)
      const response = await api.post(`/wm/tasks/${taskId}/participants`, { participants })
      const data = response.data
      setMessage(`Saved ${data.participant_count} participants. Task window: ${data.task_start_date} → ${data.task_due_date}`)
      await load()
    } catch (error) {
      const fallback = error instanceof SyntaxError ? 'Invalid JSON format in participants payload' : 'Participant configuration failed'
      setMessage(error.response?.data?.detail || fallback)
    }
  }

  return (
    <section>
      <h2>Configure Task Participants (UC-TASK-002)</h2>
      <form onSubmit={submit} className="form-grid">
        <select value={taskId} onChange={(e) => setTaskId(e.target.value)} required>
          <option value="">Select Task</option>
          {tasks.map((task) => (
            <option key={task.task_id} value={task.task_id}>
              {task.task_no} - {task.title}
            </option>
          ))}
        </select>

        <label htmlFor="participants-json">Participants JSON</label>
        <textarea
          id="participants-json"
          rows={18}
          value={participantsJson}
          onChange={(e) => setParticipantsJson(e.target.value)}
        />

        <button type="submit">Save Participants</button>
      </form>
      {message ? <p>{message}</p> : null}
    </section>
  )
}

export default TaskAssignmentPage
