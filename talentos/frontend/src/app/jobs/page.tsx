'use client';
import { friendlyError } from '../../lib/errors';

import { useEffect, useState } from 'react';
import RubricWeightEditor from '../../components/jobs/RubricWeightEditor';
import DeveloperMode from '../../components/ui/DeveloperMode';
import { api } from '../../lib/api-client';
import { DEVELOPER_RECIPES } from '../../lib/developer-recipes';
import type { Job, Session } from '../../types/talentos';

export default function JobsPage() {
  const [session, setSession] = useState<Session | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    api.session()
      .then(setSession)
      .catch((cause: unknown) => setError(friendlyError(cause)));
    api.listJobs()
      .then(setJobs)
      .catch((cause: unknown) => setError(friendlyError(cause)));
  }, []);

  return (
    <section>
      <h1>Jobs &amp; scorecards</h1>
      <p className="muted">Set the skills you will look for so every reviewer uses the same standard.</p>
      {error ? <p className="error">{error}</p> : null}
      <RubricWeightEditor role={session?.role ?? 'viewer'} />
      <h2>Roles you are hiring for</h2>
      <table>
        <thead><tr><th>Role</th><th>Skills to assess</th><th>Created by</th></tr></thead>
        <tbody>
          {jobs.map((job) => (
            <tr key={job.id}>
              <td>{job.title}</td>
              <td>{job.rubric.length}</td>
              <td>{job.created_by}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <DeveloperMode {...DEVELOPER_RECIPES.jobs} />
    </section>
  );
}
