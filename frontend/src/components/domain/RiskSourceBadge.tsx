import React from 'react';
import { Cpu, ShieldCheck, Scale } from 'lucide-react';
import { cn } from '../../utils/cn';

export interface RiskSourceBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  source?: string | null;
  size?: 'sm' | 'md';
  className?: string;
}

export const RiskSourceBadge: React.FC<RiskSourceBadgeProps> = ({
  source,
  size = 'sm',
  className,
  ...props
}) => {
  if (!source) return null;

  const normalized = source.toUpperCase().trim();
  let label = 'Model Prediction';
  let Icon = Cpu;
  let colorClasses = 'bg-slate-100 text-slate-700 border-slate-300';

  if (normalized === 'RULE_PRECEDENCE') {
    label = 'Rule Precedence';
    Icon = ShieldCheck;
    colorClasses = 'bg-indigo-50 text-indigo-700 border-indigo-200';
  } else if (normalized === 'AGREED') {
    label = 'Agreed (Rules & BERT)';
    Icon = Scale;
    colorClasses = 'bg-emerald-50 text-emerald-700 border-emerald-200';
  } else if (normalized === 'MODEL_CLASSIFICATION') {
    label = 'Legal-BERT Model';
    Icon = Cpu;
    colorClasses = 'bg-sky-50 text-sky-700 border-sky-200';
  } else {
    label = source;
  }

  return (
    <span
      role="note"
      aria-label={`Risk Provenance: ${label}`}
      data-testid="risk-source-badge"
      className={cn(
        'inline-flex items-center rounded font-mono font-medium border transition-colors',
        colorClasses,
        size === 'sm' ? 'px-2 py-0.5 text-[10px] gap-1' : 'px-2.5 py-0.5 text-xs gap-1.5',
        className
      )}
      {...props}
    >
      <Icon className={size === 'sm' ? 'w-2.5 h-2.5 shrink-0' : 'w-3 h-3 shrink-0'} aria-hidden="true" />
      <span>{label}</span>
    </span>
  );
};

export default RiskSourceBadge;
