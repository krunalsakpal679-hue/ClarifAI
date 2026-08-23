"""
Feasibility Smoke Test 4: Multilingual-E5 (intfloat/multilingual-e5-base)
Measures vector generation latency, embedding dimension (768), RAM overhead, and prefixing logic.
"""

import os
import time
import psutil
from sentence_transformers import SentenceTransformer

MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "intfloat/multilingual-e5-base")

print("==================================================")
print(f"4. Multilingual-E5 Feasibility Smoke Test ({MODEL_NAME})")
print("==================================================")

process = psutil.Process(os.getpid())
ram_before = process.memory_info().rss / (1024 * 1024)

t0 = time.time()
model = SentenceTransformer(MODEL_NAME)
load_time = time.time() - t0

ram_after = process.memory_info().rss / (1024 * 1024)
ram_used = ram_after - ram_before

print(f"Model Load Time: {load_time:.2f} s")
print(f"RAM Overhead: {ram_used:.2f} MB (Total process RAM: {ram_after:.2f} MB)")
print(f"Embedding Dimension: {model.get_sentence_embedding_dimension()}")

english_clause = "passage: Either party may terminate this agreement for convenience upon 30 days written notice."
hindi_clause = "passage: कोई भी पक्ष 30 दिनों के लिखित नोटिस पर सुविधा के लिए इस समझौते को समाप्त कर सकता है।"

t_start = time.time()
emb_eng = model.encode(english_clause)
emb_hin = model.encode(hindi_clause)
t_end = time.time()

batch_latency = (t_end - t_start) * 1000

print(f"Batch Encoding Latency (2 clauses): {batch_latency:.2f} ms")
print(f"English Vector Shape: {emb_eng.shape} | Hindi Vector Shape: {emb_hin.shape}")
print("Status: FEASIBLE WITH CONSTRAINTS (Fine-tuned checkpoint path is IMPLEMENTATION DECISION REQUIRED)")
