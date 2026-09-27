"""The local MCP server (agora_mcp): tools in-process, then a real stdio JSON-RPC round trip."""
import json
import subprocess
import sys
from pathlib import Path

import pytest
import sympy as sp

pytest.importorskip("mcp")
from agora_mcp import server as S  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


# ------------------------------------------------------------------------------ in-process
def test_zero_sound_root_is_exact():
    r = S.zero_sound_root("93/10", M=1)
    assert r["root_found"] and sp.sympify(r["u_exact"]) == sp.Rational(10, 37)


def test_zero_sound_root_decimal_string_is_exact():
    r = S.zero_sound_root("9.3", M=1)
    assert r["F0s_exact"] == "93/10" and sp.sympify(r["u_exact"]) == sp.Rational(10, 37)


def test_zero_sound_root_with_f1s_on_real_he3():
    r = S.zero_sound_root("10.279", "5.259", M=4)
    assert r["root_found"] and r["model"] == "F0s and F1s"
    assert abs(float(r["s_numeric"]) - 3.33201587517) < 1e-9


@pytest.mark.parametrize("bad", [9.3, True, "9.3e0", "abc", "1/0"])
def test_inexact_or_malformed_inputs_are_refused(bad):
    with pytest.raises(S.InputRefused):
        S.zero_sound_root(bad, M=1)


def test_pade_order_bounds():
    assert S.pade_approximant(1)["Q"] == "1 - 3*u/5"
    with pytest.raises(S.InputRefused):
        S.pade_approximant(S.MAX_PADE_ORDER + 1)


def test_he3_parameters_from_committed_table():
    r = S.he3_landau_parameters(0)
    assert abs(r["F0s"] - 10.2788) < 1e-3 and abs(r["F1s"] - 5.2601) < 1e-3
    assert r["sound_m_per_s"]["c0_over_c1"] > 1 > r["sound_m_per_s"]["c0_F0_only"] / r["sound_m_per_s"]["c1_landau"]
    with pytest.raises(S.InputRefused):
        S.he3_landau_parameters("0.5")  # not tabulated: no interpolation


def test_helium_kinematics_maxon_above_two_delta_at_24_bar():
    r = S.helium_kinematics("24.08")
    assert r["maxon_vs_2delta"]["excess_meV"] > 0


def test_theorem_22_6_bound_reproduces_d3_claim():
    r = S.theorem_22_6_bound(3, "3/2")
    assert r["bound"] >= 4.3


def test_repository_tools():
    assert {p["id"] for p in S.list_protocols()["protocols"]} >= {"QV-01", "QVE-02", "Q-RHK-02"}
    ids = [e["id"] for e in S.get_retractions()["entries"]]
    assert "R8" in ids and "Theorem 22.6" in S.get_retractions("R8")["title"]


def test_run_verification_is_whitelisted():
    with pytest.raises(S.InputRefused):
        S.run_verification("../../bin/sh")
    if not S.ALLOW_NETWORK:
        with pytest.raises(S.InputRefused):
            S.run_verification("helium_kinematics_data")


def test_run_verification_runs_an_offline_script():
    r = S.run_verification("kernel_regularity_bounds")
    assert r["passed"], r["output_tail"]


# ------------------------------------------------------------------------- stdio round trip
class _Client:
    def __init__(self):
        self.p = subprocess.Popen([sys.executable, "-m", "agora_mcp"], cwd=ROOT, stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        self.n = 0

    def send(self, method, params=None, notify=False):
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        if not notify:
            self.n += 1
            msg["id"] = self.n
        self.p.stdin.write(json.dumps(msg) + "\n")
        self.p.stdin.flush()
        if notify:
            return None
        while True:
            line = self.p.stdout.readline()
            assert line, "server closed stdout"
            reply = json.loads(line)  # anything non-JSON on stdout would break the protocol
            if reply.get("id") == self.n:
                return reply

    def close(self):
        self.p.stdin.close()
        self.p.wait(timeout=20)


def test_stdio_round_trip():
    c = _Client()
    try:
        init = c.send("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                     "clientInfo": {"name": "pytest", "version": "0"}})
        assert init["result"]["serverInfo"]["name"] == "agora-physics"
        c.send("notifications/initialized", notify=True)

        names = {t["name"] for t in c.send("tools/list")["result"]["tools"]}
        assert names == {f.__name__ for f in S.TOOLS}

        ok = c.send("tools/call", {"name": "zero_sound_root", "arguments": {"F0s": "93/10", "M": 1}})["result"]
        assert not ok.get("isError")
        payload = ok.get("structuredContent") or json.loads(ok["content"][0]["text"])
        payload = payload.get("result", payload)
        assert payload["u_exact"] == "10/37"

        bad = c.send("tools/call", {"name": "zero_sound_root", "arguments": {"F0s": 9.3, "M": 1}})["result"]
        assert bad["isError"] and "float" in bad["content"][0]["text"]

        res = {r["uri"] for r in c.send("resources/list")["result"]["resources"]}
        assert "agora://retractions" in res
    finally:
        c.close()
