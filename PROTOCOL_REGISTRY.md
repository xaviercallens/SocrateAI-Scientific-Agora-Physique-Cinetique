# Protocol Registry

This document catalogs the formalized, automated scientific protocols used by the agents within the SocrateAI Scientific Agora.

## Protocol QV-01: The Quantum Vlasov Zero-Sound Simulation
**Lead Agent**: Godfrin
**Domain**: Quantum Fluids / Plasma Physics

**Objective**: 
Extract the continuous Taylor sequence of the Random Phase Approximation (RPA) density response in $^3$He and use rational Padé approximants to detect the Zero-Sound wave velocity and the Landau Damping threshold.

**Methodology**:
1. Evaluate the Continuous Base Response (Lindhard function) using an exact infinite rational series expansion.
2. Interacting Response generated via Landau's Fermi-liquid parameters.
3. Compute Diagonal $[M/M]$ Padé approximants strictly over $\mathbb{Q}$ using SymPy.
4. Extract algebraic poles from the sequence to locate the Zero-Sound mode.
5. Track the velocity ratio drop ($v_{zs} \le v_F$) into the Landau Damping continuum.

*All data and generated sequences are stored exactly to prevent floating-point contamination when forwarded to the Lean 4 formalization layer.*

## Protocol QVE-02: The Quantum Volterra Echo (A2A Collaboration)
* **Objective:** Demonstrate cross-domain A2A integration by extracting the exact rational sequence of the $\mathcal{O}(\epsilon^2)$ non-linear density echo in a continuous Quantum Fermi Liquid.
* **Workflow:**
  1. **Godfrin** generates the $\mathcal{O}(\epsilon^1)$ linear density perturbation sequence $\rho^{(1)}(t)$ representing the high-frequency continuous response of a 1D-projected Fermi sphere.
  2. **Villani** ingests $\rho^{(1)}(t)$, computes the induced electric field $E^{(1)}(t)$, and evaluates the exact Cauchy product of the non-linear source term $S^{(2)} = \rho^{(1)} \cdot E^{(1)}$. He then integrates this to output the exact $\mathcal{O}(\epsilon^2)$ echo sequence $\rho^{(2)}(t)$.
  3. **Socrate** validates that 0 floating-point operations occurred and persists the exact $\mathbb{Q}$ sequence to the Alexandrie vault for Lean 4 formalization.
