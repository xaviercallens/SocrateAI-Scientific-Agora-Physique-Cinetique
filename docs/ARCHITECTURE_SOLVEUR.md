# Architecture cible du solveur cinétique (proposition, 2026-09-22 — rien d'implémenté)

Rôle de ce dépôt dans le plan `PLAN_SON_ZERO_LANDAU.md` §8–§10 : le solveur **haute performance** de
l'équation cinétique de Landau 2D (δn(x, θ, t) sur le cercle de Fermi), et sa variante collisionnelle.
La référence Python, les racines certifiées (Arb), Lean 4 et le TDA restent dans
`SocrateAI-Scientific-QuantumFluids` ; ce dépôt en dépend, il ne les copie pas.

## Règle du « zéro simulation flottante », réinterprétée honnêtement

L'idée d'origine de ce dépôt — l'exactitude rationnelle — est bonne là où elle s'applique : racines et
seuils sont des **enclos certifiés** (Arb, midpoint-radius, chaque arrondi inclus dans la boule), les
développements en série sont vérifiés par le noyau Lean. Un solveur d'EDP en virgule flottante n'est pas
exact et ne le sera jamais ; il est **validé** contre ces enclos et contre des formules fermées (écho
balistique, récurrence champ coupé). Le mot « certifié » s'applique aux enclos, pas au code.

## Trois niveaux

| Niveau | Techno | Rôle | Validation |
|---|---|---|---|
| référence | Python/numpy (dans QuantumFluids) | lisible, 1 page | racine certifiée à 1 % |
| production | Rust : `rustfft` (transport en x exact en Fourier), semi-lagrangien angulaire, `rayon`, `pyo3` | balayages pressions × paramètres de Landau | bit-à-bit ≈ Python (arrondis près), mêmes contrôles négatifs |
| raide | SUNDIALS via `sundials-sys` 0.6 / `sundials` 0.4 : CVODE (BDF) pour Landau–Boltzmann linéarisé, ARKODE (IMEX) transport + collisions ; repli `diffsol` 0.16 (pur Rust) | comparer aux mesures à T > 0 (largeur ∝ T²) | limite sans collisions → niveau production ; limite hydrodynamique → premier son |

Ce qui *peut* passer en Lean : propriétés du schéma **discret** (conservation exacte de la masse par le
shift de Fourier, antisymétrie), énoncés finis et décidables. Ce n'est pas une preuve du code Rust.

## Ordre de construction

1. CI à la racine (à faire par le propriétaire : le jeton utilisé ici n'a pas le scope `workflow`) ; migration Lean 4.31 → 4.34.0-rc2 pour partager du code avec
   QuantumFluids.
2. Crate `qf-kinetic` : transport libre seul, test = écho balistique en forme fermée.
3. Champ moyen de Landau (F₀ˢ, puis F₁ˢ) ; test = taux linéaire dans l'enclos Arb.
4. `sundials-sys` : opérateur de collision relaxationnel (BGK) puis linéarisé ; test = limite τ → ∞.
5. Rien n'est écrit avant le pré-enregistrement commité côté QuantumFluids.
