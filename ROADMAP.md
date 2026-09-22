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

### Gap 1: Theorem 22.6 Attribution Unchecked

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

### Gap 2: RPA Loop Not Yet Integrated into QV-01 Orchestration

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

### Gap 3: LaTeX Documents Still Cite Agent Names

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
| 1 | Theorem 22.6 verification | Medium | Large | No | Not started | TBD |
| 2 | RPA integration into QV-01 | High | Medium | Yes (QV-01) | Scaffolded | Task #1 |
| 3 | LaTeX agent name rewrite | Medium | Small | No | Deferred | Task #2 |

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
