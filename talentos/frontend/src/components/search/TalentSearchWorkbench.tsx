'use client';
import { friendlyError } from '../../lib/errors';

import { memo, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { api } from '../../lib/api-client';
import { friendlyStage } from '../../lib/navigation';
import { debounce } from '../../lib/query-cache';
import type { ApplicationStage, TalentSearchResult } from '../../types/talentos';
import SafeText from '../ui/SafeText';

const STAGES: readonly (ApplicationStage | '')[] = [
  '', 'NEW', 'SCREENED', 'SHORTLISTED', 'INTERVIEW', 'FINAL_REVIEW', 'OFFER', 'REJECTED',
];

function TalentSearchWorkbench() {
  const [query, setQuery] = useState('');
  const [minExperience, setMinExperience] = useState('');
  const [skills, setSkills] = useState('');
  const [stage, setStage] = useState<ApplicationStage | ''>('');
  const [results, setResults] = useState<TalentSearchResult[]>([]);
  const [message, setMessage] = useState('');
  const controller = useRef<AbortController | null>(null);

  const runSearch = useCallback(async () => {
    controller.current?.abort();
    const next = new AbortController();
    controller.current = next;
    try {
      const found = await api.searchTalent(
        {
          query,
          min_experience_years: minExperience === '' ? null : Number(minExperience),
          required_skills: skills.split(',').map((item) => item.trim()).filter(Boolean),
          stage: stage === '' ? null : stage,
          top_k: 10,
        },
        next.signal,
      );
      setResults(found);
      setMessage('');
    } catch (cause: unknown) {
      if (cause instanceof DOMException && cause.name === 'AbortError') {
        return;
      }
      setMessage(friendlyError(cause));
    }
  }, [query, minExperience, skills, stage]);

  const debouncedSearch = useMemo(() => debounce(() => void runSearch(), 250), [runSearch]);

  useEffect(() => {
    if (query.trim().length > 0) {
      debouncedSearch();
    }
    return () => controller.current?.abort();
  }, [query, debouncedSearch]);

  const terms = useMemo(
    () => query.split(/\s+/).filter(Boolean),
    [query],
  );
  const rows = useMemo(
    () => results.slice(0, 25).map((item) => ({
      candidateId: item.candidate_id,
      name: item.profile.full_name,
      skills: item.profile.skills.join(', '),
      score: item.score.toFixed(4),
      excerpt: item.highlighted_excerpt.replace(/<\/?mark>/g, ''),
    })),
    [results],
  );

  return (
    <section className="panel">
      <div className="toolbar">
        <div>
          <label htmlFor="search-query">Query</label>
          <input id="search-query" value={query} onChange={(event) => setQuery(event.target.value)} />
        </div>
        <div>
          <label htmlFor="search-experience">Minimum years</label>
          <input
            id="search-experience"
            type="number"
            min="0"
            step="0.5"
            value={minExperience}
            onChange={(event) => setMinExperience(event.target.value)}
          />
        </div>
        <div>
          <label htmlFor="search-skills">Required skills (comma separated)</label>
          <input id="search-skills" value={skills} onChange={(event) => setSkills(event.target.value)} />
        </div>
        <div>
          <label htmlFor="search-stage">Where they are</label>
          <select
            id="search-stage"
            value={stage}
            onChange={(event) => setStage(event.target.value as ApplicationStage | '')}
          >
            {STAGES.map((item) => <option key={item} value={item}>{friendlyStage(item)}</option>)}
          </select>
        </div>
        <button type="button" onClick={() => void runSearch()} disabled={!query.trim()}>Search</button>
      </div>
      {message ? <p className="error">{message}</p> : null}
      <ul className="list">
        {rows.map((item) => (
          <li key={item.candidateId}>
            <strong>{item.name}</strong> — score {item.score}
            <div className="muted">{item.skills}</div>
            <SafeText text={item.excerpt} highlight={terms} />
          </li>
        ))}
      </ul>
    </section>
  );
}

export default memo(TalentSearchWorkbench);
