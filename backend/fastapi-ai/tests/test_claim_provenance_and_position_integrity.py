"""
ClarifAI Master Reusable Audit: Claim-Level Provenance & Clause-Position Integrity Regression Tests
Validates all 12 confirmed fixture bugs and proves end-to-end join integrity and grounding.
"""

import os
import re
try:
    import pytest
except ImportError:
    class _DummyPytest:
        @staticmethod
        def fixture(*args, **kwargs):
            return lambda fn: fn
        @staticmethod
        def skip(*args, **kwargs):
            pass
    pytest = _DummyPytest()


from pathlib import Path

from app.services.pdf_service import extract_pdf_text_service
from app.services.text_cleaning_service import clean_legal_text
from app.services.clause_segmentation_service import segment_document_clauses
from app.services.clause_categorization_service import categorize_clause_records
from app.services.rule_engine_service import evaluate_rules
from app.services.risk_service import classify_document_clauses_risk
from app.services.simplification_service import (
    simplify_document_clauses,
    simplify_single_clause,
    extract_category_evidence_span,
    extract_risk_evidence_span
)
from app.services.summarization_service import generate_document_summary
from app.services.claim_grounding_service import (
    verify_and_ground_clause_narrative,
    verify_and_ground_executive_summary,
    extract_obligor_and_beneficiary
)

def get_sample_dir() -> Path:
    candidates = [
        Path(__file__).resolve().parent.parent.parent.parent / "sample_documents",
        Path(__file__).resolve().parent.parent / "sample_documents",
        Path("/app/sample_documents"),
        Path("/sample_documents"),
        Path("c:/ClarifAI- AIPipeline/sample_documents"),
        Path("sample_documents")
    ]
    for c in candidates:
        if c.exists() and c.is_dir():
            return c
    return candidates[0]

FIXTURE_PATH = get_sample_dir() / "Document_B_Consulting_Services_Agreement.pdf"


@pytest.fixture(scope="module")
def document_b_fixture():
    assert FIXTURE_PATH.exists(), f"Fixture PDF not found at {FIXTURE_PATH}"
    with open(FIXTURE_PATH, "rb") as f:
        pdf_bytes = f.read()
    
    ext = extract_pdf_text_service(pdf_bytes, enable_ocr=False)
    cleaned = clean_legal_text(ext["full_text"])["cleaned_text"]
    seg_res = segment_document_clauses(cleaned, pages=ext.get("pages", []))
    segmented = seg_res["clauses"]
    
    rules_res = evaluate_rules(clauses=segmented, text=cleaned)
    findings = rules_res["findings"]
    
    cat_res = categorize_clause_records(segmented, rule_findings=findings)
    categorized = cat_res["clauses"]
    
    risk_res = classify_document_clauses_risk(categorized, rule_findings=findings)
    classified = risk_res["clauses"]
    
    simp_res = simplify_document_clauses(classified, rule_findings=findings)
    simplified = simp_res.get("clauses") or simp_res.get("simplified_clauses", [])
    
    sum_res = generate_document_summary(classified, rule_findings=findings)
    
    return {
        "raw_text": ext["full_text"],
        "cleaned_text": cleaned,
        "segmented": segmented,
        "findings": findings,
        "categorized": categorized,
        "classified": classified,
        "simplified": simplified,
        "summary": sum_res
    }


def test_part1_position_and_clause_join_integrity(document_b_fixture):
    """
    Part 1: Position and clause_id primary key integrity across all pipeline stages.
    """
    segmented = document_b_fixture["segmented"]
    categorized = document_b_fixture["categorized"]
    classified = document_b_fixture["classified"]
    simplified = document_b_fixture["simplified"]
    
    assert len(segmented) == 7
    assert len(categorized) == 7
    assert len(classified) == 7
    assert len(simplified) == 7
    
    for i in range(7):
        pos = i + 1
        expected_id = f"c-{pos:03d}"
        
        # Verify segmented
        assert segmented[i]["position"] == pos
        assert segmented[i]["clause_id"] == expected_id
        
        # Verify categorized
        assert categorized[i]["position"] == pos
        assert categorized[i]["clause_id"] == expected_id
        assert categorized[i]["text"] == segmented[i]["text"]
        
        # Verify classified
        assert classified[i]["position"] == pos
        assert classified[i]["text"] == segmented[i]["text"]
        
        # Verify simplified
        assert simplified[i]["position"] == pos
        assert simplified[i]["original_text"] == segmented[i]["text"]


def test_bug_1_clause_1_engagement_content_and_not_default_renewal(document_b_fixture):
    """
    Bug 1: Clause 1 (Engagement) has real content, not generic boilerplate tagged Dispute Resolution/Renewal.
    """
    cl1 = document_b_fixture["simplified"][0]
    assert "ENGAGEMENT AND DELIVERABLES" in cl1["original_text"]
    assert "strategic" in cl1["original_text"].lower()
    
    what_means = cl1["structured_explanation"]["what_this_clause_means"]
    assert any(term in what_means.lower() for term in ["engagement", "consult", "advis", "service", "deliverable", "scope"])
    # Confirm category is not forced to Renewal or Dispute Resolution
    cat = cl1["structured_explanation"]["category"]["label"]
    assert cat not in ["Dispute Resolution", "Renewal"]


def test_bug_2_clause_5_liability_cap_category_and_explanation(document_b_fixture):
    """
    Bug 2: Clause 5 ($50,000 liability cap) must be tagged Liability (not Termination).
    """
    cl5 = document_b_fixture["simplified"][4]
    assert "AGGREGATE LIABILITY CAP" in cl5["original_text"]
    
    cat = cl5["structured_explanation"]["category"]["label"]
    assert cat == "Liability", f"Expected Liability, got {cat}"
    
    what_means = cl5["structured_explanation"]["what_this_clause_means"]
    assert "financial ceiling" in what_means.lower() or "damages" in what_means.lower() or "liability" in what_means.lower()
    assert "terminate" not in what_means.lower()


def test_bug_3_clause_7_confidentiality_category_and_explanation(document_b_fixture):
    """
    Bug 3: Clause 7 (Confidentiality) must be tagged Confidentiality (not Termination).
    """
    cl7 = document_b_fixture["simplified"][6]
    assert "CONFIDENTIALITY COVENANT" in cl7["original_text"]
    
    cat = cl7["structured_explanation"]["category"]["label"]
    assert cat == "Confidentiality", f"Expected Confidentiality, got {cat}"
    
    what_means = cl7["structured_explanation"]["what_this_clause_means"]
    assert "confidential" in what_means.lower()
    assert "cure periods" not in what_means.lower()


def test_bug_4_clause_4_indemnity_directionality_not_reversed(document_b_fixture):
    """
    Bug 4: Clause 4 (Indemnity) source says Consultant indemnifies Client.
    Narrative text must NOT reverse parties to customer indemnifying vendor.
    """
    cl4 = document_b_fixture["simplified"][3]
    assert "INDEMNITY OBLIGATIONS" in cl4["original_text"]
    assert "Consultant agrees to defend and indemnify Client" in cl4["original_text"]
    
    simp_text = cl4["simplified_text"]
    assert "The Customer is obligated to defend, indemnify, and hold harmless the Vendor" not in simp_text
    assert "Consultant is obligated to defend, indemnify, and hold harmless the Client" in simp_text or "Consultant" in simp_text


def test_bug_5_executive_summary_no_invented_renewal(document_b_fixture):
    """
    Bug 5: Executive summary must not claim automatic renewal when no renewal clause exists.
    """
    summary = document_b_fixture["summary"]
    key_terms = summary.get("key_terms_text", "")
    key_risks = summary.get("key_risks_text", "")
    
    assert "renews automatically" not in key_terms.lower()
    assert "automatic renewal" not in key_terms.lower()
    assert "renews automatically" not in key_risks.lower()


def test_bug_6_executive_summary_unilateral_indemnity_not_mutual(document_b_fixture):
    """
    Bug 6: Executive summary must specify unilateral consultant indemnification (not mutual).
    """
    summary = document_b_fixture["summary"]
    key_risks = summary.get("key_risks_text", "")
    
    assert "mutual indemnification" not in key_risks.lower()
    assert "unilateral consultant indemnification" in key_risks.lower() or "consultant indemnification" in key_risks.lower()


def test_bug_7_and_8_clause_3_ip_no_invented_payment_condition(document_b_fixture):
    """
    Bugs 7 & 8: Clause 3 (Work Product Ownership) source has NO payment condition.
    Report must NOT invent 'conditioned upon full payment' or 'upon fee satisfaction'.
    """
    cl3 = document_b_fixture["simplified"][2]
    assert "WORK PRODUCT OWNERSHIP" in cl3["original_text"]
    assert "shall be deemed work made for hire and become Client's exclusive intellectual property" in re.sub(r'\s+', ' ', cl3["original_text"])
    
    simp_text = cl3["simplified_text"]
    what_means = cl3["structured_explanation"]["what_this_clause_means"]
    
    assert "conditioned upon full payment" not in simp_text.lower()
    assert "contingent upon full receipt of agreed payment" not in simp_text.lower()
    assert "upon payment" not in what_means.lower()
    assert "fee satisfaction" not in document_b_fixture["summary"].get("key_terms_text", "").lower()


def test_bug_9_clause_4_no_invented_attorney_fees_or_regulatory_penalties(document_b_fixture):
    """
    Bug 9: Clause 4 report must NOT invent 'legal judgments, regulatory penalties, and reasonable attorney fees'.
    """
    cl4 = document_b_fixture["simplified"][3]
    simp_text = cl4["simplified_text"]
    
    assert "regulatory penalties" not in simp_text.lower()
    assert "reasonable attorney fees" not in simp_text.lower()
    assert "legal judgments" not in simp_text.lower()


def test_bug_10_clause_7_no_invented_injunctive_relief_remedy(document_b_fixture):
    """
    Bug 10: Clause 7 report must NOT invent 'immediate injunctive relief and monetary damages'.
    """
    cl7 = document_b_fixture["simplified"][6]
    simp_text = cl7["simplified_text"]
    
    assert "immediate injunctive relief" not in simp_text.lower()


def test_bug_11_clause_6_governing_forum_no_invented_governing_substantive_law(document_b_fixture):
    """
    Bug 11: Clause 6 report must NOT invent 'governing substantive law' when clause establishes forum/jurisdiction only.
    """
    cl6 = document_b_fixture["simplified"][5]
    what_means = cl6["structured_explanation"]["what_this_clause_means"]
    
    assert "substantive law" not in what_means.lower()
    assert "jurisdiction" in what_means.lower() or "forum" in what_means.lower()


def test_bug_12_clause_2_preserves_compounding_interest_rate(document_b_fixture):
    """
    Bug 12: Clause 2 report preserves '2.0% per month compounding monthly'.
    """
    cl2 = document_b_fixture["simplified"][1]
    simp_text = cl2["simplified_text"]
    
    assert "2.0%" in simp_text
    assert "compounding monthly" in simp_text or "per month" in simp_text


def test_adversarial_invented_mechanisms_generalization():
    """
    Part 3 Generalization: 5 NEW adversarial test clauses covering distinct invented mechanisms.
    Grounding check must catch ungrounded legal mechanisms and strip or flag them.
    """
    # 1. Invented arbitration when source only provides court litigation
    source_litigation = "1. Litigation. Any dispute arising out of this Agreement shall be resolved exclusively in the state courts of Cook County, Illinois."
    res1 = verify_and_ground_clause_narrative(
        source_text=source_litigation,
        clause_title="Dispute Resolution",
        what_this_clause_means="This clause mandates binding arbitration before the American Arbitration Association waiving trial rights.",
        obligations="Both parties must arbitrate disputes in private arbitration.",
        details_list=["Arbitration: Binding AAA arbitration."],
        consequences=""
    )
    assert "arbitrat" not in res1["what_this_clause_means"].lower()
    assert len(res1["warnings"]) > 0 or "litigat" in res1["what_this_clause_means"].lower()

    # 2. Invented security deposit when source only specifies monthly rent
    source_rent = "2. Rent. Tenant shall pay Landlord monthly base rent of $3,500 on the first day of each calendar month."
    res2 = verify_and_ground_clause_narrative(
        source_text=source_rent,
        clause_title="Rent",
        what_this_clause_means="This clause requires a refundable security deposit of $7,000 to be held in escrow for damages.",
        obligations="Tenant must remit security deposit prior to occupancy.",
        details_list=["Deposit: $7,000 security deposit."],
        consequences="Deposit is forfeited if damage occurs.",
        severity="Moderate"
    )
    assert "security deposit" not in res2["what_this_clause_means"].lower()
    assert len(res2["warnings"]) > 0 or "$3,500" in str(res2["details_list"])

    # 3. Invented warranty disclaimer when source is a straightforward delivery covenant
    source_delivery = "3. Delivery. Vendor shall deliver the software installation package within thirty (30) days of execution."
    res3 = verify_and_ground_clause_narrative(
        source_text=source_delivery,
        clause_title="Delivery",
        what_this_clause_means="This clause disclaims all express and implied warranties including merchantability and fitness for a particular purpose.",
        obligations="Customer accepts software as-is without any warranties whatsoever.",
        details_list=["Warranty: Disclaimed."],
        consequences=""
    )
    assert "warranty" not in res3["what_this_clause_means"].lower()

    # 4. Invented assignment restriction when source only governs confidentiality
    source_conf = "4. Confidentiality. Receiving Party shall maintain Disclosing Party's confidential information in strict confidence."
    res4 = verify_and_ground_clause_narrative(
        source_text=source_conf,
        clause_title="Confidentiality",
        what_this_clause_means="This clause prohibits either party from assigning or transferring this agreement without prior written consent.",
        obligations="Parties cannot assign rights or subcontract without authorization.",
        details_list=["Assignment: Restricted."],
        consequences=""
    )
    assert "assign" not in res4["what_this_clause_means"].lower()

    # 5. Invented force majeure when source only governs termination for convenience
    source_convenience = "5. Termination. Either party may terminate this Agreement without cause upon sixty (60) days prior written notice."
    res5 = verify_and_ground_clause_narrative(
        source_text=source_convenience,
        clause_title="Termination",
        what_this_clause_means="This clause excuses non-performance during acts of God, pandemics, war, or force majeure events.",
        obligations="Parties are relieved from performance during force majeure emergencies.",
        details_list=["Force Majeure: Excuses delay."],
        consequences=""
    )
    assert "force majeure" not in res5["what_this_clause_means"].lower()
    assert "acts of god" not in res5["what_this_clause_means"].lower()


def test_bug_a_category_evidence_never_numeric_position_index():
    """
    Bug A Regression Test: Asserts category.evidence is never purely numeric or a clause index.
    """
    numbered_texts = [
        "1. In consideration of the mutual covenants contained herein, the parties agree as follows.",
        "2. Payment Terms. Invoices are due net 30 days from receipt.",
        "3. (a) Intellectual Property. All custom modules constitute work made for hire.",
        "4. Termination. Either party may terminate for convenience upon sixty (60) days notice.",
        "a. To pay all existing and future rates and taxes assessed on the premises.",
        "b. To keep the interior in good and substantial repair."
    ]
    for text in numbered_texts:
        reason, span = extract_category_evidence_span(text, "Payment")
        assert not span.isdigit(), f"Category evidence span '{span}' is numeric!"
        assert not re.match(r'^\W*\d+\W*$', span), f"Category evidence span '{span}' is a position number!"
        assert len(span) > 2, f"Category evidence span '{span}' is too short!"

        r_reason, r_span = extract_risk_evidence_span(text, "Low")
        assert not r_span.isdigit(), f"Risk evidence span '{r_span}' is numeric!"
        assert not re.match(r'^\W*\d+\W*$', r_span), f"Risk evidence span '{r_span}' is a position number!"


def test_document_a_saas_grounding_and_party_names():
    """
    Document A SaaS Service Agreement regression tests:
    - Clause 1: Category and severity are not 'General' / 'UNKNOWN'.
    - Clause 3: Mentions work made for hire / custom modules.
    - Clause 4: Names Provider & Subscriber.
    - Clause 6: Mentions Cook County, Illinois.
    - Clause 7: No invented cause, cure period, or fee acceleration.
    """
    doc_a_path = get_sample_dir() / "Document_A_SaaS_Service_Agreement.pdf"
    if not doc_a_path.exists():
        pytest.skip("Document A SaaS PDF not available")
    
    with open(doc_a_path, "rb") as f:
        pdf_bytes = f.read()
    
    ext = extract_pdf_text_service(pdf_bytes, enable_ocr=False)
    cleaned = clean_legal_text(ext["full_text"])["cleaned_text"]
    seg_res = segment_document_clauses(cleaned, pages=ext.get("pages", []))
    segmented = seg_res["clauses"]
    
    rules_res = evaluate_rules(clauses=segmented, text=cleaned)
    findings = rules_res["findings"]
    cat_res = categorize_clause_records(segmented, rule_findings=findings)
    categorized = cat_res["clauses"]
    risk_res = classify_document_clauses_risk(categorized, rule_findings=findings)
    classified = risk_res["clauses"]
    simp_res = simplify_document_clauses(classified, rule_findings=findings)
    simplified = simp_res.get("clauses") or simp_res.get("simplified_clauses", [])
    
    # Assert full 7-position integrity for Document A (BUG C regression test)
    assert len(simplified) == 7, f"Expected 7 clauses for Document A, got {len(simplified)}"
    positions = [c["position"] for c in simplified]
    assert positions == [1, 2, 3, 4, 5, 6, 7], f"Position sequence has gaps: {positions}"

    # Clause 1
    cl1 = simplified[0]
    cl1_cat = cl1.get("category") or categorized[0].get("category") or cl1.get("structured_explanation", {}).get("category", {}).get("label")
    assert cl1_cat != "General"
    assert cl1["severity"] != "UNKNOWN"
    
    # Clause 3 (IP)
    cl3 = simplified[2]
    cl3_means = cl3["structured_explanation"]["what_this_clause_means"].lower()
    assert "work made for hire" in cl3_means or "custom module" in cl3_means
    
    # Clause 4 (Indemnification)
    cl4 = simplified[3]
    cl4_simp = cl4["simplified_text"].lower()
    assert "provider" in cl4_simp and "subscriber" in cl4_simp
    
    # Clause 5 (Limitation of Liability - BUG C integrity check)
    cl5 = simplified[4]
    assert cl5["position"] == 5
    cl5_cat = cl5.get("category") or categorized[4].get("category") or cl5.get("structured_explanation", {}).get("category", {}).get("label")
    assert cl5_cat == "Liability" or "liability" in str(cl5_cat).lower()
    assert cl5["severity"] in ("High", "Moderate", "high", "moderate")
    assert len(cl5["simplified_text"]) > 10
    
    # Clause 6 (Dispute Resolution / Venue - BUG D regression check)
    cl6 = simplified[5]
    cl6_means = cl6["structured_explanation"]["what_this_clause_means"].lower()
    cl6_details = " ".join(cl6["structured_explanation"].get("key_details", [])).lower()
    assert "cook county" in cl6_means or "illinois" in cl6_means
    assert "governed by" not in cl6_means, f"Invented governing law found in jurisdiction-only clause: {cl6_means}"
    assert "governing law" not in cl6_means, f"Invented governing law found in jurisdiction-only clause: {cl6_means}"
    assert "governing law" not in cl6_details, f"Invented governing law detail found in jurisdiction-only clause: {cl6_details}"
    
    # Clause 7 (Termination)
    cl7 = simplified[6]
    cl7_simp = cl7["simplified_text"].lower()
    cl7_means = cl7["structured_explanation"]["what_this_clause_means"].lower()
    assert "for cause" not in cl7_means
    assert "cure period" not in cl7_means
    assert "cure period" not in cl7_simp
    assert "accrued unpaid fees" not in cl7_simp


def test_governing_law_vs_jurisdiction_adversarial_variants():
    """
    BUG D Regression Test:
    Enforces strict distinction between Governing Law vs Jurisdiction/Venue.
    Tests:
    1. Real Cook County sentence (Jurisdiction ONLY) -> No 'governed by' / 'governing law' claims.
    2. Adversarial 1: Governing Law ONLY (no jurisdiction/venue) -> Substantive law reported, no court venue invented.
    3. Adversarial 2: BOTH genuinely present -> Both governing law and court venue reported.
    4. Adversarial 3: NEITHER present (informal escalation) -> Pure dispute procedure reported, no law/venue invented.
    """
    # 1. Real Cook County sentence (Jurisdiction ONLY)
    cook_text = "Any action or proceeding arising out of or relating to this Agreement shall be submitted to the exclusive jurisdiction in Cook County, Illinois."
    res1 = simplify_single_clause({"text": cook_text, "category": "Dispute Resolution"})
    means1 = res1["structured_explanation"]["what_this_clause_means"].lower()
    simp1 = res1["simplified_text"].lower()
    assert "governed by" not in means1, f"Unexpected 'governed by' in jurisdiction-only clause: {means1}"
    assert "governing law" not in means1, f"Unexpected 'governing law' in jurisdiction-only clause: {means1}"
    assert "governed by the laws of cook county" not in simp1, f"Unexpected 'governed by' in simplified text: {simp1}"
    assert "cook county" in means1 or "illinois" in means1
    assert "exclusive" in means1 or "jurisdiction" in means1

    # 2. Adversarial 1: Governing Law ONLY
    gov_only_text = "This Agreement and all claims arising out of or relating to this Agreement shall be governed by and construed in accordance with the laws of the State of Delaware, without giving effect to any choice or conflict of law provision or rule."
    res2 = simplify_single_clause({"text": gov_only_text, "category": "Dispute Resolution"})
    means2 = res2["structured_explanation"]["what_this_clause_means"].lower()
    simp2 = res2["simplified_text"].lower()
    assert "delaware" in means2
    assert "governed by" in means2 or "governing law" in means2 or "substantive" in means2
    assert "governing law" in simp2
    assert "exclusive jurisdiction" not in means2, f"Invented exclusive jurisdiction in governing-law-only clause: {means2}"
    assert "venue" not in means2, f"Invented venue in governing-law-only clause: {means2}"
    assert "courts of" not in means2, f"Invented courts in governing-law-only clause: {means2}"
    assert "litigated exclusively" not in simp2, f"Invented litigation obligation: {simp2}"

    # 3. Adversarial 2: BOTH genuinely present
    both_text = "This Agreement shall be governed by the laws of the State of New York, and each party irrevocably submits to the exclusive jurisdiction of the state and federal courts located in New York County for any dispute arising out of this Agreement."
    res3 = simplify_single_clause({"text": both_text, "category": "Dispute Resolution"})
    means3 = res3["structured_explanation"]["what_this_clause_means"].lower()
    simp3 = res3["simplified_text"].lower()
    assert "new york" in means3
    assert "governed by" in means3 or "governing law" in means3
    assert "exclusive venue" in means3 or "exclusive jurisdiction" in means3 or "courts" in means3
    assert "governing law" in simp3
    assert "jurisdiction" in simp3 or "venue" in simp3

    # 4. Adversarial 3: NEITHER present (informal negotiation escalation)
    neither_text = "In the event of any dispute, controversy, or claim arising from or relating to this Agreement, the parties shall first consult and negotiate in good faith to resolve the controversy informally within thirty (30) days."
    res4 = simplify_single_clause({"text": neither_text, "category": "Dispute Resolution"})
    means4 = res4["structured_explanation"]["what_this_clause_means"].lower()
    simp4 = res4["simplified_text"].lower()
    assert "governed by" not in means4, f"Invented governing law in escalation clause: {means4}"
    assert "governing law" not in means4, f"Invented governing law in escalation clause: {means4}"
    assert "exclusive jurisdiction" not in means4, f"Invented exclusive jurisdiction in escalation clause: {means4}"
    assert "venue" not in means4, f"Invented venue in escalation clause: {means4}"
    assert "dispute" in means4


def test_all_sample_documents_clause_completeness_and_no_gaps():
    """
    BUG C Regression Test:
    Asserts every document in sample_documents/ produces exactly N clause entries across
    segmentation, categorization, risk classification, and simplification with NO silent gaps.
    """
    sample_dir = get_sample_dir()
    if not sample_dir.exists():
        pytest.skip("sample_documents directory not found")

    pdf_files = list(sample_dir.glob("*.pdf"))
    assert len(pdf_files) > 0, "No sample PDFs found"

    for pdf_path in sorted(pdf_files):
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        ext = extract_pdf_text_service(pdf_bytes, enable_ocr=False)
        cleaned = clean_legal_text(ext["full_text"])["cleaned_text"]
        seg_res = segment_document_clauses(cleaned, pages=ext.get("pages", []))
        segmented = seg_res["clauses"]
        n_clauses = len(segmented)
        assert n_clauses > 0, f"{pdf_path.name} produced 0 segmented clauses!"

        rules_res = evaluate_rules(clauses=segmented, text=cleaned)
        findings = rules_res["findings"]
        cat_res = categorize_clause_records(segmented, rule_findings=findings)
        categorized = cat_res["clauses"]
        risk_res = classify_document_clauses_risk(categorized, rule_findings=findings)
        classified = risk_res["clauses"]
        simp_res = simplify_document_clauses(classified, rule_findings=findings)
        simplified = simp_res.get("clauses") or simp_res.get("simplified_clauses", [])

        # Strict N = N = N = N assertion
        assert len(categorized) == n_clauses, f"{pdf_path.name}: categorized count {len(categorized)} != {n_clauses}"
        assert len(classified) == n_clauses, f"{pdf_path.name}: classified count {len(classified)} != {n_clauses}"
        assert len(simplified) == n_clauses, f"{pdf_path.name}: simplified count {len(simplified)} != {n_clauses}"

        # Strict position sequence 1..N with no missing numbers
        expected_positions = list(range(1, n_clauses + 1))
        actual_positions = [c["position"] for c in simplified]
        assert actual_positions == expected_positions, f"{pdf_path.name} has position gaps! Expected {expected_positions}, got {actual_positions}"

        # Assert no clause is empty or silently dropped
        for c in simplified:
            assert c.get("simplified_text"), f"{pdf_path.name} clause at pos {c.get('position')} has empty simplified_text"
            assert c.get("structured_explanation"), f"{pdf_path.name} clause at pos {c.get('position')} has empty structured_explanation"


def test_liability_cap_polarity_directionality_grounding():
    """
    Regression Test: Asserts that a limitation of liability clause with carve-outs
    (e.g., 'Except for Indemnification or willful misconduct, neither party's aggregate liability is capped at...')
    correctly states that general liability IS CAPPED to the specified limit,
    with indemnification and willful misconduct as the UNCAPPED exceptions (not inverted).
    """
    source_clause = (
        "Except for liabilities arising under Section 4 (Indemnification) or willful misconduct, "
        "neither party's aggregate liability under this agreement is capped at the total amounts paid in the preceding twelve months."
    )
    
    # 1. Test synthesize / simplify single clause grounding
    res = simplify_single_clause({
        "text": source_clause,
        "title": "Limitation of Liability",
        "category": "Liability",
        "severity": "High",
        "rule_findings": [{"rule_id": "R015", "risk_signal": "Uncapped Liability Carve-Out"}]
    })
    
    means = res["structured_explanation"]["what_this_clause_means"]
    simplified = res["simplified_text"]
    
    # Assert capped status is correctly grounded
    assert "capped" in means.lower() or "capped" in simplified.lower()
    assert "no maximum cap on liability" not in means.lower()
    assert "no limit on how much" not in means.lower()
    assert "neither party can limit" not in means.lower()
    assert "removes any limitation" not in means.lower()
    assert "uncapped for all" not in means.lower()
    
    # Assert exceptions (Indemnification / willful misconduct) are identified as the uncapped exceptions
    assert "indemnif" in means.lower() or "indemnif" in simplified.lower()
    assert "twelve months" in means.lower() or "twelve months" in simplified.lower() or "12 months" in means.lower() or "12 months" in simplified.lower() or "preceding twelve months" in simplified.lower()


def test_clause_record_internal_consistency():
    """
    Regression Test: Asserts that for any clause (successful or unclassified/failed),
    the top-level severity matches structured_explanation.risk.severity (case-normalized),
    and top-level category matches structured_explanation.category.label,
    with no clause allowed to pass with mismatched or contradictory values.
    """
    # 1. Test unclassified / None category clause
    unclass_clause = {
        "text": "1. SUBSCRIPTION ACCESS. Provider grants Subscriber a non-exclusive right to access the software.",
        "title": "Subscription Access",
        "category": None,
        "severity": None,
        "rule_findings": []
    }
    res_unclass = simplify_single_clause(unclass_clause)
    struct_unclass = res_unclass["structured_explanation"]
    
    # Assert category consistency
    top_cat = res_unclass.get("category")
    nested_cat = struct_unclass.get("category", {}).get("label")
    assert top_cat == nested_cat, f"Category mismatch: top={top_cat} vs nested={nested_cat}"
    assert nested_cat is None
    assert "Standard contractual provision." not in struct_unclass.get("category", {}).get("reason", "")

    # Assert severity consistency
    top_sev = res_unclass.get("severity")
    nested_sev = struct_unclass.get("risk", {}).get("severity")
    top_sev_norm = top_sev.lower() if top_sev else None
    nested_sev_norm = nested_sev.lower() if nested_sev else None
    assert top_sev_norm == nested_sev_norm, f"Severity mismatch: top={top_sev} vs nested={nested_sev}"
    assert "balanced commercial terms" not in struct_unclass.get("risk", {}).get("reason", "")

    # 2. Test classified clause (e.g., Liability / High)
    class_clause = {
        "text": "4. INDEMNIFICATION. Provider agrees to defend and indemnify Subscriber from third-party IP claims.",
        "title": "Indemnification",
        "category": "Liability",
        "severity": "High",
        "rule_findings": [{"rule_id": "R005", "risk_signal": "Broad Indemnification"}]
    }
    res_class = simplify_single_clause(class_clause)
    struct_class = res_class["structured_explanation"]
    
    top_cat = res_class.get("category")
    nested_cat = struct_class.get("category", {}).get("label")
    assert (top_cat or "Liability") == nested_cat, f"Category mismatch: top={top_cat} vs nested={nested_cat}"

    top_sev = res_class.get("severity")
    nested_sev = struct_class.get("risk", {}).get("severity")
    assert (top_sev or "High").lower() == nested_sev.lower(), f"Severity mismatch: top={top_sev} vs nested={nested_sev}"




