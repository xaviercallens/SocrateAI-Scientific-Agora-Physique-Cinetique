# Theory ↔ experiment links

Each row pairs a machine-checked or published statement with a computation or dataset that tests it.
It says what the test found, and what it does not establish. Lean sources come from this project
(`lean4_formalization/`) and from the sibling project SocrateAI-Scientific-QuantumFluids (`lean_src/`,
MIT/Apache-2.0, same author). Built 2026-09-26/27.

| # | Theory | Experiment / data | Result |
|---|---|---|---|
| L1 | **`zero_sound_bracket`** (this project, `ZeroSoundBracket.lean`, new): every undamped zero-sound root has $2e^{-(2+2/F)}\le s-1\le F$. Built on `g3_pos/le/ge` from QuantumFluids `ZeroSound.lean`. | `verification/validate_zero_sound.py`: 60-digit roots of the transcendental dispersion relation at 8 couplings (QV-01) | All 8 roots inside the bracket, now **asserted**. Lower edge **asymptotically sharp**: ratio 1.0000 (F=1/20), 1.0000069 (3/20), 1.0034 (3/10), 1.21 (1), 4.3 (9.3). The "threshold law" QV-01 had only observed is now a proved inequality. |
| L2 | **`zero_sound_iff`** (QuantumFluids): an undamped root exists **iff** F > 0 | QV-01's exact Padé solver: no admissible root at weak coupling | The Padé "negative result" is a **limitation of the method**: the mode provably exists for every F > 0, just exponentially close to the continuum edge (L1). |
| L3 | **`three_phonon_open_iff`**, `symmetric_split_excess` (QuantumFluids `HeliumKinematics.lean`): for ε = ck(1+ak²), three-phonon decay is open iff a ≥ 0 | **Real data**: Godfrin et al. PRB 103, 104516 (2021), ILL IN5 dispersion, 7 pressures, arXiv:2012.09067 ancillary files (`verification/helium_kinematics_data.py`, E5) | SVP, k→0: a = +0.95 ± 0.25 Å² on Q ≤ 0.15 (3.8σ, anomalous, so decay open), consistent with the published α₂ = 1.55, α₃ = −4.04. Narrower ranges are not significant and none contradicts. Model-free split k = 0.30 → 0.15 + 0.15: closed from 5 bar up (≥2.8σ), undecided below. The ~18–20 bar k→0 switch **cannot be decided** from this file (Q ≥ 0.15 for P > 0). |
| L4 | **`plateau_excess_calibration_invariant`** (QuantumFluids): whether an energy exceeds 2Δ cannot be changed by a proportional recalibration | same data, all 7 pressures | The maxon is **below 2Δ up to 10 bar and above it at 24.08 bar** (+0.0106 ± 0.0005 meV, ~21σ), as Beauvois et al. (PRB 97, 184520, 2018) state. By the theorem, no proportional energy recalibration can reverse this. |
| L5 | Docstring claim in `HeliumKinematics.lean`: at SVP the tabulated ε exceeds 2Δ at the top of the measured range | same data, SVP full curve | Confirmed: 1.554 meV at Q = 3.60 Å⁻¹ vs 2Δ = 1.483 meV. |
| L6 | **`klDiv_nonincreasing_to_invariant`** (QuantumFluids `Villani.lean`, from Mathlib's data-processing inequality): discrete H-theorem | `verification/validate_fisher_information_monotonicity.py`: exact Bobylev–Krook–Wu solution of the homogeneous Boltzmann equation | The continuous analogue holds on the exact trajectory: H(f\|M) decreases monotonically 0.028 → 3×10⁻¹¹, alongside Fisher information 3.32 → 3. This is an observed parallel, not a derivation from the Lean theorem. |
| L7 | **Theorem 22.6** of Villani, arXiv:2501.00925 (published, **not** formalised), literal form γ̄ = 2√(d m/M) | `verification/theorem_22_6/` (E1–E4), independent Python/Rust kernels checked against the authors' Julia code | The paper's worked examples reproduce and survive denser sampling (E1–E2). Applied to the Q-RHK-02 model kernel it gives γ̄ = 3.458 (E3). For **d = 4, the range Remark 22.8 leaves open** (γ ∈ (−3, −2√2]), the best heat-kernel comparison gives m/M ≥ 0.996, so γ̄ ≈ 3.99 > \|γ\|: covered with a wide margin, as numerical evidence and not a proof (E4). |

## What the links do not do

- They do not make any statement about real ³He or real rotons that the data do not contain. L1–L2
  concern the one-parameter Landau model, and L3–L5 test kinematic relations, not dynamics.
- The Lean theorems are proved about *model* dispersions and equations. The data only decide which
  side of a proved equivalence ⁴He lies on.
- Theorem 22.6 itself is not formalised anywhere here. L7 is numerical evidence at the same standard
  as the paper's own worked examples.
- One test design was wrong at first and is recorded as such. L3's original version asserted the
  ~18–20 bar switch, which this dataset cannot resolve. It also initially required 2σ on every fit
  range; after the first run that was relaxed to "not contradicted", because a non-significant result
  is not a contradiction.
