'use client';
import { friendlyError } from '../../lib/errors';

import { memo, useCallback, useMemo, useState } from 'react';
import { api, type CriterionEvaluationInput } from '../../lib/api-client';
import { friendlyStage } from '../../lib/navigation';
import { maskEmail, maskPhone } from '../../lib/security';
import SafeText from '../ui/SafeText';
import type {
  ApplicationStage,
  ApplicationSummary,
  CandidateReview,
  Job,
} from '../../types/talentos';

const NEXT_STAGES: Readonly<Record<ApplicationStage, readonly ApplicationStage[]>> = {
  NEW: ['SCREENED'],
  SCREENED: ['SHORTLISTED'],
  SHORTLISTED: ['INTERVIEW'],
  INTERVIEW: ['FINAL_REVIEW'],
  FINAL_REVIEW: ['OFFER', 'REJECTED'],
  OFFER: [],
  REJECTED: [],
};

function SplitEvidenceViewer({
  candidate,
  jobs,
}: {
  candidate: CandidateReview;
  jobs: Job[];
}) {
  const [applicationId, setApplicationId] = useState(candidate.applications[0]?.id ?? '');
  const [blind, setBlind] = useState(false);
  const [reason, setReason] = useState('');
  const [confirm, setConfirm] = useState(false);
  const [message, setMessage] = useState('');
  const [scores, setScores] = useState<Record<string, string>>({});

  const selected: ApplicationSummary | undefined = useMemo(
    () => candidate.applications.find((item) => item.id === applicationId),
    [candidate.applications, applicationId],
  );
  const job = useMemo(
    () => jobs.find((item) => item.id === selected?.job_id),
    [jobs, selected?.job_id],
  );
  const scoring = selected?.scoring ?? null;
  const verifiedQuotes = useMemo(
    () => scoring?.criterion_scores.flatMap((item) =>
      item.citations.filter((citation) => citation.verified).map((citation) => citation.quote),
    ) ?? [],
    [scoring],
  );

  const setCriterion = (criterionId: string, value: string) => {
    setScores((current) => ({ ...current, [criterionId]: value }));
  };

  const runScoring = useCallback(async () => {
    if (!selected) {
      return;
    }
    const evaluations: CriterionEvaluationInput[] = (job?.rubric ?? []).map((criterion) => ({
      criterion_id: criterion.id,
      score: Number(scores[criterion.id] ?? 0),
      rationale: '',
      citations: (scores[`${criterion.id}:citations`] ?? '').split('\n').filter(Boolean),
      confidence: 1,
    }));
    try {
      await api.scoreApplication({ application_id: selected.id, evaluations, blind_mode: blind });
      setMessage('Scorecard recomputed with citation verification.');
    } catch (cause: unknown) {
      setMessage(friendlyError(cause));
    }
  }, [selected, job?.rubric, blind, scores]);

  const transition = useCallback(async (toStage: ApplicationStage) => {
    if (!selected) {
      return;
    }
    try {
      const updated = await api.transitionApplication(selected.id, {
        to_stage: toStage,
        reason,
        confirm,
      });
      setMessage(`Moved to ${friendlyStage(updated.stage)}.`);
      setConfirm(false);
      setReason('');
    } catch (cause: unknown) {
      setMessage(friendlyError(cause));
    }
  }, [selected, reason, confirm]);

  const name = blind ? '[redacted]' : candidate.full_name;
  const email = blind ? maskEmail(candidate.email) : candidate.email;
  const phone = blind ? maskPhone(candidate.phone) : candidate.phone;
  const nextStages = selected ? NEXT_STAGES[selected.stage] : [];

  return (
    <div className="split">
      <section className="panel">
        <h2>{name}</h2>
        <p className="muted">{email} · {phone}</p>
        <p className="muted">
          {candidate.skills.join(', ')} · {candidate.total_experience_years} years
          {candidate.pii_masked ? ' · PII masked by policy' : ''}
        </p>
        <label htmlFor="application-select">Application</label>
        <select
          id="application-select"
          value={applicationId}
          onChange={(event) => setApplicationId(event.target.value)}
        >
          {candidate.applications.map((item) => (
            <option key={item.id} value={item.id}>
              {item.job_id} — {friendlyStage(item.stage)}
            </option>
          ))}
        </select>
        <h3>Resume lines you can quote</h3>
        <div className="resume-text">
          <SafeText text={candidate.raw_text} highlight={verifiedQuotes} />
        </div>
      </section>

      <section className="panel">
        <h2>Review by skill</h2>
        <label className="muted">
          <input
            type="checkbox"
            checked={blind}
            onChange={(event) => setBlind(event.target.checked)}
            style={{ width: 'auto', marginRight: 8 }}
          />
          Hide personal details while reviewing
        </label>
        <p>
          Overall score:{' '}
          <strong>{scoring ? `${(scoring.composite_score * 100).toFixed(0)}%` : '—'}</strong>
        </p>
        <ul className="list">
          {scoring?.criterion_scores.map((item) => (
            <li key={item.criterion_id}>
              <strong>{item.criterion_name}</strong> — {item.score} (weight {(item.weight * 100).toFixed(0)}%)
              <div className="muted">{item.rationale || 'No note yet: no matching line was found in the resume.'}</div>
              {item.citations.map((citation, index) => (
                <span
                  key={`${citation.quote}-${index}`}
                  className={citation.verified ? 'badge ok' : 'badge bad'}
                  title={citation.quote}
                >
                  {citation.verified ? 'matches resume' : 'needs checking'}
                </span>
              ))}
            </li>
          ))}
        </ul>
        <h3>Things to check</h3>
        <ul className="list">
          {scoring?.gaps_and_probes.map((gap, index) => (
            <li key={`${gap.kind}-${gap.criterion_id}-${index}`}>
              <span className="badge warn">{gap.kind}</span> {gap.detail}
            </li>
          ))}
        </ul>
        <h3>Your ratings</h3>
        {(job?.rubric ?? []).map((criterion) => (
          <div key={criterion.id}>
            <label>{criterion.name} rating (0–100)</label>
            <input
              type="number"
              min="0"
              max="100"
              value={scores[criterion.id] ?? ''}
              onChange={(event) => setCriterion(criterion.id, event.target.value)}
            />
            <label>{criterion.name} supporting lines (copy one exact line from the resume)</label>
            <textarea
              value={scores[`${criterion.id}:citations`] ?? ''}
              onChange={(event) => setCriterion(`${criterion.id}:citations`, event.target.value)}
            />
          </div>
        ))}
        <button type="button" onClick={runScoring} disabled={!selected || !job}>
          Calculate score
        </button>
        <h3>Move this person forward</h3>
        <label>Reason</label>
        <input value={reason} onChange={(event) => setReason(event.target.value)} />
        <label className="muted">
          <input
            type="checkbox"
            checked={confirm}
            onChange={(event) => setConfirm(event.target.checked)}
            style={{ width: 'auto', marginRight: 8 }}
          />
          I confirm this change
        </label>
        <div>
          {nextStages.map((stage) => {
            const needsConfirmation = stage === 'OFFER' || stage === 'REJECTED';
            return (
              <button
                key={stage}
                type="button"
                className="secondary"
                disabled={!selected || (needsConfirmation && (!confirm || !reason.trim()))}
                onClick={() => transition(stage)}
              >
                Move to {friendlyStage(stage)}
              </button>
            );
          })}
          {nextStages.length === 0 ? <p className="muted">This person has reached a final stage.</p> : null}
        </div>
        {message ? <p className="muted">{message}</p> : null}
      </section>
    </div>
  );
}

export default memo(SplitEvidenceViewer);
