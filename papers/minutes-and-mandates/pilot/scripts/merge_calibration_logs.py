#!/usr/bin/env python3
"""Merge carved and freshly measured calibration logs that share step order."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parts", type=Path, nargs="+", required=True, help="Log dirs in step-id order")
    parser.add_argument("--step-ids", type=Path, required=True, help="JSON list of final step_ids")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--prompt-version", required=True)
    parser.add_argument("--kind", default="minutes-and-mandates-calibration-merge")
    args = parser.parse_args()

    step_ids = json.loads(args.step_ids.read_text(encoding="utf-8"))
    cards_by: dict[str, dict] = {}
    prose_by: dict[str, dict] = {}
    manifests = []
    for part in args.parts:
        manifests.append(json.loads((part / "manifest.json").read_text(encoding="utf-8")))
        for row in load_jsonl(part / "smoke_cards.jsonl"):
            cards_by[row["step_id"]] = row
        for row in load_jsonl(part / "smoke_prose.jsonl"):
            prose_by[row["step_id"]] = row
    missing = [sid for sid in step_ids if sid not in cards_by or sid not in prose_by]
    if missing:
        raise SystemExit(f"missing step_ids in parts: {missing}")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    cards = []
    prose = []
    for index, step_id in enumerate(step_ids):
        for source, sink in ((cards_by, cards), (prose_by, prose)):
            row = dict(source[step_id])
            row["step_index"] = index
            row["prompt_version"] = args.prompt_version
            sink.append(row)
    (args.out_dir / "smoke_cards.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in cards), encoding="utf-8"
    )
    (args.out_dir / "smoke_prose.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in prose), encoding="utf-8"
    )
    base = dict(manifests[-1])
    base["kind"] = args.kind
    base["prompt_version"] = args.prompt_version
    base["limit"] = len(step_ids)
    base["step_ids"] = step_ids
    base["merged_from"] = [str(p) for p in args.parts]
    base["probe"] = None
    base["merge_note"] = (
        "Rows copied from part logs. Decisions and meters unchanged. "
        "step_index renumbered to 0..n-1. prompt_version set explicitly."
    )
    # Prefer earliest start / latest finish when available.
    starts = [m.get("started_at_utc") for m in manifests if m.get("started_at_utc")]
    finishes = [m.get("finished_at_utc") for m in manifests if m.get("finished_at_utc")]
    if starts:
        base["started_at_utc"] = min(starts)
    if finishes:
        base["finished_at_utc"] = max(finishes)
    (args.out_dir / "manifest.json").write_text(
        json.dumps(base, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"merged {len(step_ids)} steps -> {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
