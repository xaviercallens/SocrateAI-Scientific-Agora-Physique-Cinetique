"""
Summarise experiments E1-E3 (see EXPERIMENTS.md) from the raw output of

    rust/target/release/theorem_22_6 sweep    <DATA>
    rust/target/release/theorem_22_6 optimize <DATA>
    python3 roton_application.py              <DATA>/roton_application.json

Raw data stays in <DATA> (kept on the data disk, not in git); this writes a compact
summary to alexandrie_data/THM-22.6/experiments_summary.json and figures to
docs/figures/theorem_22_6/.

Run:  python3 verification/theorem_22_6/summarize_experiments.py <DATA>
"""
import json
import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import roton_application as RA  # noqa: E402

# reference palette, categorical slots 1-3 in fixed order (validated: CVD dE 9.2);
# slot 3 is below 3:1 on the surface, so every series is also direct-labelled/marked.
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, MUTED, GRID, AXIS, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
CLAIM = {3: 4.3, 2: 3.3}


def style(ax, title, xlabel, ylabel):
    ax.set_facecolor(SURFACE)
    ax.set_title(title, color=INK, fontsize=11, loc="left")
    ax.set_xlabel(xlabel, color=INK2, fontsize=9)
    ax.set_ylabel(ylabel, color=INK2, fontsize=9)
    ax.tick_params(colors=MUTED, labelsize=8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(AXIS)
    ax.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def claim_line(ax, d, left=False, below=False):
    ax.axhline(CLAIM[d], color=MUTED, linestyle="--", linewidth=1)
    ax.annotate(f"paper's claim: {'≥' if d == 3 else '>'} {CLAIM[d]}", xy=(0.0 if left else 1.0, CLAIM[d]),
                xycoords=("axes fraction", "data"), xytext=(4 if left else -4, -12 if below else 4), textcoords="offset points",
                ha="left" if left else "right", fontsize=8, color=INK2)


def main():
    data = Path(sys.argv[1])
    sweep = [json.loads(l) for l in open(data / "sweep_summary.jsonl")]
    opt = [json.loads(l) for l in open(data / "optimize.jsonl")]
    rot = json.load(open(data / "roton_application.json"))
    figdir = ROOT / "docs" / "figures" / "theorem_22_6"
    figdir.mkdir(parents=True, exist_ok=True)
    paper_nus = {3: [1.5, 1.6, 1.7, 1.8, 1.9, 1.925, 1.95, 1.975, 1.99, 1.999],
                 2: [1.0, 1.25, 1.5, 1.75, 1.925, 1.95, 1.99, 1.999]}

    # ---------------------------------------------------------------- E1
    e1 = {}
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), facecolor=SURFACE)
    for ax, d in zip(axes, (3, 2)):
        e1[d] = {}
        for g in ("paper_P12", "u100_from_0.36", "u200_from_0.10", "u400_from_0.05"):
            rs = sorted((r for r in sweep if r["d"] == d and r["grid"] == g), key=lambda r: r["nu"])
            worst = min(rs, key=lambda r: r["bound"])
            e1[d][g] = {"n_nu": len(rs), "min_bound": worst["bound"], "at_nu": worst["nu"],
                        "ratio": worst["lo"] / worst["hi"], "margin": worst["bound"] - CLAIM[d]}
        dense = sorted((r for r in sweep if r["d"] == d and r["grid"] == "u400_from_0.05"), key=lambda r: r["nu"])
        coarse = sorted((r for r in sweep if r["d"] == d and r["grid"] == "paper_P12"), key=lambda r: r["nu"])
        gap = max(((c["bound"] - f["bound"], c["nu"]) for c, f in zip(coarse, dense)))
        e1[d]["max_overestimate_of_11_angle_grid"] = {"amount": gap[0], "at_nu": gap[1]}
        nu = [r["nu"] for r in dense]
        ax.plot(nu, [r["bound"] for r in dense], color=BLUE, linewidth=2, label="400 angles in [0.05, π/2]")
        ax.plot([r["nu"] for r in coarse], [r["bound"] for r in coarse], color=ORANGE, linewidth=0,
                marker="o", markersize=3, label="paper's 11 angles")
        pn = [r for r in coarse if any(abs(r["nu"] - p) < 1e-9 for p in paper_nus[d])]
        ax.plot([r["nu"] for r in pn], [r["bound"] for r in pn], linewidth=0, marker="s", markersize=8,
                markerfacecolor="none", markeredgecolor=INK2, label="ν values the paper tabulates")
        w = min(dense, key=lambda r: r["bound"])
        ax.annotate(f"min {w['bound']:.4f} at ν={w['nu']:g}", xy=(w["nu"], w["bound"]), xytext=(8, -14),
                    textcoords="offset points", fontsize=8, color=INK)
        claim_line(ax, d)
        style(ax, f"d = {d}: bound vs ν, paper's weight", "ν (order of angular singularity)",
              "2√(Λ_b · c₂/C₁)")
        ax.legend(fontsize=7, frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(figdir / "e1_robustness.png", dpi=160)
    plt.close(fig)

    # ---------------------------------------------------------------- E2
    e2 = {}
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), facecolor=SURFACE)
    for ax, d in zip(axes, (3, 2)):
        rs = sorted((r for r in opt if r["d"] == d), key=lambda r: r["nu"])
        e2[d] = [{k: r[k] for k in ("nu", "fractional_laplacian_bound", "paper_weight_bound",
                                    "best_bound", "best_a", "best_b", "best_ratio")} for r in rs]
        nu = [r["nu"] for r in rs]
        for key, color, marker, label in (("fractional_laplacian_bound", AQUA, "^", "plain fractional Laplacian (w = 1)"),
                                          ("paper_weight_bound", ORANGE, "o", "paper's hand-tuned weight"),
                                          ("best_bound", BLUE, "D", "best in family (grid search)")):
            ys = [r[key] for r in rs]
            ax.plot(nu, ys, color=color, linewidth=2, marker=marker, markersize=5, label=label)
        claim_line(ax, d, left=(d == 3), below=True)
        fam = r"$1 - a\,(1 - e^{-bt})$" if d == 3 else r"$1 + a\,(1 - e^{-bt})$"
        style(ax, f"d = {d}: weight w(t) = {fam}", "ν", "2√(Λ_b · c₂/C₁)")
        ax.legend(fontsize=7, frameon=False, loc="lower right" if d == 3 else "lower left")
    fig.tight_layout()
    fig.savefig(figdir / "e2_weight_search.png", dpi=160)
    plt.close(fig)

    # ---------------------------------------------------------------- E3
    th = np.linspace(0, math.pi / 2, 1001)
    b = RA.beta_sym(th)
    b0 = sum(w * RA.heat_kernel_sym(t, th) for t, w in rot["mixture"])
    r = b0 / b
    b0_scaled = b0 / r.max()
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), facecolor=SURFACE)
    ax = axes[0]
    ax.plot(th, b, color=BLUE, linewidth=2, label="roton model kernel β (symmetrised)")
    ax.plot(th, b0_scaled, color=ORANGE, linewidth=2, linestyle="--",
            label=f"best heat-kernel mixture β₀ ({len(rot['mixture'])} atoms, t ≈ 0.38)")
    style(ax, "Q-RHK-02 kernel vs its best heat-kernel comparison", "θ", "kernel value")
    ax.legend(fontsize=7, frameon=False, loc="upper right")
    ax = axes[1]
    ax.plot(th, r / r.max(), color=BLUE, linewidth=2)
    ax.annotate(f"m/M = {rot['R_check']:.5f}", xy=(0.02, 0.1), xycoords="axes fraction", fontsize=9, color=INK)
    style(ax, f"β₀/β (normalised) → γ̄ = 2√(3·m/M) = {rot['gamma_bar']:.3f}", "θ", "β₀ / β")
    fig.tight_layout()
    fig.savefig(figdir / "e3_roton_theorem_22_6.png", dpi=160)
    plt.close(fig)

    summary = {
        "E1_robustness_min_bound_by_grid": {str(d): v for d, v in e1.items()},
        "E2_weight_search": {str(d): v for d, v in e2.items()},
        "E3_roton_kernel_theorem_22_6": rot,
        "claims": {"d=3": ">= 4.3", "d=2": "> 3.3"},
        "source": "verification/theorem_22_6 (EXPERIMENTS.md)",
    }
    out = ROOT / "alexandrie_data" / "THM-22.6" / "experiments_summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"wrote {out}")
    print(f"wrote figures to {figdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
