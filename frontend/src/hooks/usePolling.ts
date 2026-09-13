import { useEffect, useRef, useState, useCallback } from 'react';

export interface UsePollingOptions<T> {
  fn: () => Promise<T>;
  intervalMs?: number;
  enabled?: boolean;
  isTerminal: (data: T) => boolean;
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
}

export interface UsePollingResult<T> {
  data: T | null;
  error: Error | null;
  isLoading: boolean;
  isPolling: boolean;
  stopPolling: () => void;
  restartPolling: () => void;
  refetch: () => Promise<void>;
}

export function usePolling<T>({
  fn,
  intervalMs = 3000,
  enabled = true,
  isTerminal,
  onSuccess,
  onError,
}: UsePollingOptions<T>): UsePollingResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isPolling, setIsPolling] = useState(enabled);

  const timeoutIdRef = useRef<NodeJS.Timeout | number | null>(null);
  const isMountedRef = useRef(true);

  // Keep references to prevent recreating polling loops on prop changes
  const fnRef = useRef(fn);
  fnRef.current = fn;

  const isTerminalRef = useRef(isTerminal);
  isTerminalRef.current = isTerminal;

  const onSuccessRef = useRef(onSuccess);
  onSuccessRef.current = onSuccess;

  const onErrorRef = useRef(onError);
  onErrorRef.current = onError;

  const isPollingRef = useRef(isPolling);
  isPollingRef.current = isPolling;

  const clearTimer = useCallback(() => {
    if (timeoutIdRef.current !== null) {
      clearTimeout(timeoutIdRef.current as number);
      timeoutIdRef.current = null;
    }
  }, []);

  const stopPolling = useCallback(() => {
    clearTimer();
    setIsPolling(false);
  }, [clearTimer]);

  const poll = useCallback(async () => {
    clearTimer();

    try {
      const result = await fnRef.current();

      if (!isMountedRef.current) return;

      setData(result);
      setError(null);
      setIsLoading(false);
      onSuccessRef.current?.(result);

      // Check if terminal state reached (e.g. complete / failed)
      if (isTerminalRef.current(result)) {
        setIsPolling(false);
        return;
      }

      // Schedule next poll if still enabled and active
      if (isMountedRef.current && isPollingRef.current) {
        timeoutIdRef.current = setTimeout(() => {
          if (isMountedRef.current && isPollingRef.current) {
            poll();
          }
        }, intervalMs);
      }
    } catch (err: unknown) {
      if (!isMountedRef.current) return;

      const parsedError = err instanceof Error ? err : new Error(String(err));
      setError(parsedError);
      setIsLoading(false);
      onErrorRef.current?.(parsedError);

      // Schedule next poll even on transient error
      if (isMountedRef.current && isPollingRef.current) {
        timeoutIdRef.current = setTimeout(() => {
          if (isMountedRef.current && isPollingRef.current) {
            poll();
          }
        }, intervalMs);
      }
    }
  }, [clearTimer, intervalMs]);

  const restartPolling = useCallback(() => {
    setIsLoading(true);
    if (!isPollingRef.current) {
      setIsPolling(true);
    } else {
      poll();
    }
  }, [poll]);

  const refetch = useCallback(async () => {
    setIsLoading(true);
    await poll();
  }, [poll]);

  // Main polling lifecycle
  useEffect(() => {
    isMountedRef.current = true;

    if (enabled && isPolling) {
      poll();
    } else {
      clearTimer();
    }

    return () => {
      isMountedRef.current = false;
      clearTimer();
    };
  }, [enabled, isPolling, poll, clearTimer]);

  return {
    data,
    error,
    isLoading,
    isPolling,
    stopPolling,
    restartPolling,
    refetch,
  };
}

export default usePolling;
