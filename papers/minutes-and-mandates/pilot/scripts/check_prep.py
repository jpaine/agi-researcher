#!/usr/bin/env python3
"""Local and CI check for Gate A prep.

Runs unit tests, validates the committed Nebius sample, regenerates the
inject candidates and labeling sheet, and dry-runs the mock smoke loop.
No network. No gold labels. No token or time measurements.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
PILOT = SCRIPTS.parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_calibration  # noqa: E402
import generate_injects  # noqa: E402
import labeling  # noqa: E402
import nebius  # noqa: E402
from step_format import load_jsonl, sha256_text  # noqa: E402


def run_unit_tests() -> None:
    suite = unittest.defaultTestLoader.discover(
        str(PILOT / "tests"),
        pattern="test_*.py",
        top_level_dir=str(PILOT / "tests"),
    )
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():
        raise SystemExit("unit tests failed")


def check_committed_outputs() -> None:
    steps_path = PILOT / "data" / "trajectories" / "nebius_sample.jsonl"
    manifest_path = PILOT / "data" / "trajectories" / "manifest.json"
    nebius.validate_sample(steps_path, manifest_path)

    templates = generate_injects.load_templates(generate_injects.TEMPLATES)
    generate_injects.validate_templates(templates, generate_injects.load_clauses(generate_injects.CARDS))
    steps = generate_injects.load_jsonl(steps_path)
    rows, manifest = generate_injects.build_candidates(
        steps,
        templates,
        seed=generate_injects.DEFAULT_SEED,
        per_kind=generate_injects.DEFAULT_PER_KIND,
    )
    manifest["source_steps_sha256"] = sha256_text(steps_path.read_text(encoding="utf-8"))
    body = generate_injects.dump_jsonl(rows)
    committed = (PILOT / "data" / "injects" / "candidates.jsonl").read_text(encoding="utf-8")
    if body != committed:
        raise SystemExit("candidates.jsonl does not match a fresh generation; re-run generate_injects.py")
    fresh_manifest = dict(manifest)
    fresh_manifest["candidates_sha256"] = sha256_text(body)

    on_disk = json.loads((PILOT / "data" / "injects" / "manifest.json").read_text(encoding="utf-8"))
    if on_disk != fresh_manifest:
        raise SystemExit("inject manifest does not match a fresh generation")

    committed_sheet = (PILOT / "labeling" / "sheet.csv").read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        sheet = Path(tmp) / "sheet.csv"
        labeling.export_sheet(rows, sheet)
        if sheet.read_text(encoding="utf-8") != committed_sheet:
            raise SystemExit("labeling/sheet.csv does not match export of the candidates")
        report = labeling.agreement_report(labeling.read_sheet(PILOT / "labeling" / "sheet.csv"))
        if report["n_both_labeled"] != 0:
            raise SystemExit("committed labeling sheet should still be blank; do not commit gold or pass labels")

    cal_dir = PILOT / "data" / "calibration"
    if not (cal_dir / "manifest.json").exists():
        raise SystemExit("missing data/calibration/manifest.json; run build_calibration.py")

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "calibration"
        built = build_calibration.build(out_dir=out)
        committed_cal = json.loads((cal_dir / "manifest.json").read_text(encoding="utf-8"))
        for key in (
            "dev_step_ids",
            "test_step_ids",
            "seed",
            "n_dev",
            "n_test",
            "candidates_sha256",
            "nebius_steps_sha256",
        ):
            if built[key] != committed_cal[key]:
                raise SystemExit(f"calibration manifest field {key} does not match a fresh build")
        if built["clean"]["step_ids"] != committed_cal["clean"]["step_ids"]:
            raise SystemExit("calibration clean step_ids do not match a fresh build")
        for name in (
            "dev_injects.jsonl",
            "test_injects.jsonl",
            "clean_steps.jsonl",
            "dev_steps.jsonl",
            "test_steps.jsonl",
        ):
            if (out / name).read_text(encoding="utf-8") != (cal_dir / name).read_text(encoding="utf-8"):
                raise SystemExit(f"calibration file {name} does not match a fresh build")
        clean_sheet = PILOT / "labeling" / "sheet_clean.csv"
        labeling.export_sheet(load_jsonl(cal_dir / "clean_steps.jsonl"), Path(tmp) / "sheet_clean.csv")
        if (Path(tmp) / "sheet_clean.csv").read_text(encoding="utf-8") != clean_sheet.read_text(encoding="utf-8"):
            raise SystemExit("labeling/sheet_clean.csv does not match export of clean_steps.jsonl")
        clean_report = labeling.agreement_report(labeling.read_sheet(clean_sheet))
        if clean_report["n_both_labeled"] != 0:
            raise SystemExit("committed sheet_clean.csv should still be blank")
        if (PILOT / "labeling" / "sheet.csv").read_text(encoding="utf-8") != committed_sheet:
            raise SystemExit("calibration tooling must not alter labeling/sheet.csv")


def run_smoke() -> None:
    smoke = SCRIPTS / "smoke_loop.py"
    subprocess.check_call([sys.executable, str(smoke)])
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.check_call(
            [
                sys.executable,
                str(smoke),
                "--steps",
                str(PILOT / "data" / "injects" / "candidates.jsonl"),
                "--log-dir",
                tmp,
            ]
        )


def main() -> int:
    run_unit_tests()
    check_committed_outputs()
    run_smoke()
    print("prep checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
