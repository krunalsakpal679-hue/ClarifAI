"""
Dataset Preparation Script for ClarifAI AI Fine-Tuning Pipeline.
Executes the comprehensive data generation and document-level partitioning workflow.
"""

import sys
from pathlib import Path

# Add project paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from training.scripts.generate_comprehensive_dataset import generate_all_datasets

if __name__ == "__main__":
    generate_all_datasets()
