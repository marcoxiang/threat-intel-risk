import Link from 'next/link';
import { apiGet } from '../../lib/api';

export default async function RisksPage() {
  let risks: any[] = [];
  let error = '';
  try {
    risks = await apiGet('/risks');
  } catch (err) {
    error = err instanceof Error ? err.message : 'Failed to load risks';
  }

  return (
    <main>
      <h1>Risk Workbench</h1>
      {error ? <div className="card">{error}</div> : null}
      <div className="grid">
        {risks.map((risk) => (
          <div className="card" key={risk.id}>
            <h3>{risk.name}</h3>
            <p>{risk.taxonomy_category}</p>
            <p>Status: <strong>{risk.status}</strong></p>
            <p>Severity: {risk.score?.severity_band || 'N/A'}</p>
            {risk.emerging_signal?.triggered ? <span className="tag emerging">Emerging Risk</span> : null}
            <p>
              <Link href={`/risks/${risk.id}`}>Open review</Link>
            </p>
          </div>
        ))}
      </div>
      {!error && risks.length === 0 ? <div className="card">No risks generated yet.</div> : null}
    </main>
  );
}
