'use client';
import { friendlyError } from '../../lib/errors';

import { useEffect, useMemo, useState } from 'react';
import SplitEvidenceViewer from '../../components/candidates/SplitEvidenceViewer';
import { CandidateListSkeleton } from '../../components/ui/Skeletons';
import DeveloperMode from '../../components/ui/DeveloperMode';
import { api } from '../../lib/api-client';
import { DEVELOPER_RECIPES } from '../../lib/developer-recipes';
import { withMinimumDelay } from '../../lib/loading';
import type { CandidateReview, Job } from '../../types/talentos';

const PAGE_SIZE = 20;

export default function CandidatesPage() {
  const [candidates, setCandidates] = useState<CandidateReview[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedId, setSelectedId] = useState('');
  const [visible, setVisible] = useState(PAGE_SIZE);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    withMinimumDelay(api.listCandidates())
      .then((items) => {
        setCandidates(items);
        setSelectedId(items[0]?.candidate_id ?? '');
        setLoading(false);
      })
      .catch((cause: unknown) => {
        setError(friendlyError(cause));
        setLoading(false);
      });
    api.listJobs().then(setJobs).catch((cause: unknown) => setError(friendlyError(cause)));
  }, []);

  const visibleCandidates = useMemo(() => candidates.slice(0, visible), [candidates, visible]);
  const selected = candidates.find((item) => item.candidate_id === selectedId);

  return (
    <section>
      <h1>Review candidates</h1>
      <p className="muted">Read each resume beside the skills for the role, with supporting lines kept close to every rating.</p>
      {error ? <p className="error">{error}</p> : null}
      {loading ? <CandidateListSkeleton rows={4} /> : null}
      {!loading && candidates.length === 0 ? (
        <div className="empty-hint">No resumes have been added yet. <a href="/ingestion">Add your first resume</a> to begin.</div>
      ) : null}
      <div className="toolbar">
        <label htmlFor="candidate-select">Candidate</label>
        <select
          id="candidate-select"
          value={selectedId}
          onChange={(event) => setSelectedId(event.target.value)}
        >
          {visibleCandidates.map((item) => (
            <option key={item.candidate_id} value={item.candidate_id}>
              {item.full_name} — {item.total_experience_years} years
            </option>
          ))}
        </select>
        {visible < candidates.length ? (
          <button type="button" className="secondary" onClick={() => setVisible((count) => count + PAGE_SIZE)}>
            Show more
          </button>
        ) : null}
      </div>
      {selected ? (
        <SplitEvidenceViewer candidate={selected} jobs={jobs} />
      ) : null}
      <DeveloperMode {...DEVELOPER_RECIPES.candidates} />
    </section>
  );
}
