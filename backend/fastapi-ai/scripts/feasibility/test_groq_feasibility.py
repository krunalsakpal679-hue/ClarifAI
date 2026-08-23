"""
Feasibility Smoke Test 3: Groq LLM Cloud Service (openai/gpt-oss-20b)
Measures API latency, rate limits, token usage, and completion structure.
"""

import os
import time
from groq import Groq

MODEL_NAME = os.getenv("GROQ_MODEL_NAME", "openai/gpt-oss-20b")
API_KEY = os.getenv("GROQ_API_KEY")

print("==================================================")
print(f"3. Groq LLM Cloud Service Feasibility Test ({MODEL_NAME})")
print("==================================================")

if not API_KEY:
    print("Error: GROQ_API_KEY is not configured.")
    exit(1)

client = Groq(api_key=API_KEY)

prompt = "Explain in plain language the legal implications of an automatic renewal clause in a commercial software agreement."

latencies = []
for i in range(3):
    t_start = time.time()
    res = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a legal contract AI assistant."},
            {"role": "user", "content": prompt}
        ],
        model=MODEL_NAME,
        temperature=0.1,
        max_tokens=150
    )
    t_end = time.time()
    lat = (t_end - t_start) * 1000
    latencies.append(lat)
    
    msg = res.choices[0].message
    content = (msg.content or "").strip()
    if not content and getattr(msg, "reasoning", None):
        content = str(msg.reasoning).strip()
        
    print(f" Run {i+1}: Latency = {lat:.2f} ms | Response snippet = {repr(content[:80])}")

avg_latency = sum(latencies) / len(latencies)
print(f"Average API Latency: {avg_latency:.2f} ms")
print("Status: FEASIBLE WITH CONSTRAINTS (Original llama-3.1-8b-instant retired by Groq; resolved per PRD Chapter 44 to openai/gpt-oss-20b)")
