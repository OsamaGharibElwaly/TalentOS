'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { canViewRoute } from '../../lib/auth-session';
import { NAV_ITEMS } from '../../lib/navigation';
import type { UserRole } from '../../types/talentos';
import BrandMark from '../ui/BrandMark';
import Icon from '../ui/Icon';
import { Spinner } from '../ui/LoadingScreen';

export default function SidebarNav({ role, loading }: { role: UserRole; loading: boolean }) {
  const pathname = usePathname();
  return (
    <nav className="sidebar" aria-label="Primary navigation">
      <div className="brand"><BrandMark /> TalentOS</div>
      <p className="nav-caption">Your workspace</p>
      {loading ? (
        <p className="nav-loading"><Spinner size={16} label="Connecting…" /></p>
      ) : (
        NAV_ITEMS.map((item) => {
          const allowed = canViewRoute(role, item.path);
          const active = pathname === item.path;
          const className = allowed
            ? active ? 'nav-link active' : 'nav-link'
            : 'nav-link nav-locked';
          const content = (
            <>
              <span className={`nav-dot tone-${item.tone}`} aria-hidden="true" />
              <span>{item.label}</span>
              {item.path === '/guide' ? <span className="nav-new">New</span> : null}
              {allowed ? null : <span className="nav-lock" aria-hidden="true"><Icon name="lock" size={14} /></span>}
            </>
          );
          return allowed ? (
            <Link key={item.path} href={item.path} className={className} title={item.description}>
              {content}
            </Link>
          ) : (
            <span key={item.path} className={className} aria-disabled="true" title="Available to workspace administrators">
              {content}
            </span>
          );
        })
      )}
      <Link
        href="/login"
        className={pathname === '/login' ? 'nav-link active' : 'nav-link'}
        title="Choose a demo profile and workspace"
      >
        <span className="nav-dot tone-violet" aria-hidden="true" />
        <span>Sign in / switch user</span>
      </Link>
      <p className="nav-footnote">Your data stays on this computer.</p>
    </nav>
  );
}
