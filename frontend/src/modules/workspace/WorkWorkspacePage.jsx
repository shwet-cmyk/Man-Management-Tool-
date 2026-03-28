import { useMemo, useState } from 'react'

import { PRIORITY_LEVELS, WORK_STATUSES } from './workData'

const VIEW_TABS = ['List', 'Board', 'Timeline', 'Calendar']
const GROUP_OPTIONS = ['status', 'assignee', 'manager', 'client', 'priority', 'section']
const DRAWER_TABS = ['Summary', 'Activity', 'Dependencies', 'Timesheets', 'Approvals', 'Costing']
const SAVED_VIEWS = ['Execution Focus', 'Manager Triage', 'Client Delivery', 'Finance Oversight']

const defaultColumns = {
  id: true,
  title: true,
  status: true,
  assignee: true,
  manager: true,
  client: true,
  priority: true,
  dueDate: true,
}

function WorkWorkspacePage({ workItems, onUpdateItem, onCreateItem }) {
  const [activeView, setActiveView] = useState('List')
  const [groupBy, setGroupBy] = useState('status')
  const [selectedItemId, setSelectedItemId] = useState(workItems[0]?.id || null)
  const [drawerTab, setDrawerTab] = useState('Summary')
  const [savedView, setSavedView] = useState(SAVED_VIEWS[0])
  const [searchText, setSearchText] = useState('')
  const [calendarMode, setCalendarMode] = useState('Month')
  const [timelineZoom, setTimelineZoom] = useState('Month')
  const [columns, setColumns] = useState(defaultColumns)
  const [quickAdd, setQuickAdd] = useState({ title: '', assignee: '', dueDate: '' })

  const filteredItems = useMemo(
    () =>
      workItems.filter((item) => {
        const searchBucket = `${item.id} ${item.title} ${item.assignee} ${item.client} ${item.status}`.toLowerCase()
        return searchBucket.includes(searchText.toLowerCase())
      }),
    [workItems, searchText],
  )

  const groupedItems = useMemo(() => {
    const map = new Map()
    filteredItems.forEach((item) => {
      const key = item[groupBy] || 'Unassigned'
      if (!map.has(key)) map.set(key, [])
      map.get(key).push(item)
    })
    return Array.from(map.entries())
  }, [filteredItems, groupBy])

  const selectedItem = workItems.find((item) => item.id === selectedItemId) || null

  const updateField = (itemId, field, value) => {
    onUpdateItem(itemId, { [field]: value })
  }

  const onDropToStatus = (event, status) => {
    const itemId = event.dataTransfer.getData('text/plain')
    if (itemId) updateField(itemId, 'status', status)
  }

  const quickAddSubmit = (event) => {
    event.preventDefault()
    if (!quickAdd.title.trim()) return
    onCreateItem(quickAdd)
    setQuickAdd({ title: '', assignee: '', dueDate: '' })
  }

  return (
    <section className="page workspace-page">
      <header className="workspace-header card">
        <div>
          <h2>Workstream Execution Center</h2>
          <p>Task-centered workspace with one shared data model across list, board, timeline, and calendar.</p>
        </div>
        <div className="workspace-header-actions">
          <input
            value={searchText}
            onChange={(event) => setSearchText(event.target.value)}
            placeholder="Search tasks, jobs, assignee, client…"
            aria-label="Search work"
          />
          <button type="button" className="btn-secondary">Command Ready</button>
        </div>
      </header>

      <section className="card quick-add-panel">
        <div>
          <h3>Quick add</h3>
          <p className="muted">Create minimal task/job now, enrich details in drawer.</p>
        </div>
        <form className="quick-add-form" onSubmit={quickAddSubmit}>
          <input
            placeholder="Work title"
            value={quickAdd.title}
            onChange={(event) => setQuickAdd((curr) => ({ ...curr, title: event.target.value }))}
          />
          <input
            placeholder="Assignee"
            value={quickAdd.assignee}
            onChange={(event) => setQuickAdd((curr) => ({ ...curr, assignee: event.target.value }))}
          />
          <input
            type="date"
            value={quickAdd.dueDate}
            onChange={(event) => setQuickAdd((curr) => ({ ...curr, dueDate: event.target.value }))}
          />
          <button type="submit" className="btn-primary">Add</button>
        </form>
      </section>

      <section className="card workspace-controls">
        <div className="segmented-controls" role="tablist" aria-label="View switcher">
          {VIEW_TABS.map((tab) => (
            <button
              key={tab}
              type="button"
              className={`segmented-btn ${activeView === tab ? 'segmented-btn-active' : ''}`}
              onClick={() => setActiveView(tab)}
            >
              {tab}
            </button>
          ))}
        </div>
        <div className="view-helpers">
          <select value={savedView} onChange={(event) => setSavedView(event.target.value)}>
            {SAVED_VIEWS.map((view) => <option key={view}>{view}</option>)}
          </select>
          <select value={groupBy} onChange={(event) => setGroupBy(event.target.value)}>
            {GROUP_OPTIONS.map((group) => <option key={group} value={group}>Group by {group}</option>)}
          </select>
          <details className="column-chooser">
            <summary>Columns</summary>
            {Object.keys(defaultColumns).map((column) => (
              <label key={column}>
                <input
                  type="checkbox"
                  checked={columns[column]}
                  onChange={() => setColumns((curr) => ({ ...curr, [column]: !curr[column] }))}
                />
                {column}
              </label>
            ))}
          </details>
        </div>
      </section>

      {activeView === 'List' && (
        <section className="card list-view-shell">
          {groupedItems.map(([section, sectionItems]) => (
            <div key={section} className="list-section">
              <div className="list-section-header">
                <strong>{section}</strong>
                <span>{sectionItems.length}</span>
              </div>
              <table className="dense-table">
                <thead>
                  <tr>
                    {columns.id && <th>ID</th>}
                    {columns.title && <th>Title</th>}
                    {columns.status && <th>Status</th>}
                    {columns.assignee && <th>Assignee</th>}
                    {columns.manager && <th>Manager</th>}
                    {columns.client && <th>Client</th>}
                    {columns.priority && <th>Priority</th>}
                    {columns.dueDate && <th>Due</th>}
                  </tr>
                </thead>
                <tbody>
                  {sectionItems.map((item) => (
                    <tr key={item.id} onClick={() => setSelectedItemId(item.id)}>
                      {columns.id && <td>{item.id}</td>}
                      {columns.title && <td>{item.title}</td>}
                      {columns.status && (
                        <td>
                          <select
                            value={item.status}
                            onClick={(event) => event.stopPropagation()}
                            onChange={(event) => updateField(item.id, 'status', event.target.value)}
                          >
                            {WORK_STATUSES.map((status) => <option key={status}>{status}</option>)}
                          </select>
                        </td>
                      )}
                      {columns.assignee && <td>{item.assignee}</td>}
                      {columns.manager && <td>{item.manager}</td>}
                      {columns.client && <td>{item.client}</td>}
                      {columns.priority && (
                        <td>
                          <select
                            value={item.priority}
                            onClick={(event) => event.stopPropagation()}
                            onChange={(event) => updateField(item.id, 'priority', event.target.value)}
                          >
                            {PRIORITY_LEVELS.map((priority) => <option key={priority}>{priority}</option>)}
                          </select>
                        </td>
                      )}
                      {columns.dueDate && <td>{item.dueDate}</td>}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </section>
      )}

      {activeView === 'Board' && (
        <section className="board-view-grid">
          {WORK_STATUSES.map((status) => {
            const cards = filteredItems.filter((item) => item.status === status)
            return (
              <article
                key={status}
                className="card board-lane"
                onDragOver={(event) => event.preventDefault()}
                onDrop={(event) => onDropToStatus(event, status)}
              >
                <header className="board-lane-header">
                  <h3>{status}</h3>
                  <span>{cards.length}</span>
                </header>
                <div className="board-cards">
                  {cards.map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      className="board-card"
                      draggable
                      onDragStart={(event) => event.dataTransfer.setData('text/plain', item.id)}
                      onClick={() => setSelectedItemId(item.id)}
                    >
                      <strong>{item.title}</strong>
                      <p>{item.id} · {item.assignee}</p>
                      <div className="card-badges">
                        <span>{item.priority}</span>
                        <span>{item.billable ? 'Billable' : 'Non-billable'}</span>
                        {item.dependency !== '-' && <span>Dep</span>}
                        {item.rollover > 0 && <span>Rollover {item.rollover}</span>}
                      </div>
                    </button>
                  ))}
                </div>
              </article>
            )
          })}
        </section>
      )}

      {activeView === 'Timeline' && (
        <section className="card timeline-shell">
          <div className="timeline-toolbar">
            <p>Dependency-aware parent/child rows (visual connectors can be layered in next iteration).</p>
            <select value={timelineZoom} onChange={(event) => setTimelineZoom(event.target.value)}>
              <option>Week</option>
              <option>Month</option>
              <option>Quarter</option>
            </select>
          </div>
          <div className="timeline-grid">
            {filteredItems.map((item) => {
              const start = new Date(item.startDate).getTime()
              const end = new Date(item.dueDate).getTime()
              const total = Math.max(end - start, 1)
              const width = Math.max(14, Math.round(total / (1000 * 60 * 60 * 24)))
              return (
                <button key={item.id} type="button" className="timeline-row" onClick={() => setSelectedItemId(item.id)}>
                  <span>{item.id}</span>
                  <div className="timeline-bar-wrap">
                    <div className={`timeline-bar ${item.critical ? 'timeline-bar-critical' : ''}`} style={{ width: `${width}%` }}>
                      {item.title}
                    </div>
                  </div>
                </button>
              )
            })}
          </div>
        </section>
      )}

      {activeView === 'Calendar' && (
        <section className="card calendar-shell">
          <div className="calendar-toolbar">
            <h3>Capacity calendar</h3>
            <div>
              {['Month', 'Week', 'Day'].map((mode) => (
                <button
                  key={mode}
                  type="button"
                  className={`btn-secondary ${calendarMode === mode ? 'calendar-mode-active' : ''}`}
                  onClick={() => setCalendarMode(mode)}
                >
                  {mode}
                </button>
              ))}
            </div>
          </div>
          <div className="calendar-grid">
            {filteredItems.slice(0, calendarMode === 'Day' ? 4 : 12).map((item) => (
              <button key={item.id} type="button" className="calendar-item" onClick={() => setSelectedItemId(item.id)}>
                <strong>{item.dueDate}</strong>
                <p>{item.title}</p>
                <small>Planned {item.plannedHours}h · Actual {item.actualHours}h · Free {item.freeCapacityHours}h</small>
              </button>
            ))}
          </div>
        </section>
      )}

      {selectedItem && (
        <aside className="detail-drawer" aria-label="Work detail drawer">
          <header>
            <div>
              <p className="muted">{selectedItem.type} · {selectedItem.id}</p>
              <h3>{selectedItem.title}</h3>
            </div>
            <button type="button" className="btn-text" onClick={() => setSelectedItemId(null)}>Close</button>
          </header>

          <div className="drawer-quick-actions">
            <button type="button" className="btn-secondary">Add Timesheet</button>
            <button type="button" className="btn-secondary">Request Approval</button>
            <button type="button" className="btn-secondary">Attach File</button>
          </div>

          <div className="drawer-tabs">
            {DRAWER_TABS.map((tab) => (
              <button
                key={tab}
                type="button"
                className={drawerTab === tab ? 'drawer-tab-active' : ''}
                onClick={() => setDrawerTab(tab)}
              >
                {tab}
              </button>
            ))}
          </div>

          {drawerTab === 'Summary' && (
            <div className="drawer-section">
              <label>Assignee
                <input value={selectedItem.assignee} onChange={(event) => updateField(selectedItem.id, 'assignee', event.target.value)} />
              </label>
              <label>Status
                <select value={selectedItem.status} onChange={(event) => updateField(selectedItem.id, 'status', event.target.value)}>
                  {WORK_STATUSES.map((status) => <option key={status}>{status}</option>)}
                </select>
              </label>
              <label>Priority
                <select value={selectedItem.priority} onChange={(event) => updateField(selectedItem.id, 'priority', event.target.value)}>
                  {PRIORITY_LEVELS.map((priority) => <option key={priority}>{priority}</option>)}
                </select>
              </label>
              <label>Due date
                <input type="date" value={selectedItem.dueDate} onChange={(event) => updateField(selectedItem.id, 'dueDate', event.target.value)} />
              </label>
            </div>
          )}

          {drawerTab === 'Activity' && (
            <ul className="activity-list">
              {selectedItem.comments.map((comment, index) => <li key={`${comment}-${index}`}>{comment}</li>)}
              {selectedItem.comments.length === 0 && <li>No activity yet.</li>}
            </ul>
          )}

          {drawerTab !== 'Summary' && drawerTab !== 'Activity' && (
            <div className="drawer-placeholder">
              <p>{drawerTab} module is ready for ERP validations, permission checks, and extended workflows.</p>
            </div>
          )}
        </aside>
      )}
    </section>
  )
}

export default WorkWorkspacePage
