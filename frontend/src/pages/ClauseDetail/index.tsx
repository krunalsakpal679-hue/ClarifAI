import React, { useEffect, useState, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  AlertTriangle,
  FileQuestion,
  Sparkles,
  ShieldAlert,
  HelpCircle,
  Scale,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Button } from '../../components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/Card';
import { SkeletonBlock } from '../../components/ui/Skeleton';
import { RiskBadge } from '../../components/domain/RiskBadge';
import { RiskCategoryTag } from '../../components/domain/RiskCategoryTag';
import { ClauseNavControls } from '../../components/domain/ClauseNavControls';
import { useDocumentStore } from '../../store/documentStore';
import { useClauseNavStore } from '../../store/clauseNavStore';
import { useUIStore } from '../../store/uiStore';
import { documentService } from '../../services/api';
import type { ClauseItem } from '../../types';

export const ClauseDetailPage: React.FC = () => {
  const { t } = useTranslation();
  const { id, clauseId } = useParams<{ id: string; clauseId: string }>();
  const navigate = useNavigate();

  const { activeDocument, clauses: storeClauses } = useDocumentStore();
  const { clauseIds, setClauseIds, setCurrentClauseId } = useClauseNavStore();
  const { analysisLanguage, setAnalysisLanguage } = useUIStore();

  const [clause, setClause] = useState<ClauseItem | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [notFound, setNotFound] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Suggested negotiation redlines mapped by category or heuristic
  const getSuggestedRedline = (targetClause: ClauseItem): string | null => {
    if (targetClause.severity === 'Safe') return null;

    if (targetClause.category === 'Liability') {
      return 'Each party shall defend, indemnify, and hold harmless the other party solely against direct third-party damages arising out of gross negligence or willful misconduct, subject always to an aggregate liability cap not to exceed total fees paid under this Agreement in the preceding 12 months.';
    }
    if (targetClause.category === 'Termination') {
      return 'Either party may terminate this Agreement without cause by providing at least thirty (30) days prior written notice. Upon termination, Vendor shall refund pro-rata any prepaid unused fees and provide reasonable data export assistance.';
    }
    if (targetClause.category === 'Renewal') {
      return 'This Agreement shall automatically renew for additional one-year periods unless either party provides written notice of non-renewal at least thirty (30) days prior to the expiration of the then-current term. Fee adjustments upon renewal shall not exceed 3% annually.';
    }
    if (targetClause.category === 'Payment') {
      return 'Customer shall pay all undisputed invoices within thirty (30) days of receipt. Overdue amounts shall accrue simple interest at 0.5% per month or the legal maximum, whichever is lower.';
    }
    if (targetClause.category === 'Intellectual Property') {
      return 'Customer retains all right, title, and interest in and to Customer Data. Vendor shall have a limited, revocable license to process data solely to the extent necessary to deliver the contracted services.';
    }
    return 'The parties agree to negotiate a mutually balanced risk allocation capping liability and providing bilateral termination remedies.';
  };

  const loadClauseData = useCallback(async () => {
    if (!id || !clauseId) {
      setNotFound(true);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    setNotFound(false);

    try {
      // 1. Verify document completion status (PRD Ch. 15 / 16 guard)
      let doc = activeDocument;
      if (!doc || doc.id !== id) {
        doc = await documentService.getById(id);
      }

      if (doc.status !== 'complete') {
        navigate(`/documents/${id}/processing`, { replace: true });
        return;
      }

      // 2. Hydrate clauseNavStore if not already populated for this document
      if (clauseIds.length === 0 || useClauseNavStore.getState().documentId !== id) {
        if (storeClauses.length > 0 && activeDocument?.id === id) {
          setClauseIds(id, storeClauses.map((c) => c.id), clauseId);
        } else {
          // Cold-start deep link: fetch clause list to populate navigation sequence
          const response = await documentService.getClauses(id, analysisLanguage);
          setClauseIds(id, response.results.map((c) => c.id), clauseId);
        }
      } else {
        setCurrentClauseId(clauseId);
      }

      // 3. Fetch single clause detail matching Section 8.3 contract
      const clauseDetail = await documentService.getClauseDetail(id, clauseId, analysisLanguage);
      setClause(clauseDetail);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load clause';
      if (msg.includes('404') || msg.toLowerCase().includes('not found')) {
        setNotFound(true);
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  }, [
    id,
    clauseId,
    activeDocument,
    storeClauses,
    clauseIds.length,
    analysisLanguage,
    setClauseIds,
    setCurrentClauseId,
    navigate,
  ]);

  useEffect(() => {
    loadClauseData();
  }, [loadClauseData]);

  // 404 Not Found State
  if (notFound) {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4 sm:px-6">
        <Card elevation="md" className="border-red-200 bg-white text-center p-8 sm:p-12">
          <div className="w-14 h-14 mx-auto rounded-full bg-red-100 flex items-center justify-center text-red-600 mb-4">
            <FileQuestion className="w-8 h-8" aria-hidden="true" />
          </div>
          <h1 className="text-2xl font-bold font-serif text-secondary-900 mb-2">
            Clause Not Found
          </h1>
          <p className="text-sm text-secondary-600 max-w-md mx-auto mb-6">
            The requested clause ID <code className="font-mono bg-secondary-100 px-1.5 py-0.5 rounded text-secondary-800">{clauseId}</code> could not be found or you may not have permission to view it.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            <Link to={`/documents/${id}`}>
              <Button variant="primary" size="md">
                <ArrowLeft className="w-4 h-4 mr-1.5" />
                Return to Analysis Results
              </Button>
            </Link>
            <Link to="/history">
              <Button variant="outline" size="md">
                Document Archive
              </Button>
            </Link>
          </div>
        </Card>
      </div>
    );
  }

  // Generic Error State
  if (error && !loading) {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4 sm:px-6">
        <Card elevation="md" className="border-red-200 bg-red-50/50 p-8 text-center">
          <AlertTriangle className="w-10 h-10 text-red-600 mx-auto mb-3" />
          <h2 className="text-xl font-bold text-red-950 mb-2">Unable to Load Clause Detail</h2>
          <p className="text-sm text-red-800 mb-6">{error}</p>
          <div className="flex justify-center gap-4">
            <Button variant="outline" onClick={loadClauseData}>
              Try Again
            </Button>
            <Link to={`/documents/${id}`}>
              <Button variant="primary">Return to Analysis</Button>
            </Link>
          </div>
        </Card>
      </div>
    );
  }

  // Loading Skeleton State (Maintains persistent Card titles for synchronous route assertions)
  if (loading && !clause) {
    return (
      <div className="space-y-6 max-w-6xl mx-auto pb-12" data-testid="clause-detail-skeleton">
        {/* Breadcrumb Skeleton */}
        <div className="flex items-center gap-2 text-xs text-secondary-400">
          <SkeletonBlock className="h-4 w-20" />
          <span>/</span>
          <SkeletonBlock className="h-4 w-32" />
          <span>/</span>
          <SkeletonBlock className="h-4 w-24" />
        </div>

        {/* Header Skeleton */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-secondary-200">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <SkeletonBlock className="h-6 w-28 rounded-full" />
              <SkeletonBlock className="h-6 w-36 rounded-full" />
            </div>
            <SkeletonBlock className="h-8 w-64" />
          </div>
          <SkeletonBlock className="h-9 w-44" />
        </div>

        {/* Top Nav Skeleton */}
        <SkeletonBlock className="h-12 w-full rounded-lg" />

        {/* Main Content Skeleton Cards with persistent titles */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card elevation="sm" className="border-secondary-200">
            <CardHeader>
              <CardTitle className="text-base font-semibold text-secondary-900">
                Original Contract Text
              </CardTitle>
              <CardDescription>
                Exact verbatim extract parsed from source document.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <SkeletonBlock className="h-48 w-full rounded-lg" />
            </CardContent>
          </Card>

          <Card elevation="sm" className="border-secondary-200">
            <CardHeader>
              <CardTitle className="text-base font-semibold text-primary-950">
                Plain-English Breakdown &amp; Risk Driver
              </CardTitle>
              <CardDescription>
                Simplified representation for non-lawyers and business decision-makers.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <SkeletonBlock className="h-28 w-full rounded-lg" />
              <SkeletonBlock className="h-24 w-full rounded-lg" />
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (!clause) return null;

  const isClassificationFailed = clause.status === 'failed' || clause.severity === null;
  const suggestedRedline = getSuggestedRedline(clause);

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12" data-testid="clause-detail-view">
      {/* Breadcrumb Navigation */}
      <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-xs text-secondary-500">
        <Link to="/dashboard" className="hover:text-primary-700 hover:underline">
          Dashboard
        </Link>
        <span className="text-secondary-400">/</span>
        <Link to={`/documents/${id}`} className="hover:text-primary-700 hover:underline">
          Document Analysis
        </Link>
        <span className="text-secondary-400">/</span>
        <span className="text-secondary-900 font-semibold" aria-current="page">
          Clause #{clause.position}
        </span>
      </nav>

      {/* Page Header */}
      <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-secondary-200">
        <div className="space-y-1.5">
          <div className="flex flex-wrap items-center gap-2">
            {isClassificationFailed ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-900 border border-amber-300">
                <HelpCircle className="w-3.5 h-3.5 text-amber-700" aria-hidden="true" />
                <span>Classification Incomplete</span>
              </span>
            ) : (
              clause.severity && <RiskBadge severity={clause.severity} size="md" />
            )}

            {clause.category && (
              <RiskCategoryTag category={clause.category} size="md" />
            )}

            <span className="text-xs font-mono font-bold px-2.5 py-1 rounded bg-secondary-100 text-secondary-800">
              ID: {clause.id}
            </span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-serif font-bold text-primary-950">
            Clause #{clause.position} Inspection View
          </h1>
          <p className="text-xs sm:text-sm text-secondary-600">
            Comprehensive legal analysis, risk breakdown, and recommended counter-terms.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2 self-start sm:self-auto shrink-0">
          {/* Analysis Language Switcher */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAnalysisLanguage(analysisLanguage === 'en' ? 'hi' : 'en')}
            className="text-xs font-medium border-secondary-300"
          >
            {analysisLanguage === 'en' ? 'Translate to हिंदी' : 'Translate to English'}
          </Button>

          <Link to={`/documents/${id}`}>
            <Button variant="secondary" size="sm" className="gap-1.5 text-xs font-medium">
              <ArrowLeft className="w-4 h-4" aria-hidden="true" />
              <span>{t('clauseDetail.backToAnalysis', 'Back to Analysis')}</span>
            </Button>
          </Link>
        </div>
      </header>

      {/* Top Clause Navigation Controls */}
      <ClauseNavControls documentId={id!} variant="compact" />

      {/* Main Analysis Cards Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-stretch">
        {/* 1. Original Contract Text */}
        <Card elevation="sm" className="border-secondary-300 flex flex-col h-full">
          <CardHeader className="bg-secondary-50/70 border-b border-secondary-200/80">
            <CardTitle className="text-base font-semibold text-secondary-900 flex items-center justify-between">
              <span>{t('clauseDetail.originalContractText', 'Original Contract Text')}</span>
              <span className="text-xs font-normal text-secondary-500 font-sans">
                Verbatim Source
              </span>
            </CardTitle>
            <CardDescription className="text-xs">
              Exact verbatim extract parsed from source document.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-5 sm:p-6 flex-1 flex flex-col justify-between">
            <div className="p-4 sm:p-5 bg-white rounded-lg border border-secondary-200 font-serif text-sm sm:text-base leading-relaxed text-secondary-900 select-text whitespace-pre-wrap shadow-inner">
              &ldquo;{clause.original_text}&rdquo;
            </div>

            <div className="mt-4 pt-3 border-t border-secondary-100 flex items-center justify-between text-xs text-secondary-500 font-sans">
              <span>Position: Index #{clause.position}</span>
              <span>Extracted: {new Date(clause.created_at).toLocaleDateString()}</span>
            </div>
          </CardContent>
        </Card>

        {/* 2. Plain-English Breakdown & Risk Driver */}
        <Card elevation="sm" className="border-secondary-300 flex flex-col h-full">
          <CardHeader className="bg-primary-50/50 border-b border-primary-100">
            <CardTitle className="text-base font-semibold text-primary-950 flex items-center justify-between">
              <span>{t('clauseDetail.plainEnglishBreakdown', 'Plain-English Breakdown & Risk Driver')}</span>
              <Sparkles className="w-4 h-4 text-primary-600" aria-hidden="true" />
            </CardTitle>
            <CardDescription className="text-xs">
              Simplified representation for non-lawyers and business decision-makers.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-5 sm:p-6 space-y-4 flex-1">
            {/* What This Means */}
            <div className="p-4 bg-primary-50/40 rounded-lg border border-primary-200/70">
              <p className="font-semibold text-xs text-primary-900 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                <span>{analysisLanguage === 'hi' ? 'इसका क्या अर्थ है' : 'What This Means'}</span>
                {analysisLanguage === 'hi' && (
                  <span className="text-[10px] font-medium normal-case px-2 py-0.5 rounded bg-primary-100 text-primary-800">
                    हिंदी
                  </span>
                )}
              </p>
              <p className="text-sm leading-relaxed text-primary-950 font-sans">
                {analysisLanguage === 'hi'
                  ? (clause.simplified_text_hi || clause.simplified_text)
                  : clause.simplified_text}
              </p>
            </div>

            {/* Risk Severity Rationale */}
            <div className="p-4 bg-secondary-50 rounded-lg border border-secondary-200">
              <p className="font-semibold text-xs text-secondary-800 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                <ShieldAlert className="w-3.5 h-3.5 text-secondary-600" aria-hidden="true" />
                <span>{analysisLanguage === 'hi' ? 'जोखिम गंभीरता का कारण' : 'Risk Severity Rationale'}</span>
              </p>
              <p className="text-xs sm:text-sm leading-relaxed text-secondary-700">
                {analysisLanguage === 'hi'
                  ? (clause.why_flagged_hi || clause.explanation)
                  : clause.explanation}
              </p>
            </div>

            {/* Translation fallback notice if Hindi requested and translation unavailable */}
            {analysisLanguage === 'hi' && !clause.translation_available && (
              <p className="text-xs text-amber-700 italic bg-amber-50 p-2.5 rounded border border-amber-200">
                नोट: इस खंड का हिंदी अनुवाद वर्तमान में तैयार हो रहा है। मूल अंग्रेजी सरलीकरण प्रदर्शित है।
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 3. Heuristic Rule Findings (if detected) */}
      {clause.rule_findings && clause.rule_findings.length > 0 && (
        <Card elevation="sm" className="border-amber-200 bg-amber-50/30">
          <CardHeader className="pb-2">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-600" aria-hidden="true" />
              <CardTitle className="text-sm font-semibold text-amber-950">
                Heuristic Rule Violations &amp; Triggers
              </CardTitle>
            </div>
            <CardDescription className="text-xs">
              Algorithmic rule matching flagged the following contractual risk indicators:
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-2">
            <div className="space-y-2.5">
              {clause.rule_findings.map((rule, idx) => (
                <div
                  key={idx}
                  className="p-3 bg-white rounded-md border border-amber-200/80 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold px-1.5 py-0.5 rounded bg-amber-100 text-amber-900">
                        {rule.rule_id}
                      </span>
                      <span className="font-medium text-secondary-800">
                        {rule.rule_name || 'Pattern Trigger'}
                      </span>
                    </div>
                    {rule.description && (
                      <p className="text-secondary-600">{rule.description}</p>
                    )}
                  </div>
                  {rule.matched_text && (
                    <div className="text-xs font-mono text-secondary-500 bg-secondary-50 px-2 py-1 rounded border border-secondary-200 sm:max-w-xs truncate">
                      Matched: &ldquo;{rule.matched_text}&rdquo;
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 4. Suggested Negotiation Redline / Counter-Language */}
      {suggestedRedline && (
        <Card elevation="sm" className="border-accent-300 bg-gradient-to-r from-accent-50/40 via-white to-accent-50/20">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <Scale className="w-4 h-4 text-accent-700" aria-hidden="true" />
              <CardTitle className="text-base font-semibold text-accent-950">
                Recommended Negotiation Counter-Language
              </CardTitle>
            </div>
            <CardDescription className="text-xs">
              Actionable legal redline designed to mitigate exposure and achieve standard commercial balance.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="p-4 bg-white rounded-lg border border-accent-200/80 text-xs sm:text-sm font-mono text-secondary-800 leading-relaxed shadow-sm">
              &ldquo;{suggestedRedline}&rdquo;
            </div>
          </CardContent>
        </Card>
      )}

      {/* Bottom Navigation Controls & Actions */}
      <footer className="pt-4 space-y-4">
        <ClauseNavControls documentId={id!} variant="expanded" />

        <div className="flex justify-between items-center pt-2">
          <Link to={`/documents/${id}`}>
            <Button variant="outline" size="sm" className="gap-1.5 text-xs text-secondary-700">
              <ArrowLeft className="w-3.5 h-3.5" aria-hidden="true" />
              <span>Back to Overview</span>
            </Button>
          </Link>
          <span className="text-xs text-secondary-400">
            ClarifAI Clause Intelligence Engine
          </span>
        </div>
      </footer>
    </div>
  );
};
