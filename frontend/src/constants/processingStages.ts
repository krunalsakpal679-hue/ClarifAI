/**
 * ClarifAI Nine-Stage Processing Pipeline Specification (PRD Ch. 15.1)
 */
import type { DocumentStatusType } from '../types/documents';

export type ProcessingStageId =
  | 'queued'
  | 'extracting'
  | 'ocr'
  | 'segmenting'
  | 'classifying'
  | 'simplifying'
  | 'summarizing'
  | 'indexing'
  | 'complete';

export interface ProcessingStageDefinition {
  id: ProcessingStageId;
  label: string;
  description: string;
  isConditional?: boolean;
  conditionalNote?: string;
}

/**
 * Exact sequential nine stages per PRD Ch. 15.1
 */
export const PROCESSING_STAGES: ProcessingStageDefinition[] = [
  {
    id: 'queued',
    label: 'Validating document',
    description: 'Verifying PDF structure, integrity, and security checks',
  },
  {
    id: 'extracting',
    label: 'Extracting text',
    description: 'Parsing raw text layers, layouts, and page content',
  },
  {
    id: 'ocr',
    label: 'Running OCR (conditional)',
    description: 'Performing optical character recognition on scanned pages',
    isConditional: true,
    conditionalNote: 'Skipped for digital PDFs',
  },
  {
    id: 'segmenting',
    label: 'Segmenting clauses',
    description: 'Identifying section boundaries, headings, and contractual clauses',
  },
  {
    id: 'classifying',
    label: 'Analyzing risks',
    description: 'Evaluating legal liabilities, risk severities, and flagging critical terms',
  },
  {
    id: 'simplifying',
    label: 'Simplifying clauses',
    description: 'Translating complex legalese into plain English explanations',
  },
  {
    id: 'summarizing',
    label: 'Generating summary',
    description: 'Synthesizing executive summary, key risks, and obligations overview',
  },
  {
    id: 'indexing',
    label: 'Preparing chatbot',
    description: 'Generating semantic vector embeddings for interactive document Q&A',
  },
  {
    id: 'complete',
    label: 'Complete',
    description: 'Contract analysis complete and ready for review',
  },
];

const STAGE_ORDER: ProcessingStageId[] = [
  'queued',
  'extracting',
  'ocr',
  'segmenting',
  'classifying',
  'simplifying',
  'summarizing',
  'indexing',
  'complete',
];

export const getStageIndex = (status: DocumentStatusType): number => {
  if (status === 'failed') return -1;
  return STAGE_ORDER.indexOf(status as ProcessingStageId);
};

export const isStagePassed = (currentStatus: DocumentStatusType, targetStage: ProcessingStageId): boolean => {
  if (currentStatus === 'complete') return true;
  if (currentStatus === 'failed') return false;

  const currentIndex = getStageIndex(currentStatus);
  const targetIndex = STAGE_ORDER.indexOf(targetStage);

  return currentIndex > targetIndex;
};
