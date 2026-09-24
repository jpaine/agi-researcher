#!/usr/bin/env python3
"""Week-1 smoke loop. Dry-run mock by default. Not a pilot result.

Loads OrgPolicy cards or matched prose, walks a tiny fixture JSONL in
fixed order, and logs allow/escalate/block decisions. Real Nebius
trajectory download and gold labels are still human week-1 work.

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


def load_steps(path: Path) -> list[dict]:
    steps = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            steps.append(json.loads(line))
    if not 2 <= len(steps) <= 3:
        raise SystemExit(f"fixture must have 2–3 steps, found {len(steps)}")
    return steps


def mock_judge(step: dict, policy_text: str) -> dict:
    """Deterministic dry-run. Does not score violations."""
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
    args = parser.parse_args()
    steps = load_steps(FIXTURE)
    order = [s["step_id"] for s in steps]
    conditions = ["cards", "prose"] if args.condition == "both" else [args.condition]
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    for condition in conditions:
        rows = run(condition, steps)
        got = [r["step_id"] for r in rows]
        if got != order:
            raise SystemExit(f"step order drifted for {condition}: {got} != {order}")
        out = LOG_DIR / f"smoke_{condition}.jsonl"
        out.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
        written.append(out)
        print(f"{condition}: {len(rows)} steps, order={got}, log={out}")
    print("Dry-run only. Token/time fields are null. Not a pilot metric.")
    print("Real Nebius trajectories and gold labels are still human week-1 work.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
