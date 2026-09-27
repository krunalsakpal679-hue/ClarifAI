import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Button } from '../../components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  FileText,
  RefreshCw,
  CheckCircle2,
  FolderOpen,
  Laptop,
  UploadCloud,
  X,
} from 'lucide-react';
import { useComparisonStore } from '../../store/comparisonStore';
import { documentService } from '../../services/api';
import { validatePdfFile } from '../../utils/fileValidation';
import { toast } from '../../components/ui/Toast';
import { cn } from '../../utils/cn';
import type { DocumentItem } from '../../types/documents';

interface DocumentSlotProps {
  slotTitle: string;
  badgeVariant: 'primary' | 'accent';
  source: 'library' | 'upload';
  onSourceChange: (s: 'library' | 'upload') => void;
  selectedId: string;
  onSelectChange: (id: string) => void;
  documents: DocumentItem[];
  selectId: string;
  selectLabel: string;
  hint: string;
  isLoadingDocs: boolean;
  isCreating: boolean;
  onDocumentAdded: (doc: DocumentItem) => void;
  isAnalyzing: boolean;
  setIsAnalyzing: (b: boolean) => void;
}

const DocumentSlot: React.FC<DocumentSlotProps> = ({
  slotTitle,
  badgeVariant,
  source,
  onSourceChange,
  selectedId,
  onSelectChange,
  documents,
  selectId,
  selectLabel,
  hint,
  isLoadingDocs,
  isCreating,
  onDocumentAdded,
  isAnalyzing,
  setIsAnalyzing,
}) => {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadedFile, setUploadedFile] = useState<DocumentItem | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const pollTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Clean up timer on unmount
  useEffect(() => {
    return () => {
      if (pollTimerRef.current) {
        clearInterval(pollTimerRef.current);
      }
    };
  }, []);

  const selectedDoc = documents.find((d) => d.id === selectedId) || uploadedFile;

  const handleFileUpload = async (file: File) => {
    const valErr = validatePdfFile(file);
    if (valErr) {
      setUploadError(valErr);
      return;
    }

    setUploadError(null);
    setIsUploading(true);
    setUploadProgress(0);

    try {
      const res = await documentService.upload(file, (pct) => {
        setUploadProgress(pct);
      });

      setIsUploading(false);
      setIsAnalyzing(true);

      // Poll until analysis completes
      let attempts = 0;
      pollTimerRef.current = setInterval(async () => {
        attempts++;
        try {
          const doc = await documentService.getById(res.id);
          if (doc.status === 'complete') {
            if (pollTimerRef.current) clearInterval(pollTimerRef.current);
            setIsAnalyzing(false);
            setUploadedFile(doc);
            onDocumentAdded(doc);
            onSelectChange(doc.id);
            toast.success(`"${doc.original_filename}" analyzed and ready for comparison!`);
          } else if (doc.status === 'failed') {
            if (pollTimerRef.current) clearInterval(pollTimerRef.current);
            setIsAnalyzing(false);
            setUploadError('Document analysis failed. Please try a different contract file.');
          } else if (attempts > 60) {
            if (pollTimerRef.current) clearInterval(pollTimerRef.current);
            setIsAnalyzing(false);
            setUploadError('Analysis timed out. Please try again.');
          }
        } catch {
          if (attempts > 5) {
            if (pollTimerRef.current) clearInterval(pollTimerRef.current);
            setIsAnalyzing(false);
            setUploadError('Failed to verify document status.');
          }
        }
      }, 2000);
    } catch (err) {
      setIsUploading(false);
      setIsAnalyzing(false);
      const msg = err instanceof Error ? err.message : 'Upload failed. Please try again.';
      setUploadError(msg);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileUpload(files[0]);
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
    if (isUploading || isAnalyzing || isCreating) return;
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  const resetUpload = () => {
    if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    setUploadedFile(null);
    setUploadError(null);
    setIsUploading(false);
    setIsAnalyzing(false);
    setUploadProgress(0);
    onSelectChange('');
  };

  return (
    <div className="space-y-3 p-4 rounded-xl border border-secondary-200 bg-secondary-50/50 flex flex-col justify-between">
      {/* Slot Header */}
      <div>
        <div className="flex items-center justify-between gap-2 mb-2">
          <span
            className={cn(
              'inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider',
              badgeVariant === 'primary'
                ? 'bg-primary-100 text-primary-800'
                : 'bg-accent-100 text-accent-800'
            )}
          >
            {slotTitle}
          </span>

          {/* Segmented Source Switcher */}
          <div className="flex items-center p-0.5 bg-secondary-200/70 rounded-lg text-[11px]">
            <button
              type="button"
              onClick={() => onSourceChange('library')}
              className={cn(
                'flex items-center gap-1 px-2 py-1 rounded-md font-medium transition-all',
                source === 'library'
                  ? 'bg-white text-secondary-900 shadow-sm'
                  : 'text-secondary-600 hover:text-secondary-900'
              )}
            >
              <FolderOpen className="w-3 h-3" />
              <span>Library</span>
            </button>
            <button
              type="button"
              onClick={() => onSourceChange('upload')}
              className={cn(
                'flex items-center gap-1 px-2 py-1 rounded-md font-medium transition-all',
                source === 'upload'
                  ? 'bg-white text-secondary-900 shadow-sm'
                  : 'text-secondary-600 hover:text-secondary-900'
              )}
            >
              <Laptop className="w-3 h-3" />
              <span>Upload from PC</span>
            </button>
          </div>
        </div>

        {/* Hidden or Active Select for Accessibility & Test Contract */}
        <label
          htmlFor={selectId}
          className={cn(
            'block text-xs font-semibold text-secondary-700 mb-1.5',
            source === 'upload' && 'sr-only'
          )}
        >
          {selectLabel}
        </label>
        <select
          id={selectId}
          aria-label={selectLabel}
          value={selectedId}
          onChange={(e) => onSelectChange(e.target.value)}
          disabled={isLoadingDocs || isCreating || isUploading || isAnalyzing}
          className={cn(
            'w-full text-xs sm:text-sm rounded-lg border border-secondary-300 bg-white p-2.5 text-secondary-900 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-60',
            source === 'upload' && 'hidden'
          )}
        >
          <option value="">-- Choose Contract --</option>
          {documents.map((doc) => (
            <option key={`${selectId}-${doc.id}`} value={doc.id}>
              {doc.original_filename} {doc.status !== 'complete' ? `(${doc.status})` : ''}
            </option>
          ))}
        </select>

        {/* Upload Mode UI */}
        {source === 'upload' && (
          <div className="space-y-2">
            {/* 1. Upload in progress or analyzing */}
            {(isUploading || isAnalyzing) && (
              <div className="p-4 rounded-xl border border-primary-200 bg-primary-50/50 text-center space-y-2">
                <RefreshCw className="w-6 h-6 text-primary-600 animate-spin mx-auto" />
                <p className="text-xs font-semibold text-primary-950">
                  {isUploading ? `Uploading document (${uploadProgress}%)` : 'Analyzing clauses & risk factors...'}
                </p>
                <div className="w-full bg-primary-100 rounded-full h-1.5 overflow-hidden">
                  <div
                    className={cn(
                      'h-full bg-primary-600 transition-all duration-300',
                      isAnalyzing && 'w-full animate-pulse'
                    )}
                    style={{ width: isUploading ? `${uploadProgress}%` : '100%' }}
                  />
                </div>
                <p className="text-[10px] text-primary-700">Please wait while ClarifAI processes the contract.</p>
              </div>
            )}

            {/* 2. Upload Complete and Ready */}
            {!isUploading && !isAnalyzing && selectedDoc && selectedDoc.status === 'complete' && (
              <div className="p-3.5 rounded-xl border border-emerald-300 bg-emerald-50/60 flex items-start justify-between gap-2.5">
                <div className="flex items-start gap-2 overflow-hidden">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <div className="overflow-hidden">
                    <p className="text-xs font-semibold text-emerald-950 truncate" title={selectedDoc.original_filename}>
                      {selectedDoc.original_filename}
                    </p>
                    <div className="flex items-center gap-1.5 mt-0.5">
                      <Badge variant="success" size="sm">Ready to compare</Badge>
                      {selectedDoc.overall_risk && (
                        <span className="text-[10px] text-emerald-700 capitalize">
                          Risk: {selectedDoc.overall_risk}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={resetUpload}
                  className="text-xs text-secondary-500 hover:text-red-600 p-1 rounded hover:bg-white transition-colors"
                  title="Choose a different file"
                  aria-label="Remove uploaded file"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            )}

            {/* 3. Dropzone when no file selected or ready to choose */}
            {!isUploading && !isAnalyzing && (!selectedDoc || selectedDoc.status !== 'complete') && (
              <div
                role="button"
                tabIndex={0}
                onClick={() => fileInputRef.current?.click()}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    fileInputRef.current?.click();
                  }
                }}
                onDragOver={(e) => {
                  e.preventDefault();
                  setIsDragOver(true);
                }}
                onDragLeave={() => setIsDragOver(false)}
                onDrop={handleDrop}
                className={cn(
                  'cursor-pointer border-2 border-dashed rounded-xl p-4 text-center transition-all flex flex-col items-center justify-center gap-1.5',
                  isDragOver
                    ? 'border-primary-500 bg-primary-50/70 scale-[1.01]'
                    : 'border-secondary-300 bg-white hover:border-primary-400 hover:bg-secondary-50'
                )}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,application/pdf"
                  className="hidden"
                  onChange={handleFileInputChange}
                  aria-label={`Upload ${slotTitle} PDF from PC`}
                />
                <UploadCloud className="w-6 h-6 text-primary-600" />
                <div>
                  <span className="text-xs font-semibold text-primary-800 underline">
                    Choose PDF from PC
                  </span>{' '}
                  <span className="text-xs text-secondary-500">or drag & drop</span>
                </div>
                <p className="text-[10px] text-secondary-400">PDF up to 20MB</p>
              </div>
            )}

            {/* Upload Error */}
            {uploadError && (
              <div className="p-2.5 rounded-lg bg-red-50 border border-red-200 text-xs text-red-800 flex items-start gap-1.5">
                <AlertCircle className="w-3.5 h-3.5 text-red-600 shrink-0 mt-0.5" />
                <span className="flex-1">{uploadError}</span>
                <button
                  type="button"
                  onClick={() => setUploadError(null)}
                  className="text-red-600 hover:text-red-900"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      <p className="text-[11px] text-secondary-500 pt-1 border-t border-secondary-200/60">
        {hint}
      </p>
    </div>
  );
};

export const ComparisonSetupPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { createComparison, isCreating, error: storeError, reset } = useComparisonStore();

  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [isLoadingDocs, setIsLoadingDocs] = useState<boolean>(true);
  const [fetchError, setFetchError] = useState<string | null>(null);

  const [sourceA, setSourceA] = useState<'library' | 'upload'>('library');
  const [sourceB, setSourceB] = useState<'library' | 'upload'>('library');

  const [docA, setDocA] = useState<string>('');
  const [docB, setDocB] = useState<string>('');

  const [isAnalyzingA, setIsAnalyzingA] = useState(false);
  const [isAnalyzingB, setIsAnalyzingB] = useState(false);

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

  const handleDocumentAdded = (newDoc: DocumentItem) => {
    setDocuments((prev) => [newDoc, ...prev.filter((d) => d.id !== newDoc.id)]);
  };

  const selectedDocA = documents.find((d) => d.id === docA);
  const selectedDocB = documents.find((d) => d.id === docB);

  const isSameDocument = Boolean(docA && docB && docA === docB);
  const isDocAIncomplete = Boolean(selectedDocA && selectedDocA.status !== 'complete');
  const isDocBIncomplete = Boolean(selectedDocB && selectedDocB.status !== 'complete');
  const isBusy = isCreating || isAnalyzingA || isAnalyzingB;

  const canInitiate =
    Boolean(docA && docB) &&
    !isSameDocument &&
    !isDocAIncomplete &&
    !isDocBIncomplete &&
    !isBusy;

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
      {/* Page Header */}
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
            'Select two document versions from your library or upload them from your PC to compare clause changes, additions, deletions, and risk level shifts side by side.'
          )}
        </p>
      </div>

      {/* Main Configuration Card */}
      <Card elevation="sm" className="border-secondary-300">
        <CardHeader className="bg-secondary-50/50 border-b border-secondary-200">
          <CardTitle className="text-lg text-primary-950">Comparison Configuration</CardTitle>
          <CardDescription>
            Choose a baseline contract and a counterparty or revised draft from your library or upload directly from your PC.
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
                  <span>Cannot compare a document against itself. Please select or upload two distinct contracts.</span>
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
              {/* Document A Slot */}
              <DocumentSlot
                slotTitle="Document A (Baseline)"
                badgeVariant="primary"
                source={sourceA}
                onSourceChange={setSourceA}
                selectedId={docA}
                onSelectChange={setDocA}
                documents={documents}
                selectId="select-doc-a"
                selectLabel="Select Base Contract"
                hint="Serves as the baseline reference point for clause alignment."
                isLoadingDocs={isLoadingDocs}
                isCreating={isCreating}
                onDocumentAdded={handleDocumentAdded}
                isAnalyzing={isAnalyzingA}
                setIsAnalyzing={setIsAnalyzingA}
              />

              {/* Document B Slot */}
              <DocumentSlot
                slotTitle="Document B (Counter-Party / Revised)"
                badgeVariant="accent"
                source={sourceB}
                onSourceChange={setSourceB}
                selectedId={docB}
                onSelectChange={setDocB}
                documents={documents}
                selectId="select-doc-b"
                selectLabel="Select Comparison Target"
                hint="The revised counterparty draft or renegotiated version."
                isLoadingDocs={isLoadingDocs}
                isCreating={isCreating}
                onDocumentAdded={handleDocumentAdded}
                isAnalyzing={isAnalyzingB}
                setIsAnalyzing={setIsAnalyzingB}
              />
            </div>

            {/* Helpful guidance if user has fewer than 2 documents */}
            {!isLoadingDocs && documents.length < 2 && (
              <div className="p-4 rounded-xl border border-secondary-200 bg-white text-center space-y-2">
                <FileText className="w-8 h-8 text-secondary-400 mx-auto" />
                <p className="text-xs sm:text-sm text-secondary-700 font-medium">
                  You need at least two uploaded documents to run a comparison.
                </p>
                <p className="text-xs text-secondary-500">
                  You can upload files directly from your PC using the <strong>Upload from PC</strong> tab above for Document A and Document B.
                </p>
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
              {isBusy ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>{isCreating ? 'Aligning Clauses...' : 'Processing Document...'}</span>
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
