"""
ClarifAI PDF Extraction & Adaptive OCR Pydantic Schemas
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from app.models.common import SCHEMA_VERSION


class PageExtractionItem(BaseModel):
    page_number: int = Field(..., description="1-indexed page number")
    text: str = Field(..., description="Extracted digital or OCR text for this page")
    character_count: int = Field(..., description="Total non-whitespace character count")
    ocr_required: bool = Field(..., description="True if character count was below OCR threshold")
    ocr_performed: bool = Field(False, description="True if Tesseract OCR was executed for this page")
    extraction_method: str = Field("digital", description="Extraction method for this page: digital or ocr")


class PDFExtractionResponse(BaseModel):
    success: bool = Field(True, description="True on successful extraction")
    total_pages: int = Field(..., description="Total page count in document")
    ocr_required_pages_count: int = Field(..., description="Number of pages flagged needing OCR")
    ocr_performed_pages_count: int = Field(0, description="Number of pages on which OCR was executed")
    extraction_method: str = Field("digital", description="Overall document extraction method: digital, ocr, or hybrid")
    full_text: str = Field(..., description="Concatenated page-ordered document text")
    pages: List[PageExtractionItem] = Field(..., description="Per-page text extraction items")
    file_size_bytes: int = Field(..., description="PDF file size in bytes")
    is_encrypted: bool = Field(False, description="Always False for successful extractions")
    schema_version: str = Field(SCHEMA_VERSION, description="Semver schema version tag")
