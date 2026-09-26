#!/usr/bin/env python3
"""Minimal Denario critique loop for papers/minutes-and-mandates.

Locks the idea (working title + claim + Angle 1), then asks Denario for a
methodology draft. Does NOT call get_results or get_paper.

Pinned models (keys into denario.models / vendor/denario/denario/llm.py):
  Flagship chat / method generator : gpt-5
  Reasoning / review / format       : o3-mini
  Fast-mode single LLM             : gpt-5  (not gemini-2.0-flash)

Do not put API keys in the repo. Set them in the environment only.

Required environment (see Denario docs):
  OPENAI_API_KEY          required for the pinned OpenAI models above
  GOOGLE_API_KEY          optional (only if you override --llm to a Gemini id)
  ANTHROPIC_API_KEY       optional
  PERPLEXITY_API_KEY      optional (literature)
  FUTURE_HOUSE_API_KEY    optional

  https://denario.readthedocs.io/en/latest/llm_api_keys/apikeys/

Usage (from repo root, Denario installed):
  python3 papers/minutes-and-mandates/run_denario_loop.py
  python3 papers/minutes-and-mandates/run_denario_loop.py --mode cmbagent
  python3 papers/minutes-and-mandates/run_denario_loop.py --dry-run
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
REPO_ROOT = PROJECT_DIR.parents[1]
DATA_DESCRIPTION = PROJECT_DIR / "data_description.md"
CONSTRAINTS = PROJECT_DIR / "constraints.md"
IDEA_LOCKED = PROJECT_DIR / "idea_locked.md"
INPUT_FILES = PROJECT_DIR / "input_files"
CRITIQUE_PROMPT = PROJECT_DIR / "prompts" / "critique_pass.md"

# Newest OpenAI ids registered in vendor/denario/denario/llm.py (as of submodule pin).
MODEL_FLAGSHIP = "gpt-5"
MODEL_REASONING = "o3-mini"

# Env vars Denario commonly expects (presence checked; values never printed).
ENV_VARS = (
    "OPENAI_API_KEY",
    "GOOGLE_API_KEY",
    "ANTHROPIC_API_KEY",
    "PERPLEXITY_API_KEY",
    "FUTURE_HOUSE_API_KEY",
    "GOOGLE_APPLICATION_CREDENTIALS",
)


def _read(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"Missing required file: {path}")
    return path.read_text(encoding="utf-8")


def _print_env_status() -> dict[str, bool]:
    status = {name: bool(os.environ.get(name)) for name in ENV_VARS}
    print("Environment key status (True = set, value hidden):")
    for name, present in status.items():
        print(f"  {name}: {present}")
    return status


def _ensure_vendor_on_path() -> None:
    """Allow running against the git submodule without a prior pip install."""
    vendor = REPO_ROOT / "vendor" / "denario"
    if vendor.is_dir():
        sys.path.insert(0, str(vendor))


def build_data_description() -> str:
    """Combine data_description.md with constraints.md for set_data_description."""
    body = _read(DATA_DESCRIPTION).rstrip()
    constraints = _read(CONSTRAINTS).rstrip()
    return (
        f"{body}\n\n"
        f"---\n\n"
        f"# Binding constraints (from constraints.md)\n\n"
        f"{constraints}\n"
    )


def build_locked_idea() -> str:
    return _read(IDEA_LOCKED).rstrip() + "\n"


def dry_run() -> int:
    desc = build_data_description()
    idea = build_locked_idea()
    INPUT_FILES.mkdir(parents=True, exist_ok=True)
    desc_out = INPUT_FILES / "data_description.md"
    idea_out = INPUT_FILES / "idea.md"
    desc_out.write_text(desc, encoding="utf-8")
    idea_out.write_text(idea, encoding="utf-8")
    print("Dry run — wrote locked inputs only (no Denario LLM calls):")
    print(f"  {desc_out}")
    print(f"  {idea_out}")
    print(f"Pinned models (unused in dry-run): flagship={MODEL_FLAGSHIP}, reasoning={MODEL_REASONING}")
    print(f"Critique prompt (manual second pass): {CRITIQUE_PROMPT}")
    return 0


def run(mode: str, llm: str) -> int:
    status = _print_env_status()
    # Pinned defaults are OpenAI; require OPENAI_API_KEY unless user overrode to a non-OpenAI id.
    needs_openai = llm.startswith("gpt-") or llm.startswith("o3") or mode == "cmbagent"
    if needs_openai and not status.get("OPENAI_API_KEY"):
        print(
            "\nOPENAI_API_KEY is not set. Pinned Denario models "
            f"({MODEL_FLAGSHIP} / {MODEL_REASONING}) need it.\n"
            "Refusing to call Denario. Re-run with keys set, or use --dry-run.\n",
            file=sys.stderr,
        )
        return 2

    _ensure_vendor_on_path()
    try:
        from denario import Denario, models
    except ImportError as exc:
        print(
            "Could not import denario. Install with:\n"
            "  ./scripts/denario.sh install\n"
            "or: pip install -e 'vendor/denario[app]'\n",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc

    for key in {llm, MODEL_FLAGSHIP, MODEL_REASONING}:
        if key not in models:
            print(
                f"Model id {key!r} is not in denario.models. "
                f"Available: {sorted(models.keys())}",
                file=sys.stderr,
            )
            return 1

    desc = build_data_description()
    idea = build_locked_idea()

    # clear_project_dir=False so we keep prompts/ and tracked markdown.
    den = Denario(project_dir=str(PROJECT_DIR), clear_project_dir=False)

    print("Setting data description (description + constraints)...")
    den.set_data_description(desc)

    # Prefer set_idea with the locked spine so get_idea cannot violate the lock.
    print("Setting locked idea (title + claim + Angle 1); skipping get_idea()...")
    den.set_idea(idea)

    print(
        f"Generating methodology with Denario.get_method(mode={mode!r}) "
        f"using flagship={MODEL_FLAGSHIP}, reasoning={MODEL_REASONING}, fast_llm={llm}..."
    )
    if mode == "fast":
        den.get_method(mode="fast", llm=llm)
    else:
        den.get_method(
            mode="cmbagent",
            method_generator_model=MODEL_FLAGSHIP,
            planner_model=MODEL_FLAGSHIP,
            plan_reviewer_model=MODEL_REASONING,
            orchestration_model=MODEL_FLAGSHIP,
            formatter_model=MODEL_REASONING,
        )

    idea_path = INPUT_FILES / "idea.md"
    methods_path = INPUT_FILES / "methods.md"
    desc_path = INPUT_FILES / "data_description.md"

    print("\nDone. Draft outputs (critique these; claim stays locked):")
    for path in (desc_path, idea_path, methods_path):
        exists = path.is_file()
        print(f"  {'OK' if exists else 'MISSING'}: {path}")

    print(f"\nNext: second-pass critique using\n  {CRITIQUE_PROMPT}")
    print("Do NOT run get_paper / get_results until go/no-go allows.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("fast", "cmbagent"),
        default="fast",
        help="Denario get_method mode (default: fast with pinned gpt-5)",
    )
    parser.add_argument(
        "--llm",
        default=MODEL_FLAGSHIP,
        help=f"Fast-mode LLM id in denario.models (default: {MODEL_FLAGSHIP})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Write locked data_description/idea into input_files/ without LLM calls",
    )
    args = parser.parse_args()

    if args.dry_run:
        _print_env_status()
        return dry_run()
    return run(args.mode, args.llm)


if __name__ == "__main__":
    raise SystemExit(main())
