import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileText,
  ShieldCheck,
  AlertTriangle,
  Lock,
  X,
  ArrowRight,
  RefreshCw,
} from 'lucide-react';
import { useDocumentStore } from '../../store/documentStore';
import { documentService } from '../../services/api';
import { Button } from '../../components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../../components/ui/Card';
import { toast } from '../../components/ui/Toast';
import { UploadDropzone } from '../../components/domain/UploadDropzone';

export const UploadPage: React.FC = () => {
  const navigate = useNavigate();
  const fetchDocuments = useDocumentStore((state) => state.fetchDocuments);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const handleFileSelected = (file: File) => {
    // Client-side duplicate-file blocking must NOT exist per PRD Ch. 58 R-14.
    // Every selected file is accepted fresh.
    setSelectedFile(file);
    setErrorMessage(null);
  };

  const handleValidationError = (error: string) => {
    setErrorMessage(error);
  };

  const handleRemoveFile = () => {
    if (isUploading) return;
    setSelectedFile(null);
    setErrorMessage(null);
    setUploadProgress(0);
  };

  const handleCancelUpload = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsUploading(false);
    setUploadProgress(0);
    toast.info('Upload was canceled.');
  };

  const handleStartUpload = async () => {
    if (!selectedFile || isUploading) return;

    setIsUploading(true);
    setUploadProgress(0);
    setErrorMessage(null);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const response = await documentService.upload(
        selectedFile,
        (progress) => {
          setUploadProgress(progress);
        },
        controller.signal
      );

      // On successful upload: refresh documents store & hand-off to Processing
      toast.success(`"${response.original_filename}" uploaded successfully!`);
      fetchDocuments({ page: 1, page_size: 100 }).catch(() => {});
      navigate(`/documents/${response.id}/processing`);
    } catch (err: unknown) {
      // Check if user initiated cancel
      if (
        (err instanceof DOMException && err.name === 'AbortError') ||
        (err instanceof Error && err.name === 'CanceledError')
      ) {
        setIsUploading(false);
        setUploadProgress(0);
        return;
      }

      setIsUploading(false);
      setUploadProgress(0);

      const message =
        err instanceof Error ? err.message : 'Upload failed. Please check your connection and try again.';
      setErrorMessage(message);
    } finally {
      abortControllerRef.current = null;
    }
  };

  const isPasswordProtectedError =
    Boolean(errorMessage?.toLowerCase().includes('password')) ||
    Boolean(errorMessage?.toLowerCase().includes('encrypted'));

  return (
    <div className="max-w-2xl mx-auto space-y-6" data-testid="upload-page">
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-2xl sm:text-3xl font-serif font-bold text-primary-950">
          Upload Legal Document
        </h1>
        <p className="text-sm text-secondary-600 max-w-lg mx-auto">
          Upload a contract or agreement in PDF format for automated clause extraction and risk analysis.
        </p>
      </div>

      {/* Error Alert */}
      {errorMessage && (
        <div
          role="alert"
          aria-live="polite"
          className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-900 flex items-start gap-3 shadow-sm animate-in fade-in duration-200"
        >
          {isPasswordProtectedError ? (
            <Lock className="w-5 h-5 text-red-600 shrink-0 mt-0.5" aria-hidden="true" />
          ) : (
            <AlertTriangle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" aria-hidden="true" />
          )}
          <div className="flex-1 text-xs sm:text-sm">
            <strong className="font-semibold block mb-0.5">
              {isPasswordProtectedError ? 'Password-Protected PDF Detected' : 'Upload Validation Error'}
            </strong>
            <p className="text-red-800 leading-relaxed">{errorMessage}</p>
          </div>
          <button
            type="button"
            onClick={() => setErrorMessage(null)}
            aria-label="Dismiss error"
            className="p-1 rounded-md text-red-500 hover:text-red-700 hover:bg-red-100 transition-colors"
          >
            <X className="w-4 h-4" aria-hidden="true" />
          </button>
        </div>
      )}

      {/* Main Upload Card */}
      <Card elevation="sm" className="border-secondary-200">
        <CardHeader className="pb-4 border-b border-secondary-100">
          <CardTitle className="text-base text-primary-950">Document Ingestion</CardTitle>
          <CardDescription className="text-xs text-secondary-500">
            Maximum file size: 20 MB. Both digital and scanned PDFs are accepted for automated AI processing.
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-6 pt-6">
          {/* Dropzone (shown when no file selected) */}
          {!selectedFile && (
            <UploadDropzone
              onFileSelected={handleFileSelected}
              onError={handleValidationError}
              disabled={isUploading}
            />
          )}

          {/* Selected File Preview Card */}
          {selectedFile && (
            <div
              className="p-4 sm:p-5 rounded-xl border border-secondary-200 bg-secondary-50/50 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
              data-testid="selected-file-card"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className="p-2.5 rounded-lg bg-primary-100 text-primary-800 shrink-0 border border-primary-200">
                  <FileText className="w-6 h-6" aria-hidden="true" />
                </div>
                <div className="min-w-0">
                  <p
                    className="font-medium text-sm text-primary-950 truncate max-w-sm"
                    title={selectedFile.name}
                  >
                    {selectedFile.name}
                  </p>
                  <p className="text-xs text-secondary-500 mt-0.5">
                    {formatFileSize(selectedFile.size)} &bull; Ready for upload
                  </p>
                </div>
              </div>

              {!isUploading && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleRemoveFile}
                  className="text-xs text-secondary-600 hover:text-red-600 hover:border-red-300 gap-1.5 self-start sm:self-auto"
                >
                  <X className="w-3.5 h-3.5" aria-hidden="true" />
                  <span>Remove file</span>
                </Button>
              )}
            </div>
          )}

          {/* Progress Bar & Cancel Action (PRD Ch. 22.5) */}
          {isUploading && (
            <div
              className="p-4 rounded-xl border border-primary-200 bg-primary-50/40 space-y-3"
              data-testid="upload-progress-section"
            >
              <div className="flex items-center justify-between text-xs font-medium text-primary-950">
                <span className="flex items-center gap-2">
                  <RefreshCw className="w-3.5 h-3.5 animate-spin text-primary-700" aria-hidden="true" />
                  <span>Uploading contract to secure processing pipeline...</span>
                </span>
                <span className="font-semibold text-primary-900">{uploadProgress}%</span>
              </div>

              <div
                className="w-full h-2.5 bg-secondary-200 rounded-full overflow-hidden shadow-inner"
                role="progressbar"
                aria-valuenow={uploadProgress}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-label="Upload progress"
              >
                <div
                  className="h-full bg-primary-600 transition-all duration-150 ease-out"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>

              <div className="flex justify-end pt-1">
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={handleCancelUpload}
                  className="text-xs gap-1.5"
                >
                  <span>Cancel Upload</span>
                </Button>
              </div>
            </div>
          )}

          {/* Enterprise Security Copy (PRD Ch. 22.5) */}
          <div className="p-4 rounded-xl bg-secondary-50/80 border border-secondary-200 flex items-start gap-3 text-xs text-secondary-600 leading-relaxed">
            <ShieldCheck className="w-5 h-5 text-primary-700 shrink-0 mt-0.5" aria-hidden="true" />
            <div>
              <strong className="font-semibold text-primary-950 block mb-0.5">
                Enterprise Confidentiality & Privacy Guaranteed
              </strong>
              Your documents are processed in isolated tenant environments, encrypted at rest (AES-256) and in transit (TLS 1.3), and strictly ownership-scoped. ClarifAI never shares your proprietary legal agreements or uses your documents to train foundation AI models.
            </div>
          </div>
        </CardContent>

        <CardFooter className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-3 border-t border-secondary-100">
          <Button
            variant="outline"
            size="md"
            onClick={() => navigate('/dashboard')}
            disabled={isUploading}
            className="w-full sm:w-auto"
          >
            Back to Dashboard
          </Button>

          <Button
            variant="primary"
            size="md"
            onClick={handleStartUpload}
            disabled={!selectedFile || isUploading}
            isLoading={isUploading}
            className="w-full sm:w-auto gap-2 shadow-sm"
          >
            <span>{isUploading ? 'Uploading Document...' : 'Upload & Start Analysis'}</span>
            {!isUploading && <ArrowRight className="w-4 h-4" aria-hidden="true" />}
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
};

export default UploadPage;
