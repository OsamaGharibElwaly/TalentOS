'use client';

import { useEffect, useState } from 'react';
import InterviewCopilotPanel from '../../components/interviews/InterviewCopilotPanel';
import DeveloperMode from '../../components/ui/DeveloperMode';
import { api } from '../../lib/api-client';
import { DEVELOPER_RECIPES } from '../../lib/developer-recipes';
import type { CandidateReview, Job } from '../../types/talentos';

export default function InterviewsPage() {
  const [candidates, setCandidates] = useState<CandidateReview[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);

  useEffect(() => {
    api.listCandidates().then(setCandidates).catch(() => setCandidates([]));
    api.listJobs().then(setJobs).catch(() => setJobs([]));
  }, []);

  return (
    <section>
      <h1>Interview guide</h1>
      <p className="muted">Suggested questions are built from the skills you chose for the role and the resume in front of you.</p>
      <InterviewCopilotPanel candidates={candidates} jobs={jobs} />
      <DeveloperMode {...DEVELOPER_RECIPES.interviews} />
    </section>
  );
}
