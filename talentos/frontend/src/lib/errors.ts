export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export function friendlyError(cause: unknown): string {
  if (cause instanceof ApiError) {
    if (cause.status === 403) {
      return 'You do not have access to this area. Ask your workspace admin to change your role.';
    }
    if (cause.status === 404) {
      return 'We could not find that item. It may have been moved or removed.';
    }
    if (cause.status >= 500) {
      return 'The workspace could not finish that task. Please try again in a moment.';
    }
    return 'That change could not be saved. Check the details and try again.';
  }
  if (cause instanceof TypeError) {
    return 'The workspace could not be reached. Check that the local server is running.';
  }
  if (cause instanceof Error && cause.message) {
    return cause.message;
  }
  return 'Something went wrong. Please try again.';
}
