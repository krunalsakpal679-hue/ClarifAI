import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Button } from '../../components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { AlertCircle, AlertTriangle, ArrowRight, FileText, Upload, RefreshCw } from 'lucide-react';
import { useComparisonStore } from '../../store/comparisonStore';
import { documentService } from '../../services/api';
import type { DocumentItem } from '../../types/documents';

export const ComparisonSetupPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { createComparison, isCreating, error: storeError, reset } = useComparisonStore();

  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [isLoadingDocs, setIsLoadingDocs] = useState<boolean>(true);
  const [fetchError, setFetchError] = useState<string | null>(null);

  const [docA, setDocA] = useState<string>('');
  const [docB, setDocB] = useState<string>('');

  // Fetch user documents on mount
  useEffect(() => {
    reset();
    let mounted = true;

    const loadDocuments = async () => {
      setIsLoadingDocs(true);
      setFetchError(null);
      try {
        const res = await documentService.list({ page_size: 50 });
        if (mounted) {
          setDocuments(res.results);

          // Auto-select first two complete documents if available without overwriting existing selection
          const completeDocs = res.results.filter((d) => d.status === 'complete');
          setDocA((prev) => prev || (completeDocs[0] ? completeDocs[0].id : ''));
          setDocB((prev) => prev || (completeDocs[1] ? completeDocs[1].id : ''));
        }
      } catch (err) {
        if (mounted) {
          const msg = err instanceof Error ? err.message : 'Failed to load documents.';
          setFetchError(msg);
        }
      } finally {
        if (mounted) {
          setIsLoadingDocs(false);
        }
      }
    };

    loadDocuments();

    return () => {
      mounted = false;
    };
  }, [reset]);

  const selectedDocA = documents.find((d) => d.id === docA);
  const selectedDocB = documents.find((d) => d.id === docB);

  const isSameDocument = Boolean(docA && docB && docA === docB);
  const isDocAIncomplete = Boolean(selectedDocA && selectedDocA.status !== 'complete');
  const isDocBIncomplete = Boolean(selectedDocB && selectedDocB.status !== 'complete');

  const canInitiate =
    Boolean(docA && docB) &&
    !isSameDocument &&
    !isDocAIncomplete &&
    !isDocBIncomplete &&
    !isCreating;

  const handleCompare = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canInitiate) return;

    try {
      const comparisonId = await createComparison(docA, docB);
      navigate(`/compare/${comparisonId}`);
    } catch {
      // Error is set in store
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6 pb-12" data-testid="comparison-setup-page">
      {/* Page Header with Persistent Title for Routing Contract */}
      <div className="text-center space-y-2">
        <Badge variant="info" size="sm" className="uppercase tracking-wider">
          Contract Redlining
        </Badge>
        <h1 className="text-3xl font-serif font-bold text-primary-950">
          {t('comparison.setupTitle', 'Compare Legal Documents')}
        </h1>
        <p className="text-sm text-secondary-600 max-w-xl mx-auto">
          {t(
            'comparison.setupSubtitle',
            'Select two document versions to compare clause changes, additions, deletions, and risk level shifts side by side.'
          )}
        </p>
      </div>

      {/* Main Configuration Card */}
      <Card elevation="sm" className="border-secondary-300">
        <CardHeader className="bg-secondary-50/50 border-b border-secondary-200">
          <CardTitle className="text-lg text-primary-950">Comparison Configuration</CardTitle>
          <CardDescription>
            Choose a baseline contract and a counterparty or revised draft from your processed documents.
          </CardDescription>
        </CardHeader>

        <form onSubmit={handleCompare} data-testid="comparison-form">
          <CardContent className="space-y-6 pt-6">
            {/* Fetch Error or Store Error Alert */}
            {(fetchError || storeError) && (
              <div
                role="alert"
                className="p-3.5 rounded-lg bg-red-50 border border-red-200 text-xs sm:text-sm text-red-900 flex items-start gap-2.5"
              >
                <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" aria-hidden="true" />
                <span>{fetchError || storeError}</span>
              </div>
            )}

            {/* Validation: Same Document Selected Client-Side */}
            {isSameDocument && (
              <div
                role="alert"
                className="p-3.5 rounded-lg bg-amber-50 border border-amber-300 text-xs sm:text-sm text-amber-950 flex items-start gap-2.5"
                data-testid="same-document-warning"
              >
                <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" aria-hidden="true" />
                <div>
                  <strong className="font-semibold block">Identical Documents Selected:</strong>
                  <span>Cannot compare a document against itself. Please select two distinct contracts.</span>
                </div>
              </div>
            )}

            {/* Validation: Incomplete Document Selected */}
            {(isDocAIncomplete || isDocBIncomplete) && (
              <div
                role="alert"
                className="p-3.5 rounded-lg bg-amber-50 border border-amber-300 text-xs sm:text-sm text-amber-950 flex items-start gap-2.5"
                data-testid="incomplete-document-warning"
              >
                <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" aria-hidden="true" />
                <div>
                  <strong className="font-semibold block">Document Analysis Incomplete:</strong>
                  <span>
                    {isDocAIncomplete && selectedDocA
                      ? `Baseline document "${selectedDocA.original_filename}" has status "${selectedDocA.status}". `
                      : ''}
                    {isDocBIncomplete && selectedDocB
                      ? `Target document "${selectedDocB.original_filename}" has status "${selectedDocB.status}". `
                      : ''}
                    Both documents must be fully analyzed before pairwise comparison can be initiated.
                  </span>
                </div>
              </div>
            )}

            {/* Selectors Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Document A Selector */}
              <div className="space-y-3 p-4 rounded-xl border border-secondary-200 bg-secondary-50/50">
                <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-primary-100 text-primary-800">
                  Document A (Baseline)
                </span>
                <label
                  htmlFor="select-doc-a"
                  className="block text-xs font-semibold text-secondary-700"
                >
                  Select Base Contract
                </label>
                <select
                  id="select-doc-a"
                  aria-label="Select Base Contract"
                  value={docA}
                  onChange={(e) => setDocA(e.target.value)}
                  disabled={isLoadingDocs || isCreating}
                  className="w-full text-xs sm:text-sm rounded-lg border border-secondary-300 bg-white p-2.5 text-secondary-900 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-60"
                >
                  <option value="">-- Choose Base Document --</option>
                  {documents.map((doc) => (
                    <option key={`a-${doc.id}`} value={doc.id}>
                      {doc.original_filename} {doc.status !== 'complete' ? `(${doc.status})` : ''}
                    </option>
                  ))}
                </select>
                <p className="text-[11px] text-secondary-500">
                  Serves as the baseline reference point for clause alignment.
                </p>
              </div>

              {/* Document B Selector */}
              <div className="space-y-3 p-4 rounded-xl border border-secondary-200 bg-secondary-50/50">
                <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-accent-100 text-accent-800">
                  Document B (Counter-Party / Revised)
                </span>
                <label
                  htmlFor="select-doc-b"
                  className="block text-xs font-semibold text-secondary-700"
                >
                  Select Comparison Target
                </label>
                <select
                  id="select-doc-b"
                  aria-label="Select Comparison Target"
                  value={docB}
                  onChange={(e) => setDocB(e.target.value)}
                  disabled={isLoadingDocs || isCreating}
                  className="w-full text-xs sm:text-sm rounded-lg border border-secondary-300 bg-white p-2.5 text-secondary-900 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-60"
                >
                  <option value="">-- Choose Target Document --</option>
                  {documents.map((doc) => (
                    <option key={`b-${doc.id}`} value={doc.id}>
                      {doc.original_filename} {doc.status !== 'complete' ? `(${doc.status})` : ''}
                    </option>
                  ))}
                </select>
                <p className="text-[11px] text-secondary-500">
                  The revised counterparty draft or renegotiated version.
                </p>
              </div>
            </div>

            {/* Empty State Warning if user has no documents */}
            {!isLoadingDocs && documents.length < 2 && (
              <div className="p-4 rounded-xl border border-secondary-200 bg-white text-center space-y-2">
                <FileText className="w-8 h-8 text-secondary-400 mx-auto" />
                <p className="text-xs sm:text-sm text-secondary-700 font-medium">
                  You need at least two uploaded documents to run a comparison.
                </p>
                <Link to="/upload">
                  <Button variant="secondary" size="sm" className="gap-1.5 mt-1 text-xs">
                    <Upload className="w-3.5 h-3.5" />
                    <span>Upload New Document</span>
                  </Button>
                </Link>
              </div>
            )}
          </CardContent>

          <CardFooter className="flex flex-col sm:flex-row justify-between items-center gap-3 pt-4 border-t border-secondary-200">
            <Button
              type="button"
              variant="outline"
              size="md"
              onClick={() => navigate('/dashboard')}
              disabled={isCreating}
              className="w-full sm:w-auto text-xs"
            >
              {t('common.cancel', 'Cancel')}
            </Button>

            <Button
              type="submit"
              variant="primary"
              size="md"
              disabled={!canInitiate}
              className="w-full sm:w-auto gap-2 text-xs font-semibold"
              aria-label={t('comparison.compareButton', 'Run Version Comparison')}
            >
              {isCreating ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Aligning Clauses...</span>
                </>
              ) : (
                <>
                  <span>{t('comparison.compareButton', 'Run Version Comparison')}</span>
                  <ArrowRight className="w-4 h-4" aria-hidden="true" />
                </>
              )}
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
};
