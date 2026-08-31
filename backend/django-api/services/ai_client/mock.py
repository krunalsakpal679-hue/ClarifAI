"""
Mock AI Client Implementation (PRD Phase 7).
Provides realistic, schema-validated mock data for development and testing.
Supports simulation modes for testing malformed responses, network failures, rate-limiting, and service errors.
"""
import logging
from services.ai_client.exceptions import (
    AIServiceConnectionError,
    AIServiceRateLimitError,
    AIServiceUnavailableError,
)
from services.ai_client.validators import (
    validate_chat_response,
    validate_compare_response,
    validate_process_document_response,
    validate_translate_response,
)

logger = logging.getLogger(__name__)


class MockAIClient:
    """
    Mock AI Client providing identical function signatures to RealAIClient.
    Used during development and unit testing when AI_SERVICE_USE_MOCK = True.
    """

    def __init__(self, simulation_mode: str = None):
        """
        :param simulation_mode: Optional test mode ('malformed', 'network_failure', 'rate_limit', 'unavailable')
        """
        self.simulation_mode = simulation_mode

    def _check_simulation(self):
        """Triggers simulated failure conditions if configured."""
        if self.simulation_mode == 'network_failure':
            raise AIServiceConnectionError("Simulated network connection drop to AI microservice after retry.")
        elif self.simulation_mode == 'rate_limit':
            raise AIServiceRateLimitError("Simulated 429 Rate Limit / Free-tier quota exhaustion.")
        elif self.simulation_mode == 'unavailable':
            raise AIServiceUnavailableError("Simulated 503 Internal AI Service Unavailable.")

    def process_document(self, document_id: str, file_reference: str) -> dict:
        """Mock document processing pipeline (extraction, risk classification, simplification, summarization)."""
        self._check_simulation()

        if self.simulation_mode == 'malformed':
            # Returns payload with invalid severity enum to test validation rejection
            raw_response = {
                "document_id": str(document_id),
                "summary": "Sample legal document summary.",
                "clauses": [
                    {
                        "severity": "extreme",  # Invalid severity value
                        "category": "Payment",
                        "original_text": "Payment is due in 30 days.",
                        "simplified_text": "Pay within 30 days.",
                        "explanation": "Standard payment terms."
                    }
                ]
            }
        else:
            raw_response = {
                "document_id": str(document_id),
                "summary": {
                    "overview": "Standard commercial agreement detailing payment, confidentiality, and liability terms.",
                    "key_points": [
                        "Net 30 payment terms",
                        "Standard 2-year confidentiality requirement",
                        "Limitation of liability capped at total contract value"
                    ]
                },
                "clauses": [
                    {
                        "clause_id": "c-001",
                        "severity": "high",
                        "category": "Liability",
                        "original_text": "In no event shall either party be liable for any indirect, incidental, special, or consequential damages.",
                        "simplified_text": "Neither party is responsible for indirect or accidental damages.",
                        "explanation": "Limits liability scope, protecting against high consequential damages.",
                        "rule_findings": [{"rule_id": "R-101", "risk_score": 0.85}]
                    },
                    {
                        "clause_id": "c-002",
                        "severity": "moderate",
                        "category": "Payment",
                        "original_text": "Invoices are payable within 30 days of receipt, subject to a 1.5% monthly late fee.",
                        "simplified_text": "Pay invoices within 30 days or pay a 1.5% late fee per month.",
                        "explanation": "Includes late payment penalties.",
                        "rule_findings": [{"rule_id": "R-202", "risk_score": 0.50}]
                    },
                    {
                        "clause_id": "c-003",
                        "severity": "safe",
                        "category": "Confidentiality",
                        "original_text": "Each party agrees to maintain the confidentiality of proprietary information.",
                        "simplified_text": "Both parties must keep shared private information secret.",
                        "explanation": "Standard mutual confidentiality clause.",
                        "rule_findings": []
                    }
                ]
            }

        return validate_process_document_response(raw_response)

    def chat(self, document_id: str, message: str, history: list = None) -> dict:
        """Mock RAG Chat response with legal-boundary framing (PRD Ch. 56.38)."""
        self._check_simulation()

        if self.simulation_mode == 'malformed':
            raw_response = {"answer": ""}  # Empty string fails validation
        else:
            raw_response = {
                "document_id": str(document_id),
                "answer": (
                    f"Based on the document analysis: The contract specifies Net 30 payment terms and mutual confidentiality. "
                    f"Please note: ClarifAI provides automated document analysis for information purposes only and does NOT constitute legal advice."
                ),
                "source_clause_ids": ["c-001", "c-002"],
                "disclaimer": "This system provides analysis, not legal advice."
            }

        return validate_chat_response(raw_response)

    def compare(self, document_a_id: str, document_b_id: str) -> dict:
        """Mock document comparison response."""
        self._check_simulation()

        if self.simulation_mode == 'malformed':
            raw_response = {"changed": "not a list"}  # String instead of list fails validation
        else:
            raw_response = {
                "document_a_id": str(document_a_id),
                "document_b_id": str(document_b_id),
                "changed": [
                    {
                        "category": "Payment",
                        "doc_a_clause": "Payment within 30 days.",
                        "doc_b_clause": "Payment within 15 days.",
                        "risk_change": "Increased liability in Version B due to shorter payment window."
                    }
                ],
                "matched": [
                    {
                        "category": "Confidentiality",
                        "clause_text": "Mutual non-disclosure for 2 years."
                    }
                ],
                "missing": [
                    {
                        "category": "Dispute Resolution",
                        "doc_a_clause": "Mandatory binding arbitration in New York.",
                        "doc_b_clause": None
                    }
                ]
            }

        return validate_compare_response(raw_response)

    def translate(self, document_id: str, target_lang: str, fields: list = None) -> dict:
        """Mock document translation response."""
        self._check_simulation()

        if self.simulation_mode == 'malformed':
            raw_response = {"target_lang": ""}  # Empty string fails validation
        else:
            raw_response = {
                "document_id": str(document_id),
                "target_lang": target_lang,
                "translated_content": {
                    "summary": "यह एक मानक वाणिज्यिक समझौता है।",
                    "key_clauses": [
                        "भुगतान 30 दिनों के भीतर देय है।",
                        "गोपनीयता की अवधि 2 वर्ष है।"
                    ]
                }
            }

        return validate_translate_response(raw_response)
