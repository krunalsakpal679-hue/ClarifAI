"""
ClarifAI Legal-BERT Fine-Tuning Entrypoint (Phase 4)
Delegates to backend/fastapi-ai/training/scripts/train_legal_bert.py.
"""

import sys
from pathlib import Path

# Add scripts directory to path
SCRIPTS_DIR = Path(__file__).resolve().parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from train_legal_bert import train_legal_bert, re_evaluate_checkpoint

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--eval-only":
        re_evaluate_checkpoint()
    else:
        train_legal_bert()
