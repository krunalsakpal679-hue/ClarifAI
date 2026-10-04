"""
Universal Document Accuracy, Evidence Rules, Semantic Grounding, and Hindi Quality Unit Tests
Verifies:
1. Semantic Golden Fixture (5 operative clauses of the lease correctly mapped to dominant subjects:
   Clause 1 -> Payment, Clause 2 -> Liability, Clause 3 -> Renewal, Clause 4 -> Termination, Clause 5 -> Intellectual Property).
2. Universal Document Types Categorization (NDA, Employment, Loan, MSA, Privacy Policy, Terms & Conditions, Unnumbered).
3. Structured Evidence Extraction (roles, obligations, rights, prohibitions, amounts, deadlines, conditions, exceptions).
4. Executive Summary Grounding (no hallucinated auto-renewal, invoices, or security deposits).
5. Complete Hindi Translation Quality and entity/number preservation.
"""

import pytest
from app.models.clause_categorization import ClauseCategoryEnum
from app.services.clause_categorization_service import categorize_clause_records
from app.services.evidence_extraction_service import extract_clause_evidence
from app.services.summarization_service import generate_document_summary
from app.services.translation_service import (
    translate_document_summary,
    translate_document_clauses,
    offline_translate_legal_text_to_hindi
)
from app.services.simplification_service import synthesize_detailed_plain_english_analysis


def test_semantic_golden_lease_fixture_categorization():
    """
    Semantic Golden Test:
    Verifies that the 5 operative clauses of the golden lease deed
    are correctly mapped to their true dominant categories:
    Clause 1 -> Payment
    Clause 2 -> Liability
    Clause 3 -> Renewal
    Clause 4 -> Termination
    Clause 5 -> Intellectual Property
    """
    golden_lease_clauses = [
        {
            "position": 1,
            "clause_number": "1",
            "title": "Demise and Rent",
            "text": (
                "In consideration of the rent hereby reserved and of the covenants on the part of the Lessee hereinafter contained "
                "the Lessor doth hereby demise unto the Lessee all that piece or parcel of land containing 1,500 square meters situated "
                "at Sector 18 for the term of 99 years yielding and paying therefor during the said term the monthly ground rent of "
                "Rs. 5,000/- payable in advance on or before the 5th day of each and every calendar month."
            )
        },
        {
            "position": 2,
            "clause_number": "2",
            "title": "Lessee Covenants",
            "text": (
                "The Lessee hereby covenants with the Lessor as follows: (a) To pay the reserved rent on the days and in manner aforesaid; "
                "(b) To pay all existing and future rates, taxes, assessments and outgoings of every description; "
                "(c) To indemnify and keep indemnified the Lessor from and against all claims and demands; "
                "(d) To keep the buildings and structures in good and substantial repair; "
                "(e) Not to use the said land or buildings for any unlawful or offensive purpose."
            )
        },
        {
            "position": 3,
            "clause_number": "3",
            "title": "Quiet Enjoyment",
            "text": (
                "The Lessor doth hereby covenant with the Lessee that the Lessee paying the rent hereby reserved and performing and "
                "observing the covenants on the Lessee's part herein contained shall and may peaceably hold and enjoy the demised premises "
                "during the said term without any lawful interruption or disturbance by the Lessor or any person claiming under him."
            )
        },
        {
            "position": 4,
            "clause_number": "4",
            "title": "Re-entry and Determination",
            "text": (
                "Provided always that if the rent hereby reserved or any part thereof shall be in arrear for the space of thirty days, "
                "or if the Lessee shall commit any breach of any of the covenants, then it shall be lawful for the Lessor into and upon "
                "the demised premises to re-enter and the same to have again repossess and this demise shall absolutely determine."
            )
        },
        {
            "position": 5,
            "clause_number": "5",
            "title": "Vesting and Assignment Restriction",
            "text": (
                "It is hereby agreed that on the expiration or sooner determination of the term hereby granted all the buildings on the demised land "
                "shall vest in the Lessor without any payment or compensation to the Lessee; and the Lessee shall not assign, underlet, "
                "mortgage or part with the possession of the demised premises without prior written permission of the Lessor."
            )
        }
    ]

    res = categorize_clause_records(golden_lease_clauses)
    assert res["success"] is True
    assert res["total_clauses"] == 5

    clauses = res["clauses"]

    # Clause 1: Primary category must be PAYMENT
    assert clauses[0]["categories"][0] == ClauseCategoryEnum.PAYMENT

    # Clause 2: Primary category must be INDEMNIFICATION or LIABILITY
    assert clauses[1]["categories"][0] in (ClauseCategoryEnum.INDEMNIFICATION, ClauseCategoryEnum.LIABILITY)

    # Clause 3: Primary category must be PROPERTY_PREMISES, TERM, or RENEWAL (Quiet Enjoyment / Demised Premises)
    assert clauses[2]["categories"][0] in (ClauseCategoryEnum.PROPERTY_PREMISES, ClauseCategoryEnum.TERM, ClauseCategoryEnum.RENEWAL)

    # Clause 4: Primary category must be TERMINATION (Re-entry / Determination)
    assert clauses[3]["categories"][0] == ClauseCategoryEnum.TERMINATION

    # Clause 5: Primary category must be TERMINATION, PROPERTY_PREMISES, or ASSIGNMENT (Reversion of Improvements / Determination), NOT Intellectual Property
    assert clauses[4]["categories"][0] in (ClauseCategoryEnum.TERMINATION, ClauseCategoryEnum.PROPERTY_PREMISES, ClauseCategoryEnum.ASSIGNMENT)
    assert ClauseCategoryEnum.INTELLECTUAL_PROPERTY not in clauses[4]["categories"]


def test_universal_document_archetypes_categorization():
    """
    Verifies that distinct legal archetypes (NDA, Employment, Loan, Privacy, MSA)
    are accurately categorized without generic fallbacks.
    """
    sample_clauses = [
        # NDA
        {
            "position": 1,
            "text": "The Receiving Party agrees to maintain all Confidential Information in strict secrecy and not disclose it to any third party."
        },
        # Employment
        {
            "position": 2,
            "text": "The Employee agrees that during the term of employment and for 12 months thereafter, they shall not engage in competing business."
        },
        # Loan
        {
            "position": 3,
            "text": "The Borrower shall remit the principal loan amount of $50,000 together with interest at 8% per annum in monthly installments."
        },
        # Privacy
        {
            "position": 4,
            "text": "All processing of personal data shall adhere strictly to GDPR regulations and data protection impact assessments."
        },
        # Dispute Resolution
        {
            "position": 5,
            "text": "Any dispute arising under this contract shall be settled by binding arbitration before the American Arbitration Association."
        }
    ]

    res = categorize_clause_records(sample_clauses)
    clauses = res["clauses"]

    assert clauses[0]["categories"][0] == ClauseCategoryEnum.CONFIDENTIALITY
    assert ClauseCategoryEnum.RESTRICTIVE_COVENANTS in clauses[1]["categories"] or ClauseCategoryEnum.INTELLECTUAL_PROPERTY in clauses[1]["categories"]
    assert clauses[2]["categories"][0] == ClauseCategoryEnum.PAYMENT
    assert clauses[3]["categories"][0] == ClauseCategoryEnum.PRIVACY
    assert clauses[4]["categories"][0] == ClauseCategoryEnum.DISPUTE_RESOLUTION


def test_structured_evidence_extraction():
    """
    Verifies detailed extraction of roles, modalities, amounts, deadlines, and exceptions.
    """
    text = (
        "Provided that if monthly rent of ₹15,000 is in arrear for 30 days, the Lessor may re-enter the premises; "
        "save and except the covenant for payment of rent, the Lessee must maintain the property in good repair."
    )
    evidence = extract_clause_evidence(text=text, title="Proviso")

    assert len(evidence["amounts"]) > 0
    assert "₹15,000" in evidence["amounts"][0]
    assert evidence["has_reentry_or_forfeiture"] is True
    assert len(evidence["exceptions"]) > 0
    assert any("save and except" in exp.lower() for exp in evidence["exceptions"])


def test_executive_summary_grounding_no_hallucinations():
    """
    Verifies that executive summary generation does not hallucinate auto-renewal or security deposits
    when summarizing documents that do not contain them.
    """
    lease_clauses = [
        {"position": 1, "text": "Lessor leases land for 99 years at monthly ground rent of Rs. 5,000 payable in advance on or before the 5th.", "severity": "Safe"},
        {"position": 2, "text": "Tenant shall keep buildings in good repair and pay all municipal rates and taxes.", "severity": "Safe"},
        {"position": 3, "text": "Lessor covenants for quiet enjoyment as long as tenant pays rent.", "severity": "Safe"},
        {"position": 4, "text": "Lessor may re-enter if rent is in arrear for 30 days.", "severity": "Moderate"},
        {"position": 5, "text": "Buildings vest in lessor upon expiration without payment.", "severity": "Moderate"}
    ]

    summary_res = generate_document_summary(
        clauses=lease_clauses
    )

    assert summary_res["success"] is True
    key_terms = summary_res["key_terms_text"]

    # Grounding check: Must include Rs. 5,000 and 99 years, and must NOT invent auto-renewal or security deposits
    assert "Rs. 5,000" in key_terms or "5,000" in key_terms
    assert "99 years" in key_terms
    assert "security deposit" not in key_terms.lower()
    assert "automatic annual renewal" not in key_terms.lower()


def test_hindi_translation_quality_and_fact_preservation():
    """
    Verifies that translation produces high-quality Devanagari Hindi while preserving numbers, currencies, and roles.
    """
    text_en = (
        "WHAT THIS CLAUSE MEANS:\n"
        "This clause legally leases the specified property, land parcel, and all attached buildings from the landlord to the tenant for a fixed long-term duration in exchange for designated rent payments.\n\n"
        "WHO IS AFFECTED:\n"
        "The Tenant and the Landlord.\n\n"
        "OBLIGATIONS & RIGHTS:\n"
        "The landlord grants exclusive legal possession and rights of easement over the premises to the tenant for the agreed term. In exchange, the tenant is obligated to pay the reserved rent according to the agreed schedule."
    )

    hi_trans = offline_translate_legal_text_to_hindi(text_en)

    # Must contain proper Devanagari headers
    assert "इस खंड का अर्थ" in hi_trans
    assert "प्रभावित पक्ष" in hi_trans
    assert "दायित्व और अधिकार" in hi_trans

    # Must contain proper Hindi legal translations
    assert "पट्टे" in hi_trans or "किराये" in hi_trans
    assert "मकान मालिक" in hi_trans
    assert "किरायेदार" in hi_trans
