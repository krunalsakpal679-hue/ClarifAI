/* eslint-disable react-refresh/only-export-components */
import React from 'react';
import { create } from 'zustand';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';
import { cn } from '../../utils/cn';

export type ToastType = 'success' | 'error' | 'info';

export interface ToastItem {
  id: string;
  type: ToastType;
  message: string;
  duration?: number;
}

interface ToastStore {
  toasts: ToastItem[];
  addToast: (type: ToastType, message: string, duration?: number) => void;
  removeToast: (id: string) => void;
}

export const useToastStore = create<ToastStore>((set) => ({
  toasts: [],
  addToast: (type, message, duration = 4000) => {
    const id = `toast_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
    set((state) => ({ toasts: [...state.toasts, { id, type, message, duration }] }));

    if (duration > 0) {
      setTimeout(() => {
        set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) }));
      }, duration);
    }
  },
  removeToast: (id) =>
    set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) })),
}));

export const toast = {
  success: (message: string, duration?: number) =>
    useToastStore.getState().addToast('success', message, duration),
  error: (message: string, duration?: number) =>
    useToastStore.getState().addToast('error', message, duration),
  info: (message: string, duration?: number) =>
    useToastStore.getState().addToast('info', message, duration),
};

export const ToastContainer: React.FC = () => {
  const { toasts, removeToast } = useToastStore();

  if (toasts.length === 0) return null;

  return (
    <div
      role="region"
      aria-label="Notifications"
      className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none"
    >
      {toasts.map((t) => (
        <div
          key={t.id}
          role="status"
          aria-live="polite"
          className={cn(
            'pointer-events-auto flex items-start gap-3 p-3.5 rounded-lg border shadow-elevation-3 transition-all duration-200 animate-in slide-in-from-bottom-2',
            t.type === 'success' && 'bg-emerald-50 border-emerald-200 text-emerald-950',
            t.type === 'error' && 'bg-red-50 border-red-200 text-red-950',
            t.type === 'info' && 'bg-blue-50 border-blue-200 text-blue-950'
          )}
        >
          <div className="shrink-0 mt-0.5">
            {t.type === 'success' && <CheckCircle2 className="w-4 h-4 text-emerald-600" aria-hidden="true" />}
            {t.type === 'error' && <AlertCircle className="w-4 h-4 text-red-600" aria-hidden="true" />}
            {t.type === 'info' && <Info className="w-4 h-4 text-blue-600" aria-hidden="true" />}
          </div>

          <p className="flex-1 text-xs font-medium leading-relaxed">{t.message}</p>

          <button
            type="button"
            onClick={() => removeToast(t.id)}
            aria-label="Close notification"
            className="shrink-0 text-secondary-500 hover:text-secondary-800 p-0.5 rounded focus:outline-none focus:ring-2 focus:ring-accent-500"
          >
            <X className="w-3.5 h-3.5" aria-hidden="true" />
          </button>
        </div>
      ))}
    </div>
  );
};
