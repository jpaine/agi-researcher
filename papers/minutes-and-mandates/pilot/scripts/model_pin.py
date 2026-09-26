"""Pinned local judge weights. No weights are committed.

The smoke machine has 4 CPU threads and about 5 GiB MemAvailable (recorded
on the run in the smoke manifest). A 7B/8B Q4_K_M file does not fit there:

- ``Qwen/Qwen2.5-7B-Instruct-GGUF`` @ ``bb5d59e06d9551d752d08b292a50eb208b07ab1f``,
  Q4_K_M shards ``qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf`` (3993201344 bytes)
  and ``qwen2.5-7b-instruct-q4_k_m-00002-of-00002.gguf`` (689872288 bytes).
- ``Qwen/Qwen3-8B-GGUF`` @ ``7c41481f57cb95916b40956ab2f0b139b296d974``,
  ``Qwen3-8B-Q4_K_M.gguf`` (5027783488 bytes).

The pinned file is an Apache-2.0 Q4_K_M quant of Qwen3-4B-Instruct-2507
(4.02B parameters, non-thinking instruct). Byte sizes above are the Hugging
Face ``x-linked-size`` values for those revisions, not measured runtimes.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

PILOT = Path(__file__).resolve().parents[1]

REPO_ID = "unsloth/Qwen3-4B-Instruct-2507-GGUF"
REVISION = "a06e946bb6b655725eafa393f4a9745d460374c9"
FILENAME = "Qwen3-4B-Instruct-2507-Q4_K_M.gguf"
SHA256 = "3605803b982cb64aead44f6c1b2ae36e3acdb41d8e46c8a94c6533bc4c67e597"
SIZE_BYTES = 2497281120
QUANTIZATION = "Q4_K_M"
LICENSE = "Apache-2.0"
LICENSE_URL = "https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/blob/main/LICENSE"
BASE_MODEL_REPO = "Qwen/Qwen3-4B-Instruct-2507"
BASE_MODEL_REVISION = "cdbee75f17c01a7cc42f958dc650907174af0554"
PARAMETER_COUNT = 4022468096

# Hugging Face x-linked-etag for this revision and filename. Same digest as SHA256.
HUGGINGFACE_ETAG = "3605803b982cb64aead44f6c1b2ae36e3acdb41d8e46c8a94c6533bc4c67e597"


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
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_gguf() -> Path:
    """Download the pinned GGUF into the gitignored cache and check its sha256."""
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
        raise SystemExit(f"pinned GGUF size {size} != {SIZE_BYTES}")
    digest = sha256_file(path)
    if digest != SHA256:
        raise SystemExit(f"pinned GGUF sha256 {digest} != {SHA256}")
    return path
