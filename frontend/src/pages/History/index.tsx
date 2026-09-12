import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  FileText,
  Trash2,
  Download,
  AlertTriangle,
  RefreshCw,
  Plus,
  ArrowRight,
  FolderOpen,
} from 'lucide-react';
import { useDocumentStore } from '../../store/documentStore';
import { toast } from '../../components/ui/Toast';
import { Button } from '../../components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/Card';
import { Modal } from '../../components/ui/Modal';
import { SkeletonBlock } from '../../components/ui/SkeletonBlock';
import { DocumentStatusBadge } from '../../components/domain/DocumentStatusBadge';
import { RiskLevelIndicator } from '../../components/domain/RiskLevelIndicator';
import type { DocumentItem } from '../../types';

export const HistoryPage: React.FC = () => {
  const { t } = useTranslation();
  const documents = useDocumentStore((state) => state.documents);
  const isLoading = useDocumentStore((state) => state.isLoading);
  const error = useDocumentStore((state) => state.error);
  const fetchDocuments = useDocumentStore((state) => state.fetchDocuments);
  const deleteDocument = useDocumentStore((state) => state.deleteDocument);

  const [documentToDelete, setDocumentToDelete] = useState<DocumentItem | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Fetch full untruncated document archive on mount (PRD Ch. 59: lists all documents without search/filter)
  useEffect(() => {
    fetchDocuments({ page: 1, page_size: 100 });
  }, [fetchDocuments]);

  const handleDeleteConfirm = async () => {
    if (!documentToDelete) return;

    setIsDeleting(true);
    try {
      await deleteDocument(documentToDelete.id);
      toast.success(`"${documentToDelete.original_filename}" was deleted.`);
      setDocumentToDelete(null);
    } catch {
      // Functional Requirement: Delete failure -> toast, list unchanged
      toast.error('Failed to delete document. Please try again.');
    } finally {
      setIsDeleting(false);
    }
  };

  const formatDate = (isoString: string) => {
    try {
      return new Intl.DateTimeFormat('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      }).format(new Date(isoString));
    } catch {
      return isoString;
    }
  };

  return (
    <div className="space-y-6" data-testid="history-page">
      {/* Header & Upload CTA */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-secondary-200">
        <div>
          <h1 className="text-2xl sm:text-3xl font-serif font-bold text-primary-950">
            Document History
          </h1>
          <p className="text-secondary-600 text-sm mt-1">
            Access and manage previously simplified and analyzed legal contracts.
          </p>
        </div>

        <Link to="/upload">
          <Button variant="primary" size="md" className="gap-2 shadow-sm">
            <Plus className="w-4 h-4" aria-hidden="true" />
            <span>+ Upload New Document</span>
          </Button>
        </Link>
      </div>

      {/* Error Alert with Retry */}
      {error && (
        <div
          role="alert"
          aria-live="polite"
          className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
        >
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-red-600 shrink-0" aria-hidden="true" />
            <div>
              <p className="text-sm font-semibold">Unable to load document history</p>
              <p className="text-xs text-red-700">{error}</p>
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => fetchDocuments({ page: 1, page_size: 100 })}
            className="border-red-300 text-red-800 hover:bg-red-100 gap-1.5 self-start sm:self-auto"
          >
            <RefreshCw className="w-3.5 h-3.5" aria-hidden="true" />
            <span>{t('common.retry', 'Retry')}</span>
          </Button>
        </div>
      )}

      {/* Main Content Repository */}
      <Card elevation="sm" className="border-secondary-200">
        <CardHeader className="pb-3 border-b border-secondary-100">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg text-primary-950">Analyzed Documents Repository</CardTitle>
              <CardDescription className="text-xs mt-0.5">
                {isLoading
                  ? 'Loading document repository...'
                  : `Showing ${documents.length} contract${documents.length === 1 ? '' : 's'} stored in your workspace.`}
              </CardDescription>
            </div>
          </div>
        </CardHeader>

        <CardContent className="p-0">
          {/* Desktop Table View (>= 768px per PRD Ch. 24) - Semantic table remains in DOM for accessibility and routing contract */}
          <div className="overflow-x-auto">
            <table
              className="w-full text-left text-sm"
              role="table"
              aria-label="Document History"
            >
              <thead>
                <tr className="border-b border-secondary-200 bg-secondary-50 text-secondary-700 text-xs uppercase font-semibold tracking-wider">
                  <th scope="col" className="py-3 px-4 sm:px-6">Document Name</th>
                  <th scope="col" className="py-3 px-4">Status</th>
                  <th scope="col" className="py-3 px-4">Risk Severity</th>
                  <th scope="col" className="py-3 px-4">Upload Date</th>
                  <th scope="col" className="py-3 px-4 sm:px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-secondary-100">
                {/* Loading Skeletons */}
                {isLoading && (
                  [1, 2, 3, 4].map((i) => (
                    <tr key={i} className="animate-pulse" data-testid="history-skeleton-row">
                      <td className="py-4 px-4 sm:px-6">
                        <div className="space-y-2">
                          <SkeletonBlock height="1.25rem" width="60%" />
                          <SkeletonBlock height="0.8rem" width="35%" />
                        </div>
                      </td>
                      <td className="py-4 px-4">
                        <SkeletonBlock height="1.5rem" width="5rem" rounded="full" />
                      </td>
                      <td className="py-4 px-4">
                        <SkeletonBlock height="1.5rem" width="5.5rem" rounded="full" />
                      </td>
                      <td className="py-4 px-4">
                        <SkeletonBlock height="1rem" width="4rem" />
                      </td>
                      <td className="py-4 px-4 sm:px-6 text-right">
                        <SkeletonBlock height="2rem" width="5.5rem" className="ml-auto" />
                      </td>
                    </tr>
                  ))
                )}

                {/* Empty State */}
                {!isLoading && documents.length === 0 && (
                  <tr>
                    <td colSpan={5} className="py-12 px-4 text-center">
                      <div className="flex flex-col items-center justify-center space-y-4 max-w-md mx-auto">
                        <div className="w-16 h-16 rounded-full bg-primary-100 text-primary-800 flex items-center justify-center shadow-sm">
                          <FolderOpen className="w-8 h-8" aria-hidden="true" />
                        </div>
                        <div className="space-y-1">
                          <h3 className="text-lg font-serif font-bold text-primary-950">
                            No documents in history
                          </h3>
                          <p className="text-xs text-secondary-600 leading-relaxed">
                            Your document repository is currently empty. Upload contracts, service agreements, or NDAs to begin automated clause risk simplification.
                          </p>
                        </div>
                        <Link to="/upload" className="pt-2">
                          <Button variant="primary" size="md" className="gap-2 shadow-sm">
                            <Plus className="w-4 h-4" aria-hidden="true" />
                            <span>Upload Document</span>
                          </Button>
                        </Link>
                      </div>
                    </td>
                  </tr>
                )}

                {/* Populated Document Rows (Desktop View >= 768px) */}
                {!isLoading &&
                  documents.map((doc) => {
                    const isComplete = doc.status === 'complete';
                    const isInProgress = !isComplete && doc.status !== 'failed';
                    const targetLink = isInProgress
                      ? `/documents/${doc.id}/processing`
                      : `/documents/${doc.id}`;

                    return (
                      <tr
                        key={doc.id}
                        className="hidden md:table-row hover:bg-secondary-50/70 transition-colors duration-micro"
                      >
                        {/* Name & Type */}
                        <td className="py-4 px-4 sm:px-6">
                          <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-primary-50 text-primary-800 shrink-0 border border-primary-100">
                              <FileText className="w-4 h-4" aria-hidden="true" />
                            </div>
                            <div className="min-w-0">
                              <Link
                                to={targetLink}
                                className="font-medium text-primary-950 hover:text-primary-800 hover:underline block truncate max-w-xs xl:max-w-md"
                                title={doc.original_filename}
                              >
                                {doc.original_filename}
                              </Link>
                              {doc.document_type && (
                                <span className="text-xs text-secondary-500 block">
                                  {doc.document_type}
                                </span>
                              )}
                            </div>
                          </div>
                        </td>

                        {/* Status */}
                        <td className="py-4 px-4 whitespace-nowrap">
                          <DocumentStatusBadge status={doc.status} />
                        </td>

                        {/* Risk Severity (PRD Ch. 20) */}
                        <td className="py-4 px-4 whitespace-nowrap">
                          <RiskLevelIndicator risk={doc.overall_risk} size="sm" />
                        </td>

                        {/* Upload Date */}
                        <td className="py-4 px-4 text-xs text-secondary-600 whitespace-nowrap">
                          {formatDate(doc.uploaded_at)}
                        </td>

                        {/* Actions */}
                        <td className="py-4 px-4 sm:px-6 text-right whitespace-nowrap">
                          <div className="inline-flex items-center gap-2">
                            <Link
                              to={targetLink}
                              aria-label={`View analysis for ${doc.original_filename}`}
                            >
                              <Button
                                variant="outline"
                                size="sm"
                                className="gap-1.5 text-xs text-primary-900 border-secondary-300"
                              >
                                <span>View</span>
                                <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
                              </Button>
                            </Link>

                            {isComplete && (
                              <Link
                                to={`/documents/${doc.id}/report`}
                                aria-label={`Download report for ${doc.original_filename}`}
                              >
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="p-2 text-secondary-600 hover:text-primary-900"
                                  title="Download Report"
                                >
                                  <Download className="w-4 h-4" aria-hidden="true" />
                                </Button>
                              </Link>
                            )}

                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setDocumentToDelete(doc)}
                              className="p-2 text-secondary-500 hover:text-red-600 hover:bg-red-50"
                              aria-label={`Delete ${doc.original_filename}`}
                              title="Delete document"
                            >
                              <Trash2 className="w-4 h-4 text-red-600" aria-hidden="true" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
              </tbody>
            </table>
          </div>

          {/* Mobile Card View (< 768px per PRD Ch. 24) */}
          {!isLoading && documents.length > 0 && (
            <div className="md:hidden divide-y divide-secondary-100" data-testid="mobile-cards-view">
              {documents.map((doc) => {
                const isComplete = doc.status === 'complete';
                const isInProgress = !isComplete && doc.status !== 'failed';
                const targetLink = isInProgress
                  ? `/documents/${doc.id}/processing`
                  : `/documents/${doc.id}`;

                return (
                  <div key={doc.id} className="p-4 space-y-3">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-start gap-2.5 min-w-0">
                        <div className="p-1.5 rounded-md bg-primary-50 text-primary-800 shrink-0 mt-0.5 border border-primary-100">
                          <FileText className="w-4 h-4" aria-hidden="true" />
                        </div>
                        <div className="min-w-0">
                          <Link
                            to={targetLink}
                            className="font-medium text-sm text-primary-950 hover:underline block truncate max-w-[200px]"
                            title={doc.original_filename}
                          >
                            {doc.original_filename}
                          </Link>
                          <span className="text-[11px] text-secondary-500">
                            Uploaded {formatDate(doc.uploaded_at)}
                          </span>
                        </div>
                      </div>

                      <DocumentStatusBadge status={doc.status} />
                    </div>

                    <div className="flex items-center justify-between pt-2 border-t border-secondary-100">
                      <span className="text-xs text-secondary-600 font-medium">Risk Level:</span>
                      <RiskLevelIndicator risk={doc.overall_risk} size="sm" />
                    </div>

                    <div className="flex items-center justify-between gap-2 pt-2 border-t border-secondary-100">
                      <Link
                        to={targetLink}
                        className="flex-1"
                        aria-label={`View analysis for ${doc.original_filename}`}
                      >
                        <Button
                          variant="outline"
                          size="sm"
                          className="w-full justify-center text-xs gap-1.5"
                        >
                          <span>View Analysis</span>
                          <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
                        </Button>
                      </Link>

                      {isComplete && (
                        <Link
                          to={`/documents/${doc.id}/report`}
                          aria-label={`Download report for ${doc.original_filename}`}
                        >
                          <Button variant="ghost" size="sm" className="p-2 text-secondary-600" title="Report">
                            <Download className="w-4 h-4" aria-hidden="true" />
                          </Button>
                        </Link>
                      )}

                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setDocumentToDelete(doc)}
                        className="p-2 text-red-600 hover:bg-red-50"
                        aria-label={`Delete ${doc.original_filename}`}
                        title="Delete document"
                      >
                        <Trash2 className="w-4 h-4 text-red-600" aria-hidden="true" />
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={Boolean(documentToDelete)}
        onClose={() => {
          if (!isDeleting) setDocumentToDelete(null);
        }}
        title="Delete Document"
        description="This action cannot be undone."
      >
        <div className="space-y-4">
          <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-red-800 flex items-start gap-2.5">
            <AlertTriangle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" aria-hidden="true" />
            <p>
              Deleting this contract will permanently purge the uploaded PDF, all extracted clauses, summaries, and associated AI embeddings.
            </p>
          </div>

          <p className="text-sm text-secondary-700">
            Are you sure you want to delete{' '}
            <strong className="text-primary-950 font-semibold break-all">
              "{documentToDelete?.original_filename}"
            </strong>
            ?
          </p>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-secondary-100">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setDocumentToDelete(null)}
              disabled={isDeleting}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              size="sm"
              onClick={handleDeleteConfirm}
              isLoading={isDeleting}
              disabled={isDeleting}
              className="gap-1.5"
            >
              <Trash2 className="w-3.5 h-3.5" aria-hidden="true" />
              <span>{isDeleting ? 'Deleting...' : 'Delete Document'}</span>
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default HistoryPage;
