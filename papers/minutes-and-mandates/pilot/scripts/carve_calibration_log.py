#!/usr/bin/env python3
"""Carve a calibration log dir from an existing measured smoke log.

Used to reuse the committed v0 smoke rows that overlap the calibration
dev/test inject ids. Does not invent decisions: every row is copied from
the source JSONL. Adds prompt_version when the source omitted it.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--step-ids", type=Path, required=True, help="JSON list of step_ids in order")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--prompt-version", default="v0")
    parser.add_argument("--kind", default="minutes-and-mandates-calibration-carve")
    args = parser.parse_args()

    step_ids = json.loads(args.step_ids.read_text(encoding="utf-8"))
    if not isinstance(step_ids, list) or not step_ids:
        raise SystemExit("step-ids must be a non-empty JSON list")
    manifest = json.loads((args.source_dir / "manifest.json").read_text(encoding="utf-8"))
    cards_by = {row["step_id"]: row for row in load_jsonl(args.source_dir / "smoke_cards.jsonl")}
    prose_by = {row["step_id"]: row for row in load_jsonl(args.source_dir / "smoke_prose.jsonl")}
    missing = [sid for sid in step_ids if sid not in cards_by or sid not in prose_by]
    if missing:
        raise SystemExit(f"source log missing step_ids: {missing}")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    carved_cards = []
    carved_prose = []
    for index, step_id in enumerate(step_ids):
        for source, sink in ((cards_by, carved_cards), (prose_by, carved_prose)):
            row = dict(source[step_id])
            row["step_index"] = index
            row["prompt_version"] = args.prompt_version
            sink.append(row)

    (args.out_dir / "smoke_cards.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in carved_cards),
        encoding="utf-8",
    )
    (args.out_dir / "smoke_prose.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in carved_prose),
        encoding="utf-8",
    )
    out_manifest = dict(manifest)
    out_manifest["kind"] = args.kind
    out_manifest["prompt_version"] = args.prompt_version
    out_manifest["limit"] = len(step_ids)
    out_manifest["step_ids"] = step_ids
    out_manifest["carved_from"] = str(args.source_dir)
    out_manifest["probe"] = None
    out_manifest["carve_note"] = (
        "Rows copied from the source measured log. Decisions and meters are unchanged. "
        "step_index was renumbered to 0..n-1 for this subset. prompt_version was set explicitly."
    )
    (args.out_dir / "manifest.json").write_text(
        json.dumps(out_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"carved {len(step_ids)} steps -> {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
