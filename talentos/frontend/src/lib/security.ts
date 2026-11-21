import type {
  ApplicationStage,
  Permission,
  UserRole,
} from '../types/talentos';

export const MASKED_STAGES: readonly ApplicationStage[] = [
  'NEW',
  'SCREENED',
  'REJECTED',
];

export const ROLE_PERMISSIONS: Readonly<Record<UserRole, readonly Permission[]>> = {
  admin: ['job:create', 'job:read', 'application:create', 'application:read', 'telemetry:read'],
  recruiter: ['job:create', 'job:read', 'application:create', 'application:read'],
  hiring_manager: ['job:read', 'application:read'],
  viewer: ['job:read'],
};

export const ALLOWED_RESUME_EXTENSIONS: readonly string[] = [
  '.pdf',
  '.docx',
  '.txt',
  '.md',
];

export const RUBRIC_TOLERANCE = 1e-6;

export function can(role: UserRole, permission: Permission): boolean {
  return ROLE_PERMISSIONS[role].includes(permission);
}

export function isPiiMasked(role: UserRole, stages: readonly ApplicationStage[]): boolean {
  if (role !== 'hiring_manager') {
    return false;
  }
  return !stages.some((stage) => !MASKED_STAGES.includes(stage));
}

export function maskEmail(value: string): string {
  const at = value.indexOf('@');
  return at >= 0 ? `${value.slice(0, 1)}***@${value.slice(at + 1)}` : '***';
}

export function maskPhone(value: string): string {
  return '*'.repeat(value.length);
}

export function canEditRubric(role: UserRole): boolean {
  return can(role, 'job:create');
}

export function canViewTelemetry(role: UserRole): boolean {
  return can(role, 'telemetry:read');
}

export function isAllowedResume(filename: string): boolean {
  const dot = filename.lastIndexOf('.');
  return dot >= 0 && ALLOWED_RESUME_EXTENSIONS.includes(filename.slice(dot).toLowerCase());
}

export function weightsAreValid(weights: readonly number[]): boolean {
  return (
    weights.length > 0 &&
    weights.every((weight) => weight > 0) &&
    Math.abs(weights.reduce((total, weight) => total + weight, 0) - 1) <= RUBRIC_TOLERANCE
  );
}

export function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

export function renderHighlighted(value: string): string {
  return escapeHtml(value)
    .replace(/&lt;mark&gt;/g, '<mark>')
    .replace(/&lt;\/mark&gt;/g, '</mark>');
}

const BLOCKED_PROTOCOLS: readonly string[] = ['javascript:', 'data:', 'vbscript:'];

export function sanitizeExternalUrl(value: string): string | null {
  try {
    const parsed = new URL(value);
    const protocol = parsed.protocol.toLowerCase();
    if (
      BLOCKED_PROTOCOLS.includes(protocol) ||
      (protocol !== 'https:' && protocol !== 'http:')
    ) {
      return null;
    }
    if (!parsed.hostname || parsed.username || parsed.password) {
      return null;
    }
    return parsed.toString();
  } catch {
    return null;
  }
}

export function externalLinkProps(
  value: string,
): { href: string; target: '_blank'; rel: 'noopener noreferrer' } | null {
  const safe = sanitizeExternalUrl(value);
  return safe === null
    ? null
    : { href: safe, target: '_blank', rel: 'noopener noreferrer' };
}
