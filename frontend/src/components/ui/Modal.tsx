import React, { useEffect, useId } from 'react';
import { X } from 'lucide-react';
import { cn } from '../../utils/cn';

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  description,
  children,
  className,
}) => {
  const generatedId = useId();
  const titleId = `${generatedId}-title`;
  const descId = `${generatedId}-desc`;

  // Close on Escape key
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Lock background body scroll when open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6"
      role="presentation"
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-primary-950/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
        aria-hidden="true"
        data-testid="modal-backdrop"
      />

      {/* Modal Dialog Card */}
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? titleId : undefined}
        aria-describedby={description ? descId : undefined}
        className={cn(
          'relative w-full max-w-lg rounded-card bg-white p-6 shadow-elevation-3 border border-secondary-200 z-10 transition-all transform animate-in fade-in zoom-in-95',
          className
        )}
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-3 pb-3 border-b border-secondary-100">
          <div>
            {title && (
              <h2 id={titleId} className="text-lg font-serif font-bold text-primary-950">
                {title}
              </h2>
            )}
            {description && (
              <p id={descId} className="text-xs text-secondary-500 mt-0.5">
                {description}
              </p>
            )}
          </div>

          <button
            type="button"
            onClick={onClose}
            aria-label="Close dialog"
            className="p-1 rounded-md text-secondary-400 hover:text-primary-950 hover:bg-secondary-100 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <X className="w-5 h-5" aria-hidden="true" />
          </button>
        </div>

        {/* Content Body */}
        <div className="pt-4">{children}</div>
      </div>
    </div>
  );
};

export default Modal;
