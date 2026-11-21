'use client';

import { useEffect, useState } from 'react';
import InsightsPanel from '../../components/telemetry/InsightsPanel';
import TelemetryMetricsGrid from '../../components/telemetry/TelemetryMetricsGrid';
import DeveloperMode from '../../components/ui/DeveloperMode';
import ErrorState from '../../components/ui/ErrorState';
import { Spinner } from '../../components/ui/LoadingScreen';
import { api } from '../../lib/api-client';
import { DEVELOPER_RECIPES } from '../../lib/developer-recipes';
import { friendlyError } from '../../lib/errors';
import { withMinimumDelay } from '../../lib/loading';
import { canViewTelemetry } from '../../lib/security';
import type { Session } from '../../types/talentos';

export default function TelemetryPage() {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    withMinimumDelay(api.session())
      .then((value) => { if (active) { setSession(value); } })
      .catch((cause: unknown) => { if (active) { setError(friendlyError(cause)); } })
      .finally(() => { if (active) { setLoading(false); } });
    return () => { active = false; };
  }, []);

  if (loading) {
    return <div className="insights-status"><Spinner label="Opening your insights…" /></div>;
  }
  if (error) {
    return <ErrorState title="Insights could not open" message={error} />;
  }

  return (
    <section>
      <div className="page-hero guide-hero insights-hero">
        <div>
          <p className="eyebrow">Activity &amp; insights</p>
          <h1>See what is happening, then decide what to do next.</h1>
          <p className="hero-copy">
            This page reads your own workspace data and turns it into a clear picture of your hiring,
            with suggested next steps you can act on.
          </p>
        </div>
        <div className="hero-art" aria-hidden="true">
          <span className="orbit orbit-one" />
          <span className="orbit orbit-two" />
          <span className="hero-card hero-card-one">Pipeline</span>
          <span className="hero-card hero-card-two">Scores</span>
          <span className="hero-card hero-card-three">Next steps</span>
        </div>
      </div>
      <InsightsPanel session={session} />
      {session && canViewTelemetry(session.role) ? (
        <div className="section-heading">
          <h2>Behind the scenes</h2>
          <p className="muted">A technical activity log for workspace administrators.</p>
        </div>
      ) : null}
      {session && canViewTelemetry(session.role) ? (
        <TelemetryMetricsGrid session={session} />
      ) : null}
      <DeveloperMode {...DEVELOPER_RECIPES.telemetry} />
    </section>
  );
}
