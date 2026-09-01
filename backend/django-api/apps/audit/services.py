"""
Audit Log Services and helper functions for recording security events (PRD Ch. 26.8 & Ch. 29.8).
"""
import logging
from apps.audit.models import AuditLog

logger = logging.getLogger(__name__)

# Mandatory event types per PRD Ch. 26.8
EVENT_LOGIN_SUCCESS = 'login_success'
EVENT_LOGIN_FAILURE = 'login_failure'
EVENT_SIGNUP = 'signup'
EVENT_DOCUMENT_UPLOAD = 'document_upload'
EVENT_DOCUMENT_DELETE = 'document_delete'
EVENT_ANALYSIS_FAILURE = 'analysis_failure'


def log_audit_event(event_type: str, user=None, request=None, metadata: dict = None) -> AuditLog:
    """
    Records a structured audit log entry per PRD Ch. 26.8 & Ch. 29.8.
    
    Security & Privacy Enforcement:
    - Never logs passwords, tokens, API keys, or raw confidential contract text.
    - Sanitizes metadata keys to prevent accidental sensitive data leakage.
    - Sets user=None for unauthenticated or non-existent account login failures
      to avoid leaking account existence through log queries (Ch. 26.8).
    """
    safe_metadata = metadata.copy() if metadata else {}

    # Strip any accidental sensitive keys from metadata payload
    forbidden_keys = {'password', 'token', 'secret', 'api_key', 'raw_text', 'content', 'clause_text', 'original_text'}
    for key in list(safe_metadata.keys()):
        if key.lower() in forbidden_keys:
            safe_metadata.pop(key, None)

    if request:
        ip_address = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))
        if ip_address:
            ip_address = ip_address.split(',')[0].strip()
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if ip_address:
            safe_metadata['ip_address'] = ip_address
        if user_agent:
            safe_metadata['user_agent'] = user_agent[:255]

    try:
        log_entry = AuditLog.objects.create(
            user=user if (user and getattr(user, 'is_authenticated', True)) else None,
            event_type=event_type,
            metadata=safe_metadata
        )
        return log_entry
    except Exception as exc:
        logger.error(f"Failed to record audit log entry [{event_type}]: {exc}")
        return None
