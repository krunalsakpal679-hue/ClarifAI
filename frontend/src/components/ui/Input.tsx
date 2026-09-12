import React from 'react';
import { cn } from '../../utils/cn';

export interface InputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  label?: string;
  helperText?: string;
  error?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  inputSize?: 'sm' | 'md' | 'lg';
}

const sizeClasses: Record<'sm' | 'md' | 'lg', string> = {
  sm: 'py-1.5 px-2.5 text-caption',
  md: 'py-2 px-3 text-body',
  lg: 'py-2.5 px-3.5 text-body-lg',
};

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      helperText,
      error,
      leftIcon,
      rightIcon,
      inputSize = 'md',
      disabled = false,
      required = false,
      id,
      className,
      ...props
    },
    ref
  ) => {
    const generatedId = React.useId();
    const inputId = id || generatedId;
    const helperId = `${inputId}-helper`;
    const errorId = `${inputId}-error`;

    const hasError = Boolean(error);

    return (
      <div className="w-full flex flex-col gap-1.5 text-left">
        {label && (
          <label
            htmlFor={inputId}
            className="text-label font-medium text-primary flex items-center gap-1 select-none"
          >
            {label}
            {required && <span className="text-risk-high font-bold">*</span>}
          </label>
        )}

        <div className="relative flex items-center w-full">
          {leftIcon && (
            <div className="absolute left-3 text-neutral-text-secondary pointer-events-none flex items-center justify-center">
              {leftIcon}
            </div>
          )}

          <input
            ref={ref}
            id={inputId}
            disabled={disabled}
            required={required}
            aria-invalid={hasError}
            aria-describedby={
              hasError ? errorId : helperText ? helperId : undefined
            }
            className={cn(
              'w-full rounded-control border bg-white text-primary transition-all duration-micro',
              'placeholder:text-neutral-text-secondary/60',
              sizeClasses[inputSize],
              leftIcon && 'pl-9',
              rightIcon && 'pr-9',
              // Normal state
              !hasError &&
                'border-neutral-border hover:border-neutral-text-secondary/70 focus:border-accent focus:ring-2 focus:ring-accent/20 focus:outline-none',
              // Error state
              hasError &&
                'border-risk-high bg-risk-high-bg/30 text-risk-high-text focus:border-risk-high focus:ring-2 focus:ring-risk-high/20 focus:outline-none',
              // Disabled state
              disabled &&
                'bg-neutral-subtle opacity-60 cursor-not-allowed pointer-events-none border-neutral-border/70',
              className
            )}
            {...props}
          />

          {rightIcon && (
            <div className="absolute right-3 text-neutral-text-secondary flex items-center justify-center">
              {rightIcon}
            </div>
          )}
        </div>

        {hasError ? (
          <p id={errorId} className="text-caption text-risk-high font-medium" role="alert">
            {error}
          </p>
        ) : helperText ? (
          <p id={helperId} className="text-caption text-neutral-text-secondary">
            {helperText}
          </p>
        ) : null}
      </div>
    );
  }
);

Input.displayName = 'Input';

export default Input;
