"""Download one pinned Qwen embedding snapshot into this experiment folder."""

import json
import os
import time
from pathlib import Path


EXPERIMENT = Path(__file__).resolve().parent
MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"

# Set cache locations before importing Hugging Face libraries.
os.environ["HF_HOME"] = str(EXPERIMENT / "models" / "huggingface")
os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"

from huggingface_hub import HfApi, snapshot_download


def main() -> None:
    started = time.perf_counter()
    model_root = EXPERIMENT / "models"
    model_root.mkdir(parents=True, exist_ok=True)
    config_path = model_root / "qwen_model.json"
    if config_path.exists():
        revision = json.loads(config_path.read_text(encoding="utf-8"))["revision"]
    else:
        revision = HfApi().model_info(MODEL_ID).sha
    print(f"Downloading {MODEL_ID} at {revision}", flush=True)
    snapshot = snapshot_download(
        MODEL_ID,
        revision=revision,
        cache_dir=model_root / "huggingface" / "hub",
        max_workers=2,
        allow_patterns=[
            "config.json", "model.safetensors", "model-*.safetensors",
            "model.safetensors.index.json", "modules.json", "sentence_bert_config.json",
            "config_sentence_transformers.json", "tokenizer.json", "tokenizer_config.json",
            "special_tokens_map.json", "vocab.json", "merges.txt",
            "1_Pooling/config.json", "2_Normalize/config.json", "README.md",
        ],
    )
    config = {
        "model_id": MODEL_ID,
        "revision": revision,
        "snapshot_path": str(Path(snapshot).resolve().relative_to(EXPERIMENT)),
        "download_seconds": round(time.perf_counter() - started, 3),
    }
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(f"Model ready: {snapshot}", flush=True)


if __name__ == "__main__":
    main()
