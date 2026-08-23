"""
Feasibility Smoke Test 1: Legal-BERT (Fine-Tuned / nlpaueb/legal-bert-base-uncased)
Measures inference latency, output logits shape, label mapping, and memory usage.
"""

import os
import time
import torch
import psutil
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODEL_NAME = os.getenv("LEGAL_BERT_MODEL_NAME", "nlpaueb/legal-bert-base-uncased")
NUM_LABELS = 4

print("==================================================")
print(f"1. Legal-BERT Feasibility Smoke Test ({MODEL_NAME})")
print("==================================================")

process = psutil.Process(os.getpid())
ram_before = process.memory_info().rss / (1024 * 1024)

t0 = time.time()
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=NUM_LABELS)
model.eval()
load_time = time.time() - t0

ram_after = process.memory_info().rss / (1024 * 1024)
ram_used = ram_after - ram_before

print(f"Model Load Time: {load_time:.2f} s")
print(f"RAM Overhead: {ram_used:.2f} MB (Total process RAM: {ram_after:.2f} MB)")
print(f"PyTorch Device: {'CUDA' if torch.cuda.is_available() else 'CPU'}")

# Realistic synthetic clause text
sample_clause = (
    "In no event shall either party be liable for indirect, incidental, consequential, "
    "special, or punitive damages arising out of or in connection with this Agreement. "
    "Total cumulative liability shall not exceed the fees paid in the preceding 12 months."
)

latencies = []
outputs_list = []

for i in range(3):
    t_start = time.time()
    inputs = tokenizer(sample_clause, return_tensors="pt", max_length=512, truncation=True)
    with torch.no_grad():
        out = model(**inputs)
        logits = out.logits
        probs = torch.softmax(logits, dim=-1)
        pred_class = torch.argmax(probs, dim=-1).item()
    t_end = time.time()
    lat = (t_end - t_start) * 1000
    latencies.append(lat)
    outputs_list.append((logits.shape, pred_class, probs[0][pred_class].item()))
    print(f" Run {i+1}: Latency = {lat:.2f} ms | Logits Shape = {list(logits.shape)} | Predicted Class = {pred_class}")

avg_latency = sum(latencies[1:]) / len(latencies[1:]) if len(latencies) > 1 else latencies[0]
print(f"Warm-up Latency: {latencies[0]:.2f} ms")
print(f"Average Steady-State Latency: {avg_latency:.2f} ms per clause")
print("Status: FEASIBLE WITH CONSTRAINTS (Fine-tuned checkpoint path is IMPLEMENTATION DECISION REQUIRED)")
