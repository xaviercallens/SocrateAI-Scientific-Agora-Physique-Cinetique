"""
Figures for docs/textbook/agora_textbook.tex.

Every curve is either read from a committed result file under alexandrie_data/, or computed here
from a closed form (the Landau kernel, the exact BKW solution). Nothing is typed in by hand except
Table 2 of docs/agora_engine_paper.tex (the Padé convergence study), which is quoted with its source.

Run from the repository root:
    python3 docs/textbook/figures/make_figures.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mpmath as mp

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent

# reference palette, first three categorical slots (validated all-pairs), text inks
C1, C2, C3 = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#dcdad3"

plt.rcParams.update({
    "font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
    "ytick.color": INK2, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 2,
    "legend.frameon": False, "savefig.bbox": "tight",
})


def save(fig, name):
    fig.savefig(OUT / name)
    plt.close(fig)
    print("wrote", OUT / name)


# ---------------------------------------------------------------- Padé convergence (engine paper, Table 2)
def fig_pade():
    M = [1, 2, 3, 4]
    rows = {"$F_0^s=30$": [3.20e-4, 2.01e-7, 1.25e-10, 7.71e-14],
            "$F_0^s=93/10$": [2.89e-3, 1.79e-5, 1.11e-7, 6.81e-10],
            "$F_0^s=1$": [None, 1.49e-2, 3.87e-3, 1.12e-3]}
    fig, ax = plt.subplots(figsize=(4.6, 3.0))
    for (lab, ys), c in zip(rows.items(), (C1, C2, C3)):
        xs = [m for m, y in zip(M, ys) if y is not None]
        ys = [y for y in ys if y is not None]
        ax.semilogy(xs, ys, "-o", color=c, ms=5, label=lab)
        ax.annotate(lab, (xs[-1], ys[-1]), xytext=(6, 0), textcoords="offset points",
                    va="center", color=INK, fontsize=8)
    ax.set_xticks(M)
    ax.set_xlim(0.8, 5.0)
    ax.set_xlabel("Padé order $M$ of the $[M/M]$ approximant")
    ax.set_ylabel("relative error in $s$")
    save(fig, "pade_convergence.pdf")


# ---------------------------------------------------------------- the proved bracket vs 60-digit roots
def fig_bracket():
    mp.mp.dps = 60
    g3 = lambda s: s / 2 * mp.log((s + 1) / (s - 1)) - 1
    Fs = [mp.mpf(1) / 20, mp.mpf(1) / 10, mp.mpf(3) / 20, mp.mpf(3) / 10, mp.mpf(1) / 2, mp.mpf(1),
          mp.mpf(3), mp.mpf(93) / 10, mp.mpf(30)]
    roots = []
    for F in Fs:
        # s - 1 = x; bisection on log x between the proved bracket edges (widened slightly)
        lo = mp.log(2 * mp.e ** (-(2 + 2 / F))) - 1
        hi = mp.log(F) + 1
        f = lambda y: g3(1 + mp.e ** y) - 1 / F
        for _ in range(250):
            mid = (lo + hi) / 2
            if f(mid) > 0:
                lo = mid
            else:
                hi = mid
        roots.append(float(mp.e ** ((lo + hi) / 2)))
    grid = [10 ** (-1.4 + 3.0 * i / 300) for i in range(301)]
    fig, ax = plt.subplots(figsize=(4.6, 3.2))
    ax.loglog(grid, grid, color=C2, lw=1.5, label="upper edge $F$")
    ax.loglog(grid, [2 * mp.e ** (-(2 + 2 / x)) for x in grid], color=C1, lw=1.5,
              label=r"lower edge $2e^{-(2+2/F)}$")
    ax.loglog([float(F) for F in Fs], roots, "o", color=INK, ms=4.5, label="60-digit roots")
    ax.set_ylim(1e-20, 1e2)
    ax.set_xlabel(r"coupling $F = F_0^s$")
    ax.set_ylabel(r"$s-1$ at the undamped root")
    ax.legend(loc="lower right", fontsize=8)
    save(fig, "zero_sound_bracket.pdf")


# ---------------------------------------------------------------- real 3He: c0/c1 for both models
def fig_he3():
    d = json.loads((ROOT / "alexandrie_data/HE3-LANDAU/zero_sound_real_he3.json").read_text())["results"]
    P = [r["P_bar"] for r in d]
    fig, ax = plt.subplots(figsize=(4.6, 3.0))
    one = [r["c0_F0_only"] / r["c1_landau"] for r in d]
    two = [r["c0_over_c1"] for r in d]
    ax.plot(P, two, "-o", color=C1, ms=4)
    ax.plot(P, one, "-o", color=C2, ms=4)
    ax.axhline(1, color=INK2, lw=1, ls="--")
    ax.annotate(r"with $F_1^s$", (P[-1], two[-1]), xytext=(0, 8), textcoords="offset points",
                ha="right", color=INK, fontsize=8)
    ax.annotate(r"$F_0^s$ only", (P[-1], one[-1]), xytext=(0, 8), textcoords="offset points",
                ha="right", color=INK, fontsize=8)
    ax.text(0.5, 1.0, "  $c_0=c_1$", va="bottom", color=INK2, fontsize=8)
    ax.set_xlabel("pressure $P$ (bar)")
    ax.set_ylabel("zero sound / first sound, $c_0/c_1$")
    save(fig, "he3_c0_over_c1.pdf")


# ---------------------------------------------------------------- real 4He: maxon - 2 Delta
def fig_he4():
    d = json.loads((ROOT / "alexandrie_data/HE4-KIN/helium_kinematics.json").read_text())["T2_maxon_vs_2delta"]
    P = [r["P_bar"] for r in d]
    fig, ax = plt.subplots(figsize=(4.6, 3.0))
    ax.errorbar(P, [r["excess_meV"] for r in d], yerr=[r["excess_err"] for r in d], fmt="o",
                color=C1, ms=4.5, capsize=2, lw=1.2)
    ax.axhline(0, color=INK2, lw=1, ls="--")
    ax.text(12, 0.012, r"maxon $=2\Delta$", color=INK2, fontsize=8)
    ax.set_xlabel("pressure $P$ (bar)")
    ax.set_ylabel(r"maxon energy $-\,2\Delta$ (meV)")
    save(fig, "he4_maxon_minus_2delta.pdf")


# ---------------------------------------------------------------- exact BKW: Fisher information and entropy
def fig_bkw():
    mp.mp.dps = 25
    K0 = mp.mpf("0.65")  # as in verification/validate_fisher_information_monotonicity.py
    K_of_t = lambda t: 1 - (1 - K0) * mp.e ** (-t / 6)

    def f(r, K):
        return (2 * mp.pi * K) ** mp.mpf(-1.5) * mp.e ** (-r * r / (2 * K)) * (
            (5 * K - 3) / (2 * K) + (1 - K) / (2 * K * K) * r * r)

    def fp(r, K):
        A = (2 * mp.pi * K) ** mp.mpf(-1.5) * mp.e ** (-r * r / (2 * K))
        Pr = (5 * K - 3) / (2 * K) + (1 - K) / (2 * K * K) * r * r
        return A * ((1 - K) / (K * K) * r - r / K * Pr)

    maxw = lambda r: (2 * mp.pi) ** mp.mpf(-1.5) * mp.e ** (-r * r / 2)
    ts = [0, 0.5, 1, 1.5, 2, 3, 4, 5, 6, 8, 10, 13, 16, 20, 25, 30]
    I, H = [], []
    for t in ts:
        K = K_of_t(mp.mpf(t))
        I.append(float(mp.quad(lambda r: 4 * mp.pi * r * r * fp(r, K) ** 2 / f(r, K), [0, 4, 12]) - 3))
        H.append(float(mp.quad(lambda r: 4 * mp.pi * r * r * f(r, K) * mp.log(f(r, K) / maxw(r)),
                               [0, 4, 12])))
    fig, axs = plt.subplots(1, 2, figsize=(6.4, 2.7))
    axs[0].semilogy(ts, I, "-o", color=C1, ms=3.5)
    axs[0].set_title(r"Fisher information $I(t)-3$", fontsize=9, color=INK)
    axs[1].semilogy(ts, H, "-o", color=C2, ms=3.5)
    axs[1].set_title(r"relative entropy $H(f\,|\,M)$", fontsize=9, color=INK)
    for ax in axs:
        ax.set_xlabel("time $t$")
    fig.tight_layout()
    save(fig, "bkw_fisher_entropy.pdf")


if __name__ == "__main__":
    fig_pade()
    fig_bracket()
    fig_he3()
    fig_he4()
    fig_bkw()
