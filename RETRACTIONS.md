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

## R4 — Known inconsistencies, not yet resolved

- Lindhard series coefficients: 1/3, 19/45 (Lean) vs 2/3, 2/15 (Python, tests) vs 1/(2k+1) (TeX).
- Roton bound: 1.567 (README) vs 1.9513 (TeX, Lean, JSON; the code produces 1.9513).
- Manifold: T² in code, "ℝP¹" in the documents.
- The formula attributed to "Theorem 22.6" has not been checked against its source.
- "Autonomously rediscovered" (proposition_recherche.tex): the series is hard-coded.

## Not done here, for the owner to decide

No LICENSE file exists (the README says "open source"). The CI workflow sits in
`lean4_formalization/.github/`, where GitHub does not run it.
