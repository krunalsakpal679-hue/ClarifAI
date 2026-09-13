import React from 'react';
import { AlertTriangle, AlertCircle, Info, CheckCircle2, Clock } from 'lucide-react';
import { cn } from '../../utils/cn';
import type { DocumentOverallRisk } from '../../types';

export interface RiskLevelIndicatorProps extends React.HTMLAttributes<HTMLSpanElement> {
  risk: DocumentOverallRisk;
  className?: string;
  size?: 'sm' | 'md';
}

interface RiskConfig {
  label: string;
  ariaLabel: string;
  icon: React.ReactNode;
  classes: string;
}

export const RiskLevelIndicator: React.FC<RiskLevelIndicatorProps> = ({
  risk,
  className,
  size = 'md',
  ...props
}) => {
  const configs: Record<NonNullable<DocumentOverallRisk>, RiskConfig> = {
    high: {
      label: 'High Risk',
      ariaLabel: 'Risk Level: High Risk (immediate counsel attention recommended)',
      icon: <AlertTriangle className="w-3.5 h-3.5 shrink-0 text-red-600" aria-hidden="true" />,
      classes: 'bg-red-50 text-red-700 border-red-200 font-semibold',
    },
    moderate: {
      label: 'Moderate Risk',
      ariaLabel: 'Risk Level: Moderate Risk (review key clauses)',
      icon: <AlertCircle className="w-3.5 h-3.5 shrink-0 text-amber-600" aria-hidden="true" />,
      classes: 'bg-amber-50 text-amber-800 border-amber-200 font-semibold',
    },
    low: {
      label: 'Low Risk',
      ariaLabel: 'Risk Level: Low Risk (minor deviations noted)',
      icon: <Info className="w-3.5 h-3.5 shrink-0 text-blue-600" aria-hidden="true" />,
      classes: 'bg-blue-50 text-blue-700 border-blue-200 font-medium',
    },
    safe: {
      label: 'Safe',
      ariaLabel: 'Risk Level: Safe (standard balanced provisions)',
      icon: <CheckCircle2 className="w-3.5 h-3.5 shrink-0 text-emerald-600" aria-hidden="true" />,
      classes: 'bg-emerald-50 text-emerald-700 border-emerald-200 font-medium',
    },
  };

  const current = risk ? configs[risk] : null;

  if (!current) {
    return (
      <span
        role="status"
        aria-label="Risk Level: Pending Analysis"
        className={cn(
          'inline-flex items-center gap-1.5 rounded-full border border-secondary-200 bg-secondary-50 text-secondary-600',
          size === 'sm' ? 'px-2 py-0.5 text-[11px]' : 'px-2.5 py-1 text-xs',
          className
        )}
        {...props}
      >
        <Clock className="w-3.5 h-3.5 shrink-0 text-secondary-500" aria-hidden="true" />
        <span>Risk Pending</span>
      </span>
    );
  }

  return (
    <span
      role="status"
      aria-label={current.ariaLabel}
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border',
        current.classes,
        size === 'sm' ? 'px-2 py-0.5 text-[11px]' : 'px-2.5 py-1 text-xs',
        className
      )}
      {...props}
    >
      {current.icon}
      <span>{current.label}</span>
    </span>
  );
};
