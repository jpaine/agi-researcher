#!/usr/bin/env python3
"""Week-1 smoke loop. Dry-run mock by default. Not a pilot result.

Loads OrgPolicy cards or matched prose, walks step JSONL in fixed order,
and logs allow/escalate/block decisions. The default input is the 3-step
fixture. `--steps` can point at the generated inject candidates.

The judge is a dry-run mock. It does not read labels and it does not fill
token or time fields. Gold labels are still a human labeling task.

OPENAI_API_KEY is optional and unused. This stub never calls the network.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

PILOT = Path(__file__).resolve().parents[1]
REPO = PILOT.parents[2]
CARDS = REPO / "brainstorm" / "minutes-and-mandates" / "cards"
FIXTURE = PILOT / "data" / "fixtures" / "smoke_steps.jsonl"
LOG_DIR = PILOT / "logs"


def load_artifact(condition: str) -> str:
    if condition == "cards":
        parts = []
        for path in sorted(CARDS.glob("*.yaml")):
            parts.append(path.read_text(encoding="utf-8"))
        if len(parts) != 10:
            raise SystemExit(f"expected 10 card YAML files, found {len(parts)}")
        return "\n".join(parts)
    if condition == "prose":
        parts = []
        for path in sorted((CARDS / "prose").glob("*.md")):
            parts.append(path.read_text(encoding="utf-8"))
        if len(parts) != 10:
            raise SystemExit(f"expected 10 prose files, found {len(parts)}")
        return "\n".join(parts)
    raise SystemExit(f"unknown condition {condition}")


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


def mock_judge(step: dict, policy_text: str) -> dict:
    """Deterministic dry-run. Does not score violations or read proposed labels."""
    del step, policy_text
    return {
        "decision": "allow",
        "matched_cards": [],
        "rationale": "dry-run mock; not a measured judgment",
        "risk_score": None,
    }


def run(condition: str, steps: list[dict]) -> list[dict]:
    policy = load_artifact(condition)
    rows = []
    for index, step in enumerate(steps):
        decision = mock_judge(step, policy)
        rows.append(
            {
                "condition": condition,
                "trajectory_id": step["trajectory_id"],
                "step_id": step["step_id"],
                "step_index": index,
                "decision": decision["decision"],
                "matched_cards": decision["matched_cards"],
                "rationale": decision["rationale"],
                "risk_score": None,
                "judge": "dry-run-mock",
                "tokens_in": None,
                "tokens_out": None,
                "wall_time_ms": None,
                "policy_artifact": condition,
                "policy_chars": len(policy),
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--condition",
        choices=("cards", "prose", "both"),
        default="both",
        help="A=cards, B=prose, or both in the same step order",
    )
    parser.add_argument(
        "--steps",
        type=Path,
        default=None,
        help="Step JSONL to judge. Default: the 3-step fixture.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Use only the first N steps, in file order, for every condition.",
    )
    parser.add_argument("--log-dir", type=Path, default=LOG_DIR)
    args = parser.parse_args()
    steps_path = args.steps or FIXTURE
    steps = load_steps(steps_path, fixture_mode=args.steps is None)
    if args.limit is not None:
        if args.limit < 1:
            raise SystemExit("--limit must be >= 1")
        steps = steps[: args.limit]
    order = [s["step_id"] for s in steps]
    conditions = ["cards", "prose"] if args.condition == "both" else [args.condition]
    args.log_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for condition in conditions:
        rows = run(condition, steps)
        for row in rows:
            if row["tokens_in"] is not None or row["tokens_out"] is not None or row["wall_time_ms"] is not None:
                raise SystemExit("dry-run filled a token or time field")
            if row["judge"] != "dry-run-mock":
                raise SystemExit("dry-run swapped in a real judge")
        got = [r["step_id"] for r in rows]
        if got != order:
            raise SystemExit(f"step order drifted for {condition}: {got} != {order}")
        out = args.log_dir / f"smoke_{condition}.jsonl"
        out.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
        written.append(out)
        print(f"{condition}: {len(rows)} steps, order={got}, log={out}")
    print("Dry-run only. Token/time fields are null. Not a pilot metric.")
    print("Gold labels are still human work. This mock does not judge violations.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
