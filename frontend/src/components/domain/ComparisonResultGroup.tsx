import React from 'react';
import { Badge } from '../ui/Badge';
import { ComparisonClausePair } from './ComparisonClausePair';
import { ArrowRightLeft, CheckCircle2, AlertCircle } from 'lucide-react';
import { cn } from '../../utils/cn';
import type { ComparisonCategory, ComparisonClauseItem } from '../../types/comparison';

export interface ComparisonResultGroupProps {
  category: ComparisonCategory;
  items: ComparisonClauseItem[];
  docALabel?: string;
  docBLabel?: string;
  className?: string;
}

const CATEGORY_CONFIG: Record<
  ComparisonCategory,
  {
    title: string;
    description: string;
    badgeVariant: 'warning' | 'success' | 'danger';
    icon: React.ComponentType<{ className?: string }>;
    emptyMessage: string;
  }
> = {
  changed: {
    title: 'Changed Clauses',
    description: 'Clauses present in both documents with substantial wording or risk alterations.',
    badgeVariant: 'warning',
    icon: ArrowRightLeft,
    emptyMessage: 'No modified or changed clauses detected between these two documents.',
  },
  matched: {
    title: 'Matched / Unchanged Clauses',
    description: 'Clauses with identical or semantically identical legal obligations across drafts.',
    badgeVariant: 'success',
    icon: CheckCircle2,
    emptyMessage: 'No identical or unchanged clauses found.',
  },
  missing: {
    title: 'Missing & Added Clauses',
    description: 'Clauses deleted from the baseline contract or newly introduced in the target draft.',
    badgeVariant: 'danger',
    icon: AlertCircle,
    emptyMessage: 'No added or deleted clauses detected between these drafts.',
  },
};

export const ComparisonResultGroup: React.FC<ComparisonResultGroupProps> = ({
  category,
  items,
  docALabel,
  docBLabel,
  className,
}) => {
  const config = CATEGORY_CONFIG[category];
  const Icon = config.icon;

  return (
    <section
      aria-labelledby={`group-heading-${category}`}
      className={cn('space-y-4', className)}
      data-testid={`comparison-group-${category}`}
    >
      {/* Group Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-secondary-200">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-secondary-100 flex items-center justify-center text-secondary-700">
            <Icon className="w-4 h-4" aria-hidden="true" />
          </div>
          <div>
            <h2
              id={`group-heading-${category}`}
              className="text-base sm:text-lg font-semibold text-secondary-900 flex items-center gap-2"
            >
              <span>{config.title}</span>
              <Badge variant={config.badgeVariant} size="sm">
                {items.length} {items.length === 1 ? 'clause' : 'clauses'}
              </Badge>
            </h2>
            <p className="text-xs text-secondary-500">{config.description}</p>
          </div>
        </div>
      </div>

      {/* Items list or empty state */}
      {items.length > 0 ? (
        <div className="space-y-4">
          {items.map((item, idx) => (
            <ComparisonClausePair
              key={item.id || `item-${category}-${idx}`}
              item={item}
              docALabel={docALabel}
              docBLabel={docBLabel}
            />
          ))}
        </div>
      ) : (
        <div
          className="p-6 rounded-xl border border-dashed border-secondary-300 bg-secondary-50/50 text-center text-xs text-secondary-500"
          data-testid={`comparison-group-empty-${category}`}
        >
          {config.emptyMessage}
        </div>
      )}
    </section>
  );
};
