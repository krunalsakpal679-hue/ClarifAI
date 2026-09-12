import React from 'react';
import { Badge } from '../ui/Badge';
import { Card, CardHeader, CardContent } from '../ui/Card';
import { FileText, ArrowRightLeft, MinusCircle, PlusCircle, CheckCircle2 } from 'lucide-react';
import { cn } from '../../utils/cn';
import type { ComparisonClauseItem } from '../../types/comparison';

export interface ComparisonClausePairProps {
  item: ComparisonClauseItem;
  docALabel?: string;
  docBLabel?: string;
  className?: string;
}

export const ComparisonClausePair: React.FC<ComparisonClausePairProps> = ({
  item,
  docALabel = 'Document A (Baseline)',
  docBLabel = 'Document B (Revised)',
  className,
}) => {
  const category = item.category;
  const isChanged = category === 'changed';
  const isMatched = category === 'matched';
  const isMissing = category === 'missing';

  const isAddedInB = isMissing && !item.text_a && Boolean(item.text_b);
  const isDeletedFromA = isMissing && Boolean(item.text_a) && !item.text_b;

  const similarityPercentage =
    typeof item.similarity_score === 'number'
      ? Math.round(item.similarity_score * 100)
      : null;

  return (
    <Card
      elevation="sm"
      className={cn('overflow-hidden border-secondary-200 shadow-sm transition-all', className)}
      data-testid={`comparison-clause-pair-${item.id || item.category}`}
    >
      {/* Pair Header */}
      <CardHeader className="py-3 px-4 sm:px-5 bg-secondary-50/70 border-b border-secondary-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
        <div className="flex items-center gap-2">
          {isChanged && (
            <span className="flex items-center gap-1 text-amber-700">
              <ArrowRightLeft className="w-4 h-4" aria-hidden="true" />
              <Badge variant="warning" size="sm">Changed Clause</Badge>
            </span>
          )}
          {isMatched && (
            <span className="flex items-center gap-1 text-emerald-700">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" aria-hidden="true" />
              <Badge variant="success" size="sm">Identical / Matched</Badge>
            </span>
          )}
          {isMissing && (
            <span className="flex items-center gap-1 text-red-700">
              {isAddedInB ? (
                <>
                  <PlusCircle className="w-4 h-4 text-primary-600" aria-hidden="true" />
                  <Badge variant="info" size="sm">Added in Revised</Badge>
                </>
              ) : (
                <>
                  <MinusCircle className="w-4 h-4 text-red-600" aria-hidden="true" />
                  <Badge variant="danger" size="sm">Deleted in Revised</Badge>
                </>
              )}
            </span>
          )}

          {/* Screen-reader status announcement */}
          <span className="sr-only">
            Classification: {category}.{' '}
            {isAddedInB ? 'Clause added in revised document.' : ''}
            {isDeletedFromA ? 'Clause removed from revised document.' : ''}
          </span>

          {similarityPercentage !== null && (
            <span className="text-[11px] font-mono font-medium text-secondary-600 bg-white px-2 py-0.5 rounded border border-secondary-200">
              {similarityPercentage}% match
            </span>
          )}
        </div>

        <div className="flex items-center gap-2 text-xs text-secondary-500 font-mono">
          {item.base_clause_id && (
            <span>Base: #{item.base_clause_id.replace('clause-', '')}</span>
          )}
          {item.base_clause_id && item.target_clause_id && <span>&harr;</span>}
          {item.target_clause_id && (
            <span>Target: #{item.target_clause_id.replace('clause-', '')}</span>
          )}
        </div>
      </CardHeader>

      {/* Difference Explanation Banner (if changed or explanation present) */}
      {item.difference_explanation && (
        <div className="p-3 sm:px-5 bg-amber-50/50 border-b border-amber-200/60 text-xs sm:text-sm text-secondary-800 flex items-start gap-2">
          <strong className="text-amber-900 shrink-0 font-semibold">Change Summary:</strong>
          <p className="leading-relaxed">{item.difference_explanation}</p>
        </div>
      )}

      {/* Side-by-Side Clause Texts (Degrading to Stacked on Mobile per PRD Ch. 24) */}
      <CardContent className="p-0">
        <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-secondary-200">
          {/* Baseline Clause A */}
          <div
            className={cn(
              'p-4 sm:p-5 space-y-2',
              isDeletedFromA ? 'bg-red-50/30' : 'bg-white'
            )}
            data-testid="clause-side-a"
          >
            <div className="flex items-center justify-between text-xs font-semibold text-secondary-600">
              <span className="flex items-center gap-1.5 text-primary-900">
                <FileText className="w-3.5 h-3.5 text-primary-700" aria-hidden="true" />
                <span>{docALabel}</span>
              </span>
              {item.position_a && (
                <span className="text-[11px] font-mono text-secondary-400">
                  Pos: {item.position_a}
                </span>
              )}
            </div>

            {item.text_a ? (
              <p className="text-xs sm:text-sm text-secondary-900 font-serif leading-relaxed whitespace-pre-wrap select-text">
                {item.text_a}
              </p>
            ) : (
              <p className="text-xs italic text-secondary-400 bg-secondary-50 p-3 rounded-lg border border-dashed border-secondary-300">
                [Clause was not present in baseline contract]
              </p>
            )}
          </div>

          {/* Comparison Target Clause B */}
          <div
            className={cn(
              'p-4 sm:p-5 space-y-2',
              isAddedInB ? 'bg-emerald-50/30' : 'bg-white'
            )}
            data-testid="clause-side-b"
          >
            <div className="flex items-center justify-between text-xs font-semibold text-secondary-600">
              <span className="flex items-center gap-1.5 text-accent-900">
                <FileText className="w-3.5 h-3.5 text-accent-700" aria-hidden="true" />
                <span>{docBLabel}</span>
              </span>
              {item.position_b && (
                <span className="text-[11px] font-mono text-secondary-400">
                  Pos: {item.position_b}
                </span>
              )}
            </div>

            {item.text_b ? (
              <p className="text-xs sm:text-sm text-secondary-900 font-serif leading-relaxed whitespace-pre-wrap select-text">
                {item.text_b}
              </p>
            ) : (
              <p className="text-xs italic text-red-500 bg-red-50/50 p-3 rounded-lg border border-dashed border-red-300">
                [Clause completely deleted in counterparty draft]
              </p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
