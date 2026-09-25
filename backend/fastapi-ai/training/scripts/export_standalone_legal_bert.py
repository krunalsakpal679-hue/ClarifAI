"""
ClarifAI Legal-BERT Standalone Model Exporter
Merges PEFT/LoRA adapter weights into the base Legal-BERT model to produce a
standalone Hugging Face checkpoint with zero runtime PEFT dependency.
"""

from pathlib import Path
import logging
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from peft import PeftModel
from safetensors.torch import load_file

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("export_standalone_legal_bert")

BASE_MODEL_ID = "nlpaueb/legal-bert-base-uncased"
CHECKPOINT_DIR = Path(__file__).resolve().parent.parent / "checkpoints" / "legalbert" / "v2.0"
ADAPTER_DIR = CHECKPOINT_DIR / "adapter"


def export_standalone():
    logger.info(f"Loading base model '{BASE_MODEL_ID}'...")
    base_model = AutoModelForSequenceClassification.from_pretrained(BASE_MODEL_ID, num_labels=4)

    adapter_path = ADAPTER_DIR if (ADAPTER_DIR / "adapter_config.json").exists() else CHECKPOINT_DIR
    logger.info(f"Loading LoRA adapter from '{adapter_path}'...")
    peft_model = PeftModel.from_pretrained(base_model, str(adapter_path))

    # Map classifier head weights if present
    weights_file = adapter_path / "adapter_model.safetensors"
    if weights_file.exists():
        weights = load_file(str(weights_file))
        for k, v in list(weights.items()):
            if "base_model.model.classifier.weight" in k:
                weights["base_model.model.classifier.modules_to_save.default.weight"] = v
                weights["base_model.model.classifier.original_module.weight"] = v
            elif "base_model.model.classifier.bias" in k:
                weights["base_model.model.classifier.modules_to_save.default.bias"] = v
                weights["base_model.model.classifier.original_module.bias"] = v
        peft_model.load_state_dict(weights, strict=False)

    logger.info("Merging LoRA adapter weights into base model...")
    merged_model = peft_model.merge_and_unload()
    merged_model.config.id2label = {0: "Safe", 1: "Low", 2: "Moderate", 3: "High"}
    merged_model.config.label2id = {"Safe": 0, "Low": 1, "Moderate": 2, "High": 3}
    merged_model.config.num_labels = 4

    logger.info(f"Saving merged standalone checkpoint to '{CHECKPOINT_DIR}'...")
    tokenizer = AutoTokenizer.from_pretrained(str(CHECKPOINT_DIR))
    merged_model.save_pretrained(str(CHECKPOINT_DIR))
    tokenizer.save_pretrained(str(CHECKPOINT_DIR))
    logger.info("Standalone model export complete! Checkpoint now loads directly without PEFT.")


if __name__ == "__main__":
    export_standalone()
