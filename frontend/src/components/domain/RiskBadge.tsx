import React from 'react';
import { AlertTriangle, AlertCircle, Info, CheckCircle2, HelpCircle } from 'lucide-react';
import { cn } from '../../utils/cn';
import {
  type SeverityLevel,
  SEVERITY_DEFINITIONS,
  normalizeSeverity,
} from '../../constants/severityLevels';

export interface RiskBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  severity?: SeverityLevel | string | null;
  size?: 'sm' | 'md';
  className?: string;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({
  severity,
  size = 'md',
  className,
  ...props
}) => {
  const normalized = normalizeSeverity(severity);

  if (!normalized) {
    return (
      <span
        role="status"
        aria-label="Severity: Unclassified"
        className={cn(
          'inline-flex items-center rounded-full border border-solid font-medium bg-secondary-100 text-secondary-700 border-secondary-300',
          size === 'sm' ? 'px-2 py-0.5 text-[11px] gap-1' : 'px-2.5 py-1 text-xs gap-1.5',
          className
        )}
        {...props}
      >
        <HelpCircle className={size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5'} aria-hidden="true" />
        <span>Unclassified</span>
      </span>
    );
  }

  const def = SEVERITY_DEFINITIONS[normalized];

  const renderIcon = () => {
    const iconClass = size === 'sm' ? 'w-3 h-3 shrink-0' : 'w-3.5 h-3.5 shrink-0';
    switch (normalized) {
      case 'High':
        return <AlertTriangle className={iconClass} aria-hidden="true" />;
      case 'Moderate':
        return <AlertCircle className={iconClass} aria-hidden="true" />;
      case 'Low':
        return <Info className={iconClass} aria-hidden="true" />;
      case 'Safe':
        return <CheckCircle2 className={iconClass} aria-hidden="true" />;
    }
  };

  return (
    <span
      role="status"
      aria-label={`Severity: ${def.label}`}
      className={cn(
        'inline-flex items-center rounded-full border border-solid font-semibold transition-colors duration-200',
        def.badgeBg,
        def.badgeText,
        def.badgeBorder,
        size === 'sm' ? 'px-2 py-0.5 text-[11px] gap-1' : 'px-2.5 py-1 text-xs gap-1.5',
        className
      )}
      {...props}
    >
      {renderIcon()}
      <span>{def.label}</span>
    </span>
  );
};

export default RiskBadge;
