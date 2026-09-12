import React from 'react';
import {
  AlertTriangle,
  AlertCircle,
  Info,
  CheckCircle2,
  Clock,
  Loader2,
  XCircle,
} from 'lucide-react';
import { cn } from '../../utils/cn';

export type RiskSeverityVariant = 'HIGH' | 'MODERATE' | 'LOW' | 'SAFE';
export type ProcessingStatusVariant = 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'outline' | 'neutral';
  severity?: RiskSeverityVariant;
  status?: ProcessingStatusVariant;
  size?: 'sm' | 'md';
  icon?: React.ReactNode;
}

const severityConfig: Record<
  RiskSeverityVariant,
  { label: string; icon: React.ReactNode; className: string }
> = {
  HIGH: {
    label: 'High Risk',
    icon: <AlertTriangle className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />,
    className:
      'bg-risk-high-bg text-risk-high border-risk-high-border font-semibold',
  },
  MODERATE: {
    label: 'Moderate Risk',
    icon: <AlertCircle className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />,
    className:
      'bg-risk-moderate-bg text-risk-moderate border-risk-moderate-border font-semibold',
  },
  LOW: {
    label: 'Low Risk',
    icon: <Info className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />,
    className:
      'bg-risk-low-bg text-risk-low border-risk-low-border font-medium',
  },
  SAFE: {
    label: 'Safe',
    icon: <CheckCircle2 className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />,
    className:
      'bg-risk-safe-bg text-risk-safe border-risk-safe-border font-medium',
  },
};

const statusConfig: Record<
  ProcessingStatusVariant,
  { label: string; icon: React.ReactNode; className: string }
> = {
  QUEUED: {
    label: 'Queued',
    icon: <Clock className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />,
    className: 'bg-neutral-subtle text-neutral-text-secondary border-neutral-border',
  },
  PROCESSING: {
    label: 'Processing',
    icon: <Loader2 className="w-3.5 h-3.5 shrink-0 animate-spin" aria-hidden="true" />,
    className: 'bg-accent-light text-accent border-accent/30',
  },
  COMPLETED: {
    label: 'Complete',
    icon: <CheckCircle2 className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />,
    className: 'bg-risk-safe-bg text-risk-safe border-risk-safe-border',
  },
  FAILED: {
    label: 'Failed',
    icon: <XCircle className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />,
    className: 'bg-risk-high-bg text-risk-high border-risk-high-border',
  },
};

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  severity,
  status,
  size = 'md',
  icon,
  className,
  ...props
}) => {
  // If severity is provided, enforce PRD WCAG rule: icon + label paired
  if (severity) {
    const config = severityConfig[severity];
    return (
      <span
        className={cn(
          'inline-flex items-center rounded-full border border-solid transition-colors duration-micro',
          size === 'sm' ? 'px-2 py-0.5 text-[11px] gap-1' : 'px-2.5 py-1 text-caption gap-1.5',
          config.className,
          className
        )}
        {...props}
      >
        {config.icon}
        <span>{children || config.label}</span>
      </span>
    );
  }

  // If processing status is provided
  if (status) {
    const config = statusConfig[status];
    return (
      <span
        className={cn(
          'inline-flex items-center rounded-full border border-solid transition-colors duration-micro',
          size === 'sm' ? 'px-2 py-0.5 text-[11px] gap-1' : 'px-2.5 py-1 text-caption gap-1.5',
          config.className,
          className
        )}
        {...props}
      >
        {config.icon}
        <span>{children || config.label}</span>
      </span>
    );
  }

  // Standard category or general badge
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full font-medium transition-colors duration-micro',
        size === 'sm' ? 'px-2 py-0.5 text-[11px] gap-1' : 'px-2.5 py-0.5 text-caption gap-1.5',
        variant === 'default' &&
          'bg-accent-light text-accent border border-accent/20',
        variant === 'outline' &&
          'bg-white text-primary border border-neutral-border',
        variant === 'neutral' &&
          'bg-neutral-subtle text-neutral-text-secondary border border-neutral-border',
        className
      )}
      {...props}
    >
      {icon && <span className="inline-flex shrink-0">{icon}</span>}
      <span>{children}</span>
    </span>
  );
};

export default Badge;
