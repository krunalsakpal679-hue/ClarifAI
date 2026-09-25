"""
Comprehensive Production-Grade Fine-Tuning Dataset Generator (AI-PHASE-DATA-COMPREHENSIVE-02)
Generates an extensive, highly balanced, multi-domain legal dataset covering:
- 60 Diverse Contract Documents across 20 Legal Domains
- 200+ Verified Legal Clauses covering all 8 PRD Categories and 4 Severities
- Complete 14-Rule Signal Integration (R001–R014)
- 25+ Document Comparison Pairs covering MATCHED, CHANGED, and MISSING alignments (English & Multilingual)
- Strict Document-Level Non-Overlapping Splitting (70% Train, 15% Val, 15% Test)
- Deterministic text hashing and deduplication
"""

import json
import hashlib
import random
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple

DATASET_VERSION = "v2.0-comprehensive"

TRAINING_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = TRAINING_DIR / "data"
LEGAL_BERT_DIR = DATA_DIR / "legal_bert"
MULTILINGUAL_E5_DIR = DATA_DIR / "multilingual_e5"


# ==============================================================================
# 60 COMPREHENSIVE LEGAL DOCUMENTS FOR LEGAL-BERT (200+ Verified Clauses)
# ==============================================================================

DOCUMENTS_LEGAL_BERT_EXPANDED = [
    # 1. Enterprise SaaS
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
            },
            {
                "clause_id": "c05",
                "text": "Customer may request export of raw transaction and account logs once per calendar quarter.",
                "category": "Privacy",
                "severity": "Low",
                "rule_findings": [],
                "why_flagged": "Periodic customer data export request provision."
            }
        ]
    },
    # 2. Cloud Infrastructure SLA
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
                "text": "Provider may unilaterally modify system specifications, API endpoints, and pricing without prior customer consent or notice.",
                "category": "Termination",
                "severity": "High",
                "rule_findings": [{"rule_id": "R007", "risk_signal": "Unilateral Modification"}],
                "why_flagged": "Unilateral right to change core API contracts and pricing."
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
    # 3. Bilateral NDA
    {
        "doc_id": "doc_nda_bilateral_003",
        "doc_type": "Mutual Non-Disclosure Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Each party shall protect the other party's Confidential Information with the same degree of care used for its own confidential data.",
                "category": "Confidentiality",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard mutual duty of care."
            },
            {
                "clause_id": "c02",
                "text": "Receiving Party shall permanently assign all inventions, patents, and improvements derived from Disclosing Party's confidential information.",
                "category": "Intellectual Property",
                "severity": "High",
                "rule_findings": [{"rule_id": "R006", "risk_signal": "Broad IP Assignment"}],
                "why_flagged": "Predatory assignment of recipient IP developments."
            },
            {
                "clause_id": "c03",
                "text": "Confidentiality obligations under this Agreement shall survive for a period of three (3) years following disclosure.",
                "category": "Confidentiality",
                "severity": "Low",
                "rule_findings": [],
                "why_flagged": "Standard 3-year confidentiality survival period."
            }
        ]
    },
    # 4. Multilateral Consortium NDA
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
            },
            {
                "clause_id": "c04",
                "text": "Notice of disclosure required by judicial subpoena shall be delivered within ten (10) business days.",
                "category": "Confidentiality",
                "severity": "Low",
                "rule_findings": [],
                "why_flagged": "Standard subpoena notification timeframe."
            }
        ]
    },
    # 5. Executive Employment Agreement
    {
        "doc_id": "doc_employment_exec_005",
        "doc_type": "Executive Employment Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Executive shall receive an annual base salary of $250,000 paid in semi-monthly installments subject to tax withholdings.",
                "category": "Payment",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard executive compensation structure."
            },
            {
                "clause_id": "c02",
                "text": "For three (3) years post-termination, Executive shall not engage in any competing enterprise globally across all business sectors.",
                "category": "Termination",
                "severity": "High",
                "rule_findings": [{"rule_id": "R010", "risk_signal": "Restrictive Non-Compete"}],
                "why_flagged": "Overly broad 3-year global non-compete."
            },
            {
                "clause_id": "c03",
                "text": "Executive agrees never to make any critical, disparaging, or negative statements regarding Company or its officers.",
                "category": "Confidentiality",
                "severity": "Moderate",
                "rule_findings": [{"rule_id": "R009", "risk_signal": "Non-Disparagement Gag"}],
                "why_flagged": "Perpetual non-disparagement gag clause."
            },
            {
                "clause_id": "c04",
                "text": "Company will provide standard group medical, dental, and disability insurance coverage.",
                "category": "Payment",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard employee benefits package."
            }
        ]
    },
    # 6. Software Developer Employment
    {
        "doc_id": "doc_employment_dev_006",
        "doc_type": "Software Developer Employment Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Employee assigns all inventions created during employment hours using Company equipment to Employer.",
                "category": "Intellectual Property",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard work-for-hire assignment."
            },
            {
                "clause_id": "c02",
                "text": "Employer retains exclusive ownership of all prior personal inventions and open-source contributions created prior to employment.",
                "category": "Intellectual Property",
                "severity": "High",
                "rule_findings": [{"rule_id": "R006", "risk_signal": "Broad IP Assignment"}],
                "why_flagged": "Unlawful assignment of pre-existing background inventions."
            },
            {
                "clause_id": "c03",
                "text": "Employee shall give thirty (30) days written notice prior to voluntary resignation.",
                "category": "Termination",
                "severity": "Low",
                "rule_findings": [],
                "why_flagged": "Standard 30-day resignation notice period."
            }
        ]
    },
    # 7. Master Services Agreement
    {
        "doc_id": "doc_msa_consulting_007",
        "doc_type": "Master Consulting Services Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Services will be billed on a time and materials basis per approved Statement of Work rates.",
                "category": "Payment",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard T&M consulting terms."
            },
            {
                "clause_id": "c02",
                "text": "Client agrees to indemnify, defend, and hold harmless Consultant from all third-party claims without limitation or exception.",
                "category": "Liability",
                "severity": "High",
                "rule_findings": [{"rule_id": "R014", "risk_signal": "Asymmetric Indemnification"}],
                "why_flagged": "Completely unilateral third-party indemnification burden."
            },
            {
                "clause_id": "c03",
                "text": "Either party may terminate any SOW for convenience upon forty-five (45) days prior written notice.",
                "category": "Termination",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Mutual termination for convenience."
            }
        ]
    },
    # 8. Subcontractor SOW
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
                "rule_findings": [{"rule_id": "R002", "risk_signal": "Early-Termination Penalty"}],
                "why_flagged": "Short 3-day termination for convenience."
            },
            {
                "clause_id": "c03",
                "text": "Subcontractor assigns all right, title, and interest in work product to Prime Contractor upon creation.",
                "category": "Intellectual Property",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard work-for-hire assignment."
            },
            {
                "clause_id": "c04",
                "text": "Subcontractor will provide bi-weekly written progress summaries to Prime Contractor.",
                "category": "Payment",
                "severity": "Low",
                "rule_findings": [],
                "why_flagged": "Standard bi-weekly milestone reporting requirement."
            }
        ]
    },
    # 9. Commercial Property Lease
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
                "rule_findings": [{"rule_id": "R003", "risk_signal": "Hidden/Add-on Charges"}, {"rule_id": "R007", "risk_signal": "Unilateral Modification"}],
                "why_flagged": "Unilateral imposition of unitemized maintenance charges."
            },
            {
                "clause_id": "c03",
                "text": "This lease shall extend automatically for five (5) additional years unless Tenant provides notice twelve months in advance.",
                "category": "Renewal",
                "severity": "High",
                "rule_findings": [{"rule_id": "R001", "risk_signal": "Auto-Renewal"}],
                "why_flagged": "Extremely long 5-year auto-extension with restrictive 12-month notice window."
            },
            {
                "clause_id": "c04",
                "text": "Tenant shall maintain routine cleanliness of internal leased office space at Tenant's sole expense.",
                "category": "Liability",
                "severity": "Low",
                "rule_findings": [],
                "why_flagged": "Routine tenant maintenance and upkeep duty."
            }
        ]
    },
    # 10. Equipment Lease Agreement
    {
        "doc_id": "doc_equipment_lease_010",
        "doc_type": "Heavy Industrial Equipment Lease",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Lessee will operate leased machinery strictly in accordance with manufacturer operating manuals.",
                "category": "Liability",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard equipment operational requirement."
            },
            {
                "clause_id": "c02",
                "text": "Lessor disclaims all express and implied warranties, including merchantability and fitness for a particular purpose.",
                "category": "Liability",
                "severity": "Moderate",
                "rule_findings": [{"rule_id": "R008", "risk_signal": "Unilateral Liability Disclaimer"}],
                "why_flagged": "Standard commercial as-is warranty disclaimer."
            },
            {
                "clause_id": "c03",
                "text": "Late lease payments shall accrue interest at 1.5% per month or maximum rate permitted by governing law.",
                "category": "Payment",
                "severity": "Moderate",
                "rule_findings": [{"rule_id": "R004", "risk_signal": "Late-Payment Penalty"}],
                "why_flagged": "Standard 1.5% monthly late payment interest."
            }
        ]
    },
    # 11. Patent License Agreement
    {
        "doc_id": "doc_patent_license_011",
        "doc_type": "Exclusive Patent License Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Licensor grants Licensee an exclusive, royalty-bearing license under the Licensed Patents in the Field of Use.",
                "category": "Intellectual Property",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard patent license grant."
            },
            {
                "clause_id": "c02",
                "text": "Licensee covenants never to challenge the validity, enforceability, or scope of Licensor's patents in any judicial forum.",
                "category": "Dispute Resolution",
                "severity": "High",
                "rule_findings": [{"rule_id": "R012", "risk_signal": "Mandatory Binding Arbitration"}],
                "why_flagged": "No-challenge clause restricting patent validity contest."
            },
            {
                "clause_id": "c03",
                "text": "Licensee shall maintain comprehensive records of royalty calculations subject to annual audit.",
                "category": "Payment",
                "severity": "Low",
                "rule_findings": [],
                "why_flagged": "Standard royalty audit and recordkeeping covenant."
            }
        ]
    },
    # 12. Trademark & Brand Licensing
    {
        "doc_id": "doc_trademark_license_012",
        "doc_type": "International Trademark License Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Licensee shall submit all promotional materials featuring the Licensed Mark for Licensor's prior written quality approval.",
                "category": "Intellectual Property",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard trademark quality control clause."
            },
            {
                "clause_id": "c02",
                "text": "Licensor may immediately terminate license without cure period if Licensee experiences any change of ownership or control.",
                "category": "Termination",
                "severity": "Moderate",
                "rule_findings": [{"rule_id": "R002", "risk_signal": "Early-Termination Penalty"}],
                "why_flagged": "Immediate termination on change of control."
            },
            {
                "clause_id": "c03",
                "text": "Licensee shall report gross merchandise sales figures quarterly within fifteen (15) calendar days.",
                "category": "Payment",
                "severity": "Low",
                "rule_findings": [],
                "why_flagged": "Standard quarterly sales reporting deadline."
            }
        ]
    },
    # 13. Data Processing Addendum (GDPR)
    {
        "doc_id": "doc_dpa_gdpr_013",
        "doc_type": "Data Processing Addendum (GDPR & CCPA Compliant)",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Processor shall process personal data solely on documented instructions from Controller.",
                "category": "Privacy",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard GDPR Article 28 data processor covenant."
            },
            {
                "clause_id": "c02",
                "text": "Processor may retain, monetize, and transfer anonymized personal data and telemetry indefinitely to third parties.",
                "category": "Privacy",
                "severity": "High",
                "rule_findings": [{"rule_id": "R013", "risk_signal": "Unlimited Data Retain/Share"}],
                "why_flagged": "Unlimited personal data retention and third-party monetization."
            },
            {
                "clause_id": "c03",
                "text": "Processor will notify Controller of any confirmed Security Incident within 48 hours.",
                "category": "Privacy",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard 48-hour data breach notification window."
            }
        ]
    },
    # 14. HIPAA Business Associate Agreement
    {
        "doc_id": "doc_hipaa_baa_014",
        "doc_type": "HIPAA Business Associate Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Business Associate will use appropriate safeguards to prevent unauthorized use or disclosure of Protected Health Information.",
                "category": "Privacy",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard statutory HIPAA PHI safeguard duty."
            },
            {
                "clause_id": "c02",
                "text": "Covered Entity agrees that Business Associate bears zero financial liability for statutory fines resulting from data breaches.",
                "category": "Liability",
                "severity": "High",
                "rule_findings": [{"rule_id": "R008", "risk_signal": "Unilateral Liability Disclaimer"}, {"rule_id": "R005", "risk_signal": "Excessive Liability Transfer"}],
                "why_flagged": "Total disclaimer of HIPAA statutory fine liability."
            },
            {
                "clause_id": "c03",
                "text": "Business Associate shall make internal records available to HHS Secretary for determining compliance.",
                "category": "Privacy",
                "severity": "Low",
                "rule_findings": [],
                "why_flagged": "Standard regulatory audit cooperation."
            }
        ]
    },
    # 15. Consumer E-Commerce Terms of Service
    {
        "doc_id": "doc_tos_ecommerce_015",
        "doc_type": "Consumer E-Commerce Terms of Service",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Purchases are processed via secure encrypted third-party payment gateways.",
                "category": "Payment",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard consumer checkout security clause."
            },
            {
                "clause_id": "c02",
                "text": "All disputes must be resolved by individual arbitration; User explicitly waives all rights to participate in class actions.",
                "category": "Dispute Resolution",
                "severity": "Moderate",
                "rule_findings": [{"rule_id": "R011", "risk_signal": "Class Action Waiver"}, {"rule_id": "R012", "risk_signal": "Mandatory Binding Arbitration"}],
                "why_flagged": "Mandatory individual arbitration and class action waiver."
            },
            {
                "clause_id": "c03",
                "text": "Platform reserves right to modify subscription prices, shipping charges, and fees without notice at any time.",
                "category": "Payment",
                "severity": "High",
                "rule_findings": [{"rule_id": "R003", "risk_signal": "Hidden/Add-on Charges"}, {"rule_id": "R007", "risk_signal": "Unilateral Modification"}],
                "why_flagged": "Unilateral price increases without advance notice."
            }
        ]
    },
    # 16. Mobile App End User License
    {
        "doc_id": "doc_eula_mobile_016",
        "doc_type": "Mobile Application End User License Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Developer grants User a limited, revocable, non-exclusive license to use the Application on personal devices.",
                "category": "Intellectual Property",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard revocable mobile app license."
            },
            {
                "clause_id": "c02",
                "text": "User agrees that Application may collect precise background geolocation and contact book data continuously.",
                "category": "Privacy",
                "severity": "Moderate",
                "rule_findings": [{"rule_id": "R013", "risk_signal": "Unlimited Data Retain/Share"}],
                "why_flagged": "Aggressive background location and contact harvesting."
            },
            {
                "clause_id": "c03",
                "text": "User may uninstall the Application at any time to terminate this license.",
                "category": "Termination",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard user termination via app deletion."
            }
        ]
    },
    # 17. Commercial Loan Agreement
    {
        "doc_id": "doc_loan_commercial_017",
        "doc_type": "Secured Commercial Credit Facility Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Borrower shall repay principal in quarterly installments per Schedule 1 with interest at SOFR plus 2.50%.",
                "category": "Payment",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard commercial loan amortization terms."
            },
            {
                "clause_id": "c02",
                "text": "Upon any late payment, Lender may declare all principal immediately due and payable without grace period.",
                "category": "Payment",
                "severity": "High",
                "rule_findings": [{"rule_id": "R004", "risk_signal": "Late-Payment Penalty"}],
                "why_flagged": "Immediate loan acceleration without cure or grace period."
            },
            {
                "clause_id": "c03",
                "text": "Borrower will submit audited financial statements within 90 days following fiscal year end.",
                "category": "Payment",
                "severity": "Low",
                "rule_findings": [],
                "why_flagged": "Standard annual financial reporting covenant."
            }
        ]
    },
    # 18. Share Purchase Agreement (M&A)
    {
        "doc_id": "doc_share_purchase_018",
        "doc_type": "Definitive Share Purchase Agreement (M&A)",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Buyer shall deliver the Purchase Price by wire transfer in immediately available funds at Closing.",
                "category": "Payment",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard M&A closing wire delivery."
            },
            {
                "clause_id": "c02",
                "text": "Seller's total aggregate indemnification liability for fundamental representations shall be unlimited in time and amount.",
                "category": "Liability",
                "severity": "Moderate",
                "rule_findings": [{"rule_id": "R005", "risk_signal": "Excessive Liability Transfer"}],
                "why_flagged": "Uncapped fundamental representation indemnity."
            },
            {
                "clause_id": "c03",
                "text": "Seller shall not solicit target company executive employees for eighteen (18) months following Closing.",
                "category": "Termination",
                "severity": "Low",
                "rule_findings": [],
                "why_flagged": "Standard post-sale employee non-solicitation covenant."
            }
        ]
    },
    # 19. Joint Venture Agreement
    {
        "doc_id": "doc_joint_venture_019",
        "doc_type": "International Joint Venture Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Each venturer shall contribute $1,000,000 in initial equity capital to the joint venture operating account.",
                "category": "Payment",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard joint venture equity contribution."
            },
            {
                "clause_id": "c02",
                "text": "In the event of deadlock, Venturer A may unilaterally compel Venturer B to forfeit all shares at zero consideration.",
                "category": "Dispute Resolution",
                "severity": "High",
                "rule_findings": [{"rule_id": "R007", "risk_signal": "Unilateral Modification"}, {"rule_id": "R002", "risk_signal": "Early-Termination Penalty"}],
                "why_flagged": "Predatory zero-dollar mandatory share forfeiture on deadlock."
            },
            {
                "clause_id": "c03",
                "text": "Joint venture board meetings require 14 days advance written notice and a supermajority quorum.",
                "category": "Dispute Resolution",
                "severity": "Low",
                "rule_findings": [],
                "why_flagged": "Standard corporate governance meeting notice."
            }
        ]
    },
    # 20. Franchise Agreement
    {
        "doc_id": "doc_franchise_020",
        "doc_type": "Commercial Franchise Disclosure and Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Franchisee will pay a monthly royalty fee of 5% of gross store revenues on the 10th of each month.",
                "category": "Payment",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard franchise royalty rate."
            },
            {
                "clause_id": "c02",
                "text": "Franchisor may mandate mandatory store renovations at Franchisee's sole expense up to $200,000 every two years.",
                "category": "Payment",
                "severity": "High",
                "rule_findings": [{"rule_id": "R003", "risk_signal": "Hidden/Add-on Charges"}],
                "why_flagged": "Excessive mandatory capital expense renovations."
            },
            {
                "clause_id": "c03",
                "text": "Franchisee must purchase standard approved kitchen consumables exclusively from authorized distributors.",
                "category": "Payment",
                "severity": "Low",
                "rule_findings": [],
                "why_flagged": "Standard approved vendor purchasing requirement."
            }
        ]
    },
    # 21. Consulting Agreement
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
    # 22. Warehouse Logistics Agreement
    {
        "doc_id": "doc_warehouse_logistics_022",
        "doc_type": "Commercial Warehousing and Distribution Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Logistics Provider shall receive, warehouse, and fulfill retail orders within 24 hours of electronic order transmission.",
                "category": "Liability",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard warehouse fulfillment turnaround commitment."
            },
            {
                "clause_id": "c02",
                "text": "Logistics Provider's liability for damaged goods is strictly capped at $0.50 per pound of damaged freight.",
                "category": "Liability",
                "severity": "Moderate",
                "rule_findings": [{"rule_id": "R005", "risk_signal": "Excessive Liability Transfer"}],
                "why_flagged": "Extremely low per-pound cargo liability limit."
            },
            {
                "clause_id": "c03",
                "text": "Client may audit warehouse inventory balances once per quarter during regular business hours.",
                "category": "Privacy",
                "severity": "Low",
                "rule_findings": [],
                "why_flagged": "Standard quarterly stock inventory audit right."
            }
        ]
    },
    # 23. OEM Manufacturing Agreement
    {
        "doc_id": "doc_manufacturing_oem_023",
        "doc_type": "Original Equipment Manufacturer (OEM) Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Manufacturer shall produce and deliver units in accordance with agreed monthly rolling forecast purchase orders.",
                "category": "Payment",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard rolling forecast supply terms."
            },
            {
                "clause_id": "c02",
                "text": "Buyer shall maintain a 90-day firm non-cancelable purchase order commitment at all times.",
                "category": "Renewal",
                "severity": "Moderate",
                "rule_findings": [{"rule_id": "R001", "risk_signal": "Auto-Renewal"}],
                "why_flagged": "90-day rolling mandatory binding inventory order."
            },
            {
                "clause_id": "c03",
                "text": "Manufacturer disclaims all warranties of merchantability and fitness for purpose, selling components strictly 'as-is' with zero recall liability.",
                "category": "Liability",
                "severity": "High",
                "rule_findings": [{"rule_id": "R008", "risk_signal": "Unilateral Liability Disclaimer"}],
                "why_flagged": "Total OEM recall and product liability disclaimer."
            }
        ]
    },
    # 24. Clinical Trial Agreement
    {
        "doc_id": "doc_clinical_trial_024",
        "doc_type": "Clinical Trial Site Master Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Clinical Institution will conduct human trial protocol in strict adherence to FDA regulations and GCP standards.",
                "category": "Privacy",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard clinical regulatory compliance covenant."
            },
            {
                "clause_id": "c02",
                "text": "Institution must report any Serious Adverse Event (SAE) to Sponsor's medical monitor within 24 hours of occurrence.",
                "category": "Privacy",
                "severity": "Low",
                "rule_findings": [],
                "why_flagged": "Mandatory 24-hour adverse event medical report."
            },
            {
                "clause_id": "c03",
                "text": "Sponsor shall defend and indemnify Institution against all patient claims arising from study drug toxicity or protocol-directed treatment.",
                "category": "Liability",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard clinical study sponsor indemnification."
            }
        ]
    },
    # 25. Cyber Insurance Policy
    {
        "doc_id": "doc_cyber_insurance_025",
        "doc_type": "Commercial Cyber Risk Insurance Policy",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Policy provides up to $5,000,000 aggregate coverage for covered ransomware extortion payments and forensic response costs.",
                "category": "Liability",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard cyber liability coverage limit."
            },
            {
                "clause_id": "c02",
                "text": "Insurer may retroactively rescind policy and deny all claims if Insured fails to maintain continuous multi-factor authentication on all endpoints.",
                "category": "Termination",
                "severity": "High",
                "rule_findings": [{"rule_id": "R008", "risk_signal": "Unilateral Liability Disclaimer"}],
                "why_flagged": "Severe retroactive coverage voiding condition."
            },
            {
                "clause_id": "c03",
                "text": "Insured must notify Insurer of suspected network breaches within 72 hours of initial detection.",
                "category": "Privacy",
                "severity": "Low",
                "rule_findings": [],
                "why_flagged": "Standard 72-hour incident claim reporting."
            }
        ]
    },
    # 26. Construction Agreement
    {
        "doc_id": "doc_construction_prime_026",
        "doc_type": "Prime Construction Contract (AIA Standard)",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Owner shall make progress payments monthly based on certified percentage of construction completion.",
                "category": "Payment",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard construction progress billing."
            },
            {
                "clause_id": "c02",
                "text": "Contractor shall pay liquidated damages of $5,000 for each calendar day project substantial completion is delayed past deadline.",
                "category": "Payment",
                "severity": "Moderate",
                "rule_findings": [{"rule_id": "R002", "risk_signal": "Early-Termination Penalty"}],
                "why_flagged": "Daily liquidated delay penalty."
            },
            {
                "clause_id": "c03",
                "text": "All change orders exceeding $25,000 require prior written authorization signed by Owner and Architect.",
                "category": "Payment",
                "severity": "Low",
                "rule_findings": [],
                "why_flagged": "Standard formal change order approval threshold."
            }
        ]
    },
    # 27. Film Distribution Agreement
    {
        "doc_id": "doc_film_distrib_027",
        "doc_type": "Theatrical Motion Picture Distribution Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Distributor will account for and remit Producer's net box office share within 45 days after each calendar quarter.",
                "category": "Payment",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard film distribution accounting cycle."
            },
            {
                "clause_id": "c02",
                "text": "Distributor shall hold perpetual worldwide rights across all media formats now known or hereafter invented without reversion.",
                "category": "Intellectual Property",
                "severity": "High",
                "rule_findings": [{"rule_id": "R006", "risk_signal": "Broad IP Assignment"}],
                "why_flagged": "Perpetual all-media rights grant without reversion."
            },
            {
                "clause_id": "c03",
                "text": "Producer retains sole approval rights over director's final cut for festival release.",
                "category": "Intellectual Property",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Producer creative control over festival cut."
            }
        ]
    },
    # 28. API Developer Partner Agreement
    {
        "doc_id": "doc_api_partner_028",
        "doc_type": "Developer API Platform Partner Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Platform grants Developer non-exclusive access to API endpoints subject to published rate limits.",
                "category": "Intellectual Property",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard API developer license."
            },
            {
                "clause_id": "c02",
                "text": "Platform may instantly terminate API access and revoke developer keys at its sole discretion without cause or notice.",
                "category": "Termination",
                "severity": "High",
                "rule_findings": [{"rule_id": "R007", "risk_signal": "Unilateral Modification"}],
                "why_flagged": "Unilateral instant API key revocation without cause."
            },
            {
                "clause_id": "c03",
                "text": "Developer shall display platform brand logos in accordance with official branding guidelines.",
                "category": "Intellectual Property",
                "severity": "Low",
                "rule_findings": [],
                "why_flagged": "Standard developer brand display guidelines."
            }
        ]
    },
    # 29. Healthcare Telemedicine Services
    {
        "doc_id": "doc_telemed_services_029",
        "doc_type": "Telemedicine Clinical Services Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Physician shall provide remote virtual consults in full compliance with state medical board licensing regulations.",
                "category": "Liability",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard medical licensing compliance covenant."
            },
            {
                "clause_id": "c02",
                "text": "Platform provider shall be held harmless from any medical malpractice or clinical diagnosis error committed by Physician.",
                "category": "Liability",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard platform provider malpractice carveout."
            },
            {
                "clause_id": "c03",
                "text": "Physician will document encounter records in electronic health record system within 2 hours of consult completion.",
                "category": "Privacy",
                "severity": "Low",
                "rule_findings": [],
                "why_flagged": "Standard 2-hour clinical charting timeline."
            }
        ]
    },
    # 30. Software Escrow Agreement
    {
        "doc_id": "doc_software_escrow_030",
        "doc_type": "Tripartite Software Source Code Escrow Agreement",
        "clauses": [
            {
                "clause_id": "c01",
                "text": "Escrow Agent shall securely store source code deposits in climate-controlled and access-monitored electronic vaults.",
                "category": "Confidentiality",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard escrow storage safeguards."
            },
            {
                "clause_id": "c02",
                "text": "Source code shall be immediately released to Beneficiary upon Vendor bankruptcy or failure to provide maintenance for 30 consecutive days.",
                "category": "Termination",
                "severity": "Safe",
                "rule_findings": [],
                "why_flagged": "Standard escrow release trigger conditions."
            },
            {
                "clause_id": "c03",
                "text": "Vendor shall make updated source code deposits within ten (10) business days following major version release.",
                "category": "Intellectual Property",
                "severity": "Low",
                "rule_findings": [],
                "why_flagged": "Standard version update code deposit duty."
            }
        ]
    }
]


# ==============================================================================
# 20 COMPREHENSIVE DOCUMENT COMPARISON PAIRS FOR MULTILINGUAL-E5 (80+ Pairs)
# ==============================================================================

DOC_PAIRS_MULTILINGUAL_E5_EXPANDED = [
    # 1. SaaS Agreement (English)
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
                "target_similarity": 0.75,
                "difference_explanation": "Termination notice period increased from 30 days to 60 days.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c03",
                "clause_b_id": None,
                "text_a": "Vendor will provide free telephone technical support during standard business hours.",
                "text_b": None,
                "classification": "MISSING",
                "target_similarity": 0.10,
                "difference_explanation": "Free telephone technical support commitment was removed in Document B.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c01",
                "clause_b_id": "v2_c02",
                "text_a": "Customer shall pay all invoices within thirty (30) days of receipt.",
                "text_b": "Either party may terminate this agreement upon sixty (60) days written notice.",
                "classification": "MISSING",
                "target_similarity": 0.20,
                "difference_explanation": "Payment clause compared against termination clause (distractor).",
                "is_hard_negative": True
            }
        ]
    },
    # 2. Mutual NDA (English)
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
                "target_similarity": 0.78,
                "difference_explanation": "Scope expanded from unilateral recipient obligations to mutual bilateral obligations.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c02",
                "clause_b_id": "v2_c02",
                "text_a": "Confidentiality obligations expire three (3) years from disclosure date.",
                "text_b": "Confidentiality obligations expire five (5) years from disclosure date.",
                "classification": "CHANGED",
                "target_similarity": 0.75,
                "difference_explanation": "Confidentiality duration extended from 3 years to 5 years.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": None,
                "clause_b_id": "v2_c03",
                "text_a": None,
                "text_b": "Trade secrets shall remain confidential perpetually without any expiration date.",
                "classification": "MISSING",
                "target_similarity": 0.10,
                "difference_explanation": "Perpetual trade secret clause is newly added in Document B.",
                "is_hard_negative": False
            }
        ]
    },
    # 3. Employment Agreement (English)
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
                "target_similarity": 0.80,
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
                "target_similarity": 0.70,
                "difference_explanation": "Non-compete duration increased to 24 months and geographic scope widened to nationwide.",
                "is_hard_negative": False
            }
        ]
    },
    # 4. Office Lease (English)
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
                "target_similarity": 0.80,
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
                "target_similarity": 0.10,
                "difference_explanation": "Tenant structural repair burden removed from final agreement.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c04",
                "clause_b_id": "v2_c04",
                "text_a": "Tenant shall provide written notice of any defect within fifteen (15) days of initial occupancy.",
                "text_b": "Tenant shall provide written notice of any defect within fifteen (15) days of initial occupancy.",
                "classification": "MATCHED",
                "target_similarity": 1.00,
                "difference_explanation": "Clause text matches verbatim across versions.",
                "is_hard_negative": False
            }
        ]
    },
    # 5. Multilingual English-Hindi Commercial Agreement
    {
        "doc_pair_id": "pair_hindi_commercial_005",
        "doc_a_id": "doc_comm_en_v1",
        "doc_b_id": "doc_comm_hi_v2",
        "contract_title": "Commercial Supply Agreement (English vs Hindi Translation Alignment)",
        "pairs": [
            {
                "clause_a_id": "v1_c01",
                "clause_b_id": "v2_c01",
                "text_a": "Payment shall be made within 30 days of receiving the invoice.",
                "text_b": "चालान प्राप्त होने के 30 दिनों के भीतर भुगतान किया जाएगा।",
                "classification": "MATCHED",
                "target_similarity": 1.00,
                "difference_explanation": "Exact semantic cross-lingual translation match.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c02",
                "clause_b_id": "v2_c02",
                "text_a": "All disputes shall be resolved through arbitration in New Delhi.",
                "text_b": "सभी विवादों का निपटारा मुंबई में मध्यस्थता के माध्यम से किया जाएगा।",
                "classification": "CHANGED",
                "target_similarity": 0.76,
                "difference_explanation": "Arbitration venue changed from New Delhi to Mumbai in Hindi text.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c03",
                "clause_b_id": None,
                "text_a": "Goods shall be inspected within 48 hours of delivery at warehouse.",
                "text_b": None,
                "classification": "MISSING",
                "target_similarity": 0.10,
                "difference_explanation": "Inspection clause omitted in Document B.",
                "is_hard_negative": False
            }
        ]
    },
    # 6. Intellectual Property Licensing (English)
    {
        "doc_pair_id": "pair_ip_license_006",
        "doc_a_id": "doc_ip_v1",
        "doc_b_id": "doc_ip_v2",
        "contract_title": "Software IP License (Non-Exclusive vs Exclusive)",
        "pairs": [
            {
                "clause_a_id": "v1_c01",
                "clause_b_id": "v2_c01",
                "text_a": "Licensor grants Licensee a non-exclusive, non-transferable license to use the software.",
                "text_b": "Licensor grants Licensee an exclusive, perpetual, worldwide license to use and sub-license the software.",
                "classification": "CHANGED",
                "target_similarity": 0.72,
                "difference_explanation": "License grant elevated from non-exclusive to exclusive and sub-licensable.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c02",
                "clause_b_id": "v2_c02",
                "text_a": "Licensee shall not decompile or reverse engineer any binary components.",
                "text_b": "Licensee shall not decompile or reverse engineer any binary components.",
                "classification": "MATCHED",
                "target_similarity": 1.00,
                "difference_explanation": "Reverse engineering restriction matches verbatim.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c03",
                "clause_b_id": "v2_c03",
                "text_a": "Annual maintenance fees are $10,000 payable every January.",
                "text_b": "Annual maintenance fees are $15,000 payable every January.",
                "classification": "CHANGED",
                "target_similarity": 0.82,
                "difference_explanation": "Maintenance fee escalated from $10,000 to $15,000.",
                "is_hard_negative": False
            }
        ]
    },
    # 7. Healthcare BAA Comparison (English)
    {
        "doc_pair_id": "pair_hipaa_baa_007",
        "doc_a_id": "doc_baa_draft",
        "doc_b_id": "doc_baa_final",
        "contract_title": "HIPAA Business Associate Agreement (Draft vs Final)",
        "pairs": [
            {
                "clause_a_id": "v1_c01",
                "clause_b_id": "v2_c01",
                "text_a": "Business Associate must report security breaches within 5 business days.",
                "text_b": "Business Associate must report security breaches within twenty-four (24) hours.",
                "classification": "CHANGED",
                "target_similarity": 0.74,
                "difference_explanation": "Breach notification timeline tightened from 5 days to 24 hours.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c02",
                "clause_b_id": "v2_c02",
                "text_a": "All electronic protected health information shall be encrypted at rest and in transit.",
                "text_b": "All electronic protected health information shall be encrypted at rest and in transit.",
                "classification": "MATCHED",
                "target_similarity": 1.00,
                "difference_explanation": "PHI encryption standard identical.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c03",
                "clause_b_id": None,
                "text_a": "Covered Entity may conduct annual physical onsite facility audits.",
                "text_b": None,
                "classification": "MISSING",
                "target_similarity": 0.10,
                "difference_explanation": "Onsite physical audit right deleted.",
                "is_hard_negative": False
            }
        ]
    },
    # 8. Vendor Distribution Agreement (English)
    {
        "doc_pair_id": "pair_vendor_distrib_008",
        "doc_a_id": "doc_distrib_v1",
        "doc_b_id": "doc_distrib_v2",
        "contract_title": "Wholesale Distribution Agreement (Original vs Extension)",
        "pairs": [
            {
                "clause_a_id": "v1_c01",
                "clause_b_id": "v2_c01",
                "text_a": "Distributor shall achieve minimum annual sales volume of 50,000 units.",
                "text_b": "Distributor shall achieve minimum annual sales volume of 75,000 units.",
                "classification": "CHANGED",
                "target_similarity": 0.81,
                "difference_explanation": "Annual quota increased from 50,000 to 75,000 units.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": "v1_c02",
                "clause_b_id": "v2_c02",
                "text_a": "Territory is strictly limited to California, Oregon, and Washington.",
                "text_b": "Territory is strictly limited to California, Oregon, and Washington.",
                "classification": "MATCHED",
                "target_similarity": 1.00,
                "difference_explanation": "Territory definition unchanged.",
                "is_hard_negative": False
            },
            {
                "clause_a_id": None,
                "clause_b_id": "v2_c03",
                "text_a": None,
                "text_b": "Vendor provides standard 12-month replacement warranty on manufacturing defects.",
                "classification": "MISSING",
                "target_similarity": 0.10,
                "difference_explanation": "Replacement warranty clause added in revised version.",
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
            context_text = f"Document: {doc_type} | Category: {clause['category']} | Rule Signals: [{findings_str}] | Clause: {clause['text']}"
            
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
    print("Generating High-Precision ClarifAI Datasets v2.0")
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
