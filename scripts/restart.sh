#!/usr/bin/env bash
# Quick restart for humans and AI agents: where the project stands, and a fast health check.
#
#   scripts/restart.sh            status: git, toolchains, CI, open PRs/issues, live roadmap
#   scripts/restart.sh check      status + fast checks (~2 min): pytest, 60-digit QV-01, DSMC --quick
#   scripts/restart.sh full       status + everything CI runs, plus lake build (network for data fetches)
#   scripts/restart.sh mcp        start the local MCP server on stdio (python3 -m agora_mcp)
#   scripts/restart.sh notebooks  start Jupyter on notebooks/ (uses $AGORA_VENV if set)
#   eval "$(scripts/restart.sh env)"   export the environment into the current shell
#
# Machine-specific settings live OUTSIDE the repo in ~/.config/agora/restart.env (optional), e.g.
#   AGORA_DATA_DIR=/big/disk/agora-data         # raw simulation output, fetched datasets
#   CARGO_TARGET_DIR=/big/disk/cargo-target/agora
#   AGORA_VENV=/big/disk/venvs/agora-nb         # venv with jupyter/nbclient, if system pip is locked
#   AGORA_GH_ENV_FILE=~/.gh_workflow_token      # file that exports GH_TOKEN (needs 'workflow' scope to push CI changes)
# Secrets are never printed: the token file is only sourced, and only its presence is reported.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
LOCAL_ENV="${AGORA_RESTART_ENV:-$HOME/.config/agora/restart.env}"
# shellcheck disable=SC1090
[ -f "$LOCAL_ENV" ] && set -a && . "$LOCAL_ENV" && set +a
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1   # unrelated global pytest plugins can break collection
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
PY="${AGORA_PYTHON:-python3}"
MODE="${1:-status}"

if [ -t 1 ]; then B=$'\e[1m'; G=$'\e[32m'; R=$'\e[31m'; Y=$'\e[33m'; N=$'\e[0m'; else B= G= R= Y= N=; fi
hdr()  { printf '\n%s== %s ==%s\n' "$B" "$1" "$N"; }
ok()   { printf '  %s✓%s %s\n' "$G" "$N" "$1"; }
bad()  { printf '  %s✗%s %s\n' "$R" "$N" "$1"; FAILED=$((FAILED+1)); }
note() { printf '  %s•%s %s\n' "$Y" "$N" "$1"; }
FAILED=0

gh_auth() {  # use the workflow-scoped token if configured, without echoing it
  if [ -n "${AGORA_GH_ENV_FILE:-}" ] && [ -f "${AGORA_GH_ENV_FILE/#\~/$HOME}" ]; then
    set -a; . "${AGORA_GH_ENV_FILE/#\~/$HOME}" >/dev/null 2>&1; set +a
  fi
}

run() {  # run <label> <cmd...>: quiet on success, tail of output on failure
  local label="$1"; shift
  local t0=$SECONDS out
  if out="$("$@" 2>&1)"; then ok "$label ($((SECONDS-t0)) s)"
  else bad "$label ($((SECONDS-t0)) s)"; printf '%s\n' "$out" | tail -15 | sed 's/^/      /'; fi
}

status() {
  hdr "Repository"
  note "$(git log -1 --format='%h %s' 2>/dev/null)"
  note "branch $(git rev-parse --abbrev-ref HEAD) — $(git status -sb | head -1 | sed 's/^## //')"
  local dirty; dirty=$(git status --porcelain | wc -l)
  [ "$dirty" -eq 0 ] && ok "working tree clean" || note "$dirty uncommitted change(s): git status"
  note "latest tag $(git describe --tags --abbrev=0 2>/dev/null || echo none)"

  hdr "Toolchains"
  "$PY" -c 'import sympy, mpmath, numpy, scipy' 2>/dev/null && ok "python deps ($("$PY" --version 2>&1))" \
    || bad "python deps missing: pip install -r requirements.txt"
  "$PY" -c 'import mcp.server.fastmcp' 2>/dev/null && ok "mcp (1.x, for agora_mcp)" || note "mcp<2 not installed (MCP server/tests skipped)"
  command -v lake  >/dev/null && ok "lean/lake ($(cat lean4_formalization/lean-toolchain))" || note "lake not on PATH (Lean proofs)"
  command -v julia >/dev/null && ok "julia $(julia --version 2>/dev/null | awk '{print $3}')" || note "julia not on PATH (authors' Theorem 22.6 code)"
  command -v cargo >/dev/null && ok "cargo $(cargo --version | awk '{print $2}')" || note "cargo not on PATH (Rust implementation)"
  command -v pdflatex >/dev/null && ok "pdflatex" || note "pdflatex not on PATH (papers, textbook)"
  [ -n "${AGORA_VENV:-}" ] && { [ -x "$AGORA_VENV/bin/python" ] && ok "notebook venv $AGORA_VENV" || bad "AGORA_VENV set but missing: $AGORA_VENV"; }
  [ -n "${AGORA_DATA_DIR:-}" ] && { [ -d "$AGORA_DATA_DIR" ] && ok "data dir $AGORA_DATA_DIR ($(df -h --output=avail "$AGORA_DATA_DIR" | tail -1 | tr -d ' ') free)" || bad "data dir missing (disk not mounted?): $AGORA_DATA_DIR"; }
  note "root disk: $(df -h --output=pcent / | tail -1 | tr -d ' ') used"

  hdr "GitHub"
  if command -v gh >/dev/null; then
    gh_auth
    if gh auth status >/dev/null 2>&1; then
      ok "gh authenticated$([ -n "${GH_TOKEN:-}" ] && echo ' (GH_TOKEN from AGORA_GH_ENV_FILE)')"
      gh run list -L 4 --json workflowName,conclusion,status,headBranch \
        -q '.[]|"  • CI \(.workflowName) [\(.headBranch)]: \(.conclusion // .status)"' 2>/dev/null
      local prs issues
      prs=$(gh pr list --json number,title -q '.[]|"#\(.number) \(.title)"' 2>/dev/null)
      issues=$(gh issue list -L 10 --json number,title,labels -q '.[]|"#\(.number) \(.title) [\([.labels[].name]|join(","))]"' 2>/dev/null)
      [ -n "$prs" ] && printf '%s\n' "$prs" | sed 's/^/  • PR /' || note "no open PRs"
      [ -n "$issues" ] && printf '%s\n' "$issues" | sed 's/^/  • issue /' || note "no open issues"
    else note "gh not authenticated (status of CI/issues unavailable)"; fi
  fi

  hdr "Live roadmap (ROADMAP.md)"
  awk '/^\| RM-/{split($0,c,"|"); gsub(/^ +| +$/,"",c[2]); gsub(/^ +| +$/,"",c[5]); t=c[3]; gsub(/^ +| +$/,"",t);
       if (length(t)>70) t=substr(t,1,67)"..."; printf "  • %s %s — %s\n", c[2], t, c[5]}' ROADMAP.md
  hdr "Before changing anything"
  note "read AGENTS.md (rules) and RETRACTIONS.md (R1–R9: claims never to re-introduce)"
}

quick_checks() {
  hdr "Fast checks"
  run "pytest (exact engine, MCP, simulation tests)" "$PY" -m pytest tests/ -q
  run "QV-01 60-digit validation + Lean bracket" "$PY" verification/validate_zero_sound.py
  # write to a temp file, not the committed summary, so a health check never dirties the tree
  local tmp; tmp=$(mktemp --suffix=.json)
  run "large simulation, CI-sized (DSMC vs exact BKW)" "$PY" simulations/large_scale/dsmc_bkw.py --quick --no-figures --summary "$tmp"
  rm -f "$tmp"
}

full_checks() {
  quick_checks
  hdr "Full CI set"
  run "Q-RHK-02 independent check"        "$PY" verification/validate_kernel_regularity_bounds.py
  run "Fisher information / H-theorem"    "$PY" verification/validate_fisher_information_monotonicity.py
  run "Theorem 22.6 reproduction"         "$PY" verification/theorem_22_6/reproduce.py
  run "4He IN5 data vs Lean lemmas (net)" "$PY" verification/helium_kinematics_data.py
  run "3He Table IX extraction (net)"     "$PY" verification/he3_landau/extract_table_ix.py
  run "zero sound on real 3He"            "$PY" verification/he3_landau/zero_sound_real_he3.py
  run "3He exact Pade pressure sweep"     "$PY" simulations/large_scale/he3_pressure_sweep.py
  if command -v lake >/dev/null; then
    hdr "Lean"
    local log; log=$(mktemp)
    if (cd lean4_formalization && lake build >"$log" 2>&1); then
      if grep -q "declaration uses 'sorry'\|sorryAx" "$log"; then bad "lake build: sorry/sorryAx present"
      else ok "lake build clean, $(grep -c 'depends on axioms' "$log") axiom audits without sorryAx"; fi
    else bad "lake build failed"; tail -15 "$log" | sed 's/^/      /'; fi
    rm -f "$log"
  fi
}

case "$MODE" in
  status)    status ;;
  check)     status; quick_checks ;;
  full)      status; full_checks ;;
  mcp)       exec "$PY" -m agora_mcp ;;
  notebooks) J="${AGORA_VENV:+$AGORA_VENV/bin/}jupyter"; exec "$J" lab notebooks/ ;;
  env)       printf 'export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1\nexport PYTHONPATH=%q\nexport PATH=%q\n' "$PYTHONPATH" "$PATH"
             for v in AGORA_DATA_DIR CARGO_TARGET_DIR AGORA_VENV AGORA_GH_ENV_FILE; do
               [ -n "${!v:-}" ] && printf 'export %s=%q\n' "$v" "${!v}"; done
             [ -n "${AGORA_GH_ENV_FILE:-}" ] && printf 'set -a; . %q >/dev/null 2>&1; set +a\n' "${AGORA_GH_ENV_FILE/#\~/$HOME}"
             exit 0 ;;
  -h|--help|help) sed -n '2,19p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
  *) echo "unknown mode '$MODE' (status|check|full|mcp|notebooks|env|help)"; exit 2 ;;
esac

hdr "Summary"
[ "$FAILED" -eq 0 ] && ok "all good" || { bad "$FAILED problem(s) above"; exit 1; }
