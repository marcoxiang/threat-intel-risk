'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { apiBase, authHeaders } from '../../../lib/api';

export default function RiskDetailPage() {
  const params = useParams<{ id: string }>();
  const riskId = params?.id;
  const [payload, setPayload] = useState<any>(null);
  const [error, setError] = useState('');
  const [note, setNote] = useState('');

  async function refresh() {
    if (!riskId) return;
    try {
      const res = await fetch(`${apiBase()}/risks/${riskId}`, {
        cache: 'no-store',
        headers: authHeaders(),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body?.detail || 'Failed to load risk');
      setPayload(body);
      setError('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load risk');
    }
  }

  useEffect(() => {
    if (riskId) {
      refresh();
    }
  }, [riskId]);

  async function approve() {
    if (!riskId) return;
    const res = await fetch(`${apiBase()}/risks/${riskId}/approve`, {
      method: 'POST',
      headers: authHeaders(),
    });
    if (!res.ok) {
      setError(await res.text());
      return;
    }
    setNote('Risk approved.');
    refresh();
  }

  async function reject() {
    if (!riskId) return;
    const res = await fetch(`${apiBase()}/risks/${riskId}/reject`, {
      method: 'POST',
      headers: authHeaders(),
    });
    if (!res.ok) {
      setError(await res.text());
      return;
    }
    setNote('Risk rejected.');
    refresh();
  }

  async function setEmerging(triggered: boolean) {
    if (!riskId) return;
    const reason = window.prompt('Override reason (required):', 'Analyst override after review');
    if (!reason) return;

    const res = await fetch(`${apiBase()}/risks/${riskId}/override-emerging`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...authHeaders(),
      },
      body: JSON.stringify({ triggered, reason }),
    });
    if (!res.ok) {
      setError(await res.text());
      return;
    }
    setNote('Emerging override saved.');
    refresh();
  }

  const risk = payload?.risk;
  const evidence = payload?.evidence || [];

  return (
    <main>
      <h1>Risk Review</h1>
      {error ? <div className="card">{error}</div> : null}
      {note ? <div className="card">{note}</div> : null}
      {risk ? (
        <>
          <div className="card">
            <h2>{risk.name}</h2>
            <p>Status: <strong>{risk.status}</strong></p>
            <p>Category: {risk.taxonomy_category}</p>
            <p>Threat actor: {risk.threat_actor || 'Unknown'}</p>
            <p>FAIR-lite: {risk.score?.composite_score || 'N/A'} ({risk.score?.severity_band || 'N/A'})</p>
            <p>
              Emerging: <strong>{risk.emerging_signal?.triggered ? 'Yes' : 'No'}</strong>
              {' '}({risk.emerging_signal?.trigger_reason || 'no reason'})
            </p>
            <p>Why care: {risk.statement?.why_care}</p>
            <p>Business impact: {risk.statement?.business_impact}</p>
            <p>Actions: {(risk.statement?.recommended_actions || []).join(' | ')}</p>
            <p>Citations: {(risk.statement?.citation_snippet_ids || []).join(', ') || 'None'}</p>

            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <button onClick={approve}>Approve</button>
              <button className="danger" onClick={reject}>Reject</button>
              <button className="secondary" onClick={() => setEmerging(true)}>Force Emerging</button>
              <button className="secondary" onClick={() => setEmerging(false)}>Unset Emerging</button>
            </div>
          </div>

          <div className="card">
            <h3>Evidence Snippets</h3>
            {evidence.length === 0 ? <p>No evidence snippets linked.</p> : null}
            {evidence.map((snippet: any) => (
              <div key={snippet.id} style={{ marginBottom: 12 }}>
                <p><strong>{snippet.page_or_dom_ref}</strong> | Confidence: {snippet.confidence}</p>
                <p>{snippet.text}</p>
              </div>
            ))}
          </div>
        </>
      ) : (
        <div className="card">Loading...</div>
      )}
    </main>
  );
}
