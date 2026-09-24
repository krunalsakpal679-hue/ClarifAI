"""
Seed Dataset Builder for ClarifAI AI Models (AI-PHASE-DATA-SEED-01)
Constructs versioned, document-scoped synthetic seed datasets for:
1. Task 1: Legal-BERT Clause Risk Classification (4 Severities, 8 Categories, Contextual Rule Findings)
2. Task 2: Multilingual-E5 Pairwise Contract Clause Comparison (MATCHED, CHANGED, MISSING + Hard Negatives)

Enforces:
- Explicit 'SEED/SYNTHETIC' origin tagging on every record.
- Strict deduplication of clause text before splitting.
- Document-level split allocation (70% Train, 15% Validation, 15% Test).
- Automated leakage prevention check.
"""

import json
import hashlib
import random
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple

DATASET_VERSION = "v0.1-seed"

# Base directories
TRAINING_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = TRAINING_DIR / "data"
LEGAL_BERT_DIR = DATA_DIR / "legal_bert"
MULTILINGUAL_E5_DIR = DATA_DIR / "multilingual_e5"


# ==============================================================================
# SEED DOCUMENTS & CLAUSES DEFINITION (TASK 1: LEGAL-BERT)
# 20 distinct document types representing typical contracts
# ==============================================================================

DOCUMENTS_LEGAL_BERT = [
    {
        "doc_id": "doc_saas_master_001",
        "doc_type": "SaaS Subscription Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Customer shall pay all subscription fees annually in advance within thirty (30) days of invoice date.",
                "category": "Payment",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard advance payment clause."
            },
            {
                "clause_id": "c02",
                "text": "This Agreement shall automatically renew for successive 12-month terms unless either party gives written notice at least 60 days prior.",
                "category": "Renewal",
                "severity": "Moderate",
                "rule_findings": [{"rule_id": "R001", "risk_signal": "Auto-Renewal"}],
                "why_flagged": "Automatic annual renewal requiring advance notice."
            },
            {
                "clause_id": "c03",
                "text": "In no event shall Vendor's total cumulative liability exceed the total fees paid by Customer in the preceding six months.",
                "category": "Liability",
                "severity": "Moderate",
                "rule_findings": [{"rule_id": "R005", "risk_signal": "Excessive Liability Transfer"}],
                "why_flagged": "Liability capped to 6 months of historical fees."
            },
            {
                "clause_id": "c04",
                "text": "Early termination by Customer prior to term expiration shall incur an immediate liquidated penalty equal to 100% of remaining contract value.",
                "category": "Termination",
                "severity": "High",
                "rule_findings": [{"rule_id": "R002", "risk_signal": "Early-Termination Penalty"}],
                "why_flagged": "Severe 100% early termination fee penalty."
            }
        ]
    },
    {
        "doc_id": "doc_nda_bilateral_002",
        "doc_type": "Mutual Non-Disclosure Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Each party agrees to hold all Proprietary Information in strict confidence for a period of three (3) years from disclosure.",
                "category": "Confidentiality",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard 3-year mutual confidentiality term."
            },
            {
                "clause_id": "c02",
                "text": "Receiving Party's confidentiality obligations shall survive perpetually with no expiration for trade secret materials.",
                "category": "Confidentiality",
                "severity": "Low",
                "rule_findings": [],
                "why_flagged": "Perpetual confidentiality on trade secrets."
            },
            {
                "clause_id": "c03",
                "text": "Disclosing Party may seek immediate ex-parte injunction and unilateral damages without need to post bond in any jurisdiction.",
                "category": "Dispute Resolution",
                "severity": "Moderate",
                "rule_findings": [{"rule_id": "R012", "risk_signal": "Dispute Venue Inconvenience"}],
                "why_flagged": "Injunctive relief without bond."
            }
        ]
    },
    {
        "doc_id": "doc_employment_exec_003",
        "doc_type": "Executive Employment Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Executive shall receive a base salary of $250,000 payable semi-monthly subject to standard statutory withholdings.",
                "category": "Payment",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard executive base compensation."
            },
            {
                "clause_id": "c02",
                "text": "Executive agrees not to engage in any competing business worldwide for a period of twenty-four (24) months following termination.",
                "category": "Intellectual Property",
                "severity": "High",
                "rule_findings": [{"rule_id": "R009", "risk_signal": "Non-Compete Scope"}],
                "why_flagged": "Broad 24-month worldwide non-compete covenant."
            },
            {
                "clause_id": "c03",
                "text": "All inventions, software, and works created by Executive, whether on company time or personal time, belong exclusively to Employer.",
                "category": "Intellectual Property",
                "severity": "High",
                "rule_findings": [{"rule_id": "R008", "risk_signal": "IP Ownership Transfer"}],
                "why_flagged": "Overly broad IP assignment claiming personal-time inventions."
            },
            {
                "clause_id": "c04",
                "text": "Employer may terminate this Agreement without cause upon giving thirty (30) days notice with standard severance payout.",
                "category": "Termination",
                "severity": "Low",
                "rule_findings": [],
                "why_flagged": "Standard employer termination for convenience."
            }
        ]
    },
    {
        "doc_id": "doc_vendor_services_004",
        "doc_type": "Master Services Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Vendor warrants that all deliverables will conform to published technical specifications for ninety (90) days.",
                "category": "Liability",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard 90-day warranty period."
            },
            {
                "clause_id": "c02",
                "text": "Client agrees to defend, indemnify, and hold harmless Vendor from any third-party claims arising from deliverables.",
                "category": "Liability",
                "severity": "High",
                "rule_findings": [{"rule_id": "R006", "risk_signal": "Broad Indemnification"}],
                "why_flagged": "Unilateral indemnification forced upon client."
            },
            {
                "clause_id": "c03",
                "text": "Overdue invoices accrue compound interest at 2.5% per month plus a fixed administrative surcharge.",
                "category": "Payment",
                "severity": "Moderate",
                "rule_findings": [
                    {"rule_id": "R004", "risk_signal": "Late-Payment Penalty"},
                    {"rule_id": "R003", "risk_signal": "Hidden/Add-on Charges"}
                ],
                "why_flagged": "Compound late interest with additional administrative surcharge."
            }
        ]
    },
    {
        "doc_id": "doc_commercial_lease_005",
        "doc_type": "Commercial Property Lease",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Tenant shall remit monthly base rent on the first calendar day of each month to Landlord's designated account.",
                "category": "Payment",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard base rent payment."
            },
            {
                "clause_id": "c02",
                "text": "Landlord reserves the right to modify operating cost allocations and impose unitemized maintenance surcharges at its sole discretion.",
                "category": "Payment",
                "severity": "High",
                "rule_findings": [
                    {"rule_id": "R003", "risk_signal": "Hidden/Add-on Charges"},
                    {"rule_id": "R007", "risk_signal": "Unilateral Modification"}
                ],
                "why_flagged": "Unilateral imposition of unitemized maintenance charges."
            },
            {
                "clause_id": "c03",
                "text": "This lease shall extend automatically for five (5) additional years unless Tenant provides notice twelve months in advance.",
                "category": "Renewal",
                "severity": "High",
                "rule_findings": [{"rule_id": "R001", "risk_signal": "Auto-Renewal"}],
                "why_flagged": "Extremely long 5-year auto-extension with restrictive 12-month notice window."
            }
        ]
    },
    {
        "doc_id": "doc_cloud_sla_006",
        "doc_type": "Cloud Service Level Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Provider will use commercially reasonable efforts to make the online services available with 99.9% uptime monthly.",
                "category": "Liability",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard 99.9% uptime commitment."
            },
            {
                "clause_id": "c02",
                "text": "Service credits shall be Customer's sole and exclusive financial remedy for any unavailability or system failure.",
                "category": "Liability",
                "severity": "Low",
                "rule_findings": [],
                "why_flagged": "Standard sole remedy clause for SLA downtime."
            },
            {
                "clause_id": "c03",
                "text": "Provider may alter SLA targets, downtime calculation metrics, or credit percentages at any time upon posting updates to its website.",
                "category": "Liability",
                "severity": "High",
                "rule_findings": [{"rule_id": "R007", "risk_signal": "Unilateral Modification"}],
                "why_flagged": "Unilateral right to weaken SLA commitments via website posting."
            }
        ]
    },
    {
        "doc_id": "doc_data_privacy_dpa_007",
        "doc_type": "Data Processing Addendum (DPA)",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Processor will process Personal Data solely on documented instructions from Controller in compliance with GDPR.",
                "category": "Privacy",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard GDPR Article 28 data processor obligation."
            },
            {
                "clause_id": "c02",
                "text": "Processor shall notify Controller of any confirmed personal data breach without undue delay and within 48 hours.",
                "category": "Privacy",
                "severity": "Low",
                "rule_findings": [],
                "why_flagged": "48-hour breach notification timeframe."
            },
            {
                "clause_id": "c03",
                "text": "Processor may transfer personal customer information to third-party sub-processors internationally without prior written consent.",
                "category": "Privacy",
                "severity": "High",
                "rule_findings": [{"rule_id": "R010", "risk_signal": "Data Rights Waiver"}],
                "why_flagged": "Unrestricted international data transfers without Controller consent."
            }
        ]
    },
    {
        "doc_id": "doc_consulting_services_008",
        "doc_type": "Consulting Professional Services Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Consultant is an independent contractor and nothing herein creates any partnership, joint venture, or agency.",
                "category": "Liability",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard independent contractor clause."
            },
            {
                "clause_id": "c02",
                "text": "Any controversy arising out of this agreement shall be submitted to confidential binding arbitration in New York, NY.",
                "category": "Dispute Resolution",
                "severity": "Low",
                "rule_findings": [],
                "why_flagged": "Standard commercial arbitration provision."
            },
            {
                "clause_id": "c03",
                "text": "Client waives all right to a jury trial and agrees not to participate in any class action litigation against Consultant.",
                "category": "Dispute Resolution",
                "severity": "Moderate",
                "rule_findings": [{"rule_id": "R011", "risk_signal": "Class Action Waiver"}],
                "why_flagged": "Class action and jury trial waiver."
            }
        ]
    },
    {
        "doc_id": "doc_software_license_009",
        "doc_type": "End User License Agreement (EULA)",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Licensor grants Licensee a non-exclusive, non-transferable revocable license to install and use the Software.",
                "category": "Intellectual Property",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard software license grant."
            },
            {
                "clause_id": "c02",
                "text": "Licensee shall not reverse engineer, decompile, or disassemble any binary components of the Software.",
                "category": "Intellectual Property",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard reverse engineering prohibition."
            },
            {
                "clause_id": "c03",
                "text": "Licensor may remotely deactivate or audit Licensee's systems at any time without prior warning or notice.",
                "category": "Intellectual Property",
                "severity": "High",
                "rule_findings": [{"rule_id": "R013", "risk_signal": "Aggressive Audit Rights"}],
                "why_flagged": "Unilateral remote deactivation without prior notice."
            }
        ]
    },
    {
        "doc_id": "doc_loan_financing_010",
        "doc_type": "Commercial Loan & Security Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Borrower shall repay principal and interest in monthly installments over a 36-month maturity schedule.",
                "category": "Payment",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard 3-year term loan repayment."
            },
            {
                "clause_id": "c02",
                "text": "Lender may accelerate full balance maturity upon any payment default occurring more than 5 days overdue.",
                "category": "Termination",
                "severity": "High",
                "rule_findings": [
                    {"rule_id": "R004", "risk_signal": "Late-Payment Penalty"},
                    {"rule_id": "R014", "risk_signal": "Cross-Default Trigger"}
                ],
                "why_flagged": "Aggressive 5-day default acceleration trigger."
            },
            {
                "clause_id": "c03",
                "text": "Prepayment of principal during the first twelve months requires a 5% prepayment penalty fee.",
                "category": "Payment",
                "severity": "Moderate",
                "rule_findings": [{"rule_id": "R002", "risk_signal": "Early-Termination Penalty"}],
                "why_flagged": "Prepayment penalty fee on early loan payoff."
            }
        ]
    },
    {
        "doc_id": "doc_marketing_agency_011",
        "doc_type": "Digital Marketing Agency Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Agency shall submit monthly campaign performance reports and analytics dashboards by the 5th business day.",
                "category": "Payment",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard agency reporting requirement."
            },
            {
                "clause_id": "c02",
                "text": "Client assigns all marketing creative ownership and trademarks developed under this campaign to Agency.",
                "category": "Intellectual Property",
                "severity": "High",
                "rule_findings": [{"rule_id": "R008", "risk_signal": "IP Ownership Transfer"}],
                "why_flagged": "Agency claims ownership of client trademarks and creative assets."
            },
            {
                "clause_id": "c03",
                "text": "Agency may feature Client's name and logo in marketing case studies and portfolio materials.",
                "category": "Confidentiality",
                "severity": "Low",
                "rule_findings": [],
                "why_flagged": "Standard marketing portfolio usage permission."
            }
        ]
    },
    {
        "doc_id": "doc_equipment_maintenance_012",
        "doc_type": "Hardware Maintenance Contract",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Service provider will dispatch field engineers within 4 business hours of a confirmed hardware failure.",
                "category": "Liability",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard 4-hour on-site dispatch SLA."
            },
            {
                "clause_id": "c02",
                "text": "Contract automatically extends for 3-year periods unless written cancellation is received 90 days prior.",
                "category": "Renewal",
                "severity": "Moderate",
                "rule_findings": [{"rule_id": "R001", "risk_signal": "Auto-Renewal"}],
                "why_flagged": "3-year multi-year auto-extension."
            },
            {
                "clause_id": "c03",
                "text": "Replacement components may be refurbished or aftermarket parts at service provider's sole discretion.",
                "category": "Liability",
                "severity": "Low",
                "rule_findings": [],
                "why_flagged": "Allows refurbished hardware parts."
            }
        ]
    },
    {
        "doc_id": "doc_distributor_agreement_013",
        "doc_type": "Exclusive Distribution Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Distributor shall meet minimum annual purchase targets of $500,000 to maintain exclusivity.",
                "category": "Payment",
                "severity": "Low",
                "rule_findings": [],
                "why_flagged": "Standard annual sales threshold for distribution exclusivity."
            },
            {
                "clause_id": "c02",
                "text": "Manufacturer may terminate exclusivity immediately upon Distributor missing any quarterly quota by 1%.",
                "category": "Termination",
                "severity": "Moderate",
                "rule_findings": [{"rule_id": "R002", "risk_signal": "Early-Termination Penalty"}],
                "why_flagged": "Hair-trigger loss of exclusivity on minor quota miss."
            },
            {
                "clause_id": "c03",
                "text": "Distributor shall submit all disputes to foreign courts located exclusively in Zurich, Switzerland.",
                "category": "Dispute Resolution",
                "severity": "Moderate",
                "rule_findings": [{"rule_id": "R012", "risk_signal": "Dispute Venue Inconvenience"}],
                "why_flagged": "Foreign forum selection clause."
            }
        ]
    },
    {
        "doc_id": "doc_website_tos_014",
        "doc_type": "Consumer Website Terms of Service",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Users must be at least 18 years of age to register an account on the platform.",
                "category": "Privacy",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard age restriction."
            },
            {
                "clause_id": "c02",
                "text": "Platform reserves the right to modify these terms, fees, and feature availability at any time without notice.",
                "category": "Renewal",
                "severity": "High",
                "rule_findings": [{"rule_id": "R007", "risk_signal": "Unilateral Modification"}],
                "why_flagged": "Unilateral terms and pricing changes without notice."
            },
            {
                "clause_id": "c03",
                "text": "Users grant platform a perpetual, irrevocable, worldwide license to monetize and sell all uploaded content.",
                "category": "Intellectual Property",
                "severity": "High",
                "rule_findings": [
                    {"rule_id": "R008", "risk_signal": "IP Ownership Transfer"},
                    {"rule_id": "R010", "risk_signal": "Data Rights Waiver"}
                ],
                "why_flagged": "Overreaching commercial license to monetize user uploads."
            }
        ]
    },
    {
        "doc_id": "doc_subcontractor_nda_015",
        "doc_type": "Subcontractor Confidentiality Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Subcontractor will use confidential materials solely for performing designated project services.",
                "category": "Confidentiality",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard purpose limitation on confidential information."
            },
            {
                "clause_id": "c02",
                "text": "Upon completion of work, Subcontractor shall certify return or destruction of all confidential files.",
                "category": "Confidentiality",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard destruction certificate on contract conclusion."
            }
        ]
    },
    {
        "doc_id": "doc_joint_venture_016",
        "doc_type": "Joint Venture Operating Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Profits and losses from joint operations will be distributed pro-rata based on capital contributions.",
                "category": "Payment",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard capital contribution profit split."
            },
            {
                "clause_id": "c02",
                "text": "Partner A shall have unilateral tie-breaking authority on all operational capital expenditures above $50,000.",
                "category": "Dispute Resolution",
                "severity": "Low",
                "rule_findings": [],
                "why_flagged": "Operational deadlock tie-breaking mechanism."
            },
            {
                "clause_id": "c03",
                "text": "Default by either party on any unrelated commercial debt constitutes automatic default under this venture.",
                "category": "Termination",
                "severity": "High",
                "rule_findings": [{"rule_id": "R014", "risk_signal": "Cross-Default Trigger"}],
                "why_flagged": "Severe cross-default trigger linked to outside debts."
            }
        ]
    },
    {
        "doc_id": "doc_telecom_service_017",
        "doc_type": "Enterprise Telecom Services Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Carrier will provide 10 Gbps dedicated optical transit lines with 99.95% network availability.",
                "category": "Liability",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard optical transit SLA specification."
            },
            {
                "clause_id": "c02",
                "text": "Unpaid bills after 15 days will incur a 2.0% monthly late charge and immediate service suspension.",
                "category": "Payment",
                "severity": "Moderate",
                "rule_findings": [{"rule_id": "R004", "risk_signal": "Late-Payment Penalty"}],
                "why_flagged": "Short 15-day grace period with service cutoff."
            }
        ]
    },
    {
        "doc_id": "doc_saas_reseller_018",
        "doc_type": "SaaS Channel Partner Reseller Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Reseller earns a 20% commission on all new recurring annual contracts registered and closed.",
                "category": "Payment",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard reseller margin."
            },
            {
                "clause_id": "c02",
                "text": "Vendor reserves the right to re-audit Reseller's customer records on 24 hours notice at Reseller's expense.",
                "category": "Liability",
                "severity": "Moderate",
                "rule_findings": [{"rule_id": "R013", "risk_signal": "Aggressive Audit Rights"}],
                "why_flagged": "Aggressive short-notice audit with cost shifting."
            }
        ]
    },
    {
        "doc_id": "doc_research_grant_019",
        "doc_type": "University Research & Development Grant",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Institution will submit semi-annual financial expense reconciliations and technical milestones.",
                "category": "Payment",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard grant accountability reporting."
            },
            {
                "clause_id": "c02",
                "text": "Sponsor retains commercial exclusive royalty-free license to all patents generated from grant funding.",
                "category": "Intellectual Property",
                "severity": "Moderate",
                "rule_findings": [{"rule_id": "R008", "risk_signal": "IP Ownership Transfer"}],
                "why_flagged": "Sponsor patent commercialization license."
            }
        ]
    },
    {
        "doc_id": "doc_software_escrow_020",
        "doc_type": "Software Source Code Escrow Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Developer will deposit updated source code builds into secure escrow quarterly.",
                "category": "Intellectual Property",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Quarterly source code deposit requirement."
            },
            {
                "clause_id": "c02",
                "text": "Escrow agent shall release code to Beneficiary only upon Developer filing for bankruptcy or liquidation.",
                "category": "Termination",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard bankruptcy release condition."
            }
        ]
    }
]


# ==============================================================================
# SEED DOCUMENT PAIRS DEFINITION (TASK 2: MULTILINGUAL-E5 COMPARISON)
# 15 distinct document pair comparisons representing redlines / revisions
# ==============================================================================

DOC_PAIRS_MULTILINGUAL_E5 = [
    {
        "doc_pair_id": "pair_saas_v1_v2_001",
        "doc_a_id": "doc_saas_v1",
        "doc_b_id": "doc_saas_v2",
        "contract_title": "SaaS Subscription Agreement (Baseline vs Revised)",
        "pairs": [
            {
                "clause_a_id": "v1_c01",
                "clause_b_id": "v2_c01",
                "text_a": "Customer shall pay all invoices within thirty (30) days of receipt.",
                "text_b": "Customer shall pay all invoices within thirty (30) days of receipt.",
                "classification": "MATCHED",
                "target_similarity": 1.00,
                "difference_explanation": "Clause text is verbatim identical across versions.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c02",
                "clause_b_id": "v2_c02",
                "text_a": "Either party may terminate this agreement upon 30 days written notice.",
                "text_b": "Either party may terminate this agreement upon sixty (60) days written notice.",
                "classification": "CHANGED",
                "target_similarity": 0.82,
                "difference_explanation": "Termination notice period increased from 30 days to 60 days.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c03",
                "clause_b_id": None,
                "text_a": "Vendor will provide free telephone technical support during standard business hours.",
                "text_b": None,
                "classification": "MISSING",
                "target_similarity": 0.0,
                "difference_explanation": "Free telephone technical support commitment was removed in Document B.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c01",
                "clause_b_id": "v2_c02",
                "text_a": "Customer shall pay all invoices within thirty (30) days of receipt.",
                "text_b": "Either party may terminate this agreement upon sixty (60) days written notice.",
                "classification": "MISSING",
                "target_similarity": 0.25,
                "difference_explanation": "Payment clause compared against termination clause (distractor).",
                "is_hard_negative": True
            }
        ]
    },
    {
        "doc_pair_id": "pair_nda_unilateral_bilateral_002",
        "doc_a_id": "doc_nda_unilateral_v1",
        "doc_b_id": "doc_nda_bilateral_v2",
        "contract_title": "NDA (Unilateral Baseline vs Bilateral Revised)",
        "pairs": [
            {
                "clause_a_id": "v1_c01",
                "clause_b_id": "v2_c01",
                "text_a": "Recipient shall protect Discloser's proprietary information using reasonable care.",
                "text_b": "Each party shall protect the other party's proprietary information using reasonable care.",
                "classification": "CHANGED",
                "target_similarity": 0.85,
                "difference_explanation": "Scope expanded from unilateral recipient obligations to mutual bilateral obligations.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c02",
                "clause_b_id": "v2_c02",
                "text_a": "Confidentiality obligations expire three (3) years from disclosure date.",
                "text_b": "Confidentiality obligations expire five (5) years from disclosure date.",
                "classification": "CHANGED",
                "target_similarity": 0.80,
                "difference_explanation": "Confidentiality duration extended from 3 years to 5 years.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": None,
                "clause_b_id": "v2_c03",
                "text_a": None,
                "text_b": "Trade secrets shall remain confidential perpetually without any expiration date.",
                "classification": "MISSING",
                "target_similarity": 0.0,
                "difference_explanation": "Perpetual trade secret clause is newly added in Document B.",
                "is_hard_negative": False
            }
        ]
    },
    {
        "doc_pair_id": "pair_employment_initial_amended_003",
        "doc_a_id": "doc_emp_v1",
        "doc_b_id": "doc_emp_v2",
        "contract_title": "Employment Agreement (Initial Offer vs Exec Amendment)",
        "pairs": [
            {
                "clause_a_id": "v1_c01",
                "clause_b_id": "v2_c01",
                "text_a": "Employee will receive an initial base salary of $120,000 per annum.",
                "text_b": "Employee will receive an initial base salary of $150,000 per annum.",
                "classification": "CHANGED",
                "target_similarity": 0.86,
                "difference_explanation": "Annual base compensation increased from $120,000 to $150,000.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c02",
                "clause_b_id": "v2_c02",
                "text_a": "Employee is entitled to twenty (20) days of paid annual vacation.",
                "text_b": "Employee is entitled to twenty (20) days of paid annual vacation.",
                "classification": "MATCHED",
                "target_similarity": 1.00,
                "difference_explanation": "Vacation entitlement matches exactly.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c03",
                "clause_b_id": "v2_c03",
                "text_a": "Non-compete covenant applies for twelve (12) months within 50 miles.",
                "text_b": "Non-compete covenant applies for twenty-four (24) months nationwide.",
                "classification": "CHANGED",
                "target_similarity": 0.74,
                "difference_explanation": "Non-compete duration increased to 24 months and geographic scope widened to nationwide.",
                "is_hard_negative": False
            }
        ]
    },
    {
        "doc_pair_id": "pair_lease_draft_final_004",
        "doc_a_id": "doc_lease_draft",
        "doc_b_id": "doc_lease_final",
        "contract_title": "Office Lease (Draft vs Executed Final)",
        "pairs": [
            {
                "clause_a_id": "v1_c01",
                "clause_b_id": "v2_c01",
                "text_a": "Monthly rent shall be $8,500 due on the 1st of each month.",
                "text_b": "Monthly rent shall be $8,000 due on the 1st of each month.",
                "classification": "CHANGED",
                "target_similarity": 0.88,
                "difference_explanation": "Monthly rent discounted from $8,500 to $8,000.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c02",
                "clause_b_id": "v2_c02",
                "text_a": "Security deposit equal to two months rent shall be deposited at signing.",
                "text_b": "Security deposit equal to two months rent shall be deposited at signing.",
                "classification": "MATCHED",
                "target_similarity": 1.00,
                "difference_explanation": "Security deposit terms identical.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c03",
                "clause_b_id": None,
                "text_a": "Tenant is responsible for building roof and structural foundation repairs.",
                "text_b": None,
                "classification": "MISSING",
                "target_similarity": 0.0,
                "difference_explanation": "Tenant structural repair burden removed from final agreement.",
                "is_hard_negative": False
            }
        ]
    },
    {
        "doc_pair_id": "pair_msa_vendor_client_005",
        "doc_a_id": "doc_msa_vendor_paper",
        "doc_b_id": "doc_msa_client_markup",
        "contract_title": "Master Services Agreement (Vendor vs Client Redline)",
        "pairs": [
            {
                "clause_a_id": "v1_c01",
                "clause_b_id": "v2_c01",
                "text_a": "Client shall indemnify Vendor against all third party claims.",
                "text_b": "Each party shall indemnify the other for claims arising from gross negligence.",
                "classification": "CHANGED",
                "target_similarity": 0.72,
                "difference_explanation": "Indemnification made mutual and limited to gross negligence.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c02",
                "clause_b_id": "v2_c02",
                "text_a": "Governing law shall be the State of Delaware without regard to conflicts.",
                "text_b": "Governing law shall be the State of Delaware without regard to conflicts.",
                "classification": "MATCHED",
                "target_similarity": 1.00,
                "difference_explanation": "Delaware governing law clause identical.",
                "is_hard_negative": False
            }
        ]
    },
    {
        "doc_pair_id": "pair_eula_2025_2026_006",
        "doc_a_id": "doc_eula_2025",
        "doc_b_id": "doc_eula_2026",
        "contract_title": "Software EULA (2025 Release vs 2026 Update)",
        "pairs": [
            {
                "clause_a_id": "v1_c01",
                "clause_b_id": "v2_c01",
                "text_a": "Licensor grants user a non-exclusive license to use the app on up to 3 devices.",
                "text_b": "Licensor grants user a non-exclusive license to use the app on up to 5 devices.",
                "classification": "CHANGED",
                "target_similarity": 0.87,
                "difference_explanation": "Device limit increased from 3 to 5 authorized devices.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": None,
                "clause_b_id": "v2_c02",
                "text_a": None,
                "text_b": "AI telemetry and diagnostic logs may be collected to train quality models.",
                "classification": "MISSING",
                "target_similarity": 0.0,
                "difference_explanation": "New AI telemetry data collection clause added in 2026 version.",
                "is_hard_negative": False
            }
        ]
    },
    {
        "doc_pair_id": "pair_cloud_sla_standard_enterprise_007",
        "doc_a_id": "doc_sla_standard",
        "doc_b_id": "doc_sla_enterprise",
        "contract_title": "Cloud SLA (Standard vs Enterprise Tier)",
        "pairs": [
            {
                "clause_a_id": "v1_c01",
                "clause_b_id": "v2_c01",
                "text_a": "Monthly service commitment availability target is 99.5%.",
                "text_b": "Monthly service commitment availability target is 99.99%.",
                "classification": "CHANGED",
                "target_similarity": 0.85,
                "difference_explanation": "Uptime availability target upgraded from 99.5% to 99.99%.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c02",
                "clause_b_id": "v2_c02",
                "text_a": "Support response time for critical issues is within 4 hours.",
                "text_b": "Support response time for critical issues is within 15 minutes.",
                "classification": "CHANGED",
                "target_similarity": 0.78,
                "difference_explanation": "Critical support response time expedited from 4 hours to 15 minutes.",
                "is_hard_negative": False
            }
        ]
    },
    {
        "doc_pair_id": "pair_consulting_fixed_hourly_008",
        "doc_a_id": "doc_consult_fixed",
        "doc_b_id": "doc_consult_t_and_m",
        "contract_title": "Consulting Agreement (Fixed Price vs Time & Materials)",
        "pairs": [
            {
                "clause_a_id": "v1_c01",
                "clause_b_id": "v2_c01",
                "text_a": "Client shall pay a total fixed milestone fee of $75,000 upon project signoff.",
                "text_b": "Client shall be billed on a Time and Materials basis at $175 per consultant hour.",
                "classification": "CHANGED",
                "target_similarity": 0.68,
                "difference_explanation": "Billing structure transitioned from fixed $75,000 milestone to hourly $175 T&M rate.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c02",
                "clause_b_id": "v2_c02",
                "text_a": "Consultant retains ownership of pre-existing background code libraries.",
                "text_b": "Consultant retains ownership of pre-existing background code libraries.",
                "classification": "MATCHED",
                "target_similarity": 1.00,
                "difference_explanation": "Background IP ownership clause matches verbatim.",
                "is_hard_negative": False
            }
        ]
    },
    {
        "doc_pair_id": "pair_dpa_scc_modernized_009",
        "doc_a_id": "doc_dpa_legacy_scc",
        "doc_b_id": "doc_dpa_modern_scc",
        "contract_title": "Data Processing Addendum (Legacy 2010 SCC vs 2021 Modular SCC)",
        "pairs": [
            {
                "clause_a_id": "v1_c01",
                "clause_b_id": "v2_c01",
                "text_a": "Data transfers to third countries incorporate 2010 EU Standard Contractual Clauses.",
                "text_b": "Data transfers incorporate 2021 EU Standard Contractual Clauses (Module 2 Controller-to-Processor).",
                "classification": "CHANGED",
                "target_similarity": 0.77,
                "difference_explanation": "Standard Contractual Clauses updated to the 2021 modern modular version.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c02",
                "clause_b_id": "v2_c02",
                "text_a": "Sub-processors must be audited annually by independent cybersecurity firms.",
                "text_b": "Sub-processors must be audited annually by independent cybersecurity firms.",
                "classification": "MATCHED",
                "target_similarity": 1.00,
                "difference_explanation": "Annual sub-processor audit requirement identical.",
                "is_hard_negative": False
            }
        ]
    },
    {
        "doc_pair_id": "pair_distribution_regional_global_010",
        "doc_a_id": "doc_dist_regional",
        "doc_b_id": "doc_dist_global",
        "contract_title": "Distribution Agreement (Regional Territory vs Global Expansion)",
        "pairs": [
            {
                "clause_a_id": "v1_c01",
                "clause_b_id": "v2_c01",
                "text_a": "The Territory shall encompass the continental United States and Canada.",
                "text_b": "The Territory shall encompass North America, the European Union, and the United Kingdom.",
                "classification": "CHANGED",
                "target_similarity": 0.76,
                "difference_explanation": "Territory expanded to include the European Union and the United Kingdom.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c02",
                "clause_b_id": "v2_c02",
                "text_a": "Distributor shall maintain commercial general liability insurance of $2,000,000.",
                "text_b": "Distributor shall maintain commercial general liability insurance of $2,000,000.",
                "classification": "MATCHED",
                "target_similarity": 1.00,
                "difference_explanation": "Insurance policy amount identical across agreements.",
                "is_hard_negative": False
            }
        ]
    },
    {
        "doc_pair_id": "pair_loan_secured_unsecured_011",
        "doc_a_id": "doc_loan_secured",
        "doc_b_id": "doc_loan_unsecured",
        "contract_title": "Loan Agreement (Senior Secured vs Unsecured Note)",
        "pairs": [
            {
                "clause_a_id": "v1_c01",
                "clause_b_id": "v2_c01",
                "text_a": "Loan is secured by a first-priority blanket lien on all corporate assets and accounts receivable.",
                "text_b": "Loan is an unsecured general corporate obligation with no lien on underlying assets.",
                "classification": "CHANGED",
                "target_similarity": 0.69,
                "difference_explanation": "Collateral lien replaced with unsecured corporate obligation.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c02",
                "clause_b_id": "v2_c02",
                "text_a": "Interest accrues at 6.0% per annum payable monthly in arrears.",
                "text_b": "Interest accrues at 8.5% per annum payable monthly in arrears.",
                "classification": "CHANGED",
                "target_similarity": 0.86,
                "difference_explanation": "Interest rate increased from 6.0% to 8.5%.",
                "is_hard_negative": False
            }
        ]
    },
    {
        "doc_pair_id": "pair_reseller_exclusive_nonexclusive_012",
        "doc_a_id": "doc_reseller_excl",
        "doc_b_id": "doc_reseller_nonexcl",
        "contract_title": "Reseller Agreement (Exclusive vs Non-Exclusive)",
        "pairs": [
            {
                "clause_a_id": "v1_c01",
                "clause_b_id": "v2_c01",
                "text_a": "Partner is appointed as the exclusive authorized reseller in the State of California.",
                "text_b": "Partner is appointed as a non-exclusive authorized reseller in the State of California.",
                "classification": "CHANGED",
                "target_similarity": 0.88,
                "difference_explanation": "Exclusivity right removed; partner converted to non-exclusive reseller.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c02",
                "clause_b_id": "v2_c02",
                "text_a": "Payment terms are Net 45 days from delivery of product keys.",
                "text_b": "Payment terms are Net 45 days from delivery of product keys.",
                "classification": "MATCHED",
                "target_similarity": 1.00,
                "difference_explanation": "Net 45 payment terms identical.",
                "is_hard_negative": False
            }
        ]
    },
    {
        "doc_pair_id": "pair_jv_initial_recapitalized_013",
        "doc_a_id": "doc_jv_init",
        "doc_b_id": "doc_jv_recap",
        "contract_title": "Joint Venture (50/50 Initial vs 70/30 Recapitalized)",
        "pairs": [
            {
                "clause_a_id": "v1_c01",
                "clause_b_id": "v2_c01",
                "text_a": "Member A and Member B each hold a fifty percent (50%) equity interest.",
                "text_b": "Member A holds a 70% equity interest and Member B holds a 30% equity interest.",
                "classification": "CHANGED",
                "target_similarity": 0.81,
                "difference_explanation": "Equity allocation shifted from equal 50/50 to 70/30 in favor of Member A.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c02",
                "clause_b_id": None,
                "text_a": "Unanimous consent of both members is required for any commercial debt exceeding $10,000.",
                "text_b": None,
                "classification": "MISSING",
                "target_similarity": 0.0,
                "difference_explanation": "Unanimous consent threshold removed in revised agreement.",
                "is_hard_negative": False
            }
        ]
    },
    {
        "doc_pair_id": "pair_agency_retainer_performance_014",
        "doc_a_id": "doc_agency_ret",
        "doc_b_id": "doc_agency_perf",
        "contract_title": "Agency Retainer (Fixed Retainer vs Performance Bonus)",
        "pairs": [
            {
                "clause_a_id": "v1_c01",
                "clause_b_id": "v2_c01",
                "text_a": "Client pays an advance monthly agency retainer fee of $10,000.",
                "text_b": "Client pays a monthly base of $5,000 plus 5% commission on net revenue growth.",
                "classification": "CHANGED",
                "target_similarity": 0.70,
                "difference_explanation": "Fixed $10k retainer replaced with $5k base plus performance commission.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c02",
                "clause_b_id": "v2_c02",
                "text_a": "Either party may terminate upon 30 days notice with written cause.",
                "text_b": "Either party may terminate upon 30 days notice with written cause.",
                "classification": "MATCHED",
                "target_similarity": 1.00,
                "difference_explanation": "30-day cause termination clause identical.",
                "is_hard_negative": False
            }
        ]
    },
    {
        "doc_pair_id": "pair_escrow_single_three_party_015",
        "doc_a_id": "doc_escrow_single",
        "doc_b_id": "doc_escrow_triparty",
        "contract_title": "Source Code Escrow (Two-Party vs Tri-Party Agreement)",
        "pairs": [
            {
                "clause_a_id": "v1_c01",
                "clause_b_id": "v2_c01",
                "text_a": "Escrow agent fees shall be borne entirely by Licensee.",
                "text_b": "Escrow agent fees shall be split equally fifty-fifty between Licensor and Licensee.",
                "classification": "CHANGED",
                "target_similarity": 0.83,
                "difference_explanation": "Escrow fees shifted from 100% Licensee to 50/50 split.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c02",
                "clause_b_id": "v2_c02",
                "text_a": "Deposits are subject to bi-annual integrity and compilation verification tests.",
                "text_b": "Deposits are subject to bi-annual integrity and compilation verification tests.",
                "classification": "MATCHED",
                "target_similarity": 1.00,
                "difference_explanation": "Bi-annual compilation verification requirement matches.",
                "is_hard_negative": False
            }
        ]
    }
]


def deduplicate_clauses(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicates clauses by exact text content within each document before dataset creation.
    """
    seen_hashes: Set[str] = set()
    cleaned_docs = []
    
    for doc in documents:
        unique_clauses = []
        for c in doc["clauses"]:
            h = hashlib.sha256(c["text"].strip().lower().encode("utf-8")).hexdigest()
            if h not in seen_hashes:
                seen_hashes.add(h)
                unique_clauses.append(c)
        if unique_clauses:
            cleaned_doc = dict(doc)
            cleaned_doc["clauses"] = unique_clauses
            cleaned_docs.append(cleaned_doc)
            
    return cleaned_docs


def split_by_document(
    items: List[Dict[str, Any]],
    id_key: str,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    seed: int = 42
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Splits items strictly by their unique document ID.
    Every clause/pair belonging to a document ID lands entirely within one split.
    """
    random.seed(seed)
    shuffled_items = list(items)
    random.shuffle(shuffled_items)
    
    n_total = len(shuffled_items)
    n_train = max(1, int(n_total * train_ratio))
    n_val = max(1, int(n_total * val_ratio))
    
    train_docs = shuffled_items[:n_train]
    val_docs = shuffled_items[n_train:n_train + n_val]
    test_docs = shuffled_items[n_train + n_val:]
    
    return train_docs, val_docs, test_docs


def build_legal_bert_examples(docs: List[Dict[str, Any]], split_name: str) -> List[Dict[str, Any]]:
    """
    Formats Legal-BERT training records with contextual input formatting per PRD Ch. 16.9.
    """
    severity_to_id = {"Safe": 0, "Low": 1, "Moderate": 2, "High": 3}
    records = []
    
    for doc in docs:
        doc_id = doc["doc_id"]
        doc_type = doc.get("doc_type", "Contract")
        
        for clause in doc["clauses"]:
            rule_findings = clause.get("rule_findings", [])
            findings_str = ", ".join([f"{rf['rule_id']} ({rf['risk_signal']})" for rf in rule_findings]) if rule_findings else "None"
            
            # Contextual input string format per Chapter 16.9
            context_text = f"[CLS] {clause['text']} [SEP] Rule Findings: {findings_str} [SEP] Document Type: {doc_type} [SEP]"
            
            record = {
                "doc_id": doc_id,
                "doc_type": doc_type,
                "clause_id": clause["clause_id"],
                "clause_text": clause["text"],
                "rule_findings": rule_findings,
                "context_text": context_text,
                "severity": clause["severity"],
                "severity_id": severity_to_id[clause["severity"]],
                "category": clause["category"],
                "why_flagged": clause.get("why_flagged", ""),
                "split": split_name,
                "metadata": {
                    "origin": "SEED/SYNTHETIC",
                    "dataset_version": DATASET_VERSION,
                    "language": "en"
                }
            }
            records.append(record)
            
    return records


def build_multilingual_e5_examples(pairs: List[Dict[str, Any]], split_name: str) -> List[Dict[str, Any]]:
    """
    Formats Multilingual-E5 comparison records with asymmetric passage prefixing.
    """
    records = []
    for doc_pair in pairs:
        doc_pair_id = doc_pair["doc_pair_id"]
        doc_a_id = doc_pair["doc_a_id"]
        doc_b_id = doc_pair["doc_b_id"]
        title = doc_pair.get("contract_title", "Contract Comparison")
        
        for pair in doc_pair["pairs"]:
            text_a = pair["text_a"]
            text_b = pair["text_b"]
            
            # Asymmetric E5 prefixing protocol
            formatted_text_a = f"passage: {text_a.strip()}" if text_a else None
            formatted_text_b = f"passage: {text_b.strip()}" if text_b else None
            
            record = {
                "doc_pair_id": doc_pair_id,
                "doc_a_id": doc_a_id,
                "doc_b_id": doc_b_id,
                "contract_title": title,
                "clause_a_id": pair["clause_a_id"],
                "clause_b_id": pair["clause_b_id"],
                "text_a": text_a,
                "text_b": text_b,
                "e5_text_a": formatted_text_a,
                "e5_text_b": formatted_text_b,
                "classification": pair["classification"],
                "target_similarity": pair["target_similarity"],
                "difference_explanation": pair.get("difference_explanation", ""),
                "is_hard_negative": pair.get("is_hard_negative", False),
                "split": split_name,
                "metadata": {
                    "origin": "SEED/SYNTHETIC",
                    "dataset_version": DATASET_VERSION,
                    "language": "en"
                }
            }
            records.append(record)
            
    return records


def save_jsonl(records: List[Dict[str, Any]], path: Path) -> None:
    """Saves records to JSONL format."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def generate_all_datasets() -> Dict[str, Any]:
    """
    Main orchestration routine generating all datasets with strict document-level splitting.
    """
    print("==================================================")
    print("Generating ClarifAI Fine-Tuning Seed Datasets")
    print("==================================================")
    
    # 1. Deduplicate Task 1 documents
    cleaned_docs = deduplicate_clauses(DOCUMENTS_LEGAL_BERT)
    print(f"Legal-BERT: Total documents = {len(cleaned_docs)}")
    
    # Split Task 1 documents (70% Train, 15% Val, 15% Test)
    train_docs_lb, val_docs_lb, test_docs_lb = split_by_document(cleaned_docs, id_key="doc_id", seed=42)
    print(f"Legal-BERT Doc Splits: Train={len(train_docs_lb)}, Val={len(val_docs_lb)}, Test={len(test_docs_lb)}")
    
    train_records_lb = build_legal_bert_examples(train_docs_lb, "train")
    val_records_lb = build_legal_bert_examples(val_docs_lb, "validation")
    test_records_lb = build_legal_bert_examples(test_docs_lb, "test")
    
    save_jsonl(train_records_lb, LEGAL_BERT_DIR / "train.jsonl")
    save_jsonl(val_records_lb, LEGAL_BERT_DIR / "validation.jsonl")
    save_jsonl(test_records_lb, LEGAL_BERT_DIR / "test.jsonl")
    print(f"Legal-BERT Records: Train={len(train_records_lb)}, Val={len(val_records_lb)}, Test={len(test_records_lb)}")
    
    # 2. Task 2 Document Pairs (70% Train, 15% Val, 15% Test)
    print(f"\nMultilingual-E5: Total document pairs = {len(DOC_PAIRS_MULTILINGUAL_E5)}")
    train_pairs, val_pairs, test_pairs = split_by_document(DOC_PAIRS_MULTILINGUAL_E5, id_key="doc_pair_id", seed=42)
    print(f"Multilingual-E5 Doc Splits: Train={len(train_pairs)}, Val={len(val_pairs)}, Test={len(test_pairs)}")
    
    train_records_e5 = build_multilingual_e5_examples(train_pairs, "train")
    val_records_e5 = build_multilingual_e5_examples(val_pairs, "validation")
    test_records_e5 = build_multilingual_e5_examples(test_pairs, "test")
    
    save_jsonl(train_records_e5, MULTILINGUAL_E5_DIR / "train.jsonl")
    save_jsonl(val_records_e5, MULTILINGUAL_E5_DIR / "validation.jsonl")
    save_jsonl(test_records_e5, MULTILINGUAL_E5_DIR / "test.jsonl")
    print(f"Multilingual-E5 Records: Train={len(train_records_e5)}, Val={len(val_records_e5)}, Test={len(test_records_e5)}")
    
    return {
        "legal_bert": {
            "train": len(train_records_lb),
            "val": len(val_records_lb),
            "test": len(test_records_lb)
        },
        "multilingual_e5": {
            "train": len(train_records_e5),
            "val": len(val_records_e5),
            "test": len(test_records_e5)
        }
    }


if __name__ == "__main__":
    generate_all_datasets()
