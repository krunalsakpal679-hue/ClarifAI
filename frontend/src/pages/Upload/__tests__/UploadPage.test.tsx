import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { UploadPage } from '../index';
import { documentService } from '../../../services/api';
import { toast } from '../../../components/ui/Toast';
import '../../../app/i18n';

// Spy on Toast methods
vi.spyOn(toast, 'success');
vi.spyOn(toast, 'error');
vi.spyOn(toast, 'info');

const mockedNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockedNavigate,
  };
});

describe('UploadPage (PRD Ch. 14, 22.5, 58 & Section 8.2)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderUploadPage = () => {
    return render(
      <MemoryRouter>
        <UploadPage />
      </MemoryRouter>
    );
  };

  it('renders page header, dropzone, and enterprise security reassurance copy', () => {
    renderUploadPage();

    expect(screen.getByRole('heading', { name: /Upload Legal Document/i })).toBeInTheDocument();
    expect(screen.getByTestId('upload-dropzone')).toBeInTheDocument();
    expect(
      screen.getByText(/Enterprise Confidentiality & Privacy Guaranteed/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/encrypted at rest \(AES-256\) and in transit \(TLS 1.3\)/i)
    ).toBeInTheDocument();
  });

  it('rejects non-PDF files client-side without initiating any network call (PRD Ch. 14)', async () => {
    const uploadSpy = vi.spyOn(documentService, 'upload');
    renderUploadPage();

    const docxFile = new File(['binary docx'], 'contract.docx', {
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    });

    const dropzone = screen.getByTestId('upload-dropzone');
    fireEvent.drop(dropzone, {
      dataTransfer: { files: [docxFile] },
    });

    expect(uploadSpy).not.toHaveBeenCalled();
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText(/Only PDF documents \(\.pdf\) are supported/i)).toBeInTheDocument();
    expect(screen.queryByTestId('selected-file-card')).not.toBeInTheDocument();
  });

  it('rejects oversized files (>20MB) client-side without initiating network call (PRD Ch. 58 R-11)', async () => {
    const uploadSpy = vi.spyOn(documentService, 'upload');
    renderUploadPage();

    const hugeFile = new File([new Uint8Array(21 * 1024 * 1024)], 'giant_contract.pdf', {
      type: 'application/pdf',
    });

    const dropzone = screen.getByTestId('upload-dropzone');
    fireEvent.drop(dropzone, {
      dataTransfer: { files: [hugeFile] },
    });

    expect(uploadSpy).not.toHaveBeenCalled();
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText(/File size exceeds the 20MB limit/i)).toBeInTheDocument();
    expect(screen.queryByTestId('selected-file-card')).not.toBeInTheDocument();
  });

  it('selects valid PDF, shows preview card, and allows removal', () => {
    renderUploadPage();

    const validFile = new File(['%PDF-1.4 sample content'], 'Master_Agreement.pdf', {
      type: 'application/pdf',
    });

    const dropzone = screen.getByTestId('upload-dropzone');
    fireEvent.drop(dropzone, {
      dataTransfer: { files: [validFile] },
    });

    // Preview card is rendered
    expect(screen.getByTestId('selected-file-card')).toBeInTheDocument();
    expect(screen.getByText('Master_Agreement.pdf')).toBeInTheDocument();
    expect(screen.getByText(/Ready for upload/i)).toBeInTheDocument();

    // Click Remove file
    const removeBtn = screen.getByRole('button', { name: /Remove file/i });
    fireEvent.click(removeBtn);

    // Dropzone restored
    expect(screen.queryByTestId('selected-file-card')).not.toBeInTheDocument();
    expect(screen.getByTestId('upload-dropzone')).toBeInTheDocument();
  });

  it('successfully uploads PDF, shows progress bar, and navigates to processing page', async () => {
    renderUploadPage();

    const validFile = new File(['%PDF-1.4 content'], 'Service_Level_Agreement.pdf', {
      type: 'application/pdf',
    });

    const dropzone = screen.getByTestId('upload-dropzone');
    fireEvent.drop(dropzone, {
      dataTransfer: { files: [validFile] },
    });

    const uploadBtn = screen.getByRole('button', { name: /Upload & Start Analysis/i });
    fireEvent.click(uploadBtn);

    // Progress bar appears
    expect(screen.getByRole('progressbar', { name: /Upload progress/i })).toBeInTheDocument();

    // Wait for upload to complete and navigation
    await waitFor(() => {
      expect(mockedNavigate).toHaveBeenCalledWith(
        expect.stringMatching(/\/documents\/doc-upload-.*\/processing/)
      );
    });

    expect(toast.success).toHaveBeenCalledWith(
      expect.stringContaining('"Service_Level_Agreement.pdf" uploaded successfully')
    );
  });

  it('cancels upload mid-flight via explicit Cancel action (PRD Ch. 22.5)', async () => {
    renderUploadPage();

    const validFile = new File(['%PDF-1.4 content'], 'Large_Contract.pdf', {
      type: 'application/pdf',
    });

    const dropzone = screen.getByTestId('upload-dropzone');
    fireEvent.drop(dropzone, {
      dataTransfer: { files: [validFile] },
    });

    const uploadBtn = screen.getByRole('button', { name: /Upload & Start Analysis/i });
    fireEvent.click(uploadBtn);

    // Cancel button is displayed during active upload
    const cancelBtn = screen.getByRole('button', { name: /Cancel Upload/i });
    expect(cancelBtn).toBeInTheDocument();

    fireEvent.click(cancelBtn);

    // Progress bar dismissed and info toast called
    await waitFor(() => {
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    });

    expect(toast.info).toHaveBeenCalledWith('Upload was canceled.');
    expect(mockedNavigate).not.toHaveBeenCalled();
  });

  it('surfaces distinct, specific error message for password-protected PDFs (PRD Ch. 14, Ch. 58 R-12)', async () => {
    renderUploadPage();

    const encryptedFile = new File(['%PDF-1.4 encrypted'], 'NDA_Password_Protected.pdf', {
      type: 'application/pdf',
    });

    const dropzone = screen.getByTestId('upload-dropzone');
    fireEvent.drop(dropzone, {
      dataTransfer: { files: [encryptedFile] },
    });

    const uploadBtn = screen.getByRole('button', { name: /Upload & Start Analysis/i });
    fireEvent.click(uploadBtn);

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    // Verify distinct error message per PRD Ch. 58 R-12
    expect(
      screen.getByText(
        'Password-protected PDFs are not supported. Please upload an unencrypted document.'
      )
    ).toBeInTheDocument();
    expect(screen.getByText('Password-Protected PDF Detected')).toBeInTheDocument();
  });

  it('allows duplicate uploads of the exact same file without blocking or warning (PRD Ch. 58 R-14)', async () => {
    renderUploadPage();

    const file = new File(['%PDF-1.4 content'], 'Standard_Agreement.pdf', {
      type: 'application/pdf',
    });

    // 1. First selection
    const dropzone = screen.getByTestId('upload-dropzone');
    fireEvent.drop(dropzone, {
      dataTransfer: { files: [file] },
    });

    expect(screen.getByText('Standard_Agreement.pdf')).toBeInTheDocument();

    // Remove
    fireEvent.click(screen.getByRole('button', { name: /Remove file/i }));

    // 2. Second selection of identical file
    const secondDropzone = screen.getByTestId('upload-dropzone');
    fireEvent.drop(secondDropzone, {
      dataTransfer: { files: [file] },
    });

    // Confirms NO duplicate-file warning dialog or blocking occurs
    expect(screen.queryByText(/duplicate/i)).not.toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(screen.getByText('Standard_Agreement.pdf')).toBeInTheDocument();
  });
});
