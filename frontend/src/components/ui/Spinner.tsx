import React from 'react';
import { cn } from '../../utils/cn';

export interface SpinnerProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: 'sm' | 'md' | 'lg';
  variant?: 'primary' | 'accent' | 'white';
  label?: string;
}

const sizeClasses: Record<'sm' | 'md' | 'lg', string> = {
  sm: 'w-4 h-4 border-2',
  md: 'w-6 h-6 border-2',
  lg: 'w-8 h-8 border-3',
};

const variantClasses: Record<'primary' | 'accent' | 'white', string> = {
  primary: 'border-primary/20 border-t-primary',
  accent: 'border-accent/20 border-t-accent',
  white: 'border-white/20 border-t-white',
};

export const Spinner: React.FC<SpinnerProps> = ({
  size = 'md',
  variant = 'accent',
  label = 'Loading...',
  className,
  ...props
}) => {
  return (
    <div
      role="status"
      aria-label={label}
      className={cn('inline-flex items-center justify-center', className)}
      {...props}
    >
      <div
        className={cn(
          'rounded-full animate-spin',
          sizeClasses[size],
          variantClasses[variant]
        )}
      />
      <span className="sr-only">{label}</span>
    </div>
  );
};

export default Spinner;
