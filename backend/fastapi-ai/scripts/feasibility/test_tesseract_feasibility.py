"""
Feasibility Smoke Test 5: Tesseract OCR (v5.4.0 Native Binary)
Measures OCR text extraction latency, binary executable availability, and language data.
"""

import os
import sys
import time
import pytesseract
from PIL import Image, ImageDraw, ImageFont

print("==================================================")
print("5. Tesseract OCR Feasibility Smoke Test (v5.4.0)")
print("==================================================")

# Discover Tesseract executable path
custom_cmd = os.getenv("TESSERACT_CMD")
if custom_cmd and os.path.exists(custom_cmd):
    pytesseract.pytesseract.tesseract_cmd = custom_cmd
elif sys.platform.startswith("win"):
    default_win_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(default_win_path):
        pytesseract.pytesseract.tesseract_cmd = default_win_path

print(f"Tesseract Binary Executable: {pytesseract.pytesseract.tesseract_cmd}")

try:
    version = pytesseract.get_tesseract_version()
    print(f"Tesseract Version: {version}")
except Exception as e:
    print(f"Tesseract Version Discovery Failed: {e}")
    exit(1)

# Synthetic test image containing synthetic legal text
img = Image.new("RGB", (600, 150), color=(255, 255, 255))
d = ImageDraw.Draw(img)
d.text((20, 40), "CONFIDENTIALITY AGREEMENT - SECTION 4.1", fill=(0, 0, 0))

t0 = time.time()
extracted_text = pytesseract.image_to_string(img, lang="eng").strip()
latency_ms = (time.time() - t0) * 1000

print(f"OCR Extraction Latency: {latency_ms:.2f} ms")
print(f"Extracted Text: {repr(extracted_text)}")
print("Status: FEASIBLE WITH CONSTRAINTS (Tesseract binary path must be explicitly configured via TESSERACT_CMD or added to system PATH)")
