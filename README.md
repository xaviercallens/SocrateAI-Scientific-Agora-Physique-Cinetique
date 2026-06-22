# 🏛️ Agora-Physique-Cinetique : Modélisation Neuro-Symbolique et Échos Quantiques

Bienvenue dans le dépôt open source du projet **Agora-Physique-Cinetique**, un sous-ensemble du laboratoire SocrateAI dédié à l'extraction algébrique et à la vérification formelle en physique cinétique (Fluides Quantiques & Plasmas).

## 🌌 Vision du Projet
L'application de l'Intelligence Artificielle à la physique théorique se heurte à deux problèmes critiques :
1. L'hallucination sémantique des modèles de langage (LLMs).
2. L'altération de la dynamique continue par la discrétisation numérique flottante (Float64), qui fausse des phénomènes complexes comme l'amortissement Landau.

Ce projet impose une **règle épistémologique stricte : la "Zéro Simulation Flottante"**. Les équations continues sont réduites à des invariants algébriques et des séries de Taylor / produits de Cauchy calculés de manière exacte sur le corps des rationnels ($\mathbb{Q}$). Ces séquences pures sont ensuite formatées pour être prouvées avec 0 axiome non-vérifié ("0 sorry") dans le compilateur **Lean 4**.

## 🤖 L'Essaim Collaboratif (Architecture A2A)
Ce dépôt implémente une collaboration inter-domaines automatisée via trois agents logiciels :
* ⚛️ **Agent Godfrin (Expert Fluides Quantiques) :** Extrait la dynamique continue de la sphère de Fermi.
* 🌌 **Agent Villani (Expert Physique Mathématique) :** Applique les intégrations cinétiques non-linéaires (perturbations de Volterra, équation de Vlasov).
* 🏛️ **Agent Socrate (Orchestrateur Épistémologique) :** Garantit la pureté algébrique des échanges et archive les résultats dans la voûte *Alexandrie*.

## 🔬 Découverte : Protocole QVE-02 (Quantum Volterra Echo)
Un fluide de Fermi purement quantique peut-il produire un écho plasma non-linéaire continu ?
L'essaim a combiné la réponse linéaire quantique de l'Agent Godfrin avec l'intégrateur non-linéaire de Volterra $\mathcal{O}(\epsilon^2)$ de l'Agent Villani pour extraire la séquence temporelle algébrique exacte de cet écho :

`Termes t^2 à t^{10} : [1/2, -1/18, 13/4050, -4/33075, 73/22325625]`

Aucune approximation numérique n'a été utilisée. Ces séquences constituent le point de départ de la formalisation Lean 4.

## 🔬 Expérimentation : Protocole Q-RHK-02 (Roton Fractional Heat Kernels)

**[FR] Modélisation Phénoménologique de l'Amortissement**
Pour tester les bornes de régularité cinétique du Théorème 22.6 de C. Villani (2025), l'Agent Godfrin a formulé un noyau de diffusion roton-roton algébrique. Ce noyau mathématique est *inspiré* de la phénoménologie du "forward-peaking" observée expérimentalement (ex: ILL IN5), mais il reste un modèle analytique strict (sans données empiriques directes) pour préserver la règle de la "Zéro Simulation Flottante" :
$\beta(\cos \theta) = \frac{1}{2}(1 + \cos^2\theta) \exp(-\frac{1}{10}(1 - \cos\theta))$

L'Agent Villani dérive formellement par algèbre symbolique (SymPy) que, sous ce modèle exact, la singularité cinétique admissible est bornée par :
$|\gamma| \le \sqrt{3}\exp(-0.1) \approx 1.567$

**[EN] Phenomenological Modeling of Damping**
To test the kinetic regularity bounds of C. Villani's Theorem 22.6 (2025), Agent Godfrin formulated an algebraic roton-roton scattering kernel. This mathematical kernel is *inspired* by the "forward-peaking" phenomenology observed experimentally (e.g., ILL IN5), but remains a strict analytical model (without direct empirical data) to enforce the "Zero Floating-Point Simulation" rule:
$\beta(\cos \theta) = \frac{1}{2}(1 + \cos^2\theta) \exp(-\frac{1}{10}(1 - \cos\theta))$

Agent Villani formally derives via symbolic algebra (SymPy) that, under this exact model, the admissible kinetic singularity is bounded by:
$|\gamma| \le \sqrt{3}\exp(-0.1) \approx 1.567$

## 🚀 Utilisation

### 1. Protocole QVE-02 (Écho Quantique de Volterra)
```bash
# Lancer la simulation collaborative multi-agents
python simulations/qve_02_quantum_echo.py
```

### 2. Protocole Q-RHK-02 (Noyaux de Chaleur Fractionnaires de Rotons)
```bash
# Calculer les bornes et la décroissance de l'Information de Fisher pour les rotons
python simulations/q_rhk_02_roton_fisher.py
```

### 3. Protocole QV-01 (Quantum Vlasov Zero-Sound Simulation)
```bash
# Extraire les pôles exacts du Son Zéro (Padé [M/M]) sur la fonction de Lindhard
python simulations/qv_01_zero_sound.py
```

### 4. Protocole Q-RIP-03 (2D Quantum Ripplons)
```bash
# Dériver la constante de Bakry-Émery L*=4 pour la protection topologique des ripplons 2D
python simulations/q_rip_03_ripplon.py
```

*Les données générées sont archivées de manière permanente dans `/alexandrie_data/`. Consultez le dossier `/docs/` pour la monographie scientifique détaillée en PDF.*

