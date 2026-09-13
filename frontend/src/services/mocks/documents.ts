// MOCK DATA
/**
 * Mock Service for Section 8.2 Document List (PRD Section 11 Mock Strategy)
 */
import type {
  ClauseItem,
  DocumentItem,
  DocumentListParams,
  DocumentStatusType,
  DocumentSummary,
  DocumentUploadResponse,
  IDocumentService,
  PaginatedClauseResponse,
  PaginatedDocumentListResponse,
} from '../../types';
import { MockApiError } from '../../utils/errors';

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));


export const INITIAL_MOCK_DOCUMENTS: DocumentItem[] = [
  {
    id: 'doc-msa-001',
    original_filename: 'Master_Services_Agreement_Enterprise_2026.pdf',
    file_reference: 'uploads/documents/doc-msa-001_Master_Services_Agreement_Enterprise_2026.pdf',
    document_type: 'Master Services Agreement',
    status: 'complete',
    failure_reason: null,
    overall_risk: 'high',
    uploaded_at: '2026-09-12T14:30:00.000Z',
    updated_at: '2026-09-12T14:35:00.000Z',
  },
  {
    id: 'doc-sla-002',
    original_filename: 'Vendor_Service_Level_Agreement_Q3.pdf',
    file_reference: 'uploads/documents/doc-sla-002_Vendor_Service_Level_Agreement_Q3.pdf',
    document_type: 'Service Level Agreement',
    status: 'complete',
    failure_reason: null,
    overall_risk: 'moderate',
    uploaded_at: '2026-09-11T16:15:00.000Z',
    updated_at: '2026-09-11T16:18:00.000Z',
  },
  {
    id: 'doc-nda-003',
    original_filename: 'Mutual_Confidentiality_NDA_AcmeCorp.pdf',
    file_reference: 'uploads/documents/doc-nda-003_Mutual_Confidentiality_NDA_AcmeCorp.pdf',
    document_type: 'Non-Disclosure Agreement',
    status: 'complete',
    failure_reason: null,
    overall_risk: 'low',
    uploaded_at: '2026-09-10T10:00:00.000Z',
    updated_at: '2026-09-10T10:02:00.000Z',
  },
  {
    id: 'doc-ip-004',
    original_filename: 'Standard_Employee_Proprietary_Info_IP.pdf',
    file_reference: 'uploads/documents/doc-ip-004_Standard_Employee_Proprietary_Info_IP.pdf',
    document_type: 'IP Agreement',
    status: 'complete',
    failure_reason: null,
    overall_risk: 'safe',
    uploaded_at: '2026-09-09T09:20:00.000Z',
    updated_at: '2026-09-09T09:22:00.000Z',
  },
  {
    id: 'doc-lease-005',
    original_filename: 'Commercial_Office_Lease_Draft_v2.pdf',
    file_reference: 'uploads/documents/doc-lease-005_Commercial_Office_Lease_Draft_v2.pdf',
    document_type: 'Lease Agreement',
    status: 'extracting',
    failure_reason: null,
    overall_risk: null,
    uploaded_at: '2026-09-12T17:45:00.000Z',
    updated_at: '2026-09-12T17:46:00.000Z',
  },
  {
    id: 'doc-scan-006',
    original_filename: 'Corrupted_Scan_Export_0912.pdf',
    file_reference: 'uploads/documents/doc-scan-006_Corrupted_Scan_Export_0912.pdf',
    document_type: null,
    status: 'failed',
    failure_reason: 'Corrupted PDF file header or unsupported encryption format.',
    overall_risk: null,
    uploaded_at: '2026-09-08T11:00:00.000Z',
    updated_at: '2026-09-08T11:01:00.000Z',
  },
  {
    id: 'doc-safe-001',
    original_filename: 'Standard_Mutual_Safe_Agreement.pdf',
    file_reference: 'uploads/documents/doc-safe-001_Standard_Mutual_Safe_Agreement.pdf',
    document_type: 'Standard Mutual Agreement',
    status: 'complete',
    failure_reason: null,
    overall_risk: 'safe',
    uploaded_at: '2026-09-12T10:00:00.000Z',
    updated_at: '2026-09-12T10:05:00.000Z',
  },
  {
    id: 'doc-sample-123',
    original_filename: 'Sample_Services_Agreement_123.pdf',
    file_reference: 'uploads/documents/doc-sample-123_Sample.pdf',
    document_type: 'Master Services Agreement',
    status: 'complete',
    failure_reason: null,
    overall_risk: 'high',
    uploaded_at: '2026-09-12T14:30:00.000Z',
    updated_at: '2026-09-12T14:35:00.000Z',
  },
];

let mockDocumentsDb: DocumentItem[] = INITIAL_MOCK_DOCUMENTS.map((d) => ({ ...d }));
let autoProgressEnabled = false;

export const mockDocumentService: IDocumentService = {
  list: async (params?: DocumentListParams): Promise<PaginatedDocumentListResponse> => {
    // Simulate network delay per PRD Section 11
    await delay(150);

    const page = params?.page || 1;
    const pageSize = params?.page_size || 20;

    const startIndex = (page - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    const paginatedResults = mockDocumentsDb.slice(startIndex, endIndex);

    return {
      count: mockDocumentsDb.length,
      next: endIndex < mockDocumentsDb.length ? `/api/documents/?page=${page + 1}` : null,
      previous: page > 1 ? `/api/documents/?page=${page - 1}` : null,
      results: paginatedResults,
    };
  },

  delete: async (id: string): Promise<void> => {
    await delay(150);
    const index = mockDocumentsDb.findIndex((doc) => doc.id === id);
    if (index === -1) {
      throw new MockApiError('Document not found or access denied (404)', 'DOCUMENT_NOT_FOUND', 404);
    }
    mockDocumentsDb.splice(index, 1);
  },

  upload: async (
    file: File,
    onProgress?: (progressPercentage: number) => void,
    signal?: AbortSignal
  ): Promise<DocumentUploadResponse> => {
    if (signal?.aborted) {
      throw new DOMException('Upload canceled by user', 'AbortError');
    }

    const lowerName = file.name.toLowerCase();

    // 1. Password-protected PDF check (Distinct message per PRD Ch. 14, Ch. 58 R-12)
    if (lowerName.includes('password') || lowerName.includes('encrypted')) {
      await delay(100);
      throw new MockApiError('Password-protected PDFs are not supported. Please upload an unencrypted document.', 'ENCRYPTED_PDF_NOT_SUPPORTED', 422);
    }

    // 2. Corrupted PDF check
    if (lowerName.includes('corrupted')) {
      await delay(100);
      throw new MockApiError('PDF file is corrupted or unparseable.', 'CORRUPTED_PDF', 422);
    }

    // 3. Empty PDF check
    if (file.size === 0 || lowerName.includes('empty')) {
      await delay(100);
      throw new MockApiError('PDF file is corrupted or empty.', 'EMPTY_PDF', 422);
    }

    // Step-by-step progress simulation (e.g. 25% -> 50% -> 75% -> 100%)
    const steps = [25, 50, 75, 100];
    for (const step of steps) {
      if (signal?.aborted) {
        throw new DOMException('Upload canceled by user', 'AbortError');
      }
      await delay(80);
      if (signal?.aborted) {
        throw new DOMException('Upload canceled by user', 'AbortError');
      }
      onProgress?.(step);
    }

    const newDocId = `doc-upload-${Date.now().toString(36)}-${Math.random().toString(36).substring(2, 6)}`;
    const newDoc: DocumentItem = {
      id: newDocId,
      original_filename: file.name,
      file_reference: `uploads/documents/${newDocId}_${file.name}`,
      document_type: 'Legal Document',
      status: 'queued',
      failure_reason: null,
      overall_risk: null,
      uploaded_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    mockDocumentsDb.unshift(newDoc);

    return {
      id: newDoc.id,
      original_filename: newDoc.original_filename,
      file_reference: newDoc.file_reference,
      status: newDoc.status,
      uploaded_at: newDoc.uploaded_at,
    };
  },

  getById: async (id: string): Promise<DocumentItem> => {
    await delay(50);
    const doc = mockDocumentsDb.find((d) => d.id === id);
    if (!doc) {
      if (id.startsWith('doc-')) {
        const fallbackDoc: DocumentItem = {
          id,
          original_filename: `Document_${id}.pdf`,
          file_reference: `uploads/documents/${id}.pdf`,
          document_type: 'Legal Document',
          status: 'extracting',
          failure_reason: null,
          overall_risk: null,
          uploaded_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };
        mockDocumentsDb.push(fallbackDoc);
        return { ...fallbackDoc };
      }
      throw new MockApiError(`Document not found with ID ${id} (404)`, 'DOCUMENT_NOT_FOUND', 404);
    }

    // Auto progression simulation for in-progress documents
    if (autoProgressEnabled && doc.status !== 'complete' && doc.status !== 'failed') {
      const stageSequence: DocumentStatusType[] = [
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
      const currentIndex = stageSequence.indexOf(doc.status);
      if (currentIndex !== -1 && currentIndex < stageSequence.length - 1) {
        doc.status = stageSequence[currentIndex + 1];
        doc.updated_at = new Date().toISOString();
      }
    }

    return { ...doc };
  },

  getSummary: async (id: string, lang = 'en'): Promise<DocumentSummary> => {
    await delay(100);

    const doc = mockDocumentsDb.find((d) => d.id === id);
    if (!doc && !id.startsWith('doc-')) {
      throw new MockApiError(`Document not found with ID ${id} (404)`, 'DOCUMENT_NOT_FOUND', 404);
    }

    if (doc && doc.status !== 'complete') {
      throw new MockApiError(`Document analysis not complete (422)`, 'DOCUMENT_NOT_READY', 422);
    }

    const summaryKey = id === 'doc-safe-001' ? 'doc-safe-001' : 'doc-msa-001';
    const summaryData = MOCK_SUMMARIES[summaryKey] || MOCK_SUMMARIES['doc-msa-001'];

    if (lang === 'hi' && summaryData.hi) {
      return {
        ...summaryData.hi,
        id: `sum-${id}-hi`,
        document_id: id,
      };
    }

    return {
      ...summaryData.en,
      id: `sum-${id}`,
      document_id: id,
    };
  },

  getClauses: async (
    id: string,
    lang = 'en',
    severity?: string
  ): Promise<PaginatedClauseResponse> => {
    await delay(120);

    const doc = mockDocumentsDb.find((d) => d.id === id);
    if (!doc && !id.startsWith('doc-')) {
      throw new MockApiError(`Document not found with ID ${id} (404)`, 'DOCUMENT_NOT_FOUND', 404);
    }

    if (doc && doc.status !== 'complete') {
      throw new MockApiError(`Document analysis not complete (422)`, 'DOCUMENT_NOT_READY', 422);
    }

    const clausesKey = id === 'doc-safe-001' ? 'doc-safe-001' : 'doc-msa-001';
    let clauses = (MOCK_CLAUSES_BY_DOC[clausesKey] || MOCK_CLAUSES_BY_DOC['doc-msa-001']).map(
      (c) => ({
        ...c,
        document_id: id,
      })
    );

    // Multilingual Hindi mapping
    if (lang === 'hi') {
      clauses = clauses.map((c) => ({
        ...c,
        simplified_text: HINDI_SIMPLIFICATIONS[c.id] || c.simplified_text,
        explanation: HINDI_EXPLANATIONS[c.id] || c.explanation,
        translation_available: Boolean(HINDI_SIMPLIFICATIONS[c.id]),
      }));
    }

    // Apply optional severity filter
    if (severity) {
      const filterLower = severity.toLowerCase();
      if (filterLower === 'risky') {
        clauses = clauses.filter(
          (c) => c.severity === 'High' || c.severity === 'Moderate' || c.severity === 'Low'
        );
      } else if (filterLower === 'safe') {
        clauses = clauses.filter((c) => c.severity === 'Safe');
      } else {
        clauses = clauses.filter((c) => c.severity?.toLowerCase() === filterLower);
      }
    }

    return {
      count: clauses.length,
      next: null,
      previous: null,
      results: clauses,
    };
  },

  getClauseDetail: async (
    documentId: string,
    clauseId: string,
    lang = 'en'
  ): Promise<ClauseItem> => {
    await delay(80);

    const doc = mockDocumentsDb.find((d) => d.id === documentId);
    if (!doc && !documentId.startsWith('doc-')) {
      throw new MockApiError(`Document not found with ID ${documentId} (404)`, 'DOCUMENT_NOT_FOUND', 404);
    }

    if (doc && doc.status !== 'complete') {
      throw new MockApiError(`Document analysis not complete (422)`, 'DOCUMENT_NOT_READY', 422);
    }

    const clausesKey = documentId === 'doc-safe-001' ? 'doc-safe-001' : 'doc-msa-001';
    const clauses = MOCK_CLAUSES_BY_DOC[clausesKey] || MOCK_CLAUSES_BY_DOC['doc-msa-001'];
    const clause = clauses.find((c) => c.id === clauseId);

    if (!clause) {
      throw new MockApiError(`Clause not found with ID ${clauseId} (404)`, 'CLAUSE_NOT_FOUND', 404);
    }

    const localizedClause: ClauseItem = {
      ...clause,
      document_id: documentId,
    };

    if (lang === 'hi') {
      localizedClause.simplified_text = HINDI_SIMPLIFICATIONS[clause.id] || clause.simplified_text;
      localizedClause.explanation = HINDI_EXPLANATIONS[clause.id] || clause.explanation;
      localizedClause.translation_available = Boolean(HINDI_SIMPLIFICATIONS[clause.id]);
    }

    return localizedClause;
  },
};

/**
 * Mock Summaries Data (PRD Ch. 16, 30.3)
 */
const MOCK_SUMMARIES: Record<string, { en: DocumentSummary; hi?: DocumentSummary }> = {
  'doc-msa-001': {
    en: {
      id: 'sum-msa-001',
      document_id: 'doc-msa-001',
      purpose_text:
        'This Master Services Agreement establishes the legal and commercial terms under which Enterprise Cloud Services are provisioned to the customer across global enterprise facilities.',
      key_risks_text:
        'The contract imposes uncapped unilateral customer indemnification for third-party claims, strict vendor limitation of liability to 3 months of fees, and immediate termination for vendor convenience without transition covenants.',
      key_terms_text:
        'Initial term is 36 months with automatic annual renewal unless 60 days advance written notice is provided. Payment is Net 30 with 1.5% compounding late fee interest.',
      obligations_text:
        'Customer must maintain SOC2-compliant access protocols, provide unhindered remote audit access, and preserve strict trade secret confidentiality during and after the agreement.',
      created_at: '2026-09-12T14:35:00.000Z',
      updated_at: '2026-09-12T14:35:00.000Z',
      translation_available: true,
    },
    hi: {
      id: 'sum-msa-001-hi',
      document_id: 'doc-msa-001',
      purpose_text:
        'यह मास्टर सेवा समझौता उन कानूनी और व्यावसायिक शर्तों को स्थापित करता है जिनके तहत ग्राहक को क्लाउड सेवाएं प्रदान की जाती हैं।',
      key_risks_text:
        'अनुबंध तीसरे पक्ष के दावों के लिए ग्राहक पर असीमित क्षतिपूर्ति लागू करता है और विक्रेता के दायित्व को पिछले 3 महीनों के शुल्क तक सीमित करता है।',
      key_terms_text:
        'प्रारंभिक अवधि 36 महीने की है जिसमें 60 दिनों की अग्रिम लिखित सूचना न देने पर स्वतः वार्षिक नवीनीकरण शामिल है। भुगतान की अवधि 30 दिन है।',
      obligations_text:
        'ग्राहक को डेटा सुरक्षा नियमों का पालन करना होगा और समझौते के दौरान तथा बाद में गोपनीयता बनाए रखनी होगी।',
      created_at: '2026-09-12T14:35:00.000Z',
      updated_at: '2026-09-12T14:35:00.000Z',
      translation_available: true,
    },
  },
  'doc-safe-001': {
    en: {
      id: 'sum-safe-001',
      document_id: 'doc-safe-001',
      purpose_text:
        'This Standard Mutual Collaboration Agreement establishes balanced, mutual terms between two equal commercial partners for preliminary technology research.',
      key_risks_text:
        'No critical or disproportionate legal hazards identified. All liability, indemnity, and termination terms are reciprocal with equal mutual protections.',
      key_terms_text:
        'Term is 12 months with mutual non-renewal by standard written notice. Each party retains independent ownership of preexisting intellectual property.',
      obligations_text:
        'Both parties agree to standard mutual nondisclosure of shared technical materials and ordinary professional care in research execution.',
      created_at: '2026-09-12T10:05:00.000Z',
      updated_at: '2026-09-12T10:05:00.000Z',
      translation_available: true,
    },
  },
};

/**
 * Mock Clauses Data (PRD Ch. 16, 22.7, 30.3, 30.9)
 * Represents all 4 severities, all 8 corrected categories, and a classification failure.
 */
const MOCK_CLAUSES_BY_DOC: Record<string, ClauseItem[]> = {
  'doc-msa-001': [
    {
      id: 'clause-101',
      document_id: 'doc-msa-001',
      position: 1,
      original_text:
        'Customer shall defend, indemnify, and hold harmless Vendor, its affiliates, officers, directors, employees, and agents from and against any and all claims, demands, liabilities, damages, losses, costs, and expenses (including attorney fees) arising from Customer data or use of Services without limitation.',
      simplified_text:
        'You must pay all legal costs, damages, and attorney fees if the vendor is sued because of your data or how you used their service. There is no maximum dollar limit on your liability.',
      severity: 'High',
      category: 'Liability',
      explanation:
        'Uncapped unilateral indemnification disproportionately transfers third-party risk to you without any mutual indemnity protection from the vendor.',
      status: 'analyzed',
      rule_findings: [
        {
          rule_id: 'R-101',
          rule_name: 'Uncapped Customer Indemnity',
          severity: 'High',
          matched_text: 'without limitation',
          description: 'Indemnity clause lacks monetary ceiling or reciprocal vendor coverage.',
        },
      ],
      created_at: '2026-09-12T14:35:00.000Z',
      translation_available: true,
    },
    {
      id: 'clause-102',
      document_id: 'doc-msa-001',
      position: 2,
      original_text:
        'Vendor reserves the right to suspend or terminate this Agreement and all associated service provisioning immediately upon written notice for any reason or no reason, without obligation to refund prepaid fees or assist in transition migrations.',
      simplified_text:
        'The vendor can cancel the service and terminate this contract immediately at any time without giving a reason, will not refund your prepaid money, and will not help you transfer your data.',
      severity: 'High',
      category: 'Termination',
      explanation:
        'Immediate unilateral termination for convenience without refund or data transition creates critical operational dependency and business continuity risk.',
      status: 'analyzed',
      rule_findings: [
        {
          rule_id: 'R-102',
          rule_name: 'Unilateral Immediate Termination',
          severity: 'High',
          matched_text: 'immediately upon written notice for any reason or no reason',
          description: 'Immediate termination without cause or transition support.',
        },
      ],
      created_at: '2026-09-12T14:35:00.000Z',
      translation_available: true,
    },
    {
      id: 'clause-103',
      document_id: 'doc-msa-001',
      position: 3,
      original_text:
        'This Agreement shall automatically renew for successive consecutive twelve (12) month periods unless either party delivers written opt-out notification at least sixty (60) days prior to the expiration of the then-current term. Vendor may escalate subscription pricing by up to fifteen percent (15%) upon each renewal.',
      simplified_text:
        'The contract automatically renews every year unless you cancel in writing at least 60 days before the renewal date. The vendor can also raise prices by up to 15% each year.',
      severity: 'Moderate',
      category: 'Renewal',
      explanation:
        'Automatic rollover with a strict 60-day notification deadline and 15% annual compounding price increases can lock your organization into escalating recurring costs.',
      status: 'analyzed',
      rule_findings: [
        {
          rule_id: 'R-103',
          rule_name: 'Auto-Renewal Price Escalation',
          severity: 'Moderate',
          matched_text: 'automatically renew... escalate subscription pricing by up to fifteen percent',
          description: 'Automatic renewal combined with above-market price escalation allowance.',
        },
      ],
      created_at: '2026-09-12T14:35:00.000Z',
      translation_available: true,
    },
    {
      id: 'clause-104',
      document_id: 'doc-msa-001',
      position: 4,
      original_text:
        'Invoices are due and payable within fifteen (15) days of receipt. Unpaid amounts shall accrue interest at the maximum rate permitted by law or 1.5% per month, compounded monthly, plus all collection costs and reasonable legal fees.',
      simplified_text:
        'You must pay invoices within 15 days. Overdue payments accrue 1.5% monthly compound interest plus collection agency costs and attorney fees.',
      severity: 'Moderate',
      category: 'Payment',
      explanation:
        'A 15-day Net payment window is unusually compressed for enterprise procurement workflows, and monthly compounding penalties add financial exposure.',
      status: 'analyzed',
      rule_findings: [
        {
          rule_id: 'R-104',
          rule_name: 'Aggressive Payment Terms',
          severity: 'Moderate',
          matched_text: 'fifteen (15) days... 1.5% per month, compounded monthly',
          description: 'Short payment window with high compounding interest rate.',
        },
      ],
      created_at: '2026-09-12T14:35:00.000Z',
      translation_available: true,
    },
    {
      id: 'clause-105',
      document_id: 'doc-msa-001',
      position: 5,
      original_text:
        'Each party shall hold Confidential Information in strict confidence for a period of three (3) years following disclosure; provided that Trade Secrets shall be preserved indefinitely. Disclosures mandated by court order are permitted with prior written notice.',
      simplified_text:
        'Both parties must keep confidential information secret for 3 years, while trade secrets must stay protected forever. Court-ordered disclosures are permitted with advance notice.',
      severity: 'Low',
      category: 'Confidentiality',
      explanation:
        'A 3-year term is standard commercial practice, though enterprise proprietary technology workflows typically prefer 5-year confidentiality periods.',
      status: 'analyzed',
      rule_findings: [
        {
          rule_id: 'R-105',
          rule_name: 'Short Confidentiality Window',
          severity: 'Low',
          matched_text: 'period of three (3) years',
          description: '3-year expiration window on general confidential disclosures.',
        },
      ],
      created_at: '2026-09-12T14:35:00.000Z',
      translation_available: true,
    },
    {
      id: 'clause-106',
      document_id: 'doc-msa-001',
      position: 6,
      original_text:
        'Vendor retains all right, title, and interest in and to the Platform and underlying algorithms. Customer grants Vendor a perpetual, irrevocable, royalty-free license to use anonymized operational usage telemetry to enhance algorithmic models.',
      simplified_text:
        'The vendor owns the platform technology. You grant the vendor permission to use your anonymized system usage data to train and improve their software models.',
      severity: 'Low',
      category: 'Intellectual Property',
      explanation:
        'Telemetry usage is anonymized, but perpetual irrevocable data usage rights should be verified against your internal data governance protocols.',
      status: 'analyzed',
      rule_findings: [
        {
          rule_id: 'R-106',
          rule_name: 'Perpetual Telemetry License',
          severity: 'Low',
          matched_text: 'perpetual, irrevocable, royalty-free license',
          description: 'Irrevocable license for training and analytics telemetry.',
        },
      ],
      created_at: '2026-09-12T14:35:00.000Z',
      translation_available: true,
    },
    {
      id: 'clause-107',
      document_id: 'doc-msa-001',
      position: 7,
      original_text:
        'Both parties agree to comply with all applicable data privacy regulations, including GDPR and CCPA, implementing appropriate technical and organizational safeguards against unauthorized processing or data loss.',
      simplified_text:
        'Both parties agree to follow all data privacy laws and maintain strong technical security measures to protect personal data.',
      severity: 'Safe',
      category: 'Privacy',
      explanation:
        'Standard mutual privacy clause aligning with global regulatory data protection baselines.',
      status: 'analyzed',
      rule_findings: [],
      created_at: '2026-09-12T14:35:00.000Z',
      translation_available: true,
    },
    {
      id: 'clause-108',
      document_id: 'doc-msa-001',
      position: 8,
      original_text:
        'This Agreement shall be governed by and construed in accordance with the laws of the State of Delaware, without regard to conflicts of law principles. Any dispute shall be resolved through binding arbitration administered by the American Arbitration Association.',
      simplified_text:
        'The contract is governed by Delaware law, and any legal disputes will be resolved through neutral binding arbitration.',
      severity: 'Safe',
      category: 'Dispute Resolution',
      explanation:
        'Standard neutral commercial dispute forum with mutual binding arbitration rules.',
      status: 'analyzed',
      rule_findings: [],
      created_at: '2026-09-12T14:35:00.000Z',
      translation_available: true,
    },
    {
      id: 'clause-109',
      document_id: 'doc-msa-001',
      position: 9,
      original_text:
        'Where cross-border tariff modifications under Annex IV intersect with Section 7.2 force majeure contingencies, apportionment shall be dynamically negotiated under UNCITRAL Article 79 rules.',
      simplified_text: '',
      severity: null,
      category: null,
      explanation:
        'The automated classification engine could not determine risk severity for this clause due to conflicting international cross-references. Independent legal counsel review is advised.',
      status: 'failed',
      rule_findings: [],
      created_at: '2026-09-12T14:35:00.000Z',
      translation_available: false,
    },
  ],
  'doc-safe-001': [
    {
      id: 'clause-safe-101',
      document_id: 'doc-safe-001',
      position: 1,
      original_text:
        'Each party agrees to hold the other party confidential materials in confidence and use identical degree of care as exercised for its own proprietary records.',
      simplified_text:
        'Both parties will protect each other confidential information with the same care they use for their own confidential files.',
      severity: 'Safe',
      category: 'Confidentiality',
      explanation: 'Balanced, reciprocal mutual confidentiality clause with mutual standards of care.',
      status: 'analyzed',
      rule_findings: [],
      created_at: '2026-09-12T10:05:00.000Z',
      translation_available: true,
    },
    {
      id: 'clause-safe-102',
      document_id: 'doc-safe-001',
      position: 2,
      original_text:
        'Neither party charges commercial fees for collaborative exploratory research under this preliminary framework.',
      simplified_text: 'Neither company owes money or charges fees for this exploratory research collaboration.',
      severity: 'Safe',
      category: 'Payment',
      explanation: 'Zero-dollar exploratory arrangement without payment risk.',
      status: 'analyzed',
      rule_findings: [],
      created_at: '2026-09-12T10:05:00.000Z',
      translation_available: true,
    },
    {
      id: 'clause-safe-103',
      document_id: 'doc-safe-001',
      position: 3,
      original_text:
        'Each party shall comply with applicable privacy statutes and shall not transfer personally identifiable information without explicit written consent.',
      simplified_text: 'Both parties agree to obey privacy laws and will not share personal information without permission.',
      severity: 'Safe',
      category: 'Privacy',
      explanation: 'Standard mutual data privacy protections.',
      status: 'analyzed',
      rule_findings: [],
      created_at: '2026-09-12T10:05:00.000Z',
      translation_available: true,
    },
    {
      id: 'clause-safe-104',
      document_id: 'doc-safe-001',
      position: 4,
      original_text:
        'Disputes arising out of this Agreement shall be resolved through good-faith executive escalation followed by mutual mediation.',
      simplified_text: 'Any disagreement will first be negotiated in good faith by company executives, then mediated amicably.',
      severity: 'Safe',
      category: 'Dispute Resolution',
      explanation: 'Amicable multi-tier dispute resolution mechanism.',
      status: 'analyzed',
      rule_findings: [],
      created_at: '2026-09-12T10:05:00.000Z',
      translation_available: true,
    },
  ],
};

const HINDI_SIMPLIFICATIONS: Record<string, string> = {
  'clause-101':
    'यदि आपके डेटा या सेवा के उपयोग के कारण विक्रेता पर मुकदमा होता है, तो आपको सभी कानूनी लागत, क्षतिपूर्ति और वकील की फीस का भुगतान करना होगा। आपके दायित्व पर कोई सीमा नहीं है।',
  'clause-102':
    'विक्रेता बिना कोई कारण बताए किसी भी समय तुरंत सेवा और अनुबंध रद्द कर सकता है, कोई अग्रिम शुल्क वापस नहीं करेगा और डेटा माइग्रेशन में सहायता नहीं करेगा।',
  'clause-103':
    'अनुबंध हर साल स्वतः नवीनीकृत होगा जब तक कि आप 60 दिन पहले लिखित रूप में रद्द न करें। प्रत्येक नवीनीकरण पर कीमतें 15% तक बढ़ सकती हैं।',
  'clause-104':
    'चालान का भुगतान 15 दिनों के भीतर करना आवश्यक है। अतिदेय राशि पर 1.5% मासिक चक्रवृद्धि ब्याज लगेगा।',
};

const HINDI_EXPLANATIONS: Record<string, string> = {
  'clause-101':
    'असीमित एकतरफा क्षतिपूर्ति तीसरे पक्ष के जोखिम को पूरी तरह से आप पर डालती है, जिसमें विक्रेता से कोई सुरक्षा नहीं है।',
  'clause-102':
    'बिना कारण तुरंत समाप्ति से व्यवसाय की निरंतरता को गंभीर खतरा हो सकता है।',
  'clause-103':
    'कड़े 60-दिवसीय नोटिस और 15% मूल्य वृद्धि के साथ स्वचालित नवीनीकरण आपकी लागत को बढ़ा सकता है।',
  'clause-104':
    '15-दिन की भुगतान अवधि कॉर्पोरेट मानकों की तुलना में बहुत कम है और इस पर उच्च ब्याज दर लगती है।',
};

/**
 * Testing helpers to set/reset mock document fixtures
 */
export const __setMockDocuments = (docs: DocumentItem[]): void => {
  mockDocumentsDb = [...docs];
};

export const __setMockDocumentProgression = (enabled: boolean): void => {
  autoProgressEnabled = enabled;
};

export const __setMockDocumentStatus = (
  id: string,
  status: DocumentStatusType,
  failureReason: string | null = null
): void => {
  const doc = mockDocumentsDb.find((d) => d.id === id);
  if (doc) {
    doc.status = status;
    doc.failure_reason = failureReason;
    doc.updated_at = new Date().toISOString();
  }
};

export const __setMockSummary = (
  docId: string,
  summary: { en: DocumentSummary; hi?: DocumentSummary }
): void => {
  MOCK_SUMMARIES[docId] = summary;
};

export const __setMockClauses = (docId: string, clauses: ClauseItem[]): void => {
  MOCK_CLAUSES_BY_DOC[docId] = [...clauses];
};

export const __resetMockDocuments = (): void => {
  mockDocumentsDb = INITIAL_MOCK_DOCUMENTS.map((doc) => ({ ...doc }));
  autoProgressEnabled = false;
};

