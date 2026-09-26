#!/usr/bin/env python3
"""Render CALIBRATION_REPORT.md from committed calibration logs only."""

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


def load_proposed_labels(*paths: Path) -> dict[str, str]:
    labels: dict[str, str] = {}
    for path in paths:
        for row in load_jsonl(path):
            step_id = row["step_id"]
            if step_id in labels and labels[step_id] != row["proposed_label"]:
                raise SystemExit(f"conflicting proposed_label for {step_id}")
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
    }


def sanity_table(rows: list[dict], labels: dict[str, str]) -> list[dict]:
    buckets: dict[str, dict[str, int]] = {}
    for row in rows:
        step_id = row["step_id"]
        if step_id not in labels:
            raise SystemExit(f"{step_id} is not in the proposed-label files")
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


def load_run(log_dir: Path) -> tuple[dict, list[dict], list[dict]]:
    manifest = json.loads((log_dir / "manifest.json").read_text(encoding="utf-8"))
    cards = load_jsonl(log_dir / "smoke_cards.jsonl")
    prose = load_jsonl(log_dir / "smoke_prose.jsonl")
    if [row["step_id"] for row in cards] != manifest["step_ids"]:
        raise SystemExit(f"{log_dir}: cards step order does not match manifest")
    if [row["step_id"] for row in prose] != manifest["step_ids"]:
        raise SystemExit(f"{log_dir}: prose step order does not match manifest")
    return manifest, cards, prose


def render_run_section(
    title: str,
    manifest: dict,
    cards: list[dict],
    prose: list[dict],
    labels: dict[str, str],
) -> str:
    card_facts = condition_facts(cards)
    prose_facts = condition_facts(prose)
    card_sanity = sanity_table(cards, labels)
    prose_sanity = sanity_table(prose, labels)
    prompt_version = manifest.get("prompt_version")
    if prompt_version is None:
        # Older smoke manifests predate the field; those runs used v0 wording.
        prompt_version = "v0 (implicit; pre-versioning smoke)"
    model = manifest.get("model") or {}
    host = manifest.get("host") or {}
    libraries = manifest.get("libraries") or {}

    def facts_block(name: str, facts: dict) -> str:
        rate_final = f"{facts['final_parse_failures']}/{facts['n']}"
        return "\n".join(
            [
                f"#### {name}",
                "",
                f"- calls: {facts['n']}",
                f"- final parse-failure rate: {rate_final}",
                f"- first-attempt parse-failure rate: {facts['first_attempt_parse_failures']}/{facts['n']}",
                f"- decisions among schema-valid calls: allow {facts['decisions']['allow']}, "
                f"escalate {facts['decisions']['escalate']}, block {facts['decisions']['block']}",
                f"- escalations (escalate + block, schema-valid only): {facts['escalations']}",
                f"- tokens_in sum {facts['tokens_in_sum']}, min {facts['tokens_in_min']}, max {facts['tokens_in_max']}",
                f"- tokens_out sum {facts['tokens_out_sum']}, min {facts['tokens_out_min']}, max {facts['tokens_out_max']}",
                f"- wall_time_ms sum {facts['wall_time_ms_sum']}, min {facts['wall_time_ms_min']}, max {facts['wall_time_ms_max']}",
                f"- wall_time_s sum {_ms_as_seconds(facts['wall_time_ms_sum'])}, "
                f"min {_ms_as_seconds(facts['wall_time_ms_min'])}, max {_ms_as_seconds(facts['wall_time_ms_max'])}",
                "",
            ]
        )

    parts = [
        f"### {title}",
        "",
        _kv_table(
            [
                ("log_dir", manifest.get("_log_dir", "")),
                ("started_at_utc", manifest["started_at_utc"]),
                ("finished_at_utc", manifest["finished_at_utc"]),
                ("code_git_sha", manifest.get("code_git_sha")),
                ("prompt_version", prompt_version),
                ("steps_file", manifest.get("steps_file")),
                ("limit", manifest.get("limit")),
                ("subset_seed", manifest.get("subset_seed")),
                ("hosted_endpoint_calls", manifest.get("hosted_endpoint_calls")),
                ("cost_note", manifest.get("cost_note")),
                ("model_repo", model.get("repo_id") or model.get("openai_model")),
                ("model_filename", model.get("filename")),
                ("model_sha256", model.get("sha256")),
                ("n_threads", host.get("n_threads")),
                ("mem_available_kib", host.get("mem_available_kib")),
                ("llama_cpp_python", libraries.get("llama_cpp_python")),
            ]
        ),
        "",
        facts_block("cards (condition A)", card_facts),
        facts_block("prose (condition B)", prose_facts),
        "Sanity check vs proposed labels (not gold, not detection rates):",
        "",
        "cards:",
        "",
        _sanity_md(card_sanity),
        "",
        "prose:",
        "",
        _sanity_md(prose_sanity),
        "",
    ]
    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--meta",
        type=Path,
        required=True,
        help="JSON describing which log dirs to include and the narrative fields.",
    )
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    meta = json.loads(args.meta.read_text(encoding="utf-8"))
    label_paths = [Path(p) for p in meta["proposed_label_files"]]
    labels = load_proposed_labels(*label_paths)

    sections = []
    for run in meta["runs"]:
        log_dir = Path(run["log_dir"])
        manifest, cards, prose = load_run(log_dir)
        manifest = dict(manifest)
        manifest["_log_dir"] = run["log_dir"]
        sections.append(
            render_run_section(run["title"], manifest, cards, prose, labels)
        )

    parts = [
        "# Judge calibration — decision bar and holdout",
        "",
        "Every count in this file is computed from the committed JSONL logs and manifests "
        "listed below by `scripts/summarize_calibration.py`. Numbers are not invented.",
        "",
        "Proposed labels (`violation`, `foil`, `clean`) are synthesizer / clean-by-construction "
        "intention only. They are **not gold**. Cross-tabs are a sanity check, not detection rates.",
        "",
        "## Protocol",
        "",
        meta["protocol_markdown"].rstrip(),
        "",
        "## Runs",
        "",
        "\n".join(sections),
        "## Not verified",
        "",
        meta["not_verified_markdown"].rstrip(),
        "",
    ]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
