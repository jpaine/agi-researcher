"""Shared step-record helpers for the week-1 pilot.

Step JSONL is the input the smoke loop reads. Decision logs are separate
(`schema/log_line.md`). Nothing here is a gold label or a measured metric.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

CARD_IDS = (
    "cross-tenant",
    "external-exfil",
    "irreversible-delete",
    "pii-egress",
    "prod-write",
    "retention",
    "secrets",
    "sod-author-ne-approver",
    "sod-requester-ne-payer",
    "spend-limit",
)

TOOL_NAMES = ("editor", "fs", "git", "http", "terminal")

# Methods §1.2 fields, plus the fixture keys smoke_steps.jsonl already uses.
STEP_KEYS = (
    "trajectory_id",
    "step_id",
    "step_index",
    "timestamp",
    "tool_name",
    "tool_input",
    "tool_output",
    "agent_text",
    "repo_path",
    "file_path",
    "environment",
    "actor",
    "fixture",
    "gold",
    "metadata",
)

TRUNCATION_MARK = "…[truncated]"

_EMAIL = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
_GITHUB = re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b")
_AWS = re.compile(r"\bAKIA[0-9A-Z]{16}\b")
_SLACK = re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{10,}\b")
_OPENAI = re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")
_BEARER = re.compile(r"(?i)(bearer\s+)[A-Za-z0-9\-._~+/]+=*")
_PRIVATE_KEY = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
    re.S,
)


def scrub_text(text: str) -> tuple[str, int]:
    """Regex scrub for incidental emails and credential-shaped strings.

    Returns the scrubbed text and the number of replacements. This is not a
    claim that all personal data was removed.
    """
    if not text:
        return text, 0
    count = 0

    def sub(pattern: re.Pattern[str], repl: str, value: str) -> str:
        nonlocal count

        def _one(_match: re.Match[str]) -> str:
            nonlocal count
            count += 1
            return repl

        return pattern.sub(_one, value)

    value = text
    value = sub(_PRIVATE_KEY, "[redacted-private-key]", value)
    value = sub(_EMAIL, "[redacted-email]", value)
    value = sub(_GITHUB, "[redacted-token]", value)
    value = sub(_AWS, "[redacted-token]", value)
    value = sub(_SLACK, "[redacted-token]", value)
    value = sub(_OPENAI, "[redacted-token]", value)
    value = sub(_BEARER, r"\1[redacted-token]", value)
    return value, count


def truncate_text(text: str, limit: int) -> str:
    if text is None:
        return ""
    if limit < 1 or len(text) <= limit:
        return text
    mark = TRUNCATION_MARK
    if limit <= len(mark):
        return text[:limit]
    return text[: limit - len(mark)] + mark


def dump_jsonl(rows: list[dict]) -> str:
    return "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for row in rows
    )


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    text = path.read_text(encoding="utf-8")
    for line_no, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}:{line_no}: {exc}") from exc
        if not isinstance(obj, dict):
            raise SystemExit(f"{path}:{line_no}: expected a JSON object")
        rows.append(obj)
    return rows


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def require_step_keys(row: dict, *, where: str) -> None:
    missing = [key for key in STEP_KEYS if key not in row]
    if missing:
        raise SystemExit(f"{where}: missing step fields {missing}")
    if not isinstance(row["trajectory_id"], str) or not row["trajectory_id"]:
        raise SystemExit(f"{where}: trajectory_id must be a non-empty string")
    if not isinstance(row["step_id"], str) or not row["step_id"]:
        raise SystemExit(f"{where}: step_id must be a non-empty string")
    if not isinstance(row["step_index"], int) or row["step_index"] < 0:
        raise SystemExit(f"{where}: step_index must be a non-negative int")
    if row["tool_name"] not in TOOL_NAMES:
        raise SystemExit(f"{where}: unknown tool_name {row['tool_name']!r}")
    for key in ("tool_input", "tool_output", "agent_text", "actor"):
        if not isinstance(row[key], str):
            raise SystemExit(f"{where}: {key} must be a string")
    if row["timestamp"] is not None and not isinstance(row["timestamp"], str):
        raise SystemExit(f"{where}: timestamp must be a string or null")
    for key in ("repo_path", "file_path"):
        if row[key] is not None and not isinstance(row[key], str):
            raise SystemExit(f"{where}: {key} must be a string or null")
    if not isinstance(row["environment"], dict):
        raise SystemExit(f"{where}: environment must be an object")
    if not isinstance(row["fixture"], bool) or not isinstance(row["gold"], bool):
        raise SystemExit(f"{where}: fixture and gold must be booleans")
    if not isinstance(row["metadata"], dict):
        raise SystemExit(f"{where}: metadata must be an object")
