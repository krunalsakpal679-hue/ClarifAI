/**
 * Mock Service for Section 8.5 Comparison Endpoints (PRD Ch. 18, 30.5)
 */
import type { ComparisonClauseItem, ComparisonDetail, IComparisonService } from '../../types/comparison';
import { mockDocumentService } from './documents';

const delay = (ms: number) =>
  new Promise((resolve) => setTimeout(resolve, process.env.NODE_ENV === 'test' ? 10 : ms));

export const SAMPLE_COMPARISON_RESULTS: ComparisonClauseItem[] = [
  // 1. Changed Clause: Indemnification (high-risk discrepancy)
  {
    id: 'diff-item-01',
    category: 'changed',
    base_clause_id: 'clause-101',
    target_clause_id: 'clause-201',
    clause_id_a: 'clause-101',
    clause_id_b: 'clause-201',
    position_a: 14,
    position_b: 14,
    text_a:
      'Each party shall defend, indemnify, and hold harmless the other party against third-party claims, subject to a mutual liability ceiling of $500,000.',
    text_b:
      'Customer shall defend, indemnify, and hold harmless Vendor against all third-party claims, without monetary ceiling or reciprocal obligation.',
    similarity_score: 0.72,
    difference_explanation:
      'Mutual indemnification with a $500,000 ceiling was altered to unilateral, uncapped Customer indemnification in the counterparty draft.',
    created_at: '2026-09-12T14:35:00.000Z',
  },
  // 2. Changed Clause: Termination Notice
  {
    id: 'diff-item-02',
    category: 'changed',
    base_clause_id: 'clause-102',
    target_clause_id: 'clause-202',
    clause_id_a: 'clause-102',
    clause_id_b: 'clause-202',
    position_a: 18,
    position_b: 19,
    text_a:
      'Either party may terminate this agreement for convenience upon sixty (60) days prior written notice without penalty.',
    text_b:
      'Vendor may terminate this agreement immediately without cause. Customer may terminate only upon ninety (90) days prior notice with prepaid fees forfeit.',
    similarity_score: 0.65,
    difference_explanation:
      'Bilateral 60-day notice was modified to grant Vendor immediate termination rights while extending Customer notice to 90 days with fee forfeiture.',
    created_at: '2026-09-12T14:35:00.000Z',
  },
  // 3. Changed Clause: Payment & Interest
  {
    id: 'diff-item-03',
    category: 'changed',
    base_clause_id: 'clause-104',
    target_clause_id: 'clause-204',
    clause_id_a: 'clause-104',
    clause_id_b: 'clause-204',
    position_a: 5,
    position_b: 6,
    text_a:
      'Invoices are due within thirty (30) days of receipt. Overdue balances accrue simple interest at 0.5% per month.',
    text_b:
      'Invoices are due within fifteen (15) days of receipt. Overdue balances accrue compounding monthly interest at 1.5% plus collection expenses.',
    similarity_score: 0.78,
    difference_explanation:
      'Net-30 payment term reduced to Net-15, and overdue penalty changed from 0.5% simple interest to 1.5% compounding interest.',
    created_at: '2026-09-12T14:35:00.000Z',
  },
  // 4. Matched Clause: Confidentiality
  {
    id: 'diff-item-04',
    category: 'matched',
    base_clause_id: 'clause-105',
    target_clause_id: 'clause-205',
    clause_id_a: 'clause-105',
    clause_id_b: 'clause-205',
    position_a: 8,
    position_b: 8,
    text_a:
      'Receiving Party agrees to protect Confidential Information using the same degree of care it uses for its own confidential materials, but not less than reasonable care.',
    text_b:
      'Receiving Party agrees to protect Confidential Information using the same degree of care it uses for its own confidential materials, but not less than reasonable care.',
    similarity_score: 1.0,
    difference_explanation:
      'Standard confidentiality protections are verbatim identical across both documents.',
    created_at: '2026-09-12T14:35:00.000Z',
  },
  // 5. Matched Clause: Force Majeure
  {
    id: 'diff-item-05',
    category: 'matched',
    base_clause_id: 'clause-106',
    target_clause_id: 'clause-206',
    clause_id_a: 'clause-106',
    clause_id_b: 'clause-206',
    position_a: 22,
    position_b: 24,
    text_a:
      'Neither party shall be liable for delays or failure in performance resulting from acts beyond reasonable control, including natural disasters and war.',
    text_b:
      'Neither party shall be liable for delays or failure in performance resulting from acts beyond reasonable control, including natural disasters and war.',
    similarity_score: 0.98,
    difference_explanation:
      'Standard mutual force majeure excuse terms match with negligible stylistic variance.',
    created_at: '2026-09-12T14:35:00.000Z',
  },
  // 6. Missing Clause: Data Security & SOC 2 Audit Rights (Deleted in target)
  {
    id: 'diff-item-06',
    category: 'missing',
    base_clause_id: 'clause-107',
    target_clause_id: null,
    clause_id_a: 'clause-107',
    clause_id_b: null,
    position_a: 11,
    position_b: null,
    text_a:
      'Customer retains the right to audit Vendor security logs and SOC 2 Type II compliance reports annually upon fourteen (14) days advance notice.',
    text_b: null,
    similarity_score: 0.0,
    difference_explanation:
      'Annual customer security inspection and SOC 2 compliance audit rights present in the baseline were completely deleted in the revised version.',
    created_at: '2026-09-12T14:35:00.000Z',
  },
  // 7. Missing Clause: Mandatory Arbitration (Added in target)
  {
    id: 'diff-item-07',
    category: 'missing',
    base_clause_id: null,
    target_clause_id: 'clause-208',
    clause_id_a: null,
    clause_id_b: 'clause-208',
    position_a: null,
    position_b: 28,
    text_a: null,
    text_b:
      'All disputes shall be resolved exclusively through binding arbitration administered by AAA in Wilmington, Delaware, waiving all jury trial and class action rights.',
    similarity_score: 0.0,
    difference_explanation:
      'Binding arbitration clause with jury trial and class action waivers was added to the revised contract (not present in baseline).',
    created_at: '2026-09-12T14:35:00.000Z',
  },
];

const INITIAL_MOCK_COMPARISONS: Record<string, ComparisonDetail> = {
  'comp-msa-sla': {
    id: 'comp-msa-sla',
    base_document_id: 'doc-msa-001',
    target_document_id: 'doc-sla-002',
    status: 'complete',
    results: SAMPLE_COMPARISON_RESULTS,
    created_at: '2026-09-12T14:35:00.000Z',
    updated_at: '2026-09-12T14:36:00.000Z',
    translation_available: true,
    is_low_confidence: false,
    confidence_warning: null,
    matched_count: 2,
    changed_count: 3,
    missing_count: 2,
    total_clauses_a: 6,
    total_clauses_b: 6,
  },
  'comp-low-confidence': {
    id: 'comp-low-confidence',
    base_document_id: 'doc-msa-001',
    target_document_id: 'doc-lease-005',
    status: 'complete',
    results: SAMPLE_COMPARISON_RESULTS.slice(0, 4),
    created_at: '2026-09-12T15:00:00.000Z',
    updated_at: '2026-09-12T15:01:00.000Z',
    translation_available: true,
    is_low_confidence: true,
    confidence_warning:
      'Warning: The two selected documents exhibit significantly different structure, clause count, and length (Master Services Agreement vs Short Lease). Alignment confidence is reduced (PRD Ch. 18.3 clause length ratio > 2.0). Semantic match results may be inaccurate.',
    matched_count: 1,
    changed_count: 2,
    missing_count: 1,
    total_clauses_a: 14,
    total_clauses_b: 4,
  },
};

let mockComparisons: Record<string, ComparisonDetail> = { ...INITIAL_MOCK_COMPARISONS };

export const mockComparisonService: IComparisonService = {
  create: async (documentIdA: string, documentIdB: string): Promise<ComparisonDetail> => {
    await delay(70);

    if (!documentIdA || !documentIdB) {
      throw new Error('Both base (Document A) and target (Document B) documents are required.');
    }

    // Client-side & backend validation: disallow comparing same document
    if (documentIdA === documentIdB) {
      throw new Error('Cannot compare a document against itself. (400)');
    }

    // Validate both documents exist and are complete
    try {
      const docA = await mockDocumentService.getById(documentIdA);
      const docB = await mockDocumentService.getById(documentIdB);

      if (docA.status !== 'complete' || docB.status !== 'complete') {
        throw new Error(
          'DOCUMENT_NOT_READY: Both documents must complete analysis before comparison can be initiated. (422)'
        );
      }
    } catch (err) {
      if (err instanceof Error && err.message.includes('DOCUMENT_NOT_READY')) {
        throw err;
      }
      if (err instanceof Error && err.message.includes('404')) {
        throw err;
      }
    }

    // PRD Ch. 18.3 Low confidence heuristic:
    // Different document types (e.g. MSA vs Lease, or explicit low-conf IDs)
    const isDivergent =
      (documentIdA.includes('lease') && !documentIdB.includes('lease')) ||
      (!documentIdA.includes('lease') && documentIdB.includes('lease')) ||
      documentIdA === 'doc-low-conf' ||
      documentIdB === 'doc-low-conf';

    const compId = `comp-${documentIdA}-${documentIdB}`;

    const newComparison: ComparisonDetail = {
      id: compId,
      base_document_id: documentIdA,
      target_document_id: documentIdB,
      status: 'complete',
      results: isDivergent ? SAMPLE_COMPARISON_RESULTS.slice(0, 4) : [...SAMPLE_COMPARISON_RESULTS],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      translation_available: true,
      is_low_confidence: isDivergent,
      confidence_warning: isDivergent
        ? 'Warning: The two selected documents exhibit significantly different structure, clause count, and length. Alignment confidence is reduced (PRD Ch. 18.3 clause length ratio > 2.0). Semantic match results may be inaccurate.'
        : null,
      matched_count: isDivergent ? 1 : 2,
      changed_count: isDivergent ? 2 : 3,
      missing_count: isDivergent ? 1 : 2,
      total_clauses_a: isDivergent ? 14 : 6,
      total_clauses_b: isDivergent ? 4 : 6,
    };

    mockComparisons[compId] = newComparison;
    return { ...newComparison };
  },

  getResult: async (comparisonId: string, lang = 'en'): Promise<ComparisonDetail> => {
    await delay(60);

    // Direct lookup or synthesized lookup for valid doc pairs
    let found = mockComparisons[comparisonId];

    if (!found && comparisonId.startsWith('comp-doc-')) {
      const parts = comparisonId.replace(/^comp-/, '').split('-doc-');
      if (parts.length === 2) {
        const idA = parts[0];
        const idB = `doc-${parts[1]}`;
        const isDivergent = comparisonId.includes('lease') || comparisonId.includes('low-conf');
        found = {
          id: comparisonId,
          base_document_id: idA,
          target_document_id: idB,
          status: 'complete',
          results: [...SAMPLE_COMPARISON_RESULTS],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          translation_available: true,
          is_low_confidence: isDivergent,
          confidence_warning: isDivergent
            ? 'Warning: The two selected documents exhibit significantly different structure, clause count, and length. Alignment confidence is reduced (PRD Ch. 18.3 clause length ratio > 2.0). Semantic match results may be inaccurate.'
            : null,
          matched_count: 2,
          changed_count: 3,
          missing_count: 2,
        };
        mockComparisons[comparisonId] = found;
      }
    }

    if (!found) {
      throw new Error(`Comparison not found with ID ${comparisonId} (404)`);
    }

    // Multilingual Hindi translation support
    if (lang === 'hi') {
      const translatedResults = found.results.map((item) => ({
        ...item,
        difference_explanation: item.difference_explanation
          ? `[हिंदी अनुवाद] ${item.difference_explanation}`
          : null,
      }));
      return {
        ...found,
        results: translatedResults,
      };
    }

    return { ...found };
  },

  list: async (): Promise<ComparisonDetail[]> => {
    await delay(50);
    return Object.values(mockComparisons);
  },
};

export const __resetMockComparisons = (): void => {
  mockComparisons = { ...INITIAL_MOCK_COMPARISONS };
};

export const __setMockComparison = (comp: ComparisonDetail): void => {
  mockComparisons[comp.id] = comp;
};
