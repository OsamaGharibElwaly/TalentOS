'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useState, type FormEvent } from 'react';
import BrandMark from '../../components/ui/BrandMark';
import DeveloperMode from '../../components/ui/DeveloperMode';
import Icon, { type IconName } from '../../components/ui/Icon';
import { api } from '../../lib/api-client';
import { DEVELOPER_RECIPES } from '../../lib/developer-recipes';
import {
  clearProfile,
  readSession,
  writeProfile,
  writeSession,
} from '../../lib/auth-session';
import { friendlyError } from '../../lib/errors';
import { invalidateCache } from '../../lib/query-cache';

type LoginMode = 'signin' | 'signup';

const PROFILES: readonly {
  id: string;
  label: string;
  detail: string;
  icon: IconName;
  tone: string;
}[] = [
  { id: 'admin', label: 'Workspace admin', detail: 'Everything, including activity insights', icon: 'shield', tone: 'violet' },
  { id: 'recruiter', label: 'Recruiter', detail: 'Add resumes, review people and run interviews', icon: 'briefcase', tone: 'teal' },
  { id: 'manager', label: 'Hiring manager', detail: 'Review roles and candidates with privacy masking', icon: 'users', tone: 'cyan' },
  { id: 'viewer', label: 'Viewer', detail: 'Look at roles only', icon: 'search', tone: 'slate' },
];

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<LoginMode>('signin');
  const [userId, setUserId] = useState('recruiter');
  const [tenantId, setTenantId] = useState('org-1');
  const [workspaceName, setWorkspaceName] = useState('');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [current, setCurrent] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    setCurrent(readSession().userId);
  }, []);

  const finish = () => {
    invalidateCache('');
    router.push('/');
    router.refresh();
  };

  const signIn = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const organization = tenantId.trim();
    if (!organization) {
      setError('Enter your organization. The seeded demo workspace is org-1.');
      return;
    }

    const previous = readSession();
    setBusy(true);
    setError('');
    clearProfile();
    writeSession({ userId, tenantId: organization });
    invalidateCache('');
    try {
      await api.session();
      finish();
    } catch (cause: unknown) {
      writeSession(previous);
      setError(friendlyError(cause));
      setBusy(false);
    }
  };

  const signUp = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const organization = workspaceName.trim();
    const name = fullName.trim();
    const workEmail = email.trim().toLowerCase();
    if (organization.length < 2 || name.length < 2 || !EMAIL_PATTERN.test(workEmail)) {
      setError('Add a workspace name, your full name and a valid work email.');
      return;
    }

    setBusy(true);
    setError('');
    try {
      const account = await api.createAccount({
        organization,
        full_name: name,
        email: workEmail,
      });
      writeSession({ userId: account.user_id, tenantId: account.tenant_id });
      writeProfile({
        userId: account.user_id,
        tenantId: account.tenant_id,
        fullName: account.full_name,
        organization: account.organization,
        email: workEmail,
      });
      finish();
    } catch (cause: unknown) {
      setError(friendlyError(cause));
      setBusy(false);
    }
  };

  return (
    <section className="login-page">
      <div className="login-card">
        <div className="login-intro">
          <div className="brand"><BrandMark size={34} /> TalentOS</div>
          <p className="eyebrow">Local hiring workspace</p>
          <h1>Open the workspace you will hire from</h1>
          <p className="hero-copy">
            Choose a demo profile or set up a fresh workspace. Your organization, role and
            candidate data all stay on this computer — no password or outside service is needed.
          </p>
          {current ? <p className="muted">Currently signed in as <strong>{current}</strong>.</p> : null}
          <div className="login-note">
            <Icon name="lock" size={18} />
            <span>
              Seeded demo data is ready in <strong>org-1</strong>: 3 roles, 9 candidates and 9
              applications. Choose <strong>admin</strong> to open Activity &amp; Insights.
            </span>
          </div>
        </div>

        <div className="login-form">
          <div className="login-tabs" role="tablist" aria-label="Workspace access">
            <button
              type="button"
              role="tab"
              aria-selected={mode === 'signin'}
              className={mode === 'signin' ? 'active' : ''}
              onClick={() => { setMode('signin'); setError(''); }}
            >
              Sign in
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={mode === 'signup'}
              className={mode === 'signup' ? 'active' : ''}
              onClick={() => { setMode('signup'); setError(''); }}
            >
              Create workspace
            </button>
          </div>

          {mode === 'signin' ? (
            <form onSubmit={signIn} aria-label="Sign in to an existing workspace">
              <label htmlFor="login-tenant">Organization</label>
              <input
                id="login-tenant"
                value={tenantId}
                onChange={(event) => setTenantId(event.target.value)}
                placeholder="org-1"
                autoComplete="organization"
              />
              <span className="field-hint">The seeded demo workspace is <code>org-1</code>.</span>

              <span className="field-label">Switch user role</span>
              <div className="profile-grid">
                {PROFILES.map((profile) => (
                  <button
                    key={profile.id}
                    type="button"
                    className={`profile-card tone-${profile.tone}${userId === profile.id ? ' selected' : ''}`}
                    onClick={() => setUserId(profile.id)}
                    aria-pressed={userId === profile.id}
                  >
                    <span className="profile-icon"><Icon name={profile.icon} /></span>
                    <strong>{profile.label}</strong>
                    <span className="muted">{profile.detail}</span>
                  </button>
                ))}
              </div>

              {error ? <p className="error" role="alert">{error}</p> : null}
              <button type="submit" className="btn-primary login-submit" disabled={busy}>
                {busy ? 'Opening your workspace…' : 'Sign in'}
                {busy ? null : <span aria-hidden="true">→</span>}
              </button>
            </form>
          ) : (
            <form onSubmit={signUp} aria-label="Create a new local workspace">
              <label htmlFor="signup-organization">Workspace name</label>
              <input
                id="signup-organization"
                value={workspaceName}
                onChange={(event) => setWorkspaceName(event.target.value)}
                placeholder="Northstar Hiring"
                autoComplete="organization"
                minLength={2}
                required
              />
              <span className="field-hint">Use your team or company name.</span>

              <label htmlFor="signup-name">Your full name</label>
              <input
                id="signup-name"
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
                placeholder="Alex Morgan"
                autoComplete="name"
                minLength={2}
                required
              />

              <label htmlFor="signup-email">Work email</label>
              <input
                id="signup-email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="alex@company.com"
                autoComplete="email"
                required
              />
              <span className="field-hint">
                New workspaces start with Recruiter access: add resumes, review candidates and run
                interviews. Admin access stays in the seeded demo workspace.
              </span>

              {error ? <p className="error" role="alert">{error}</p> : null}
              <button type="submit" className="btn-primary login-submit" disabled={busy}>
                {busy ? 'Creating your workspace…' : 'Create workspace & sign in'}
                {busy ? null : <span aria-hidden="true">→</span>}
              </button>
            </form>
          )}

          <Link href="/" className="step-link">Continue as the default recruiter instead</Link>
        </div>
      </div>

      <DeveloperMode {...DEVELOPER_RECIPES.login} />
    </section>
  );
}
