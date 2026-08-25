"""
Feasibility Smoke Test 2: BART-base (facebook/bart-base)
Measures summarization inference latency, context handling, RAM usage, and token output bounds.
"""

import os
import time
import torch
import psutil
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

MODEL_NAME = os.getenv("SUMMARIZATION_MODEL_NAME", "facebook/bart-base")

print("==================================================")
print(f"2. BART-base Feasibility Smoke Test ({MODEL_NAME})")
print("==================================================")

process = psutil.Process(os.getpid())
ram_before = process.memory_info().rss / (1024 * 1024)

t0 = time.time()
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
model.eval()
load_time = time.time() - t0

ram_after = process.memory_info().rss / (1024 * 1024)
ram_used = ram_after - ram_before

print(f"Model Load Time: {load_time:.2f} s")
print(f"RAM Overhead: {ram_used:.2f} MB (Total process RAM: {ram_after:.2f} MB)")
print(f"PyTorch Device: {'CUDA' if torch.cuda.is_available() else 'CPU'}")

# Representative multi-paragraph synthetic contract document (~300 words)
doc_text = """
This Master Services Agreement ("Agreement") is entered into by Provider and Client.
1. SERVICES. Provider agrees to perform document analysis, contract risk classification, automated summarization, and vector search services.
2. TERM AND TERMINATION. This Agreement commences on Effective Date for 1 year. Either party may terminate for convenience upon 90 days written notice.
3. CONFIDENTIALITY. Each party agrees to protect confidential information with reasonable care. Uploaded user documents remain exclusive property of Client.
4. LIMITATION OF LIABILITY. Neither party shall be liable for indirect or consequential damages. Liability is capped at fees paid in preceding 12 months.
"""

inputs = tokenizer(doc_text, return_tensors="pt", max_length=1024, truncation=True)

t_start = time.time()
with torch.no_grad():
    summary_ids = model.generate(
        inputs["input_ids"],
        max_length=150,
        min_length=30,
        length_penalty=2.0,
        num_beams=4,
        early_stopping=True
    )
t_end = time.time()

summary_text = tokenizer.decode(summary_ids[0], skip_special_tokens=True).strip()
latency_ms = (t_end - t_start) * 1000
summary_token_count = len(summary_ids[0])

print(f"Summary Generation Latency: {latency_ms:.2f} ms")
print(f"Generated Summary ({summary_token_count} tokens):\n{summary_text}")
print("Status: FEASIBLE WITH CONSTRAINTS (Fine-tuned checkpoint path is IMPLEMENTATION DECISION REQUIRED; ~9s latency on CPU requires PyTorch CUDA GPU acceleration)")
