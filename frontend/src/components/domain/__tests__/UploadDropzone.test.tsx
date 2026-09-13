import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { UploadDropzone } from '../UploadDropzone';
import { MAX_FILE_SIZE_BYTES } from '../../../utils/fileValidation';

describe('UploadDropzone (components/domain/UploadDropzone)', () => {
  it('renders with accessible role, button label, and helper hints', () => {
    render(<UploadDropzone onFileSelected={() => {}} />);

    const dropzone = screen.getByRole('button', { name: /Upload PDF legal document/i });
    expect(dropzone).toBeInTheDocument();
    expect(screen.getByText(/Drag & drop your contract here/i)).toBeInTheDocument();
    expect(screen.getByText(/Supported format: PDF up to 20 MB/i)).toBeInTheDocument();
  });

  it('accepts valid PDF file on drop and calls onFileSelected', () => {
    const handleFileSelected = vi.fn();
    const handleError = vi.fn();

    render(<UploadDropzone onFileSelected={handleFileSelected} onError={handleError} />);

    const validPdf = new File(['%PDF-1.4 sample content'], 'contract.pdf', {
      type: 'application/pdf',
    });

    const dropzone = screen.getByTestId('upload-dropzone');
    fireEvent.drop(dropzone, {
      dataTransfer: {
        files: [validPdf],
      },
    });

    expect(handleFileSelected).toHaveBeenCalledWith(validPdf);
    expect(handleError).not.toHaveBeenCalled();
  });

  it('rejects non-PDF files client-side without calling onFileSelected (PRD Ch. 14)', () => {
    const handleFileSelected = vi.fn();
    const handleError = vi.fn();

    render(<UploadDropzone onFileSelected={handleFileSelected} onError={handleError} />);

    const docxFile = new File(['docx content'], 'agreement.docx', {
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    });

    const dropzone = screen.getByTestId('upload-dropzone');
    fireEvent.drop(dropzone, {
      dataTransfer: {
        files: [docxFile],
      },
    });

    expect(handleFileSelected).not.toHaveBeenCalled();
    expect(handleError).toHaveBeenCalledWith(
      expect.stringContaining('Only PDF documents (.pdf) are supported')
    );
  });

  it('rejects oversized files > 20 MB client-side (PRD Ch. 14, Ch. 58 R-11)', () => {
    const handleFileSelected = vi.fn();
    const handleError = vi.fn();

    render(<UploadDropzone onFileSelected={handleFileSelected} onError={handleError} />);

    // Create file larger than 20MB
    const oversizedBytes = new Uint8Array(MAX_FILE_SIZE_BYTES + 1024);
    const oversizedFile = new File([oversizedBytes], 'huge_contract.pdf', {
      type: 'application/pdf',
    });

    const dropzone = screen.getByTestId('upload-dropzone');
    fireEvent.drop(dropzone, {
      dataTransfer: {
        files: [oversizedFile],
      },
    });

    expect(handleFileSelected).not.toHaveBeenCalled();
    expect(handleError).toHaveBeenCalledWith(
      expect.stringContaining('File size exceeds the 20MB limit')
    );
  });

  it('rejects empty 0-byte files client-side', () => {
    const handleFileSelected = vi.fn();
    const handleError = vi.fn();

    render(<UploadDropzone onFileSelected={handleFileSelected} onError={handleError} />);

    const emptyFile = new File([], 'empty.pdf', {
      type: 'application/pdf',
    });

    const dropzone = screen.getByTestId('upload-dropzone');
    fireEvent.drop(dropzone, {
      dataTransfer: {
        files: [emptyFile],
      },
    });

    expect(handleFileSelected).not.toHaveBeenCalled();
    expect(handleError).toHaveBeenCalledWith(
      expect.stringContaining('The selected file is empty (0 bytes)')
    );
  });

  it('handles drag-over and drag-leave styling states', () => {
    render(<UploadDropzone onFileSelected={() => {}} />);

    const dropzone = screen.getByTestId('upload-dropzone');
    fireEvent.dragOver(dropzone);
    expect(screen.getByText(/Drop your PDF contract here/i)).toBeInTheDocument();

    fireEvent.dragLeave(dropzone);
    expect(screen.getByText(/Drag & drop your contract here/i)).toBeInTheDocument();
  });

  it('handles file selection via hidden file input', () => {
    const handleFileSelected = vi.fn();
    render(<UploadDropzone onFileSelected={handleFileSelected} />);

    const validPdf = new File(['%PDF-1.4 content'], 'nda.pdf', {
      type: 'application/pdf',
    });

    const fileInput = screen.getByTestId('dropzone-file-input');
    fireEvent.change(fileInput, { target: { files: [validPdf] } });

    expect(handleFileSelected).toHaveBeenCalledWith(validPdf);
  });
});
