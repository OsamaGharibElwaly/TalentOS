'use client';
import { friendlyError } from '../../lib/errors';

import { useState } from 'react';
import { api } from '../../lib/api-client';
import { canEditRubric, weightsAreValid } from '../../lib/security';
import type { RubricCriterion, UserRole } from '../../types/talentos';

const NEW_CRITERION = (index: number): RubricCriterion => ({
  id: `c${index + 1}`,
  name: '',
  weight: 0,
  description: '',
  mandatory: false,
});

export default function RubricWeightEditor({ role }: { role: UserRole }) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [criteria, setCriteria] = useState<RubricCriterion[]>([NEW_CRITERION(0)]);
  const [message, setMessage] = useState('');
  const editable = canEditRubric(role);
  const total = criteria.reduce((sum, item) => sum + item.weight, 0);
  const valid = weightsAreValid(criteria.map((item) => item.weight)) && title.trim().length > 0;

  const update = (index: number, patch: Partial<RubricCriterion>) => {
    setCriteria((current) =>
      current.map((item, position) => (position === index ? { ...item, ...patch } : item)),
    );
  };

  const submit = async () => {
    if (!valid) {
      return;
    }
    try {
      const job = await api.createJob({ title, description, rubric: criteria });
      setMessage(`Role saved. Reference: ${job.id}`);
      setTitle('');
      setDescription('');
      setCriteria([NEW_CRITERION(0)]);
    } catch (cause: unknown) {
      setMessage(friendlyError(cause));
    }
  };

  return (
    <section className="panel">
      <h2>Skills &amp; weights</h2>
      <p className="muted">List the skills for this role and give each one a share of the final score.</p>
      <label htmlFor="job-title">Role title</label>
      <input
        id="job-title"
        value={title}
        disabled={!editable}
        onChange={(event) => setTitle(event.target.value)}
      />
      <label htmlFor="job-description">Description</label>
      <input
        id="job-description"
        value={description}
        disabled={!editable}
        onChange={(event) => setDescription(event.target.value)}
      />
      <table>
        <thead>
          <tr>
            <th>Skill</th>
            <th>Weight (%)</th>
            <th>Must have</th>
          </tr>
        </thead>
        <tbody>
          {criteria.map((item, index) => (
            <tr key={item.id}>
              <td>
                <input
                  aria-label={`criterion-${index}-name`}
                  value={item.name}
                  disabled={!editable}
                  onChange={(event) => update(index, { name: event.target.value })}
                />
              </td>
              <td>
                <input
                  aria-label={`criterion-${index}-weight`}
                  type="number"
                  min="0"
                  max="100"
                  step="1"
                  value={Number((item.weight * 100).toFixed(4))}
                  disabled={!editable}
                  onChange={(event) =>
                    update(index, { weight: Number(event.target.value) / 100 })
                  }
                />
              </td>
              <td>
                <input
                  aria-label={`criterion-${index}-mandatory`}
                  type="checkbox"
                  checked={item.mandatory}
                  disabled={!editable}
                  onChange={(event) => update(index, { mandatory: event.target.checked })}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className={valid ? 'muted' : 'error'}>
        Assigned {(total * 100).toFixed(2)}% — the shares must total exactly 100%.
      </p>
      <button
        type="button"
        onClick={() => setCriteria((current) => [...current, NEW_CRITERION(current.length)])}
        disabled={!editable}
        className="secondary"
      >
        Add skill
      </button>{' '}
      <button type="button" onClick={submit} disabled={!editable || !valid}>
        Save role
      </button>
      {message ? <p className="muted">{message}</p> : null}
      {!editable ? <p className="muted">Your role can view the skills but not change them.</p> : null}
    </section>
  );
}
