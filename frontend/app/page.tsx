export default function HomePage() {
  return (
    <main className="hero-page">
      <section className="hero-topbar">
        <span className="brand">ThreatIntelRisk</span>
        <div className="hero-links">
          <span>01 Home</span>
          <span>02 Intake</span>
          <span>03 Risks</span>
          <span>04 Dashboard</span>
        </div>
      </section>

      <section className="hero-art" aria-hidden>
        <div className="orb orb-a" />
        <div className="orb orb-b" />
        <div className="orb orb-c" />
        <div className="orb orb-d" />
      </section>

      <section className="hero-copy">
        <h1>Threat intelligence, translated into business risk.</h1>
        <p>
          Ingest intelligence feeds and documents, extract evidence-backed statements, and surface
          emerging risks with trend and novelty signals.
        </p>
      </section>
    </main>
  );
}
