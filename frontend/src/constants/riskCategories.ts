/**
 * ClarifAI Approved 8 Risk Categories Specification (PRD Ch. 16 & Section 8.3)
 */
export type RiskCategory =
  | 'Payment'
  | 'Termination'
  | 'Renewal'
  | 'Confidentiality'
  | 'Liability'
  | 'Intellectual Property'
  | 'Privacy'
  | 'Dispute Resolution';

export interface RiskCategoryDefinition {
  id: RiskCategory;
  label: string;
  description: string;
}

export const RISK_CATEGORIES: RiskCategoryDefinition[] = [
  {
    id: 'Payment',
    label: 'Payment',
    description: 'Fees, invoicing schedules, price escalations, late penalties, and reimbursement terms',
  },
  {
    id: 'Termination',
    label: 'Termination',
    description: 'Termination for cause/convenience, transition duties, and post-termination survival',
  },
  {
    id: 'Renewal',
    label: 'Renewal',
    description: 'Contract extension triggers, advance opt-out notification windows, and term lengths',
  },
  {
    id: 'Confidentiality',
    label: 'Confidentiality',
    description: 'Proprietary data protections, trade secret definitions, disclosures, and NDA duties',
  },
  {
    id: 'Liability',
    label: 'Liability',
    description: 'Indemnification, damage caps, indirect loss exclusions, and risk apportionment',
  },
  {
    id: 'Intellectual Property',
    label: 'Intellectual Property',
    description: 'Ownership of works, patent/trademark rights, licensing boundaries, and IP warranties',
  },
  {
    id: 'Privacy',
    label: 'Privacy',
    description: 'Personal data handling, GDPR/compliance duties, security safeguards, and breach notice',
  },
  {
    id: 'Dispute Resolution',
    label: 'Dispute Resolution',
    description: 'Arbitration mandates, governing law, venue jurisdiction, and legal fee allocations',
  },
];

export const VALID_RISK_CATEGORY_SET = new Set<string>(RISK_CATEGORIES.map((c) => c.id));

export const isValidRiskCategory = (val: string): val is RiskCategory => {
  return VALID_RISK_CATEGORY_SET.has(val);
};
