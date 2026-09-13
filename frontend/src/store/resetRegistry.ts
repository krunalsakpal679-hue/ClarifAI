/**
 * Central Store Reset Registry (PRD Ch. 26.1 & Ch. 30.8)
 *
 * Provides decoupled registration for domain state resets on logout
 * to prevent circular module dependencies between authStore and domain stores.
 */

type ResetFn = () => void;

const resetHandlers: Set<ResetFn> = new Set();

export const registerResetHandler = (handler: ResetFn): (() => void) => {
  resetHandlers.add(handler);
  return () => resetHandlers.delete(handler);
};

export const resetAllDomainStores = (): void => {
  resetHandlers.forEach((handler) => {
    try {
      handler();
    } catch {
      // Graceful ignore in test runners
    }
  });
};
