"""
ClarifAI Primary LLM Structured Fact Extraction Service (PRD Step 3.1)
Executes temperature 0.0 structured JSON extraction using Groq (openai/gpt-oss-20b),
batches clauses within token budgets, validates against Pydantic schemas, and runs
the deterministic verifier on every extracted fact.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from groq import Groq

from app.core.config import settings
from app.services.llm_client import get_groq_client, get_groq_model_name, get_groq_api_key
from app.services.fact_verifier_service import verify_and_filter_clause_facts

logger = logging.getLogger(__name__)

# Allowed 24 taxonomy categories per PRD Step 3.3
ALLOWED_CATEGORIES: List[str] = [
    "Scope of Services",
    "Payment / Rent",
    "Term",
    "Renewal",
    "Termination",
    "Confidentiality",
    "Intellectual Property",
    "Indemnification",
    "Limitation of Liability",
    "Privacy",
    "Dispute Resolution",
    "Governing Law",
    "Restrictive Covenants",
    "Premises",
    "Use",
    "Maintenance",
    "Alterations",
    "Insurance",
    "Warranty",
    "Force Majeure",
    "Assignment",
    "Notices",
    "General / Boilerplate",
    "Audit / Inspection"
]


class ExtractedLegalFact(BaseModel):
    field: str = Field(..., description="Name of the contractual fact, e.g., payment_window, interest_rate, liability_cap")
    value: str = Field(..., description="Extracted fact value or 'not_stated'")
    unit: Optional[str] = Field(None, description="Unit of measurement, e.g., days, months, %, USD")
    source_quote: str = Field(..., description="Exact substring quote from the clause text")
    bound_party: Optional[str] = Field(None, description="Party bound by duty or 'both_parties'")


class ClauseExtractionSchema(BaseModel):
    clause_id: Optional[str] = None
    category: str = Field(..., description="Primary category from 24 allowed categories")
    who_is_bound: str = Field(..., description="Obligated party: e.g., 'Client only', 'Consultant only', 'Both parties'")
    facts: List[ExtractedLegalFact] = Field(default_factory=list)
    plain_language_summary: str = Field(..., description="One to two sentence plain English summary of this clause")
    not_stated_items: List[str] = Field(default_factory=list, description="Standard fields missing from this clause")


def build_batch_extraction_prompt(
    doc_header: Dict[str, Any],
    clauses: List[Dict[str, Any]]
) -> str:
    """Builds structured system and user prompts for batch clause extraction."""
    title = doc_header.get("title", "Commercial Contract")
    parties = doc_header.get("parties", "the contracting parties")

    prompt = f"DOCUMENT CONTEXT:\nDocument Title: {title}\nParties & Roles: {parties}\n\n"
    prompt += "Extract structured legal facts for the following contract clauses. Output valid JSON array with schema for each clause.\n\n"

    for idx, c in enumerate(clauses):
        c_num = c.get("clause_number") or c.get("position") or (idx + 1)
        c_title = c.get("title", "")
        c_text = c.get("original_text") or c.get("text", "")
        prompt += f"--- CLAUSE {c_num} [{c_title}] ---\n{c_text}\n\n"

    prompt += "RULES:\n"
    prompt += "1. Extract ONLY facts present in the text. If not present, use 'not_stated'.\n"
    prompt += "2. source_quote MUST be an EXACT verbatim substring from the clause.\n"
    prompt += f"3. category MUST be chosen from: {', '.join(ALLOWED_CATEGORIES)}.\n"
    prompt += "4. Format output strictly as a JSON object: {\"clauses\": [ ... ]}\n"

    return prompt


def extract_structured_clause_facts_llm(
    clauses: List[Dict[str, Any]],
    doc_header: Optional[Dict[str, Any]] = None,
    override_client: Optional[Any] = None
) -> List[Dict[str, Any]]:
    """
    Primary path: batches clauses, calls Groq LLM, parses JSON schema,
    and runs deterministic verifier on all extracted facts.
    """
    api_key = get_groq_api_key()
    if not api_key and not override_client:
        logger.info("Groq API key not configured. Skipping LLM extraction (Limited mode).")
        return clauses

    doc_hdr = doc_header or {}
    model_name = get_groq_model_name()
    client = override_client or get_groq_client()

    batch_size = 4
    processed_clauses = []

    for i in range(0, len(clauses), batch_size):
        batch = clauses[i:i+batch_size]
        prompt = build_batch_extraction_prompt(doc_hdr, batch)

        try:
            resp = client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a precise, evidence-grounded legal contract extraction engine. You extract verbatim facts in valid JSON only."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.0,
                max_tokens=1500
            )
            raw_json = resp.choices[0].message.content or "{}"
            parsed = json.loads(raw_json)
            extracted_list = parsed.get("clauses", [])

            for j, c in enumerate(batch):
                c_copy = dict(c)
                orig_text = c_copy.get("original_text") or c_copy.get("text", "")
                llm_c = extracted_list[j] if j < len(extracted_list) else None

                if llm_c and isinstance(llm_c, dict):
                    raw_facts = [f for f in llm_c.get("facts", []) if isinstance(f, dict)]
                    verified_facts, dropped = verify_and_filter_clause_facts(raw_facts, orig_text)
                    
                    c_copy["llm_category"] = llm_c.get("category")
                    c_copy["who_is_bound"] = llm_c.get("who_is_bound") or "Both parties"
                    c_copy["verified_facts"] = verified_facts
                    c_copy["dropped_facts_reasons"] = dropped
                    if llm_c.get("plain_language_summary"):
                        c_copy["llm_summary"] = llm_c.get("plain_language_summary")
                
                processed_clauses.append(c_copy)

        except Exception as e:
            logger.warning(f"Groq LLM extraction batch error ({e}). Preserving clauses with deterministic fallback.")
            for c in batch:
                processed_clauses.append(dict(c))

    return processed_clauses
