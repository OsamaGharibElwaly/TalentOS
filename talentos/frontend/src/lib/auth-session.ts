import type { Permission, Session, UserRole } from '../types/talentos';
import { can } from './security';

export const SESSION_STORAGE_KEY = 'talentos.session';
const PROFILE_STORAGE_KEY = 'talentos.profile';

// Local-first demo identity: the seeded workspace is usable without setup.
export const DEFAULT_USER_ID = 'recruiter';
export const DEFAULT_TENANT_ID = 'org-1';

export interface SessionIdentity {
  readonly userId: string;
  readonly tenantId: string;
}

export interface WorkspaceProfile {
  readonly userId: string;
  readonly tenantId: string;
  readonly fullName: string;
  readonly organization: string;
  readonly email: string;
}

function defaultIdentity(): SessionIdentity {
  return {
    userId: process.env.NEXT_PUBLIC_USER_ID || DEFAULT_USER_ID,
    tenantId: process.env.NEXT_PUBLIC_TENANT_ID || DEFAULT_TENANT_ID,
  };
}

export function readSession(): SessionIdentity {
  if (typeof window === 'undefined') {
    return defaultIdentity();
  }
  const raw = window.localStorage.getItem(SESSION_STORAGE_KEY);
  if (!raw) {
    return defaultIdentity();
  }
  try {
    const parsed = JSON.parse(raw) as Partial<SessionIdentity>;
    const fallback = defaultIdentity();
    return {
      userId: typeof parsed.userId === 'string' && parsed.userId ? parsed.userId : fallback.userId,
      tenantId: typeof parsed.tenantId === 'string' && parsed.tenantId ? parsed.tenantId : fallback.tenantId,
    };
  } catch {
    return defaultIdentity();
  }
}

export function writeSession(identity: SessionIdentity): void {
  if (typeof window === 'undefined') {
    return;
  }
  window.localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(identity));
}

export function readProfile(): WorkspaceProfile | null {
  if (typeof window === 'undefined') {
    return null;
  }
  const raw = window.localStorage.getItem(PROFILE_STORAGE_KEY);
  if (!raw) {
    return null;
  }
  try {
    const parsed = JSON.parse(raw) as Partial<WorkspaceProfile>;
    if (
      typeof parsed.userId !== 'string' ||
      typeof parsed.tenantId !== 'string' ||
      typeof parsed.fullName !== 'string' ||
      typeof parsed.organization !== 'string' ||
      typeof parsed.email !== 'string'
    ) {
      return null;
    }
    return {
      userId: parsed.userId,
      tenantId: parsed.tenantId,
      fullName: parsed.fullName,
      organization: parsed.organization,
      email: parsed.email,
    };
  } catch {
    return null;
  }
}

export function writeProfile(profile: WorkspaceProfile): void {
  if (typeof window === 'undefined') {
    return;
  }
  window.localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify(profile));
}

export function clearProfile(): void {
  if (typeof window === 'undefined') {
    return;
  }
  window.localStorage.removeItem(PROFILE_STORAGE_KEY);
}

export function authHeaders(identity: SessionIdentity): Record<string, string> {
  return {
    'X-User-Id': identity.userId,
    'X-Tenant-Id': identity.tenantId,
  };
}

export function csrfHeaders(): Record<string, string> {
  if (typeof document === 'undefined') {
    return { 'X-Requested-With': 'XMLHttpRequest' };
  }
  const match = document.cookie.match(/(?:^|;\s*)talentos_csrf=([^;]+)/);
  return match
    ? {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRF-Token': decodeURIComponent(match[1]),
      }
    : { 'X-Requested-With': 'XMLHttpRequest' };
}

export function hasPermission(session: Session | null, permission: Permission): boolean {
  return session !== null && session.permissions.includes(permission);
}

export function canViewRoute(role: UserRole, route: string): boolean {
  if (route.startsWith('/telemetry')) {
    return can(role, 'application:read');
  }
  if (route.startsWith('/ingestion')) {
    return can(role, 'application:create');
  }
  if (
    route.startsWith('/candidates') ||
    route.startsWith('/interviews') ||
    route.startsWith('/talent-pool')
  ) {
    return can(role, 'application:read');
  }
  if (route.startsWith('/jobs')) {
    return can(role, 'job:read');
  }
  return true;
}
