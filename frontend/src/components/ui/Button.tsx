import React from 'react';
import { cn } from '../../utils/cn';
import { Spinner } from './Spinner';

export type ButtonVariant = 'primary' | 'secondary' | 'tertiary' | 'destructive';
export type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    'bg-accent text-white hover:bg-accent-hover active:bg-accent-active shadow-elevation-1 border border-transparent',
  secondary:
    'bg-white text-primary border border-neutral-border hover:bg-neutral-subtle hover:border-neutral-text-secondary active:bg-neutral-border/30 shadow-elevation-1',
  tertiary:
    'bg-transparent text-accent hover:bg-accent-light active:bg-accent-light/80 border border-transparent',
  destructive:
    'bg-risk-high text-white hover:bg-[#992E2E] active:bg-[#802626] shadow-elevation-1 border border-transparent',
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'text-caption py-1.5 px-3 rounded-control gap-1.5 font-medium',
  md: 'text-body py-2 px-4 rounded-control gap-2 font-medium',
  lg: 'text-body-lg py-2.5 px-5 rounded-control gap-2.5 font-semibold',
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      variant = 'primary',
      size = 'md',
      isLoading = false,
      disabled = false,
      leftIcon,
      rightIcon,
      className,
      type = 'button',
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || isLoading;

    return (
      <button
        ref={ref}
        type={type}
        disabled={isDisabled}
        aria-busy={isLoading}
        className={cn(
          'inline-flex items-center justify-center transition-all duration-micro select-none',
          'focus-ring',
          variantStyles[variant],
          sizeStyles[size],
          isDisabled && 'opacity-50 cursor-not-allowed pointer-events-none shadow-none',
          className
        )}
        {...props}
      >
        {isLoading ? (
          <>
            <Spinner
              size={size === 'lg' ? 'md' : 'sm'}
              variant={variant === 'primary' || variant === 'destructive' ? 'white' : 'accent'}
              className="mr-1.5"
            />
            <span>{children}</span>
          </>
        ) : (
          <>
            {leftIcon && <span className="inline-flex shrink-0">{leftIcon}</span>}
            <span>{children}</span>
            {rightIcon && <span className="inline-flex shrink-0">{rightIcon}</span>}
          </>
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';

export default Button;
