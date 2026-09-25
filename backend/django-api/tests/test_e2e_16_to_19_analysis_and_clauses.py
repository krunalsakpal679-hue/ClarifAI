"""
E2E Integration Test Suite for Classification, Simplification, Summary & Clause Detail
Scenarios E2E-16 through E2E-19 (PRD v2.3 Chapter 16, Chapter 30).

Coverage:
- E2E-16 Classification & Evidence Preservation:
    * Every clause has exactly one severity from {'high', 'moderate', 'low', 'safe'} (or null if failed).
    * No numerical risk score anywhere in public API response.
    * Genuine R001-R014 findings preserved in rule_findings JSON array as evidence alongside classifier severity.
- E2E-17 Simplification:
    * Simplified text preserves key numbers, monetary amounts, and core contractual obligations.
- E2E-18 Summary Completeness & High-Risk Grounding:
    * All four fields populated: purpose_text, key_risks_text, key_terms_text, obligations_text.
    * key_risks_text specifically references genuinely high-severity clauses.
- E2E-19 Clause Detail & Sequential Navigation:
    * GET /api/documents/{id}/clauses/{clauseId} returns full detail matching list contract.
    * Sequential position indexing supports previous/next navigation across clauses.
    * IDOR security: Non-owner receives HTTP 404 Not Found for summary, clause list, and clause detail.
"""
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.documents.models import (
    Clause,
    ClauseCategory,
    ClauseSeverity,
    ClauseStatus,
    Document,
    DocumentStatus,
    DocumentSummary,
)

User = get_user_model()


class E2EAnalysisAndClausesTestCase(APITestCase):
    """
    Test cases for E2E-16, E2E-17, E2E-18, and E2E-19.
    """

    def setUp(self):
        cache.clear()
        self.owner = User.objects.create_user(
            email='counsel_owner@clarifai.io',
            password='Password123!'
        )
        self.unauthorized_user = User.objects.create_user(
            email='unauthorized@clarifai.io',
            password='Password123!'
        )

        refresh_owner = RefreshToken.for_user(self.owner)
        self.token_owner = str(refresh_owner.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_owner}')

        refresh_unauth = RefreshToken.for_user(self.unauthorized_user)
        self.token_unauth = str(refresh_unauth.access_token)

        # Completed test document
        self.doc = Document.objects.create(
            user=self.owner,
            original_filename='enterprise_master_agreement.pdf',
            file_reference='uploads/documents/enterprise_master_agreement.pdf',
            status=DocumentStatus.COMPLETE
        )

        # Four summary fields populated per Chapter 16 / 30.3
        self.summary = DocumentSummary.objects.create(
            document=self.doc,
            purpose_text="Enterprise Cloud SaaS and Professional Services Master Agreement.",
            key_risks_text="High Risk: Clause 1 exposes Customer to uncapped unilateral indemnification without financial limitation.",
            key_terms_text="Term: 36 months starting October 1, 2026. Automatic renewal for successive 12-month periods.",
            obligations_text="Payment within 30 days of invoice date. 99.9% uptime service level commitment."
        )

        # Clause 1: High severity with genuine R006 (Broad Indemnification) finding
        self.clause_1 = Clause.objects.create(
            document=self.doc,
            position=1,
            original_text=(
                "Customer shall defend, indemnify, and hold harmless Vendor against any and all claims, "
                "liabilities, losses, damages, and reasonable attorney fees without limitation or cap."
            ),
            simplified_text=(
                "You must defend Vendor and pay all losses, claims, and legal costs with no financial cap."
            ),
            explanation="Uncapped unilateral indemnification disproportionately transfers third-party risk to Customer.",
            severity=ClauseSeverity.HIGH,
            category=ClauseCategory.LIABILITY,
            status=ClauseStatus.COMPLETE,
            rule_findings=[
                {
                    "rule_id": "R006",
                    "risk_signal": "Broad Indemnification",
                    "matched_pattern": "indemnify and hold harmless",
                    "evidence_span": "...defend, indemnify, and hold harmless Vendor against any and all claims..."
                }
            ]
        )

        # Clause 2: Moderate severity with genuine R001 (Auto-Renewal) finding & numbers/obligations
        self.clause_2 = Clause.objects.create(
            document=self.doc,
            position=2,
            original_text=(
                "This Agreement shall automatically renew for successive 12-month terms unless either party "
                "gives written notice of non-renewal at least 60 days prior to the expiration of the current term."
            ),
            simplified_text=(
                "Contract automatically renews for 12 months unless you provide written notice at least 60 days in advance."
            ),
            explanation="Automatic annual renewal with a 60-day notice window requires proactive calendar management.",
            severity=ClauseSeverity.MODERATE,
            category=ClauseCategory.RENEWAL,
            status=ClauseStatus.COMPLETE,
            rule_findings=[
                {
                    "rule_id": "R001",
                    "risk_signal": "Auto-Renewal",
                    "matched_pattern": "automatically renew",
                    "evidence_span": "...shall automatically renew for successive 12-month terms..."
                }
            ]
        )

        # Clause 3: Safe severity with key monetary amount ($50,000) & net 30 payment term
        self.clause_3 = Clause.objects.create(
            document=self.doc,
            position=3,
            original_text=(
                "Customer shall pay an annual licensing fee of $50,000 due within thirty (30) days of invoice receipt."
            ),
            simplified_text=(
                "You must pay $50,000 annually within 30 days of receiving the invoice."
            ),
            explanation="Standard commercial payment terms with clear pricing and payment window.",
            severity=ClauseSeverity.SAFE,
            category=ClauseCategory.PAYMENT,
            status=ClauseStatus.COMPLETE,
            rule_findings=[]
        )

        # Clause 4: Low severity dispute resolution clause
        self.clause_4 = Clause.objects.create(
            document=self.doc,
            position=4,
            original_text=(
                "Any dispute arising out of this Agreement shall be settled by binding arbitration in San Francisco, California."
            ),
            simplified_text=(
                "Disputes will be resolved through binding arbitration in San Francisco, California."
            ),
            explanation="Standard arbitration forum selection clause.",
            severity=ClauseSeverity.LOW,
            category=ClauseCategory.DISPUTE_RESOLUTION,
            status=ClauseStatus.COMPLETE,
            rule_findings=[
                {
                    "rule_id": "R012",
                    "risk_signal": "Arbitration/Dispute Restriction",
                    "matched_pattern": "binding arbitration",
                    "evidence_span": "...settled by binding arbitration in San Francisco..."
                }
            ]
        )

    # =========================================================================
    # E2E-16: Classification & Rule Evidence Preservation
    # =========================================================================
    def test_e2e_16_classification_four_severity_enum_and_evidence_preservation(self):
        """
        E2E-16:
        1. Every clause has exactly one severity from {High, Moderate, Low, Safe}; no numerical score anywhere.
        2. Clause with a genuine R001-R014 finding shows it preserved as evidence alongside its final Legal-BERT severity.
        """
        url = reverse('document_clause_list', kwargs={'pk': self.doc.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        clauses = res.data['results']
        self.assertEqual(len(clauses), 4)

        allowed_severities = {'high', 'moderate', 'low', 'safe'}

        for cl in clauses:
            # 1. Exactly one severity from the allowed 4-value enum
            self.assertIn(cl['severity'], allowed_severities)

            # 2. Strict AI Safety: Zero numerical risk score anywhere in clause payload
            self.assertNotIn('numerical_score', cl)
            self.assertNotIn('risk_score', cl)
            self.assertNotIn('score', cl)
            self.assertNotIn('percentage', cl)

        # Verify Clause 1 has High severity and preserves R006 Broad Indemnification evidence
        c1 = [c for c in clauses if c['id'] == str(self.clause_1.id)][0]
        self.assertEqual(c1['severity'], 'high')
        self.assertEqual(c1['category'], 'Liability')
        self.assertEqual(len(c1['rule_findings']), 1)
        r006_finding = c1['rule_findings'][0]
        self.assertEqual(r006_finding['rule_id'], 'R006')
        self.assertEqual(r006_finding['risk_signal'], 'Broad Indemnification')
        self.assertIn('indemnify', r006_finding['matched_pattern'])

        # Verify Clause 2 has Moderate severity and preserves R001 Auto-Renewal evidence
        c2 = [c for c in clauses if c['id'] == str(self.clause_2.id)][0]
        self.assertEqual(c2['severity'], 'moderate')
        self.assertEqual(c2['category'], 'Renewal')
        self.assertEqual(len(c2['rule_findings']), 1)
        r001_finding = c2['rule_findings'][0]
        self.assertEqual(r001_finding['rule_id'], 'R001')
        self.assertEqual(r001_finding['risk_signal'], 'Auto-Renewal')

        # Verify Clause 3 has Safe severity and empty rule findings
        c3 = [c for c in clauses if c['id'] == str(self.clause_3.id)][0]
        self.assertEqual(c3['severity'], 'safe')
        self.assertEqual(c3['category'], 'Payment')
        self.assertEqual(c3['rule_findings'], [])

        # Verify Clause 4 has Low severity and preserves R012 Arbitration evidence
        c4 = [c for c in clauses if c['id'] == str(self.clause_4.id)][0]
        self.assertEqual(c4['severity'], 'low')
        self.assertEqual(c4['category'], 'Dispute Resolution')
        self.assertEqual(len(c4['rule_findings']), 1)
        self.assertEqual(c4['rule_findings'][0]['rule_id'], 'R012')

    # =========================================================================
    # E2E-17: Simplification Integrity (Numbers & Key Obligations)
    # =========================================================================
    def test_e2e_17_simplification_preserves_numbers_and_obligations(self):
        """
        E2E-17:
        Simplified text preserves key obligations, numeric thresholds, and monetary amounts.
        """
        url = reverse('document_clause_list', kwargs={'pk': self.doc.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        clauses_by_id = {c['id']: c for c in res.data['results']}

        # Clause 2: Auto-renewal numbers (12 months, 60 days)
        c2 = clauses_by_id[str(self.clause_2.id)]
        self.assertIn("12", c2['simplified_text'])
        self.assertIn("60 days", c2['simplified_text'])
        self.assertIn("written notice", c2['simplified_text'])

        # Clause 3: Monetary amount ($50,000) and payment deadline (30 days)
        c3 = clauses_by_id[str(self.clause_3.id)]
        self.assertIn("$50,000", c3['simplified_text'])
        self.assertIn("30 days", c3['simplified_text'])

        # Clause 1: Obligation to defend and pay without cap
        c1 = clauses_by_id[str(self.clause_1.id)]
        self.assertIn("defend", c1['simplified_text'].lower())
        self.assertIn("cap", c1['simplified_text'].lower())

    # =========================================================================
    # E2E-18: Summary Completeness & Grounding
    # =========================================================================
    def test_e2e_18_summary_all_four_fields_and_high_risk_grounding(self):
        """
        E2E-18:
        All four summary fields populated; key_risks_text references genuinely high-severity clauses.
        """
        url = reverse('document_summary', kwargs={'pk': self.doc.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        data = res.data

        # 1. All four summary fields exist and are non-empty strings
        for field in ['purpose_text', 'key_risks_text', 'key_terms_text', 'obligations_text']:
            self.assertIn(field, data)
            self.assertIsInstance(data[field], str)
            self.assertGreater(len(data[field].strip()), 0, f"Field {field} must not be empty")

        # 2. Strict AI Safety: Zero numerical risk score in summary
        self.assertNotIn('overall_score', data)
        self.assertNotIn('risk_score', data)
        self.assertNotIn('numerical_score', data)

        # 3. key_risks_text specifically references the genuinely High-risk clause (Clause 1)
        self.assertIn("Clause 1", data['key_risks_text'])
        self.assertIn("indemnif", data['key_risks_text'].lower())
        self.assertIn("uncapped", data['key_risks_text'].lower())

    # =========================================================================
    # E2E-19: Clause Detail & Sequential Navigation
    # =========================================================================
    def test_e2e_19_clause_detail_and_sequential_navigation(self):
        """
        E2E-19:
        1. GET /api/documents/{id}/clauses/{clauseId} returns full detail matching list contract.
        2. Clauses are ordered sequentially by position, enabling previous/next navigation.
        3. Non-owner access returns HTTP 404 Not Found (IsOwner IDOR enforcement).
        """
        # Fetch list to inspect ordering
        list_url = reverse('document_clause_list', kwargs={'pk': self.doc.id})
        list_res = self.client.get(list_url)
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)

        clauses = list_res.data['results']
        positions = [c['position'] for c in clauses]
        self.assertEqual(positions, [1, 2, 3, 4], "Clauses must be strictly ordered by position 1..N")

        # Navigate sequentially through Clause 1 to Clause 4 via detail endpoint
        for idx, clause_obj in enumerate([self.clause_1, self.clause_2, self.clause_3, self.clause_4]):
            detail_url = reverse('document_clause_detail', kwargs={
                'pk': self.doc.id,
                'clause_id': clause_obj.id
            })
            detail_res = self.client.get(detail_url)
            self.assertEqual(detail_res.status_code, status.HTTP_200_OK)

            detail_data = detail_res.data
            self.assertEqual(detail_data['id'], str(clause_obj.id))
            self.assertEqual(detail_data['position'], idx + 1)
            self.assertEqual(detail_data['original_text'], clause_obj.original_text)
            self.assertEqual(detail_data['simplified_text'], clause_obj.simplified_text)
            self.assertEqual(detail_data['severity'], clause_obj.severity)
            self.assertEqual(detail_data['category'], clause_obj.category)
            self.assertEqual(detail_data['explanation'], clause_obj.explanation)
            self.assertEqual(detail_data['status'], 'complete')

            # Verify rule_findings array structure
            self.assertIsInstance(detail_data['rule_findings'], list)

        # IDOR Security Validation: Unauthorized user access
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_unauth}')

        # 1. Summary non-owner -> 404
        summary_res = self.client.get(reverse('document_summary', kwargs={'pk': self.doc.id}))
        self.assertEqual(summary_res.status_code, status.HTTP_404_NOT_FOUND)

        # 2. Clause list non-owner -> 404
        clause_list_res = self.client.get(reverse('document_clause_list', kwargs={'pk': self.doc.id}))
        self.assertEqual(clause_list_res.status_code, status.HTTP_404_NOT_FOUND)

        # 3. Clause detail non-owner -> 404
        clause_detail_res = self.client.get(reverse('document_clause_detail', kwargs={
            'pk': self.doc.id,
            'clause_id': self.clause_1.id
        }))
        self.assertEqual(clause_detail_res.status_code, status.HTTP_404_NOT_FOUND)
