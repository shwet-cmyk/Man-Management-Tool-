import { useMemo, useState } from 'react'

const dashboardDefinitions = [
  {
    id: 'executive',
    label: 'Executive / Leadership',
    purpose: 'Macro visibility across risk, profitability, backlog, and critical enterprise blockers.',
    tier1Alerts: ['Critical blockers: 11', 'Loss threshold breached: 4 clients', 'Escalations awaiting leadership review: 6'],
    kpis: [
      { label: 'Active Tasks', value: '4,820', bucket: 'workload' },
      { label: 'Pending Jobs', value: '1,164', bucket: 'workload' },
      { label: 'Total Cost', value: '$9.4M', bucket: 'financials' },
      { label: 'Total Billed', value: '$11.1M', bucket: 'financials' },
      { label: 'Total Profit', value: '$1.7M', bucket: 'financials' },
      { label: 'Critical Items', value: '93', bucket: 'risk' },
    ],
    primaryWidgets: [
      { title: 'Profit vs Loss Trend', size: 'medium', tier: 'Tier 3 · trends', drilldown: 'Open finance trend register' },
      { title: 'Critical Issues by Department', size: 'medium', tier: 'Tier 1 · risk', drilldown: 'Open department risk queue' },
      { title: 'Billable vs Non-Billable Split', size: 'medium', tier: 'Tier 2 · financials', drilldown: 'Open billability breakdown' },
    ],
    secondaryWidgets: [
      { title: 'Top Loss-Making Clients', tier: 'Tier 3 · client service' },
      { title: 'Top Delayed Managers', tier: 'Tier 3 · timeliness' },
    ],
    detailColumns: ['Entity', 'Owner', 'Risk', 'Impact', 'Action'],
    detailRows: [
      ['Client C-188', 'Finance Ops', 'Margin < 3%', 'High', 'Open profitability detail'],
      ['Department West', 'Regional Director', 'Critical backlog', 'High', 'Open workload queue'],
      ['Manager M-42', 'Delivery Lead', 'Repeated delays', 'Medium', 'Open governance view'],
    ],
  },
  {
    id: 'operations',
    label: 'Operations Control',
    purpose: 'Daily operational oversight of workload, delays, blocked execution, and intervention queues.',
    tier1Alerts: ['Overdue work: 146', 'Blocked jobs: 39', 'Stale work > 7 days: 58'],
    kpis: [
      { label: 'Due Today', value: '284', bucket: 'timeliness' },
      { label: 'Overdue', value: '146', bucket: 'timeliness' },
      { label: 'Blocked Jobs', value: '39', bucket: 'exceptions' },
      { label: 'Awaiting Acceptance', value: '65', bucket: 'workload' },
      { label: 'Pending Approvals', value: '72', bucket: 'approvals' },
      { label: 'Stale Work', value: '58', bucket: 'risk' },
    ],
    primaryWidgets: [
      { title: 'Workload by Department', size: 'medium', tier: 'Tier 2 · workload', drilldown: 'Open department action queue' },
      { title: 'Job Status Distribution', size: 'medium', tier: 'Tier 2 · workload', drilldown: 'Open status register' },
      { title: 'Transfer Delay Trend', size: 'medium', tier: 'Tier 3 · trends', drilldown: 'Open transfer diagnostics' },
    ],
    secondaryWidgets: [
      { title: 'Action Queue by Manager', tier: 'Tier 3 · productivity' },
      { title: 'Blocked Work by Dependency Type', tier: 'Tier 3 · exceptions' },
    ],
    detailColumns: ['Queue', 'Count', 'Oldest', 'Owner', 'Action'],
    detailRows: [
      ['Acceptance Queue', '65', '3d', 'Operations Manager', 'Open acceptance queue'],
      ['Blocked Transfer Queue', '39', '4d', 'Job Control Team', 'Open blocked transfer list'],
      ['Stale Execution Queue', '58', '9d', 'Regional Leads', 'Open stale-work list'],
    ],
  },
  {
    id: 'task',
    label: 'Task Governance',
    purpose: 'Task flow health, overdue discipline, dependency blockage, and manager accountability.',
    tier1Alerts: ['Tasks with 3+ rollovers: 44', 'Billing blocked tasks: 21', 'Overdue tasks: 118'],
    kpis: [
      { label: 'Active Tasks', value: '3,912', bucket: 'workload' },
      { label: 'Overdue Tasks', value: '118', bucket: 'timeliness' },
      { label: 'Blocked by Jobs', value: '57', bucket: 'exceptions' },
      { label: '3+ Rollovers', value: '44', bucket: 'risk' },
      { label: 'Pending Review', value: '129', bucket: 'approvals' },
      { label: 'Billing Blocked', value: '21', bucket: 'financials' },
    ],
    primaryWidgets: [
      { title: 'Task Status Trend', size: 'medium', tier: 'Tier 3 · trends', drilldown: 'Open status timeline' },
      { title: 'Rollover Distribution', size: 'medium', tier: 'Tier 1 · risk', drilldown: 'Open rollover diagnostics' },
      { title: 'Dependency Delay Breakdown', size: 'medium', tier: 'Tier 3 · exceptions', drilldown: 'Open dependency matrix' },
    ],
    secondaryWidgets: [
      { title: 'Critical Task Leaderboard', tier: 'Tier 3 · risk' },
      { title: 'Manager Backlog Leaderboard', tier: 'Tier 3 · workload' },
    ],
    detailColumns: ['Task', 'Manager', 'Days Overdue', 'Blocker', 'Action'],
    detailRows: [
      ['TASK-2093', 'Manager M-42', '6', 'Dependency wait', 'Open task detail'],
      ['TASK-2217', 'Manager M-17', '9', 'Billing hold', 'Open billing blocker'],
      ['TASK-2321', 'Manager M-09', '4', 'Transfer pending', 'Open transfer chain'],
    ],
  },
  {
    id: 'job',
    label: 'Job Operations',
    purpose: 'Execution movement, pending/completed/billed flow, dependency blockage, and transfer queues.',
    tier1Alerts: ['Overdue jobs: 63', 'Critical jobs: 18', 'Dependency blocked jobs: 32'],
    kpis: [
      { label: 'Pending Jobs', value: '1,164', bucket: 'workload' },
      { label: 'Completed Jobs', value: '3,402', bucket: 'workload' },
      { label: 'Billed Jobs', value: '2,917', bucket: 'financials' },
      { label: 'Overdue Jobs', value: '63', bucket: 'timeliness' },
      { label: 'Critical Jobs', value: '18', bucket: 'risk' },
      { label: 'Awaiting Acceptance', value: '65', bucket: 'approvals' },
    ],
    primaryWidgets: [
      { title: 'Job Status Chart', size: 'medium', tier: 'Tier 2 · workload', drilldown: 'Open status-wise job list' },
      { title: 'Employee Job Load', size: 'medium', tier: 'Tier 2 · productivity', drilldown: 'Open employee capacity view' },
      { title: 'Dependency Blocked Jobs', size: 'medium', tier: 'Tier 1 · exceptions', drilldown: 'Open blocked dependency queue' },
    ],
    secondaryWidgets: [
      { title: 'Transfer Queue Load', tier: 'Tier 3 · workload' },
      { title: 'Delayed Acceptance Leaderboard', tier: 'Tier 3 · timeliness' },
    ],
    detailColumns: ['Job', 'Status', 'Owner', 'Age', 'Action'],
    detailRows: [
      ['JOB-1199', 'Pending', 'Emp E-19', '5d', 'Open pending jobs table'],
      ['JOB-1451', 'Awaiting Acceptance', 'Emp E-07', '3d', 'Open transfer queue'],
      ['JOB-1612', 'Blocked', 'Emp E-04', '8d', 'Open dependency blockers'],
    ],
  },
  {
    id: 'employee',
    label: 'Employee Productivity',
    purpose: 'Workload, utilization, billability, cost vs recovery, and delay accountability.',
    tier1Alerts: ['Low utilization employees: 27', 'Missing timesheets: 31', 'High delay contributors: 14'],
    kpis: [
      { label: 'Total Hours', value: '12,480', bucket: 'productivity' },
      { label: 'Billable Hours', value: '8,620', bucket: 'financials' },
      { label: 'Non-Billable', value: '3,860', bucket: 'financials' },
      { label: 'Employee Cost', value: '$1.24M', bucket: 'financials' },
      { label: 'Recovery', value: '$1.46M', bucket: 'financials' },
      { label: 'Utilization', value: '69%', bucket: 'productivity' },
    ],
    primaryWidgets: [
      { title: 'Hours by Employee', size: 'medium', tier: 'Tier 2 · productivity', drilldown: 'Open employee hour register' },
      { title: 'Cost vs Recovery by Employee', size: 'medium', tier: 'Tier 2 · financials', drilldown: 'Open employee profitability view' },
      { title: 'Delay/Rollover Leaderboard', size: 'medium', tier: 'Tier 1 · risk', drilldown: 'Open delay contributors' },
    ],
    secondaryWidgets: [
      { title: 'Utilization Band Distribution', tier: 'Tier 3 · diagnostics' },
      { title: 'Recovery Gap by Department', tier: 'Tier 3 · trends' },
    ],
    detailColumns: ['Employee', 'Hours', 'Utilization', 'Recovery Gap', 'Action'],
    detailRows: [
      ['Emp E-42', '188h', '54%', '-$2,100', 'Open employee detail'],
      ['Emp E-17', '176h', '61%', '-$1,400', 'Open productivity profile'],
      ['Emp E-09', '121h', '47%', '-$2,980', 'Open coaching plan'],
    ],
  },
  {
    id: 'client',
    label: 'Client / Commercial',
    purpose: 'Client workload, hours, cost, profitability, and service performance risk.',
    tier1Alerts: ['Loss clients this month: 9', 'Client SLA risk: 13 accounts', 'Escalated client issues: 7'],
    kpis: [
      { label: 'Active Clients', value: '148', bucket: 'client service' },
      { label: 'Client Hours', value: '9,410', bucket: 'workload' },
      { label: 'Client Cost', value: '$2.31M', bucket: 'financials' },
      { label: 'Client Billed', value: '$2.76M', bucket: 'financials' },
      { label: 'Client Profit', value: '$450K', bucket: 'financials' },
      { label: 'Loss Clients', value: '9', bucket: 'risk' },
    ],
    primaryWidgets: [
      { title: 'Hours by Client', size: 'medium', tier: 'Tier 2 · workload', drilldown: 'Open client hours register' },
      { title: 'Cost vs Billed by Client', size: 'medium', tier: 'Tier 2 · financials', drilldown: 'Open client margin analysis' },
      { title: 'SLA by Client', size: 'medium', tier: 'Tier 1 · compliance', drilldown: 'Open client SLA detail' },
    ],
    secondaryWidgets: [
      { title: 'Top Profit Clients', tier: 'Tier 3 · financials' },
      { title: 'Top Loss Clients', tier: 'Tier 3 · risk' },
    ],
    detailColumns: ['Client', 'Margin', 'SLA Risk', 'Owner', 'Action'],
    detailRows: [
      ['Client ALPHA', '4.2%', 'High', 'Commercial Lead', 'Open client risk table'],
      ['Client BETA', '-2.8%', 'Medium', 'Account Manager', 'Open recovery action queue'],
      ['Client OMEGA', '1.1%', 'High', 'Service Lead', 'Open SLA intervention'],
    ],
  },
  {
    id: 'finance',
    label: 'Finance / Profitability',
    purpose: 'Cost, billed value, margin, non-billable burden, and loss maker detection.',
    tier1Alerts: ['Low margin tasks: 86', 'Non-billable burden rising: +11%', 'Recovery gap breached: $312K'],
    kpis: [
      { label: 'Direct Cost', value: '$4.8M', bucket: 'financials' },
      { label: 'Overhead', value: '$1.6M', bucket: 'financials' },
      { label: 'Total Cost', value: '$6.4M', bucket: 'financials' },
      { label: 'Total Billed', value: '$7.2M', bucket: 'financials' },
      { label: 'Total Profit', value: '$0.8M', bucket: 'financials' },
      { label: 'Total Loss', value: '$0.3M', bucket: 'risk' },
    ],
    primaryWidgets: [
      { title: 'Margin Trend', size: 'medium', tier: 'Tier 3 · trends', drilldown: 'Open margin trend breakdown' },
      { title: 'Billable vs Non-Billable Cost', size: 'medium', tier: 'Tier 2 · financials', drilldown: 'Open cost composition detail' },
      { title: 'Profitability by Client/Branch', size: 'medium', tier: 'Tier 2 · financials', drilldown: 'Open profitability matrix' },
    ],
    secondaryWidgets: [
      { title: 'Top Low Margin Segments', tier: 'Tier 3 · risk' },
      { title: 'Overhead Contributors', tier: 'Tier 3 · diagnostics' },
    ],
    detailColumns: ['Entity', 'Margin', 'Cost', 'Billed', 'Action'],
    detailRows: [
      ['Task Cluster-17', '2.2%', '$124K', '$127K', 'Open low-margin task table'],
      ['Branch South', '3.1%', '$1.4M', '$1.45M', 'Open branch profitability'],
      ['Client BETA', '-2.8%', '$232K', '$225K', 'Open client financial deep-dive'],
    ],
  },
  {
    id: 'approval',
    label: 'Approval / Escalation',
    purpose: 'Pending, stale, rejected approvals and escalation bottlenecks by manager.',
    tier1Alerts: ['Overdue approvals: 41', 'Escalated items: 16', 'Pending manager actions: 53'],
    kpis: [
      { label: 'Pending Approvals', value: '72', bucket: 'approvals' },
      { label: 'Overdue Approvals', value: '41', bucket: 'timeliness' },
      { label: 'Rejected', value: '19', bucket: 'approvals' },
      { label: 'Escalated', value: '16', bucket: 'risk' },
      { label: 'Pending Manager Actions', value: '53', bucket: 'approvals' },
    ],
    primaryWidgets: [
      { title: 'Approvals by Type', size: 'medium', tier: 'Tier 2 · approvals', drilldown: 'Open type-wise approval queue' },
      { title: 'Approval Aging Trend', size: 'medium', tier: 'Tier 1 · timeliness', drilldown: 'Open approval aging analysis' },
      { title: 'Manager Approval Load', size: 'medium', tier: 'Tier 2 · approvals', drilldown: 'Open manager bottleneck view' },
    ],
    secondaryWidgets: [
      { title: 'Slowest Approval Chains', tier: 'Tier 3 · risk' },
      { title: 'Escalation Frequency by Unit', tier: 'Tier 3 · trends' },
    ],
    detailColumns: ['Approval', 'Age', 'Manager', 'Escalation', 'Action'],
    detailRows: [
      ['APR-991', '5d', 'Manager M-11', 'Level 1', 'Open pending approval queue'],
      ['APR-1032', '8d', 'Manager M-27', 'Level 2', 'Open escalated queue'],
      ['APR-1076', '6d', 'Manager M-42', 'None', 'Open approval detail'],
    ],
  },
  {
    id: 'sla',
    label: 'SLA / Ticket Governance',
    purpose: 'SLA breaches, stale tickets, priority risks, and ticket-to-task conversion health.',
    tier1Alerts: ['Response breaches: 24', 'Closure breaches: 19', 'High-priority unresolved: 34'],
    kpis: [
      { label: 'Open Tickets', value: '312', bucket: 'workload' },
      { label: 'Response Breaches', value: '24', bucket: 'compliance' },
      { label: 'Closure Breaches', value: '19', bucket: 'compliance' },
      { label: 'Stale Tickets', value: '46', bucket: 'timeliness' },
      { label: 'High Priority Unresolved', value: '34', bucket: 'risk' },
      { label: 'Reopened Tickets', value: '27', bucket: 'quality' },
    ],
    primaryWidgets: [
      { title: 'SLA Trend', size: 'medium', tier: 'Tier 3 · trends', drilldown: 'Open SLA timeline view' },
      { title: 'Ticket Priority Distribution', size: 'medium', tier: 'Tier 2 · workload', drilldown: 'Open priority split queue' },
      { title: 'Ticket Status Distribution', size: 'medium', tier: 'Tier 2 · workload', drilldown: 'Open status-wise tickets' },
    ],
    secondaryWidgets: [
      { title: 'Breach Owners Leaderboard', tier: 'Tier 3 · compliance' },
      { title: 'Ticket-to-Task Conversion Quality', tier: 'Tier 3 · diagnostics' },
    ],
    detailColumns: ['Ticket', 'Priority', 'Breach Type', 'Owner', 'Action'],
    detailRows: [
      ['TIC-5541', 'P1', 'Response', 'Support Lead', 'Open breach list'],
      ['TIC-5604', 'P2', 'Closure', 'Ops Coordinator', 'Open stale ticket queue'],
      ['TIC-5639', 'P1', 'Closure', 'Escalation Team', 'Open conversion queue'],
    ],
  },
  {
    id: 'alert',
    label: 'Alert / Automation',
    purpose: 'Notification delivery quality, pending reminder queues, failures, and alert noise control.',
    tier1Alerts: ['Failed alerts: 18', 'Critical alerts open: 29', 'Escalation volume spike: +22%'],
    kpis: [
      { label: 'Alerts Sent Today', value: '2,341', bucket: 'alerts' },
      { label: 'Failed Alerts', value: '18', bucket: 'exceptions' },
      { label: 'Pending Queue', value: '73', bucket: 'workload' },
      { label: 'Critical Alerts Open', value: '29', bucket: 'risk' },
      { label: 'Digest Jobs Pending', value: '11', bucket: 'workload' },
      { label: 'Suppressed Alerts', value: '92', bucket: 'compliance' },
    ],
    primaryWidgets: [
      { title: 'Alert Volume by Type', size: 'medium', tier: 'Tier 2 · trends', drilldown: 'Open alert type analytics' },
      { title: 'Channel Split', size: 'medium', tier: 'Tier 2 · diagnostics', drilldown: 'Open channel-wise delivery report' },
      { title: 'Failure Trend', size: 'medium', tier: 'Tier 1 · risk', drilldown: 'Open failure trend and causes' },
    ],
    secondaryWidgets: [
      { title: 'Repeated Recipient Alert Load', tier: 'Tier 3 · exceptions' },
      { title: 'Noise vs Actionability Ratio', tier: 'Tier 3 · compliance' },
    ],
    detailColumns: ['Alert', 'Channel', 'Failure Cause', 'Owner', 'Action'],
    detailRows: [
      ['ALT-19021', 'Email', 'SMTP timeout', 'Alert Ops', 'Open failed alert log'],
      ['ALT-19057', 'SMS', 'Invalid recipient', 'Alert Ops', 'Open recipient correction queue'],
      ['ALT-19083', 'In-App', 'Template mismatch', 'Platform Team', 'Open template diagnostics'],
    ],
  },
]

const filterFields = [
  'Date Range',
  'Company',
  'Branch',
  'Department',
  'Manager',
  'Employee',
  'Client',
  'Priority',
  'Billable / Non-Billable',
  'Status',
  'Critical Only',
]

function HomePage() {
  const [activeDashboardId, setActiveDashboardId] = useState(dashboardDefinitions[0].id)
  const activeDashboard = useMemo(
    () => dashboardDefinitions.find((dashboard) => dashboard.id === activeDashboardId) || dashboardDefinitions[0],
    [activeDashboardId],
  )

  return (
    <section className="page dashboard-page">
      <div className="dashboard-group-tabs" role="tablist" aria-label="Dashboard groups">
        {dashboardDefinitions.map((dashboard) => (
          <button
            key={dashboard.id}
            type="button"
            role="tab"
            aria-selected={dashboard.id === activeDashboard.id}
            className={`dashboard-group-tab ${dashboard.id === activeDashboard.id ? 'dashboard-group-tab-active' : ''}`}
            onClick={() => setActiveDashboardId(dashboard.id)}
          >
            {dashboard.label}
          </button>
        ))}
      </div>

      <div className="card dashboard-control-card">
        <div className="page-heading">
          <h2>{activeDashboard.label} Dashboard</h2>
          <p>{activeDashboard.purpose}</p>
        </div>
        <div className="dashboard-filters">
          {filterFields.map((field) => (
            <span key={field} className="dashboard-filter-chip">{field}</span>
          ))}
          <span className="dashboard-filter-chip">Saved View / Scope</span>
        </div>
      </div>

      <div className="card">
        <h3 className="card-title">Critical Exception Strip (Tier 1)</h3>
        <div className="alert-strip">
          {activeDashboard.tier1Alerts.map((alert) => (
            <div key={alert} className="alert-strip-item">
              <span className="badge badge-danger">Action Now</span>
              <span>{alert}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="dashboard-kpi-grid">
        {activeDashboard.kpis.slice(0, 6).map((kpi) => (
          <article key={kpi.label} className="card kpi-card">
            <p className="muted">{kpi.label}</p>
            <p className="metric-value">{kpi.value}</p>
            <p className="widget-tier">Bucket: {kpi.bucket}</p>
          </article>
        ))}
      </div>

      <div className="dashboard-widget-grid">
        {activeDashboard.primaryWidgets.map((widget) => (
          <article key={widget.title} className="card widget-card">
            <div className="widget-card-header">
              <h3 className="card-title">{widget.title}</h3>
              <span className="badge badge-warning">{widget.size}</span>
            </div>
            <p className="widget-tier">{widget.tier}</p>
            <button className="btn-text" type="button">{widget.drilldown}</button>
          </article>
        ))}
      </div>

      <div className="dashboard-widget-grid dashboard-widget-grid-secondary">
        {activeDashboard.secondaryWidgets.slice(0, 2).map((widget) => (
          <article key={widget.title} className="card widget-card">
            <h3 className="card-title">{widget.title}</h3>
            <p className="widget-tier">{widget.tier}</p>
            <button className="btn-text" type="button">Open ranked view</button>
          </article>
        ))}
      </div>

      <div className="card">
        <h3 className="card-title">Drill-down Queue (Tier 4)</h3>
        <table className="data-table">
          <thead>
            <tr>
              {activeDashboard.detailColumns.map((column) => (
                <th key={column}>{column}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {activeDashboard.detailRows.map((row) => (
              <tr key={row[0]}>
                {row.map((value) => (
                  <td key={`${row[0]}-${value}`}>{value}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

export default HomePage
