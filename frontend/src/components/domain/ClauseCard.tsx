import React from 'react';
import { Sparkles, Info, AlertOctagon, HelpCircle } from 'lucide-react';
import { Card, CardContent } from '../ui/Card';
import { RiskBadge } from './RiskBadge';
import { RiskCategoryTag } from './RiskCategoryTag';
import { cn } from '../../utils/cn';
import type { ClauseItem } from '../../types';

export interface ClauseCardProps {
  clause: ClauseItem;
  documentId: string;
  className?: string;
  lang?: string;
}

const formatDate = (isoString?: string): string => {
  if (!isoString) return '12/09/2026';
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return '12/09/2026';
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();
    return `${day}/${month}/${year}`;
  } catch {
    return '12/09/2026';
  }
};

export const ClauseCard: React.FC<ClauseCardProps> = ({
  clause,
  className,
  lang = 'en',
}) => {
  const isFailed = clause.status === 'failed' || clause.severity === null;

  // PRD Ch. 16.5: Explicit "couldn't be classified" card state
  if (isFailed) {
    return (
      <Card
        elevation="sm"
        className={cn(
          'border-l-4 border-l-amber-500 border-secondary-200 bg-white rounded-2xl shadow-sm p-6 sm:p-8 space-y-5',
          className
        )}
        data-testid={`clause-card-${clause.id}`}
        role="article"
        aria-label={`Clause ${clause.position}: Classification Failed`}
      >
        <CardContent className="p-0 space-y-4">
          {/* Header Metadata */}
          <div className="space-y-1.5 pb-3 border-b border-secondary-100">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-bold font-mono px-2 py-0.5 rounded bg-secondary-100 text-secondary-800">
                Clause #{clause.position}
              </span>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-900 border border-amber-300">
                <HelpCircle className="w-3.5 h-3.5 text-amber-700" aria-hidden="true" />
                <span>Classification Incomplete</span>
              </span>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-secondary-100 text-secondary-600">
                ID: {clause.id}
              </span>
              <span className="text-xs text-secondary-500 italic">
                (Preserved verbatim without defaulting to Safe per PRD Ch. 16.5)
              </span>
            </div>

            <h3 className="text-2xl font-serif font-bold text-primary-950 pt-1">
              Clause #{clause.position} Inspection View
            </h3>
            <p className="text-xs text-secondary-500">
              Comprehensive legal analysis, risk breakdown, and recommended counter-terms.
            </p>
          </div>

          {/* Failure Alert Banner */}
          <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 flex items-start gap-3">
            <AlertOctagon className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" aria-hidden="true" />
            <div className="text-xs text-amber-900 space-y-0.5">
              <p className="font-semibold">This clause could not be classified automatically.</p>
              <p className="text-amber-800 leading-relaxed">
                {clause.explanation ||
                  'The AI analysis pipeline encountered conflicting international cross-references or ambiguous non-standard dialect. Manual legal review is recommended.'}
              </p>
            </div>
          </div>

          {/* Verbatim Original Text */}
          <div className="p-4 sm:p-5 rounded-xl border border-secondary-200 bg-white font-serif text-sm text-secondary-900 leading-relaxed select-text">
            &ldquo;{clause.original_text}&rdquo;
          </div>
        </CardContent>
      </Card>
    );
  }

  const simplifiedText =
    lang === 'hi' && clause.simplified_text_hi
      ? clause.simplified_text_hi
      : clause.simplified_text;

  const explanationText =
    lang === 'hi' && clause.why_flagged_hi
      ? clause.why_flagged_hi
      : clause.explanation;

  return (
    <Card
      elevation="sm"
      className={cn(
        'border border-secondary-200 bg-white rounded-2xl shadow-sm p-6 sm:p-8 space-y-6 transition-all hover:border-secondary-300',
        className
      )}
      data-testid={`clause-card-${clause.id}`}
      role="article"
      aria-label={`Clause ${clause.position}, Severity ${clause.severity}, Category ${clause.category}`}
    >
      <CardContent className="p-0 space-y-6">
        {/* Top Badges & Heading */}
        <div className="space-y-2 pb-2 border-b border-secondary-100">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-bold font-mono px-2 py-0.5 rounded bg-secondary-100 text-secondary-800">
              Clause #{clause.position}
            </span>
            {clause.severity && <RiskBadge severity={clause.severity} size="md" />}
            {clause.category && <RiskCategoryTag category={clause.category} size="md" />}
            <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-secondary-100 text-secondary-700">
              ID: {clause.id}
            </span>
          </div>

          <div>
            <h3 className="text-2xl sm:text-3xl font-serif font-bold text-primary-950">
              Clause #{clause.position} Inspection View
            </h3>
            <p className="text-xs sm:text-sm text-secondary-500 mt-0.5">
              Comprehensive legal analysis, risk breakdown, and recommended counter-terms.
            </p>
          </div>
        </div>

        {/* Two-Column Side-by-Side Cards (Responsive Grid) */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-stretch">
          {/* Left Column: Original Contract Text */}
          <div className="p-5 sm:p-6 rounded-xl border border-secondary-200 bg-white flex flex-col justify-between h-full">
            <div>
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-semibold text-secondary-900">Original Contract Text</h4>
                <span className="text-xs text-secondary-400 font-sans">Verbatim Source</span>
              </div>
              <p className="text-xs text-secondary-400 mt-0.5">
                Exact verbatim extract parsed from source document.
              </p>

              <div className="mt-4 p-4 sm:p-5 rounded-xl border border-secondary-200 bg-white text-secondary-900 font-serif text-sm leading-relaxed whitespace-pre-wrap select-text shadow-2xs">
                &ldquo;{clause.original_text}&rdquo;
              </div>
            </div>

            <div className="mt-6 pt-3 border-t border-secondary-100 flex items-center justify-between text-xs text-secondary-500 font-sans">
              <span>Position: Index #{clause.position}</span>
              <span>Extracted: {formatDate(clause.created_at)}</span>
            </div>
          </div>

          {/* Right Column: Plain-English Breakdown & Risk Driver */}
          <div className="p-5 sm:p-6 rounded-xl border border-secondary-200 bg-white flex flex-col justify-between h-full space-y-4">
            <div>
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-semibold text-secondary-900">
                  Plain-English Breakdown &amp; Risk Driver
                </h4>
                <Sparkles className="w-4 h-4 text-primary-600" aria-hidden="true" />
              </div>
              <p className="text-xs text-secondary-400 mt-0.5">
                Simplified representation for non-lawyers and business decision-makers.
              </p>
            </div>

            <div className="space-y-4 flex-1">
              {/* Box 1: WHAT THIS MEANS */}
              <div className="p-4 rounded-xl border border-secondary-200 bg-white space-y-1.5 shadow-2xs">
                <p className="text-[11px] font-bold uppercase tracking-wider text-secondary-700">
                  {lang === 'hi' ? 'इसका क्या अर्थ है (WHAT THIS MEANS)' : 'WHAT THIS MEANS'}
                </p>
                <p className="text-xs sm:text-sm text-secondary-900 leading-relaxed font-sans">
                  {simplifiedText || 'No plain-English summary available.'}
                </p>
              </div>

              {/* Box 2: RISK SEVERITY RATIONALE */}
              <div className="p-4 rounded-xl border border-secondary-200 bg-white space-y-1.5 shadow-2xs">
                <p className="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-secondary-700">
                  <Info className="w-3.5 h-3.5 text-secondary-500" aria-hidden="true" />
                  <span>
                    {lang === 'hi'
                      ? 'जोखिम गंभीरता का कारण (RISK SEVERITY RATIONALE)'
                      : 'RISK SEVERITY RATIONALE'}
                  </span>
                </p>
                <p className="text-xs sm:text-sm text-secondary-700 leading-relaxed font-sans">
                  {explanationText ||
                    'Standard contractual clause aligning with legal commercial baselines.'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default ClauseCard;
