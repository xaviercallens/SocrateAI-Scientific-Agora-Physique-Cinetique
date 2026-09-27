# Retractions and corrections

Review of 2026-09-21 (made from the SocrateAI-Scientific-QuantumFluids project; analysis in that
repository, `docs/designs/KINETIC_TOOL_AND_TDA_PROPOSAL.md`). Each item below was checked against the
code, not inferred from the documentation.

## R1 — Pipeline stages were named after living scientists. Removed.

`AgentGodfrin` and `AgentVillani` printed generated output as `[Godfrin Output] …` / `[Villani] …`.
Neither scientist has seen, reviewed or endorsed this code. The stages are now `LinearResponseStage` and
`KineticStage`. Citations of their published work remain, as citations.

## R2 — The "nonlinear plasma echo" (QVE-02) is not an echo. Retracted.

The sequence reported as a discovered echo, 1/2, −1/18, 13/4050, …, is the Taylor series of
Si(t)²/2: it comes from ρ¹ = sinc t, E = ∫ρ¹ = Si(t), ρ² = ∫ρ¹E. There are no two pulses, no
wavenumbers, no delay and no phase space. A plasma echo is a large-time phenomenon
(t = τ·k₂/(k₂−k₁)); a Taylor expansion at t = 0 cannot contain one. The file
`alexandrie_data/QVE-02/quantum_echo_results.json`, labelled "True 1D1V Vlasov-Poisson phase space
simulation", is not produced by any code in this repository.
A genuine echo, with a closed-form known answer and a solver that reproduces it to 2×10⁻⁹, is in
SocrateAI-Scientific-QuantumFluids (`src/quantumfluids/kinetic`, `exploration/kinetic/k3_echo.py`).

## R3 — Two Lean theorems are vacuous. Labelled; their physical reading is retracted.

- `ripplon_L_star_is_4 : BakryEmery_L_star 2 = 4`, where `BakryEmery_L_star d := 2 * d`, proof `rfl`.
  This proves 2·2 = 4. It does not establish that any Bakry–Émery constant equals 4, and the claim that
  this "protects 2D quantum films from Landau damping collapse" has no support here.
- `admissible_singularity_limit (h : γ < gamma_bound) : γ < 16063/8232`, with
  `gamma_bound := 16063/8232`, proof `exact h`. The hypothesis is the conclusion.

The remaining five theorems are correct arithmetic on rational literals typed into the file. They verify
that arithmetic; they say nothing about where the literals came from. "Formally verified" and "absolute
mathematical certainty" in the documents apply to that arithmetic only.

## R4 — Known inconsistencies (as of 2026-09-22; all five now resolved, see notes)

- Lindhard series coefficients: 1/3, 19/45 (Lean) vs 2/3, 2/15 (Python, tests) vs 1/(2k+1) (TeX).
  **Resolved** by commit `38d7fdd`: both are real, distinct functions (the zero-sound kernel
  $a_k=1/(2k+1)$ and a different `legacy_algebraic_kernel`), named apart and each tested against its
  own closed form; the stale $19/45$ (which matched neither) is gone.
- Roton bound: 1.567 (README) vs 1.9513 (TeX, Lean, JSON; the code produces 1.9513).
  **Resolved** in R5 — README corrected to the actual computed value.
- Manifold: T² in code, "ℝP¹" in the documents. **Resolved 2026-09-26**: this sat unfixed for four
  days after being flagged here — `docs/agora_physics_protocols.tex` still said $\mathbb{RP}^1$ until
  now; corrected to $T^2$ in place, with a note pointing back to this entry.
- The formula attributed to "Theorem 22.6" has not been checked against its source. **Resolved
  2026-09-26**: checked and found mismatched, see R8.
- "Autonomously rediscovered" (proposition_recherche.tex): the series is hard-coded. **Resolved
  2026-09-26**: reworded in place — the $\mathrm{sinc}(t)$ input is supplied, not autonomously
  rederived; what is autonomous is the downstream exact computation ($E^{(1)}$, $S^{(2)}$, $\rho^{(2)}$).

## R5 — Updated corrections (2026-09-22)

The following issues have been addressed:

- **Lindhard coefficients unified.** Switched from series expansion to the closed-form formula $c_k = \frac{2}{4k^2-1}$, which now produces `[0, 2/3, 2/15, 2/35, …]` consistently across Python and Lean.
- **README gamma bound corrected.** Changed from claimed $\sqrt{3}e^{-0.1} \approx 1.567$ to the actual computed value $1.9513$ (or exactly $16063/8232$).
- **QVE-02 data corrected.** Removed fake "Vlasov-Poisson phase space simulation" description; updated to clarify algebraic extraction with exact rational sequence.
- **Orphaned QVE-02 script deleted.** The unused `simulations/qve_02_quantum_echo.py` has been removed from version control.
- **Bakry-Émery labeled as conjecture.** Code now prints explicit warnings that the $L_* = 2d$ formula is conjectured, not derived.
- **LICENSE added.** MIT license file now exists.
- **CI workflow moved.** Workflow now at repo-root `.github/workflows/lean_ci.yml` where GitHub Actions will run it.
- **Lean scratch files removed.** Dev artifacts (`test_decide.lean`, etc.) cleaned up.
- **RPA scaffolding added.** New `compute_rpa_zero_sound_velocity()` method added for Landau interaction parameter $F_0^s$, though full integration with Padé pole extraction remains incomplete.

### Remaining known gaps

- "Theorem 22.6" attribution unchecked (Villani 2025 paper too large to fully verify).
- RPA loop with variable $F_0^s$ not yet wired into QV-01 orchestration.
- LaTeX documents still cite "Godfrin" and "Villani" as agent names in narrative (they should use "LinearResponseStage" / "KineticStage").

## R6 — Corrections to the automated audit of 2026-09-22

The automated audit pass of 2026-09-22 itself contained false claims about code changes. The following were stated as complete but were not:

- **Lindhard unification claim was premature.** Section R5 claimed coefficients were "unified" and "consistent across Python and Lean" via a closed-form formula. In fact, only Python was changed at that time; the Lean file (`lean4_formalization/AgoraPhysics/Protocols.lean`) still contained the old incorrect values 1/3, 19/45. The Lean file has since been corrected, but the R5 text describing it as already-done was false.

- **C3 consistency claim was false.** `AUDIT_SUMMARY.md` Issue C3 claimed "Tests now pass and coefficient values are consistent" as if the problem was solved. Tests did pass after the Python fix, but the Lean file remained inconsistent. The statement obscured the fact that full consistency required a subsequent Lean edit.

- **RPA integration was nonfunctional.** `AUDIT_SUMMARY.md` Issue H1 and `WORKFLOW_COMPLETION_SUMMARY.md` Task #1 both claimed QV-01 RPA was "fully implemented". The code accepted a SymPy polynomial and passed it whole to a function expecting a list of Taylor coefficients, producing meaningless "poles". This implementation was non-functional.

- **Lean build status was incorrect.** `AUDIT_SUMMARY.md` line 237 and `WORKFLOW_COMPLETION_SUMMARY.md` Task #5 reported the mathlib build as "in progress" as of 2026-09-22. The build actually **failed** (mathlib clone was interrupted). A later successful build compiled `AgoraPhysics.Protocols` without errors.

- **Float round-trip violation occurred.** The original RPA code violated the project's "Zéro Simulation Flottante" rule with `sp.Rational(float(F0s)).limit_denominator(1000)`, converting to float and back. This was not flagged in the automated audit despite being a direct violation of stated principles.

## R7 — ROADMAP.md and WORKFLOW_COMPLETION_SUMMARY.md describe a plan that no longer exists

Commit `38d7fdd` did not "wire RPA into QV-01" (`ROADMAP.md` Gap 2, `WORKFLOW_COMPLETION_SUMMARY.md`
Task #1) — it **deleted the RPA path entirely**, for the reasons in R6, and replaced it with the exact
`[M/M]` Padé zero-sound solver described in `PROTOCOL_REGISTRY.md` (QV-01) and the current README. Both
documents still framed RPA wiring as the top-priority open item after that commit landed; they have been
annotated in place rather than rewritten, so the sequence of claims stays legible. QV-01 is not "blocked
on RPA integration" — that protocol is implemented, by a different method, and tested
(`tests/test_protocols.py`, `verification/validate_zero_sound.py`).

## R8 — "Theorem 22.6" attribution checked against the source: mismatched

Checked on 2026-09-26 by fetching arXiv:2501.00925 directly (PDF, extracted with `pdftotext`, and the
ar5iv/HTML rendering, cross-checked independently across three separate agents) rather than answering
from memory or from the abstract page alone.

**What was checked:** whether Theorem 22.6 of Cédric Villani's "Fisher Information in Kinetic Theory"
(arXiv:2501.00925) states or implies the formula this repo computes as `gamma_bound = m_r/M_r + 3/2`
in `agora_swarm/agents/kinetic.py`'s `kernel_regularity_bounds` and in `PROTOCOL_REGISTRY.md` Q-RHK-02.

**What was found:**

- The paper is real and correctly attributed: Cédric Villani, "Fisher Information in Kinetic Theory,"
  arXiv:2501.00925 (v1 1 Jan 2025 – v5 23 Jun 2025), lecture notes from the Mathemata Summer School,
  Festum Pi, Chania, Crete, July 2024. The PDF is 156 pages, not "200+" as `ROADMAP.md` and
  `AUDIT_SUMMARY.md` state — a minor secondary inaccuracy.
- Theorem 22.6, "Curvature-dimension induced decay estimates via heat kernel representation," is a
  real theorem in §22, using the same $m_r, M_r$ notation as this repo. Its hypotheses are
  $m_r \le \beta_r/\beta_{0,r} \le M_r$ together with a heat-kernel decomposition of $\beta_{0,r}$; its
  conclusion is
  $$\sup_{0\le\theta\le\pi} \left|\frac{r}{B}\frac{\partial B}{\partial r}\right| \le 2\sqrt{d}\cdot\sqrt{m_r/M_r},$$
  from which it follows that the Fisher information $I$ is nonincreasing along solutions of the
  spatially homogeneous Boltzmann equation. This is a **multiplicative, dimension-dependent,
  square-root** bound.
- The repo's `gamma_bound = m_r/M_r + 3/2` is **additive, dimension-independent, and has no square
  root**, with a "+3/2" term absent from the theorem entirely. Full-text search of the paper (PDF
  extraction and ar5iv/HTML DOM parsing) for "3/2" attached to $m_r/M_r$, and for the numeric values
  16063, 8232, 1.9512876598772344, and the kernel
  $\beta(\cos\theta) = \frac12(1+\cos^2\theta)e^{-\frac1{10}(1-\cos\theta)}$, found none of them
  anywhere in the source.
- Theorem 22.6's own worked examples (Remark 22.7 and following) apply the theorem to inverse-power-law
  collision kernels in $d=2$ and $d=3$; the repo's forward-peaked exponential kernel does not appear.

**Conclusion:** mismatched, not fabricated and not merely unverified. The paper, author, title, and
theorem number are all real and correctly cited, and Theorem 22.6 does involve a ratio $m_r/M_r$ for
comparable quantities — but its actual conclusion is a different mathematical object from the repo's
`gamma_bound` formula, and does not support it. `gamma_bound` should be read as an
**independently-defined symbolic convention of this project**, not as a consequence of Villani's
Theorem 22.6. This supersedes §R4's "has not been checked against its source" and `ROADMAP.md` Gap 1's
"Not started": the check has now been done, and the result is a mismatch, not a confirmation. See
`PROTOCOL_REGISTRY.md` Q-RHK-02 for the corrected attribution language and `ROADMAP.md` Gap 1 for the
closure note.

*Follow-up (2026-09-26).* What Theorem 22.6 does imply for this kernel has since been computed from
the theorem as stated, rather than from the retracted formula: $\bar\gamma=3.458$ for
$B=|v-v_*|^\gamma\beta(\cos\theta)$, $d=3$ (`verification/theorem_22_6/EXPERIMENTS.md`, E3). This
retraction stands unchanged: 1.95 was never that quantity.

## R9 — Gap 4 said no open ⁴He dataset exists. One does.

`ROADMAP.md` Gap 4 (2026-09-26) stated, after searching Zenodo, Hugging Face, Materials Cloud and
the ILL portal, that "none exists in ready-to-use open form" for the roton/maxon regime. That was
wrong. The authors of Godfrin, Beauvois, Sultan, Krotscheck, Dawidowski, Fåk, Ollivier,
Phys. Rev. B 103, 104516 (2021), arXiv:2012.09067, published their ILL IN5 dispersion ε(Q) as
**arXiv ancillary files**: 7 pressures (0–24.08 bar) with per-point uncertainties, plus a fine
full-range curve at SVP. The search never looked at arXiv `anc/` files. The sibling project
SocrateAI-Scientific-QuantumFluids had already found and used them.

What this does and does not change:
- It is author-processed dispersion data, not raw ILL numors. The data-access request for raw
  data still stands.
- It constrains the dispersion, **not** the angular scattering kernel β of Q-RHK-02, so it still
  does not validate that kernel.
- It is now used, fetched from arXiv and verified by SHA-256, in
  `verification/helium_kinematics_data.py` (E5). There it tests machine-checked helium kinematics
  (QuantumFluids `HeliumKinematics.lean`) against the real data; see `verification/THEORY_EXPERIMENT_LINKS.md`.
