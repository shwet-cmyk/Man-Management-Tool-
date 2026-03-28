function CreateJobPage() {
  return (
    <section className="page">
      <div className="page-heading">
        <h2>Create Job</h2>
        <p className="muted">Job workspace is available in backend workflows and ready for UI wiring.</p>
      </div>
      <div className="page-actions">
        <button className="btn-text" type="button">No actions</button>
      </div>
      <div className="card empty-state">
        <p>No UI fields configured yet for job creation in this frontend shell.</p>
      </div>
    </section>
  )
}

export default CreateJobPage
