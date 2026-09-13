import React from 'react';
import { FileText, AlertTriangle, ShieldCheck, Scale, Globe, RefreshCw } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { Skeleton } from '../ui/Skeleton';
import type { DocumentSummary } from '../../types';

export interface SummaryPanelProps {
  summary: DocumentSummary | null;
  isLoading: boolean;
  error?: string | null;
  onRetry?: () => void;
  lang?: string;
  className?: string;
}

export const SummaryPanel: React.FC<SummaryPanelProps> = ({
  summary,
  isLoading,
  error,
  onRetry,
  lang = 'en',
  className,
}) => {
  const isUntranslatedHindi = lang === 'hi' && summary?.translation_available === false;

  return (
    <Card elevation="sm" className={className} data-testid={isLoading ? 'summary-panel-skeleton' : error ? 'summary-panel-error' : 'summary-panel'}>
      <CardHeader className="pb-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <CardTitle className="text-lg sm:text-xl font-serif font-bold text-primary-950 flex items-center gap-2">
              <FileText className="w-5 h-5 text-primary-700 shrink-0" aria-hidden="true" />
              <span>Executive Plain-Language Summary</span>
            </CardTitle>
            <CardDescription className="text-xs text-secondary-500 mt-1">
              Synthesized by ClarifAI legal simplification models from extracted contractual provisions.
            </CardDescription>
          </div>

          {isUntranslatedHindi && (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-medium bg-amber-50 text-amber-800 border border-amber-200 self-start sm:self-auto">
              <Globe className="w-3 h-3 text-amber-600" aria-hidden="true" />
              <span>Hindi translation unavailable (English fallback)</span>
            </span>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-5">
        {isLoading && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-lg border border-secondary-100 space-y-2">
              <Skeleton className="h-5 w-40" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-5/6" />
            </div>
            <div className="p-4 rounded-lg border border-secondary-100 space-y-2">
              <Skeleton className="h-5 w-40" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-5/6" />
            </div>
            <div className="p-4 rounded-lg border border-secondary-100 space-y-2">
              <Skeleton className="h-5 w-40" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-5/6" />
            </div>
            <div className="p-4 rounded-lg border border-secondary-100 space-y-2">
              <Skeleton className="h-5 w-40" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-5/6" />
            </div>
          </div>
        )}

        {!isLoading && error && (
          <div className="p-6 text-center space-y-3">
            <AlertTriangle className="w-8 h-8 text-amber-500 mx-auto" aria-hidden="true" />
            <div className="space-y-1">
              <h3 className="text-base font-semibold text-primary-950">
                Executive Summary Unavailable
              </h3>
              <p className="text-xs text-secondary-600 max-w-md mx-auto">
                {error || 'Unable to load executive plain-language summary for this document.'}
              </p>
            </div>
            {onRetry && (
              <Button variant="outline" size="sm" onClick={onRetry} className="gap-1.5 text-xs">
                <RefreshCw className="w-3 h-3" aria-hidden="true" />
                <span>Retry Loading Summary</span>
              </Button>
            )}
          </div>
        )}

        {!isLoading && !error && summary && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* 1. Purpose & Scope */}
          <div className="p-4 rounded-lg bg-secondary-50/70 border border-secondary-200/80 space-y-1.5">
            <div className="flex items-center gap-2 text-primary-900 font-semibold text-sm">
              <FileText className="w-4 h-4 text-primary-700" aria-hidden="true" />
              <h4>Contract Purpose &amp; Scope</h4>
            </div>
            <p className="text-xs text-secondary-700 leading-relaxed">
              {summary.purpose_text}
            </p>
          </div>

          {/* 2. Key Liabilities & Risks */}
          <div className="p-4 rounded-lg bg-risk-high-bg/60 border border-risk-high-border/70 space-y-1.5">
            <div className="flex items-center gap-2 text-risk-high-text font-semibold text-sm">
              <AlertTriangle className="w-4 h-4 text-risk-high" aria-hidden="true" />
              <h4>Key Liabilities &amp; Risks</h4>
            </div>
            <p className="text-xs text-secondary-700 leading-relaxed">
              {summary.key_risks_text}
            </p>
          </div>

          {/* 3. Essential Terms */}
          <div className="p-4 rounded-lg bg-secondary-50/70 border border-secondary-200/80 space-y-1.5">
            <div className="flex items-center gap-2 text-primary-900 font-semibold text-sm">
              <Scale className="w-4 h-4 text-primary-700" aria-hidden="true" />
              <h4>Essential Commercial Terms</h4>
            </div>
            <p className="text-xs text-secondary-700 leading-relaxed">
              {summary.key_terms_text}
            </p>
          </div>

          {/* 4. Obligations */}
          <div className="p-4 rounded-lg bg-risk-safe-bg/60 border border-risk-safe-border/70 space-y-1.5">
            <div className="flex items-center gap-2 text-risk-safe-text font-semibold text-sm">
              <ShieldCheck className="w-4 h-4 text-risk-safe" aria-hidden="true" />
              <h4>Operational Obligations</h4>
            </div>
            <p className="text-xs text-secondary-700 leading-relaxed">
              {summary.obligations_text}
            </p>
          </div>
        </div>
      )}
    </CardContent>
    </Card>
  );
};

export default SummaryPanel;
