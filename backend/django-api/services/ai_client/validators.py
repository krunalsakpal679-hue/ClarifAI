"""
AI Response Validation Layer (PRD Ch. 49.3, Ch. 56.9).
Strictly validates incoming AI service response payloads.
Rejects malformed outputs, invalid severity values, or unlisted risk categories with AIServiceValidationError.
Never auto-corrects or silently accepts corrupt schemas.
"""
from services.ai_client.exceptions import AIServiceValidationError

ALLOWED_SEVERITIES = {'high', 'moderate', 'low', 'safe'}
ALLOWED_CATEGORIES = {
    'Payment',
    'Termination',
    'Renewal',
    'Confidentiality',
    'Liability',
    'Intellectual Property',
    'Privacy',
    'Dispute Resolution',
}


def validate_clause(clause_data: dict) -> dict:
    """
    Validates an individual clause structure against PRD Ch. 16.1 (4 severity levels)
    and Ch. 16.2 (fixed 8 risk categories).
    """
    if not isinstance(clause_data, dict):
        raise AIServiceValidationError("Clause item must be a dictionary.")

    severity = clause_data.get('severity')
    if severity not in ALLOWED_SEVERITIES:
        raise AIServiceValidationError(
            f"Invalid clause severity '{severity}'. Allowed: {sorted(list(ALLOWED_SEVERITIES))}"
        )

    category = clause_data.get('category')
    if category not in ALLOWED_CATEGORIES:
        raise AIServiceValidationError(
            f"Invalid risk category '{category}'. Allowed: {sorted(list(ALLOWED_CATEGORIES))}"
        )

    if not isinstance(clause_data.get('original_text'), str) or not clause_data.get('original_text'):
        raise AIServiceValidationError("Clause 'original_text' must be a non-empty string.")

    if not isinstance(clause_data.get('simplified_text'), str):
        raise AIServiceValidationError("Clause 'simplified_text' must be a string.")

    if not isinstance(clause_data.get('explanation'), str):
        raise AIServiceValidationError("Clause 'explanation' must be a string.")

    return clause_data


def validate_process_document_response(data: dict) -> dict:
    """
    Validates complete document processing response payload.
    Must contain 'clauses' list and 'summary' dictionary.
    """
    if not isinstance(data, dict):
        raise AIServiceValidationError("Process document response must be a dictionary.")

    clauses = data.get('clauses')
    if not isinstance(clauses, list):
        raise AIServiceValidationError("Process document response must contain a 'clauses' list.")

    for idx, clause in enumerate(clauses):
        try:
            validate_clause(clause)
        except AIServiceValidationError as exc:
            raise AIServiceValidationError(f"Invalid clause at index {idx}: {exc}") from exc

    summary = data.get('summary')
    if not isinstance(summary, dict) and not isinstance(summary, str):
        raise AIServiceValidationError("Process document response must contain a valid 'summary'.")

    return data


def validate_chat_response(data: dict) -> dict:
    """
    Validates RAG Chat response payload.
    Must contain 'answer' string and optional 'source_clause_ids' list.
    """
    if not isinstance(data, dict):
        raise AIServiceValidationError("Chat response must be a dictionary.")

    answer = data.get('answer')
    if not isinstance(answer, str) or not answer.strip():
        raise AIServiceValidationError("Chat response must contain a non-empty 'answer' string.")

    source_ids = data.get('source_clause_ids', [])
    if not isinstance(source_ids, list):
        raise AIServiceValidationError("Chat response 'source_clause_ids' must be a list.")

    return data


def validate_compare_response(data: dict) -> dict:
    """
    Validates document comparison response payload.
    Must contain comparison results structure ('changed', 'matched', 'missing' or 'differences').
    """
    if not isinstance(data, dict):
        raise AIServiceValidationError("Compare response must be a dictionary.")

    if 'differences' in data:
        if not isinstance(data['differences'], list):
            raise AIServiceValidationError("Compare response 'differences' must be a list.")
    elif all(k in data for k in ('changed', 'matched', 'missing')):
        for key in ('changed', 'matched', 'missing'):
            if not isinstance(data[key], list):
                raise AIServiceValidationError(f"Compare response '{key}' must be a list.")
    else:
        raise AIServiceValidationError(
            "Compare response must contain 'differences' or ('changed', 'matched', 'missing') lists."
        )

    return data


def validate_translate_response(data: dict) -> dict:
    """
    Validates translation response payload.
    Must contain 'target_lang' string and 'translated_content' string or dict.
    """
    if not isinstance(data, dict):
        raise AIServiceValidationError("Translate response must be a dictionary.")

    target_lang = data.get('target_lang')
    if not isinstance(target_lang, str) or not target_lang.strip():
        raise AIServiceValidationError("Translate response must contain a non-empty 'target_lang' string.")

    translated_content = data.get('translated_content')
    if translated_content is None:
        raise AIServiceValidationError("Translate response must contain 'translated_content'.")

    return data
