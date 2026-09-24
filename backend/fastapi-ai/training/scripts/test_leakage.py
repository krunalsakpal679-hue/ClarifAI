"""
Leakage and Deduplication Verification Test Runner for ClarifAI AI Fine-Tuning Splits.
"""

import sys
from pathlib import Path

# Add project paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from training.scripts.leakage_check import (
    run_full_leakage_check,
    simulate_leakage_detection_failure
)

if __name__ == "__main__":
    success = run_full_leakage_check()
    if not success:
        sys.exit(1)
    
    print("\nExecuting synthetic failure test...")
    sim_success = simulate_leakage_detection_failure()
    if not sim_success:
        sys.exit(1)
    
    print("\nALL LEAKAGE CHECKS PASSED SUCCESSFULLY.")
