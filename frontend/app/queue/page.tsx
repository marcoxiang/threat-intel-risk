import { apiGet } from '../../lib/api';

export default async function QueuePage() {
  let jobs: any[] = [];
  let error = '';
  try {
    jobs = await apiGet('/ingestions');
  } catch (err) {
    error = err instanceof Error ? err.message : 'Failed to load queue';
  }

  return (
    <main>
      <h1>Ingestion Queue</h1>
      {error ? <div className="card">{error}</div> : null}
      {jobs.map((job) => (
        <div className="card" key={job.id}>
          <h3>{job.id}</h3>
          <p>Status: <strong>{job.status}</strong></p>
          <p>Source: {job.source_document_id}</p>
          <p>Error: {job.error_message || 'None'}</p>
        </div>
      ))}
      {!error && jobs.length === 0 ? <div className="card">No ingestion jobs yet.</div> : null}
    </main>
  );
}
