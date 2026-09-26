#!/usr/bin/env python3
"""Seeded inject candidate generator.

Reads converted pilot steps and the per-card templates. Emits a balanced set
of proposed violation and near-miss foil steps. Every intended label is
`proposed`. Gold labels are not created here.
"""

from __future__ import annotations

import argparse
import json
import random
import re
from collections import Counter
from pathlib import Path

import yaml

from step_format import CARD_IDS, TOOL_NAMES, dump_jsonl, load_jsonl, require_step_keys, sha256_text

PILOT = Path(__file__).resolve().parents[1]
REPO = PILOT.parents[2]
TEMPLATES = PILOT / "injects" / "templates"
CARDS = REPO / "brainstorm" / "minutes-and-mandates" / "cards"
DEFAULT_STEPS = PILOT / "data" / "trajectories" / "nebius_sample.jsonl"
DEFAULT_OUT = PILOT / "data" / "injects" / "candidates.jsonl"
DEFAULT_MANIFEST = PILOT / "data" / "injects" / "manifest.json"

DEFAULT_SEED = 20260926
DEFAULT_PER_KIND = 3
_PLACEHOLDER = re.compile(r"\{[a-zA-Z0-9_]+\}")


def fill(text: str, params: dict) -> str:
    out = "" if text is None else str(text)
    for key in sorted(params, key=len, reverse=True):
        out = out.replace("{" + key + "}", str(params[key]))
    leftover = _PLACEHOLDER.findall(out)
    if leftover:
        raise SystemExit(f"unfilled placeholder {leftover} in {out!r}")
    return out


def load_templates(directory: Path) -> dict[str, dict]:
    found = {}
    for path in sorted(directory.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise SystemExit(f"{path} is not a mapping")
        if data.get("card_id") != path.stem:
            raise SystemExit(f"{path} card_id {data.get('card_id')!r} != filename")
        found[path.stem] = data
    return found


def load_clauses(cards_dir: Path) -> dict[str, set[str]]:
    clauses = {}
    for path in sorted(cards_dir.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        clauses[path.stem] = {item["id"] for item in data["escalate_when"]}
    return clauses


def validate_templates(templates: dict[str, dict], clauses: dict[str, set[str]]) -> None:
    if tuple(sorted(templates)) != CARD_IDS:
        raise SystemExit(f"template ids {sorted(templates)} != locked cards {list(CARD_IDS)}")
    for card_id, spec in templates.items():
        if spec.get("label_status") != "proposed":
            raise SystemExit(f"{card_id}: label_status must be proposed")
        attach = spec.get("attach_tool_names") or []
        if not attach or any(name not in TOOL_NAMES for name in attach):
            raise SystemExit(f"{card_id}: attach_tool_names must use {TOOL_NAMES}")
        renderings = spec.get("renderings") or {}
        examples = spec.get("examples") or {}
        for kind in ("violation", "foil"):
            items = renderings.get(kind) or []
            shown = examples.get(kind) or []
            if not 2 <= len(items) <= 3:
                raise SystemExit(f"{card_id} {kind}: need 2–3 renderings, found {len(items)}")
            if [item["id"] for item in items] != [item["id"] for item in shown]:
                raise SystemExit(f"{card_id} {kind}: examples are not the concrete renderings")
            for item, shown_item in zip(items, shown):
                clause_id = item["clause_id"]
                if clause_id not in clauses[card_id]:
                    raise SystemExit(f"{card_id}: clause {clause_id} is not on the card")
                params = item["example_params"]
                for field in ("actor", "tool_input", "tool_output", "agent_text"):
                    if fill(item[field], params) != shown_item[field]:
                        raise SystemExit(f"{card_id} {item['id']} {field}: example rendering drifted")
                if item["tool_name"] != shown_item["tool_name"]:
                    raise SystemExit(f"{card_id} {item['id']}: tool_name example drifted")
                if item["tool_name"] not in TOOL_NAMES:
                    raise SystemExit(f"{card_id} {item['id']}: bad tool_name")
                env = item.get("environment") or {}
                shown_env = shown_item.get("environment") or {}
                filled_env = {key: fill(str(value), params) for key, value in env.items()}
                if filled_env != shown_env:
                    raise SystemExit(f"{card_id} {item['id']}: environment example drifted")


def group_steps(steps: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {}
    for index, step in enumerate(steps):
        require_step_keys(step, where=f"trajectory step {index}")
        if step.get("gold") is True:
            raise SystemExit("refusing to inject on steps already marked gold")
        groups.setdefault(step["trajectory_id"], []).append(step)
    for group in groups.values():
        group.sort(key=lambda step: step["step_index"])
    if not groups:
        raise SystemExit("no trajectories to attach injects to")
    return groups


def bridge(source: dict) -> str:
    bits = []
    if source.get("repo_path"):
        bits.append(f"cwd {source['repo_path']}")
    if source.get("file_path"):
        bits.append(f"file {source['file_path']}")
    where = f" ({', '.join(bits)})" if bits else ""
    return f"Next command in this SWE-agent session{where}. "


def build_candidates(
    steps: list[dict],
    templates: dict[str, dict],
    *,
    seed: int,
    per_kind: int,
) -> tuple[list[dict], dict]:
    if per_kind < 1:
        raise SystemExit("--per-kind must be >= 1")
    groups = group_steps(steps)
    rng = random.Random(seed)
    order = sorted(groups)
    rng.shuffle(order)
    cursor = 0
    matched = 0
    fallback = 0

    def pick_source(attach: list[str]) -> tuple[dict, str]:
        nonlocal cursor, matched, fallback
        for _ in range(len(order)):
            trajectory_id = order[cursor % len(order)]
            cursor += 1
            pool = [step for step in groups[trajectory_id] if step["tool_name"] in attach]
            if pool:
                matched += 1
                return rng.choice(pool), "matched_tool"
        trajectory_id = order[cursor % len(order)]
        cursor += 1
        fallback += 1
        return rng.choice(groups[trajectory_id]), "fallback_any_step"

    pending = []
    for card_id in sorted(templates):
        spec = templates[card_id]
        for kind in ("violation", "foil"):
            variants = spec["renderings"][kind]
            for index in range(per_kind):
                variant = variants[index % len(variants)]
                params = {
                    key: rng.choice(list(values))
                    for key, values in sorted(spec["parameters"].items())
                }
                source, how = pick_source(list(spec["attach_tool_names"]))
                env = {
                    key: fill(str(value), params)
                    for key, value in (variant.get("environment") or {}).items()
                }
                pending.append(
                    {
                        "card_id": card_id,
                        "kind": kind,
                        "variant": variant,
                        "params": {key: str(value) for key, value in params.items()},
                        "source": source,
                        "attachment": how,
                        "environment": env,
                    }
                )
    rng.shuffle(pending)

    rows = []
    items = []
    for index, item in enumerate(pending):
        source = item["source"]
        variant = item["variant"]
        params = item["params"]
        item_id = f"inj-{index:04d}"
        file_path = source.get("file_path")
        if variant.get("file_path"):
            file_path = fill(str(variant["file_path"]), params)
        row = {
            "trajectory_id": source["trajectory_id"],
            "step_id": item_id,
            "step_index": source["step_index"],
            "timestamp": None,
            "tool_name": variant["tool_name"],
            "tool_input": fill(variant["tool_input"], params),
            "tool_output": fill(variant["tool_output"], params),
            "agent_text": bridge(source) + fill(variant["agent_text"], params),
            "repo_path": source.get("repo_path"),
            "file_path": file_path,
            "environment": item["environment"],
            "actor": fill(variant["actor"], params),
            "fixture": False,
            "gold": False,
            "injected": True,
            "label_status": "proposed",
            "proposed_label": item["kind"],
            "proposed_card_id": item["card_id"],
            "proposed_clause_id": variant["clause_id"],
            "template_variant": variant["id"],
            "metadata": {
                "origin": "inject",
                "label_status": "proposed",
                "source_trajectory_id": source["trajectory_id"],
                "source_step_index": source["step_index"],
                "source_step_id": source["step_id"],
                "source_tool_name": source["tool_name"],
                "source_tool_input": (source.get("tool_input") or "")[:180],
                "attachment": item["attachment"],
                "template_params": params,
                "tokens_estimate": None,
                "provider": None,
            },
        }
        require_step_keys(row, where=item_id)
        if row["proposed_label"] not in {"violation", "foil"}:
            raise SystemExit(f"{item_id}: bad proposed label")
        if row["gold"] is not False or row["label_status"] != "proposed":
            raise SystemExit(f"{item_id}: labels must stay proposed")
        rows.append(row)
        items.append(
            {
                "item_id": item_id,
                "source_trajectory_id": source["trajectory_id"],
                "source_step_index": source["step_index"],
                "source_step_id": source["step_id"],
                "card_id": item["card_id"],
                "clause_id": variant["clause_id"],
                "template_variant": variant["id"],
                "proposed_label": item["kind"],
                "label_status": "proposed",
                "attachment": item["attachment"],
                "template_params": params,
            }
        )

    by_card = Counter(item["card_id"] for item in items)
    by_label = Counter(item["proposed_label"] for item in items)
    for card_id in CARD_IDS:
        if by_card[card_id] != per_kind * 2:
            raise SystemExit(f"{card_id}: expected {per_kind * 2} candidates, found {by_card[card_id]}")
    if by_label["violation"] != by_label["foil"]:
        raise SystemExit(f"unbalanced proposed labels: {dict(by_label)}")
    manifest = {
        "seed": seed,
        "per_kind": per_kind,
        "n_candidates": len(rows),
        "label_status": "proposed",
        "note": (
            "proposed_label is the synthesizer's intended class (violation or near-miss foil). "
            "It is not a gold label. Gold labels come from two human labeling passes."
        ),
        "counts_by_card": {card_id: by_card[card_id] for card_id in CARD_IDS},
        "counts_by_proposed_label": dict(sorted(by_label.items())),
        "attachment_counts": {"matched_tool": matched, "fallback_any_step": fallback},
        "items": items,
    }
    return rows, manifest


def write_outputs(rows: list[dict], manifest: dict, out: Path, manifest_path: Path) -> None:
    body = dump_jsonl(rows)
    manifest = dict(manifest)
    manifest["candidates_sha256"] = sha256_text(body)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(body, encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trajectories", type=Path, default=DEFAULT_STEPS)
    parser.add_argument("--templates", type=Path, default=TEMPLATES)
    parser.add_argument("--cards", type=Path, default=CARDS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--per-kind", type=int, default=DEFAULT_PER_KIND)
    args = parser.parse_args(argv)

    templates = load_templates(args.templates)
    validate_templates(templates, load_clauses(args.cards))
    steps = load_jsonl(args.trajectories)
    rows, manifest = build_candidates(steps, templates, seed=args.seed, per_kind=args.per_kind)
    manifest["source_steps_sha256"] = sha256_text(args.trajectories.read_text(encoding="utf-8"))
    write_outputs(rows, manifest, args.out, args.manifest)
    print(
        f"wrote {manifest['n_candidates']} proposed candidates "
        f"({manifest['counts_by_proposed_label']}) -> {args.out}"
    )
    print("Intended labels are proposed only. Not gold.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
