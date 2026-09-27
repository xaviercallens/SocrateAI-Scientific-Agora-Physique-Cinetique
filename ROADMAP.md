# Project Roadmap — SocrateAI-Scientific-Agora-Physique-Cinetique

**Audit Date:** 2026-09-22  
**Status:** Post-audit implementation phase  
**See also:** [AUDIT_SUMMARY.md](./AUDIT_SUMMARY.md), [RETRACTIONS.md](./RETRACTIONS.md)

---

## Overview

The comprehensive audit of 2026-09-22 resolved 10 critical and high-severity issues. This roadmap documents the 3 remaining known gaps that require attention before full peer-review readiness.

All gaps are **non-blocking for research continuity**, but addressing them is essential for:
- Academic credibility and reproducibility claims
- Proper attribution to source materials
- Complete implementation of documented methodologies

---

## Known Gaps

### Gap 1: Theorem 22.6 Attribution Unchecked — **CLOSED, see correction below**

> [!IMPORTANT]
> **Correction (2026-09-26, see [RETRACTIONS.md §R8](./RETRACTIONS.md#r8--theorem-226-attribution-checked-against-the-source-mismatched)):**
> This gap is closed, not "Not started." The paper (arXiv:2501.00925, Villani, "Fisher Information in
> Kinetic Theory") was obtained in full (PDF and HTML) and Theorem 22.6 was located, quoted verbatim,
> and compared against the repo's usage. Result: **mismatched**, not merely unverified. The paper,
> author, and theorem number are all correctly cited, and Theorem 22.6 does involve a ratio $m_r/M_r$ —
> but its actual conclusion is the multiplicative, dimension-dependent bound
> $2\sqrt{d}\cdot\sqrt{m_r/M_r}$, used to show Fisher-information monotonicity along the spatially
> homogeneous Boltzmann equation, not the repo's additive $\gamma_{\text{bound}} = m_r/M_r + 3/2$. The
> paper is 156 pages, not "200+" as stated below. See `PROTOCOL_REGISTRY.md` Q-RHK-02 for the corrected
> attribution language. The rest of this section is kept as a historical record of the gap as it was
> understood on 2026-09-22; do not treat it as a live task.

**Reference:** [AUDIT_SUMMARY.md §U1](./AUDIT_SUMMARY.md#u1-theorem-226-attribution-not-verified), [RETRACTIONS.md §R4](./RETRACTIONS.md#r4--known-inconsistencies-not-yet-resolved)

**Why it matters:**  
The roton Fisher Information bounds in the documentation attribute the underlying formula to "Theorem 22.6" in Villani 2025 (arXiv:2501.00925). This citation appears throughout the methodology—in `PROTOCOL_REGISTRY.md`, in docstrings, and in roton-related calculations. Without verification, any peer reviewer will flag this as incomplete attribution. It directly affects the credibility of the Q-RIP-03 roton bound derivation.

**What work is needed:**  
1. Obtain full text of arXiv:2501.00925
2. Locate Section 22+ of the Villani paper
3. Find Theorem 22.6 (or the relevant numbered theorem)
4. Compare the exact statement, hypotheses, and conclusion to our usage
5. Update documentation with precise quote or formal reference if statement differs
6. Note any gaps between Villani's result and our application

**Effort:** **Large** (~6–8 hours)  
- Paper is 200+ pages with dense mathematical notation
- Requires domain expertise in optimal transport / quantum kinetics
- May require cross-referencing lemmas if theorem depends on prior material

**Blocks:** None (research can proceed), but essential for **peer-review credibility** and **publication readiness**

**Acceptance Criteria:**  
- [ ] Villani 2025 full text retrieved and archived in `/docs/references/`
- [ ] Section 22+ read and Theorem 22.6 located
- [ ] Statement and assumptions documented in a new section of `PROTOCOL_REGISTRY.md`
- [ ] Any discrepancies or adaptations noted clearly
- [ ] Updated README or abstract if citation turns out to be different

---

### Gap 2: RPA Loop Not Yet Integrated into QV-01 Orchestration — **OBSOLETE, see correction below**

> [!IMPORTANT]
> **Correction (2026-09-26, see [RETRACTIONS.md §R7](./RETRACTIONS.md#r7--roadmapmd-and-workflow_completion_summarymd-describe-a-plan-that-no-longer-exists)):**
> Commit `38d7fdd` did not complete this gap — it deleted the RPA path entirely (it was
> non-functional and violated the float-free rule; see RETRACTIONS.md §R6) and replaced it with an
> exact `[M/M]` Padé zero-sound solver. QV-01 is implemented and tested by that method, not by RPA.
> The rest of this section is kept as a historical record of the gap as it was understood on
> 2026-09-22; do not treat it as a live task.

**Reference:** [AUDIT_SUMMARY.md §H1 & U2](./AUDIT_SUMMARY.md#issue-h1-qv-01-documentation-describes-rpa-methodology-that-isnt-implemented), [RETRACTIONS.md §R5](./RETRACTIONS.md#r5--updated-corrections-2026-09-22)

**Why it matters:**  
The QV-01 protocol documentation describes a full Random Phase Approximation (RPA) workflow with Landau interaction parameter $F_0^s$, stating:

> "Interacting Response generated via Landau's Fermi-liquid parameters... chi_RPA(z) = chi_0(z) / (1 - F_0^s * chi_0(z)) where F_0^s ≈ 0.1"

The new `LinearResponseStage.compute_rpa_zero_sound_velocity()` method was added in commit 6278d23, but it is **scaffolded but not wired**. The orchestration method `AgentSocrate.execute_protocol_qv_01()` still calls only the bare Lindhard function without invoking the RPA correction. This means:
- Documented methodology does not match implementation
- QV-01 outputs are incomplete (missing Landau correlation)
- Protocol claims to be "Interacting Response" but produces only bare response

**What work is needed:**  
1. Modify `AgentSocrate.execute_protocol_qv_01()` to call `compute_rpa_zero_sound_velocity()`
2. Wire the $F_0^s$ parameter through from configuration (currently hardcoded as 0.1)
3. Integrate Padé pole extraction with RPA-modified response
4. Update test suite: add `test_qv_01_with_rpa_interaction()` to verify output differs from bare Lindhard
5. Document the parameter tuning and physical interpretation
6. Update `PROTOCOL_REGISTRY.md` to mark QV-01 as "fully implemented"

**Effort:** **Medium** (~4–6 hours)  
- Scaffolding already exists; main work is wiring and testing
- Requires understanding of RPA formalism and Padé approximation interaction
- CI and test suite already in place

**Blocks:** **QV-01 experimental deployment** — protocol cannot be considered complete for external use until this is wired

**Acceptance Criteria:**  
- [ ] `AgentSocrate.execute_protocol_qv_01()` calls `compute_rpa_zero_sound_velocity()` when RPA mode is enabled
- [ ] $F_0^s$ parameter configurable (not hardcoded)
- [ ] Padé pole extraction operates on RPA-modified response, not bare Lindhard
- [ ] New test `test_qv_01_with_rpa_interaction()` added and passing
- [ ] Test verifies that RPA output differs from bare Lindhard (by ~5–15% for $F_0^s = 0.1$)
- [ ] `PROTOCOL_REGISTRY.md` updated to mark "QV-01" as "Fully implemented"
- [ ] Commit message references this gap and issue #2

---

### Gap 3: LaTeX Documents Still Cite Agent Names — **DONE**

> [!IMPORTANT]
> **Correction (2026-09-26):** this was completed in commit `e0f2954` (documented in
> `WORKFLOW_COMPLETION_SUMMARY.md` Task #2) but never marked done here. Both `.tex` files now use
> `LinearResponseStage`/`KineticStage` throughout; verified by direct grep, no "Agent Godfrin"/"Agent
> Villani" occurrences remain in either file. The rest of this section is historical record.

**Reference:** [AUDIT_SUMMARY.md §H4 & U3](./AUDIT_SUMMARY.md#issue-h4-latex-documents-still-use-retracted-agent-godfrvinvillani-framing), [RETRACTIONS.md §R1](./RETRACTIONS.md#r1--pipeline-stages-were-named-after-living-scientists-removed)

**Why it matters:**  
`RETRACTIONS.md` §R1 explicitly corrects the use of living scientists' names in the codebase (agent names `AgentGodfrin` and `AgentVillani` were removed "out of respect"). However, the legacy LaTeX documents—`docs/proposition_recherche.tex` and `docs/agora_physics_protocols.tex`—still frame the entire research narrative around "Agent Godfrin" and "Agent Villani" as if they are endorsed software components or collaborators.

This violates the respect principle stated in §R1 and creates a misleading impression that the work has their endorsement or collaboration.

**What work is needed:**  
1. Audit both `.tex` files for all references to "Godfrin" and "Villani" as agent/stage names
2. Replace agent references:
   - `Agent Godfrin` → `LinearResponseStage`
   - `Agent Villani` → `KineticStage`
3. Update narrative framing: change from "Agent X computes" to "The LinearResponseStage computes"
4. Keep all citations of their published work intact (citations are appropriate and correct)
5. Add a preamble or footnote clarifying that the stage names reference the scientists' published methods, not their endorsement
6. Re-render PDFs if applicable; update README with new links

**Effort:** **Small** (~2–3 hours)  
- Largely mechanical text replacement
- Requires careful review to preserve citations while updating framing
- May involve minor rewording for naturalness (e.g., "Agent Villani analyzed…" → "The kinetic analysis, via methods from Villani, determines…")

**Blocks:** Nothing immediate, but affects **documentation consistency** and **publication ethics**

**Acceptance Criteria:**  
- [ ] All instances of "Agent Godfrin" and "Agent Villani" as stage names replaced in both `.tex` files
- [ ] All citations of Villani and Godfrin's published work remain intact
- [ ] Preamble or footnote added clarifying the distinction
- [ ] `docs/` directory updated (PDFs re-generated if applicable)
- [ ] README updated with reference to corrected LaTeX docs and link to §R1
- [ ] Commit message references this gap and issue #3

---

### Gap 4: No empirical validation data for any of the four protocols — plan for institutional data access

**Reference:** `PROTOCOL_REGISTRY.md`'s Dataset Falsification Policy note; this gap makes "pending
institutional data access" concrete.

**Why it matters:** all four protocols' physical inputs are phenomenological or definitional — Q-RHK-02's
kernel and QV-01's $F_0^s = 93/10$ stand-in explicitly "using no measured data" (README); QVE-02's
$\rho^{(1)} = \operatorname{sinc}(t)$ is the free (non-interacting) Fermi-sphere response, not measured
from any real interacting system; Q-RIP-03's $L_*=2d$ is a bare conjecture with no physical input at all.
Closing this gap needs real data or a real numerical check for each, not more symbolic computation.

> [!IMPORTANT]
> **Correction (2026-09-27, see [RETRACTIONS.md §R9](./RETRACTIONS.md)):** the conclusion below that no
> open dataset exists is wrong for ⁴He. Godfrin et al. (2021, PRB 103, 104516) published their IN5
> dispersion at 7 pressures as arXiv ancillary files (arXiv:2012.09067), which this search missed. It
> constrains the dispersion, not the angular kernel β, and it is now used in E5
> (`verification/helium_kinematics_data.py`).

**What was checked (2026-09-26, two passes — QV-01/Q-RHK-02/Villani first, then QVE-02/Q-RIP-03):**
searched Zenodo, Hugging Face Datasets, Materials Cloud, and the ILL data portal for an open, structured
dataset covering all four protocols plus the Villani-side numerical bound. Result: **none exists in
ready-to-use open form for any of them** — this is a field where the real data sits inside papers or
behind an experiment's own DOI, not in a self-serve repository. Specifically:

- **Q-RHK-02 (roton/maxon angular scattering):** the directly relevant real measurement is
  K. Beauvois, J. Dawidowski, B. Fåk, H. Godfrin, E. Krotscheck, J. Ollivier, A. Sultan,
  *"Microscopic dynamics of superfluid $^4$He: a comprehensive study by inelastic neutron scattering"*,
  Phys. Rev. B 97, 184520 (2018), arXiv:1802.08120 — ILL IN5 data, exactly the roton/maxon regime this
  project's kernel is shaped after. No data-availability statement or Zenodo/figshare deposit found.
  ILL assigns a DOI to every proposal's raw numors under `10.5291/ILL-DATA.*` (data.ill.eu) after a
  3–5 year embargo, but even past embargo this needs ILL's own reduction pipeline (LAMP/Mantid), and
  the specific proposal DOI for this run was not found from the paper text alone.
- **QV-01 ($F_0^s$ for liquid $^3$He):** no Zenodo/figshare dataset exists for Landau parameters either
  — the standard source (Greywall's thermodynamic measurements, Phys. Rev. B 1983, and later
  reanalyses) is table-in-a-paper only. Unlike the neutron data, this one does not need a formal
  dataset search: it is a handful of well-known papers with a small (~10–15 point) pressure-dependent
  table that could be transcribed directly.
- **Villani-side numerical benchmark:** no open Boltzmann-equation/DSMC benchmark dataset was found on
  Zenodo or Hugging Face that specifically targets the *spatially homogeneous* Boltzmann equation (the
  setting of Theorem 22.6). One recent candidate, "TransportBench" (arXiv:2606.02997, stated
  MIT-licensed), covers spatially *inhomogeneous* rarefied flows instead — the wrong shape of test —
  and no code/data release could be located regardless.
- **QVE-02 (Fermi-liquid dynamic response):** the real analogues of $\rho^{(1)}=\operatorname{sinc}(t)$
  are measurements of $S(q,\omega)$ for an interacting Fermi liquid at small $q$ — e.g. Godfrin's own
  inelastic-neutron measurements of normal liquid $^3$He, and of a 2D $^3$He monolayer where a
  collective mode reappears past the particle-hole continuum (see Q-RIP-03 entry below, same paper). A
  genuinely new (Sept. 2025) result, arXiv:2509.10741, "Direct Observation of the Lindhard Continuum
  using Resonant Inelastic X-ray Scattering" (MgB$_2$), probes the free-electron-gas Lindhard response
  directly by a different, modern technique — worth checking for a raw-spectra deposit if pursued. None
  of these has an open structured dataset; the classic two-pulse plasma-echo experiments
  (Malmberg–Wharton, PRL 20, 95 (1968), and later Penning-trap successors) are 1960s–1990s vintage with
  no digital data and are relevant only as citable context for what a real echo looks like — this
  project's QVE-02 computation is not that (RETRACTIONS.md R2).
- **Q-RIP-03 (ripplons on He films):** the directly relevant real measurement is H. J. Lauter, H.
  Godfrin, V. L. P. Frank, P. Leiderer, *"Ripplons in $^4$He films observed by neutron scattering"*,
  Phys. Rev. Lett. 68, 2484 (1992) — ripplon dispersion $\omega(k)$ on a graphite-adsorbed $^4$He film,
  exactly this protocol's physical setting. Also directly relevant (2D Fermi liquid, not $^4$He): H.
  Godfrin, M. Meschke, H.-J. Lauter, A. Sultan, H. M. Böhm, E. Krotscheck, M. Panholzer, *"Observation
  of a roton collective mode in a two-dimensional Fermi liquid"*, Nature 483, 576 (2012) — a $^3$He
  monolayer. Both confirmed real; both predate open-data conventions and have no accessible
  data-availability statement or deposit (the Nature page is paywalled with no arXiv preprint found).

**Recommended next step — this is a data-access request, not a download:**
1. For Q-RHK-02 and Q-RIP-03: contact H. Godfrin directly (or via ILL), citing PRB 97, 184520 (2018),
   PRL 68, 2484 (1992), and/or Nature 483, 576 (2012) by proposal number, and ask for either the
   post-embargo `ILL-DATA` DOI for the relevant run, or the digitized data tables behind those papers'
   figures.
2. For QV-01: transcribe $F_0^s(P)$ from Greywall (1983) and later reanalyses directly — no external
   dataset search needed.
3. For QVE-02: if a quantitative check is wanted rather than qualitative context, check whether
   arXiv:2509.10741's RIXS data has a raw-spectra deposit.
4. For the Villani-side bound: rather than searching for a pre-made benchmark, numerically solve the
   spatially homogeneous Boltzmann equation for Theorem 22.6's own worked examples (inverse-power-law
   kernels, $d=2,3$) with an existing open solver, and compare against the paper's stated bounds
   directly.

**Acceptance Criteria:**
- [ ] Data-access email drafted and sent to Godfrin/ILL citing the specific proposals
- [ ] Greywall $F_0^s(P)$ table transcribed into a structured file in this repo
- [x] A numerical (not dataset-based) check of Theorem 22.6's own worked examples (inverse-power-law
      kernels, $d=2,3$, their heat-kernel decomposition and $m_r,M_r$ construction) — **done
      2026-09-26**: `verification/theorem_22_6/run.sh`. The paper (§22, after Remark 22.7) says these
      bounds were obtained numerically by L. Silvestre, published in Imbert–Silvestre–Villani,
      arXiv:2409.01183, with code at `github.com/luissilvestre/collisionkernel` (the paper's ref.
      [160]). That code was re-executed here at pinned commit `01a9d44` (not vendored — the upstream
      repository has no LICENSE). Results: $d=3$, $\gamma\in(-3,-2]$, tuned weight
      $1-\min(\tfrac{13}{8}-\tfrac34\nu,\tfrac25)(1-e^{-2t})$: minimum $2\sqrt{\Lambda_b\,c_2/C_1} = 4.357$
      (paper claims $\ge 4.3$); $d=2$, $\nu\in[1,2)$, weight $1+2(\nu-1)^2(1-e^{-2t})$: minimum $3.363$
      (paper claims $>3.3$); plain fractional-Laplacian ratio $M/m = 1.572$ at $d=3,\nu=1$ (paper:
      "approaches 1.6"). Both claims reproduce, and agree with the upstream notebooks' saved outputs
      to 2 decimals. Scope: this confirms the *cited paper's* numerics; it says nothing new about this
      project's own $\gamma_{\text{bound}}$, which R8 already establishes is a different object — the
      two numbers (≈4.36 vs 1.95) must not be compared
- [x] **Independent Python and Rust implementations** of the same computation, so the check no
      longer depends on Julia or on unlicensed code — 2026-09-26. `verification/theorem_22_6/kernels.py`
      and `rust/` are written from the mathematics, not translated from the authors' code (which has no
      licence): collision kernel from classical scattering, parametrised by $\beta=p^2/r_0^2$ with the
      deflection derivative taken under the integral (reproduces the Rutherford cross-section to
      $10^{-12}$ in $d=2,3$); subordinate kernel from the spherical heat-kernel expansion with each
      $t$-integral an exact incomplete gamma function; both normalised by their exact $\theta\to0$
      constants; $\Lambda_b$ in closed form. Against the authors' code (`reference_julia.json`, from
      `gen_reference.jl`): collision kernel within $2\times10^{-6}$ (their finite-difference derivative),
      subordinate kernel within $0.7\%$ (theirs bump-averaged, ours pointwise). Both claims reproduce:
      $d=3$ minimum $4.355\ge4.3$, $d=2$ minimum $3.364>3.3$. Rust vs Python: $\le2\times10^{-9}$.
      One finding about the authors' numerics: their adaptive quadrature of the $\Lambda_b$ integrals
      underestimates $\Lambda_b$ as $\nu\to2$ (at $d=2$, $\nu=1.999$: $3.932$ vs exact $3.997$, confirmed
      by a singularity-resolving substitution to 12 digits), because the integrand tends to $t^{-1}$.
      The error is conservative — their tabulated bounds are slightly *lower* than the true ones — so
      neither claim is affected
- [x] **Experiments E1–E3** (`verification/theorem_22_6/EXPERIMENTS.md`) — 2026-09-26.
      E1: both claims survive 52 ν values × 400 angles (d=3 min 4.3544, d=2 min 3.3593 at ν≈1.06,
      a dip between the paper's sampled ν). E2: the paper's hand-tuned weights are within 0.06 of the
      best in their family; without tuning both claims fail. E3: Theorem 22.6 as stated, applied to
      this project's Q-RHK-02 model kernel, gives $\bar\gamma=3.458$. E4 (2026-09-27): in d=4, over the
      range the notes' Remark 22.8 leaves open, the literal criterion gives $\bar\gamma\approx3.99>|\gamma|$
      (m/M ≥ 0.996, needed ≤ 0.5625). This is numerical evidence to offer the authors, not a proof
- [x] Independent numerical cross-check of Q-RHK-02's own exact quantities ($m_r$, $M_r$,
      $\Sigma(\beta)$, $\gamma_{\text{bound}}$) added: `verification/validate_kernel_regularity_bounds.py`
      (golden-section search, mpmath quadrature, Monte Carlo integration, and a rejection-sampling
      simulation of the scattering angle) — 2026-09-26, all pass to $<10^{-9}$ relative error
- [x] Numerical simulation of the general physical principle behind the Villani citation (Fisher
      information monotonicity for the homogeneous Boltzmann equation) added:
      `verification/validate_fisher_information_monotonicity.py`, using the exact Bobylev–Krook–Wu mode
      for Maxwell molecules — 2026-09-26, passes (mass conserved exactly, Maxwellian limit matches the
      known closed form $I=3$ exactly, monotonic decrease observed over the full trajectory). This is
      **not** a test of Theorem 22.6 itself — see the script's docstring for exact scope
- [ ] This gap's status updated once real data lands (the numerical items above are all done; only the
      empirical-data items — Godfrin/ILL request, Greywall transcription — remain open)

---

## Work Priority and Dependencies

### Priority Ranking

1. **Gap 2 (RPA Integration)** — High priority  
   - Blocks QV-01 protocol completion
   - Medium effort with clear acceptance criteria
   - Unblocks experimental deployment

2. **Gap 3 (LaTeX Rewrite)** — Medium priority  
   - Affects publication ethics and documentation consistency
   - Small effort; can be done in parallel with other work
   - No blockers; straightforward text replacement

3. **Gap 1 (Theorem 22.6 Verification)** — Lower priority (but essential before submission)  
   - Large effort; requires external resource (Villani paper)
   - Non-blocking for development but critical for peer review
   - Should be completed before final manuscript submission

### Recommended Execution Order

1. Complete **Gap 2** to unblock QV-01 deployment
2. Parallelize **Gap 3** (can be assigned to different contributor)
3. Schedule **Gap 1** after Villani 2025 is published and available in full form

---

## Work Status Summary

| Gap | Issue | Priority | Effort | Blocker | Status | Owner |
|-----|-------|----------|--------|---------|--------|-------|
| 1 | Theorem 22.6 verification | Medium | Large | No | **Closed — checked, mismatched, see R8** | — |
| 2 | RPA integration into QV-01 | ~~High~~ | ~~Medium~~ | No | **Obsolete — RPA replaced by exact solver in 38d7fdd, see R7** | — |
| 3 | LaTeX agent name rewrite | Medium | Small | No | **Done — commit e0f2954** | Task #2 |
| 4 | Empirical validation data access | Medium | Large (institutional) | No | **Checked — no open dataset exists; data-access request drafted as next step** | — |

---

## Implementation Roadmap

### Phase 1: Complete RPA Integration (Task #1)
- **Effort:** 1 sprint (~1 week)
- **Owner:** TBD
- **Deliverables:**
  - Wired QV-01 with RPA loop
  - Passing test suite
  - Updated PROTOCOL_REGISTRY.md
  - Commit to main with full traceability

### Phase 2: Rewrite LaTeX Documentation (Task #2)
- **Effort:** 1–2 days (~4–6 hours)
- **Owner:** TBD
- **Deliverables:**
  - Updated `.tex` files with neutral stage names
  - Re-rendered PDFs (if applicable)
  - Updated README
  - Commit to main

### Phase 3: Verify Theorem 22.6 (Task #3, after arXiv availability)
- **Effort:** 2–3 days (~6–8 hours)
- **Owner:** TBD (preferably physicist with optimal transport background)
- **Deliverables:**
  - Reference document with full Villani §22.6 text
  - Verification memo comparing to our usage
  - Updated PROTOCOL_REGISTRY.md if corrections needed
  - Commit to main

---

## Relevant Links and References

- **Audit findings:** [AUDIT_SUMMARY.md](./AUDIT_SUMMARY.md)
- **Retractions & corrections:** [RETRACTIONS.md](./RETRACTIONS.md)
- **Protocol registry:** [PROTOCOL_REGISTRY.md](./PROTOCOL_REGISTRY.md)
- **Original QV-01 design:** `agora_swarm/protocols.py` (see `LinearResponseStage`, `KineticStage`, `AgentSocrate.execute_protocol_qv_01()`)
- **Lean formalization:** `lean4_formalization/AgoraPhysics/Protocols.lean`
- **LaTeX documents:** `docs/proposition_recherche.tex`, `docs/agora_physics_protocols.tex`

---

## Notes for Contributors

1. **Respect principle**: When implementing Gap 3, remember that scientist names in the code/docs now refer to their published methods, not the people themselves. Use neutral language.

2. **Testing discipline**: Gaps 1 and 2 both affect methodology claims. Ensure that all changes include:
   - Updated unit tests
   - Documentation of expected behavior
   - Commit message traceability to this roadmap

3. **Citation accuracy**: For Gap 1, when Villani 2025 becomes available, archive the full PDF in `docs/references/` with a dated note. Do not paraphrase; quote exactly.

4. **Cross-document consistency**: Updates to any of these gaps should trigger a re-read of:
   - `PROTOCOL_REGISTRY.md` (protocol descriptions)
   - `README.md` (high-level claims)
   - Relevant docstrings in `protocols.py` and `.lean` files

---

## Related Issues and Pull Requests

- Task #1: RPA orchestration integration
- Task #2: LaTeX rewrite (agent names)
- Task #3: Theorem 22.6 verification (to be created when arXiv 2501.00925 is available)

---

**Last Updated:** 2026-09-22  
**Next Review:** Upon completion of Phase 1 or Phase 2 (whichever completes first)
