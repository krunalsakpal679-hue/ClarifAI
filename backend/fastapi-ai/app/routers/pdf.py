"""
ClarifAI PDF Text Extraction Router
Internal endpoint for PDF validation, PyMuPDF digital extraction, and OCR heuristic detection.
"""

from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, status
from app.models.pdf import PDFExtractionResponse
from app.services.pdf_service import extract_pdf_text_service
from app.core.security import verify_internal_secret

router = APIRouter(prefix="/api/v1", tags=["PDF Processing"])


@router.post(
    "/extract-pdf",
    response_model=PDFExtractionResponse,
    dependencies=[Depends(verify_internal_secret)]
)
async def extract_pdf_endpoint(
    file: UploadFile = File(...),
    enable_ocr: bool = True
):
    """
    Internal endpoint to extract text and per-page OCR flags from uploaded PDF files.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_FILE_TYPE",
                "message": "Uploaded file must be a PDF document (.pdf)."
            }
        )

    pdf_bytes = await file.read()
    result = extract_pdf_text_service(pdf_bytes, enable_ocr=enable_ocr)
    return PDFExtractionResponse(**result)
