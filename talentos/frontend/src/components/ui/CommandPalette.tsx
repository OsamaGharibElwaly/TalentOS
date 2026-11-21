'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { canViewRoute } from '../../lib/auth-session';
import { NAV_ITEMS } from '../../lib/navigation';
import type { UserRole } from '../../types/talentos';

export default function CommandPalette({ role }: { role: UserRole }) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const router = useRouter();
  const items = useMemo(
    () => NAV_ITEMS.filter((item) => canViewRoute(role, item.path)),
    [role],
  );

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        setOpen((current) => !current);
      } else if (event.key === 'Escape') {
        setOpen(false);
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  if (!open) {
    return null;
  }
  const visible = items.filter((item) =>
    item.label.toLowerCase().includes(query.toLowerCase()),
  );

  return (
    <div className="command-backdrop" onClick={() => setOpen(false)}>
      <div
        className="command-dialog"
        role="dialog"
        aria-modal="true"
        aria-label="Quick jump"
        onClick={(event) => event.stopPropagation()}
      >
        <input
          autoFocus
          aria-label="Quick jump search"
          placeholder="Jump to…"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
        <ul className="list">
          {visible.map((item) => (
            <li key={item.path}>
              <button
                type="button"
                className="command-item"
                onClick={() => {
                  router.push(item.path);
                  setOpen(false);
                  setQuery('');
                }}
              >
                <span>{item.label}</span>
                <span className="muted">{item.description}</span>
              </button>
            </li>
          ))}
        </ul>
        <p className="muted">Esc to close</p>
      </div>
    </div>
  );
}
