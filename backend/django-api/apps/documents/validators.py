"""
Server-side security validation pipeline for uploaded PDF files (PRD Ch. 14, 26.3, 58).
"""
import pypdf
from django.conf import settings
from rest_framework.exceptions import ValidationError


def validate_pdf_upload(uploaded_file):
    """
    Enforces sequential server-side validation per PRD Ch. 14/26.3:
    1. Size Validation (<= 20MB, resolved decision R-11)
    2. File Type Validation (genuine %PDF- magic bytes check)
    3. PDF Structure Validation (structural sanity check via pypdf)
    4. Encryption/Password Check (reject password-protected PDFs with distinct message, R-12)
    """
    max_mb = getattr(settings, 'MAX_UPLOAD_SIZE_MB', 20)
    max_bytes = max_mb * 1024 * 1024

    # 1. Size Validation
    if uploaded_file.size > max_bytes:
        raise ValidationError(f"File size exceeds the maximum limit of {max_mb}MB.")

    # 2. File Type Validation (genuine magic bytes header check)
    header_bytes = uploaded_file.read(1024)
    uploaded_file.seek(0)

    if not header_bytes or b'%PDF-' not in header_bytes:
        raise ValidationError("Uploaded file is not a genuine PDF document.")

    # 3 & 4. PDF Structure & Encryption Validation via pypdf
    try:
        reader = pypdf.PdfReader(uploaded_file)
        
        # 4. Explicit Password Protection / Encryption Check (Distinct error message per R-12)
        if reader.is_encrypted:
            raise ValidationError(
                "Password-protected PDFs are not supported. Please upload an unencrypted document."
            )

        # 3. Structural Sanity Check (at least 1 page)
        if len(reader.pages) == 0:
            raise ValidationError("PDF file is corrupted or empty.")

    except ValidationError:
        # Re-raise explicit validation errors (e.g. password protected) directly
        raise
    except Exception as exc:
        # Catch pypdf structural parsing exceptions (corrupted / incomplete streams)
        raise ValidationError("PDF file is corrupted or unparseable.") from exc
    finally:
        # Reset file pointer for storage saving
        uploaded_file.seek(0)
