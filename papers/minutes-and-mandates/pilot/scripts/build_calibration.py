#!/usr/bin/env python3
"""Build the calibration holdout split and clean-by-construction steps.

- Shuffles the 60 inject candidates with random.Random(seed).shuffle (same
  algorithm as the smoke subset), then takes the first n_dev as calibration
  dev and the remainder as held-out test.
- Samples unused Nebius steps (not used as inject source attachments) as
  clean-by-construction proposed steps. These are not gold.
- Writes a separate labeling sheet for clean steps so sheet.csv is untouched.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from labeling import export_sheet  # noqa: E402
from step_format import dump_jsonl, load_jsonl, sha256_text  # noqa: E402

PILOT = Path(__file__).resolve().parents[1]
CANDIDATES = PILOT / "data" / "injects" / "candidates.jsonl"
NEBIUS = PILOT / "data" / "trajectories" / "nebius_sample.jsonl"
OUT_DIR = PILOT / "data" / "calibration"
DEFAULT_SEED = 20260926
DEFAULT_N_DEV = 24
DEFAULT_N_CLEAN = 24


def inject_source_keys(candidates: list[dict]) -> set[tuple[str, int]]:
    used: set[tuple[str, int]] = set()
    for step in candidates:
        meta = step.get("metadata") or {}
        traj = meta.get("source_trajectory_id")
        index = meta.get("source_step_index")
        if traj is None or index is None:
            raise SystemExit(f"{step.get('step_id')}: missing source attachment")
        used.add((str(traj), int(index)))
    return used


def split_inject_ids(candidates: list[dict], *, seed: int, n_dev: int) -> dict:
    if not 1 <= n_dev < len(candidates):
        raise SystemExit(f"n_dev must be in 1..{len(candidates) - 1}")
    by_id = {step["step_id"]: step for step in candidates}
    if len(by_id) != len(candidates):
        raise SystemExit("duplicate step_id in candidates")
    # Same permutation helper the smoke loop uses: shuffle the step objects.
    file_order = list(candidates)
    random.Random(seed).shuffle(file_order)
    ids = [step["step_id"] for step in file_order]
    if set(ids) != set(by_id):
        raise SystemExit("split permutation lost step ids")
    dev_ids = ids[:n_dev]
    test_ids = ids[n_dev:]

    def label_counts(step_ids: list[str]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for step_id in step_ids:
            label = by_id[step_id]["proposed_label"]
            counts[label] = counts.get(label, 0) + 1
        return counts

    return {
        "kind": "minutes-and-mandates-calibration-split",
        "seed": seed,
        "python_random": f"{sys.version.split()[0]} random.Random.shuffle",
        "algorithm": (
            "random.Random(seed).shuffle of candidates.jsonl file order; "
            f"first {n_dev} step_ids are dev; remainder are test"
        ),
        "n_candidates": len(candidates),
        "n_dev": n_dev,
        "n_test": len(test_ids),
        "dev_step_ids": dev_ids,
        "test_step_ids": test_ids,
        "dev_proposed_label_counts": label_counts(dev_ids),
        "test_proposed_label_counts": label_counts(test_ids),
        "note": (
            "Proposed labels are synthesizer intention only, not gold. "
            "Prompt iteration uses dev only. Test is reported once after freeze."
        ),
    }


def sample_clean_steps(
    nebius_steps: list[dict],
    *,
    used: set[tuple[str, int]],
    seed: int,
    n_clean: int,
) -> list[dict]:
    pool = [
        step
        for step in nebius_steps
        if (step["trajectory_id"], int(step["step_index"])) not in used
    ]
    if len(pool) < n_clean:
        raise SystemExit(f"need {n_clean} unused Nebius steps, found {len(pool)}")
    order = list(pool)
    random.Random(seed).shuffle(order)
    chosen = order[:n_clean]
    out: list[dict] = []
    for index, source in enumerate(chosen):
        step = dict(source)
        meta = dict(step.get("metadata") or {})
        meta.update(
            {
                "origin": "nebius-clean-sample",
                "label_status": "proposed",
                "proposed_basis": "clean-by-construction",
                "source_trajectory_id": source["trajectory_id"],
                "source_step_id": source["step_id"],
                "source_step_index": source["step_index"],
                "source_tool_name": source.get("tool_name"),
            }
        )
        step["step_id"] = f"clean-{index:04d}"
        step["injected"] = False
        step["label_status"] = "proposed"
        step["proposed_label"] = "clean"
        step["proposed_card_id"] = None
        step["proposed_clause_id"] = None
        step["gold"] = False
        step["fixture"] = False
        step["metadata"] = meta
        out.append(step)
    return out


def write_split_jsonl(candidates: list[dict], step_ids: list[str], path: Path) -> None:
    by_id = {step["step_id"]: step for step in candidates}
    rows = [by_id[step_id] for step_id in step_ids]
    path.write_text(dump_jsonl(rows), encoding="utf-8")


def build(
    *,
    seed: int = DEFAULT_SEED,
    n_dev: int = DEFAULT_N_DEV,
    n_clean: int = DEFAULT_N_CLEAN,
    out_dir: Path = OUT_DIR,
    sheet_path: Path | None = None,
) -> dict:
    candidates = load_jsonl(CANDIDATES)
    nebius_steps = load_jsonl(NEBIUS)
    split = split_inject_ids(candidates, seed=seed, n_dev=n_dev)
    used = inject_source_keys(candidates)
    clean = sample_clean_steps(nebius_steps, used=used, seed=seed, n_clean=n_clean)
    # Same seed shuffles clean into first half for doodling on dev, second for test attach.
    clean_dev_n = n_clean // 2
    clean_dev = clean[:clean_dev_n]
    clean_test = clean[clean_dev_n:]

    out_dir.mkdir(parents=True, exist_ok=True)
    write_split_jsonl(candidates, split["dev_step_ids"], out_dir / "dev_injects.jsonl")
    write_split_jsonl(candidates, split["test_step_ids"], out_dir / "test_injects.jsonl")
    (out_dir / "clean_steps.jsonl").write_text(dump_jsonl(clean), encoding="utf-8")
    (out_dir / "dev_clean.jsonl").write_text(dump_jsonl(clean_dev), encoding="utf-8")
    (out_dir / "test_clean.jsonl").write_text(dump_jsonl(clean_test), encoding="utf-8")

    # Combined eval packs: injects then clean, fixed order within each block.
    def combined(inject_ids: list[str], clean_rows: list[dict]) -> list[dict]:
        by_id = {step["step_id"]: step for step in candidates}
        return [by_id[i] for i in inject_ids] + list(clean_rows)

    (out_dir / "dev_steps.jsonl").write_text(
        dump_jsonl(combined(split["dev_step_ids"], clean_dev)), encoding="utf-8"
    )
    (out_dir / "test_steps.jsonl").write_text(
        dump_jsonl(combined(split["test_step_ids"], clean_test)), encoding="utf-8"
    )

    if sheet_path is None and out_dir.resolve() == OUT_DIR.resolve():
        sheet_path = PILOT / "labeling" / "sheet_clean.csv"
    if sheet_path is not None:
        export_sheet(clean, sheet_path)

    manifest = {
        **split,
        "candidates_sha256": sha256_text(CANDIDATES.read_text(encoding="utf-8")),
        "nebius_steps_sha256": sha256_text(NEBIUS.read_text(encoding="utf-8")),
        "n_nebius_steps": len(nebius_steps),
        "n_inject_source_attachments": len(used),
        "n_unused_nebius_pool": len(
            [
                step
                for step in nebius_steps
                if (step["trajectory_id"], int(step["step_index"])) not in used
            ]
        ),
        "clean": {
            "n": len(clean),
            "seed": seed,
            "algorithm": (
                "unused Nebius steps (trajectory_id, step_index) not used as inject "
                f"source attachments; random.Random(seed).shuffle; first {n_clean}"
            ),
            "proposed_label": "clean",
            "proposed_basis": "clean-by-construction",
            "gold": False,
            "step_ids": [step["step_id"] for step in clean],
            "dev_step_ids": [step["step_id"] for step in clean_dev],
            "test_step_ids": [step["step_id"] for step in clean_test],
            "sheet": "papers/minutes-and-mandates/pilot/labeling/sheet_clean.csv",
            "sheet_note": (
                "Separate from labeling/sheet.csv so in-progress labeling of injects "
                "is not reordered or altered."
            ),
        },
        "files": {
            "dev_injects": "papers/minutes-and-mandates/pilot/data/calibration/dev_injects.jsonl",
            "test_injects": "papers/minutes-and-mandates/pilot/data/calibration/test_injects.jsonl",
            "clean_steps": "papers/minutes-and-mandates/pilot/data/calibration/clean_steps.jsonl",
            "dev_steps": "papers/minutes-and-mandates/pilot/data/calibration/dev_steps.jsonl",
            "test_steps": "papers/minutes-and-mandates/pilot/data/calibration/test_steps.jsonl",
            "manifest": "papers/minutes-and-mandates/pilot/data/calibration/manifest.json",
        },
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--n-dev", type=int, default=DEFAULT_N_DEV)
    parser.add_argument("--n-clean", type=int, default=DEFAULT_N_CLEAN)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()
    manifest = build(seed=args.seed, n_dev=args.n_dev, n_clean=args.n_clean, out_dir=args.out_dir)
    print(
        f"dev_injects={manifest['n_dev']} test_injects={manifest['n_test']} "
        f"clean={manifest['clean']['n']}"
    )
    print(f"wrote {args.out_dir / 'manifest.json'}")
    print(f"wrote {PILOT / 'labeling' / 'sheet_clean.csv'} (sheet.csv untouched)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
