/**
 * Types for Document Comparison Feature (PRD Ch. 18, 30.5 & Section 8.5)
 */

export type ComparisonStatus = 'pending' | 'processing' | 'complete' | 'failed';

export type ComparisonCategory = 'changed' | 'matched' | 'missing';

export interface ComparisonClauseItem {
  id?: string;
  category: ComparisonCategory;
  base_clause_id?: string | null;
  target_clause_id?: string | null;
  clause_id_a?: string | null;
  clause_id_b?: string | null;
  position_a?: number | null;
  position_b?: number | null;
  text_a?: string | null;
  text_b?: string | null;
  similarity_score?: number | null;
  difference_explanation?: string | null;
  created_at?: string;
}

export interface ComparisonDetail {
  id: string;
  base_document_id: string;
  target_document_id: string;
  status: ComparisonStatus;
  results: ComparisonClauseItem[];
  created_at: string;
  updated_at: string;
  translation_available?: boolean;
  is_low_confidence?: boolean;
  confidence_warning?: string | null;
  matched_count?: number;
  changed_count?: number;
  missing_count?: number;
  total_clauses_a?: number;
  total_clauses_b?: number;
}

export interface ComparisonCreateInput {
  document_a_id: string;
  document_b_id: string;
}

export interface IComparisonService {
  create(documentIdA: string, documentIdB: string): Promise<ComparisonDetail>;
  getResult(comparisonId: string, lang?: string): Promise<ComparisonDetail>;
  list?(): Promise<ComparisonDetail[]>;
}
