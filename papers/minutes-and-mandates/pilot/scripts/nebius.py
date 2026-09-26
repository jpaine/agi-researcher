#!/usr/bin/env python3
"""Nebius SWE-agent trajectory ingest.

Subcommands:
  fetch     Stream a seeded subset from Hugging Face into a gitignored raw file.
  convert   Turn that raw file into pilot step JSONL plus a manifest.
  validate  Check a converted sample against its manifest. No network.

The committed sample is a converted subset, not gold labels. Token and time
meters are not filled in here.

Fetch reads the dataset card at runtime (id, revision, license, split size).
Do not treat those fields as results of this pilot.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shlex
import sys
from pathlib import Path

from step_format import (
    dump_jsonl,
    load_jsonl,
    require_step_keys,
    scrub_text,
    sha256_text,
    truncate_text,
)

PILOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW = PILOT / "data" / "raw" / "nebius_subset.jsonl"
DEFAULT_STEPS = PILOT / "data" / "trajectories" / "nebius_sample.jsonl"
DEFAULT_MANIFEST = PILOT / "data" / "trajectories" / "manifest.json"

DATASET_ID = "nebius/SWE-agent-trajectories"
# Pinned after reading the Hub dataset card. `fetch` still records the card's
# own sha and license rather than assuming this constant is still current.
PINNED_REVISION = "68195a1450865274106246d0d0296a1d6807b88e"

DEFAULT_SEED = 20260926
DEFAULT_MODULUS = 40
DEFAULT_SCAN_LIMIT = 2000
DEFAULT_LIMIT = 10
DEFAULT_MIN_ACTIONS = 5
DEFAULT_MAX_ACTIONS = 70

TOOL_INPUT_CHARS = 1500
TOOL_OUTPUT_CHARS = 800
AGENT_TEXT_CHARS = 500

EDITOR = {
    "open",
    "edit",
    "create",
    "goto",
    "scroll_down",
    "scroll_up",
    "search_dir",
    "search_file",
    "find_file",
}
FS = {
    "ls",
    "pwd",
    "cd",
    "rm",
    "mkdir",
    "cp",
    "mv",
    "cat",
    "head",
    "tail",
    "find",
    "touch",
    "chmod",
    "ln",
    "stat",
    "du",
    "df",
}
GIT = {"git", "gh"}
HTTP = {"curl", "wget", "http", "httpie"}

_FENCE = re.compile(r"```(?:[A-Za-z0-9_+-]*)\n(.*?)```", re.S)
_CWD = re.compile(r"\(Current directory: ([^)]+)\)")
_OPEN = re.compile(r"\(Open file: ([^)]+)\)")


def keep_row(dataset_id: str, revision: str, seed: int, row_index: int, modulus: int) -> bool:
    """Deterministic membership test. Independent of streaming library version."""
    payload = f"{dataset_id}|{revision}|{seed}|{row_index}".encode()
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[:8], "big") % modulus == 0


def extract_command(text: str) -> str | None:
    blocks = _FENCE.findall(text or "")
    if not blocks:
        return None
    command = blocks[-1].strip("\n")
    if not command.strip():
        return None
    return command


def discussion_before_command(text: str) -> str:
    if not text:
        return ""
    matches = list(_FENCE.finditer(text))
    if not matches:
        return text.strip()
    return text[: matches[-1].start()].strip()


def first_line(command: str) -> str:
    for line in command.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def classify_tool(line: str) -> str:
    token = line.split()[0] if line.split() else ""
    base = token.rsplit("/", 1)[-1]
    if base in GIT:
        return "git"
    if base in HTTP:
        return "http"
    if base in EDITOR:
        return "editor"
    if base in FS:
        return "fs"
    return "terminal"


def split_command(line: str) -> list[str]:
    try:
        return shlex.split(line)
    except ValueError:
        return line.split()


def path_from_command(line: str, tool_name: str) -> str | None:
    tokens = split_command(line)
    if len(tokens) < 2:
        return None
    cmd = tokens[0].rsplit("/", 1)[-1]
    if cmd in {"open", "create"}:
        return tokens[1]
    if cmd == "search_file" and len(tokens) >= 3:
        return tokens[-1]
    if tool_name == "fs" and cmd in {"cat", "head", "tail", "rm", "cp", "mv"}:
        return tokens[1]
    return None


def usable_path(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.strip()
    if cleaned.lower() in {"n/a", "none", "null"}:
        return None
    return cleaned


def trajectory_to_steps(
    row: dict,
    *,
    row_index: int,
    revision: str,
    dataset_id: str = DATASET_ID,
) -> tuple[list[dict], dict]:
    """Convert one dataset row into pilot steps.

    A step is one assistant command (fenced block) plus the following
    observation when that observation is a user message. The dataset has no
    per-step timestamp; `timestamp` is null. `gold` is false.
    """
    messages = row.get("trajectory") or []
    if not isinstance(messages, list):
        raise SystemExit(f"row {row_index}: trajectory is not a list")

    open_file: str | None = None
    cwd: str | None = None
    cutoff_date = None
    skipped_no_command = 0
    redactions = 0
    steps: list[dict] = []

    for message_index, message in enumerate(messages):
        if not isinstance(message, dict):
            continue
        role = message.get("role")
        text = message.get("text") or ""
        if role == "system" and message.get("cutoff_date"):
            cutoff_date = message.get("cutoff_date")
        if role != "ai":
            found_cwd = _CWD.search(text)
            if found_cwd:
                cwd = usable_path(found_cwd.group(1))
            found_open = _OPEN.search(text)
            if found_open:
                open_file = usable_path(found_open.group(1)) or open_file
            continue
        command = extract_command(text)
        if command is None:
            skipped_no_command += 1
            continue
        observation = ""
        if message_index + 1 < len(messages):
            nxt = messages[message_index + 1]
            if isinstance(nxt, dict) and nxt.get("role") == "user":
                observation = nxt.get("text") or ""

        line = first_line(command)
        tool_name = classify_tool(line)
        file_path = path_from_command(line, tool_name) or open_file
        if line.split()[:1] and line.split()[0].rsplit("/", 1)[-1] in {"open", "create"}:
            open_file = path_from_command(line, tool_name) or open_file
        found_cwd = _CWD.search(observation)
        found_open = _OPEN.search(observation)
        if found_cwd:
            cwd = usable_path(found_cwd.group(1))
        if found_open:
            open_file = usable_path(found_open.group(1)) or open_file
        if file_path is None:
            file_path = open_file

        agent_text, n1 = scrub_text(discussion_before_command(text))
        tool_input, n2 = scrub_text(command)
        tool_output, n3 = scrub_text(observation)
        redactions += n1 + n2 + n3

        step_index = len(steps)
        instance_id = row.get("instance_id")
        steps.append(
            {
                "trajectory_id": f"nebius-r{row_index}",
                "step_id": f"s{step_index}",
                "step_index": step_index,
                "timestamp": None,
                "tool_name": tool_name,
                "tool_input": truncate_text(tool_input, TOOL_INPUT_CHARS),
                "tool_output": truncate_text(tool_output, TOOL_OUTPUT_CHARS),
                "agent_text": truncate_text(agent_text, AGENT_TEXT_CHARS),
                "repo_path": cwd,
                "file_path": file_path,
                "environment": {},
                "actor": "swe-agent",
                "fixture": False,
                "gold": False,
                "metadata": {
                    "source_dataset": dataset_id,
                    "source_revision": revision,
                    "source_row_index": row_index,
                    "source_message_index": message_index,
                    "instance_id": instance_id,
                    "model_name": row.get("model_name"),
                    "provider": None,
                    "target": row.get("target"),
                    "exit_status": row.get("exit_status"),
                    "cutoff_date": cutoff_date,
                    "tokens_estimate": None,
                    "redactions": n1 + n2 + n3,
                    "origin": "nebius",
                },
            }
        )

    stats = {
        "n_messages": len(messages),
        "n_steps": len(steps),
        "skipped_no_command": skipped_no_command,
        "redactions": redactions,
        "generated_patch_chars": len(row.get("generated_patch") or ""),
        "eval_logs_chars": len(row.get("eval_logs") or ""),
    }
    return steps, stats


def _card_value(card: object, key: str):
    if card is None:
        return None
    if isinstance(card, dict):
        return card.get(key)
    getter = getattr(card, "get", None)
    if callable(getter):
        try:
            value = getter(key)
        except Exception:
            value = None
        if value is not None:
            return value
    return getattr(card, key, None)


def read_dataset_card(dataset_id: str, revision: str) -> dict:
    """Read Hub metadata. Raises SystemExit if the hub library is missing."""
    try:
        from huggingface_hub import HfApi
    except ImportError as exc:
        raise SystemExit(
            "huggingface_hub is required for fetch. Install with: pip install 'datasets>=2.19'"
        ) from exc

    info = HfApi().dataset_info(dataset_id, revision=revision)
    card = info.card_data
    license_id = _card_value(card, "license")
    dataset_info = _card_value(card, "dataset_info") or {}
    if not isinstance(dataset_info, dict):
        dataset_info = dict(dataset_info) if hasattr(dataset_info, "items") else {}
    num_examples = None
    splits = dataset_info.get("splits") if isinstance(dataset_info, dict) else None
    if isinstance(splits, list):
        for split in splits:
            if isinstance(split, dict) and split.get("name") == "train":
                num_examples = split.get("num_examples")
    features = None
    if isinstance(dataset_info, dict):
        features = dataset_info.get("features")
    return {
        "dataset_id": dataset_id,
        "revision": info.sha,
        "requested_revision": revision,
        "license": license_id,
        "card_train_examples": num_examples,
        "gated": bool(getattr(info, "gated", False)),
        "private": bool(getattr(info, "private", False)),
        "features": features,
    }


def fetch_rows(args: argparse.Namespace) -> tuple[list[dict], dict]:
    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise SystemExit(
            "datasets is required for fetch. Install with: pip install 'datasets>=2.19'"
        ) from exc

    card = read_dataset_card(args.dataset, args.revision)
    if card["revision"] and args.revision and card["revision"] != args.revision:
        print(
            f"warning: hub sha {card['revision']} != requested revision {args.revision}",
            file=sys.stderr,
        )
    revision = card["revision"] or args.revision
    print(
        f"dataset={card['dataset_id']} revision={revision} license={card['license']} "
        f"card_train_examples={card['card_train_examples']}"
    )
    stream = load_dataset(args.dataset, split="train", streaming=True, revision=revision)
    selected: list[dict] = []
    considered = 0
    scanned = 0
    skipped: list[dict] = []
    for row_index, row in enumerate(stream):
        if row_index >= args.scan_limit:
            break
        scanned = row_index + 1
        if not keep_row(args.dataset, revision, args.seed, row_index, args.modulus):
            continue
        considered += 1
        plain = {key: row.get(key) for key in row.keys()}
        steps, stats = trajectory_to_steps(plain, row_index=row_index, revision=revision, dataset_id=args.dataset)
        if not args.min_actions <= stats["n_steps"] <= args.max_actions:
            skipped.append(
                {
                    "row_index": row_index,
                    "instance_id": plain.get("instance_id"),
                    "model_name": plain.get("model_name"),
                    "n_steps": stats["n_steps"],
                    "reason": "action_count_outside_bounds",
                }
            )
            continue
        stored = {
            "row_index": row_index,
            "instance_id": plain.get("instance_id"),
            "model_name": plain.get("model_name"),
            "target": plain.get("target"),
            "exit_status": plain.get("exit_status"),
            "trajectory": plain.get("trajectory"),
            "generated_patch_chars": stats["generated_patch_chars"],
            "eval_logs_chars": stats["eval_logs_chars"],
        }
        selected.append(stored)
        print(
            f"kept row {row_index} instance={plain.get('instance_id')} "
            f"model={plain.get('model_name')} steps={stats['n_steps']}",
            flush=True,
        )
        if len(selected) >= args.limit:
            break
    if len(selected) < args.limit:
        raise SystemExit(
            f"selected {len(selected)} trajectories after scanning {scanned} rows "
            f"(wanted {args.limit}). Raise --scan-limit or loosen action bounds."
        )
    try:
        import datasets as datasets_mod

        datasets_version = getattr(datasets_mod, "__version__", None)
    except Exception:
        datasets_version = None
    meta = {
        "card": card,
        "revision_used": revision,
        "scanned_rows": scanned,
        "hash_hits": considered,
        "skipped": skipped,
        "datasets_version": datasets_version,
        "selection_args": {
            "seed": args.seed,
            "modulus": args.modulus,
            "scan_limit": args.scan_limit,
            "limit": args.limit,
            "min_actions": args.min_actions,
            "max_actions": args.max_actions,
        },
    }
    return selected, meta


def convert_raw_rows(
    raw_rows: list[dict],
    *,
    revision: str,
    dataset_id: str,
    selection: dict,
    card: dict,
) -> tuple[list[dict], dict]:
    steps: list[dict] = []
    trajectories = []
    redactions = 0
    for raw in raw_rows:
        row_index = raw["row_index"]
        converted, stats = trajectory_to_steps(
            raw,
            row_index=row_index,
            revision=revision,
            dataset_id=dataset_id,
        )
        redactions += stats["redactions"]
        steps.extend(converted)
        trajectories.append(
            {
                "trajectory_id": f"nebius-r{row_index}",
                "row_index": row_index,
                "instance_id": raw.get("instance_id"),
                "model_name": raw.get("model_name"),
                "target": raw.get("target"),
                "exit_status": raw.get("exit_status"),
                "n_steps": stats["n_steps"],
                "n_messages": stats["n_messages"],
                "skipped_no_command": stats["skipped_no_command"],
                "redactions": stats["redactions"],
                "generated_patch_chars": raw.get("generated_patch_chars", stats["generated_patch_chars"]),
                "eval_logs_chars": raw.get("eval_logs_chars", stats["eval_logs_chars"]),
            }
        )
    body = dump_jsonl(steps)
    manifest = {
        "dataset_id": dataset_id,
        "revision": revision,
        "license": card.get("license"),
        "license_notes": [
            "The license field is the dataset card value at this revision (cc-by-4.0 when this sample was fetched).",
            "The dataset card says to respect each underlying repository's license. Those licenses are listed on nebius/SWE-bench-extra and are not columns on this trajectory set, so they are not joined here.",
            "The dataset card says: if you intend to use the outputs of these models, you must comply with the Llama 3.1 license.",
        ],
        "card_train_examples": card.get("card_train_examples"),
        "seed": selection["seed"],
        "selection": selection,
        "truncation": {
            "tool_input_chars": TOOL_INPUT_CHARS,
            "tool_output_chars": TOOL_OUTPUT_CHARS,
            "agent_text_chars": AGENT_TEXT_CHARS,
            "mark": "…[truncated]",
        },
        "omitted_from_raw_subset": [
            "generated_patch body (character count kept per trajectory)",
            "eval_logs body (character count kept per trajectory)",
        ],
        "actor_field": "swe-agent means the SWE-agent process in the trace. The source rows do not name a human principal.",
        "timestamp_field": "null because trajectory messages have no per-step timestamp. cutoff_date, when present, is copied into metadata and is not a step time.",
        "gold": False,
        "counts": {
            "trajectories": len(trajectories),
            "steps": len(steps),
            "redactions": redactions,
        },
        "trajectories": trajectories,
        "steps_sha256": sha256_text(body),
        "datasets_version": selection.get("datasets_version"),
    }
    return steps, manifest


def validate_sample(steps_path: Path, manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    text = steps_path.read_text(encoding="utf-8")
    digest = sha256_text(text)
    if digest != manifest.get("steps_sha256"):
        raise SystemExit(
            f"steps sha256 {digest} != manifest {manifest.get('steps_sha256')}"
        )
    steps = load_jsonl(steps_path)
    if len(steps) != manifest["counts"]["steps"]:
        raise SystemExit("step count does not match manifest")
    by_traj: dict[str, list[dict]] = {}
    for index, step in enumerate(steps):
        require_step_keys(step, where=f"{steps_path}:{index}")
        if step["gold"] is not False:
            raise SystemExit(f"{steps_path}:{index}: converted sample must not carry gold labels")
        if step["fixture"] is not False:
            raise SystemExit(f"{steps_path}:{index}: converted sample is not the smoke fixture")
        if step["metadata"].get("origin") != "nebius":
            raise SystemExit(f"{steps_path}:{index}: expected origin nebius")
        if step["timestamp"] is not None:
            raise SystemExit(f"{steps_path}:{index}: Nebius steps have no per-step timestamp")
        if "proposed_label" in step:
            raise SystemExit(f"{steps_path}:{index}: proposed labels do not belong on source steps")
        by_traj.setdefault(step["trajectory_id"], []).append(step)
    rows = manifest["trajectories"]
    if len(rows) != manifest["counts"]["trajectories"]:
        raise SystemExit("trajectory count does not match manifest")
    if set(by_traj) != {row["trajectory_id"] for row in rows}:
        raise SystemExit("trajectory ids in the sample do not match the manifest")
    for row in rows:
        group = by_traj[row["trajectory_id"]]
        if len(group) != row["n_steps"]:
            raise SystemExit(f"{row['trajectory_id']}: step count mismatch")
        indexes = [step["step_index"] for step in group]
        if indexes != list(range(len(group))):
            raise SystemExit(f"{row['trajectory_id']}: step_index is not 0..n-1 in order")
        for step in group:
            meta = step["metadata"]
            if meta.get("source_row_index") != row["row_index"]:
                raise SystemExit(f"{row['trajectory_id']}: row_index mismatch")
            if meta.get("instance_id") != row["instance_id"]:
                raise SystemExit(f"{row['trajectory_id']}: instance_id mismatch")
            if meta.get("source_dataset") != manifest["dataset_id"]:
                raise SystemExit("dataset id mismatch inside a step")
            if meta.get("source_revision") != manifest["revision"]:
                raise SystemExit("revision mismatch inside a step")
    required = ("dataset_id", "revision", "license", "seed", "selection", "counts")
    missing = [key for key in required if key not in manifest]
    if missing:
        raise SystemExit(f"manifest missing {missing}")
    return manifest


def write_raw(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_jsonl(rows), encoding="utf-8")


def cmd_fetch(args: argparse.Namespace) -> int:
    selected, meta = fetch_rows(args)
    write_raw(args.raw, selected)
    card_path = args.raw.with_suffix(".card.json")
    card_path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {len(selected)} raw trajectories to {args.raw}")
    print("Raw files are local only. Convert with: nebius.py convert")
    return 0


def cmd_convert(args: argparse.Namespace) -> int:
    raw_rows = load_jsonl(args.raw)
    card_path = args.raw.with_suffix(".card.json")
    if not card_path.exists():
        raise SystemExit(f"missing {card_path}; run fetch first so license and revision are recorded from the Hub")
    meta = json.loads(card_path.read_text(encoding="utf-8"))
    card = meta["card"]
    revision = meta["revision_used"]
    chosen = meta["selection_args"]
    selection = {
        "algorithm": "sha256_mod",
        "hash_input": "{dataset_id}|{revision}|{seed}|{row_index}",
        "keep_when": "int.from_bytes(sha256(hash_input).digest()[:8], 'big') % modulus == 0",
        "split": "train",
        "streaming": True,
        "seed": chosen["seed"],
        "modulus": chosen["modulus"],
        "scan_limit": chosen["scan_limit"],
        "limit": chosen["limit"],
        "min_actions": chosen["min_actions"],
        "max_actions": chosen["max_actions"],
        "scanned_rows": meta["scanned_rows"],
        "hash_hits": meta["hash_hits"],
        "skipped": meta["skipped"],
        "datasets_version": meta.get("datasets_version"),
        "order": "streaming train order at the pinned revision; row_index is the enumeration index",
    }
    steps, manifest = convert_raw_rows(
        raw_rows,
        revision=revision,
        dataset_id=card["dataset_id"],
        selection=selection,
        card=card,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    body = dump_jsonl(steps)
    if sha256_text(body) != manifest["steps_sha256"]:
        raise SystemExit("internal sha mismatch")
    args.out.write_text(body, encoding="utf-8")
    args.manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"wrote {manifest['counts']['trajectories']} trajectories, "
        f"{manifest['counts']['steps']} steps -> {args.out}"
    )
    print(f"manifest {args.manifest} license={manifest['license']} revision={manifest['revision']}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    manifest = validate_sample(args.steps, args.manifest)
    print(
        f"ok {manifest['dataset_id']}@{manifest['revision']} license={manifest['license']} "
        f"trajectories={manifest['counts']['trajectories']} steps={manifest['counts']['steps']}"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    fetch = sub.add_parser("fetch", help="stream a seeded subset into data/raw (gitignored)")
    fetch.add_argument("--dataset", default=DATASET_ID)
    fetch.add_argument("--revision", default=PINNED_REVISION)
    fetch.add_argument("--seed", type=int, default=DEFAULT_SEED)
    fetch.add_argument("--modulus", type=int, default=DEFAULT_MODULUS)
    fetch.add_argument("--scan-limit", type=int, default=DEFAULT_SCAN_LIMIT)
    fetch.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    fetch.add_argument("--min-actions", type=int, default=DEFAULT_MIN_ACTIONS)
    fetch.add_argument("--max-actions", type=int, default=DEFAULT_MAX_ACTIONS)
    fetch.add_argument("--raw", type=Path, default=DEFAULT_RAW)
    fetch.set_defaults(func=cmd_fetch)

    convert = sub.add_parser("convert", help="convert the raw subset into pilot steps")
    convert.add_argument("--raw", type=Path, default=DEFAULT_RAW)
    convert.add_argument("--out", type=Path, default=DEFAULT_STEPS)
    convert.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    convert.set_defaults(func=cmd_convert)

    validate = sub.add_parser("validate", help="check converted steps against the manifest")
    validate.add_argument("--steps", type=Path, default=DEFAULT_STEPS)
    validate.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    validate.set_defaults(func=cmd_validate)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    try:
        code = main()
    except BrokenPipeError:
        code = 1
    # datasets/pyarrow can abort during interpreter shutdown after a successful
    # fetch. Skip that teardown once main has returned.
    if len(sys.argv) > 1 and sys.argv[1] == "fetch":
        import os

        os._exit(code)
    raise SystemExit(code)
