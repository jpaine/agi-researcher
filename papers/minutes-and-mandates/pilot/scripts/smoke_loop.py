#!/usr/bin/env python3
"""Week-1 smoke loop.

Default judge is the dry-run mock (CI). It does not fill token or time
fields and it does not download a model.

``--judge llama`` loads the pinned CPU GGUF. ``--judge openai`` calls
JUDGE_BASE_URL / JUDGE_MODEL. Both measuring backends validate JSON against
schema/judge_output.schema.json and log parse failures without rewriting
the model text.

Conditions A (cards) and B (prose) share one step order. Gold labels are
still a human labeling task. Proposed labels are not read by the judge.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from judge import (  # noqa: E402
    DEFAULT_DECODE,
    MockJudge,
    OpenAICompatibleJudge,
    build_llama_judge,
    evaluate,
    library_versions,
)
from model_pin import pin_record  # noqa: E402
from prompts import build_messages, load_policy_artifact, prompt_sha256  # noqa: E402

PILOT = Path(__file__).resolve().parents[1]
REPO = PILOT.parents[2]
FIXTURE = PILOT / "data" / "fixtures" / "smoke_steps.jsonl"
LOG_DIR = PILOT / "logs"
CANDIDATES = PILOT / "data" / "injects" / "candidates.jsonl"

# Time budget used only when a measuring judge is asked to size its own subset.
DEFAULT_SUBSET_BUDGET_MS = 45 * 60 * 1000
DEFAULT_SUBSET_MINIMUM = 20


def load_steps(path: Path, *, fixture_mode: bool) -> list[dict]:
    steps = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}:{line_no}: {exc}") from exc
        if not isinstance(obj, dict):
            raise SystemExit(f"{path}:{line_no}: expected a JSON object")
        if "trajectory_id" not in obj or "step_id" not in obj:
            raise SystemExit(f"{path}:{line_no}: missing trajectory_id or step_id")
        steps.append(obj)
    if not steps:
        raise SystemExit(f"no steps in {path}")
    if fixture_mode and not 2 <= len(steps) <= 3:
        raise SystemExit(f"fixture must have 2–3 steps, found {len(steps)}")
    return steps


def permute_steps(steps: list[dict], seed: int | None) -> list[dict]:
    """File order, or one Random(seed).shuffle permutation. Python's Random.shuffle."""
    if seed is None:
        return list(steps)
    order = list(steps)
    random.Random(seed).shuffle(order)
    return order


def subset_size_from_probe_ms(
    probe_ms: int,
    *,
    n_available: int,
    budget_ms: int,
    minimum: int,
) -> int:
    """How many paired steps fit in budget_ms at the probe's per-call time.

    Two conditions share the subset, so each step costs about two calls.
    The result is at least ``minimum`` when that many steps exist, and never
    above ``n_available``.
    """
    if probe_ms <= 0:
        raise ValueError("probe_ms must be positive")
    if n_available < 1 or minimum < 1 or budget_ms < 0:
        raise ValueError("subset inputs out of range")
    fit = budget_ms // (probe_ms * 2)
    return min(n_available, max(min(minimum, n_available), fit))


def host_record(n_threads: int) -> dict:
    cpu: dict[str, str] = {}
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.exists():
        for line in cpuinfo.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                break
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            cpu[key.strip()] = value.strip()
    mem: dict[str, int] = {}
    meminfo = Path("/proc/meminfo")
    if meminfo.exists():
        for line in meminfo.read_text(encoding="utf-8").splitlines():
            key, rest = line.split(":", 1)
            if key in {"MemTotal", "MemAvailable", "MemFree"}:
                mem[key] = int(rest.strip().split()[0])
    flags = cpu.get("flags", "").split()
    return {
        "cpu_model": cpu.get("model name", ""),
        "vendor_id": cpu.get("vendor_id", ""),
        "cpu_family": cpu.get("cpu family", ""),
        "cpu_model_number": cpu.get("model", ""),
        "cpu_stepping": cpu.get("stepping", ""),
        "cpu_mhz": cpu.get("cpu MHz", ""),
        "avx512f": "avx512f" in flags,
        "nproc": os.cpu_count(),
        "n_threads": n_threads,
        "mem_total_kib": mem.get("MemTotal"),
        "mem_available_kib": mem.get("MemAvailable"),
        "mem_free_kib": mem.get("MemFree"),
    }


def git_head() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def rel_repo(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO))
    except ValueError:
        return str(path)


def log_row(condition: str, index: int, step: dict, policy_chars: int, judge, evaluation: dict, messages: list[dict]) -> dict:
    row = {
        "condition": condition,
        "trajectory_id": step["trajectory_id"],
        "step_id": step["step_id"],
        "step_index": index,
        "decision": evaluation["decision"],
        "matched_cards": evaluation["matched_cards"],
        "rationale": evaluation["rationale"],
        "risk_score": evaluation["risk_score"],
        "risk_score_omitted": evaluation["risk_score_omitted"],
        "judge": judge.name,
        "tokens_in": evaluation["tokens_in"],
        "tokens_out": evaluation["tokens_out"],
        "wall_time_ms": evaluation["wall_time_ms"],
        "policy_artifact": condition,
        "policy_chars": policy_chars,
        "parse_ok": evaluation["parse_ok"],
        "parse_failure_count": evaluation["parse_failure_count"],
        "attempt_count": evaluation["attempt_count"],
        "attempts": evaluation["attempts"],
        "prompt_sha256": prompt_sha256(messages),
    }
    row.update(judge.describe())
    if any(str(key).startswith("proposed_") for key in row):
        raise SystemExit("judge log must not copy proposed labels")
    return row


def run(condition: str, steps: list[dict], judge=None, sink: Path | None = None) -> list[dict]:
    judge = judge or MockJudge()
    policy = load_policy_artifact(condition)
    rows = []
    handle = sink.open("w", encoding="utf-8") if sink is not None else None
    try:
        for index, step in enumerate(steps):
            messages = build_messages(condition, step)
            evaluation = evaluate(judge, messages)
            row = log_row(condition, index, step, len(policy), judge, evaluation, messages)
            rows.append(row)
            if handle is not None:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                handle.flush()
                if judge.measures:
                    print(
                        f"{condition} {row['step_id']} decision={row['decision']} "
                        f"parse_ok={row['parse_ok']} wall_time_ms={row['wall_time_ms']}",
                        flush=True,
                    )
    finally:
        if handle is not None:
            handle.close()
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--condition", choices=("cards", "prose", "both"), default="both")
    parser.add_argument("--steps", type=Path, default=None, help="Step JSONL. Default: the 3-step fixture.")
    parser.add_argument("--limit", type=int, default=None, help="Use the first N steps after the optional permutation.")
    parser.add_argument(
        "--subset-seed",
        type=int,
        default=None,
        help="Shuffle step order with random.Random(seed) before --limit. Same order for every condition.",
    )
    parser.add_argument(
        "--subset-budget-ms",
        type=int,
        default=DEFAULT_SUBSET_BUDGET_MS,
        help="When --limit is omitted on a measuring judge, size the subset from one probe call.",
    )
    parser.add_argument("--subset-minimum", type=int, default=DEFAULT_SUBSET_MINIMUM)
    parser.add_argument("--judge", choices=("mock", "llama", "openai"), default="mock")
    parser.add_argument("--n-ctx", type=int, default=8192)
    parser.add_argument("--n-threads", type=int, default=os.cpu_count() or 1)
    parser.add_argument("--n-batch", type=int, default=512)
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_DECODE["max_tokens"])
    parser.add_argument("--decode-seed", type=int, default=DEFAULT_DECODE["seed"])
    parser.add_argument("--log-dir", type=Path, default=LOG_DIR)
    parser.add_argument(
        "--download-model",
        action="store_true",
        help="Download and hash-check the pinned GGUF, then exit.",
    )
    args = parser.parse_args()

    if args.download_model:
        from model_pin import ensure_gguf

        path = ensure_gguf()
        print(f"verified {path}")
        return 0

    if args.limit is not None and args.limit < 1:
        raise SystemExit("--limit must be >= 1")
    if args.subset_minimum < 1:
        raise SystemExit("--subset-minimum must be >= 1")

    decode = dict(DEFAULT_DECODE)
    decode["max_tokens"] = args.max_tokens
    decode["seed"] = args.decode_seed

    steps_path = args.steps or FIXTURE
    steps = load_steps(steps_path, fixture_mode=args.steps is None)
    ordered = permute_steps(steps, args.subset_seed)

    started = _utc_now()
    host_before_load = host_record(args.n_threads)
    libraries = library_versions()
    code_sha = git_head()

    if args.judge == "mock":
        judge = MockJudge()
    elif args.judge == "llama":
        judge = build_llama_judge(
            n_ctx=args.n_ctx,
            n_threads=args.n_threads,
            n_batch=args.n_batch,
            decode=decode,
        )
    else:
        judge = OpenAICompatibleJudge(decode=decode)

    probe = None
    if judge.measures and args.limit is None:
        probe_step = ordered[0]
        probe_messages = build_messages("cards", probe_step)
        probe_eval = evaluate(judge, probe_messages)
        if not isinstance(probe_eval["wall_time_ms"], int) or probe_eval["wall_time_ms"] <= 0:
            raise SystemExit("probe call did not record a positive wall time")
        chosen = subset_size_from_probe_ms(
            probe_eval["wall_time_ms"],
            n_available=len(ordered),
            budget_ms=args.subset_budget_ms,
            minimum=args.subset_minimum,
        )
        probe = {
            "condition": "cards",
            "step_id": probe_step["step_id"],
            "wall_time_ms": probe_eval["wall_time_ms"],
            "tokens_in": probe_eval["tokens_in"],
            "tokens_out": probe_eval["tokens_out"],
            "parse_ok": probe_eval["parse_ok"],
            "parse_failure_count": probe_eval["parse_failure_count"],
            "attempt_count": probe_eval["attempt_count"],
            "included_in_paired_logs": False,
            "budget_ms": args.subset_budget_ms,
            "minimum_steps": args.subset_minimum,
            "n_available": len(ordered),
            "chosen_limit": chosen,
        }
        print(
            f"probe step {probe_step['step_id']}: {probe_eval['wall_time_ms']} ms, "
            f"chosen limit {chosen} (not written to the paired logs)",
            flush=True,
        )
        judged = ordered[:chosen]
    else:
        judged = ordered if args.limit is None else ordered[: args.limit]

    if not judged:
        raise SystemExit("no steps selected")

    conditions = ["cards", "prose"] if args.condition == "both" else [args.condition]
    order = [step["step_id"] for step in judged]
    args.log_dir.mkdir(parents=True, exist_ok=True)
    paired_started = _utc_now()

    for condition in conditions:
        out = args.log_dir / f"smoke_{condition}.jsonl"
        rows = run(condition, judged, judge, sink=out)
        if not judge.measures:
            for row in rows:
                if row["tokens_in"] is not None or row["tokens_out"] is not None or row["wall_time_ms"] is not None:
                    raise SystemExit("dry-run filled a token or time field")
                if row["judge"] != "dry-run-mock":
                    raise SystemExit("dry-run swapped in a real judge")
        else:
            for row in rows:
                if row["tokens_in"] is None or row["tokens_out"] is None or row["wall_time_ms"] is None:
                    raise SystemExit("measuring judge left a meter null")
        got = [row["step_id"] for row in rows]
        if got != order:
            raise SystemExit(f"step order drifted for {condition}: {got} != {order}")
        print(f"{condition}: {len(rows)} steps, order={got}, log={out}", flush=True)

    finished = _utc_now()
    if judge.measures:
        limit_used = len(judged)
        manifest = {
            "kind": "minutes-and-mandates-judge-smoke",
            "started_at_utc": started,
            "paired_started_at_utc": paired_started,
            "finished_at_utc": finished,
            "code_git_sha": code_sha,
            "hosted_endpoint_calls": 0 if args.judge == "llama" else None,
            "cost_note": (
                "Local llama.cpp only. No hosted endpoint was called."
                if args.judge == "llama"
                else "OpenAI-compatible endpoint was called. This manifest does not record a dollar cost."
            ),
            "steps_file": rel_repo(steps_path),
            "subset_seed": args.subset_seed,
            "permutation": (
                "random.Random(subset_seed).shuffle of file order, then the first limit steps"
                if args.subset_seed is not None
                else "file order, then the first limit steps"
            ),
            "python_random": f"{sys.version.split()[0]} random.Random.shuffle",
            "limit": limit_used,
            "step_ids": order,
            "conditions": conditions,
            "probe": probe,
            "decode": decode,
            "decode_note": "The decode seed is passed on every llama.cpp or HTTP call.",
            "host": host_before_load if args.judge == "llama" else {"n_threads": None},
            "libraries": libraries,
            "model": pin_record() if args.judge == "llama" else {"openai_model": os.environ.get("JUDGE_MODEL")},
            "llama": (
                {
                    "load_wall_time_ms": judge.load_wall_time_ms,
                    "chat_format": judge.chat_format,
                    "chat_template_sha256": prompt_sha256([{"template": judge.chat_template}]),
                    "chat_template_mentions_think": "think" in judge.chat_template.lower(),
                    "system_info": judge.system_info.strip(),
                    "n_gpu_layers": 0,
                    "prompt_cache": False,
                    "context_reset_before_call": True,
                }
                if args.judge == "llama"
                else None
            ),
        }
        manifest_path = args.log_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"manifest={manifest_path}", flush=True)
        print("Measured run. Proposed labels were not shown to the judge and are not gold.")
    else:
        print("Dry-run only. Token/time fields are null. Not a pilot metric.")
        print("Gold labels are still human work. This mock does not judge violations.")
    return 0


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


if __name__ == "__main__":
    raise SystemExit(main())
