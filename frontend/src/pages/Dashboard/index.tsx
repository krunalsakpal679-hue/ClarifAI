import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  FileText,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Plus,
  RefreshCw,
  GitCompare,
  ArrowRight,
  FolderOpen,
} from 'lucide-react';
import { useAuthStore } from '../../store/authStore';
import { useDocumentStore } from '../../store/documentStore';
import { dashboardService } from '../../services/api';
import type { DashboardSummaryResponse } from '../../types';
import { Button } from '../../components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/Card';
import { SkeletonBlock } from '../../components/ui/SkeletonBlock';
import { DocumentHistoryCard } from '../../components/domain/DocumentHistoryCard';

export const DashboardPage: React.FC = () => {
  const { t } = useTranslation();
  const user = useAuthStore((state) => state.user);
  const { documents, isLoading: isDocsLoading, error: docsError, fetchDocuments } = useDocumentStore();

  const [summary, setSummary] = useState<DashboardSummaryResponse | null>(null);
  const [isSummaryLoading, setIsSummaryLoading] = useState(true);
  const [summaryError, setSummaryError] = useState<string | null>(null);

  const loadDashboardData = useCallback(async () => {
    setIsSummaryLoading(true);
    setSummaryError(null);

    // Fetch summary and documents in parallel
    const summaryPromise = dashboardService
      .getSummary()
      .then((data) => {
        setSummary(data);
        setIsSummaryLoading(false);
      })
      .catch((err) => {
        setSummaryError(err instanceof Error ? err.message : 'Failed to load summary');
        setIsSummaryLoading(false);
      });

    const docsPromise = fetchDocuments({ page: 1, page_size: 6 });

    await Promise.allSettled([summaryPromise, docsPromise]);
  }, [fetchDocuments]);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  const isLoading = isDocsLoading || isSummaryLoading;
  const hasError = Boolean(docsError || summaryError);
  const recentDocs = documents.slice(0, 6);

  return (
    <div className="space-y-8" data-testid="dashboard-page">
      {/* Welcome & Quick Action Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-secondary-200">
        <div>
          <h1 className="text-2xl sm:text-3xl font-serif font-bold text-primary-950">
            {t('dashboard.welcome', 'Welcome back')}, {user?.fullName || 'Counsel'}
          </h1>
          <p className="text-secondary-600 text-sm mt-1">
            {t(
              'dashboard.subtitle',
              'Review document simplification summaries, inspect clause risk flags, and compare contract versions.'
            )}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link to="/upload">
            <Button variant="primary" size="md" className="gap-2 shadow-sm">
              <Plus className="w-4 h-4" aria-hidden="true" />
              <span>{t('common.actions.upload', 'Upload Document')}</span>
            </Button>
          </Link>
          <Link to="/compare">
            <Button variant="outline" size="md" className="gap-2 text-primary-900 border-secondary-300">
              <GitCompare className="w-4 h-4" aria-hidden="true" />
              <span>{t('common.actions.compare', 'Compare Documents')}</span>
            </Button>
          </Link>
        </div>
      </div>

      {/* Error State with Retry Banner */}
      {hasError && (
        <div
          role="alert"
          aria-live="polite"
          className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
        >
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-red-600 shrink-0" aria-hidden="true" />
            <div>
              <p className="text-sm font-semibold">{t('dashboard.unableToLoad', 'Unable to load dashboard data')}</p>
              <p className="text-xs text-red-700">{docsError || summaryError}</p>
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={loadDashboardData}
            className="border-red-300 text-red-800 hover:bg-red-100 gap-1.5 self-start sm:self-auto"
          >
            <RefreshCw className="w-3.5 h-3.5" aria-hidden="true" />
            <span>{t('common.retry', 'Retry')}</span>
          </Button>
        </div>
      )}

      {/* Aggregate Stat Cards (Section 8.7) */}
      <section aria-label="Dashboard Aggregate Statistics">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Card 1: Total Documents */}
          <Card elevation="sm" className="border-secondary-200 card-3d-tilt">
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardDescription className="text-xs uppercase font-semibold text-secondary-600">
                {t('dashboard.stats.totalDocuments', 'Total Documents')}
              </CardDescription>
              <div className="p-2 rounded-lg bg-primary-50 text-primary-800">
                <FileText className="w-4 h-4" aria-hidden="true" />
              </div>
            </CardHeader>
            <CardContent>
              {isSummaryLoading ? (
                <SkeletonBlock height="2rem" width="4rem" />
              ) : (
                <div className="text-3xl font-serif font-bold text-primary-950">
                  {summary?.total_documents ?? 0}
                </div>
              )}
              <p className="text-xs text-secondary-500 mt-1">
                {t('dashboard.stats.totalDocumentsDesc', 'Uploaded for legal analysis')}
              </p>
            </CardContent>
          </Card>

          {/* Card 2: Flagged Risk */}
          <Card elevation="sm" className="border-secondary-200 card-3d-tilt">
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardDescription className="text-xs uppercase font-semibold text-amber-800">
                {t('dashboard.stats.flaggedRisk', 'Risk Flagged')}
              </CardDescription>
              <div className="p-2 rounded-lg bg-amber-50 text-amber-700">
                <AlertTriangle className="w-4 h-4" aria-hidden="true" />
              </div>
            </CardHeader>
            <CardContent>
              {isSummaryLoading ? (
                <SkeletonBlock height="2rem" width="4rem" />
              ) : (
                <div className="text-3xl font-serif font-bold text-amber-700">
                  {summary?.flagged_risk_count ?? 0}
                </div>
              )}
              <p className="text-xs text-amber-700/80 mt-1 font-medium">
                {t('dashboard.stats.flaggedRiskDesc', 'Non-standard clause severity')}
              </p>
            </CardContent>
          </Card>

          {/* Card 3: In Progress Pipeline */}
          <Card elevation="sm" className="border-secondary-200 card-3d-tilt">
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardDescription className="text-xs uppercase font-semibold text-sky-800">
                {t('dashboard.stats.inProgress', 'In Progress')}
              </CardDescription>
              <div className="p-2 rounded-lg bg-sky-50 text-sky-700">
                <Clock className="w-4 h-4" aria-hidden="true" />
              </div>
            </CardHeader>
            <CardContent>
              {isSummaryLoading ? (
                <SkeletonBlock height="2rem" width="4rem" />
              ) : (
                <div className="text-3xl font-serif font-bold text-sky-700">
                  {summary?.in_progress_count ?? 0}
                </div>
              )}
              <p className="text-xs text-sky-700/80 mt-1 font-medium">
                {t('dashboard.stats.inProgressDesc', 'Under active AI simplification')}
              </p>
            </CardContent>
          </Card>

          {/* Card 4: Completed Documents */}
          <Card elevation="sm" className="border-secondary-200 card-3d-tilt">
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardDescription className="text-xs uppercase font-semibold text-emerald-800">
                {t('dashboard.stats.completed', 'Completed')}
              </CardDescription>
              <div className="p-2 rounded-lg bg-emerald-50 text-emerald-700">
                <CheckCircle2 className="w-4 h-4" aria-hidden="true" />
              </div>
            </CardHeader>
            <CardContent>
              {isSummaryLoading ? (
                <SkeletonBlock height="2rem" width="4rem" />
              ) : (
                <div className="text-3xl font-serif font-bold text-emerald-700">
                  {summary?.completed_count ?? 0}
                </div>
              )}
              <p className="text-xs text-emerald-700/80 mt-1 font-medium">
                {t('dashboard.stats.completedDesc', 'Ready for review & chat')}
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Recent Documents Section (PRD Ch. 20, 22.4) */}
      <section aria-label="Recent Documents Section" className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-serif font-bold text-primary-950">
              {t('dashboard.recentDocuments', 'Recent Documents')}
            </h2>
            <p className="text-xs text-secondary-500">
              {t('dashboard.recentDocumentsSubtitle', 'Latest legal agreements uploaded and processed by ClarifAI.')}
            </p>
          </div>

          <Link
            to="/history"
            className="inline-flex items-center gap-1 text-sm font-semibold text-primary-800 hover:text-primary-950 hover:underline"
          >
            <span>{t('dashboard.viewAllHistory', 'View all history')}</span>
            <ArrowRight className="w-4 h-4" aria-hidden="true" />
          </Link>
        </div>

        {/* Loading Skeletons */}
        {isLoading && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4" data-testid="dashboard-loading-skeletons">
            {[1, 2, 3, 4].map((i) => (
              <Card key={i} elevation="sm" className="p-5 space-y-4 border-secondary-200">
                <div className="flex items-start justify-between">
                  <div className="space-y-2 flex-1 mr-4">
                    <SkeletonBlock height="1.25rem" width="70%" />
                    <SkeletonBlock height="0.85rem" width="40%" />
                  </div>
                  <SkeletonBlock height="1.5rem" width="5rem" rounded="full" />
                </div>
                <SkeletonBlock height="2rem" width="100%" />
                <div className="flex items-center justify-between pt-3 border-t border-secondary-100">
                  <SkeletonBlock height="1.75rem" width="45%" />
                  <SkeletonBlock height="1.75rem" width="25%" />
                </div>
              </Card>
            ))}
          </div>
        )}

        {/* Empty State for New Users */}
        {!isLoading && recentDocs.length === 0 && (
          <Card elevation="sm" className="border-dashed border-2 border-secondary-300 bg-secondary-50/50 p-8 sm:p-12 text-center">
            <CardContent className="flex flex-col items-center justify-center space-y-4 max-w-md mx-auto">
              <div className="w-16 h-16 rounded-full bg-primary-100 text-primary-800 flex items-center justify-center shadow-sm">
                <FolderOpen className="w-8 h-8" aria-hidden="true" />
              </div>
              <div className="space-y-1">
                <CardTitle className="text-lg sm:text-xl font-serif text-primary-950">
                  {t('dashboard.emptyTitle', 'No documents analyzed yet')}
                </CardTitle>
                <CardDescription className="text-sm text-secondary-600">
                  {t(
                    'dashboard.emptySubtitle',
                    'Upload your first contract, NDA, or service agreement to generate plain-English summaries, pinpointed risk scores, and clause redlines.'
                  )}
                </CardDescription>
              </div>

              <Link to="/upload" className="pt-2">
                <Button variant="primary" size="md" className="gap-2 shadow-sm">
                  <Plus className="w-4 h-4" aria-hidden="true" />
                  <span>{t('dashboard.uploadFirst', 'Upload your first document')}</span>
                </Button>
              </Link>
            </CardContent>
          </Card>
        )}

        {/* Populated Recent Documents Grid */}
        {!isLoading && recentDocs.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4" data-testid="recent-documents-grid">
            {recentDocs.map((doc) => (
              <DocumentHistoryCard key={doc.id} document={doc} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
};

export default DashboardPage;
