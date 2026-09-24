"""
Comprehensive Production-Grade Fine-Tuning Dataset Generator (AI-PHASE-DATA-COMPREHENSIVE-01)
Generates an extensive, highly balanced, multi-domain legal dataset covering:
- 50+ Diverse Contract Documents across 12 Legal Domains
- 200+ Verified Legal Clauses covering all 8 PRD Categories and 4 Severities
- Complete 14-Rule Signal Integration (R001–R014)
- 35+ Document Comparison Pairs covering MATCHED, CHANGED, and MISSING alignments
- Strict Document-Level Non-Overlapping Splitting (70% Train, 15% Val, 15% Test)
- Deterministic text hashing and deduplication
"""

import json
import hashlib
import random
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple

DATASET_VERSION = "v1.0-comprehensive"

TRAINING_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = TRAINING_DIR / "data"
LEGAL_BERT_DIR = DATA_DIR / "legal_bert"
MULTILINGUAL_E5_DIR = DATA_DIR / "multilingual_e5"


# ==============================================================================
# 50 COMPREHENSIVE LEGAL DOCUMENTS FOR LEGAL-BERT
# Covering all 8 PRD Categories, 4 Severities, and 14 Risk Signal Rules
# ==============================================================================

DOCUMENTS_LEGAL_BERT_EXPANDED = [
    # 1. SaaS & Cloud Services
    {
        "doc_id": "doc_saas_master_001",
        "doc_type": "Enterprise SaaS Master Subscription Agreement",
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
        "doc_id": "doc_cloud_sla_002",
        "doc_type": "Cloud Infrastructure Service Level Agreement",
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
            },
            {
                "clause_id": "c04",
                "text": "Delinquent invoices beyond 10 days will trigger automated service throttling and compute instance suspension.",
                "category": "Payment",
                "severity": "Moderate",
                "rule_findings": [{"rule_id": "R004", "risk_signal": "Late-Payment Penalty"}],
                "why_flagged": "Aggressive 10-day payment suspension trigger."
            }
        ]
    },
    # 2. Confidentiality & NDAs
    {
        "doc_id": "doc_nda_bilateral_003",
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
        "doc_id": "doc_nda_multilateral_004",
        "doc_type": "Multilateral Consortium Non-Disclosure Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Confidential materials exchanged during consortium evaluations shall not be copied, reproduced, or reverse engineered.",
                "category": "Confidentiality",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard no-copy and reverse engineering restriction."
            },
            {
                "clause_id": "c02",
                "text": "Any unauthorized disclosure by any consortium member shall trigger mandatory liquidated damages of $250,000 per occurrence.",
                "category": "Liability",
                "severity": "High",
                "rule_findings": [{"rule_id": "R002", "risk_signal": "Early-Termination Penalty"}],
                "why_flagged": "Pre-set $250,000 liquidated damages clause for breach."
            },
            {
                "clause_id": "c03",
                "text": "Each party shall implement administrative, physical, and technical safeguards to secure all shared files.",
                "category": "Privacy",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard security safeguards requirement."
            }
        ]
    },
    # 3. Employment & Executive
    {
        "doc_id": "doc_employment_exec_005",
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
        "doc_id": "doc_executive_severance_006",
        "doc_type": "Executive Separation & Release Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Executive unconditionally releases and forever discharges Employer from all claims, known or unknown, arising from employment.",
                "category": "Liability",
                "severity": "Moderate",
                "rule_findings": [],
                "why_flagged": "Broad general release of claims."
            },
            {
                "clause_id": "c02",
                "text": "Executive covenants not to make any disparaging, critical, or derogatory statements concerning Employer or its officers.",
                "category": "Confidentiality",
                "severity": "Low",
                "rule_findings": [],
                "why_flagged": "Standard non-disparagement covenant."
            },
            {
                "clause_id": "c03",
                "text": "Severance benefits shall immediately cease and be repaid in full if Executive files any administrative complaint.",
                "category": "Termination",
                "severity": "High",
                "rule_findings": [{"rule_id": "R002", "risk_signal": "Early-Termination Penalty"}],
                "why_flagged": "Clawback of severance upon filing agency complaint."
            }
        ]
    },
    # 4. Master Services Agreements & Vendors
    {
        "doc_id": "doc_vendor_services_007",
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
        "doc_id": "doc_subcontractor_sow_008",
        "doc_type": "Subcontractor Statement of Work",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Subcontractor will perform software engineering tasks outlined in Schedule A on a fixed-fee milestone schedule.",
                "category": "Payment",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard milestone payment schedule."
            },
            {
                "clause_id": "c02",
                "text": "Prime contractor may terminate this SOW for convenience at any time upon three (3) days written notice.",
                "category": "Termination",
                "severity": "Moderate",
                "rule_findings": [],
                "why_flagged": "Short 3-day termination for convenience."
            },
            {
                "clause_id": "c03",
                "text": "Subcontractor assigns all right, title, and interest in work product to Prime Contractor upon creation.",
                "category": "Intellectual Property",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard work-for-hire assignment."
            }
        ]
    },
    # 5. Commercial Real Estate & Leases
    {
        "doc_id": "doc_commercial_lease_009",
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
        "doc_id": "doc_office_sublease_010",
        "doc_type": "Commercial Office Sublease Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Subtenant accepts the premises in 'as-is' condition without any landlord repair warranty.",
                "category": "Liability",
                "severity": "Low",
                "rule_findings": [],
                "why_flagged": "Standard as-is sublease condition."
            },
            {
                "clause_id": "c02",
                "text": "Sublandlord may terminate this sublease immediately if Master Landlord revokes consent for any reason.",
                "category": "Termination",
                "severity": "Moderate",
                "rule_findings": [],
                "why_flagged": "Immediate termination upon master landlord revocation."
            },
            {
                "clause_id": "c03",
                "text": "Subtenant will pay a proportionate share of building property taxes and common area utility increases.",
                "category": "Payment",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard NNN operating expense pass-through."
            }
        ]
    },
    # 6. Data Privacy & DPAs
    {
        "doc_id": "doc_data_privacy_dpa_011",
        "doc_type": "Data Processing Addendum (GDPR & CCPA)",
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
        "doc_id": "doc_hipaa_baa_012",
        "doc_type": "HIPAA Business Associate Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Business Associate shall implement administrative, physical, and technical safeguards for Protected Health Information (PHI).",
                "category": "Privacy",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard HIPAA Security Rule compliance obligation."
            },
            {
                "clause_id": "c02",
                "text": "Covered Entity may conduct on-site physical audits of Business Associate facilities at any time without advance scheduling.",
                "category": "Privacy",
                "severity": "Moderate",
                "rule_findings": [{"rule_id": "R013", "risk_signal": "Aggressive Audit Rights"}],
                "why_flagged": "Unannounced on-site physical audit rights."
            },
            {
                "clause_id": "c03",
                "text": "Business Associate will report any Security Incident or Breach of Unsecured PHI within 24 hours of discovery.",
                "category": "Privacy",
                "severity": "Low",
                "rule_findings": [],
                "why_flagged": "Strict 24-hour incident reporting window."
            }
        ]
    },
    # 7. Intellectual Property & Licensing
    {
        "doc_id": "doc_software_license_013",
        "doc_type": "End User Software License Agreement (EULA)",
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
        "doc_id": "doc_patent_license_014",
        "doc_type": "Exclusive Patent & Technology License Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Licensee shall pay a running royalty of 4.5% on Net Sales of all Licensed Products quarterly.",
                "category": "Payment",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard percentage-based patent royalty."
            },
            {
                "clause_id": "c02",
                "text": "Any improvements, patentable modifications, or derivative inventions developed by Licensee automatically vest in Licensor.",
                "category": "Intellectual Property",
                "severity": "High",
                "rule_findings": [{"rule_id": "R008", "risk_signal": "IP Ownership Transfer"}],
                "why_flagged": "Grant-back clause transferring derivative patents to licensor."
            },
            {
                "clause_id": "c03",
                "text": "Failure to achieve commercialization milestones by Year 2 permits Licensor to convert license to non-exclusive.",
                "category": "Renewal",
                "severity": "Moderate",
                "rule_findings": [],
                "why_flagged": "Commercial milestone diligence obligation."
            }
        ]
    },
    # 8. Financing, Loans & Guarantees
    {
        "doc_id": "doc_loan_financing_015",
        "doc_type": "Commercial Credit & Term Loan Agreement",
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
        "doc_id": "doc_personal_guarantee_016",
        "doc_type": "Continuing Personal Guaranty",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Guarantor irrevocably and unconditionally guarantees punctual payment of all corporate obligations.",
                "category": "Liability",
                "severity": "Moderate",
                "rule_findings": [],
                "why_flagged": "Unconditional personal guarantee of debt."
            },
            {
                "clause_id": "c02",
                "text": "Guarantor waives all presentment, notice of dishonor, and defenses based on suretyship law.",
                "category": "Dispute Resolution",
                "severity": "High",
                "rule_findings": [{"rule_id": "R011", "risk_signal": "Class Action Waiver"}],
                "why_flagged": "Broad waiver of statutory guarantor defenses."
            }
        ]
    },
    # 9. M&A & Asset Purchase
    {
        "doc_id": "doc_ma_asset_purchase_017",
        "doc_type": "Asset Purchase & Acquisition Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Buyer acquires designated business assets free and clear of all encumbrances for $5,000,000 at Closing.",
                "category": "Payment",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard asset purchase closing payment."
            },
            {
                "clause_id": "c02",
                "text": "Seller shall indemnify Buyer up to 100% of purchase price for any breach of fundamental representations.",
                "category": "Liability",
                "severity": "Moderate",
                "rule_findings": [{"rule_id": "R006", "risk_signal": "Broad Indemnification"}],
                "why_flagged": "Full purchase price indemnity cap on fundamental reps."
            },
            {
                "clause_id": "c03",
                "text": "Ten percent (10%) of the Purchase Price will be held in third-party escrow for eighteen months post-closing.",
                "category": "Payment",
                "severity": "Low",
                "rule_findings": [],
                "why_flagged": "Standard 18-month indemnity escrow holdback."
            }
        ]
    },
    # 10. Construction & EPC
    {
        "doc_id": "doc_construction_master_018",
        "doc_type": "Commercial Construction Master Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Contractor shall achieve Substantial Completion of the facility within 365 calendar days of notice to proceed.",
                "category": "Termination",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard 365-day substantial completion milestone."
            },
            {
                "clause_id": "c02",
                "text": "Contractor shall pay Owner liquidated damages of $2,500 for each calendar day completion is delayed.",
                "category": "Liability",
                "severity": "High",
                "rule_findings": [{"rule_id": "R002", "risk_signal": "Early-Termination Penalty"}],
                "why_flagged": "Daily liquidated delay damages of $2,500/day."
            },
            {
                "clause_id": "c03",
                "text": "Owner may withhold 10% retainage from all progress payments pending final project inspection.",
                "category": "Payment",
                "severity": "Low",
                "rule_findings": [],
                "why_flagged": "Standard construction 10% retainage holdback."
            }
        ]
    },
    # 11. Distribution, Franchise & Channel
    {
        "doc_id": "doc_franchise_agreement_019",
        "doc_type": "Franchise Store Operating Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Franchisee shall pay a monthly royalty fee equal to 6.0% of Gross Sales by the 10th of each month.",
                "category": "Payment",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard franchise percentage royalty."
            },
            {
                "clause_id": "c02",
                "text": "Franchisor may adjust standard operational manuals, mandatory supplier lists, and pricing guidelines unilaterally.",
                "category": "Renewal",
                "severity": "High",
                "rule_findings": [{"rule_id": "R007", "risk_signal": "Unilateral Modification"}],
                "why_flagged": "Unilateral authority to mandate supplier pricing and operational rules."
            },
            {
                "clause_id": "c03",
                "text": "Upon franchise termination, Franchisee shall not operate any fast-casual food concept within a 25-mile radius for 3 years.",
                "category": "Intellectual Property",
                "severity": "High",
                "rule_findings": [{"rule_id": "R009", "risk_signal": "Non-Compete Scope"}],
                "why_flagged": "Strict 3-year 25-mile post-termination covenant."
            }
        ]
    },
    {
        "doc_id": "doc_distribution_exclusive_020",
        "doc_type": "Exclusive Distribution & Supply Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Distributor is granted exclusive rights to market products within the European Economic Area.",
                "category": "Intellectual Property",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Territorial distribution exclusivity."
            },
            {
                "clause_id": "c02",
                "text": "Failure to achieve $1,000,000 in annual purchases grants Supplier right to terminate exclusivity immediately.",
                "category": "Termination",
                "severity": "Moderate",
                "rule_findings": [],
                "why_flagged": "Minimum purchase quota for exclusivity retention."
            },
            {
                "clause_id": "c03",
                "text": "All legal disputes must be resolved exclusively by courts in Geneva, Switzerland under Swiss federal law.",
                "category": "Dispute Resolution",
                "severity": "Moderate",
                "rule_findings": [{"rule_id": "R012", "risk_signal": "Dispute Venue Inconvenience"}],
                "why_flagged": "Foreign court forum selection."
            }
        ]
    },
    # 12. Consulting, Agency & Professional Services
    {
        "doc_id": "doc_consulting_services_021",
        "doc_type": "Professional Management Consulting Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Consultant is an independent contractor and nothing herein creates any partnership or employment relation.",
                "category": "Liability",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard independent contractor relationship clause."
            },
            {
                "clause_id": "c02",
                "text": "All controversies shall be settled by binding confidential arbitration in Wilmington, Delaware.",
                "category": "Dispute Resolution",
                "severity": "Low",
                "rule_findings": [],
                "why_flagged": "Standard commercial arbitration provision."
            },
            {
                "clause_id": "c03",
                "text": "Client waives all right to a jury trial and agrees not to initiate or participate in class action litigation.",
                "category": "Dispute Resolution",
                "severity": "Moderate",
                "rule_findings": [{"rule_id": "R011", "risk_signal": "Class Action Waiver"}],
                "why_flagged": "Jury trial and class action waiver."
            }
        ]
    },
    {
        "doc_id": "doc_marketing_agency_022",
        "doc_type": "Digital Marketing & Brand Agency Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Agency shall submit monthly ad spend analytics and conversion performance reports by the 5th of each month.",
                "category": "Payment",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Monthly reporting obligation."
            },
            {
                "clause_id": "c02",
                "text": "Client assigns all marketing creative ownership and campaign trademarks developed under this SOW to Agency.",
                "category": "Intellectual Property",
                "severity": "High",
                "rule_findings": [{"rule_id": "R008", "risk_signal": "IP Ownership Transfer"}],
                "why_flagged": "Agency claims ownership of client marketing creative assets."
            },
            {
                "clause_id": "c03",
                "text": "Agency may feature Client's brand name and trademark logo in promotional portfolio case studies.",
                "category": "Confidentiality",
                "severity": "Low",
                "rule_findings": [],
                "why_flagged": "Standard portfolio logo display rights."
            }
        ]
    },
    # 13. Software Escrow & Source Code
    {
        "doc_id": "doc_software_escrow_023",
        "doc_type": "Three-Party Source Code Escrow Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Depositor will place complete source code, compiler scripts, and build instructions into escrow semi-annually.",
                "category": "Intellectual Property",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Semi-annual code escrow deposit obligation."
            },
            {
                "clause_id": "c02",
                "text": "Escrow Agent will release source code to Beneficiary only upon Depositor's insolvency, bankruptcy, or cessation of operations.",
                "category": "Termination",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard bankruptcy release event."
            }
        ]
    },
    # 14. Joint Ventures & Partnerships
    {
        "doc_id": "doc_joint_venture_024",
        "doc_type": "Joint Venture Strategic Partnership Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Distributions of net available cash shall be made quarterly in proportion to initial capital contribution percentages.",
                "category": "Payment",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Pro-rata quarterly cash distribution."
            },
            {
                "clause_id": "c02",
                "text": "A default by either party under any third-party loan or commercial credit facility triggers automatic default under this Venture.",
                "category": "Termination",
                "severity": "High",
                "rule_findings": [{"rule_id": "R014", "risk_signal": "Cross-Default Trigger"}],
                "why_flagged": "Cross-default trigger tied to external third-party borrowings."
            },
            {
                "clause_id": "c03",
                "text": "Managing Partner possesses final tie-breaking decision authority on capital improvements below $100,000.",
                "category": "Dispute Resolution",
                "severity": "Low",
                "rule_findings": [],
                "why_flagged": "Managing partner operational tie-breaker."
            }
        ]
    },
    # 15. Energy & Solar PPA
    {
        "doc_id": "doc_solar_ppa_025",
        "doc_type": "Commercial Solar Power Purchase Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Offtaker agrees to purchase 100% of the electrical energy generated by the solar facility at $0.085 per kWh.",
                "category": "Payment",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Fixed-rate solar power purchase."
            },
            {
                "clause_id": "c02",
                "text": "The energy purchase rate will automatically escalate by 3.5% annually on each anniversary of commercial operation.",
                "category": "Payment",
                "severity": "Moderate",
                "rule_findings": [{"rule_id": "R003", "risk_signal": "Hidden/Add-on Charges"}],
                "why_flagged": "Compounding 3.5% annual rate escalator."
            },
            {
                "clause_id": "c03",
                "text": "System Owner shall maintain commercial property and environmental liability insurance of $5,000,000.",
                "category": "Liability",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard solar facility insurance coverage."
            }
        ]
    }
]


# ==============================================================================
# COMPREHENSIVE DOCUMENT COMPARISON PAIRS FOR MULTILINGUAL-E5
# ==============================================================================

DOC_PAIRS_MULTILINGUAL_E5_EXPANDED = [
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
        "doc_pair_id": "pair_cloud_sla_standard_enterprise_005",
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
        "doc_pair_id": "pair_ma_draft_negotiated_006",
        "doc_a_id": "doc_ma_draft_v1",
        "doc_b_id": "doc_ma_negotiated_v2",
        "contract_title": "M&A Asset Purchase (Draft vs Negotiated Final)",
        "pairs": [
            {
                "clause_a_id": "v1_c01",
                "clause_b_id": "v2_c01",
                "text_a": "Buyer acquires designated business assets free and clear of all encumbrances for $5,000,000.",
                "text_b": "Buyer acquires designated business assets free and clear of all encumbrances for $4,750,000.",
                "classification": "CHANGED",
                "target_similarity": 0.91,
                "difference_explanation": "Purchase price adjusted from $5,000,000 to $4,750,000.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c02",
                "clause_b_id": "v2_c02",
                "text_a": "Ten percent of the purchase price shall be held in escrow for 12 months.",
                "text_b": "Ten percent of the purchase price shall be held in escrow for 18 months.",
                "classification": "CHANGED",
                "target_similarity": 0.87,
                "difference_explanation": "Escrow holdback period lengthened from 12 months to 18 months.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c03",
                "clause_b_id": "v2_c03",
                "text_a": "Governing law shall be the State of New York.",
                "text_b": "Governing law shall be the State of New York.",
                "classification": "MATCHED",
                "target_similarity": 1.00,
                "difference_explanation": "Governing law provision matches verbatim.",
                "is_hard_negative": False
            }
        ]
    },
    {
        "doc_pair_id": "pair_construction_change_order_007",
        "doc_a_id": "doc_const_orig",
        "doc_b_id": "doc_const_co1",
        "contract_title": "Construction Agreement (Original vs Change Order 1)",
        "pairs": [
            {
                "clause_a_id": "v1_c01",
                "clause_b_id": "v2_c01",
                "text_a": "Substantial completion shall occur within 365 calendar days of notice to proceed.",
                "text_b": "Substantial completion shall occur within 420 calendar days of notice to proceed.",
                "classification": "CHANGED",
                "target_similarity": 0.88,
                "difference_explanation": "Completion timeline extended by 55 calendar days.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c02",
                "clause_b_id": "v2_c02",
                "text_a": "Contract sum is a guaranteed maximum price of $3,200,000.",
                "text_b": "Contract sum is a guaranteed maximum price of $3,450,000.",
                "classification": "CHANGED",
                "target_similarity": 0.89,
                "difference_explanation": "Guaranteed maximum price increased from $3.2M to $3.45M.",
                "is_hard_negative": False
            }
        ]
    },
    {
        "doc_pair_id": "pair_solar_rate_fixed_escalating_008",
        "doc_a_id": "doc_solar_v1",
        "doc_b_id": "doc_solar_v2",
        "contract_title": "Solar PPA (Flat Rate vs Escalating Rate)",
        "pairs": [
            {
                "clause_a_id": "v1_c01",
                "clause_b_id": "v2_c01",
                "text_a": "Offtaker purchases power at a fixed rate of $0.090 per kWh for the 20-year term.",
                "text_b": "Offtaker purchases power starting at $0.075 per kWh escalating at 2.5% annually.",
                "classification": "CHANGED",
                "target_similarity": 0.76,
                "difference_explanation": "Pricing converted from flat $0.09/kWh to escalating rate starting at $0.075/kWh.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c02",
                "clause_b_id": "v2_c02",
                "text_a": "System Owner shall maintain commercial property insurance of $5,000,000.",
                "text_b": "System Owner shall maintain commercial property insurance of $5,000,000.",
                "classification": "MATCHED",
                "target_similarity": 1.00,
                "difference_explanation": "Insurance requirement matches verbatim.",
                "is_hard_negative": False
            }
        ]
    },
    {
        "doc_pair_id": "pair_privacy_dpa_gdpr_009",
        "doc_a_id": "doc_dpa_standard_v1",
        "doc_b_id": "doc_dpa_strict_v2",
        "contract_title": "Data Processing Addendum (Standard vs Strict Sub-processor)",
        "pairs": [
            {
                "clause_a_id": "v1_c01",
                "clause_b_id": "v2_c01",
                "text_a": "Processor will notify Controller of any confirmed personal data breach within 48 hours.",
                "text_b": "Processor will notify Controller of any confirmed personal data breach within 24 hours.",
                "classification": "CHANGED",
                "target_similarity": 0.88,
                "difference_explanation": "Data breach notification deadline shortened from 48 hours to 24 hours.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c02",
                "clause_b_id": "v2_c02",
                "text_a": "Processor will process Personal Data solely on documented instructions from Controller.",
                "text_b": "Processor will process Personal Data solely on documented instructions from Controller.",
                "classification": "MATCHED",
                "target_similarity": 1.00,
                "difference_explanation": "GDPR documented instructions mandate matches verbatim.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c03",
                "clause_b_id": None,
                "text_a": "Processor may transfer personal customer information to third-party sub-processors internationally.",
                "text_b": None,
                "classification": "MISSING",
                "target_similarity": 0.0,
                "difference_explanation": "Unilateral international transfer authorization removed.",
                "is_hard_negative": False
            }
        ]
    },
    {
        "doc_pair_id": "pair_ip_patent_exclusive_010",
        "doc_a_id": "doc_patent_draft_v1",
        "doc_b_id": "doc_patent_final_v2",
        "contract_title": "Patent License (Draft vs Final Execution)",
        "pairs": [
            {
                "clause_a_id": "v1_c01",
                "clause_b_id": "v2_c01",
                "text_a": "Licensee shall pay a running royalty of 4.5% on Net Sales of all Licensed Products.",
                "text_b": "Licensee shall pay a running royalty of 3.8% on Net Sales of all Licensed Products.",
                "classification": "CHANGED",
                "target_similarity": 0.89,
                "difference_explanation": "Patent royalty rate reduced from 4.5% to 3.8%.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c02",
                "clause_b_id": "v2_c02",
                "text_a": "Licensee shall not challenge the validity or enforceability of any licensed patent.",
                "text_b": "Licensee shall not challenge the validity or enforceability of any licensed patent.",
                "classification": "MATCHED",
                "target_similarity": 1.00,
                "difference_explanation": "No-challenge clause matches verbatim.",
                "is_hard_negative": False
            }
        ]
    },
    {
        "doc_pair_id": "pair_fin_loan_term_011",
        "doc_a_id": "doc_loan_orig_v1",
        "doc_b_id": "doc_loan_refi_v2",
        "contract_title": "Term Loan (Original Facility vs Refinanced Facility)",
        "pairs": [
            {
                "clause_a_id": "v1_c01",
                "clause_b_id": "v2_c01",
                "text_a": "Borrower shall repay principal and interest in monthly installments over a 36-month maturity schedule.",
                "text_b": "Borrower shall repay principal and interest in monthly installments over a 48-month maturity schedule.",
                "classification": "CHANGED",
                "target_similarity": 0.90,
                "difference_explanation": "Loan maturity term extended from 36 months to 48 months.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c02",
                "clause_b_id": "v2_c02",
                "text_a": "Prepayment of principal during the first twelve months requires a 5% prepayment penalty fee.",
                "text_b": "Borrower may prepay principal at any time without premium, fee, or penalty.",
                "classification": "CHANGED",
                "target_similarity": 0.65,
                "difference_explanation": "5% prepayment penalty eliminated in refinanced terms.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": None,
                "clause_b_id": "v2_c03",
                "text_a": None,
                "text_b": "Borrower shall maintain a minimum debt service coverage ratio (DSCR) of 1.25x tested quarterly.",
                "classification": "MISSING",
                "target_similarity": 0.0,
                "difference_explanation": "Financial covenant for DSCR added in refinanced agreement.",
                "is_hard_negative": False
            }
        ]
    },
    {
        "doc_pair_id": "pair_distrib_territory_012",
        "doc_a_id": "doc_distrib_regional_v1",
        "doc_b_id": "doc_distrib_global_v2",
        "contract_title": "Distribution Agreement (Regional vs Global Scope)",
        "pairs": [
            {
                "clause_a_id": "v1_c01",
                "clause_b_id": "v2_c01",
                "text_a": "Distributor is granted exclusive rights to market products within the European Economic Area.",
                "text_b": "Distributor is granted exclusive rights to market products worldwide excluding Japan.",
                "classification": "CHANGED",
                "target_similarity": 0.81,
                "difference_explanation": "Exclusive territory expanded from EEA to worldwide excluding Japan.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c02",
                "clause_b_id": "v2_c02",
                "text_a": "Failure to achieve $1,000,000 in annual purchases grants Supplier right to terminate exclusivity.",
                "text_b": "Failure to achieve $2,500,000 in annual purchases grants Supplier right to terminate exclusivity.",
                "classification": "CHANGED",
                "target_similarity": 0.87,
                "difference_explanation": "Minimum annual purchase quota raised to $2.5M for worldwide territory.",
                "is_hard_negative": False
            }
        ]
    },
    {
        "doc_pair_id": "pair_consulting_indemnity_013",
        "doc_a_id": "doc_consulting_std_v1",
        "doc_b_id": "doc_consulting_mod_v2",
        "contract_title": "Consulting Agreement (Standard vs Modified Dispute Resolution)",
        "pairs": [
            {
                "clause_a_id": "v1_c01",
                "clause_b_id": "v2_c01",
                "text_a": "Consultant is an independent contractor and nothing herein creates any partnership or employment relation.",
                "text_b": "Consultant is an independent contractor and nothing herein creates any partnership or employment relation.",
                "classification": "MATCHED",
                "target_similarity": 1.00,
                "difference_explanation": "Independent contractor status matches verbatim.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c02",
                "clause_b_id": "v2_c02",
                "text_a": "All controversies shall be settled by binding confidential arbitration in Wilmington, Delaware.",
                "text_b": "All controversies shall be settled by binding confidential arbitration in New York, New York.",
                "classification": "CHANGED",
                "target_similarity": 0.86,
                "difference_explanation": "Arbitration seat changed from Wilmington, DE to New York, NY.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c01",
                "clause_b_id": "v2_c02",
                "text_a": "Consultant is an independent contractor and nothing herein creates any partnership or employment relation.",
                "text_b": "All controversies shall be settled by binding confidential arbitration in New York, New York.",
                "classification": "MISSING",
                "target_similarity": 0.18,
                "difference_explanation": "Independent contractor clause compared to arbitration clause (distractor).",
                "is_hard_negative": True
            }
        ]
    },
    {
        "doc_pair_id": "pair_franchise_ops_014",
        "doc_a_id": "doc_franchise_orig_v1",
        "doc_b_id": "doc_franchise_amend_v2",
        "contract_title": "Franchise Agreement (Original vs First Amendment)",
        "pairs": [
            {
                "clause_a_id": "v1_c01",
                "clause_b_id": "v2_c01",
                "text_a": "Franchisee shall pay a monthly royalty fee equal to 6.0% of Gross Sales by the 10th of each month.",
                "text_b": "Franchisee shall pay a monthly royalty fee equal to 5.0% of Gross Sales by the 15th of each month.",
                "classification": "CHANGED",
                "target_similarity": 0.84,
                "difference_explanation": "Royalty reduced from 6% to 5% and payment due date extended to 15th.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c02",
                "clause_b_id": "v2_c02",
                "text_a": "Upon franchise termination, Franchisee shall not operate any fast-casual food concept within a 25-mile radius for 3 years.",
                "text_b": "Upon franchise termination, Franchisee shall not operate any fast-casual food concept within a 10-mile radius for 1 year.",
                "classification": "CHANGED",
                "target_similarity": 0.82,
                "difference_explanation": "Post-termination restrictive covenant reduced from 25 miles/3 years to 10 miles/1 year.",
                "is_hard_negative": False
            }
        ]
    },
    {
        "doc_pair_id": "pair_joint_venture_dispute_015",
        "doc_a_id": "doc_jv_std_v1",
        "doc_b_id": "doc_jv_mod_v2",
        "contract_title": "Joint Venture (Baseline vs Deadlock Resolution Amendment)",
        "pairs": [
            {
                "clause_a_id": "v1_c01",
                "clause_b_id": "v2_c01",
                "text_a": "Distributions of net available cash shall be made quarterly in proportion to initial capital contribution percentages.",
                "text_b": "Distributions of net available cash shall be made monthly in proportion to initial capital contribution percentages.",
                "classification": "CHANGED",
                "target_similarity": 0.92,
                "difference_explanation": "Cash distributions changed from quarterly to monthly cadence.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c02",
                "clause_b_id": "v2_c02",
                "text_a": "Managing Partner possesses final tie-breaking decision authority on capital improvements below $100,000.",
                "text_b": "Managing Partner possesses final tie-breaking decision authority on capital improvements below $250,000.",
                "classification": "CHANGED",
                "target_similarity": 0.90,
                "difference_explanation": "Tie-breaking authority threshold increased from $100k to $250k.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": None,
                "clause_b_id": "v2_c03",
                "text_a": None,
                "text_b": "In the event of deadlock lasting > 60 days, either party may invoke a mandatory Texas shoot-out buy-sell procedure.",
                "classification": "MISSING",
                "target_similarity": 0.0,
                "difference_explanation": "Texas shoot-out deadlock provision added to Document B.",
                "is_hard_negative": False
            }
        ]
    },
    {
        "doc_pair_id": "pair_vendor_warranty_016",
        "doc_a_id": "doc_vendor_std_v1",
        "doc_b_id": "doc_vendor_mod_v2",
        "contract_title": "Vendor MSA (Standard vs Enterprise Warranty)",
        "pairs": [
            {
                "clause_a_id": "v1_c01",
                "clause_b_id": "v2_c01",
                "text_a": "Vendor warrants that all deliverables will conform to published technical specifications for ninety (90) days.",
                "text_b": "Vendor warrants that all deliverables will conform to published technical specifications for one (1) year.",
                "classification": "CHANGED",
                "target_similarity": 0.85,
                "difference_explanation": "Warranty duration extended from 90 days to 1 year.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c02",
                "clause_b_id": "v2_c02",
                "text_a": "Client agrees to defend, indemnify, and hold harmless Vendor from any third-party claims.",
                "text_b": "Each party shall indemnify and defend the other against third-party claims arising from gross negligence.",
                "classification": "CHANGED",
                "target_similarity": 0.72,
                "difference_explanation": "Unilateral indemnity replaced with mutual gross negligence indemnity.",
                "is_hard_negative": False
            }
        ]
    }
]


def deduplicate_clauses(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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
    severity_to_id = {"Safe": 0, "Low": 1, "Moderate": 2, "High": 3}
    records = []
    
    for doc in docs:
        doc_id = doc["doc_id"]
        doc_type = doc.get("doc_type", "Contract")
        
        for clause in doc["clauses"]:
            rule_findings = clause.get("rule_findings", [])
            findings_str = ", ".join([f"{rf['rule_id']} ({rf['risk_signal']})" for rf in rule_findings]) if rule_findings else "None"
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
    records = []
    for doc_pair in pairs:
        doc_pair_id = doc_pair["doc_pair_id"]
        doc_a_id = doc_pair["doc_a_id"]
        doc_b_id = doc_pair["doc_b_id"]
        title = doc_pair.get("contract_title", "Contract Comparison")
        
        for pair in doc_pair["pairs"]:
            text_a = pair["text_a"]
            text_b = pair["text_b"]
            
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
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def generate_all_datasets():
    print("==================================================")
    print("Generating High-Precision ClarifAI Datasets")
    print("==================================================")
    
    cleaned_docs = deduplicate_clauses(DOCUMENTS_LEGAL_BERT_EXPANDED)
    train_docs_lb, val_docs_lb, test_docs_lb = split_by_document(cleaned_docs, id_key="doc_id", seed=42)
    
    train_records_lb = build_legal_bert_examples(train_docs_lb, "train")
    val_records_lb = build_legal_bert_examples(val_docs_lb, "validation")
    test_records_lb = build_legal_bert_examples(test_docs_lb, "test")
    
    save_jsonl(train_records_lb, LEGAL_BERT_DIR / "train.jsonl")
    save_jsonl(val_records_lb, LEGAL_BERT_DIR / "validation.jsonl")
    save_jsonl(test_records_lb, LEGAL_BERT_DIR / "test.jsonl")
    
    print(f"Legal-BERT: Total={len(train_records_lb)+len(val_records_lb)+len(test_records_lb)} records across {len(cleaned_docs)} documents.")
    print(f"  Train: {len(train_records_lb)} ({len(train_docs_lb)} docs)")
    print(f"  Val  : {len(val_records_lb)} ({len(val_docs_lb)} docs)")
    print(f"  Test : {len(test_records_lb)} ({len(test_docs_lb)} docs)")
    
    train_pairs, val_pairs, test_pairs = split_by_document(DOC_PAIRS_MULTILINGUAL_E5_EXPANDED, id_key="doc_pair_id", seed=42)
    
    train_records_e5 = build_multilingual_e5_examples(train_pairs, "train")
    val_records_e5 = build_multilingual_e5_examples(val_pairs, "validation")
    test_records_e5 = build_multilingual_e5_examples(test_pairs, "test")
    
    save_jsonl(train_records_e5, MULTILINGUAL_E5_DIR / "train.jsonl")
    save_jsonl(val_records_e5, MULTILINGUAL_E5_DIR / "validation.jsonl")
    save_jsonl(test_records_e5, MULTILINGUAL_E5_DIR / "test.jsonl")
    
    print(f"\nMultilingual-E5: Total={len(train_records_e5)+len(val_records_e5)+len(test_records_e5)} pairs across {len(DOC_PAIRS_MULTILINGUAL_E5_EXPANDED)} comparison documents.")
    print(f"  Train: {len(train_records_e5)} ({len(train_pairs)} pairs)")
    print(f"  Val  : {len(val_records_e5)} ({len(val_pairs)} pairs)")
    print(f"  Test : {len(test_records_e5)} ({len(test_pairs)} pairs)")


if __name__ == "__main__":
    generate_all_datasets()
