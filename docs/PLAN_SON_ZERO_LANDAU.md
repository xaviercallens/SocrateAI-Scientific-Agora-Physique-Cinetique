# Proposition : amortissement de Landau du son zéro dans l'hélium-3 bidimensionnel — un objet commun pour C. Villani et H. Godfrin

**Statut : PROPOSITION (2026-09-22). Rien n'est implémenté. Le hold sur tout contact reste en vigueur
(`docs/FOR_GODFRIN.md` §0).**

## 1. Pourquoi cet objet et pas un autre

Le point de rencontre n'est pas à inventer : l'équation cinétique de Landau pour un liquide de Fermi sans
collisions est une équation de type Vlasov (transport libre + champ moyen donné par les paramètres de
Landau F₀ˢ, F₁ˢ…), et l'amortissement de Landau du son zéro — le mode collectif qui entre dans le
continuum particule-trou — est exactement le phénomène de Mouhot–Villani, avec F₀ˢ à la place de 1/k².
Godfrin a mesuré ce mode par diffusion de neutrons dans une monocouche de ³He (Nature 483, 576, 2012) ;
Villani a démontré la version non linéaire du phénomène (Acta Math. 2011), formalisée en Lean par
Bedrossian (arXiv:2609.16801, fond petit, sans relation de dispersion ni critère de Penrose).

Ce qui rend le cas **bidimensionnel** singulier, et c'est le cœur de la proposition : la fonction de
Lindhard 2D est **algébrique** (Ω(s) = 1 − s/√(s²−1) hors continuum, 1 + i s/√(1−s²) dedans), alors qu'en
3D elle est logarithmique. Toute la théorie linéaire — racines, taux d'amortissement, seuil d'entrée dans
le continuum, critère de stabilité — se réduit à des équations polynomiales. *Sans approximation* n'est
donc pas un slogan : c'est le régime où Lean peut tout prouver et où une énumération certifiée est exacte.

## 2. Ce qui existe déjà et sert directement

| Actif | Réutilisation |
|---|---|
| `ZeroSound.lean` (6 thm.) : son zéro non amorti ⟺ F₀ˢ > 0, 2D et 3D, racine 2D explicite (1+F)/√(1+2F) | premier énoncé du programme ; à étendre à F₁ˢ et au continuum |
| `dispersion.py` : racines certifiées (Arb, Newton par intervalles) de relations de dispersion Vlasov | remplacer Z(ζ) par Ω₂(s) : le code est le même |
| `vlasov.py` : solveur 1D1V semi-lagrangien validé à 0,14 % contre une racine certifiée, échos et récurrence épinglés | remplacer v ∈ ℝ par θ ∈ S¹ (vitesse v_F(cos θ, sin θ)) et E par l'intégrale de Landau ∫ F(θ−θ′) δn(θ′) : même structure, même coût |
| `PhononSeries` : troncature comme nilpotence, certificats CAS vérifiés par le noyau | pour les développements en petit q / petit F |
| Ancillaires Godfrin (PRB 103, 104516) et méthode de comparaison à résolution instrumentale (`HeliumKinematics`) | convolution avec la résolution IN5 |
| Discipline : pré-enregistrement, contrôles négatifs, portes littérature, registre | obligatoire vu le bilan TDA (5 propositions, 5 réfutées) |

## 3. Programme, en quatre volets

**V1 — Théorie linéaire exacte, en Lean (Villani ↔ Godfrin, via la même équation).**
- `zero_sound_F1` : condition de son zéro avec F₀ˢ et F₁ˢ en 2D ; existence, unicité, position s(F₀,F₁)
  — tout algébrique.
- **« Pomeranchuk = Penrose »** : la stabilité de l'équation cinétique de Landau 2D (aucune racine à
  Im ω > 0) équivaut à F₀ˢ > −1. C'est le critère de Penrose spécialisé au fond de Fermi, prouvable sans
  transformée de Laplace précisément parce que tout est algébrique. Bedrossian écrit que ce volet manque
  à sa formalisation ; ce serait la première pièce de ce type.
- Taux d'amortissement de Landau dans le continuum : formule fermée, prouvée.
- Chaque énoncé avec contrôle négatif (F₀ˢ > −1 remplacé par ≥ −1 doit échouer) et Comparator.

**V2 — Énumération certifiée, en Arb.** Pour chaque pression mesurée par Godfrin (densité surfacique →
v_F, m*, F₀ˢ, F₁ˢ tirés de la littérature, sources à fixer avant tout calcul) : boule certifiée
contenant la racine, seuil q_c d'entrée dans le continuum, largeur d'amortissement Γ(q). Contrôle négatif :
une boule décalée doit être rejetée.

**V3 — Solveur cinétique de Landau 2D, haute performance.** δn(x, θ, t) sur un tore : transport exact
en Fourier, champ moyen par convolution angulaire, splitting de Strang. Validation : taux linéaire dans
la boule certifiée de V2 (ce que nous avons fait pour Vlasov), récurrence et écho **champ coupé** où ils
sont exacts. Puis la question que seul le solveur pose : **le scénario de Mouhot–Villani (amortissement
non linéaire, retour vers le transport libre) tient-il pour les paramètres de Landau réels du ³He 2D ?**
Et la variante Fermi-liquide de l'écho à deux impulsions — un écho de son zéro — a-t-elle une signature
observable ? (Question ouverte ; kill : si l'amplitude prédite est sous le bruit de toute mesure
envisageable, on le dit et on arrête.)

**V4 — Confrontation à l'expérience, comme modèle nul certifié.** Le résultat de Nature 2012 est
justement que le mode mesuré (type roton) *n'est pas* décrit par la théorie de Landau/RPA : il faut les
fluctuations de paires (Krotscheck, Böhm, Panholzer). Notre apport n'est donc pas de retrouver le mode,
mais de fournir **la référence exacte** dont la mesure s'écarte : S(q, ω) de Landau 2D, sans aucune
approximation numérique, convolué avec la résolution instrumentale, avec l'écart quantifié en σ par q.
Un écart certifié est plus informatif qu'un accord approché ; c'est ce qu'un expérimentateur peut
utiliser, et c'est la première chose à lui montrer.

## 4. Ce que chacun y trouve

- **Villani** : le critère de Penrose et la relation de dispersion formalisés dans le seul cas où c'est
  algébrique, sur une équation physique réelle ; un solveur validé contre des racines certifiées pour
  explorer numériquement l'amortissement non linéaire hors du régime « fond petit » du théorème.
- **Godfrin** : un modèle nul exact de son zéro 2D à ses pressions, avec résolution instrumentale, et la
  liste certifiée des seuils q_c ; plus la confirmation déjà acquise de son Éq. (22) (PRB 2021).
- **Le point commun** : l'objet est un seul, l'équation de Landau–Vlasov, et les deux lectures — théorème
  d'un côté, spectre de l'autre — sont reliées par un calcul sans approximation.

## 5. Ce que cela ne fait pas, et critères d'arrêt

- Aucune nouvelle physique n'est promise. V1 et V2 sont de la physique de manuel rendue exacte ; V4 est
  un modèle nul. Le seul élément potentiellement nouveau (V3, non linéaire) est une question, pas un résultat.
- Rien sur les fluctuations de paires ni sur le mode roton lui-même : hors de portée d'un traitement exact.
- **Portes avant tout code** : (1) recherche d'antériorité — Penrose/Pomeranchuk en 2D a-t-il déjà été
  formalisé ou traité comme tel ? amortissement non linéaire en liquide de Fermi (Bedrossian a-t-il des
  fonds Fermi-Dirac ?) ; (2) sources fixées pour F₀ˢ, F₁ˢ, m* du ³He 2D par densité ; (3)
  pré-enregistrement commité avant le premier nombre, cette fois sans exception.
- **Arrêt** si : la porte (1) montre que V1 est fait ; les paramètres de Landau 2D ne sont pas
  disponibles avec incertitudes ; le solveur ne reproduit pas la racine certifiée à 1 %.

## 6. Première étape concrète (une semaine)

Portes (1)–(2), puis V1 « Pomeranchuk = Penrose » en Lean et V2 pour une seule pression. Si V1 passe
Comparator et V2 donne une boule certifiée, on a de quoi écrire une page à chacun — après levée du hold,
et sur décision du propriétaire.

---

# Extension (2026-09-22) : boucle complète Théorie → Topologie → Physique → Expérience → Solveur → TDA → Théorie, Lean 4 en clé de voûte

Faits vérifiés avant d'écrire (pas de mémoire) : dépôt Bedrossian `Jacob24876/LandauDamping-Public`,
Lean **v4.29.1**, dépendance `AnalysisBase-Public`, « no sorry, no custom axioms », README : « the public
assembly results include hypotheses and some parameter restrictions beyond the source theorem ». Crates
Rust : `sundials-sys` 0.6.2 (bindings SUNDIALS : CVODE, ARKODE, IDA), `sundials` 0.4.1 (wrapper sûr),
`diffsol` 0.16.2 (ODE/DAE pur Rust, 100 k téléchargements). **Aucune crate « runux » ni
« rusty-sundials » n'existe sur crates.io** ; je suppose que « rusty sundials » désigne `sundials`/`sundials-sys`
et je ne devine pas ce que « runux » désigne — à préciser.

## 7. Étendre et formaliser les travaux de Villani en Lean 4, sur les épaules des grands projets IA

Trois codes sources, trois toolchains, trois usages différents :

| Source | Toolchain | Ce qu'on en prend | Comment |
|---|---|---|---|
| **Bedrossian, LandauDamping** (2026) | 4.29.1 (+ AnalysisBase) | normes de Gevrey sur l'espace des phases, bornes d'écho résonant et de Schur, résolvante de Volterra, scattering vers le transport libre | *construire dessus* : nos énoncés 2D Fermi doivent être formulés dans SES définitions (fond, normes, mode k) pour que « Penrose = Pomeranchuk » s'assemble avec son théorème. Coût : migration 4.29 → 4.34 ou pin de notre module à 4.29 ; à mesurer avant tout |
| **OpenAI NavierStokesAndEuler** | 4.34.0-rc2 (dépendance déjà en place) | vocabulaire tore/dérivées/Sobolev | inchangé (`MadelungNSE`) |
| **Anthropic FLT** | 4.33.1 | inversion de Fourier sur le tore à n dimensions, borne sup Sobolev sur un cube | port (deux fichiers, ~500 lignes), pour passer des modes de Fourier au champ δn(x, θ) |

**Cibles, par ordre de faisabilité, chacune avec ce qui manque à Bedrossian selon son propre README :**

1. **Critère de Penrose et relation de dispersion, cas algébrique 2D Fermi** (V1 ci-dessus). Absent de sa
   formalisation (« fond petit », pas de Laplace). Le cas 2D évite l'analyse complexe : c'est le *seul*
   endroit où l'on peut fermer ce trou aujourd'hui. Nouveau et modeste.
2. **Fond de Fermi–Dirac au lieu du fond « petit ».** Son théorème est énoncé pour un fond de faible
   amplitude ; le fond physique (Fermi–Dirac à T > 0, analytique) ne l'est pas. Première marche :
   prouver que le fond de Fermi–Dirac satisfait ses hypothèses de régularité Gevrey (c'est un calcul de
   normes, pas un théorème nouveau) ; seconde marche : le cas F₀ˢ petit mais fond d'amplitude 1, qui est
   exactement le régime « liquide de Fermi faiblement interagissant ». Kill : si ses hypothèses encodent
   « petit » de façon inséparable de la régularité, le dire.
3. **Échos non linéaires de son zéro** : ses bornes d'écho (Schur) instanciées avec F(θ−θ′) à la place
   du noyau de Poisson — une *application* de ses lemmes, pas un théorème nouveau ; c'est ce qui borne
   V3 rigoureusement.
4. **Plus loin, hors de portée immédiate, dit tel quel** : hypocoercivité (Villani, Memoirs AMS 2009) —
   Mathlib n'a ni Fokker–Planck ni les espaces fonctionnels ; théorème H de Boltzmann — pas d'entropie
   cinétique dans Mathlib ; transport optimal/Wasserstein — programme de plusieurs années. À ne pas
   promettre.

Porte avant tout : recherche d'antériorité sur (1) et (2), et construction de son dépôt en local pour
lire les énoncés réels (le README prévient que la portée est restreinte).

## 8. Solveur certifié et optimisé : Python de référence, Rust de production, SUNDIALS pour le raide

Trois niveaux, chacun validé contre le précédent et contre la racine certifiée Arb :

| Niveau | Rôle | Validation |
|---|---|---|
| **Python** (`vlasov.py` étendu à δn(x, θ)) | référence lisible, 1 page | racine certifiée à 1 % ; écho/récurrence champ coupé exacts |
| **Rust** (crate `qf-kinetic`) : transport en Fourier (`rustfft`), semi-lagrangien angulaire, parallélisme `rayon`, FFI vers Python (`pyo3`) | production : x-θ à 512×1024 en minutes, balayage des pressions et des paramètres de Landau | bit-à-bit égal à Python sur les cas de test aux erreurs d'arrondi près ; mêmes contrôles |
| **SUNDIALS via `sundials-sys`/`sundials`** : CVODE (BDF) pour la variante *avec* collisions (Landau–Boltzmann linéarisé, raide : temps de relaxation τ ∝ T⁻²), ARKODE (IMEX) pour transport + collisions | c'est le passage Vlasov → cinétique complète, indispensable pour comparer aux mesures à T > 0 (largeur collisionnelle ∝ T²) | limite sans collisions → niveau Rust ; solution de Chapman–Enskog en limite hydrodynamique (premier son, réponse connue) |

« Certifié » a un sens précis et limité ici : (a) les racines et seuils sont des enclos Arb, prouvés ;
(b) les schémas sont validés contre ces enclos et contre des formules fermées ; (c) les propriétés
structurelles du schéma (conservation discrète de la masse, antisymétrie du transport en Fourier) sont
des énoncés candidats pour Lean sur le schéma *discret* (finis, décidables) — pas une preuve du code
Rust. Ne pas écrire « solveur prouvé ».

`diffsol` (pur Rust, DAE) est l'alternative si les bindings SUNDIALS posent problème à la compilation.

## 9. Topologie et TDA : fermer la boucle, avec le bilan honnête

Bilan : cinq propositions TDA, cinq réfutées ; mécanisme identifié pour les deux dernières
(persistance = profondeur jusqu'au col de connexion). Le TDA ne revient donc **qu'en instrument à
réponse connue**, et chaque usage ci-dessous nomme sa réponse connue et son contrôle.

| Maillon | Usage TDA (GUDHI) | Réponse connue / contrôle | Retour vers la théorie (Lean) |
|---|---|---|---|
| **Solveur → TDA** : filamentation sur le cercle de Fermi | persistance H₀ des sous-niveaux de δn(x₀, θ, t) (complexe cubique périodique en θ) ; nombre de barres = nombre de filaments | transport libre : δn = cos(kθ·… − kv_F t cos θ) a un nombre de barres calculable exactement à chaque t ; le solveur doit le reproduire *champ coupé* | **`persistence_cos` en Lean** : la persistance H₀ de θ ↦ cos(nθ) sur S¹ est exactement n barres de longueur 2 (énoncé fini, décidable via l'elder rule sur un graphe cycle) — le premier théorème TDA du dépôt qui ne soit pas un simple lemme de 1-squelette |
| **TDA → Théorie** : dualité | contrôle D0 (déjà exact sur données GP) | théorème de symétrie CSEH 2009 | **`symmetry_1d` en Lean** : version discrète 1D du théorème de symétrie (H₀ de f vs H₀ de −f sur un cycle) — clé de voûte : ce que GUDHI calcule est ce que Lean prouve |
| **Physique → TDA** : entrée dans le continuum | diagramme H₀ de la *relation de dispersion* Im D(s, q) : le bar né en q_c est le seuil | q_c certifié par Arb (V2) ; la barre doit naître à q_c ± l'enclos | rien à prouver : c'est un test que le pipeline lit bien un seuil certifié |
| **Expérience → TDA** | proéminence des pics de S(q, ω) mesuré vs modèle nul (V4) | déjà fait pour ε(k) : 0,4501 = 0,4501 meV (c'est la proéminence, et on le dit) | — |

Ce que la boucle **ne** fait pas : découvrir une structure. Chaque flèche transporte une quantité dont
la valeur est connue à l'avance par au moins un autre maillon ; la boucle est fermée quand chaque
maillon rend la même valeur, et Lean est la clé de voûte parce que c'est le seul maillon dont la sortie
ne peut pas être ajustée.

## 10. Plan et workflow (pour approbation)

Sept agents maximum, portes dures, tout pré-enregistré et commité avant le premier nombre.

| Phase | Agents | Livrable | Porte |
|---|---|---|---|
| 0. Antériorité | 2 (Lean/Villani ; solveur/TDA) | mémo : (1) et (2) de §7 sont-ils faits ? paramètres de Landau 2D sourcés ? | tout item déjà fait est rayé |
| 1. Pré-enregistrement | — (moi, revu par le propriétaire) | critères, tolérances, contrôles négatifs, réponses connues | commit horodaté |
| 2. Lean noyau | 1 | `zero_sound_F1`, `pomeranchuk_penrose`, `persistence_cos`, `symmetry_1d` ; Comparator | contrôles négatifs échouent |
| 3. Enclos certifiés | 1 | Arb : racines, q_c, Γ(q) par pression | boule décalée rejetée |
| 4. Solveurs | 2 (Python+Rust ; SUNDIALS) | δn(x,θ,t) validé ; variante collisionnelle | racine certifiée à 1 % ; échos champ coupé exacts |
| 5. TDA | 1 | filamentation vs transport libre ; D0 ; q_c lu | réponses connues reproduites |
| 6. Modèle nul vs expérience | 1 | S(q,ω) Landau 2D convolué IN5, écart en σ par q | — (résultat, quel qu'il soit) |
| 7. Revue adverse | 1, contexte vierge | « qu'objecterait un cinéticien / un neutronicien en dix minutes » | décision du propriétaire sur tout contact |

Dépôt cible : **ce dépôt** pour Lean, Arb, Python et TDA (registre, Comparator, tests déjà là) ;
**Physique-Cinétique** reçoit le solveur Rust/SUNDIALS et devient le dépôt « cinétique haute
performance », relié à celui-ci par une dépendance déclarée — pas par copie. Première PR là-bas : ce
plan, la CI déplacée à la racine, LICENSE laissée au propriétaire.
