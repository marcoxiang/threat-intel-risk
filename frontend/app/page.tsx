export default function HomePage() {
  return (
    <main>
      <div className="card">
        <h1>ThreatIntelRisk v1</h1>
        <p>
          Ingest threat intelligence from PDFs and websites, generate business-focused risk statements,
          and automatically surface <strong>Emerging Risks</strong> using trend and novelty signals.
        </p>
      </div>
      <div className="grid">
        <div className="card">
          <h3>Strict Citation Policy</h3>
          <p>Analyst approvals are blocked unless key statements are backed by evidence snippets.</p>
        </div>
        <div className="card">
          <h3>FAIR-lite Scoring</h3>
          <p>Likelihood and loss factors are normalized into a 0-100 business risk score.</p>
        </div>
        <div className="card">
          <h3>Analyst Review Gate</h3>
          <p>Risk statements are drafted by AI and must be approved or rejected by reviewers/admins.</p>
        </div>
      </div>
    </main>
  );
}
