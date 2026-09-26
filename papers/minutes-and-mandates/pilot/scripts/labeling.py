#!/usr/bin/env python3
"""Labeling sheet export and pass-1 vs pass-2 agreement.

The sheet is the labeling view. Proposed synthesizer labels are not copied
into it. Agreement does not compare either pass to those proposed labels.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from step_format import load_jsonl

PILOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATES = PILOT / "data" / "injects" / "candidates.jsonl"
DEFAULT_SHEET = PILOT / "labeling" / "sheet.csv"

SHEET_COLUMNS = (
    "item_id",
    "trajectory_id",
    "step_id",
    "step_index",
    "tool_name",
    "actor",
    "repo_path",
    "file_path",
    "tool_input",
    "tool_output",
    "agent_text",
    "source_trajectory_id",
    "source_step_index",
    "source_tool_name",
    "label_pass1",
    "cards_pass1",
    "confidence_pass1",
    "notes_pass1",
    "label_pass2",
    "cards_pass2",
    "confidence_pass2",
    "notes_pass2",
)

HIDDEN_FIELDS = (
    "proposed_label",
    "proposed_card_id",
    "proposed_clause_id",
    "template_variant",
    "label_status",
    "injected",
)

LABELS = ("violation", "near-miss", "clean", "ambiguous")


def sheet_row(step: dict) -> dict:
    meta = step.get("metadata") or {}
    row = {
        "item_id": step["step_id"],
        "trajectory_id": step.get("trajectory_id", ""),
        "step_id": step.get("step_id", ""),
        "step_index": step.get("step_index", ""),
        "tool_name": step.get("tool_name", ""),
        "actor": step.get("actor", ""),
        "repo_path": step.get("repo_path") or "",
        "file_path": step.get("file_path") or "",
        "tool_input": step.get("tool_input", ""),
        "tool_output": step.get("tool_output", ""),
        "agent_text": step.get("agent_text", ""),
        "source_trajectory_id": meta.get("source_trajectory_id", ""),
        "source_step_index": meta.get("source_step_index", ""),
        "source_tool_name": meta.get("source_tool_name", ""),
        "label_pass1": "",
        "cards_pass1": "",
        "confidence_pass1": "",
        "notes_pass1": "",
        "label_pass2": "",
        "cards_pass2": "",
        "confidence_pass2": "",
        "notes_pass2": "",
    }
    leaked = set(HIDDEN_FIELDS) & set(row)
    if leaked:
        raise SystemExit(f"labeling sheet tried to include {sorted(leaked)}")
    return row


def export_sheet(steps: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SHEET_COLUMNS, lineterminator="\n")
        writer.writeheader()
        for step in steps:
            writer.writerow(sheet_row(step))


def read_sheet(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise SystemExit(f"{path} has no header")
        hidden = [name for name in reader.fieldnames if name.startswith("proposed") or name in HIDDEN_FIELDS]
        if hidden:
            raise SystemExit(f"{path} exposes labeling-view fields {hidden}")
        missing = [name for name in SHEET_COLUMNS if name not in reader.fieldnames]
        if missing:
            raise SystemExit(f"{path} missing columns {missing}")
        return list(reader)


def card_set(value: str) -> tuple[str, ...]:
    parts = []
    for piece in (value or "").replace("|", ",").split(","):
        card = piece.strip()
        if card:
            parts.append(card)
    return tuple(sorted(parts))


def cohen_kappa(pairs: list[tuple[str, str]]) -> float | None:
    """Cohen's kappa for two nominal passes. None when it is undefined."""
    n = len(pairs)
    if n == 0:
        return None
    labels = sorted({left for left, _ in pairs} | {right for _, right in pairs})
    if len(labels) < 2:
        return None
    index = {label: pos for pos, label in enumerate(labels)}
    matrix = [[0] * len(labels) for _ in labels]
    for left, right in pairs:
        matrix[index[left]][index[right]] += 1
    observed = sum(matrix[i][i] for i in range(len(labels))) / n
    row_mass = [sum(matrix[i]) / n for i in range(len(labels))]
    col_mass = [sum(matrix[i][j] for i in range(len(labels))) / n for j in range(len(labels))]
    expected = sum(row_mass[i] * col_mass[i] for i in range(len(labels)))
    if expected == 1:
        return None
    return (observed - expected) / (1 - expected)


def agreement_report(rows: list[dict]) -> dict:
    complete = []
    for row in rows:
        left = (row.get("label_pass1") or "").strip()
        right = (row.get("label_pass2") or "").strip()
        if left and right:
            complete.append(row)
    label_pairs = [
        ((row.get("label_pass1") or "").strip(), (row.get("label_pass2") or "").strip())
        for row in complete
    ]
    card_pairs = [
        (card_set(row.get("cards_pass1") or ""), card_set(row.get("cards_pass2") or ""))
        for row in complete
    ]
    n = len(complete)
    label_agree = sum(left == right for left, right in label_pairs)
    card_agree = sum(left == right for left, right in card_pairs)
    unknown = sorted(
        {
            value
            for row in complete
            for value in (
                (row.get("label_pass1") or "").strip(),
                (row.get("label_pass2") or "").strip(),
            )
            if value not in LABELS
        }
    )
    return {
        "n_items": len(rows),
        "n_both_labeled": n,
        "n_label_agree": label_agree,
        "label_agreement": (label_agree / n) if n else None,
        "cohen_kappa_labels": cohen_kappa(label_pairs) if n else None,
        "n_card_agree": card_agree,
        "card_agreement": (card_agree / n) if n else None,
        "unknown_labels": unknown,
        "compared_to_proposed_labels": False,
    }


def format_report(report: dict) -> str:
    if report["n_both_labeled"] == 0:
        return (
            f"items={report['n_items']} both_passes_filled=0\n"
            "No pass-1/pass-2 pairs yet. Agreement is not computed.\n"
            "This script does not compare either pass to proposed synthesizer labels.\n"
        )
    kappa = report["cohen_kappa_labels"]
    kappa_text = "undefined" if kappa is None else f"{kappa:.4f}"
    lines = [
        f"items={report['n_items']} both_passes_filled={report['n_both_labeled']}",
        f"label_agreement={report['label_agreement']:.4f} ({report['n_label_agree']}/{report['n_both_labeled']})",
        f"cohen_kappa_labels={kappa_text}",
        f"card_set_agreement={report['card_agreement']:.4f} ({report['n_card_agree']}/{report['n_both_labeled']})",
        "Compared passes to each other only. Proposed synthesizer labels were not used.",
    ]
    if report["unknown_labels"]:
        lines.append("labels outside {violation, near-miss, clean, ambiguous}: " + ", ".join(report["unknown_labels"]))
    return "\n".join(lines) + "\n"


def cmd_export(args: argparse.Namespace) -> int:
    steps = load_jsonl(args.candidates)
    export_sheet(steps, args.sheet)
    print(f"wrote {len(steps)} labeling rows to {args.sheet}")
    print("Proposed labels are not in this sheet.")
    return 0


def cmd_agree(args: argparse.Namespace) -> int:
    rows = read_sheet(args.sheet)
    report = agreement_report(rows)
    text = format_report(report)
    print(text, end="")
    if args.json:
        args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"wrote {args.json}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    export = sub.add_parser("export", help="write the labeling sheet from candidates")
    export.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    export.add_argument("--sheet", type=Path, default=DEFAULT_SHEET)
    export.set_defaults(func=cmd_export)
    agree = sub.add_parser("agree", help="compare pass 1 and pass 2 on a filled sheet")
    agree.add_argument("--sheet", type=Path, default=DEFAULT_SHEET)
    agree.add_argument("--json", type=Path, default=None)
    agree.set_defaults(func=cmd_agree)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
