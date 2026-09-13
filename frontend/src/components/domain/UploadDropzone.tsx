import React, { useRef, useState } from 'react';
import { UploadCloud, FileText } from 'lucide-react';
import { cn } from '../../utils/cn';
import { validatePdfFile } from '../../utils/fileValidation';

export interface UploadDropzoneProps {
  onFileSelected: (file: File) => void;
  onError?: (errorMessage: string) => void;
  disabled?: boolean;
  className?: string;
}

export const UploadDropzone: React.FC<UploadDropzoneProps> = ({
  onFileSelected,
  onError,
  disabled = false,
  className,
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const processFile = (file: File) => {
    const validationError = validatePdfFile(file);
    if (validationError) {
      onError?.(validationError);
      return;
    }

    onFileSelected(file);
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) {
      setIsDragOver(true);
    }
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    if (disabled) return;

    const droppedFiles = e.dataTransfer.files;
    if (droppedFiles && droppedFiles.length > 0) {
      processFile(droppedFiles[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = e.target.files;
    if (selectedFiles && selectedFiles.length > 0) {
      processFile(selectedFiles[0]);
    }
    // Reset file input value so re-selecting the identical file triggers onChange (PRD Ch. 58 R-14 duplicate upload support)
    if (inputRef.current) {
      inputRef.current.value = '';
    }
  };

  const handleClick = () => {
    if (!disabled) {
      inputRef.current?.click();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if ((e.key === 'Enter' || e.key === ' ') && !disabled) {
      e.preventDefault();
      inputRef.current?.click();
    }
  };

  return (
    <div
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-label="Upload PDF legal document"
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      data-testid="upload-dropzone"
      className={cn(
        'relative flex flex-col items-center justify-center p-8 sm:p-12 text-center rounded-2xl border-2 border-dashed transition-all duration-micro select-none',
        isDragOver
          ? 'border-primary-600 bg-primary-50/70 scale-[1.008] shadow-elevation-2'
          : 'border-secondary-300 bg-secondary-50/40 hover:bg-secondary-50 hover:border-secondary-400',
        disabled && 'opacity-60 cursor-not-allowed pointer-events-none',
        !disabled && 'cursor-pointer focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
        className
      )}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,application/pdf"
        className="sr-only"
        tabIndex={-1}
        aria-hidden="true"
        disabled={disabled}
        onChange={handleFileInputChange}
        data-testid="dropzone-file-input"
      />

      <div
        className={cn(
          'w-16 h-16 rounded-full flex items-center justify-center mb-4 transition-colors',
          isDragOver
            ? 'bg-primary-600 text-white shadow-md'
            : 'bg-primary-100 text-primary-800'
        )}
      >
        {isDragOver ? (
          <FileText className="w-8 h-8 animate-bounce" aria-hidden="true" />
        ) : (
          <UploadCloud className="w-8 h-8" aria-hidden="true" />
        )}
      </div>

      <div className="space-y-1.5 max-w-sm">
        <p className="text-base font-semibold text-primary-950">
          {isDragOver ? (
            'Drop your PDF contract here'
          ) : (
            <>
              Drag & drop your contract here, or{' '}
              <span className="text-primary-700 underline underline-offset-2 hover:text-primary-900">
                browse files
              </span>
            </>
          )}
        </p>
        <p className="text-xs text-secondary-500">
          Supported format: PDF up to 20 MB (digital or scanned)
        </p>
      </div>
    </div>
  );
};

export default UploadDropzone;
