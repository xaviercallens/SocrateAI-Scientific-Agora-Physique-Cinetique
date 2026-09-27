# 🏛️ Agora-Physique-Cinetique — exact-rational kinetic physics, checked against proof and data

An open engine that computes kinetic response functions as **exact objects over $\mathbb{Q}$**, proves
what can be proved in **Lean 4**, and confronts its models with **published measurements**. Scientists
and AI coding agents (Claude Code, Google Jules, others) are invited to contribute. The rules for
doing so are in [Contributing](#-contributing-scientists-and-ai-agents) below.

> **Honesty first.** This repository keeps every withdrawn claim in [`RETRACTIONS.md`](RETRACTIONS.md)
> (R1–R9). No result here has been reviewed or endorsed by the scientists whose work is cited.
> Pipeline stages are not named after living people.

| Read | What it is |
|---|---|
| [`docs/agora_engine_paper.pdf`](docs/agora_engine_paper.pdf) | The engine, all results, limits and retractions (16 pp.) |
| [`docs/textbook/agora_textbook.pdf`](docs/textbook/agora_textbook.pdf) | Training guide and textbook for students, with exercises |
| [`notebooks/`](notebooks/) | Executed Jupyter notebooks, from quick start to the large simulation |
| [`docs/MCP.md`](docs/MCP.md) | Local MCP server: the engine as tools for AI agents |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) · [`AGENTS.md`](AGENTS.md) | How humans and agents contribute |

---

## 🌌 The approach

Two failure modes motivate the design:

1. **Semantic hallucination.** A language model can produce fluent mathematics that is wrong and
   looks right.
2. **Discretisation damage.** A continuous kinetic problem pushed through `float64` loses the analytic
   structure (branch points, cancellations) that decides its qualitative behaviour.

The answer is a **ladder of evidence**, where each claim is labelled by the highest rung it reaches:

| Level | Evidence | What it can certify |
|---|---|---|
| 1 | exact symbolic computation over $\mathbb{Q}$ + tests | coefficients, Padé approximants, algebraic roots |
| 2 | independent high-precision / independent-code validation | agreement with the transcendental equations; the same numbers from two languages |
| 3 | Lean 4 + Mathlib, audited with `#print axioms` | the stated mathematics (e.g. the zero-sound bracket), never the physics of a real fluid |
| 4 | comparison with published measurements | whether the *model* describes real helium |

The **"Zéro Simulation Flottante"** rule governs level 1. Taylor coefficients, Cauchy products, Padé
approximants and root extraction are exact. Passing a `float` where a physical parameter belongs raises
`ScientificHonestyException`, and a test asserts that it does. Floating point is allowed only in
verification and simulation code, and it is always checked *against* an exact or
independently computed reference, never the reverse.

## 📊 Results

**QV-01: zero sound, exactly.** The Landau kernel
$\chi(s) = \tfrac{s}{2}\ln\tfrac{s+1}{s-1} - 1 = \sum_{k\ge1} u^k/(2k+1)$, with $u = 1/s^2$, is replaced by its exact
$[M/M]$ Padé approximant. The dispersion relation then becomes a polynomial over $\mathbb{Q}$.
- At $F_0^s = 93/10$ the $[1/1]$ root is $u = 10/37$.
- At $[4/4]$ it agrees with a 60-digit reference to $6.8\times10^{-10}$.
- *Negative result:* at weak coupling no admissible root exists at any order. Instead, **Lean proves**
  that every undamped root satisfies $2e^{-(2+2/F)} \le s-1 \le F$ (`ZeroSoundBracket.lean`).

**QV-01 on real ³He** (level 4). $F_0^s(P)$ and $F_1^s(P)$ are derived from Kollar & Vollhardt, PRB 61,
15347 (2000), Table IX (Greywall's data), read from the arXiv PDF text layer.
- The one-parameter model predicts zero sound *slower* than first sound, which is **wrong**.
- With $F_1^s$ the engine gives $c_0/c_1 = 1.036$ at 0 bar, falling to $1.005$ at 29 bar, in line with
  experiment.
- The exact solver now handles $(F_0^s, F_1^s)$, and agrees with the 60-digit reference to $<10^{-8}$ at $[4/4]$.

**Villani's Theorem 22.6** (arXiv:2501.00925), the numerical worked examples. They are reproduced three
ways: the authors' Julia code, and independent Python and Rust implementations.
- Minimum bound 4.355 in $d=3$ (the paper claims $\ge 4.3$), and 3.364 in $d=2$ (the paper claims $>3.3$).
- The case $d=4$, $\gamma\in(-3,-2\sqrt2]$, which Remark 22.8 leaves open, gets $m/M \ge 0.996$ and
  $\bar\gamma \approx 3.99 > |\gamma|$. This is numerical evidence, not a proof.
- Applied literally to this project's model roton kernel, the theorem gives $\bar\gamma = 3.458$.
  See [`verification/theorem_22_6/EXPERIMENTS.md`](verification/theorem_22_6/EXPERIMENTS.md).

**⁴He kinematics on open neutron data** (Godfrin et al. 2021, arXiv:2012.09067 ancillary IN5 files,
SHA-256 checked). The maxon rises above $2\Delta$ at 24 bar (+0.0106 ± 0.0005 meV, about 21σ), tested
against machine-checked lemmas.

**QVE-02** is an exact second-order Volterra response. It is the Taylor series of $\mathrm{Si}(t)^2/2$,
*not* a plasma echo (R2). Lean proves that its input $\mathrm{sinc}(t)$ is the free-transport
phase-mixing mode of a flat-top distribution, decaying like $1/t$ (`PhaseMixingLink.lean`).

**Large simulation.** A particle (DSMC) simulation of the homogeneous Boltzmann equation is certified
by the exact Bobylev–Krook–Wu solution. The error against the exact moments shrinks like $N^{-1/2}$.
See `simulations/large_scale/` and
[`notebooks/04_large_simulation_dsmc_vs_exact_bkw.ipynb`](notebooks/04_large_simulation_dsmc_vs_exact_bkw.ipynb).

The full theory ↔ experiment map is [`verification/THEORY_EXPERIMENT_LINKS.md`](verification/THEORY_EXPERIMENT_LINKS.md).

## 🚀 Quick start

```bash
pip install -r requirements.txt
scripts/restart.sh check                        # status + fast health check (~2 min); 'help' for modes
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1        # avoids unrelated global pytest plugins
python3 -m pytest tests/ -q                     # exact checks, incl. float refusal

python3 simulations/qv_01_zero_sound.py         # exact derivations -> alexandrie_data/
python3 verification/validate_zero_sound.py     # 60-digit validation + Lean bracket asserted
python3 verification/he3_landau/extract_table_ix.py      # real 3He parameters (fetches arXiv PDF)
python3 verification/he3_landau/zero_sound_real_he3.py   # c0 vs c1 on real 3He
python3 verification/helium_kinematics_data.py           # 4He IN5 data vs Lean lemmas
python3 verification/theorem_22_6/reproduce.py           # Theorem 22.6 worked examples (Python)
(cd verification/theorem_22_6/rust && cargo run --release)   # same, in Rust
python3 simulations/large_scale/dsmc_bkw.py --quick      # large simulation, CI-sized

jupyter lab notebooks/                           # guided tour
cd lean4_formalization && lake exe cache get && lake build   # proofs (library target)
```

**For AI agents on the same machine**, `python3 -m agora_mcp` starts a stdio MCP server that exposes
the engine as tools: exact zero-sound roots, Padé approximants, ³He parameters, Theorem 22.6 bounds
and whitelisted verifications. Claude Code picks it up from [`.mcp.json`](.mcp.json). For other
clients, see [`docs/MCP.md`](docs/MCP.md).

## 🤝 Contributing: scientists and AI agents

Contributions of four kinds are welcome, each with its own issue form:

| You want to… | Open | Label |
|---|---|---|
| request a **numeric or symbolic calculation** (a root at new parameters, a bound for a new kernel, a data comparison) | *Numeric calculation request* | `numeric-request` |
| propose a **roadmap change** (new protocol, dataset, proof target) | *Roadmap proposal* | `roadmap` |
| report a **scientific error** or ask for a **retraction** | *Scientific error / retraction* | `retraction` |
| report a software bug | *Bug* | `bug` |

Issues that are specified well enough for an autonomous agent carry the `agent-ready` label. Claude Code
(yours or anyone's) and Google Jules can pick them up. Agents follow [`AGENTS.md`](AGENTS.md):
- no floats in derivations;
- no numbers from memory; every value is computed or fetched with provenance;
- no claim above the evidence level actually reached;
- retracted claims must never be re-introduced;
- every PR states the level of each new claim.

Humans follow the same rules. Details are in [`CONTRIBUTING.md`](CONTRIBUTING.md).

The roadmap is a living document. Accepted proposals get an ID in the *Live roadmap* section at the top
of [`ROADMAP.md`](ROADMAP.md) and are closed by a PR that cites it.

**Open requests to the community:**
- the ILL-DATA identifiers for the IN5 runs behind PRB 97, 184520 and PRB 103, 104516;
- a licence on the Theorem 22.6 reference code, so it can be reused rather than only run;
- independent checks of the $d=4$ computation.

## 📄 Documents

* [`docs/agora_engine_paper.pdf`](docs/agora_engine_paper.pdf) — the main write-up.
* [`docs/textbook/agora_textbook.pdf`](docs/textbook/agora_textbook.pdf) — textbook and training guide.
* [`RETRACTIONS.md`](RETRACTIONS.md) — every withdrawn claim, including an automated audit's claims about its own work.
* [`PROTOCOL_REGISTRY.md`](PROTOCOL_REGISTRY.md) — protocol definitions and status.
* [`ROADMAP.md`](ROADMAP.md) — live roadmap plus the historical gap record.
* Older papers kept as annotated history: [`docs/proposition_recherche.pdf`](docs/proposition_recherche.pdf),
  [`docs/agora_physics_protocols.pdf`](docs/agora_physics_protocols.pdf).

Generated artefacts are in [`alexandrie_data/`](alexandrie_data/). Large raw simulation output is
not committed; the scripts regenerate it.

## 📚 Citing

See [`CITATION.cff`](CITATION.cff). Please also cite the primary sources the results rest on:
- Villani, arXiv:2501.00925;
- Kollar & Vollhardt, PRB 61, 15347;
- Greywall, PRB 27, 2747;
- Godfrin et al., PRB 103, 104516.

## 📜 License

MIT — see [`LICENSE`](LICENSE). Third-party data is fetched from its source at run time and is not
redistributed.
