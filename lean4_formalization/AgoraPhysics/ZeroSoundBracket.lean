/-
  ZeroSoundBracket.lean -- a machine-checked bracket for the zero-sound root, linking the
  QV-01 experiments of this project to real-analysis theorems.

  PROVENANCE. `g3` and the three lemmas `g3_pos`, `g3_le`, `g3_ge` are taken from
  SocrateAI-Scientific-QuantumFluids, `lean_src/ZeroSound.lean` (commit c91d1b3, MIT/Apache-2.0,
  same author), where they support `zero_sound_iff`: in 3D an undamped zero-sound root `s > 1` of
  `g3 s = 1/F` exists iff `F > 0`. They are restated here because the two projects pin different
  Lean/Mathlib versions.

  NEW HERE. `zero_sound_bracket`: at any undamped root,
      2 exp(-(2 + 2/F)) ≤ s - 1 ≤ F.
  The lower edge is exactly the weak-coupling threshold law `s - 1 ≃ 2 e^{-2-2/F}` that this
  project's QV-01 validation observed numerically (verification/validate_zero_sound.py). With this
  theorem it becomes a proved inequality. The experiments, in turn, show it is asymptotically sharp:
  the measured ratio (s-1) / (2 e^{-2-2/F}) tends to 1 as F -> 0. The validation script now asserts
  the bracket at every reference root it computes.

  This is real analysis over ℝ (log, exp), not only arithmetic over ℚ. It concerns the Landau
  kinetic model with one parameter F = F₀ˢ, not measured ³He data.
-/
import Mathlib

open Real

namespace AgoraPhysics.ZeroSoundBracket

/-- `g3(s) = (s/2) log((s+1)/(s-1)) - 1`: the Landau zero-sound kernel χ(s) of QV-01.
The 3D dispersion relation is `g3 s = 1/F`. -/
noncomputable def g3 (s : ℝ) : ℝ := s / 2 * log ((s + 1) / (s - 1)) - 1

/-- (QuantumFluids, `ZeroSound.lean`) -/
theorem g3_pos {s : ℝ} (hs : 1 < s) : 0 < g3 s := by
  have h1 : 0 < s - 1 := by linarith
  have hx : 0 < 2 / (s - 1) := by positivity
  have h := lt_log_one_add_of_pos hx
  have e1 : 1 + 2 / (s - 1) = (s + 1) / (s - 1) := by field_simp; ring
  have e2 : 2 * (2 / (s - 1)) / (2 / (s - 1) + 2) = 2 / s := by field_simp; ring
  rw [e1, e2] at h
  unfold g3
  have : s / 2 * (2 / s) < s / 2 * log ((s + 1) / (s - 1)) :=
    mul_lt_mul_of_pos_left h (by linarith)
  have e3 : s / 2 * (2 / s) = 1 := by field_simp
  linarith

/-- (QuantumFluids, `ZeroSound.lean`) -/
theorem g3_le {s : ℝ} (hs : 1 < s) : g3 s ≤ 1 / (s - 1) := by
  have h1 : 0 < s - 1 := by linarith
  have hy : 0 < (s + 1) / (s - 1) := by positivity
  have h := log_le_sub_one_of_pos hy
  have e1 : (s + 1) / (s - 1) - 1 = 2 / (s - 1) := by field_simp; ring
  rw [e1] at h
  unfold g3
  have : s / 2 * log ((s + 1) / (s - 1)) ≤ s / 2 * (2 / (s - 1)) :=
    mul_le_mul_of_nonneg_left h (by linarith)
  have e2 : s / 2 * (2 / (s - 1)) - 1 = 1 / (s - 1) := by field_simp; ring
  linarith

/-- (QuantumFluids, `ZeroSound.lean`) -/
theorem g3_ge {s : ℝ} (hs : 1 < s) : 1 / 2 * log (2 / (s - 1)) - 1 ≤ g3 s := by
  have h1 : 0 < s - 1 := by linarith
  have hmono : log (2 / (s - 1)) ≤ log ((s + 1) / (s - 1)) :=
    log_le_log (div_pos two_pos h1) (by gcongr; linarith)
  have hnn : 0 ≤ log ((s + 1) / (s - 1)) :=
    log_nonneg (by rw [le_div_iff₀ h1]; linarith)
  unfold g3
  nlinarith

/-- **Upper edge.** At an undamped root, `s - 1 ≤ F`. -/
theorem root_upper {F s : ℝ} (hF : 0 < F) (hs : 1 < s) (hroot : g3 s = 1 / F) : s - 1 ≤ F := by
  have h1 : 0 < s - 1 := by linarith
  have h := g3_le hs
  rw [hroot] at h
  exact (one_div_le_one_div hF h1).mp h

/-- **Lower edge.** At an undamped root, `2 exp(-(2 + 2/F)) ≤ s - 1`: the weak-coupling
threshold law, as a proved inequality. (`F > 0` is not needed: `g3_pos` rules out a root for
`F < 0`, and `1/0 = 0` rules it out for `F = 0`.) -/
theorem root_lower {F s : ℝ} (hs : 1 < s) (hroot : g3 s = 1 / F) :
    2 * exp (-(2 + 2 / F)) ≤ s - 1 := by
  have h1 : 0 < s - 1 := by linarith
  have h := g3_ge hs
  rw [hroot] at h
  have hlog : log (2 / (s - 1)) ≤ 2 + 2 / F := by
    have : 1 / 2 * log (2 / (s - 1)) ≤ 1 / F + 1 := by linarith
    have e : 2 / F = 2 * (1 / F) := by ring
    rw [e]; linarith
  have hle : 2 / (s - 1) ≤ exp (2 + 2 / F) :=
    (log_le_iff_le_exp (div_pos two_pos h1)).mp hlog
  have hmul : 2 ≤ exp (2 + 2 / F) * (s - 1) := (div_le_iff₀ h1).mp hle
  rw [exp_neg]
  have hpos := exp_pos (2 + 2 / F)
  rw [← div_eq_mul_inv, div_le_iff₀ hpos]
  linarith

/-- **The bracket.** Every undamped zero-sound root of the 3D Landau model with `F > 0` satisfies
`2 exp(-(2 + 2/F)) ≤ s - 1 ≤ F`. Combined with `zero_sound_iff` (QuantumFluids), such a root
exists for every `F > 0`, so QV-01's Padé "no admissible root" at weak coupling is a limitation
of the method, not an absence of the mode. -/
theorem zero_sound_bracket {F s : ℝ} (hF : 0 < F) (hs : 1 < s) (hroot : g3 s = 1 / F) :
    2 * exp (-(2 + 2 / F)) ≤ s - 1 ∧ s - 1 ≤ F :=
  ⟨root_lower hs hroot, root_upper hF hs hroot⟩

end AgoraPhysics.ZeroSoundBracket

#print axioms AgoraPhysics.ZeroSoundBracket.g3_pos
#print axioms AgoraPhysics.ZeroSoundBracket.g3_le
#print axioms AgoraPhysics.ZeroSoundBracket.g3_ge
#print axioms AgoraPhysics.ZeroSoundBracket.root_upper
#print axioms AgoraPhysics.ZeroSoundBracket.root_lower
#print axioms AgoraPhysics.ZeroSoundBracket.zero_sound_bracket
