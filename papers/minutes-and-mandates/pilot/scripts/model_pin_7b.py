"""Optional larger local judge pin (7B). Not used by CI.

Tried when MemAvailable allows after the 4B runs. Apache-2.0 base model.
Default smoke/calibration judge remains ``model_pin.py`` (4B).
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

PILOT = Path(__file__).resolve().parents[1]

REPO_ID = "bartowski/Qwen2.5-7B-Instruct-GGUF"
REVISION = "8911e8a47f92bac19d6f5c64a2e2095bd2f7d031"
FILENAME = "Qwen2.5-7B-Instruct-Q4_K_M.gguf"
SHA256 = "65b8fcd92af6b4fefa935c625d1ac27ea29dcb6ee14589c55a8f115ceaaa1423"
SIZE_BYTES = 4683074240
QUANTIZATION = "Q4_K_M"
LICENSE = "Apache-2.0"
LICENSE_URL = "https://huggingface.co/Qwen/Qwen2.5-7B-Instruct/blob/main/LICENSE"
BASE_MODEL_REPO = "Qwen/Qwen2.5-7B-Instruct"
# Base model git revision was not separately pinned in this round.
BASE_MODEL_REVISION = None
PARAMETER_COUNT = None
HUGGINGFACE_ETAG = "65b8fcd92af6b4fefa935c625d1ac27ea29dcb6ee14589c55a8f115ceaaa1423"


def cache_dir() -> Path:
    override = os.environ.get("JUDGE_MODEL_CACHE")
    if override:
        return Path(override)
    return PILOT / "data" / "model_cache"


def pin_record() -> dict:
    return {
        "repo_id": REPO_ID,
        "revision": REVISION,
        "filename": FILENAME,
        "sha256": SHA256,
        "size_bytes": SIZE_BYTES,
        "quantization": QUANTIZATION,
        "license": LICENSE,
        "license_url": LICENSE_URL,
        "base_model_repo": BASE_MODEL_REPO,
        "base_model_revision": BASE_MODEL_REVISION,
        "parameter_count": PARAMETER_COUNT,
        "huggingface_etag": HUGGINGFACE_ETAG,
        "note": "Optional 7B pin for calibration. Default judge remains the 4B pin in model_pin.py.",
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_gguf() -> Path:
    from huggingface_hub import hf_hub_download

    path = Path(
        hf_hub_download(
            repo_id=REPO_ID,
            filename=FILENAME,
            revision=REVISION,
            cache_dir=str(cache_dir()),
        )
    )
    size = path.stat().st_size
    if size != SIZE_BYTES:
        raise SystemExit(f"7B GGUF size {size} != {SIZE_BYTES}")
    digest = sha256_file(path)
    if digest != SHA256:
        raise SystemExit(f"7B GGUF sha256 {digest} != {SHA256}")
    return path
