'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { api } from '../../lib/api-client';
import { friendlyError } from '../../lib/errors';
import { withMinimumDelay } from '../../lib/loading';
import { friendlyStage } from '../../lib/navigation';
import type { ApplicationStage, HiringInsights, Session } from '../../types/talentos';
import ErrorState from '../ui/ErrorState';
import Icon, { type IconName } from '../ui/Icon';
import { Spinner } from '../ui/LoadingScreen';

const STAGES: readonly ApplicationStage[] = [
  'NEW', 'SCREENED', 'SHORTLISTED', 'INTERVIEW', 'FINAL_REVIEW', 'OFFER', 'REJECTED',
];

const DECISION_ICONS: Readonly<Record<string, IconName>> = {
  indigo: 'users',
  teal: 'chat',
  amber: 'alert',
  rose: 'trophy',
  violet: 'spark',
};

export default function InsightsPanel({ session }: { session: Session | null }) {
  const [insights, setInsights] = useState<HiringInsights | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!session) {
      return;
    }
    let active = true;
    setError('');
    withMinimumDelay(api.insights())
      .then((value) => { if (active) { setInsights(value); } })
      .catch((cause: unknown) => { if (active) { setError(friendlyError(cause)); } });
    return () => { active = false; };
  }, [session]);

  if (!session) {
    return <div className="insights-status"><Spinner label="Checking your workspace…" size={36} /></div>;
  }
  if (error) {
    return <ErrorState title="Insights are not available yet" message={error} compact />;
  }
  if (!insights) {
    return <div className="insights-status"><Spinner label="Reading your hiring activity…" /></div>;
  }

  const maximum = Math.max(1, ...STAGES.map((stage) => insights.by_stage[stage] ?? 0));
  const headline = insights.applications === 0
    ? 'Your pipeline is ready for its first candidates.'
    : `${insights.applications} applications are moving through your pipeline, with ${insights.ready_to_interview.length} strong people ready for the next step.`;

  return (
    <section className="insights" aria-label="Hiring insights">
      <div className="insights-lead panel tone-indigo">
        <div>
          <p className="eyebrow">Decision support</p>
          <h2>What the numbers are telling you</h2>
          <p>{headline}</p>
        </div>
        <span className="insights-lead-icon" aria-hidden="true"><Icon name="chart" size={34} /></span>
      </div>

      <div className="stat-grid">
        <article className="stat-card tone-indigo">
          <span className="stat-icon"><Icon name="users" /></span>
          <span className="stat-value">{insights.candidates.toLocaleString()}</span>
          <span className="stat-label">People in your workspace</span>
        </article>
        <article className="stat-card tone-teal">
          <span className="stat-icon"><Icon name="clipboard" /></span>
          <span className="stat-value">{insights.applications.toLocaleString()}</span>
          <span className="stat-label">Applications in progress</span>
        </article>
        <article className="stat-card tone-amber">
          <span className="stat-icon"><Icon name="chart" /></span>
          <span className="stat-value">{Math.round(insights.average_score * 100)}%</span>
          <span className="stat-label">Average review score</span>
        </article>
        <article className="stat-card tone-rose">
          <span className="stat-icon"><Icon name="alert" /></span>
          <span className="stat-value">{insights.needs_review.toLocaleString()}</span>
          <span className="stat-label">Reviews to double-check</span>
        </article>
      </div>

      <div className="insight-columns">
        <div className="panel">
          <h2>Where candidates stand</h2>
          <p className="muted">A quick read on each stage, from new applicant to offer.</p>
          <div className="insight-rows">
            {STAGES.map((stage) => {
              const count = insights.by_stage[stage] ?? 0;
              return (
                <div className="insight-row" key={stage}>
                  <span>{friendlyStage(stage)}</span>
                  <div className="insight-track"><span style={{ width: `${Math.round((count / maximum) * 100)}%` }} /></div>
                  <strong>{count}</strong>
                </div>
              );
            })}
          </div>
        </div>
        <div className="panel">
          <h2>Skills you see most</h2>
          <p className="muted">The strengths that come up again and again in your resumes.</p>
          {insights.top_skills.length === 0 ? (
            <p className="empty-hint">Add resumes to see common skills.</p>
          ) : (
            <ol className="rank-list">
              {insights.top_skills.map((skill) => (
                <li key={skill.label}>
                  <span>{skill.label}</span>
                  <strong>{Math.round(skill.value)}</strong>
                </li>
              ))}
            </ol>
          )}
        </div>
      </div>

      <div className="panel insight-ready">
        <h2>Ready for the next step</h2>
        <p className="muted">People with strong reviews who are already moving forward.</p>
        {insights.ready_to_interview.length === 0 ? (
          <p className="empty-hint">No strong matches yet. Keep reviewing to build this shortlist.</p>
        ) : (
          <div className="ready-grid">
            {insights.ready_to_interview.map((person) => (
              <article className="ready-card tone-teal" key={person.label}>
                <span className="ready-score">{Math.round(person.value * 100)}%</span>
                <strong>{person.label}</strong>
                <Link href="/candidates" className="step-link">Open review <span aria-hidden="true">→</span></Link>
              </article>
            ))}
          </div>
        )}
      </div>

      <div className="section-heading">
        <h2>What to do next</h2>
        <p className="muted">Suggestions based on the data above. You always make the final call.</p>
      </div>
      <div className="decision-grid">
        {insights.decisions.map((decision) => (
          <Link key={decision.title} href={decision.href} className={`decision-card tone-${decision.tone}`}>
            <span className="decision-icon" aria-hidden="true">
              <Icon name={DECISION_ICONS[decision.tone] ?? 'spark'} />
            </span>
            <strong>{decision.title}</strong>
            <span className="muted">{decision.detail}</span>
            <span className="capability-arrow" aria-hidden="true">→</span>
          </Link>
        ))}
      </div>
    </section>
  );
}
