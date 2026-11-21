'use client';
import { friendlyError } from '../../lib/errors';

import { useState } from 'react';
import { api } from '../../lib/api-client';
import type {
  CandidateReview,
  InterviewQuestion,
  InterviewScorecard,
  Job,
} from '../../types/talentos';

export default function InterviewCopilotPanel({
  candidates,
  jobs,
}: {
  candidates: CandidateReview[];
  jobs: Job[];
}) {
  const [candidateId, setCandidateId] = useState(candidates[0]?.candidate_id ?? '');
  const [jobId, setJobId] = useState(jobs[0]?.id ?? '');
  const [questions, setQuestions] = useState<InterviewQuestion[]>([]);
  const [notes, setNotes] = useState('');
  const [scorecard, setScorecard] = useState<InterviewScorecard | null>(null);
  const [message, setMessage] = useState('');

  const generate = async () => {
    try {
      setQuestions(
        await api.generateQuestions({ candidate_id: candidateId, job_id: jobId, application_id: null }),
      );
      setMessage('');
    } catch (cause: unknown) {
      setMessage(friendlyError(cause));
    }
  };

  const synthesize = async () => {
    try {
      setScorecard(await api.synthesizeScorecard({ candidate_id: candidateId, job_id: jobId, raw_notes: notes }));
      setMessage('');
    } catch (cause: unknown) {
      setMessage(friendlyError(cause));
    }
  };

  return (
    <section className="panel">
      <div className="toolbar">
        <div>
          <label htmlFor="interview-candidate">Candidate</label>
          <select
            id="interview-candidate"
            value={candidateId}
            onChange={(event) => setCandidateId(event.target.value)}
          >
            {candidates.map((item) => (
              <option key={item.candidate_id} value={item.candidate_id}>
                {item.full_name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="interview-job">Job</label>
          <select id="interview-job" value={jobId} onChange={(event) => setJobId(event.target.value)}>
            {jobs.map((item) => (
              <option key={item.id} value={item.id}>{item.title}</option>
            ))}
          </select>
        </div>
        <button type="button" onClick={generate} disabled={!candidateId || !jobId}>
          Generate questions
        </button>
      </div>

      <ul className="list">
        {questions.map((question, index) => (
          <li key={`${question.target_criterion}-${index}`}>
            <strong>{question.text}</strong>
            <div className="muted">Skill: {question.target_criterion}</div>
            <div className="muted">Resume context: {question.resume_context}</div>
            <div>Strong signals: {question.strong_signal_indicators.join('; ')}</div>
            <div>Red flags: {question.red_flag_indicators.join('; ')}</div>
          </li>
        ))}
      </ul>

      <h2>Notes to scorecard</h2>
      <label htmlFor="raw-notes">Raw interview notes</label>
      <textarea
        id="raw-notes"
        value={notes}
        onChange={(event) => setNotes(event.target.value)}
      />
      <button type="button" onClick={synthesize} disabled={!candidateId || !jobId || !notes.trim()}>
        Synthesize scorecard
      </button>

      {scorecard ? (
        <div>
          <h3>Recommendation: {scorecard.hire_recommendation}</h3>
          <ul className="list">
            {scorecard.criterion_ratings.map((rating) => (
              <li key={rating.criterion_id}>
                {rating.criterion_name}: {rating.rating}/5 — {rating.evidence}
              </li>
            ))}
          </ul>
          <p>Strengths: {scorecard.strengths.join('; ')}</p>
          <p>Concerns: {scorecard.concerns.join('; ')}</p>
          <ul className="list">
            {scorecard.resume_discrepancies.map((item, index) => (
              <li key={`${item.criterion_id}-${index}`}>
                <span className="badge bad">discrepancy</span> {item.claim} — {item.note}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {message ? <p className="error">{message}</p> : null}
    </section>
  );
}
