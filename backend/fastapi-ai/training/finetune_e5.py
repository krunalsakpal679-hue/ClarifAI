"""
ClarifAI Multilingual-E5 Fine-Tuning Entrypoint (Phase 5)
Delegates to backend/fastapi-ai/training/scripts/train_multilingual_e5.py.
"""

import sys
from pathlib import Path

# Add scripts directory to path
SCRIPTS_DIR = Path(__file__).resolve().parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from train_multilingual_e5 import train_multilingual_e5, re_evaluate_checkpoint

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--eval-only":
        re_evaluate_checkpoint()
    else:
        train_multilingual_e5()
