interface CacheEntry<T> {
  readonly value: T;
  readonly expiresAt: number;
}

const responses = new Map<string, CacheEntry<unknown>>();
const inFlight = new Map<string, Promise<unknown>>();
const CACHE_LIMIT = 100;

export async function cachedGet<T>(
  key: string,
  ttlMs: number,
  loader: () => Promise<T>,
): Promise<T> {
  const now = Date.now();
  const hit = responses.get(key) as CacheEntry<T> | undefined;
  if (hit && hit.expiresAt > now) {
    return hit.value;
  }
  const pending = inFlight.get(key) as Promise<T> | undefined;
  if (pending) {
    return pending;
  }
  const request = loader().then((value) => {
    if (responses.size >= CACHE_LIMIT) {
      const oldest = responses.keys().next().value;
      if (oldest !== undefined) {
        responses.delete(oldest);
      }
    }
    responses.set(key, { value, expiresAt: Date.now() + ttlMs } as CacheEntry<T>);
    inFlight.delete(key);
    return value;
  });
  inFlight.set(key, request);
  request.catch(() => inFlight.delete(key));
  return request;
}

export function invalidateCache(prefix: string): void {
  for (const key of [...responses.keys()]) {
    if (prefix === '' || key.startsWith(prefix)) {
      responses.delete(key);
    }
  }
}

export function debounce<Args extends unknown[]>(
  callback: (...args: Args) => void,
  delayMs: number,
): (...args: Args) => void {
  let timer: ReturnType<typeof setTimeout> | undefined;
  return (...args: Args) => {
    if (timer !== undefined) {
      clearTimeout(timer);
    }
    timer = setTimeout(() => callback(...args), delayMs);
  };
}
