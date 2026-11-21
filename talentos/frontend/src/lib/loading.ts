// Local data resolves almost instantly; keep the skeleton on screen long enough to read.
export const MIN_SKELETON_MS = 420;

export function withMinimumDelay<T>(
  promise: Promise<T>,
  ms: number = MIN_SKELETON_MS,
): Promise<T> {
  return Promise.all([
    promise,
    new Promise<void>((resolve) => {
      setTimeout(resolve, ms);
    }),
  ]).then(([value]) => value);
}
