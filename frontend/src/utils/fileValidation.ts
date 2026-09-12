/**
 * PDF file validation utilities (PRD Ch. 14, Ch. 58 R-11)
 */

export const MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024; // 20 MB

export const validatePdfFile = (file: File): string | null => {
  // 1. Client-side empty file check
  if (file.size === 0) {
    return 'The selected file is empty (0 bytes). Please upload a valid PDF document.';
  }

  // 2. Client-side size limit check (PRD Ch. 14, Ch. 58 R-11)
  if (file.size > MAX_FILE_SIZE_BYTES) {
    return 'File size exceeds the 20MB limit. Please upload a smaller contract document.';
  }

  // 3. Client-side PDF file type check (PRD Ch. 14)
  const isPdf =
    file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
  if (!isPdf) {
    return 'Only PDF documents (.pdf) are supported. Please select a valid PDF contract.';
  }

  return null;
};
