import '@testing-library/jest-dom';

// Fix Node 20+ / 25 AbortSignal / Request mismatch in jsdom with React Router v7
const OriginalRequest = globalThis.Request;

if (typeof OriginalRequest !== 'undefined') {
  const PatchedRequest = function (input: RequestInfo | URL, init?: RequestInit) {
    if (init && init.signal) {
      try {
        return new OriginalRequest(input, init);
      } catch (err: unknown) {
        if (err instanceof TypeError && String(err).includes('AbortSignal')) {
          const { signal: _, ...rest } = init;
          return new OriginalRequest(input, rest);
        }
        throw err;
      }
    }
    return new OriginalRequest(input, init);
  } as unknown as typeof Request;

  PatchedRequest.prototype = OriginalRequest.prototype;
  globalThis.Request = PatchedRequest;

  if (typeof window !== 'undefined') {
    window.Request = PatchedRequest;
  }
}

// Ensure localStorage and sessionStorage exist with clear/getItem/setItem
class LocalStorageMock {
  private store: Record<string, string> = {};

  clear() {
    this.store = {};
  }

  getItem(key: string) {
    return this.store[key] ?? null;
  }

  setItem(key: string, value: string) {
    this.store[key] = String(value);
  }

  removeItem(key: string) {
    delete this.store[key];
  }

  get length() {
    return Object.keys(this.store).length;
  }

  key(index: number) {
    return Object.keys(this.store)[index] ?? null;
  }
}

if (typeof window !== 'undefined') {
  const localMock = new LocalStorageMock();
  const sessionMock = new LocalStorageMock();

  try {
    if (!window.localStorage || typeof window.localStorage.clear !== 'function') {
      Object.defineProperty(window, 'localStorage', { value: localMock, writable: true });
    }
  } catch {
    (window as any).localStorage = localMock;
  }

  try {
    if (!window.sessionStorage || typeof window.sessionStorage.clear !== 'function') {
      Object.defineProperty(window, 'sessionStorage', { value: sessionMock, writable: true });
    }
  } catch {
    (window as any).sessionStorage = sessionMock;
  }

  // Also bind to globalThis for node context if needed
  if (!globalThis.localStorage || typeof globalThis.localStorage.clear !== 'function') {
    (globalThis as any).localStorage = localMock;
  }
  if (!globalThis.sessionStorage || typeof globalThis.sessionStorage.clear !== 'function') {
    (globalThis as any).sessionStorage = sessionMock;
  }
}
