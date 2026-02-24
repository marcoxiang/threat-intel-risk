import { apiGet } from '../../lib/api';

export default async function DashboardPage() {
  let data: any = null;
  let error = '';
  try {
    data = await apiGet('/dashboard/summary');
  } catch (err) {
    error = err instanceof Error ? err.message : 'Failed to load summary';
  }

  return (
    <main>
      <h1>Executive Dashboard</h1>
      {error ? <div className="card">{error}</div> : null}
      {data ? (
        <>
          <div className="grid">
            <div className="card"><div className="kpi">{data.total_risks}</div><p>Total risks</p></div>
            <div className="card"><div className="kpi">{data.approved_risks}</div><p>Approved</p></div>
            <div className="card"><div className="kpi">{data.draft_risks}</div><p>Draft</p></div>
            <div className="card"><div className="kpi">{data.emerging_risks}</div><p>Emerging</p></div>
          </div>

          <div className="card">
            <h2>Severity Breakdown</h2>
            {Object.entries(data.severity_breakdown || {}).map(([key, value]) => (
              <p key={key}>{key}: {String(value)}</p>
            ))}
          </div>
        </>
      ) : null}
    </main>
  );
}
