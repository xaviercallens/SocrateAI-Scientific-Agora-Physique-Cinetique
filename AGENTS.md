# AGENTS.md — instructions for AI coding agents

This file is read by Google Jules, Claude Code (through `CLAUDE.md`), Codex, Gemini CLI and similar
agents. Humans should follow it too. The project's value is that its claims can be trusted, so these
rules outrank speed.

## Setup and checks

`scripts/restart.sh` shows where the project stands (git, toolchains, CI, open issues, live roadmap);
`scripts/restart.sh check` adds the fast checks (~2 min), and `full` runs everything CI runs plus `lake build`.

```bash
pip install -r requirements.txt
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
python3 -m pytest tests/ -q                      # must stay green
python3 verification/validate_zero_sound.py      # 60-digit validation
python3 simulations/large_scale/dsmc_bkw.py --quick
cd lean4_formalization && lake exe cache get && lake build   # only if you touched .lean files
```

A PR is ready when pytest is green, every script listed in `.github/workflows/python_tests.yml`
still runs, and `lake build` is clean for any Lean change.

## Hard rules

1. **No floats in derivations.** Code in `agora_swarm/` works over ℚ (sympy `Rational`, exact
   algebraic numbers). Physical parameters that arrive as `float` must raise
   `ScientificHonestyException`. Floating point is allowed in `verification/`, `simulations/` and
   `notebooks/`, and only to check something against an exact or independent reference.
2. **No numbers from memory.** Every physical constant, table value or literature result is either
   computed here or fetched from a named source, with the fetch in code (URL, and a SHA-256 where
   possible). Never type a measured value from recall. If you cannot get the source, say so in the PR.
3. **Label the evidence level.** Every new claim in docs, docstrings or papers says which level it
   reaches (1 exact computation, 2 independent validation, 3 Lean proof, 4 comparison with data;
   see `README.md`). Numerical evidence is never called a proof. A Lean theorem certifies mathematics,
   not the physics of real helium.
4. **Respect retractions.** Read `RETRACTIONS.md` first. Never re-introduce a retracted claim: the
   "plasma echo" (R2), person-named agents (R1), `gamma_bound` as Villani's Theorem 22.6 (R8), and
   the rest. When a claim is withdrawn, grep the *whole* repo (code, orchestrator prints, persisted
   JSON, Lean names and comments, LaTeX) and fix every occurrence.
5. **Lean proofs have no `sorry`.** Check with `#print axioms`: only `propext`, `Classical.choice` and
   `Quot.sound` are allowed. Grepping for `sorry` is not enough.
6. **Negative results are results.** If a method fails, for example no admissible root at weak
   coupling, document and test the failure. Do not paper over it.
7. **Attribution.** Do not name pipeline stages after living scientists, and do not state or imply
   endorsement by cited authors. Do not copy unlicensed third-party code; run it at a pinned commit
   instead (see `verification/theorem_22_6/run.sh`).
8. **Secrets.** Never commit, print or log API keys. Keys live in environment variables or in
   `~/.config/agora/*.env`.
9. **Big data stays out of git.** Raw simulation output and downloaded datasets go to a cache
   directory. Commit only small JSON summaries under `alexandrie_data/` and figures.

## Picking up work

- Take issues labelled `agent-ready`. Each one states inputs, expected outputs and acceptance
  criteria. If an issue is ambiguous, comment with the question instead of guessing.
- For a `numeric-request`, add a script or test that computes the result reproducibly, write the
  output under `alexandrie_data/`, and put the key numbers with their evidence level in the PR.
- For a `roadmap` item, cite its ID from the *Live roadmap* section of `ROADMAP.md` in the PR, and
  update its status there.
- Keep PRs small and focused, with one issue per PR where possible.

## Where things are

| Path | Contents |
|---|---|
| `agora_swarm/agents/` | exact engine: `linear_response.py` (kernels), `kinetic.py` (Padé, roots, bounds) |
| `simulations/` | protocol runs; `large_scale/` holds the DSMC vs exact BKW simulation and sweeps |
| `verification/` | independent checks, data comparisons, Theorem 22.6 (Python/Rust/Julia) |
| `lean4_formalization/AgoraPhysics/` | Lean 4 proofs (Mathlib) |
| `agora_mcp/` | local MCP server exposing the engine as tools (`python3 -m agora_mcp`) |
| `notebooks/` | executed tutorials |
| `docs/` | engine paper, textbook, older papers (annotated history) |
| `alexandrie_data/` | small committed result files |

## PR description template

State what changed, the evidence level of each new claim, the commands you ran and their results,
and any retraction affected. The PR template in `.github/` prompts for these.
