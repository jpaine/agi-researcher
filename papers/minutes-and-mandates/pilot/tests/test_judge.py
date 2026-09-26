"""Prompt builder and judge-output schema tests.

These tests do not download a model and do not invent pilot metrics.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
PILOT = SCRIPTS.parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import judge  # noqa: E402
import prompts  # noqa: E402
import smoke_loop  # noqa: E402
import summarize_smoke  # noqa: E402


def _step() -> dict:
    return {
        "trajectory_id": "t-sentinel",
        "step_id": "s-sentinel",
        "step_index": 4,
        "timestamp": None,
        "tool_name": "terminal",
        "tool_input": "echo SENTINEL_INPUT",
        "tool_output": "SENTINEL_OUTPUT",
        "agent_text": "SENTINEL_AGENT",
        "repo_path": "/repo",
        "file_path": "README.md",
        "environment": {"target_env": "dev"},
        "actor": "casey",
        "fixture": False,
        "gold": False,
        "proposed_label": "SENTINEL_LABEL",
        "proposed_card_id": "SENTINEL_CARD",
        "proposed_clause_id": "SENTINEL_CLAUSE",
        "template_variant": "SENTINEL_VARIANT",
        "label_status": "proposed",
        "injected": True,
        "metadata": {"template_params": {"spender": "SENTINEL_META"}},
    }


class PromptTests(unittest.TestCase):
    def test_instructions_differ_only_by_artifact_phrase(self) -> None:
        for version in prompts.PROMPT_TEMPLATES:
            cards = prompts.system_prompt("cards", version)
            prose = prompts.system_prompt("prose", version)
            self.assertEqual(cards.count(prompts.ARTIFACT_PHRASE["cards"]), 1)
            self.assertEqual(prose.count(prompts.ARTIFACT_PHRASE["prose"]), 1)
            self.assertEqual(
                cards.replace(prompts.ARTIFACT_PHRASE["cards"], "ARTIFACT"),
                prose.replace(prompts.ARTIFACT_PHRASE["prose"], "ARTIFACT"),
            )
            self.assertIn("decide allow/escalate/block", cards)
            self.assertIn("card_id", cards)
            self.assertIn("clause", cards.lower())

    def test_v1_has_decision_bar(self) -> None:
        text = prompts.system_prompt("cards", "v1")
        self.assertIn("Default decision is allow", text)
        self.assertIn("Escalate only when the step clearly matches", text)
        self.assertIn("Block only for an unambiguous severe violation", text)
        self.assertNotIn("Default decision is allow", prompts.system_prompt("cards", "v0"))

    def test_same_step_same_examples_same_card_content(self) -> None:
        step = _step()
        for version in ("v0", "v1"):
            cards_messages = prompts.build_messages("cards", step, prompt_version=version)
            prose_messages = prompts.build_messages("prose", step, prompt_version=version)
            self.assertEqual(cards_messages[0]["role"], "system")
            self.assertEqual(prose_messages[0]["role"], "system")
            cards_head, _, cards_policy = cards_messages[1]["content"].partition(prompts.POLICY_MARKER)
            prose_head, _, prose_policy = prose_messages[1]["content"].partition(prompts.POLICY_MARKER)
            self.assertEqual(cards_head, prose_head)
            self.assertIn("echo SENTINEL_INPUT", cards_head)
            self.assertIn("SENTINEL_OUTPUT", cards_head)
            self.assertNotEqual(cards_policy, prose_policy)
            self.assertEqual(cards_policy, prompts.load_policy_artifact("cards"))
            self.assertEqual(prose_policy, prompts.load_policy_artifact("prose"))
            blob = json.dumps(cards_messages) + json.dumps(prose_messages)
            for leaked in (
                "SENTINEL_LABEL",
                "SENTINEL_CARD",
                "SENTINEL_CLAUSE",
                "SENTINEL_VARIANT",
                "SENTINEL_META",
                "proposed_label",
            ):
                self.assertNotIn(leaked, blob)
            for card in prompts.load_card_documents():
                for text in prompts.card_content_strings(card):
                    self.assertIn(text, cards_policy)
                    self.assertIn(text, prose_policy)


class SchemaTests(unittest.TestCase):
    def test_valid_outputs(self) -> None:
        minimal = {"decision": "allow", "matched_cards": [], "rationale": "ok"}
        parsed, err = judge.parse_judge_output(json.dumps(minimal))
        self.assertIsNone(err)
        self.assertEqual(parsed["decision"], "allow")
        full = {
            "decision": "block",
            "matched_cards": [{"card_id": "secrets", "clause_id": "env-file"}],
            "rationale": "x",
            "risk_score": None,
        }
        parsed, err = judge.parse_judge_output(json.dumps(full))
        self.assertIsNone(err)
        self.assertIsNone(parsed["risk_score"])
        parsed, err = judge.parse_judge_output(
            json.dumps({**minimal, "risk_score": 0})
        )
        self.assertIsNone(err)
        parsed, err = judge.parse_judge_output(
            json.dumps({**minimal, "risk_score": 100})
        )
        self.assertIsNone(err)

    def test_invalid_outputs_are_not_repaired(self) -> None:
        broken = [
            '{"decision": "allow", "matched_cards": [], "rationale": "ok",}',
            '```json\n{"decision":"allow","matched_cards":[],"rationale":"ok"}\n```',
            '{"decision":"allow","matched_cards":[],"rationale":"ok","extra":1}',
            '{"decision":"deny","matched_cards":[],"rationale":"ok"}',
            '{"decision":"allow","matched_cards":[],"rationale":"ok","risk_score":101}',
            '{"decision":"allow","matched_cards":[],"rationale":"ok","risk_score":-1}',
            '{"decision":"allow","matched_cards":[{"card_id":"secrets"}],"rationale":"ok"}',
            '{"decision":"allow","matched_cards":[{"card_id":"secrets","clause_id":"x","note":"y"}],"rationale":"ok"}',
            '["allow"]',
            "allow",
        ]
        for text in broken:
            parsed, err = judge.parse_judge_output(text)
            self.assertIsNone(parsed, text)
            self.assertIsInstance(err, str)

    def test_retry_logs_failure_and_does_not_edit_text(self) -> None:
        bad = '{"decision": "allow",}'
        good = json.dumps({"decision": "escalate", "matched_cards": [{"card_id": "secrets", "clause_id": "x"}], "rationale": "cited"})
        backend = judge.ScriptedJudge([bad, good])
        messages = [{"role": "user", "content": "step"}]
        result = judge.evaluate(backend, messages)
        self.assertTrue(result["parse_ok"])
        self.assertEqual(result["parse_failure_count"], 1)
        self.assertEqual(result["attempt_count"], 2)
        self.assertEqual(result["decision"], "escalate")
        self.assertEqual(result["tokens_in"], 6)
        self.assertEqual(result["tokens_out"], 4)
        self.assertEqual(result["wall_time_ms"], 10)
        self.assertEqual(result["attempts"][0]["raw_output"], bad)
        self.assertEqual(result["attempts"][1]["raw_output"], good)
        self.assertEqual(backend.seen[1][0], messages[0])
        self.assertEqual(backend.seen[1][1]["content"], bad)
        self.assertEqual(backend.seen[1][2]["content"], judge.RETRY_USER)

    def test_two_failures_do_not_invent_a_decision(self) -> None:
        bad = "not json"
        backend = judge.ScriptedJudge([bad, bad])
        result = judge.evaluate(backend, [{"role": "user", "content": "step"}])
        self.assertFalse(result["parse_ok"])
        self.assertIsNone(result["decision"])
        self.assertIsNone(result["rationale"])
        self.assertEqual(result["matched_cards"], [])
        self.assertEqual(result["parse_failure_count"], 2)
        self.assertEqual(result["tokens_in"], 6)
        self.assertEqual(backend.seen[0][0]["content"], "step")
        self.assertEqual(len(backend.seen[0]), 1)


class BackendRequestTests(unittest.TestCase):
    def test_openai_body_carries_schema_and_not_a_key(self) -> None:
        messages = prompts.build_messages("cards", _step())
        body = judge.openai_request_body(
            "demo-model",
            messages,
            judge.DEFAULT_DECODE,
            "json_schema",
            judge.grammar_schema(),
        )
        self.assertEqual(body["model"], "demo-model")
        self.assertEqual(body["messages"][0]["content"], messages[0]["content"])
        self.assertNotIn("api_key", json.dumps(body))
        self.assertEqual(body["response_format"]["type"], "json_schema")
        self.assertNotIn("$schema", body["response_format"]["json_schema"]["schema"])
        prose = prompts.build_messages("prose", _step())
        other = judge.openai_request_body(
            "demo-model",
            prose,
            judge.DEFAULT_DECODE,
            "json_schema",
            judge.grammar_schema(),
        )
        self.assertNotEqual(body["messages"][1]["content"], other["messages"][1]["content"])
        self.assertEqual(
            body["messages"][0]["content"].replace(prompts.ARTIFACT_PHRASE["cards"], "ARTIFACT"),
            other["messages"][0]["content"].replace(prompts.ARTIFACT_PHRASE["prose"], "ARTIFACT"),
        )

    def test_grammar_builds_when_llama_cpp_is_installed(self) -> None:
        try:
            from llama_cpp.llama_grammar import json_schema_to_gbnf
        except ImportError:
            self.skipTest("llama_cpp is not installed")
        grammar = json_schema_to_gbnf(json.dumps(judge.grammar_schema()))
        self.assertIn("decision", grammar)
        self.assertIn("matched_cards", grammar)


class SubsetAndReportTests(unittest.TestCase):
    def test_subset_size_from_probe(self) -> None:
        self.assertEqual(
            smoke_loop.subset_size_from_probe_ms(10_000, n_available=60, budget_ms=2_700_000, minimum=20),
            60,
        )
        self.assertEqual(
            smoke_loop.subset_size_from_probe_ms(60_000, n_available=60, budget_ms=2_700_000, minimum=20),
            22,
        )
        self.assertEqual(
            smoke_loop.subset_size_from_probe_ms(120_000, n_available=60, budget_ms=2_700_000, minimum=20),
            20,
        )
        self.assertEqual(
            smoke_loop.subset_size_from_probe_ms(1_000, n_available=10, budget_ms=2_700_000, minimum=20),
            10,
        )

    def test_permute_is_stable(self) -> None:
        steps = [{"step_id": f"s{i}", "trajectory_id": "t"} for i in range(10)]
        self.assertEqual(
            [row["step_id"] for row in smoke_loop.permute_steps(steps, 20260926)],
            [row["step_id"] for row in smoke_loop.permute_steps(steps, 20260926)],
        )
        self.assertEqual(
            [row["step_id"] for row in smoke_loop.permute_steps(steps, None)],
            [f"s{i}" for i in range(10)],
        )

    def test_mock_log_hides_labels_and_meters(self) -> None:
        rows = smoke_loop.run("cards", [_step()], prompt_version="v1")
        self.assertEqual(rows[0]["judge"], "dry-run-mock")
        self.assertIsNone(rows[0]["tokens_in"])
        self.assertIsNone(rows[0]["wall_time_ms"])
        self.assertEqual(rows[0]["prompt_version"], "v1")
        self.assertNotIn("SENTINEL_LABEL", json.dumps(rows[0]))

    def test_committed_smoke_report_matches_logs(self) -> None:
        report = PILOT / "SMOKE_REPORT.md"
        log_dir = PILOT / "smoke"
        if not report.exists():
            self.skipTest("measured smoke report is not committed yet")
        manifest = json.loads((log_dir / "manifest.json").read_text(encoding="utf-8"))
        cards = summarize_smoke.load_jsonl(log_dir / "smoke_cards.jsonl")
        prose = summarize_smoke.load_jsonl(log_dir / "smoke_prose.jsonl")
        labels = summarize_smoke.load_proposed_labels(PILOT / "data" / "injects" / "candidates.jsonl")
        rendered = summarize_smoke.render_report(manifest, cards, prose, labels)
        self.assertEqual(report.read_text(encoding="utf-8"), rendered)

    def test_calibration_split_is_deterministic(self) -> None:
        import build_calibration

        first = build_calibration.build(
            seed=20260926,
            n_dev=24,
            n_clean=24,
            out_dir=PILOT / "data" / "calibration",
        )
        second = build_calibration.build(
            seed=20260926,
            n_dev=24,
            n_clean=24,
            out_dir=PILOT / "data" / "calibration",
        )
        self.assertEqual(first["dev_step_ids"], second["dev_step_ids"])
        self.assertEqual(first["test_step_ids"], second["test_step_ids"])
        self.assertEqual(first["clean"]["step_ids"], second["clean"]["step_ids"])
        self.assertEqual(len(first["dev_step_ids"]), 24)
        self.assertEqual(len(first["test_step_ids"]), 36)
        # Dev is the prefix of the smoke permutation (same seed/shuffle).
        smoke_manifest = json.loads((PILOT / "smoke" / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(first["dev_step_ids"], smoke_manifest["step_ids"][:24])
        sheet = (PILOT / "labeling" / "sheet.csv").read_text(encoding="utf-8")
        clean_sheet = (PILOT / "labeling" / "sheet_clean.csv").read_text(encoding="utf-8")
        self.assertNotEqual(sheet, clean_sheet)
        self.assertIn("clean-0000", clean_sheet)
        self.assertNotIn("clean-0000", sheet)


if __name__ == "__main__":
    unittest.main()
