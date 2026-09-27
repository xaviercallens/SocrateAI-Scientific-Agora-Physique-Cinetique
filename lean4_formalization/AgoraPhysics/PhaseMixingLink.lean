/-
  PhaseMixingLink.lean -- what QVE-02's input ρ⁽¹⁾(t) = sin t / t actually is.

  RETRACTIONS.md R2 retracted the "plasma echo" reading of QVE-02. This file states, and proves,
  the correct reading of its linear input.

  CONTEXT. SocrateAI-Scientific-QuantumFluids, `lean_src/PhaseMixing.lean` (same author,
  MIT/Apache-2.0), treats free transport ∂ₜf + v ∂ₓf = 0, whose k-th density mode is
  ∫ e^{-ikvt} g(v) dv. It proves that mode tends to 0 for every g (`phase_mixing`,
  Riemann-Lebesgue), and that for the Maxwellian it is exactly e^{-k²t²/2} (`maxwellian_mode`).

  NEW HERE.
  * `flat_top_mode`: for the flat-top distribution g = ½·𝟙[-1,1] (even, so the mode is the
    cosine integral), the density mode is exactly sin(kt)/(kt). At k = 1 this is QVE-02's
    ρ⁽¹⁾(t). By Archimedes' hat-box theorem, the 1D marginal of the uniform measure on the sphere
    S² is this flat top, so ρ⁽¹⁾ is also the mode of a uniform Fermi-surface distribution.
  * `flat_top_mode_tendsto_zero`: that mode decays to 0, like 1/t: algebraic phase mixing, not the
    Gaussian decay of the Maxwellian.

  Scope: linear free streaming, no field, no collisions. It says nothing about the O(ε²) Volterra
  term of QVE-02 beyond identifying the input it is built from.
-/
import Mathlib

open Real Filter Topology intervalIntegral

namespace AgoraPhysics.PhaseMixingLink

/-- **The flat-top density mode.** `(1/2) ∫_{-1}^{1} cos(a v) dv = sin a / a` for `a ≠ 0`; with
`a = k t` this is the `k`-th free-transport density mode of `g = ½·𝟙[-1,1]` at time `t`. -/
theorem flat_top_mode {a : ℝ} (ha : a ≠ 0) :
    (∫ v in (-1 : ℝ)..1, cos (a * v)) / 2 = sin a / a := by
  rw [intervalIntegral.integral_comp_mul_left (fun x => cos x) ha, integral_cos]
  simp only [mul_neg, mul_one, sin_neg, smul_eq_mul]
  field_simp
  ring

/-- **QVE-02's input is that mode at k = 1.** -/
theorem qve02_input_is_flat_top_mode {t : ℝ} (ht : t ≠ 0) :
    (∫ v in (-1 : ℝ)..1, cos (t * v)) / 2 = sin t / t :=
  flat_top_mode ht

/-- **Phase mixing for the flat top.** `sin t / t → 0` as `t → ∞`, bounded by `1/t`. -/
theorem flat_top_mode_tendsto_zero : Tendsto (fun t : ℝ => sin t / t) atTop (𝓝 0) := by
  have hinv : Tendsto (fun t : ℝ => t⁻¹) atTop (𝓝 0) := tendsto_inv_atTop_zero
  have hbound : ∀ᶠ t : ℝ in atTop, ‖sin t / t‖ ≤ t⁻¹ := by
    filter_upwards [eventually_gt_atTop 0] with t ht
    rw [Real.norm_eq_abs, abs_div, abs_of_pos ht, div_eq_mul_inv]
    exact mul_le_of_le_one_left (inv_nonneg.mpr ht.le) (abs_sin_le_one t)
  exact squeeze_zero_norm' hbound hinv

end AgoraPhysics.PhaseMixingLink

#print axioms AgoraPhysics.PhaseMixingLink.flat_top_mode
#print axioms AgoraPhysics.PhaseMixingLink.qve02_input_is_flat_top_mode
#print axioms AgoraPhysics.PhaseMixingLink.flat_top_mode_tendsto_zero
