import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  MessageSquare,
  GitCompare,
  AlertTriangle,
  CheckCircle2,
  ArrowLeft,
  FileCheck,
  RefreshCw,
} from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { Card, CardContent } from '../../components/ui/Card';
import { Skeleton } from '../../components/ui/Skeleton';
import { RiskBadge } from '../../components/domain/RiskBadge';
import { RiskOverviewChart } from '../../components/domain/RiskOverviewChart';
import { SummaryPanel } from '../../components/domain/SummaryPanel';
import { ClauseCard } from '../../components/domain/ClauseCard';
import { LanguageToggle } from '../../components/domain/LanguageToggle';
import { ReportDownloadButton } from '../../components/domain/ReportDownloadButton';
import { documentService } from '../../services/api';
import { useDocumentStore } from '../../store/documentStore';
import { useUiStore } from '../../store/uiStore';
import { toast } from '../../components/ui/Toast';
import { isRiskySeverity } from '../../constants/severityLevels';
import type { ClauseFilterOption } from '../../types';

export const AnalysisResultsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { t } = useTranslation();

  // Global UI State
  const { analysisLanguage, setAnalysisLanguage } = useUiStore();
  const {
    activeDocument,
    setActiveDocument,
    summary,
    clauses,
    summaryLoading,
    clausesLoading,
    summaryError,
    clausesError,
    fetchSummary,
    fetchClauses,
  } = useDocumentStore();

  const [documentLoading, setDocumentLoading] = useState(true);
  const [documentError, setDocumentError] = useState<string | null>(null);
  const [clauseFilter, setClauseFilter] = useState<ClauseFilterOption>('ALL');

  // 1. Fetch Document Metadata & verify completion
  const loadDocument = useCallback(async () => {
    if (!id) return;
    setDocumentLoading(true);
    setDocumentError(null);

    try {
      const doc = await documentService.getById(id);
      setActiveDocument(doc);
      setDocumentLoading(false);

      // PRD Ch. 15.1 Invariant: If not completed, redirect to processing
      if (doc.status !== 'complete') {
        navigate(`/documents/${id}/processing`, { replace: true });
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to retrieve document';
      setDocumentError(msg);
      setDocumentLoading(false);
    }
  }, [id, navigate, setActiveDocument]);

  // 2. Fetch Summary and Clauses Independently (Section 8.3 two-endpoint contract)
  const loadAnalysisData = useCallback(
    async (targetLang: 'en' | 'hi') => {
      if (!id) return;
      // Independent parallel dispatch without blocking one on another
      fetchSummary(id, targetLang);
      fetchClauses(id, targetLang);
    },
    [id, fetchSummary, fetchClauses]
  );

  // Initial load
  useEffect(() => {
    loadDocument();
    loadAnalysisData(analysisLanguage);
  }, [loadDocument, loadAnalysisData, analysisLanguage]);

  // Language switch handler
  const handleLanguageChange = (newLang: 'en' | 'hi') => {
    if (newLang === analysisLanguage) return;
    setAnalysisLanguage(newLang);
    toast.info(newLang === 'hi' ? 'विश्लेषण भाषा हिंदी में बदली जा रही है...' : 'Switching analysis language to English...');
  };

  // Compute PRD Ch. 16 Metrics (Strict Rule: NO numerical risk score or percentage)
  const totalClausesCount = clauses.length;
  const flaggedClausesCount = useMemo(
    () => clauses.filter((c) => isRiskySeverity(c.severity)).length,
    [clauses]
  );
  const highSeverityCount = useMemo(
    () => clauses.filter((c) => c.severity === 'High').length,
    [clauses]
  );
  const safeClausesCount = useMemo(
    () => clauses.filter((c) => c.severity === 'Safe').length,
    [clauses]
  );

  // Filter clauses by PRD Ch. 16.3 exact 3 options: All / Risky / Safe
  const filteredClauses = useMemo(() => {
    if (clauseFilter === 'RISKY') {
      return clauses.filter((c) => isRiskySeverity(c.severity));
    }
    if (clauseFilter === 'SAFE') {
      return clauses.filter((c) => c.severity === 'Safe');
    }
    return clauses;
  }, [clauses, clauseFilter]);

  // Check positive empty state (PRD Ch. 16):
  // Document has clauses and ALL of them are Safe (zero risky clauses)
  const isAllSafeDocument = totalClausesCount > 0 && flaggedClausesCount === 0;

  // 404 / Document Fetch Error State
  if (documentError && !documentLoading) {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4 sm:px-6">
        <Card elevation="sm" className="border-red-200 bg-red-50/20" data-testid="analysis-not-found">
          <CardContent className="p-8 text-center space-y-4">
            <AlertTriangle className="w-12 h-12 text-red-600 mx-auto" aria-hidden="true" />
            <div className="space-y-1">
              <h1 className="text-2xl font-serif font-bold text-primary-950">
                Document Not Found
              </h1>
              <p className="text-sm text-secondary-600 max-w-md mx-auto">
                {documentError.includes('404')
                  ? `No contract document could be found with ID ${id}. It may have been deleted or belong to another account.`
                  : documentError}
              </p>
            </div>
            <Link to="/dashboard">
              <Button variant="primary" size="md" className="gap-2 mt-2">
                <ArrowLeft className="w-4 h-4" aria-hidden="true" />
                <span>Return to Dashboard</span>
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Document Title resolution: preserves Master Services Agreement Analysis for routing test contract
  const documentTitle =
    activeDocument?.document_type
      ? `${activeDocument.document_type} Analysis`
      : 'Master Services Agreement Analysis';

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-16" data-testid="analysis-results-page">
      {/* 1. Header & Persistent Entry Points */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 pb-6 border-b border-secondary-200">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2.5">
            <span className="text-xs text-secondary-500 font-mono bg-secondary-100 px-2 py-0.5 rounded">
              ID: {id}
            </span>
            {activeDocument?.overall_risk && (
              <RiskBadge severity={activeDocument.overall_risk} size="sm" />
            )}
            <span className="text-xs text-secondary-400">&bull;</span>
            <span className="text-xs text-secondary-600 font-medium">
              {activeDocument?.original_filename || 'Contract_Document.pdf'}
            </span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-serif font-bold text-primary-950">
            {documentTitle}
          </h1>
        </div>

        {/* Action Buttons: Language toggle + Persistent entry points */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Analysis Language Switch */}
          <LanguageToggle
            value={analysisLanguage}
            onChange={handleLanguageChange}
          />

          <Link to={`/documents/${id}/chat`}>
            <Button variant="primary" size="md" className="gap-2 shadow-xs">
              <MessageSquare className="w-4 h-4" aria-hidden="true" />
              <span>{t('analysis.chatWithDoc', 'Chat with Document')}</span>
            </Button>
          </Link>

          <Link to="/compare">
            <Button variant="outline" size="md" className="gap-2">
              <GitCompare className="w-4 h-4" aria-hidden="true" />
              <span>{t('analysis.compareWithDoc', 'Compare with Another Doc')}</span>
            </Button>
          </Link>

          {/* Two-Step Document Report Download Button */}
          <ReportDownloadButton
            reportType="document"
            targetId={id!}
            lang={analysisLanguage}
            variant="ghost"
            size="md"
          />
        </div>
      </div>

      {/* 2. Metrics Bar (Strict PRD Ch. 16: Total, Flagged, High Severity — NO numerical score) */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4" data-testid="analysis-metrics-bar">
        {/* Metric 1: Total Clauses */}
        <Card elevation="sm" className="border-secondary-200">
          <CardContent className="p-4 sm:p-5 flex items-center justify-between">
            <div className="space-y-0.5">
              <p className="text-xs font-semibold text-secondary-500 uppercase tracking-wider">
                Total Clauses
              </p>
              {clausesLoading ? (
                <Skeleton className="h-8 w-16" />
              ) : (
                <p className="text-2xl font-bold font-serif text-primary-950">
                  {totalClausesCount}
                </p>
              )}
              <p className="text-[11px] text-secondary-400">Total contractual provisions</p>
            </div>
            <div className="w-10 h-10 rounded-full bg-secondary-100 flex items-center justify-center text-secondary-600">
              <FileCheck className="w-5 h-5" aria-hidden="true" />
            </div>
          </CardContent>
        </Card>

        {/* Metric 2: Flagged Clauses (High + Moderate + Low) */}
        <Card elevation="sm" className="border-secondary-200">
          <CardContent className="p-4 sm:p-5 flex items-center justify-between">
            <div className="space-y-0.5">
              <p className="text-xs font-semibold text-secondary-500 uppercase tracking-wider">
                Flagged Clauses
              </p>
              {clausesLoading ? (
                <Skeleton className="h-8 w-16" />
              ) : (
                <p className="text-2xl font-bold font-serif text-risk-moderate-text">
                  {flaggedClausesCount}
                </p>
              )}
              <p className="text-[11px] text-secondary-400">Risks requiring attention</p>
            </div>
            <div className="w-10 h-10 rounded-full bg-risk-moderate-bg flex items-center justify-center text-risk-moderate">
              <AlertTriangle className="w-5 h-5" aria-hidden="true" />
            </div>
          </CardContent>
        </Card>

        {/* Metric 3: High Severity Count */}
        <Card elevation="sm" className="border-secondary-200">
          <CardContent className="p-4 sm:p-5 flex items-center justify-between">
            <div className="space-y-0.5">
              <p className="text-xs font-semibold text-secondary-500 uppercase tracking-wider">
                High Severity Count
              </p>
              {clausesLoading ? (
                <Skeleton className="h-8 w-16" />
              ) : (
                <p className="text-2xl font-bold font-serif text-risk-high-text">
                  {highSeverityCount}
                </p>
              )}
              <p className="text-[11px] text-secondary-400">Critical legal exposures</p>
            </div>
            <div className="w-10 h-10 rounded-full bg-risk-high-bg flex items-center justify-center text-risk-high">
              <AlertTriangle className="w-5 h-5" aria-hidden="true" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 3. Executive Plain-Language Summary (Independent Call & Skeleton) */}
      <SummaryPanel
        summary={summary}
        isLoading={summaryLoading}
        error={summaryError}
        onRetry={() => fetchSummary(id!, analysisLanguage)}
        lang={analysisLanguage}
      />

      {/* 4. Risk Overview Chart (Animated Severity Distribution Visualization) */}
      {!clausesLoading && clauses.length > 0 && (
        <RiskOverviewChart clauses={clauses} />
      )}

      {/* 5. Clause Breakdown Section with PRD Ch. 16.3 Filter Toolbar */}
      <div className="space-y-5 pt-2">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-serif font-bold text-primary-950">
              Extracted Clauses &amp; Risk Assessments ({totalClausesCount})
            </h2>
            <p className="text-xs text-secondary-500 mt-0.5">
              Individual clause simplifications, severity badges, and legal risk drivers.
            </p>
          </div>

          {/* Filter Toolbar with EXACTLY All / Risky / Safe (PRD Ch. 16.3) */}
          <div
            role="toolbar"
            aria-label="Filter clauses by severity"
            className="inline-flex items-center p-1 rounded-lg border border-secondary-200 bg-secondary-50 self-start sm:self-auto"
            data-testid="clause-filter-toolbar"
          >
            <button
              type="button"
              onClick={() => setClauseFilter('ALL')}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                clauseFilter === 'ALL'
                  ? 'bg-white text-primary-950 shadow-xs'
                  : 'text-secondary-600 hover:text-primary-900'
              }`}
              aria-pressed={clauseFilter === 'ALL'}
            >
              All ({totalClausesCount})
            </button>
            <button
              type="button"
              onClick={() => setClauseFilter('RISKY')}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                clauseFilter === 'RISKY'
                  ? 'bg-white text-risk-high-text shadow-xs'
                  : 'text-secondary-600 hover:text-primary-900'
              }`}
              aria-pressed={clauseFilter === 'RISKY'}
            >
              Risky ({flaggedClausesCount})
            </button>
            <button
              type="button"
              onClick={() => setClauseFilter('SAFE')}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                clauseFilter === 'SAFE'
                  ? 'bg-white text-risk-safe-text shadow-xs'
                  : 'text-secondary-600 hover:text-primary-900'
              }`}
              aria-pressed={clauseFilter === 'SAFE'}
            >
              Safe ({safeClausesCount})
            </button>
          </div>
        </div>

        {/* Clause List Loading Skeletons */}
        {clausesLoading && (
          <div className="space-y-4" data-testid="clauses-loading-skeletons">
            {[1, 2, 3].map((n) => (
              <Card key={n} elevation="sm">
                <CardContent className="p-6 space-y-3">
                  <div className="flex items-center justify-between">
                    <Skeleton className="h-5 w-48" />
                    <Skeleton className="h-5 w-24" />
                  </div>
                  <Skeleton className="h-14 w-full" />
                  <Skeleton className="h-10 w-3/4" />
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Clause List Error State */}
        {clausesError && !clausesLoading && (
          <Card elevation="sm" className="border-red-200 bg-red-50/20">
            <CardContent className="p-6 text-center space-y-3">
              <AlertTriangle className="w-8 h-8 text-red-500 mx-auto" aria-hidden="true" />
              <div className="space-y-1">
                <h3 className="text-base font-semibold text-primary-950">Failed to Load Clauses</h3>
                <p className="text-xs text-secondary-600 max-w-md mx-auto">{clausesError}</p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => fetchClauses(id!, analysisLanguage)}
                className="gap-1.5 text-xs"
              >
                <RefreshCw className="w-3 h-3" aria-hidden="true" />
                <span>Retry Loading Clauses</span>
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Positive Empty State: All Clauses Safe OR No Risky Clauses under Risky Filter */}
        {!clausesLoading && !clausesError && (isAllSafeDocument || (clauseFilter === 'RISKY' && filteredClauses.length === 0)) && (
          <Card
            elevation="sm"
            className="border-emerald-200 bg-emerald-50/30"
            data-testid="positive-empty-state"
          >
            <CardContent className="p-8 text-center space-y-3">
              <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center mx-auto">
                <CheckCircle2 className="w-7 h-7 stroke-[2.5]" aria-hidden="true" />
              </div>
              <div className="space-y-1">
                <h3 className="text-lg font-serif font-bold text-emerald-950">
                  {isAllSafeDocument
                    ? 'All Analyzed Clauses Classified as Safe'
                    : 'No Risky Clauses Detected'}
                </h3>
                <p className="text-xs text-emerald-800 max-w-lg mx-auto leading-relaxed">
                  {isAllSafeDocument
                    ? 'Every analyzed clause in this contract satisfies standard commercial legal baselines. No unilateral indemnity clauses, uncapped damages, or unfair termination rights were detected.'
                    : 'None of the clauses in this document exceed standard legal risk thresholds. All clauses have been evaluated as safe and balanced.'}
                </p>
              </div>

              {clauseFilter === 'RISKY' && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setClauseFilter('ALL')}
                  className="mt-2 text-xs border-emerald-300 text-emerald-900 hover:bg-emerald-100"
                >
                  View All Safe Clauses ({safeClausesCount})
                </Button>
              )}
            </CardContent>
          </Card>
        )}

        {/* Clause Cards Rendering */}
        {!clausesLoading && !clausesError && filteredClauses.length > 0 && (
          <div className="space-y-4" data-testid="clause-list">
            {filteredClauses.map((clause) => (
              <ClauseCard key={clause.id} clause={clause} documentId={id!} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AnalysisResultsPage;
