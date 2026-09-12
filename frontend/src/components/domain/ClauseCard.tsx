import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, AlertOctagon, HelpCircle, ShieldAlert } from 'lucide-react';
import { Card, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { RiskBadge } from './RiskBadge';
import { RiskCategoryTag } from './RiskCategoryTag';
import { cn } from '../../utils/cn';
import type { ClauseItem } from '../../types';

export interface ClauseCardProps {
  clause: ClauseItem;
  documentId: string;
  className?: string;
}

export const ClauseCard: React.FC<ClauseCardProps> = ({
  clause,
  documentId,
  className,
}) => {
  const isFailed = clause.status === 'failed' || clause.severity === null;

  // PRD Ch. 16.5: Explicit "couldn't be classified" card state
  if (isFailed) {
    return (
      <Card
        elevation="sm"
        className={cn(
          'border-l-4 border-l-amber-500 border-secondary-200 bg-amber-50/20 hover:border-amber-400 transition-colors',
          className
        )}
        data-testid={`clause-card-${clause.id}`}
        role="article"
        aria-label={`Clause ${clause.position}: Classification Failed`}
      >
        <CardContent className="p-5 sm:p-6 space-y-4">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-secondary-100">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-bold font-mono px-2 py-0.5 rounded bg-secondary-100 text-secondary-800">
                Clause #{clause.position}
              </span>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-900 border border-amber-300">
                <HelpCircle className="w-3.5 h-3.5 text-amber-700" aria-hidden="true" />
                <span>Classification Incomplete</span>
              </span>
              <span className="text-xs text-secondary-500 italic">
                (Preserved verbatim without defaulting to Safe per PRD Ch. 16.5)
              </span>
            </div>

            <Link
              to={`/documents/${documentId}/clauses/${clause.id}`}
              className="self-start sm:self-auto shrink-0"
            >
              <Button variant="ghost" size="sm" className="text-xs text-primary-700 hover:text-primary-900 gap-1.5">
                <span>View Full Details</span>
                <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
              </Button>
            </Link>
          </div>

          {/* Failure Alert Banner */}
          <div className="p-3.5 rounded-lg bg-amber-100/60 border border-amber-200 flex items-start gap-3">
            <AlertOctagon className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" aria-hidden="true" />
            <div className="text-xs text-amber-900 space-y-0.5">
              <p className="font-semibold">This clause could not be classified automatically.</p>
              <p className="text-amber-800 leading-relaxed">
                {clause.explanation ||
                  'The AI analysis pipeline encountered complex statutory cross-references or ambiguous non-standard dialect. Manual legal review is recommended.'}
              </p>
            </div>
          </div>

          {/* Verbatim Original Text */}
          <div className="space-y-1.5">
            <h4 className="text-xs font-bold uppercase tracking-wider text-secondary-600">
              Original Verbatim Contract Text
            </h4>
            <div className="p-3.5 rounded-lg bg-white border border-secondary-200 font-serif text-xs text-primary-950 leading-relaxed select-text">
              &ldquo;{clause.original_text}&rdquo;
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Standard Classified Clause Card
  return (
    <Card
      elevation="sm"
      className={cn(
        'border-secondary-200 hover:border-primary-300 hover:shadow-md transition-all duration-200',
        className
      )}
      data-testid={`clause-card-${clause.id}`}
      role="article"
      aria-label={`Clause ${clause.position}, Severity ${clause.severity}, Category ${clause.category}`}
    >
      <CardContent className="p-5 sm:p-6 space-y-4">
        {/* Header Metadata */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-secondary-100">
          <div className="flex flex-wrap items-center gap-2.5">
            <span className="text-xs font-bold font-mono px-2.5 py-0.5 rounded bg-secondary-100 text-secondary-800">
              Clause #{clause.position}
            </span>
            <RiskBadge severity={clause.severity} size="sm" />
            {clause.category && <RiskCategoryTag category={clause.category} size="sm" />}
          </div>

          <Link
            to={`/documents/${documentId}/clauses/${clause.id}`}
            className="self-start sm:self-auto shrink-0"
          >
            <Button
              variant="outline"
              size="sm"
              className="text-xs text-primary-700 hover:bg-primary-50 gap-1.5"
            >
              <span>Inspect Clause Details</span>
              <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
            </Button>
          </Link>
        </div>

        {/* 1. Simplified Plain-English Rewrite */}
        <div className="space-y-1">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-bold uppercase tracking-wider text-primary-900">
              Plain-English Summary
            </h4>
            <span className="text-[11px] text-secondary-400 font-medium">AI Simplified</span>
          </div>
          <div className="p-3.5 rounded-lg bg-primary-50/50 border border-primary-100 text-sm text-primary-950 font-medium leading-relaxed">
            {clause.simplified_text}
          </div>
        </div>

        {/* 2. Legal Explanation / Risk Driver */}
        {clause.explanation && (
          <div className="space-y-1">
            <h4 className="text-xs font-bold uppercase tracking-wider text-secondary-600">
              Risk Driver &amp; Legal Context
            </h4>
            <p className="text-xs text-secondary-700 leading-relaxed pl-3 border-l-2 border-primary-300">
              {clause.explanation}
            </p>
          </div>
        )}

        {/* Rule Findings Tags (if any) */}
        {clause.rule_findings && clause.rule_findings.length > 0 && (
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <span className="text-[11px] font-semibold text-secondary-500">Heuristic Flags:</span>
            {clause.rule_findings.map((rule) => (
              <span
                key={rule.rule_id}
                className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-red-50 text-red-800 border border-red-200"
              >
                <ShieldAlert className="w-3 h-3 text-red-600" aria-hidden="true" />
                <span>{rule.rule_name || rule.rule_id}</span>
              </span>
            ))}
          </div>
        )}

        {/* 3. Original Verbatim Contract Text (collapsible or visually distinct quote) */}
        <div className="space-y-1 pt-1">
          <h4 className="text-xs font-bold uppercase tracking-wider text-secondary-500">
            Original Contract Text
          </h4>
          <div className="p-3 rounded-lg bg-secondary-50/80 border border-secondary-200/80 font-serif text-xs text-secondary-700 leading-relaxed max-h-32 overflow-y-auto select-text">
            &ldquo;{clause.original_text}&rdquo;
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default ClauseCard;
