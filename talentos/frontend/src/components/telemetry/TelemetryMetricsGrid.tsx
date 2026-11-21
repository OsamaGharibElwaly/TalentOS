'use client';

import { useEffect, useState } from 'react';
import { api } from '../../lib/api-client';
import { friendlyError } from '../../lib/errors';
import { canViewTelemetry } from '../../lib/security';
import type { Session, TelemetrySummary } from '../../types/talentos';
import ErrorState from '../ui/ErrorState';
import { Spinner } from '../ui/LoadingScreen';

export default function TelemetryMetricsGrid({ session }: { session: Session | null }) {
  const [summary, setSummary] = useState<TelemetrySummary | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!canViewTelemetry(session?.role ?? 'viewer')) {
      return;
    }
    api.telemetrySummary()
      .then(setSummary)
      .catch((cause: unknown) => setError(friendlyError(cause)));
  }, [session]);

  if (!canViewTelemetry(session?.role ?? 'viewer')) {
    return <p className="error">Activity insights are available to workspace administrators.</p>;
  }
  if (error) {
    return <ErrorState title="Activity log unavailable" message={error} compact />;
  }
  if (!summary) {
    return <div className="insights-status"><Spinner label="Loading activity…" size={32} /></div>;
  }

  const entries = Object.entries(summary.by_operation);
  return (
    <section className="panel">
      <div className="metrics">
        <div className="metric"><span>Actions recorded</span><strong>{summary.total_operations}</strong></div>
        <div className="metric"><span>Completed</span><strong>{summary.success_count}</strong></div>
        <div className="metric"><span>Needs attention</span><strong>{summary.failure_count}</strong></div>
        <div className="metric"><span>Average response time</span><strong>{summary.average_latency_ms} ms</strong></div>
        <div className="metric">
          <span>Evidence check pass rate</span><strong>{(summary.citation_pass_rate * 100).toFixed(1)}%</strong>
        </div>
      </div>
      <h2>Activity by type</h2>
      <table>
        <thead><tr><th>Action</th><th>Count</th></tr></thead>
        <tbody>
          {entries.map(([operation, count]) => (
            <tr key={operation}><td>{operation}</td><td>{count}</td></tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
