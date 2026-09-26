#!/usr/bin/env python3
"""Render SMOKE_REPORT.md from a measured smoke log. No other number source."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

PILOT = Path(__file__).resolve().parents[1]


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}:{line_no}: {exc}") from exc
        rows.append(obj)
    return rows


def load_proposed_labels(path: Path) -> dict[str, str]:
    labels: dict[str, str] = {}
    for row in load_jsonl(path):
        step_id = row["step_id"]
        if step_id in labels:
            raise SystemExit(f"duplicate step_id in candidates: {step_id}")
        labels[step_id] = row["proposed_label"]
    return labels


def _require_int(row: dict, key: str) -> int:
    value = row[key]
    if not isinstance(value, int):
        raise SystemExit(f"{row.get('step_id')} {key} is not an int")
    return value


def condition_facts(rows: list[dict]) -> dict:
    if not rows:
        raise SystemExit("empty condition log")
    tokens_in = [_require_int(row, "tokens_in") for row in rows]
    tokens_out = [_require_int(row, "tokens_out") for row in rows]
    wall = [_require_int(row, "wall_time_ms") for row in rows]
    think_attempts = 0
    for row in rows:
        for attempt in row["attempts"]:
            raw = attempt["raw_output"].lower()
            if "<think" in raw or "</think>" in raw:
                think_attempts += 1
    final_fail = sum(1 for row in rows if row["parse_ok"] is not True)
    first_fail = 0
    for row in rows:
        attempts = row["attempts"]
        if not attempts:
            raise SystemExit(f"{row['step_id']} has no attempts")
        if attempts[0]["parse_ok"] is not True:
            first_fail += 1
    decisions = {"allow": 0, "escalate": 0, "block": 0}
    for row in rows:
        if row["parse_ok"] is True and row["decision"] in decisions:
            decisions[row["decision"]] += 1
    return {
        "n": len(rows),
        "final_parse_failures": final_fail,
        "first_attempt_parse_failures": first_fail,
        "tokens_in_sum": sum(tokens_in),
        "tokens_in_min": min(tokens_in),
        "tokens_in_max": max(tokens_in),
        "tokens_out_sum": sum(tokens_out),
        "tokens_out_min": min(tokens_out),
        "tokens_out_max": max(tokens_out),
        "wall_time_ms_sum": sum(wall),
        "wall_time_ms_min": min(wall),
        "wall_time_ms_max": max(wall),
        "decisions": decisions,
        "escalations": decisions["escalate"] + decisions["block"],
        "think_tag_attempts": think_attempts,
    }


def sanity_table(rows: list[dict], labels: dict[str, str]) -> list[dict]:
    buckets: dict[str, dict[str, int]] = {}
    for row in rows:
        step_id = row["step_id"]
        if step_id not in labels:
            raise SystemExit(f"{step_id} is not in the candidate file")
        label = labels[step_id]
        cell = buckets.setdefault(
            label,
            {"allow": 0, "escalate": 0, "block": 0, "parse_fail": 0, "n": 0},
        )
        cell["n"] += 1
        if row["parse_ok"] is not True:
            cell["parse_fail"] += 1
        elif row["decision"] in {"allow", "escalate", "block"}:
            cell[row["decision"]] += 1
        else:
            raise SystemExit(f"{step_id} parse_ok with unexpected decision")
    return [{"proposed_label": label, **buckets[label]} for label in sorted(buckets)]


def _ms_as_seconds(ms: int) -> str:
    sign = "-" if ms < 0 else ""
    magnitude = abs(ms)
    return f"{sign}{magnitude // 1000}.{magnitude % 1000:03d}"


def _call_table(rows: list[dict]) -> str:
    header = (
        "| step_index | step_id | decision | parse_ok | parse_failure_count | "
        "attempt_count | tokens_in | tokens_out | wall_time_ms | wall_time_s |"
    )
    sep = "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"
    lines = [header, sep]
    for row in rows:
        decision = row["decision"] if row["decision"] is not None else "null"
        lines.append(
            "| {step_index} | {step_id} | {decision} | {parse_ok} | {parse_failure_count} | "
            "{attempt_count} | {tokens_in} | {tokens_out} | {wall_time_ms} | {seconds} |".format(
                step_index=row["step_index"],
                step_id=row["step_id"],
                decision=decision,
                parse_ok="true" if row["parse_ok"] is True else "false",
                parse_failure_count=row["parse_failure_count"],
                attempt_count=row["attempt_count"],
                tokens_in=row["tokens_in"],
                tokens_out=row["tokens_out"],
                wall_time_ms=row["wall_time_ms"],
                seconds=_ms_as_seconds(row["wall_time_ms"]),
            )
        )
    return "\n".join(lines)


def _sanity_md(table: list[dict]) -> str:
    lines = [
        "| proposed_label | allow | escalate | block | parse_fail | n |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in table:
        lines.append(
            f"| {row['proposed_label']} | {row['allow']} | {row['escalate']} | "
            f"{row['block']} | {row['parse_fail']} | {row['n']} |"
        )
    return "\n".join(lines)


def _kv_table(pairs: list[tuple[str, object]]) -> str:
    lines = []
    for key, value in pairs:
        text = str(value).replace("\n", " ")
        lines.append(f"- {key}: `{text}`")
    return "\n".join(lines)


def render_report(
    manifest: dict,
    cards: list[dict],
    prose: list[dict],
    labels: dict[str, str],
) -> str:
    if [row["step_id"] for row in cards] != manifest["step_ids"]:
        raise SystemExit("cards log step order does not match the manifest")
    if [row["step_id"] for row in prose] != manifest["step_ids"]:
        raise SystemExit("prose log step order does not match the manifest")
    if len(cards) != manifest["limit"] or len(prose) != manifest["limit"]:
        raise SystemExit("log length does not match manifest limit")
    probe = manifest.get("probe")
    if probe is not None:
        if probe["included_in_paired_logs"] is not False:
            raise SystemExit("probe must stay out of the paired logs")
        if probe["chosen_limit"] != manifest["limit"]:
            raise SystemExit("manifest limit does not match the probe chosen_limit")
    if cards and cards[0].get("judge") == "llama-cpp":
        expected_sha = manifest["model"]["sha256"]
        expected_threads = manifest["host"]["n_threads"]
        for row in cards + prose:
            if row.get("model_sha256") != expected_sha:
                raise SystemExit("log model sha256 does not match the manifest")
            if row.get("n_threads") != expected_threads:
                raise SystemExit("log n_threads does not match the manifest")
    if [row["step_index"] for row in cards] != list(range(len(cards))):
        raise SystemExit("cards step_index is not 0..n-1 in order")
    if [row["step_index"] for row in prose] != list(range(len(prose))):
        raise SystemExit("prose step_index is not 0..n-1 in order")

    card_facts = condition_facts(cards)
    prose_facts = condition_facts(prose)
    card_sanity = sanity_table(cards, labels)
    prose_sanity = sanity_table(prose, labels)
    host = manifest["host"]
    model = manifest["model"]
    libraries = manifest["libraries"]
    decode = manifest["decode"]
    llama = manifest.get("llama") or {}

    def block(title: str, facts: dict, rows: list[dict]) -> str:
        rate_final = f"{facts['final_parse_failures']}/{facts['n']}"
        rate_first = f"{facts['first_attempt_parse_failures']}/{facts['n']}"
        return "\n".join(
            [
                f"### {title}",
                "",
                f"- calls: {facts['n']}",
                f"- final parse-failure rate: {rate_final} (schema-invalid after the logged retry, if any)",
                f"- first-attempt parse-failure rate: {rate_first}",
                f"- decisions among schema-valid calls: allow {facts['decisions']['allow']}, "
                f"escalate {facts['decisions']['escalate']}, block {facts['decisions']['block']}",
                f"- escalations (escalate + block, schema-valid only): {facts['escalations']}",
                f"- attempts whose raw_output contains a think tag: {facts['think_tag_attempts']}",
                f"- tokens_in sum {facts['tokens_in_sum']}, min {facts['tokens_in_min']}, max {facts['tokens_in_max']}",
                f"- tokens_out sum {facts['tokens_out_sum']}, min {facts['tokens_out_min']}, max {facts['tokens_out_max']}",
                f"- wall_time_ms sum {facts['wall_time_ms_sum']}, min {facts['wall_time_ms_min']}, max {facts['wall_time_ms_max']}",
                f"- wall_time_s sum {_ms_as_seconds(facts['wall_time_ms_sum'])}, "
                f"min {_ms_as_seconds(facts['wall_time_ms_min'])}, max {_ms_as_seconds(facts['wall_time_ms_max'])}",
                "",
                _call_table(rows),
                "",
            ]
        )

    probe_lines = ["Probe: none. `--limit` was set explicitly."]
    if probe is not None:
        probe_lines = [
            f"- probe step_id: {probe['step_id']}",
            f"- probe condition: {probe['condition']}",
            f"- probe included in paired logs: {str(probe['included_in_paired_logs']).lower()}",
            f"- probe wall_time_ms: {probe['wall_time_ms']}",
            f"- probe wall_time_s: {_ms_as_seconds(probe['wall_time_ms'])}",
            f"- probe tokens_in: {probe['tokens_in']}",
            f"- probe tokens_out: {probe['tokens_out']}",
            f"- probe parse_ok: {str(probe['parse_ok']).lower()}",
            f"- probe parse_failure_count: {probe['parse_failure_count']}",
            f"- probe attempt_count: {probe['attempt_count']}",
            f"- budget_ms: {probe['budget_ms']}",
            f"- minimum_steps: {probe['minimum_steps']}",
            f"- n_available: {probe['n_available']}",
            f"- chosen_limit: {probe['chosen_limit']}",
            "- chosen_limit = min(n_available, max(min(minimum_steps, n_available), budget_ms // (probe_wall_time_ms * 2)))",
            "- The probe step_id may also appear in the paired logs. That row is a separate call. Probe timings are not copied into the tables.",
        ]

    parts = [
        "# Judge smoke — condition A (cards) vs condition B (prose)",
        "",
        "Every count in this file is computed from `smoke/manifest.json`, `smoke/smoke_cards.jsonl`, and `smoke/smoke_prose.jsonl` by `scripts/summarize_smoke.py`.",
        "",
        "Proposed labels are not gold. They are the synthesizer `proposed_label` values on `data/injects/candidates.jsonl` (`violation` or `foil`). Jeffrey's two labeling passes are pending. The cross-tab below is a sanity check against those proposed labels. It is not a detection rate and not an accuracy claim.",
        "",
        "## Run",
        "",
        _kv_table(
            [
                ("started_at_utc", manifest["started_at_utc"]),
                ("paired_started_at_utc", manifest["paired_started_at_utc"]),
                ("finished_at_utc", manifest["finished_at_utc"]),
                ("code_git_sha", manifest["code_git_sha"]),
                ("hosted_endpoint_calls", manifest["hosted_endpoint_calls"]),
                ("cost_note", manifest["cost_note"]),
                ("steps_file", manifest["steps_file"]),
                ("subset_seed", manifest["subset_seed"]),
                ("permutation", manifest["permutation"]),
                ("limit", manifest["limit"]),
                ("conditions", ", ".join(manifest["conditions"])),
            ]
        ),
        "",
        "## Model",
        "",
        _kv_table([(key, model[key]) for key in model]),
        "",
        "## Host",
        "",
        _kv_table([(key, host[key]) for key in host]),
        "",
        "## Libraries",
        "",
        _kv_table([(key, libraries[key]) for key in libraries]),
        "",
        "## Decode",
        "",
        _kv_table([(key, decode[key]) for key in decode]),
        "",
        manifest.get("decode_note", ""),
        "",
        "## llama.cpp",
        "",
        _kv_table([(key, llama[key]) for key in llama]) if llama else "No llama.cpp block in the manifest.",
        "",
        "## Subset",
        "",
        *probe_lines,
        "",
        f"Paired step_ids ({len(manifest['step_ids'])}): " + ", ".join(manifest["step_ids"]),
        "",
        "Condition A is `cards`. Condition B is `prose`. Both logs use the step_id order above. A call is one step in one condition. `tokens_in`, `tokens_out`, and `wall_time_ms` on a call are the sums of its attempts, including the one retry when `attempt_count` is 2.",
        "",
        "## Calls",
        "",
        block("cards (condition A)", card_facts, cards),
        block("prose (condition B)", prose_facts, prose),
        "## Sanity check against proposed labels",
        "",
        "Joined on `step_id` to `data/injects/candidates.jsonl`. `parse_fail` means the call was still schema-invalid. Those calls are not counted as allow, escalate, or block.",
        "",
        "### cards (condition A)",
        "",
        _sanity_md(card_sanity),
        "",
        "### prose (condition B)",
        "",
        _sanity_md(prose_sanity),
        "",
    ]
    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log-dir", type=Path, required=True)
    parser.add_argument("--candidates", type=Path, default=PILOT / "data" / "injects" / "candidates.jsonl")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads((args.log_dir / "manifest.json").read_text(encoding="utf-8"))
    cards = load_jsonl(args.log_dir / "smoke_cards.jsonl")
    prose = load_jsonl(args.log_dir / "smoke_prose.jsonl")
    labels = load_proposed_labels(args.candidates)
    text = render_report(manifest, cards, prose, labels)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
