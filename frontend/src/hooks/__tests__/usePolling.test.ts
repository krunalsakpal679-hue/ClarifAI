import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { usePolling } from '../usePolling';

describe('usePolling Hook (hooks/usePolling)', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.clearAllTimers();
    vi.useRealTimers();
  });

  interface TestDoc {
    id: string;
    status: string;
  }

  it('executes poll immediately on mount and updates state', async () => {
    const fetchFn = vi.fn().mockResolvedValue({ id: 'doc-1', status: 'extracting' });

    const { result } = renderHook(() =>
      usePolling<TestDoc>({
        fn: fetchFn,
        intervalMs: 1000,
        isTerminal: (data) => data.status === 'complete',
      })
    );

    // Initial state before promise resolution
    expect(result.current.isLoading).toBe(true);
    expect(fetchFn).toHaveBeenCalledTimes(1);

    // Wait for promise resolution
    await act(async () => {
      await Promise.resolve();
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.data).toEqual({ id: 'doc-1', status: 'extracting' });
    expect(result.current.isPolling).toBe(true);
  });

  it('polls at regular interval while isTerminal is false', async () => {
    let callCount = 0;
    const fetchFn = vi.fn().mockImplementation(async () => {
      callCount++;
      return { id: 'doc-1', status: callCount >= 3 ? 'complete' : 'extracting' };
    });

    const { result } = renderHook(() =>
      usePolling<TestDoc>({
        fn: fetchFn,
        intervalMs: 2000,
        isTerminal: (data) => data.status === 'complete',
      })
    );

    await act(async () => {
      await Promise.resolve();
    });
    expect(fetchFn).toHaveBeenCalledTimes(1);

    // Advance 2 seconds -> poll 2
    await act(async () => {
      vi.advanceTimersByTime(2000);
      await Promise.resolve();
    });
    expect(fetchFn).toHaveBeenCalledTimes(2);

    // Advance another 2 seconds -> poll 3 (terminal)
    await act(async () => {
      vi.advanceTimersByTime(2000);
      await Promise.resolve();
    });
    expect(fetchFn).toHaveBeenCalledTimes(3);

    // Terminal state reached: isPolling should now be false
    expect(result.current.isPolling).toBe(false);

    // Advance another 2 seconds -> should NOT poll again
    await act(async () => {
      vi.advanceTimersByTime(2000);
      await Promise.resolve();
    });
    expect(fetchFn).toHaveBeenCalledTimes(3);
  });

  it('stops polling and clears timers on unmount', async () => {
    const fetchFn = vi.fn().mockResolvedValue({ id: 'doc-1', status: 'extracting' });

    const { unmount } = renderHook(() =>
      usePolling({
        fn: fetchFn,
        intervalMs: 3000,
        isTerminal: () => false,
      })
    );

    await act(async () => {
      await Promise.resolve();
    });
    expect(fetchFn).toHaveBeenCalledTimes(1);

    unmount();

    // Advance time after unmount
    await act(async () => {
      vi.advanceTimersByTime(6000);
      await Promise.resolve();
    });

    // Should not have polled after unmount
    expect(fetchFn).toHaveBeenCalledTimes(1);
  });

  it('supports manual stopPolling and restartPolling', async () => {
    const fetchFn = vi.fn().mockResolvedValue({ id: 'doc-1', status: 'extracting' });

    const { result } = renderHook(() =>
      usePolling({
        fn: fetchFn,
        intervalMs: 2000,
        isTerminal: () => false,
      })
    );

    await act(async () => {
      await Promise.resolve();
    });

    // Manually stop polling
    act(() => {
      result.current.stopPolling();
    });
    expect(result.current.isPolling).toBe(false);

    await act(async () => {
      vi.advanceTimersByTime(4000);
      await Promise.resolve();
    });
    expect(fetchFn).toHaveBeenCalledTimes(1);

    // Manually restart polling
    await act(async () => {
      result.current.restartPolling();
      await Promise.resolve();
    });
    expect(result.current.isPolling).toBe(true);
    expect(fetchFn).toHaveBeenCalledTimes(2);
  });
});
