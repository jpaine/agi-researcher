#!/usr/bin/env bash
# Thin helpers for using AstroPilot-AI/Denario from this workspace.
# Requires Python 3.12+ and LLM API keys (see root README).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DENARIO_SRC="${ROOT}/vendor/denario"

usage() {
  cat <<'EOF'
Usage: scripts/denario.sh <command> [args...]

Commands:
  check       Verify the Denario submodule is present
  install     Create .venv (if needed) and pip install -e vendor/denario[app]
  gui         Run the Denario GUI (denario run)
  python      Run python with the workspace venv activated
  help        Show this help

Examples:
  ./scripts/denario.sh check
  ./scripts/denario.sh install
  ./scripts/denario.sh gui

Or use Denario from Python after install:

  source .venv/bin/activate
  python -c "from denario import Denario, Journal; print(Journal.NeurIPS)"

Point project_dir at papers/<slug>/ for each paper run. See papers/README.md
and brainstorm/idea-brief.template.md.
EOF
}

ensure_submodule() {
  if [[ ! -f "${DENARIO_SRC}/pyproject.toml" ]]; then
    echo "Denario submodule missing at ${DENARIO_SRC}" >&2
    echo "Run: git submodule update --init --recursive" >&2
    exit 1
  fi
}

cmd_check() {
  ensure_submodule
  echo "OK: Denario at ${DENARIO_SRC}"
  if [[ -d "${DENARIO_SRC}/.git" ]] || [[ -f "${DENARIO_SRC}/.git" ]]; then
    git -C "${DENARIO_SRC}" rev-parse --short HEAD
    # Prefer the committed .gitmodules URL (no credentials)
    if git -C "${ROOT}" config -f "${ROOT}/.gitmodules" --get submodule.vendor/denario.url 2>/dev/null; then
      :
    else
      git -C "${DENARIO_SRC}" remote get-url origin
    fi
  fi
}

cmd_install() {
  ensure_submodule
  if [[ ! -d "${ROOT}/.venv" ]]; then
    python3 -m venv "${ROOT}/.venv"
  fi
  # shellcheck disable=SC1091
  source "${ROOT}/.venv/bin/activate"
  python -m pip install -U pip
  pip install -e "${DENARIO_SRC}[app]"
  echo "Installed editable Denario from ${DENARIO_SRC}"
  echo "Activate with: source .venv/bin/activate"
}

cmd_gui() {
  ensure_submodule
  if [[ ! -d "${ROOT}/.venv" ]]; then
    echo "No .venv found. Run: ./scripts/denario.sh install" >&2
    exit 1
  fi
  # shellcheck disable=SC1091
  source "${ROOT}/.venv/bin/activate"
  exec denario run "$@"
}

cmd_python() {
  if [[ ! -d "${ROOT}/.venv" ]]; then
    echo "No .venv found. Run: ./scripts/denario.sh install" >&2
    exit 1
  fi
  # shellcheck disable=SC1091
  source "${ROOT}/.venv/bin/activate"
  exec python "$@"
}

main() {
  local cmd="${1:-help}"
  shift || true
  case "${cmd}" in
    check) cmd_check "$@" ;;
    install) cmd_install "$@" ;;
    gui) cmd_gui "$@" ;;
    python) cmd_python "$@" ;;
    help|-h|--help) usage ;;
    *)
      echo "Unknown command: ${cmd}" >&2
      usage >&2
      exit 1
      ;;
  esac
}

main "$@"
