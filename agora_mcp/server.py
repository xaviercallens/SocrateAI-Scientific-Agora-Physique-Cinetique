"""
Local stdio MCP server for the Agora engine.

Every tool is a thin wrapper over code or committed data already in this repository; nothing
here adds physics. The tools are plain functions (importable and testable in-process) that are
then registered with FastMCP.

Safety model (the server runs on the user's machine, driven by an AI agent):
  * no arbitrary code or shell: run_verification runs only the scripts in VERIFICATIONS;
  * no network by default: scripts that download data are refused unless the environment
    variable AGORA_MCP_ALLOW_NETWORK=1 is set when the server starts;
  * no writes to the repository: the whitelisted scripts only read committed files, and the
    network ones write only to their download cache (~/.cache/agora);
  * files are read only from fixed paths inside the repository;
  * exact inputs: Landau parameters are taken as strings or integers and converted exactly;
    a float is refused, as the engine itself refuses floats (ScientificHonestyException).

The engine prints progress to stdout, which is the MCP transport here, so every call into it
runs with stdout redirected to stderr.
"""
import contextlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import sympy as sp

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ALLOW_NETWORK = os.environ.get("AGORA_MCP_ALLOW_NETWORK") == "1"
MAX_PADE_ORDER = 8

# name -> (script relative to ROOT, needs network, timeout in seconds, what it checks)
VERIFICATIONS = {
    "zero_sound": ("verification/validate_zero_sound.py", False, 900,
                   "QV-01: exact Pade roots vs a 60-digit reference; weak-coupling bracket"),
    "kernel_regularity_bounds": ("verification/validate_kernel_regularity_bounds.py", False, 900,
                                 "Q-RHK-02: independent quadrature and Monte Carlo of m_r, M_r, Sigma"),
    "fisher_information_monotonicity": ("verification/validate_fisher_information_monotonicity.py", False, 900,
                                        "Fisher information and H-theorem along the exact BKW solution"),
    "theorem_22_6_reproduce": ("verification/theorem_22_6/reproduce.py", False, 900,
                               "Theorem 22.6 worked examples (d=2,3) vs the authors' reference values"),
    "helium_kinematics_data": ("verification/helium_kinematics_data.py", True, 900,
                               "E5: helium kinematics on Godfrin et al. 2021 IN5 data (downloads from arXiv)"),
}


class InputRefused(ValueError):
    """Raised for inputs the engine would refuse; the message is returned to the client."""


@contextlib.contextmanager
def _quiet():
    with contextlib.redirect_stdout(sys.stderr):
        yield


_RATIONAL = re.compile(r"^[+-]?(\d+(\.\d*)?|\.\d+)(/[1-9]\d*)?$")


def exact(value, name="value"):
    """Convert a string ('93/10', '10.279', '12') or int to an exact sympy Rational."""
    if isinstance(value, bool):
        raise InputRefused(f"{name}: booleans are not numbers")
    if isinstance(value, float):
        raise InputRefused(
            f"{name} was sent as a floating-point number ({value!r}). The engine works exactly "
            f"over Q and refuses floats (ScientificHonestyException). Send it as a string, "
            f"e.g. \"{value}\" or a fraction \"p/q\", and it will be converted exactly.")
    if isinstance(value, int):
        return sp.Integer(value)
    if isinstance(value, str) and _RATIONAL.match(value.strip()):
        return sp.Rational(value.strip())
    raise InputRefused(f"{name}: expected an integer, decimal or fraction string such as '93/10', got {value!r}")


def _read_json(rel):
    return json.loads((ROOT / rel).read_text())


# ----------------------------------------------------------------------------- engine tools
def zero_sound_root(F0s, F1s="0", M=4):
    """Exact zero-sound root of the Landau dispersion relation, via the exact [M/M] Pade
    approximant over Q. F0s, F1s: Landau parameters as exact strings ('93/10', '10.279').
    With F1s = 0 this is QV-01's chi(s) = 1/F0s; otherwise chi(s) = 1/(F0s + F1s s^2/(1+F1s/3)).
    u = 1/s^2, s = omega/(q v_F); an undamped mode needs u in (0,1)."""
    from agora_swarm.agents.kinetic import KineticStage
    from agora_swarm.agents.linear_response import LinearResponseStage, ScientificHonestyException

    F0, F1 = exact(F0s, "F0s"), exact(F1s, "F1s")
    if not isinstance(M, int) or isinstance(M, bool) or not 1 <= M <= MAX_PADE_ORDER:
        raise InputRefused(f"M must be an integer in 1..{MAX_PADE_ORDER}")
    with _quiet():
        try:
            kernel = LinearResponseStage().landau_zero_sound_kernel(order=2 * M + 2)
            k = KineticStage()
            if F1 == 0:
                r = k.solve_zero_sound_root(kernel, F0, M=M)
            else:
                r = k.solve_zero_sound_root_f0_f1(kernel, F0, F1, M=M)
        except ScientificHonestyException as e:
            raise InputRefused(str(e)) from e
    out = dict(r)
    out.setdefault("F1s_exact", str(F1))
    if r.get("root_found"):
        u = sp.sympify(r["u_exact"])
        out["u_numeric"] = str(sp.N(u, 30))
        out["s_numeric"] = str(sp.N(1 / sp.sqrt(u), 30))
    out["model"] = "F0s only (QV-01)" if F1 == 0 else "F0s and F1s"
    return out


def pade_approximant(M=2):
    """Exact diagonal [M/M] Pade approximant P(u)/Q(u) of the Landau zero-sound kernel
    chi(s) = (s/2) ln((s+1)/(s-1)) - 1 = sum_k u^k/(2k+1), u = 1/s^2, computed over Q."""
    from agora_swarm.agents.kinetic import KineticStage
    from agora_swarm.agents.linear_response import LinearResponseStage

    if not isinstance(M, int) or isinstance(M, bool) or not 1 <= M <= MAX_PADE_ORDER:
        raise InputRefused(f"M must be an integer in 1..{MAX_PADE_ORDER}")
    with _quiet():
        a = LinearResponseStage().landau_zero_sound_kernel(order=2 * M)
        P, Q, u = KineticStage().pade_diagonal(a, M)
    return {"M": M, "variable": "u = 1/s^2", "series_coefficients": [str(c) for c in a],
            "P": str(P), "Q": str(Q),
            "P_coefficients": [str(P.coeff(u, i)) for i in range(M + 1)],
            "Q_coefficients": [str(Q.coeff(u, i)) for i in range(M + 1)]}


# ------------------------------------------------------------------------------- data tools
def he3_landau_parameters(pressure_bar):
    """Real liquid-3He Landau parameters at a tabulated pressure (bar, T -> 0), from
    Kollar & Vollhardt, PRB 61, 15347 (2000), Table IX (Greywall's data), as committed in
    alexandrie_data/HE3-LANDAU. No interpolation: only tabulated pressures are served.
    Returns F0s, m*/m, F1s = 3(m*/m - 1), and zero/first sound where computed."""
    P = float(exact(str(pressure_bar) if isinstance(pressure_bar, (int, float)) and not isinstance(pressure_bar, bool)
                    else pressure_bar, "pressure_bar"))
    table = _read_json("alexandrie_data/HE3-LANDAU/kollar_vollhardt_table_ix.json")
    rows = {r["P_bar"]: r for r in table["derived"]}
    if P not in rows:
        raise InputRefused(f"pressure {P} bar is not tabulated; available: {sorted(rows)}")
    r = rows[P]
    printed = next(x for x in table["rows"] if float(x[0]) == P)
    out = {"P_bar": P, "F0s": r["F0s"], "m_star_over_m": r["m_star_over_m"],
           "F1s": 3 * (r["m_star_over_m"] - 1), "v_F_m_per_s": r["v_F_m_per_s"],
           "printed_row": dict(zip(table["columns"], printed)),
           "source": table["source"], "pdf_sha256": table["pdf_sha256"],
           "derivation": table["derivation"] + "; F1s = 3(m*/m - 1)"}
    zs = _read_json("alexandrie_data/HE3-LANDAU/zero_sound_real_he3.json")
    for z in zs["results"]:
        if float(z["P_bar"]) == P:
            out["sound_m_per_s"] = {k: z[k] for k in ("c0_F0_only", "c0_F0_F1", "c1_landau", "c0_over_c1")}
            out["sound_note"] = ("c0_F0_only < c1 shows the one-parameter model is wrong on real 3He; "
                                 "with F1s, c0 > c1 as observed")
    return out


def helium_kinematics(pressure_bar=None):
    """Committed results of experiment E5: machine-checked helium-4 kinematics tested on the
    Godfrin et al. PRB 103, 104516 (2021) IN5 dispersion data (arXiv:2012.09067 ancillary files).
    With pressure_bar: that pressure's maxon-vs-2*Delta and three-phonon rows. Without: everything."""
    d = _read_json("alexandrie_data/HE4-KIN/helium_kinematics.json")
    if pressure_bar is None:
        return d
    P = float(exact(str(pressure_bar) if isinstance(pressure_bar, (int, float)) and not isinstance(pressure_bar, bool)
                    else pressure_bar, "pressure_bar"))
    t2 = [r for r in d["T2_maxon_vs_2delta"] if abs(r["P_bar"] - P) < 1e-9]
    if not t2:
        raise InputRefused(f"no data at {P} bar; available: {[r['P_bar'] for r in d['T2_maxon_vs_2delta']]}")
    return {"source": d["source"], "P_bar": P, "maxon_vs_2delta": t2[0],
            "three_phonon": [r for r in d["T1_three_phonon"] if abs(r["P_bar"] - P) < 1e-9],
            "outcome": d["outcome"]}


# ------------------------------------------------------------------------ Theorem 22.6 tool
def theorem_22_6_bound(d=3, nu="3/2", weight="tuned", angles=12):
    """Numerical kernel comparison behind the worked examples after Theorem 22.6 of Villani,
    arXiv:2501.00925 (independent Python implementation, verification/theorem_22_6/kernels.py).
    Compares the symmetrised inverse-power-law collision kernel (angular singularity nu, dimension
    d) with a subordinated heat kernel; returns m/M, Lambda_b and the bound 2 sqrt(Lambda_b m/M).
    weight: 'tuned' (the notes' weights, d = 2 or 3) or 'fractional_laplacian'.
    Floating point (external numerical check). Default grid takes ~1-3 s; angles <= 60."""
    import math
    sys.path.insert(0, str(ROOT / "verification" / "theorem_22_6"))
    import kernels as K

    if d not in (2, 3, 4):
        raise InputRefused("d must be 2, 3 or 4")
    nu_f = float(exact(nu, "nu")) if not isinstance(nu, float) else float(nu)
    if not 0 < nu_f < 2:
        raise InputRefused("nu must lie in (0, 2)")
    if not isinstance(angles, int) or not 3 <= angles <= 60:
        raise InputRefused("angles must be an integer in 3..60")
    if weight == "tuned":
        if d == 4:
            raise InputRefused("the notes give tuned weights for d = 2, 3 only; use 'fractional_laplacian'")
        w = K.weight_tuned_d3(nu_f) if d == 3 else K.weight_tuned_d2(nu_f)
    elif weight == "fractional_laplacian":
        w = K.weight_fractional_laplacian(nu_f)
    else:
        raise InputRefused("weight must be 'tuned' or 'fractional_laplacian'")
    with _quiet():
        r = K.compare(nu_f, d, w, P=angles)
    return {"d": d, "nu": nu_f, "gamma": 1 - 2 * nu_f if d == 3 else None, "weight": weight, "angles": angles,
            "m_over_M": r["ratio"], "M_over_m": r["M_over_m"], "lambda_b": K.lambda_b(nu_f, d, w),
            "bound": r["bound"], "theta": [float(x) for x in r["theta"]],
            "ratio_sub_over_col": [float(x) for x in r["sub"] / r["col"]],
            "notes": ["Claims in the notes: d=3 bound >= 4.3, d=2 bound > 3.3 with the tuned weights.",
                      "Sampling angles can only overestimate m/M; see EXPERIMENTS.md E1 for dense grids.",
                      "Do not compare with this project's gamma_bound = m_r/M_r + 3/2: different object (RETRACTIONS R8)."]}


# ------------------------------------------------------------------------ repository tools
def list_protocols():
    """The engine's protocols as listed in PROTOCOL_REGISTRY.md, with their verification scripts."""
    text = (ROOT / "PROTOCOL_REGISTRY.md").read_text()
    protos = [{"id": m.group(1), "title": m.group(2).strip()}
              for m in re.finditer(r"^## Protocol ([\w.-]+):\s*(.+)$", text, re.M)]
    return {"protocols": protos,
            "verifications": {k: {"script": v[0], "needs_network": v[1], "checks": v[3]}
                              for k, v in VERIFICATIONS.items()},
            "see_also": ["ROADMAP.md", "RETRACTIONS.md", "verification/THEORY_EXPERIMENT_LINKS.md"]}


def get_retractions(entry=None):
    """Entries of RETRACTIONS.md: claims this project has withdrawn and must not be re-made.
    Without an argument, the list of ids and titles; with entry='R8', that entry's full text."""
    text = (ROOT / "RETRACTIONS.md").read_text()
    parts = re.split(r"^(?=## R\d+)", text, flags=re.M)[1:]
    entries = {}
    for p in parts:
        m = re.match(r"## (R\d+)\s*[—-]\s*(.+)", p)
        if m:
            entries[m.group(1)] = {"title": m.group(2).strip(), "text": p.strip()}
    if entry is None:
        return {"entries": [{"id": k, "title": v["title"]} for k, v in entries.items()],
                "rule": "Before claiming a result, check it is not one of these."}
    if entry not in entries:
        raise InputRefused(f"unknown entry {entry!r}; available: {list(entries)}")
    return {"id": entry, **entries[entry]}


def run_verification(name):
    """Run one whitelisted verification script and return its exit code and output tail.
    Names: see list_protocols()['verifications']. No arguments are passed; no other script can be run."""
    if name not in VERIFICATIONS:
        raise InputRefused(f"unknown verification {name!r}; allowed: {sorted(VERIFICATIONS)}")
    script, needs_net, timeout, checks = VERIFICATIONS[name]
    if needs_net and not ALLOW_NETWORK:
        raise InputRefused(f"{name} downloads data; start the server with AGORA_MCP_ALLOW_NETWORK=1 to allow it")
    env = {k: v for k, v in os.environ.items() if k in ("PATH", "HOME", "LANG", "LC_ALL", "PYTHONPATH")}
    env["MPLBACKEND"] = "Agg"
    try:
        p = subprocess.run([sys.executable, str(ROOT / script)], cwd=ROOT, env=env, capture_output=True,
                           text=True, timeout=timeout, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return {"name": name, "script": script, "passed": False, "error": f"timed out after {timeout} s"}
    out = p.stdout + ("\n[stderr]\n" + p.stderr if p.stderr.strip() else "")
    return {"name": name, "script": script, "checks": checks, "exit_code": p.returncode,
            "passed": p.returncode == 0, "output_tail": out[-6000:]}


TOOLS = [zero_sound_root, pade_approximant, he3_landau_parameters, helium_kinematics,
         theorem_22_6_bound, list_protocols, get_retractions, run_verification]


# ----------------------------------------------------------------------------- MCP wiring
def build_server():
    from typing import Optional, Union

    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("agora-physics", instructions=(
        "Exact-rational kinetic-physics engine (SocrateAI Agora). Pass Landau parameters and other "
        "exact inputs as strings like '93/10'; floats are refused. Check get_retractions before "
        "claiming a result. Numbers from theorem_22_6_bound are floating-point numerical evidence, "
        "not proofs."))

    Num = Union[str, int, float]  # float accepted by the schema only so it can be refused with a clear message

    @mcp.tool(name="zero_sound_root", description=zero_sound_root.__doc__)
    def zero_sound_root_tool(F0s: Num, F1s: Num = "0", M: int = 4) -> dict:
        return zero_sound_root(F0s, F1s, M)

    @mcp.tool(name="pade_approximant", description=pade_approximant.__doc__)
    def pade_approximant_tool(M: int = 2) -> dict:
        return pade_approximant(M)

    @mcp.tool(name="he3_landau_parameters", description=he3_landau_parameters.__doc__)
    def he3_landau_parameters_tool(pressure_bar: Num) -> dict:
        return he3_landau_parameters(pressure_bar)

    @mcp.tool(name="helium_kinematics", description=helium_kinematics.__doc__)
    def helium_kinematics_tool(pressure_bar: Optional[Num] = None) -> dict:
        return helium_kinematics(pressure_bar)

    @mcp.tool(name="theorem_22_6_bound", description=theorem_22_6_bound.__doc__)
    def theorem_22_6_bound_tool(d: int = 3, nu: Num = "3/2", weight: str = "tuned", angles: int = 12) -> dict:
        return theorem_22_6_bound(d, nu, weight, angles)

    @mcp.tool(name="list_protocols", description=list_protocols.__doc__)
    def list_protocols_tool() -> dict:
        return list_protocols()

    @mcp.tool(name="get_retractions", description=get_retractions.__doc__)
    def get_retractions_tool(entry: Optional[str] = None) -> dict:
        return get_retractions(entry)

    @mcp.tool(name="run_verification", description=run_verification.__doc__)
    def run_verification_tool(name: str) -> dict:
        return run_verification(name)

    for uri, rel, desc in (("agora://roadmap", "ROADMAP.md", "Project roadmap and open gaps"),
                           ("agora://protocol-registry", "PROTOCOL_REGISTRY.md", "Protocol definitions"),
                           ("agora://retractions", "RETRACTIONS.md", "Withdrawn claims"),
                           ("agora://theory-experiment-links", "verification/THEORY_EXPERIMENT_LINKS.md",
                            "Map between Lean theorems and experiments")):
        def _make_reader(path):
            def _reader() -> str:
                return path.read_text()
            return _reader
        mcp.resource(uri, name=rel, description=desc, mime_type="text/markdown")(_make_reader(ROOT / rel))
    return mcp


def main():
    build_server().run("stdio")


if __name__ == "__main__":
    main()
