import Link from 'next/link';
import { apiGet } from '../../lib/api';

export default async function EmergingPage() {
  let risks: any[] = [];
  let error = '';
  try {
    risks = await apiGet('/dashboard/emerging');
  } catch (err) {
    error = err instanceof Error ? err.message : 'Failed to load emerging risks';
  }

  return (
    <main>
      <h1>Emerging Risks</h1>
      {error ? <div className="card">{error}</div> : null}
      {risks.map((risk) => (
        <div className="card" key={risk.id}>
          <span className="tag emerging">Emerging Risk</span>
          <h3>{risk.name}</h3>
          <p>Trend ratio: {risk.emerging_signal?.trend_ratio ?? 'n/a'}</p>
          <p>Novelty score: {risk.emerging_signal?.novelty_score ?? 'n/a'}</p>
          <p>Source diversity: {risk.emerging_signal?.source_diversity ?? 'n/a'}</p>
          <Link href={`/risks/${risk.id}`}>Review and override</Link>
        </div>
      ))}
      {!error && risks.length === 0 ? <div className="card">No emerging risks right now.</div> : null}
    </main>
  );
}
