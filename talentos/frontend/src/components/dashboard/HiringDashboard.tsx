'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { api } from '../../lib/api-client';
import { withMinimumDelay } from '../../lib/loading';
import { canViewTelemetry } from '../../lib/security';
import Icon from '../ui/Icon';
import type { ApplicationStage, CandidateReview, Job, Session } from '../../types/talentos';

const STAGES: readonly { stage: ApplicationStage; label: string; tone: string }[] = [
  { stage: 'NEW', label: 'New applicants', tone: 'indigo' },
  { stage: 'SCREENED', label: 'Screening', tone: 'cyan' },
  { stage: 'SHORTLISTED', label: 'Shortlisted', tone: 'teal' },
  { stage: 'INTERVIEW', label: 'Interviewing', tone: 'amber' },
  { stage: 'FINAL_REVIEW', label: 'Final review', tone: 'violet' },
  { stage: 'OFFER', label: 'Offers', tone: 'rose' },
];

const emptyStages = (): Record<ApplicationStage, number> => ({
  NEW: 0, SCREENED: 0, SHORTLISTED: 0, INTERVIEW: 0, FINAL_REVIEW: 0, OFFER: 0, REJECTED: 0,
});

interface Numbers {
  roles: number;
  people: number;
  interviewing: number;
  offers: number;
  actions: number | null;
  stages: Record<ApplicationStage, number>;
}

export default function HiringDashboard() {
  const [numbers, setNumbers] = useState<Numbers | null>(null);

  useEffect(() => {
    let active = true;
    withMinimumDelay(Promise.all([
      api.listJobs().catch(() => [] as Job[]),
      api.listCandidates().catch(() => [] as CandidateReview[]),
      api.session().catch(() => null as Session | null),
    ])).then(async ([jobs, candidates, session]) => {
      const stages = emptyStages();
      candidates.forEach((candidate) => {
        candidate.applications.forEach((application) => {
          stages[application.stage] += 1;
        });
      });
      let actions: number | null = null;
      if (session && canViewTelemetry(session.role)) {
        const summary = await api.telemetrySummary().catch(() => null);
        actions = summary?.total_operations ?? null;
      }
      if (active) {
        setNumbers({
          roles: jobs.length,
          people: candidates.length,
          interviewing: stages.INTERVIEW,
          offers: stages.OFFER,
          actions,
          stages,
        });
      }
    });
    return () => { active = false; };
  }, []);

  if (!numbers) {
    return (
      <section className="dashboard" aria-busy="true" aria-label="Hiring dashboard">
        <div className="stat-grid">
          {[0, 1, 2, 3].map((index) => (
            <div className="stat-card skeleton-card" key={index}>
              <span className="skeleton" style={{ width: 96, height: 12 }} />
              <span className="skeleton" style={{ width: 64, height: 34 }} />
              <span className="skeleton" style={{ width: 120, height: 10 }} />
            </div>
          ))}
        </div>
      </section>
    );
  }

  const total = STAGES.reduce((sum, item) => sum + numbers.stages[item.stage], 0);
  const max = Math.max(1, ...STAGES.map((item) => numbers.stages[item.stage]));

  return (
    <section className="dashboard" aria-label="Hiring dashboard">
      <div className="stat-grid">
        <article className="stat-card tone-indigo">
          <span className="stat-icon"><Icon name="briefcase" /></span>
          <span className="stat-value">{numbers.roles.toLocaleString()}</span>
          <span className="stat-label">Roles you are hiring for</span>
        </article>
        <article className="stat-card tone-teal">
          <span className="stat-icon"><Icon name="users" /></span>
          <span className="stat-value">{numbers.people.toLocaleString()}</span>
          <span className="stat-label">People in your workspace</span>
        </article>
        <article className="stat-card tone-amber">
          <span className="stat-icon"><Icon name="chat" /></span>
          <span className="stat-value">{numbers.interviewing.toLocaleString()}</span>
          <span className="stat-label">Interviews under way</span>
        </article>
        <article className="stat-card tone-rose">
          <span className="stat-icon"><Icon name="trophy" /></span>
          <span className="stat-value">{numbers.offers.toLocaleString()}</span>
          <span className="stat-label">Offers made</span>
        </article>
        {numbers.actions === null ? null : (
          <article className="stat-card tone-violet">
            <span className="stat-icon"><Icon name="chart" /></span>
            <span className="stat-value">{numbers.actions.toLocaleString()}</span>
            <span className="stat-label">Actions recorded</span>
          </article>
        )}
      </div>

      <div className="panel pipeline-panel">
        <div className="panel-heading">
          <div>
            <h2>Where candidates stand</h2>
            <p className="muted">A living view of your hiring pipeline, from first application to offer.</p>
          </div>
          <span className="pipeline-total">{total} in process</span>
        </div>
        <div className="pipeline">
          {STAGES.map((item) => {
            const count = numbers.stages[item.stage];
            return (
              <div className={`pipeline-step tone-${item.tone}`} key={item.stage}>
                <div className="pipeline-bar-track">
                  <span className="pipeline-bar" style={{ width: `${Math.round((count / max) * 100)}%` }} />
                </div>
                <strong>{count}</strong>
                <span>{item.label}</span>
              </div>
            );
          })}
        </div>
        {total === 0 ? (
          <p className="empty-hint">
            Nothing in the pipeline yet. <Link href="/jobs">Describe a role</Link> and{' '}
            <Link href="/ingestion">add a resume</Link> to begin.
          </p>
        ) : null}
      </div>
    </section>
  );
}
