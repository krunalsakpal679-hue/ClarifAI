import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.pdf_service import extract_pdf_text_service
from app.services.text_cleaning_service import clean_legal_text
from app.services.clause_segmentation_service import segment_document_clauses
from app.services.claim_grounding_service import verify_and_ground_clause_narrative
import re

pdf_path = Path("c:/ClarifAI- AIPipeline/sample_documents/Sample_Master_Services_Agreement.pdf")
with open(pdf_path, "rb") as f:
    pdf_bytes = f.read()

ext = extract_pdf_text_service(pdf_bytes, enable_ocr=False)
cleaned = clean_legal_text(ext["full_text"])["cleaned_text"]
seg = segment_document_clauses(cleaned, pages=ext.get("pages", []))["clauses"]

print("=== TOTAL SEGMENTED CLAUSES IN MSA ===", len(seg))
for idx, c in enumerate(seg, start=1):
    print(f"\n--- Clause {idx} | Title: {c.get('title')} ---")
    print(c.get("text"))

print("\n=== SPECIFIC SECTION 6 EXTRACTION AUDIT ===")
sec6_text = seg[5].get("text") # 6th clause
print("Section 6 Text:")
print(sec6_text)

# Run extractors
amounts = re.findall(r'(?:₹|Rs\.?|\$|€|USD|INR)\s*[\d,]+(?:\.\d+)?', sec6_text, re.IGNORECASE)
durations = re.findall(r'\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|twelve|thirty|sixty|ninety)\s+(?:days?|months?|years?|hours?|business\s+days?)\b', sec6_text, re.IGNORECASE)
percentages = [m.group(0).strip() for m in re.finditer(r'(?:\(\s*)?\b\d+(?:\.\d+)?%(?:\s*\))?(?:\s+per\s+(?:month|annum|year))?(?:\s+compounding\s+(?:monthly|annually|quarterly))?', sec6_text, re.IGNORECASE)]

print(f"Extracted Amounts: {amounts}")
print(f"Extracted Durations: {durations}")
print(f"Extracted Percentages: {percentages}")
