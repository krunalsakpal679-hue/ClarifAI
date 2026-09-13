import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ReportDownloadButton } from '../ReportDownloadButton';
import { reportService } from '../../../services/api';
import { mockReportService } from '../../../services/mocks/reports';
import i18n from '../../../app/i18n';

describe('ReportDownloadButton Component (PRD Ch. 21 & Section 8.6)', () => {
  let createObjectURLSpy: ReturnType<typeof vi.fn>;
  let revokeObjectURLSpy: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.clearAllMocks();
    mockReportService.__resetMockReports();
    i18n.changeLanguage('en');

    createObjectURLSpy = vi.fn().mockReturnValue('blob:http://localhost/mock-blob-uuid');
    revokeObjectURLSpy = vi.fn();
    window.URL.createObjectURL = createObjectURLSpy;
    window.URL.revokeObjectURL = revokeObjectURLSpy;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders initial idle state with Export Report label', () => {
    render(
      <ReportDownloadButton
        reportType="document"
        targetId="doc-sample-123"
        lang="en"
      />
    );

    const button = screen.getByRole('button', { name: /export report/i });
    expect(button).toBeInTheDocument();
    expect(screen.getByTestId('report-state-idle')).toBeInTheDocument();
  });

  it('progresses through two-step flow: idle -> generating -> ready -> downloaded', async () => {
    const onDownloadComplete = vi.fn();

    render(
      <ReportDownloadButton
        reportType="document"
        targetId="doc-sample-123"
        lang="en"
        onDownloadComplete={onDownloadComplete}
      />
    );

    // 1. Click generate
    const generateBtn = screen.getByRole('button', { name: /export report/i });
    fireEvent.click(generateBtn);

    // 2. Expect generating state
    expect(screen.getByTestId('report-state-generating')).toBeInTheDocument();
    expect(screen.getByText(/generating report/i)).toBeInTheDocument();

    // 3. Expect ready (preview) state
    await waitFor(() => {
      expect(screen.getByTestId('report-state-ready')).toBeInTheDocument();
    });
    expect(screen.getByText(/report ready \(pdf\)/i)).toBeInTheDocument();
    const downloadBtn = screen.getByRole('button', { name: /download pdf/i });
    expect(downloadBtn).toBeInTheDocument();

    // 4. Click download
    fireEvent.click(downloadBtn);

    // 5. Expect downloaded state
    await waitFor(() => {
      expect(screen.getByTestId('report-state-downloaded')).toBeInTheDocument();
    });
    expect(screen.getByText(/downloaded/i)).toBeInTheDocument();
    expect(createObjectURLSpy).toHaveBeenCalled();
    expect(onDownloadComplete).toHaveBeenCalled();
  });

  it('handles comparison reports using generateComparisonReport endpoint', async () => {
    const spyComp = vi.spyOn(reportService, 'generateComparisonReport');

    render(
      <ReportDownloadButton
        reportType="comparison"
        targetId="comp-docA-docB"
        lang="hi"
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /export report/i }));

    await waitFor(() => {
      expect(screen.getByTestId('report-state-ready')).toBeInTheDocument();
    });

    expect(spyComp).toHaveBeenCalledWith('comp-docA-docB', 'hi');
  });

  it('transitions to failed state when generation fails and supports retry', async () => {
    mockReportService.__simulateNextFailure(true);
    const onError = vi.fn();

    render(
      <ReportDownloadButton
        reportType="document"
        targetId="doc-sample-123"
        lang="en"
        onError={onError}
      />
    );

    // Trigger failure
    fireEvent.click(screen.getByRole('button', { name: /export report/i }));

    await waitFor(() => {
      expect(screen.getByTestId('report-state-failed')).toBeInTheDocument();
    });

    expect(screen.getByText(/retry report/i)).toBeInTheDocument();
    expect(onError).toHaveBeenCalled();

    // Clicking Retry attempts generation again (simulateFailureOnce was consumed)
    const retryBtn = screen.getByRole('button', { name: /retry report/i });
    fireEvent.click(retryBtn);

    // Should transition to generating then ready
    await waitFor(() => {
      expect(screen.getByTestId('report-state-ready')).toBeInTheDocument();
    });
  });

  it('allows re-downloading in downloaded state', async () => {
    render(
      <ReportDownloadButton
        reportType="document"
        targetId="doc-sample-123"
        lang="en"
      />
    );

    // Step 1: generate
    fireEvent.click(screen.getByRole('button', { name: /export report/i }));
    await waitFor(() => {
      expect(screen.getByTestId('report-state-ready')).toBeInTheDocument();
    });

    // Step 2: download
    fireEvent.click(screen.getByRole('button', { name: /download pdf/i }));
    await waitFor(() => {
      expect(screen.getByTestId('report-state-downloaded')).toBeInTheDocument();
    });

    // Step 3: click download again
    const reDownloadBtn = screen.getByRole('button', { name: /download again/i });
    fireEvent.click(reDownloadBtn);

    await waitFor(() => {
      expect(createObjectURLSpy).toHaveBeenCalledTimes(2);
    });
  });
});
