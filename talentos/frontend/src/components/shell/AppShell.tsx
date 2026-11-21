'use client';
import { friendlyError } from '../../lib/errors';

import { usePathname } from 'next/navigation';
import { useEffect, useState, type ReactNode } from 'react';
import { api } from '../../lib/api-client';
import type { Session } from '../../types/talentos';
import CommandPalette from '../ui/CommandPalette';
import SidebarNav from './SidebarNav';
import WorkspaceRbacBar from './WorkspaceRbacBar';

export default function AppShell({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const pathname = usePathname();

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError('');
    api.session()
      .then((value) => { if (active) { setSession(value); } })
      .catch((cause: unknown) => {
        if (active) { setError(friendlyError(cause)); }
      })
      .finally(() => { if (active) { setLoading(false); } });
    return () => { active = false; };
  }, [pathname]);

  return (
    <div className="app-shell">
      <SidebarNav role={session?.role ?? 'viewer'} loading={loading} />
      <div className="workspace">
        <WorkspaceRbacBar session={session} loading={loading} error={error} />
        <main key={pathname} className="workspace-main page-transition">{children}</main>
      </div>
      <CommandPalette role={session?.role ?? 'viewer'} />
    </div>
  );
}
