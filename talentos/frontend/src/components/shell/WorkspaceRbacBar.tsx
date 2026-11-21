'use client';

import { useEffect, useState } from 'react';
import { clearProfile, readProfile, writeSession, type WorkspaceProfile } from '../../lib/auth-session';
import {
  friendlyPermission,
  friendlyRole,
  permissionIcon,
  permissionTone,
  roleIcon,
  roleTone,
} from '../../lib/navigation';
import type { Session } from '../../types/talentos';
import Icon from '../ui/Icon';
import { Spinner } from '../ui/LoadingScreen';

export default function WorkspaceRbacBar({
  session,
  loading,
  error,
}: {
  session: Session | null;
  loading: boolean;
  error: string;
}) {
  const [workspace, setWorkspace] = useState(session?.tenant_id ?? '');
  const [profile, setProfile] = useState<WorkspaceProfile | null>(null);

  useEffect(() => {
    setWorkspace(session?.tenant_id ?? '');
  }, [session?.tenant_id]);

  useEffect(() => {
    setProfile(readProfile());
  }, [session?.user_id, session?.tenant_id]);

  const role = session?.role ?? 'viewer';
  const signedInAs =
    profile && session && profile.userId === session.user_id && profile.tenantId === session.tenant_id
      ? profile.fullName
      : (session?.user_id ?? '');

  return (
    <header className="rbac-bar">
      <div className="rbac-identity">
        <label htmlFor="workspace">Your workspace</label>
        <select
          id="workspace"
          value={workspace}
          disabled={loading || session === null}
          onChange={(event) => {
            setWorkspace(event.target.value);
            clearProfile();
            if (session) {
              writeSession({ userId: session.user_id, tenantId: event.target.value });
            }
          }}
        >
          <option value={session?.tenant_id ?? ''}>
            {loading ? 'Connecting…' : (session?.tenant_id ?? 'Not connected')}
          </option>
        </select>
        {loading ? (
          <Spinner size={16} label="Opening your workspace…" />
        ) : (
          <>
            <span className={`role-chip tone-${roleTone(role)}`}>
              <Icon name={roleIcon(role)} size={14} />
              {friendlyRole(role)}
            </span>
            {signedInAs ? <span className="muted">Signed in as {signedInAs}</span> : null}
          </>
        )}
        {error ? <span className="error">We could not reach your workspace.</span> : null}
      </div>
      <div className="permission-chips" aria-label="What you can do here">
        {loading ? (
          <span className="skeleton" style={{ width: 180, height: 18 }} aria-hidden="true" />
        ) : (
          (session?.permissions ?? []).map((permission) => (
            <span key={permission} className={`permission-chip tone-${permissionTone(permission)}`}>
              <Icon name={permissionIcon(permission)} size={14} />
              {friendlyPermission(permission)}
            </span>
          ))
        )}
      </div>
    </header>
  );
}
