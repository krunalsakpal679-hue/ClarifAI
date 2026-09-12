/**
 * ClarifAI Shared Frontend Type Definitions (PRD v2.3)
 */

export type RiskSeverity = 'HIGH' | 'MODERATE' | 'LOW' | 'SAFE';

export type ProcessingStatus = 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED';

export type ClauseCategory =
  | 'PAYMENT'
  | 'TERMINATION'
  | 'RENEWAL'
  | 'CONFIDENTIALITY'
  | 'LIABILITY'
  | 'IP'
  | 'PRIVACY'
  | 'DISPUTE_RESOLUTION'
  | 'OTHER';

export interface User {
  id: string;
  email: string;
  fullName: string;
  preferredLanguage: 'en' | 'hi';
  createdAt: string;
}

export interface DocumentMetadata {
  id: string;
  title: string;
  fileName: string;
  fileSize: number;
  uploadedAt: string;
  status: ProcessingStatus;
  overallRiskSeverity?: RiskSeverity;
  clauseCount?: number;
}

export * from './auth';
export * from './dashboard';
export * from './documents';
export * from './clause';
export * from '../constants/riskCategories';
export * from '../constants/severityLevels';
