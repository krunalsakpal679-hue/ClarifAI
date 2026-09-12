import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ProgressStepper } from '../ProgressStepper';
import { PROCESSING_STAGES } from '../../../constants/processingStages';

describe('ProgressStepper Component (components/ui/ProgressStepper)', () => {
  it('renders all nine stages simultaneously matching exact PRD Ch. 15.1 labels', () => {
    render(<ProgressStepper currentStatus="queued" />);

    expect(screen.getByRole('list', { name: /Document Processing Pipeline Stages/i })).toBeInTheDocument();
    const stageItems = screen.getAllByRole('listitem');
    expect(stageItems.length).toBe(9);

    // Verify all 9 exact labels appear simultaneously
    PROCESSING_STAGES.forEach((stage) => {
      expect(screen.getByText(stage.label)).toBeInTheDocument();
      expect(screen.getByText(stage.description)).toBeInTheDocument();
    });

    // Check exact strings per PRD Ch. 15.1
    expect(screen.getByText('Validating document')).toBeInTheDocument();
    expect(screen.getByText('Extracting text')).toBeInTheDocument();
    expect(screen.getByText('Running OCR (conditional)')).toBeInTheDocument();
    expect(screen.getByText('Segmenting clauses')).toBeInTheDocument();
    expect(screen.getByText('Analyzing risks')).toBeInTheDocument();
    expect(screen.getByText('Simplifying clauses')).toBeInTheDocument();
    expect(screen.getByText('Generating summary')).toBeInTheDocument();
    expect(screen.getByText('Preparing chatbot')).toBeInTheDocument();
    expect(screen.getByText('Complete')).toBeInTheDocument();
  });

  it('correctly reflects active stage with aria-current="step" and animated state', () => {
    render(<ProgressStepper currentStatus="segmenting" />);

    const segmentingItem = screen.getByTestId('stepper-stage-segmenting');
    expect(segmentingItem).toHaveAttribute('aria-current', 'step');
    expect(screen.getByText('(In progress)')).toBeInTheDocument();

    // Past stages should be completed
    const validatingItem = screen.getByTestId('stepper-stage-queued');
    expect(validatingItem).not.toHaveAttribute('aria-current');

    const extractingItem = screen.getByTestId('stepper-stage-extracting');
    expect(extractingItem).not.toHaveAttribute('aria-current');

    // Future stages should not be current or completed
    const analyzingItem = screen.getByTestId('stepper-stage-classifying');
    expect(analyzingItem).not.toHaveAttribute('aria-current');
  });

  it('renders conditional badge and note on the OCR stage (PRD Ch. 15.1 UI Requirement)', () => {
    render(<ProgressStepper currentStatus="queued" />);

    const ocrBadge = screen.getByTestId('ocr-conditional-badge');
    expect(ocrBadge).toBeInTheDocument();
    expect(ocrBadge).toHaveTextContent('Conditional');
    expect(screen.getByText(/Skipped for digital PDFs/i)).toBeInTheDocument();
  });

  it('displays failed stage indicator when pipeline status is failed', () => {
    render(<ProgressStepper currentStatus="failed" failedStageId="classifying" />);

    const classifyingItem = screen.getByTestId('stepper-stage-classifying');
    expect(classifyingItem).toBeInTheDocument();
    expect(screen.getByText('(Failed)')).toBeInTheDocument();
  });

  it('marks all stages as completed when status is complete', () => {
    render(<ProgressStepper currentStatus="complete" />);

    const completedIcons = screen.getAllByText('(Completed)');
    expect(completedIcons.length).toBe(9);
  });
});
