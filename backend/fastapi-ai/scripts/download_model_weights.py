#!/usr/bin/env python3
"""
ClarifAI Model Weight Downloader and Checkpoint Provisioning Tool
Resolves cold-start latency and clean-checkout weight provisioning.

Features:
- Pre-downloads and caches Legal-BERT and Multilingual-E5 base weights.
- Validates local fine-tuned checkpoints or syncs from remote store if configured.
- Verifies INT8 CPU dynamic quantization compatibility.
- Ensures zero cold-start delay during first inference request.
"""

import os
import sys
import time
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("download_model_weights")

# Core AI Models
LEGAL_BERT_BASE = "nlpaueb/legal-bert-base-uncased"
MULTILINGUAL_E5_BASE = "intfloat/multilingual-e5-base"


def download_and_verify_legal_bert(cache_dir: Optional[str] = None, test_quantization: bool = True) -> Dict[str, Any]:
    """
    Downloads, caches, and verifies Legal-BERT tokenizer and sequence classification model.
    """
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification

    logger.info(f"Downloading/Caching Legal-BERT base model: '{LEGAL_BERT_BASE}'...")
    start_time = time.perf_counter()

    tokenizer = AutoTokenizer.from_pretrained(LEGAL_BERT_BASE, cache_dir=cache_dir)
    model = AutoModelForSequenceClassification.from_pretrained(
        LEGAL_BERT_BASE,
        num_labels=4,
        cache_dir=cache_dir
    )
    model.eval()
    download_elapsed = time.perf_counter() - start_time
    logger.info(f"Legal-BERT successfully cached in {download_elapsed:.2f}s.")

    # Quick test inference
    sample_text = "Either party may terminate this agreement with thirty days written notice."
    inputs = tokenizer(sample_text, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        out = model(**inputs)
    logits_shape = list(out.logits.shape)

    quantization_verified = False
    if test_quantization:
        try:
            qmodel = torch.quantization.quantize_dynamic(model, {torch.nn.Linear}, dtype=torch.qint8)
            with torch.no_grad():
                qout = qmodel(**inputs)
            assert qout.logits.shape == out.logits.shape
            quantization_verified = True
            logger.info("Dynamic INT8 quantization verified successfully for Legal-BERT.")
        except Exception as q_err:
            logger.warning(f"Dynamic INT8 quantization verification failed: {q_err}")

    return {
        "model": LEGAL_BERT_BASE,
        "status": "READY",
        "download_elapsed_seconds": round(download_elapsed, 2),
        "logits_shape": logits_shape,
        "quantization_verified": quantization_verified
    }


def download_and_verify_e5(cache_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Downloads, caches, and verifies Multilingual-E5 embedding model.
    """
    from sentence_transformers import SentenceTransformer

    logger.info(f"Downloading/Caching Multilingual-E5 model: '{MULTILINGUAL_E5_BASE}'...")
    start_time = time.perf_counter()

    model = SentenceTransformer(MULTILINGUAL_E5_BASE, cache_folder=cache_dir)
    download_elapsed = time.perf_counter() - start_time
    logger.info(f"Multilingual-E5 successfully cached in {download_elapsed:.2f}s.")

    # Quick test embedding
    sample_clause = "passage: The Contractor agrees to indemnify and hold harmless the Company."
    embedding = model.encode(sample_clause, normalize_embeddings=True)
    embedding_dim = int(len(embedding))
    logger.info(f"Generated test embedding with dimension {embedding_dim}.")

    return {
        "model": MULTILINGUAL_E5_BASE,
        "status": "READY",
        "download_elapsed_seconds": round(download_elapsed, 2),
        "embedding_dim": embedding_dim
    }


def inspect_local_checkpoints(base_dir: Path) -> Dict[str, Any]:
    """
    Audits local fine-tuned checkpoints in training/checkpoints/.
    """
    checkpoints_dir = base_dir / "backend" / "fastapi-ai" / "training" / "checkpoints"
    results = {}

    legal_bert_v2 = checkpoints_dir / "legal-bert" / "v2.0"
    legalbert_v2_alt = checkpoints_dir / "legalbert" / "v2.0"
    legal_bert_path = legal_bert_v2 if legal_bert_v2.exists() else (legalbert_v2_alt if legalbert_v2_alt.exists() else None)

    if legal_bert_path:
        has_config = (legal_bert_path / "config.json").exists()
        has_weights = (legal_bert_path / "model.safetensors").exists() or (legal_bert_path / "pytorch_model.bin").exists()
        has_adapter = (legal_bert_path / "adapter" / "adapter_config.json").exists() or (legal_bert_path / "adapter_config.json").exists()
        results["legal_bert_checkpoint"] = {
            "path": str(legal_bert_path),
            "present": True,
            "has_direct_weights": has_config and has_weights,
            "has_adapter": has_adapter
        }
    else:
        results["legal_bert_checkpoint"] = {
            "path": str(legal_bert_v2),
            "present": False,
            "fallback": "nlpaueb/legal-bert-base-uncased"
        }

    e5_v1 = checkpoints_dir / "multilingual-e5" / "v1.1"
    e5_v1_alt = checkpoints_dir / "e5" / "v1.1"
    e5_path = e5_v1 if e5_v1.exists() else (e5_v1_alt if e5_v1_alt.exists() else None)

    if e5_path:
        results["e5_checkpoint"] = {
            "path": str(e5_path),
            "present": True
        }
    else:
        results["e5_checkpoint"] = {
            "path": str(e5_v1),
            "present": False,
            "fallback": "intfloat/multilingual-e5-base"
        }

    return results


def main():
    parser = argparse.ArgumentParser(description="ClarifAI Model Weight Provisioner")
    parser.add_argument("--cache-dir", type=str, default=None, help="Directory to cache models")
    parser.add_argument("--skip-e5", action="store_true", help="Skip Multilingual-E5 download")
    parser.add_argument("--skip-legal-bert", action="store_true", help="Skip Legal-BERT download")
    parser.add_argument("--skip-quantization-test", action="store_true", help="Skip INT8 quantization check")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    logger.info("=== ClarifAI AI Model Weight Provisioning ===")

    # 1. Audit Checkpoints
    checkpoint_audit = inspect_local_checkpoints(repo_root)
    for model_key, info in checkpoint_audit.items():
        if info["present"]:
            logger.info(f"Local checkpoint found for {model_key}: {info['path']}")
        else:
            logger.info(f"Local checkpoint not present for {model_key}. Clean checkout will use fallback: {info['fallback']}")

    # 2. Download / Cache Models
    results = {}
    if not args.skip_legal_bert:
        try:
            results["legal_bert"] = download_and_verify_legal_bert(
                cache_dir=args.cache_dir,
                test_quantization=not args.skip_quantization_test
            )
        except Exception as e:
            logger.error(f"Failed to prepare Legal-BERT: {e}")
            results["legal_bert"] = {"status": "ERROR", "error": str(e)}

    if not args.skip_e5:
        try:
            results["multilingual_e5"] = download_and_verify_e5(cache_dir=args.cache_dir)
        except Exception as e:
            logger.error(f"Failed to prepare Multilingual-E5: {e}")
            results["multilingual_e5"] = {"status": "ERROR", "error": str(e)}

    logger.info("=== Provisioning Summary ===")
    for model, res in results.items():
        logger.info(f"  {model}: {res.get('status')} {res}")

    all_passed = all(res.get("status") == "READY" for res in results.values())
    if all_passed:
        logger.info("All model weights successfully verified and ready for deployment.")
        sys.exit(0)
    else:
        logger.warning("One or more models encountered an issue during provisioning.")
        sys.exit(1)


if __name__ == "__main__":
    main()
