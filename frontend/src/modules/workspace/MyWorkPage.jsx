function sectionRules(items) {
  const now = new Date('2026-03-28')
  const todayKey = now.toISOString().slice(0, 10)

  return {
    'Assigned to me': items.filter((item) => item.assignee === 'Aisha M'),
    'Due today': items.filter((item) => item.dueDate === todayKey),
    Upcoming: items.filter((item) => item.dueDate > todayKey && item.status !== 'Done'),
    Overdue: items.filter((item) => item.dueDate < todayKey && item.status !== 'Done'),
    Blocked: items.filter((item) => item.status === 'Blocked'),
    'Awaiting acceptance': items.filter((item) => item.status === 'Review'),
    'Pending approvals': items.filter((item) => item.status === 'Review' || item.critical),
    'Missing timesheets': items.filter((item) => item.actualHours === 0),
  }
}

function MyWorkPage({ workItems, onOpenItem }) {
  const sections = sectionRules(workItems)

  return (
    <section className="page">
      <header className="card workspace-header">
        <div>
          <h2>My Work</h2>
          <p>Daily operating view for execution, approvals, and compliance follow-through.</p>
        </div>
      </header>

      <div className="my-work-grid">
        {Object.entries(sections).map(([title, items]) => (
          <article key={title} className="card my-work-section">
            <header>
              <h3>{title}</h3>
              <span>{items.length}</span>
            </header>
            <div className="my-work-list">
              {items.map((item) => (
                <button key={item.id} type="button" onClick={() => onOpenItem(item.id)}>
                  <strong>{item.title}</strong>
                  <small>{item.id} · {item.status} · Due {item.dueDate}</small>
                </button>
              ))}
              {items.length === 0 && <p className="muted">No items in this section.</p>}
            </div>
          </article>
        ))}
      </div>
    </section>
  )
}

export default MyWorkPage
