import torch
import json
from app.services.risk_service import load_legal_bert_model, APPROVED_SEVERITY_LABELS, get_legal_bert_model_name, resolve_legal_bert_path

CLAUSES = [
    {
        "id": "C1_HIGH_INDEMNITY",
        "expected": "High",
        "text": "Provider shall unconditionally defend, indemnify, and hold harmless Customer, its affiliates, officers, and employees from and against any and all claims, liabilities, losses, damages, and expenses, including unlimited consequential damages and attorney fees, arising out of any breach or negligence without limitation of liability."
    },
    {
        "id": "C2_HIGH_TERMINATION",
        "expected": "High",
        "text": "Customer reserves the absolute right to terminate this Agreement immediately for convenience at any time without notice and without any penalty or liability for work completed prior to termination."
    },
    {
        "id": "C3_HIGH_IP_ASSIGNMENT",
        "expected": "High",
        "text": "All intellectual property, pre-existing background technology, patents, trademarks, and future developments created by Contractor or its personnel shall become the sole and exclusive property of Client worldwide in perpetuity immediately upon inception."
    },
    {
        "id": "C4_MODERATE_AUDIT",
        "expected": "Moderate",
        "text": "Client may audit Provider's books, records, and internal technical systems upon five (5) business days' prior written notice during normal business hours to verify compliance with service fee calculations."
    },
    {
        "id": "C5_MODERATE_PAYMENT",
        "expected": "Moderate",
        "text": "Client shall pay undisputed invoices within thirty (30) days of receipt. Late payments shall accrue interest at a rate of 1.5% per month or the maximum rate permitted by law."
    },
    {
        "id": "C6_LOW_NOTICES",
        "expected": "Low",
        "text": "All notices required under this Agreement shall be given in writing and deemed received within two (2) business days if sent by registered mail or confirmed electronic transmission."
    },
    {
        "id": "C7_SAFE_DEFINITIONS",
        "expected": "Safe",
        "text": "This Agreement may be executed in multiple counterparts, each of which shall be deemed an original, but all of which together shall constitute one and the same instrument."
    },
    {
        "id": "C8_SAFE_SEVERABILITY",
        "expected": "Safe",
        "text": "If any provision of this Agreement is held to be invalid or unenforceable, such provision shall be severed and the remaining provisions shall remain in full force and effect."
    }
]

def run_forensic_test():
    tokenizer, model = load_legal_bert_model()
    model_name = get_legal_bert_model_name()
    resolved = resolve_legal_bert_path(model_name)
    
    print("=" * 80)
    print("LEGAL-BERT FORENSIC VERIFICATION RESULTS")
    print("=" * 80)
    print(f"Model Identifier: {model_name}")
    print(f"Resolved Path:    {resolved}")
    print(f"Model Config Num Labels: {model.config.num_labels}")
    print(f"id2label: {model.config.id2label}")
    print(f"label2id: {model.config.label2id}")
    print(f"Tokenizer Class: {tokenizer.__class__.__name__}")
    print(f"Model Class:     {model.__class__.__name__}")
    print(f"Model in eval mode: {not model.training}")
    print("=" * 80)
    
    results = []
    for c in CLAUSES:
        inputs = tokenizer(c["text"], return_tensors="pt", truncation=True, max_length=512)
        device = next(model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits[0].cpu().numpy().tolist()
            probs = torch.softmax(outputs.logits[0], dim=-1).cpu().numpy().tolist()
            pred_id = int(torch.argmax(outputs.logits[0], dim=-1).item())
            pred_label = APPROVED_SEVERITY_LABELS.get(pred_id, "UNKNOWN")
            
        res = {
            "clause_id": c["id"],
            "expected": c["expected"],
            "predicted_id": pred_id,
            "predicted_label": pred_label,
            "raw_logits": [round(x, 4) for x in logits],
            "softmax_probs": [round(p, 4) for p in probs],
            "probs_map": {APPROVED_SEVERITY_LABELS[i]: round(probs[i], 4) for i in range(len(probs))}
        }
        results.append(res)
        print(f"Clause ID:       {res['clause_id']}")
        print(f"Expected:        {res['expected']} | Predicted: {res['predicted_label']} (ID={res['predicted_id']})")
        print(f"Raw Logits:      {res['raw_logits']}")
        print(f"Softmax Probs:   {res['softmax_probs']} -> {res['probs_map']}")
        print("-" * 80)
        
    # Check differentiation
    all_prob_vectors = [r["softmax_probs"] for r in results]
    unique_vectors = len(set(tuple(p) for p in all_prob_vectors))
    print(f"\nDifferentiation Check: {unique_vectors} unique probability distributions across {len(results)} clauses.")
    return results

def test_legal_bert_differentiation():
    results = run_forensic_test()
    assert len(results) == 8
    all_prob_vectors = [r["softmax_probs"] for r in results]
    unique_vectors = len(set(tuple(p) for p in all_prob_vectors))
    assert unique_vectors >= 7, f"Expected distinct probability distributions, got {unique_vectors}"

if __name__ == "__main__":
    run_forensic_test()
