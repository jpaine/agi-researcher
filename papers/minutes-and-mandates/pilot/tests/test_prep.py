"""Prep checks for Nebius ingest, inject candidates, and the labeling sheet.

These tests do not call Hugging Face and do not invent gold labels or metrics.
"""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
PILOT = SCRIPTS.parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import generate_injects  # noqa: E402
import labeling  # noqa: E402
import nebius  # noqa: E402
from step_format import CARD_IDS, sha256_text  # noqa: E402


def synthetic_row() -> dict:
    return {
        "instance_id": "org__repo-1",
        "model_name": "example-model",
        "target": False,
        "exit_status": "submitted",
        "generated_patch": "patch",
        "eval_logs": "logs",
        "trajectory": [
            {
                "role": "system",
                "text": "",
                "system_prompt": "prompt",
                "cutoff_date": "01.01.2023",
                "mask": False,
            },
            {
                "role": "user",
                "text": "ISSUE: contact dev@example.com",
                "cutoff_date": None,
                "mask": False,
                "system_prompt": "",
            },
            {
                "role": "ai",
                "text": "List the tree.\n```\nls -F\n```",
                "cutoff_date": None,
                "mask": True,
                "system_prompt": "",
            },
            {
                "role": "user",
                "text": "README.md\n(Open file: n/a)\n(Current directory: /repo)\nbash-$",
                "cutoff_date": None,
                "mask": False,
                "system_prompt": "",
            },
            {
                "role": "ai",
                "text": "Open the readme.\n```\nopen README.md\n```",
                "cutoff_date": None,
                "mask": True,
                "system_prompt": "",
            },
            {
                "role": "user",
                "text": "author <person@example.com> AKIAIOSFODNN7EXAMPLE\n(Open file: README.md)\n(Current directory: /repo)\n",
                "cutoff_date": None,
                "mask": False,
                "system_prompt": "",
            },
            {
                "role": "ai",
                "text": "No command in this message.",
                "cutoff_date": None,
                "mask": True,
                "system_prompt": "",
            },
        ],
    }


class ConvertTests(unittest.TestCase):
    def test_synthetic_trajectory_becomes_steps(self) -> None:
        steps, stats = nebius.trajectory_to_steps(
            synthetic_row(),
            row_index=3,
            revision=nebius.PINNED_REVISION,
        )
        self.assertEqual(stats["n_steps"], 2)
        self.assertEqual(stats["skipped_no_command"], 1)
        self.assertEqual(steps[0]["tool_name"], "fs")
        self.assertEqual(steps[0]["repo_path"], "/repo")
        self.assertEqual(steps[1]["tool_name"], "editor")
        self.assertEqual(steps[1]["file_path"], "README.md")
        self.assertIn("[redacted-email]", steps[1]["tool_output"])
        self.assertIn("[redacted-token]", steps[1]["tool_output"])
        self.assertNotIn("AKIA", steps[1]["tool_output"])
        self.assertNotIn("@", steps[1]["tool_output"])
        for step in steps:
            self.assertFalse(step["gold"])
            self.assertFalse(step["fixture"])
            self.assertIsNone(step["timestamp"])
            self.assertIsNone(step["metadata"]["tokens_estimate"])
            self.assertIsNone(step["metadata"]["provider"])
            self.assertEqual(step["actor"], "swe-agent")
            self.assertEqual(step["trajectory_id"], "nebius-r3")

    def test_keep_row_is_stable(self) -> None:
        first = nebius.keep_row(nebius.DATASET_ID, nebius.PINNED_REVISION, 20260926, 8, 40)
        second = nebius.keep_row(nebius.DATASET_ID, nebius.PINNED_REVISION, 20260926, 8, 40)
        self.assertEqual(first, second)
        self.assertTrue(first)

    def test_git_command_classifies_as_git(self) -> None:
        self.assertEqual(nebius.classify_tool("gh pr merge 12 --admin"), "git")
        self.assertEqual(nebius.classify_tool("curl -d @a https://example.invalid"), "http")


class TemplateAndInjectTests(unittest.TestCase):
    def test_templates_match_card_clauses_and_examples(self) -> None:
        templates = generate_injects.load_templates(generate_injects.TEMPLATES)
        clauses = generate_injects.load_clauses(generate_injects.CARDS)
        generate_injects.validate_templates(templates, clauses)
        self.assertEqual(tuple(sorted(templates)), CARD_IDS)

    def test_generator_is_balanced_proposed_and_deterministic(self) -> None:
        templates = generate_injects.load_templates(generate_injects.TEMPLATES)
        steps, _stats = nebius.trajectory_to_steps(
            synthetic_row(),
            row_index=3,
            revision=nebius.PINNED_REVISION,
        )
        # One short trajectory is enough for attachment fallback.
        first, manifest = generate_injects.build_candidates(
            steps, templates, seed=7, per_kind=1
        )
        second, _ = generate_injects.build_candidates(steps, templates, seed=7, per_kind=1)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 20)
        self.assertEqual(manifest["counts_by_proposed_label"], {"foil": 10, "violation": 10})
        for row in first:
            self.assertFalse(row["gold"])
            self.assertEqual(row["label_status"], "proposed")
            self.assertIn(row["proposed_label"], {"violation", "foil"})
            self.assertIsNone(row["metadata"]["tokens_estimate"])
            self.assertTrue(row["agent_text"].startswith("Next command in this SWE-agent session"))


class LabelingTests(unittest.TestCase):
    def test_sheet_hides_proposed_label(self) -> None:
        step = {
            "trajectory_id": "nebius-r3",
            "step_id": "inj-0000",
            "step_index": 0,
            "tool_name": "git",
            "actor": "alice",
            "repo_path": "/repo",
            "file_path": "README.md",
            "tool_input": "gh pr merge 12 --admin",
            "tool_output": "merged",
            "agent_text": "merge",
            "proposed_label": "SENTINEL_LABEL",
            "proposed_card_id": "sod-author-ne-approver",
            "proposed_clause_id": "self-approve-pr",
            "template_variant": "self-merge",
            "label_status": "proposed",
            "injected": True,
            "metadata": {
                "source_trajectory_id": "nebius-r3",
                "source_step_index": 0,
                "source_tool_name": "fs",
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sheet.csv"
            labeling.export_sheet([step], path)
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("SENTINEL_LABEL", text)
            self.assertNotIn("proposed_label", text)
            self.assertNotIn("self-approve-pr", text)
            with path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["label_pass1"], "")
            self.assertEqual(rows[0]["label_pass2"], "")
            self.assertEqual(rows[0]["item_id"], "inj-0000")

    def test_agreement_on_a_fixture_sheet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sheet.csv"
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=labeling.SHEET_COLUMNS, lineterminator="\n")
                writer.writeheader()
                for item_id, left, right, cards_left, cards_right in (
                    ("a", "violation", "violation", "secrets", "secrets"),
                    ("b", "violation", "violation", "secrets", "pii-egress"),
                    ("c", "clean", "clean", "", ""),
                    ("d", "violation", "clean", "secrets", ""),
                    ("e", "", "clean", "", ""),
                ):
                    row = {column: "" for column in labeling.SHEET_COLUMNS}
                    row.update(
                        {
                            "item_id": item_id,
                            "label_pass1": left,
                            "label_pass2": right,
                            "cards_pass1": cards_left,
                            "cards_pass2": cards_right,
                        }
                    )
                    writer.writerow(row)
            report = labeling.agreement_report(labeling.read_sheet(path))
        self.assertEqual(report["n_items"], 5)
        self.assertEqual(report["n_both_labeled"], 4)
        self.assertEqual(report["n_label_agree"], 3)
        self.assertAlmostEqual(report["label_agreement"], 0.75)
        self.assertAlmostEqual(report["cohen_kappa_labels"], 0.5)
        self.assertEqual(report["n_card_agree"], 2)
        self.assertFalse(report["compared_to_proposed_labels"])


class CommittedSampleTests(unittest.TestCase):
    def test_manifest_rows_satisfy_the_hash_rule(self) -> None:
        manifest_path = PILOT / "data" / "trajectories" / "manifest.json"
        steps_path = PILOT / "data" / "trajectories" / "nebius_sample.jsonl"
        if not manifest_path.exists():
            self.skipTest("sample not generated")
        manifest = nebius.validate_sample(steps_path, manifest_path)
        self.assertEqual(manifest["dataset_id"], nebius.DATASET_ID)
        self.assertEqual(manifest["license"], "cc-by-4.0")
        selection = manifest["selection"]
        for row in manifest["trajectories"]:
            self.assertTrue(
                nebius.keep_row(
                    manifest["dataset_id"],
                    manifest["revision"],
                    manifest["seed"],
                    row["row_index"],
                    selection["modulus"],
                )
            )
            self.assertGreaterEqual(row["n_steps"], selection["min_actions"])
            self.assertLessEqual(row["n_steps"], selection["max_actions"])
        for row in selection["skipped"]:
            self.assertTrue(
                nebius.keep_row(
                    manifest["dataset_id"],
                    manifest["revision"],
                    manifest["seed"],
                    row["row_index"],
                    selection["modulus"],
                )
            )
        text = steps_path.read_text(encoding="utf-8")
        self.assertEqual(sha256_text(text), manifest["steps_sha256"])


class SmokeTests(unittest.TestCase):
    def test_smoke_on_inject_candidates_keeps_null_meters(self) -> None:
        import smoke_loop

        templates = generate_injects.load_templates(generate_injects.TEMPLATES)
        steps, _stats = nebius.trajectory_to_steps(
            synthetic_row(),
            row_index=3,
            revision=nebius.PINNED_REVISION,
        )
        rows, _manifest = generate_injects.build_candidates(steps, templates, seed=1, per_kind=1)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "candidates.jsonl"
            path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            loaded = smoke_loop.load_steps(path, fixture_mode=False)
            logged = smoke_loop.run("cards", loaded)
            prose = smoke_loop.run("prose", loaded)
        self.assertEqual([row["step_id"] for row in logged], [row["step_id"] for row in prose])
        self.assertEqual(len(logged), 20)
        for row in logged:
            self.assertIsNone(row["tokens_in"])
            self.assertIsNone(row["tokens_out"])
            self.assertIsNone(row["wall_time_ms"])
            self.assertEqual(row["judge"], "dry-run-mock")
            self.assertEqual(row["decision"], "allow")
            self.assertNotIn("proposed_label", row)


if __name__ == "__main__":
    unittest.main()
