import React, { useEffect, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { Card, CardContent } from '../../components/ui/Card';
import { Skeleton } from '../../components/ui/Skeleton';
import {
  ComparisonConfidenceIndicator,
  ComparisonResultGroup,
  LanguageToggle,
  ReportDownloadButton,
} from '../../components/domain';
import {
  ArrowLeft,
  RotateCcw,
  AlertTriangle,
  AlertCircle,
  ArrowRightLeft,
  CheckCircle2,
  MinusCircle,
} from 'lucide-react';
import { useComparisonStore } from '../../store/comparisonStore';
import { useUiStore } from '../../store/uiStore';
import type { ComparisonClauseItem } from '../../types/comparison';

export const ComparisonResultsPage: React.FC = () => {
  const { t } = useTranslation();
  const { idA, idB, comparisonId } = useParams<{
    idA?: string;
    idB?: string;
    comparisonId?: string;
  }>();

  const { comparison, isLowConfidence, confidenceWarning, isLoading, error, fetchComparison } =
    useComparisonStore();

  const { analysisLanguage, setAnalysisLanguage } = useUiStore();

  // Resolved ID for fetch
  const effectiveId = useMemo(() => {
    if (comparisonId) return comparisonId;
    if (idA && idB) return `comp-${idA}-${idB}`;
    return '';
  }, [comparisonId, idA, idB]);

  // Document labels for display and routing contract
  const docALabel = comparison?.base_document_id || idA || 'doc-1';
  const docBLabel = comparison?.target_document_id || idB || 'doc-2';

  useEffect(() => {
    if (effectiveId) {
      fetchComparison(effectiveId, analysisLanguage);
    }
  }, [effectiveId, analysisLanguage, fetchComparison]);

  // Group clauses into the 3 categories
  const { changedItems, matchedItems, missingItems } = useMemo(() => {
    const results = comparison?.results || [];
    const changed: ComparisonClauseItem[] = [];
    const matched: ComparisonClauseItem[] = [];
    const missing: ComparisonClauseItem[] = [];

    results.forEach((item) => {
      if (item.category === 'changed') changed.push(item);
      else if (item.category === 'matched') matched.push(item);
      else if (item.category === 'missing') missing.push(item);
    });

    return { changedItems: changed, matchedItems: matched, missingItems: missing };
  }, [comparison]);

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-12" data-testid="comparison-results-page">
      {/* Breadcrumb Navigation */}
      <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-xs text-secondary-500">
        <Link to="/dashboard" className="hover:text-primary-700 hover:underline">
          Dashboard
        </Link>
        <span className="text-secondary-400">/</span>
        <Link to="/compare" className="hover:text-primary-700 hover:underline">
          Compare
        </Link>
        <span className="text-secondary-400">/</span>
        <span className="text-secondary-900 font-semibold" aria-current="page">
          Comparison Results
        </span>
      </nav>

      {/* Page Header with Persistent Title & Subtitle for Routing Invariant */}
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-secondary-200">
        <div className="space-y-1">
          <div className="flex items-center gap-2 mb-1">
            <Badge variant="info" size="sm" className="font-mono">
              Pairwise Analysis
            </Badge>
            {changedItems.length > 0 && (
              <Badge variant="warning" size="sm">
                {changedItems.length} Discrepancies
              </Badge>
            )}
          </div>
          <h1 className="text-2xl sm:text-3xl font-serif font-bold text-primary-950">
            Comparison Results
          </h1>
          <p className="text-xs sm:text-sm text-secondary-600 font-mono">
            Comparing: <strong className="text-secondary-900 font-semibold">{docALabel} vs {docBLabel}</strong>
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5 self-start md:self-auto">
          {/* Analysis Language Switch */}
          <LanguageToggle
            value={analysisLanguage}
            onChange={(nextLang) => setAnalysisLanguage(nextLang)}
          />

          {/* Two-Step Comparison Report Download Button */}
          <ReportDownloadButton
            reportType="comparison"
            targetId={effectiveId}
            lang={analysisLanguage}
            variant="outline"
            size="sm"
          />

          {/* Reconfigure Comparison Link */}
          <Link to="/compare">
            <Button variant="secondary" size="sm" className="gap-1.5 text-xs font-medium">
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>{t('comparison.configureNew', 'Configure New Comparison')}</span>
            </Button>
          </Link>
        </div>
      </header>

      {/* Loading skeleton view */}
      {isLoading && !comparison && (
        <div className="space-y-6 pt-2" data-testid="comparison-loading-skeleton">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Skeleton className="h-20" />
            <Skeleton className="h-20" />
            <Skeleton className="h-20" />
          </div>
          <Skeleton className="h-40" />
          <Skeleton className="h-40" />
        </div>
      )}

      {/* Error view */}
      {error && !comparison && (
        <div className="py-12 text-center space-y-4" data-testid="comparison-error-view">
          <div className="w-12 h-12 rounded-full bg-red-100 text-red-600 flex items-center justify-center mx-auto">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <h2 className="text-xl font-bold text-secondary-900">Comparison Failed to Load</h2>
          <p className="text-sm text-secondary-600 max-w-md mx-auto">{error}</p>
          <div className="flex justify-center gap-3 pt-2">
            <Link to="/compare">
              <Button variant="outline" size="sm">
                &larr; Return to Setup
              </Button>
            </Link>
            <Button
              variant="primary"
              size="sm"
              onClick={() => effectiveId && fetchComparison(effectiveId, analysisLanguage)}
              className="gap-1.5"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Retry Comparison</span>
            </Button>
          </div>
        </div>
      )}

      {/* Main Results View */}
      {comparison && (
        <div className="space-y-6">
          {/* PRD Ch. 18.3 Low Alignment Confidence Indicator */}
          {isLowConfidence && (
            <ComparisonConfidenceIndicator
              warning={confidenceWarning}
              className="my-2"
            />
          )}

          {/* Explicit Notice when Translation is Temporarily Unavailable */}
          {comparison.translation_available === false && (
            <div
              role="alert"
              className="p-3.5 rounded-lg bg-blue-50 border border-blue-200 text-xs sm:text-sm text-blue-900 flex items-center gap-2.5 my-2"
              data-testid="translation-unavailable-notice"
            >
              <AlertCircle className="w-4 h-4 text-blue-600 shrink-0" aria-hidden="true" />
              <span>
                {t(
                  'common.translationNotice',
                  'Translation temporarily unavailable. Showing in English.'
                )}
              </span>
            </div>
          )}

          {/* Metrics Summary Overview Bar */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {/* Changed Metric */}
            <Card elevation="sm" className="border-amber-200 bg-amber-50/40">
              <CardContent className="p-4 flex items-center justify-between">
                <div className="space-y-0.5">
                  <span className="text-xs font-semibold uppercase tracking-wider text-amber-800">
                    Changed Clauses
                  </span>
                  <p className="text-2xl font-bold text-amber-950 font-serif">
                    {changedItems.length}
                  </p>
                  <p className="text-[11px] text-amber-700">Wording / risk differences</p>
                </div>
                <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-700 flex items-center justify-center">
                  <ArrowRightLeft className="w-5 h-5" />
                </div>
              </CardContent>
            </Card>

            {/* Matched Metric */}
            <Card elevation="sm" className="border-emerald-200 bg-emerald-50/40">
              <CardContent className="p-4 flex items-center justify-between">
                <div className="space-y-0.5">
                  <span className="text-xs font-semibold uppercase tracking-wider text-emerald-800">
                    Matched Clauses
                  </span>
                  <p className="text-2xl font-bold text-emerald-950 font-serif">
                    {matchedItems.length}
                  </p>
                  <p className="text-[11px] text-emerald-700">Substantially identical terms</p>
                </div>
                <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
              </CardContent>
            </Card>

            {/* Missing Metric */}
            <Card elevation="sm" className="border-rose-200 bg-rose-50/40">
              <CardContent className="p-4 flex items-center justify-between">
                <div className="space-y-0.5">
                  <span className="text-xs font-semibold uppercase tracking-wider text-rose-800">
                    Missing / Added
                  </span>
                  <p className="text-2xl font-bold text-rose-950 font-serif">
                    {missingItems.length}
                  </p>
                  <p className="text-[11px] text-rose-700">Deleted or newly introduced</p>
                </div>
                <div className="w-10 h-10 rounded-xl bg-rose-100 text-rose-700 flex items-center justify-center">
                  <MinusCircle className="w-5 h-5" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* The Three Comparison Groups */}
          <div className="space-y-8 pt-2">
            {/* 1. Changed Group */}
            <ComparisonResultGroup
              category="changed"
              items={changedItems}
              docALabel={docALabel}
              docBLabel={docBLabel}
            />

            {/* 2. Missing & Added Group */}
            <ComparisonResultGroup
              category="missing"
              items={missingItems}
              docALabel={docALabel}
              docBLabel={docBLabel}
            />

            {/* 3. Matched / Unchanged Group */}
            <ComparisonResultGroup
              category="matched"
              items={matchedItems}
              docALabel={docALabel}
              docBLabel={docBLabel}
            />
          </div>
        </div>
      )}
    </div>
  );
};
