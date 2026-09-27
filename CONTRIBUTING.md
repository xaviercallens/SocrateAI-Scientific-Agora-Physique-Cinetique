# Contributing

Physicists, mathematicians, students and AI agents are welcome. The rules in [`AGENTS.md`](AGENTS.md)
apply to everyone. This page covers the process.

## Ways to contribute

### 1. Request a calculation (`numeric-request`)
Use the **Numeric calculation request** issue form. Good requests are precise:
- the exact inputs, as rationals where possible, e.g. `F0s = 1028/100, F1s = 526/100`;
- the quantity wanted, e.g. the zero-sound root at Padé order 6, or the Theorem 22.6 bound for a
  new kernel;
- the precision or evidence level needed;
- the source of any physical input.

A maintainer or an agent answers with a script or test, a result file under `alexandrie_data/`, and
a PR. Requests that are fully specified get the `agent-ready` label.

### 2. Propose a roadmap change (`roadmap`)
Use the **Roadmap proposal** form: a new protocol, a dataset to confront, a theorem to formalise, or
a method to replace. Say what would count as success *and* what would count as a negative result.
Accepted proposals get an ID (`RM-nn`) in the *Live roadmap* section of [`ROADMAP.md`](ROADMAP.md).

### 3. Report a scientific error (`retraction`)
If a claim here is wrong, overstated or mis-attributed, use the **Scientific error / retraction**
form. This is the most valuable contribution. Confirmed errors are recorded in
[`RETRACTIONS.md`](RETRACTIONS.md) with credit, and fixed everywhere the claim appears.

### 4. Code, proofs, data
Fork, branch, and open a PR against `main`:
- **Code:** exact arithmetic in `agora_swarm/`; tests for every behaviour, including failures.
- **Lean:** Mathlib, no `sorry`, audited with `#print axioms`; say which statement is certified.
- **Data:** fetch from the original source in code, verify a checksum, cite the paper, and do not
  redistribute third-party files.
- **Docs and papers:** label evidence levels; the papers are LaTeX in `docs/`, rebuilt with pdflatex.

## AI agents

Agents are first-class contributors under the same rules.
- **Claude Code** reads `CLAUDE.md`, which imports `AGENTS.md`, and gets the local MCP server from
  `.mcp.json`.
- **Google Jules** reads `AGENTS.md` and works in its own cloud VM. It uses the scripts and tests
  directly; the local MCP server is for agents running on the same machine.
- Others: point them at `AGENTS.md`.

Agent PRs must say they were agent-authored and name the tool, for example with a `Co-Authored-By`
trailer. A human maintainer merges.

## Review checklist

- [ ] `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/ -q` is green.
- [ ] The CI verification scripts still run.
- [ ] Each new claim carries its evidence level; nothing numerical is called a proof.
- [ ] No floats in `agora_swarm/` derivations; no numbers typed from memory.
- [ ] No retracted claim re-introduced (`RETRACTIONS.md`).
- [ ] Lean: `lake build` is clean, and `#print axioms` shows no `sorryAx`.

## Conduct

Be precise and kind. Criticism of claims is welcome and expected; criticism of people is not.
