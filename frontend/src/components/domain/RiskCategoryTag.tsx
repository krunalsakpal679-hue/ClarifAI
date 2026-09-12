import React from 'react';
import { Tag } from 'lucide-react';
import { cn } from '../../utils/cn';
import type { RiskCategory } from '../../constants/riskCategories';

export interface RiskCategoryTagProps extends React.HTMLAttributes<HTMLSpanElement> {
  category?: RiskCategory | string | null;
  size?: 'sm' | 'md';
  className?: string;
}

export const RiskCategoryTag: React.FC<RiskCategoryTagProps> = ({
  category,
  size = 'md',
  className,
  ...props
}) => {
  const displayLabel = category || 'General / Unclassified';

  return (
    <span
      role="note"
      aria-label={`Category: ${displayLabel}`}
      className={cn(
        'inline-flex items-center rounded-md font-medium border transition-colors',
        'bg-secondary-50 text-secondary-700 border-secondary-200',
        size === 'sm' ? 'px-2 py-0.5 text-[11px] gap-1' : 'px-2.5 py-0.5 text-xs gap-1.5',
        className
      )}
      {...props}
    >
      <Tag className={size === 'sm' ? 'w-2.5 h-2.5 shrink-0 text-secondary-500' : 'w-3 h-3 shrink-0 text-secondary-500'} aria-hidden="true" />
      <span>{displayLabel}</span>
    </span>
  );
};

export default RiskCategoryTag;
