import { useMemo, useState } from 'react'

const NAV_ITEMS = [
  'API Dashboard',
  'API Applications',
  'API Keys',
  'API Scopes',
  'Endpoint Registry',
  'Webhooks',
  'API Logs',
  'Usage & Rate Limits',
  'API Settings',
  'API Documentation',
]

const kpis = [
  { label: 'Active API Apps', value: 42 },
  { label: 'Active API Keys', value: 118 },
  { label: 'Requests Today', value: '1.24M' },
  { label: 'Failed Requests Today', value: '4,920' },
  { label: 'Active Webhooks', value: 65 },
  { label: 'Rate Limit Violations Today', value: 73 },
]

const applications = [
  { id: 1, name: 'Finance ERP Connector', code: 'APP-FIN-01', type: 'Internal System', owner: 'Anita Rao', env: 'Production', status: 'Active', lastUsed: '2026-03-28 11:12', webhook: 'Yes', scopes: 14, createdOn: '2025-12-04' },
  { id: 2, name: 'Field Ops Mobile Gateway', code: 'APP-OPS-12', type: 'Internal App', owner: 'Rahul Shah', env: 'UAT', status: 'Active', lastUsed: '2026-03-28 09:05', webhook: 'Yes', scopes: 9, createdOn: '2026-01-19' },
  { id: 3, name: 'Partner Data Bridge', code: 'APP-PAR-02', type: 'Partner', owner: 'Priya Mehta', env: 'Production', status: 'Suspended', lastUsed: '2026-03-25 20:42', webhook: 'No', scopes: 5, createdOn: '2025-11-16' },
]

const keys = [
  { id: 'KEY-01', app: 'Finance ERP Connector', status: 'Active', env: 'Production', createdOn: '2026-01-01', expiresOn: '2026-06-30', lastUsed: '2026-03-28 11:10', revokedOn: '-', rotationDue: '2026-05-31' },
  { id: 'KEY-02', app: 'Field Ops Mobile Gateway', status: 'Active', env: 'UAT', createdOn: '2026-02-12', expiresOn: '2026-04-12', lastUsed: '2026-03-27 17:21', revokedOn: '-', rotationDue: '2026-04-05' },
  { id: 'KEY-03', app: 'Partner Data Bridge', status: 'Revoked', env: 'Production', createdOn: '2025-12-11', expiresOn: '2026-03-11', lastUsed: '2026-03-11 03:21', revokedOn: '2026-03-12', rotationDue: '-' },
]

const scopes = [
  { code: 'API_APP_VIEW', name: 'View API Applications', module: 'API', type: 'read', sensitive: 'No', status: 'Active' },
  { code: 'API_KEY_GENERATE', name: 'Generate API Key', module: 'API', type: 'admin', sensitive: 'Yes', status: 'Active' },
  { code: 'API_LOG_EXPORT', name: 'Export API Logs', module: 'API', type: 'write', sensitive: 'Yes', status: 'Active' },
]

const endpoints = [
  { code: 'API_APPS_LIST', path: '/api/v1/api-apps', method: 'GET', module: 'API Admin', version: 'v1', scope: 'API_APP_VIEW', status: 'Active', deprecated: 'No', updated: '2026-03-21' },
  { code: 'API_KEYS_REVOKE', path: '/api/v1/api-apps/{id}/keys/{keyId}/revoke', method: 'POST', module: 'API Admin', version: 'v1', scope: 'API_KEY_REVOKE', status: 'Active', deprecated: 'No', updated: '2026-03-24' },
  { code: 'API_DOCS_VIEW', path: '/api/v1/api-docs', method: 'GET', module: 'API Admin', version: 'v1', scope: 'API_DOCS_VIEW', status: 'Active', deprecated: 'No', updated: '2026-03-26' },
]

const webhooks = [
  { id: 'WH-11', name: 'Invoice Event Relay', app: 'Finance ERP Connector', event: 'billing.invoice.created', url: 'https://internal.iesl/finance-webhook', status: 'Active', lastDelivery: '2026-03-28 10:32', lastStatus: 'Success', retryPolicy: '3x exp backoff', failCount: 0 },
  { id: 'WH-12', name: 'Task Escalation Webhook', app: 'Field Ops Mobile Gateway', event: 'task.escalated', url: 'https://internal.iesl/tasks-hook', status: 'Paused', lastDelivery: '2026-03-27 13:01', lastStatus: 'Failed', retryPolicy: '5x linear', failCount: 6 },
]

const logs = [
  { ts: '2026-03-28 11:25:11', app: 'Finance ERP Connector', method: 'POST', endpoint: '/api/v1/approvals/233/approve', status: 200, outcome: 'Success', latency: '201ms', traceId: 'trc_18s0', entity: 'Approval#233', error: '-' },
  { ts: '2026-03-28 11:24:58', app: 'Partner Data Bridge', method: 'GET', endpoint: '/api/v1/reports/job-profitability', status: 429, outcome: 'Fail', latency: '11ms', traceId: 'trc_18rz', entity: 'Report#job-profitability', error: 'Rate limit exceeded' },
  { ts: '2026-03-28 11:24:41', app: 'Field Ops Mobile Gateway', method: 'POST', endpoint: '/api/v1/webhooks/WH-12/test', status: 401, outcome: 'Fail', latency: '28ms', traceId: 'trc_18rv', entity: 'Webhook#WH-12', error: 'Invalid key signature' },
]

const usageRows = [
  { subject: 'Finance ERP Connector', requests: '642k', failRate: '0.7%', p95: '312ms', limit: '80%' },
  { subject: 'Field Ops Mobile Gateway', requests: '412k', failRate: '1.8%', p95: '411ms', limit: '61%' },
  { subject: 'Partner Data Bridge', requests: '186k', failRate: '4.4%', p95: '589ms', limit: '93%' },
]

function Badge({ value }) {
  return <span className={`status-badge status-${String(value).toLowerCase().replace(/\s+/g, '-')}`}>{value}</span>
}

function ModuleToolbar({ title, actionLabel }) {
  return (
    <header className="card api-module-toolbar">
      <div>
        <p className="api-breadcrumb">Admin / Integrations / API Module / {title}</p>
        <h2>{title}</h2>
      </div>
      <div className="api-toolbar-actions">
        <input placeholder="Search" aria-label={`${title} search`} />
        <select defaultValue="all">
          <option value="all">All statuses</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
          <option value="failed">Failed only</option>
        </select>
        <button className="btn-secondary" type="button">Export</button>
        {actionLabel ? <button className="btn-primary" type="button">{actionLabel}</button> : null}
      </div>
    </header>
  )
}

function ApiModulePage() {
  const [activeNav, setActiveNav] = useState('API Dashboard')
  const [drawer, setDrawer] = useState(null)
  const [settings, setSettings] = useState({
    auth: 'API Key + IP allowlist',
    keyRotationDays: 90,
    rateLimitPerMinute: 600,
    webhookRetries: 5,
    retentionDays: 180,
    docsExposure: 'Internal only',
    tryItOut: false,
  })

  const docsModules = useMemo(
    () => ['API Admin', 'Users & Roles', 'Masters', 'Tickets', 'Tasks', 'Jobs', 'Timesheets', 'Projects', 'Approvals', 'Alerts', 'Goals', 'Intake', 'Launches', 'Resource Planning', 'Dashboards', 'Reports'],
    [],
  )

  const renderDashboard = () => (
    <>
      <div className="api-kpi-grid">
        {kpis.map((kpi) => (
          <article key={kpi.label} className="card api-kpi-card">
            <p>{kpi.label}</p>
            <strong>{kpi.value}</strong>
          </article>
        ))}
      </div>
      <div className="api-widgets-grid">
        {['API traffic trend', 'Top API apps by usage', 'Top failing endpoints', 'Recent auth failures', 'Recent webhook failures', 'Scope usage distribution', 'Slow endpoint summary'].map((title) => (
          <section key={title} className="card api-widget">
            <h3>{title}</h3>
            <p className="muted">Operational widget with module, app, and time filters.</p>
            <div className="api-mini-chart" />
          </section>
        ))}
      </div>
      <section className="card">
        <div className="section-head-inline">
          <h3>Recent API Activity</h3>
          <button type="button" className="btn-text">View full logs</button>
        </div>
        <table className="dense-table">
          <thead><tr><th>Timestamp</th><th>App</th><th>Endpoint</th><th>Status</th><th>Latency</th><th>Trace</th><th /></tr></thead>
          <tbody>
            {logs.map((log) => (
              <tr key={log.traceId}>
                <td>{log.ts}</td><td>{log.app}</td><td>{log.endpoint}</td><td><Badge value={log.outcome} /></td><td>{log.latency}</td><td>{log.traceId}</td>
                <td><button type="button" className="btn-text" onClick={() => setDrawer(log)}>View</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  )

  const renderTablePage = (title, rows, columns, actionLabel) => (
    <>
      <ModuleToolbar title={title} actionLabel={actionLabel} />
      <section className="card">
        <table className="dense-table">
          <thead>
            <tr>
              {columns.map((col) => <th key={col.key}>{col.label}</th>)}
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, idx) => (
              <tr key={row.id || row.code || row.ts || idx}>
                {columns.map((col) => (
                  <td key={col.key}>
                    {col.key === 'status' || col.key === 'outcome' || col.key === 'deprecated' ? <Badge value={row[col.key]} /> : row[col.key]}
                  </td>
                ))}
                <td>
                  <div className="table-actions">
                    <button type="button" className="btn-text" onClick={() => setDrawer(row)}>View</button>
                    <button type="button" className="btn-text">Edit</button>
                    <button type="button" className="btn-text">Audit</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  )

  return (
    <section className="page api-module-page">
      <div className="api-module-layout">
        <aside className="card api-subnav">
          <h3>API Module</h3>
          <p className="muted">Integration control center</p>
          <div className="api-subnav-list" role="tablist" aria-label="API module sections">
            {NAV_ITEMS.map((item) => (
              <button key={item} className={`api-subnav-btn ${activeNav === item ? 'api-subnav-btn-active' : ''}`} type="button" onClick={() => setActiveNav(item)}>
                {item}
              </button>
            ))}
          </div>
        </aside>

        <div className="api-content">
          {activeNav === 'API Dashboard' && (
            <>
              <ModuleToolbar title="API Dashboard" actionLabel="Create API Application" />
              {renderDashboard()}
              <section className="card warning-banner">
                <strong>Security Notice:</strong> 3 applications are within 7 days of key expiry and 2 endpoints exceeded failure threshold.
              </section>
            </>
          )}

          {activeNav === 'API Applications' && renderTablePage('API Applications', applications, [
            { key: 'name', label: 'App Name' }, { key: 'code', label: 'App Code' }, { key: 'type', label: 'Consumer Type' }, { key: 'owner', label: 'Owner' }, { key: 'env', label: 'Environment' }, { key: 'status', label: 'Status' }, { key: 'lastUsed', label: 'Last Used' }, { key: 'webhook', label: 'Webhook Enabled' }, { key: 'scopes', label: 'Scope Count' }, { key: 'createdOn', label: 'Created On' },
          ], 'Add API Application')}

          {activeNav === 'API Keys' && (
            <>
              {renderTablePage('API Keys', keys, [
                { key: 'app', label: 'App Name' }, { key: 'id', label: 'Key Public ID' }, { key: 'status', label: 'Status' }, { key: 'env', label: 'Environment' }, { key: 'createdOn', label: 'Created On' }, { key: 'expiresOn', label: 'Expires On' }, { key: 'lastUsed', label: 'Last Used' }, { key: 'revokedOn', label: 'Revoked On' }, { key: 'rotationDue', label: 'Rotation Due' },
              ], 'Generate API Key')}
              <section className="card warning-banner"><strong>Warning:</strong> Regenerating or revoking keys immediately impacts integrations.</section>
            </>
          )}

          {activeNav === 'API Scopes' && (
            <>
              {renderTablePage('API Scopes', scopes, [
                { key: 'code', label: 'Scope Code' }, { key: 'name', label: 'Scope Name' }, { key: 'module', label: 'Module' }, { key: 'type', label: 'Type' }, { key: 'sensitive', label: 'Sensitive Flag' }, { key: 'status', label: 'Active Status' },
              ], 'Assign Scopes')}
              <section className="card">
                <h3>Scope Assignment Matrix</h3>
                <div className="scope-matrix">
                  <div className="matrix-row matrix-head"><span>Scope</span><span>Finance ERP</span><span>Field Ops</span><span>Partner Bridge</span></div>
                  {scopes.map((scope) => (
                    <div key={scope.code} className="matrix-row"><span>{scope.code}</span><span>✓</span><span>{scope.code === 'API_LOG_EXPORT' ? '—' : '✓'}</span><span>—</span></div>
                  ))}
                </div>
              </section>
            </>
          )}

          {activeNav === 'Endpoint Registry' && renderTablePage('Endpoint Registry', endpoints, [
            { key: 'code', label: 'Endpoint Code' }, { key: 'path', label: 'Path' }, { key: 'method', label: 'Method' }, { key: 'module', label: 'Module' }, { key: 'version', label: 'Version' }, { key: 'scope', label: 'Required Scope' }, { key: 'status', label: 'Status' }, { key: 'deprecated', label: 'Deprecated' }, { key: 'updated', label: 'Last Updated' },
          ], 'Register Endpoint')}

          {activeNav === 'Webhooks' && (
            <>
              {renderTablePage('Webhooks', webhooks, [
                { key: 'name', label: 'Webhook Name' }, { key: 'app', label: 'App Name' }, { key: 'event', label: 'Event Code' }, { key: 'url', label: 'Target URL' }, { key: 'status', label: 'Status' }, { key: 'lastDelivery', label: 'Last Delivery' }, { key: 'lastStatus', label: 'Last Status' }, { key: 'retryPolicy', label: 'Retry Policy' }, { key: 'failCount', label: 'Fail Count' },
              ], 'Create Webhook')}
              <section className="card warning-banner"><strong>Alert:</strong> 1 webhook has repeated delivery failures above configured threshold.</section>
            </>
          )}

          {activeNav === 'API Logs' && renderTablePage('API Logs', logs, [
            { key: 'ts', label: 'Timestamp' }, { key: 'app', label: 'App Name' }, { key: 'method', label: 'Method' }, { key: 'endpoint', label: 'Endpoint' }, { key: 'status', label: 'Status Code' }, { key: 'outcome', label: 'Success/Fail' }, { key: 'latency', label: 'Response Time' }, { key: 'traceId', label: 'Trace ID' }, { key: 'entity', label: 'Affected Entity' }, { key: 'error', label: 'Error Summary' },
          ], 'Export Logs')}

          {activeNav === 'Usage & Rate Limits' && (
            <>
              <ModuleToolbar title="Usage & Rate Limits" actionLabel="Adjust Rate Limits" />
              <div className="api-widgets-grid">
                {['Requests by day', 'Requests by app', 'Requests by module', 'Read vs write split', '4xx/5xx trends', 'Rate-limit violations', 'Slowest endpoints'].map((title) => (
                  <section key={title} className="card api-widget"><h3>{title}</h3><div className="api-mini-chart" /></section>
                ))}
              </div>
              <section className="card">
                <h3>Apps Closest to Limit</h3>
                <table className="dense-table"><thead><tr><th>App</th><th>Requests</th><th>Fail Rate</th><th>P95 Latency</th><th>Limit Utilization</th></tr></thead><tbody>{usageRows.map((r) => <tr key={r.subject}><td>{r.subject}</td><td>{r.requests}</td><td>{r.failRate}</td><td>{r.p95}</td><td>{r.limit}</td></tr>)}</tbody></table>
              </section>
            </>
          )}

          {activeNav === 'API Settings' && (
            <>
              <ModuleToolbar title="API Settings" actionLabel="Save Settings" />
              <section className="card settings-grid">
                <label>Authentication<select value={settings.auth} onChange={(event) => setSettings((curr) => ({ ...curr, auth: event.target.value }))}><option>API Key + IP allowlist</option><option>API Key only</option><option>API Key + Signature</option></select></label>
                <label>Key Rotation (days)<input type="number" value={settings.keyRotationDays} onChange={(event) => setSettings((curr) => ({ ...curr, keyRotationDays: Number(event.target.value) }))} /></label>
                <label>Rate Limit / min<input type="number" value={settings.rateLimitPerMinute} onChange={(event) => setSettings((curr) => ({ ...curr, rateLimitPerMinute: Number(event.target.value) }))} /></label>
                <label>Webhook Retries<input type="number" value={settings.webhookRetries} onChange={(event) => setSettings((curr) => ({ ...curr, webhookRetries: Number(event.target.value) }))} /></label>
                <label>Retention (days)<input type="number" value={settings.retentionDays} onChange={(event) => setSettings((curr) => ({ ...curr, retentionDays: Number(event.target.value) }))} /></label>
                <label>Docs Exposure<select value={settings.docsExposure} onChange={(event) => setSettings((curr) => ({ ...curr, docsExposure: event.target.value }))}><option>Internal only</option><option>Admin only</option><option>Disabled</option></select></label>
                <label className="toggle-row">Try-It-Out enabled<input type="checkbox" checked={settings.tryItOut} onChange={(event) => setSettings((curr) => ({ ...curr, tryItOut: event.target.checked }))} /></label>
              </section>
            </>
          )}

          {activeNav === 'API Documentation' && (
            <>
              <ModuleToolbar title="API Documentation" actionLabel="Export OpenAPI" />
              <section className="card docs-layout">
                <aside>
                  <h3>Modules</h3>
                  {docsModules.map((module) => <button key={module} type="button" className="btn-text docs-link">{module}</button>)}
                </aside>
                <div>
                  <h3>Endpoint Detail</h3>
                  <p className="muted">Includes auth requirements, required scopes, request/response schemas, error model, and examples.</p>
                  <pre className="docs-snippet">GET /api/v1/api-apps/{{id}}/keys</pre>
                  <pre className="docs-snippet">x-api-key: &lt;api_key&gt;\nX-Scope: API_KEY_VIEW</pre>
                </div>
              </section>
            </>
          )}
        </div>
      </div>

      {drawer && (
        <aside className="side-drawer" role="dialog" aria-label="Detail drawer">
          <header>
            <h3>Detail / Audit View</h3>
            <button type="button" className="btn-text" onClick={() => setDrawer(null)}>Close</button>
          </header>
          <pre>{JSON.stringify(drawer, null, 2)}</pre>
          <div className="drawer-audit">
            <h4>Audit Trail</h4>
            <ul>
              <li>2026-03-28 11:27 — Viewed by OPS Admin</li>
              <li>2026-03-27 19:03 — Metadata edited by Integration Admin</li>
              <li>2026-03-21 14:34 — Created by System Seeder</li>
            </ul>
          </div>
        </aside>
      )}
    </section>
  )
}

export default ApiModulePage
