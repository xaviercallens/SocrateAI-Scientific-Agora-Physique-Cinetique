# Notebooks

Four short, executed notebooks that walk through the engine's method and results. They are stored with outputs, so you
can read them on GitHub without running anything.

| Notebook | What it shows | Time |
|---|---|---|
| [`01_exact_zero_sound_quickstart.ipynb`](01_exact_zero_sound_quickstart.ipynb) | The core method: the Landau kernel as an exact rational series, its Padé approximant, the zero-sound velocity as an exact algebraic number, convergence against a 60-digit reference, the float refusal, and where the method stops (weak coupling). | < 1 min |
| [`02_real_he3_zero_sound.ipynb`](02_real_he3_zero_sound.ipynb) | The model confronted with measured ³He Landau parameters (Kollar & Vollhardt 2000, Table IX, from Greywall's data). With F₀ˢ alone it gets the sign of c₀ − c₁ wrong; adding F₁ˢ fixes it. Includes the exact pressure sweep. | ~1 min |
| [`03_theorem_22_6_numerics.ipynb`](03_theorem_22_6_numerics.ipynb) | The numerical worked examples after Theorem 22.6 of Villani's *Fisher Information in Kinetic Theory*, recomputed independently, with an exact anchor, and the theorem applied to the project's model roton kernel (γ̄ = 3.458). | ~1 min |
| [`04_large_simulation_dsmc_vs_exact_bkw.ipynb`](04_large_simulation_dsmc_vs_exact_bkw.ipynb) | A stochastic particle simulation (DSMC) of the homogeneous Boltzmann equation, certified by the exact Bobylev–Krook–Wu solution. It converges at the Monte Carlo rate N^−1/2, with no fitted parameter. | ~2 min |

Suggested order: 01 → 02, then 04, then 03. Only 03 needs any kinetic-theory background beyond a first course.

## Running them

From the repository root:

```bash
pip install -r requirements.txt jupyterlab     # or: pip install ... notebook
jupyter lab notebooks/
```

Each notebook finds the repository root on its own, so it can be opened from any directory inside the clone. Everything
runs offline. The ³He table is read from `alexandrie_data/HE3-LANDAU/`, which `verification/he3_landau/extract_table_ix.py`
produced from the arXiv PDF.

## Regenerating them

The notebooks are generated from [`build_notebooks.py`](build_notebooks.py), not edited by hand. To change one, edit that
file and rebuild:

```bash
pip install nbformat nbclient ipykernel
python3 notebooks/build_notebooks.py                       # write and execute all four
python3 notebooks/build_notebooks.py 02_real_he3_zero_sound.ipynb   # just one
```

The heavy computations behind notebooks 02 and 04 are full scripts in [`../simulations/large_scale/`](../simulations/large_scale):

```bash
python3 simulations/large_scale/he3_pressure_sweep.py      # 8 pressures x Padé orders 1..6, about 30 s
python3 simulations/large_scale/dsmc_bkw.py --quick        # CI check, about 20 s
python3 simulations/large_scale/dsmc_bkw.py                # N = 1e4, 1e5, 1e6 with several seeds, about 8 min
```

## Floating point here

The engine's derivations are exact over ℚ, and floats are refused there. Floats appear in these notebooks only to *check*
exact results against independent references, or in the particle simulation, which is a floating-point computation
judged against an exact solution. Never the reverse.
