/**
 * ClarifAI Section 8.3 Summary and Clause API Contracts (PRD Ch. 16, 22.7, 30.3, 30.9)
 */
import type { RiskCategory } from '../constants/riskCategories';
import type { SeverityLevel } from '../constants/severityLevels';

export interface DocumentSummary {
  id: string;
  document_id: string;
  purpose_text: string;
  key_risks_text: string;
  key_terms_text: string;
  obligations_text: string;
  created_at: string;
  updated_at?: string;
  translation_available: boolean;
}

export interface RuleFinding {
  rule_id: string;
  rule_name?: string;
  description?: string;
  severity?: string;
  matched_text?: string;
}

export type ClauseClassificationStatus = 'analyzed' | 'failed';

export interface ClauseItem {
  id: string;
  document_id: string;
  position: number;
  original_text: string;
  simplified_text: string;
  severity: SeverityLevel | null;
  category: RiskCategory | null;
  explanation: string;
  status: ClauseClassificationStatus;
  rule_findings: RuleFinding[];
  created_at: string;
  translation_available: boolean;
  simplified_text_hi?: string;
  why_flagged_hi?: string;
}

export interface PaginatedClauseResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: ClauseItem[];
}

/**
 * Filter toolbar option per PRD Ch. 16.3: exactly 'All', 'Risky', 'Safe'
 */
export type ClauseFilterOption = 'ALL' | 'RISKY' | 'SAFE';

export interface ClauseFilterState {
  filter: ClauseFilterOption;
}
