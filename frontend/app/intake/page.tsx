'use client';

import { FormEvent, useState } from 'react';
import { apiBase, authHeaders } from '../../lib/api';

type IntakeFeedback = {
  kind: 'success' | 'error';
  message: string;
  details?: string[];
};

export default function IntakePage() {
  const [feedback, setFeedback] = useState<IntakeFeedback | null>(null);

  function setSuccessMessage(kind: 'PDF' | 'URL', payload: any) {
    const status = payload?.status || 'queued';
    setFeedback({
      kind: 'success',
      message: `${kind} ingest accepted.`,
      details: [
        `Status: ${status}`,
        `Ingestion ID: ${payload?.ingestion_id ?? 'N/A'}`,
        `Source ID: ${payload?.source_document_id ?? 'N/A'}`,
      ],
    });
  }

  async function readResponseBody(res: Response): Promise<any> {
    const raw = await res.text();
    try {
      return JSON.parse(raw);
    } catch {
      return { detail: raw };
    }
  }

  async function submitPdf(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    setFeedback(null);
    try {
      const res = await fetch(`${apiBase()}/sources/pdf`, {
        method: 'POST',
        headers: authHeaders(),
        body: formData,
      });
      const body = await readResponseBody(res);
      if (!res.ok) {
        setFeedback({
          kind: 'error',
          message: 'PDF ingest failed.',
          details: [body?.detail || `HTTP ${res.status}`],
        });
        return;
      }
      setSuccessMessage('PDF', body);
      form.reset();
    } catch (err) {
      setFeedback({
        kind: 'error',
        message: 'PDF ingest failed.',
        details: [err instanceof Error ? err.message : 'Network error'],
      });
    }
  }

  async function submitUrl(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = Object.fromEntries(new FormData(form).entries());
    setFeedback(null);

    const payload = {
      url: data.url,
      title: data.title || null,
      publisher: data.publisher || null,
      notes: data.notes || null,
    };

    try {
      const res = await fetch(`${apiBase()}/sources/url`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...authHeaders(),
        },
        body: JSON.stringify(payload),
      });
      const body = await readResponseBody(res);
      if (!res.ok) {
        setFeedback({
          kind: 'error',
          message: 'URL ingest failed.',
          details: [body?.detail || `HTTP ${res.status}`],
        });
        return;
      }
      setSuccessMessage('URL', body);
      form.reset();
    } catch (err) {
      setFeedback({
        kind: 'error',
        message: 'URL ingest failed.',
        details: [err instanceof Error ? err.message : 'Network error'],
      });
    }
  }

  return (
    <main>
      <h1>Intake</h1>
      <div className="grid">
        <div className="card">
          <h2>Upload PDF Report</h2>
          <form onSubmit={submitPdf}>
            <label htmlFor="file">Report file</label>
            <input id="file" name="file" type="file" accept="application/pdf" required />

            <label htmlFor="title">Title</label>
            <input id="title" name="title" placeholder="Quarterly threat report" />

            <label htmlFor="publisher">Publisher</label>
            <input id="publisher" name="publisher" placeholder="Vendor or research org" />

            <button type="submit">Ingest PDF</button>
          </form>
        </div>

        <div className="card">
          <h2>Submit URL</h2>
          <form onSubmit={submitUrl}>
            <label htmlFor="url">Article URL</label>
            <input id="url" name="url" type="url" placeholder="https://..." required />

            <label htmlFor="url-title">Title (optional)</label>
            <input id="url-title" name="title" placeholder="Threat blog title" />

            <label htmlFor="url-publisher">Publisher (optional)</label>
            <input id="url-publisher" name="publisher" placeholder="Blog/source owner" />

            <label htmlFor="notes">Notes (optional)</label>
            <textarea id="notes" name="notes" rows={4} placeholder="Context for analysts" />

            <button type="submit" className="secondary">Ingest URL</button>
          </form>
        </div>
      </div>

      {feedback ? (
        <div className={`card ${feedback.kind === 'success' ? 'feedback-success' : 'feedback-error'}`}>
          <h3>{feedback.message}</h3>
          {(feedback.details || []).map((line) => (
            <p key={line}>{line}</p>
          ))}
        </div>
      ) : null}
    </main>
  );
}
