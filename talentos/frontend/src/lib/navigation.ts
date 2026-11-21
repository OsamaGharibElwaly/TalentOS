import type { IconName } from '../components/ui/Icon';
import type { ApplicationStage, Permission, UserRole } from '../types/talentos';

export interface NavItem {
  readonly path: string;
  readonly label: string;
  readonly description: string;
  readonly tone: string;
  readonly icon: IconName;
}

export const NAV_ITEMS: readonly NavItem[] = [
  { path: '/', label: 'Overview', description: 'See what is happening across your hiring.', tone: 'indigo', icon: 'home' },
  { path: '/guide', label: 'Getting Started', description: 'Follow the hiring journey step by step.', tone: 'violet', icon: 'compass' },
  { path: '/jobs', label: 'Jobs & Scorecards', description: 'Describe a role and the skills you will look for.', tone: 'teal', icon: 'clipboard' },
  { path: '/ingestion', label: 'Add Resumes', description: 'Bring candidate resumes into your workspace.', tone: 'amber', icon: 'upload' },
  { path: '/candidates', label: 'Review Candidates', description: 'Compare people against the skills for the job.', tone: 'rose', icon: 'search' },
  { path: '/interviews', label: 'Interviews', description: 'Get suggested questions and notes for each conversation.', tone: 'cyan', icon: 'chat' },
  { path: '/talent-pool', label: 'Find Talent', description: 'Search everyone by skill, experience and stage.', tone: 'lime', icon: 'spark' },
  { path: '/telemetry', label: 'Activity & Insights', description: 'See your hiring numbers and what to do next.', tone: 'slate', icon: 'chart' },
] as const;

export const WORKFLOW_ITEMS: readonly NavItem[] = NAV_ITEMS.filter(
  (item) => item.path !== '/' && item.path !== '/guide',
);

const STAGE_LABELS: Readonly<Record<ApplicationStage, string>> = {
  NEW: 'New applicant',
  SCREENED: 'Screening',
  SHORTLISTED: 'Shortlisted',
  INTERVIEW: 'Interviewing',
  FINAL_REVIEW: 'Final review',
  OFFER: 'Offer',
  REJECTED: 'Not moving forward',
};

export function friendlyStage(stage: ApplicationStage | ''): string {
  return stage === '' ? 'All stages' : STAGE_LABELS[stage];
}

const ROLE_LABELS: Readonly<Record<UserRole, string>> = {
  admin: 'Workspace admin',
  recruiter: 'Recruiter',
  hiring_manager: 'Hiring manager',
  viewer: 'Viewer',
};

const PERMISSION_LABELS: Readonly<Record<Permission, string>> = {
  'job:create': 'Create roles',
  'job:read': 'View roles',
  'application:create': 'Add candidates',
  'application:read': 'Review candidates',
  'telemetry:read': 'View insights',
};

export function friendlyRole(role: UserRole): string {
  return ROLE_LABELS[role] ?? role;
}

export function friendlyPermission(permission: Permission): string {
  return PERMISSION_LABELS[permission] ?? permission;
}

const PERMISSION_TONES: Readonly<Record<Permission, string>> = {
  'job:create': 'violet',
  'job:read': 'indigo',
  'application:create': 'amber',
  'application:read': 'teal',
  'telemetry:read': 'rose',
};

const PERMISSION_ICONS: Readonly<Record<Permission, IconName>> = {
  'job:create': 'clipboard',
  'job:read': 'briefcase',
  'application:create': 'upload',
  'application:read': 'users',
  'telemetry:read': 'chart',
};

const ROLE_ICONS: Readonly<Record<UserRole, IconName>> = {
  admin: 'shield',
  recruiter: 'briefcase',
  hiring_manager: 'users',
  viewer: 'search',
};

const ROLE_TONES: Readonly<Record<UserRole, string>> = {
  admin: 'violet',
  recruiter: 'teal',
  hiring_manager: 'cyan',
  viewer: 'slate',
};

export function permissionTone(permission: Permission): string {
  return PERMISSION_TONES[permission] ?? 'slate';
}

export function permissionIcon(permission: Permission): IconName {
  return PERMISSION_ICONS[permission] ?? 'spark';
}

export function roleIcon(role: UserRole): IconName {
  return ROLE_ICONS[role] ?? 'shield';
}

export function roleTone(role: UserRole): string {
  return ROLE_TONES[role] ?? 'slate';
}
