import type { Metadata } from 'next';
import Link from 'next/link';
import './globals.css';

export const metadata: Metadata = {
  title: 'ThreatIntelRisk',
  description: 'Threat intel ingestion and business risk statement workbench',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="shell">
          <nav className="nav">
            <Link href="/">Home</Link>
            <Link href="/intake">Intake</Link>
            <Link href="/queue">Ingestion Queue</Link>
            <Link href="/risks">Risk Workbench</Link>
            <Link href="/emerging">Emerging Risks</Link>
            <Link href="/dashboard">Executive Dashboard</Link>
          </nav>
          {children}
        </div>
      </body>
    </html>
  );
}
