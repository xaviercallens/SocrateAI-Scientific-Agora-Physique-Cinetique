# Local MCP server: `agora-physics`

`agora_mcp/` is a [Model Context Protocol](https://modelcontextprotocol.io) server. It runs over
stdio on your own machine and lets an AI agent or other MCP client call the engine and read the
committed results directly, instead of reimplementing them. Each tool is a thin wrapper over code
or data already in this repository. It adds no physics.

## Requirements

Python 3.10 or later, with the repository's requirements plus the MCP SDK:

```bash
pip install -r requirements.txt   # includes mcp>=1.20,<2 (the server uses the 1.x FastMCP API)
python3 -m agora_mcp        # starts the server on stdio; normally a client starts it for you
```

## Tools

| tool | arguments | returns |
|---|---|---|
| `zero_sound_root` | `F0s`, `F1s="0"`, `M=4` (M from 1 to 8) | exact root `u = 1/s²` and `s`, the dispersion polynomial, 30-digit numerics |
| `pade_approximant` | `M=2` | exact `[M/M]` Padé `P/Q` of the Landau kernel, with its coefficients |
| `he3_landau_parameters` | `pressure_bar` (an integer from 0 to 29) | F₀ˢ, m\*/m, F₁ˢ and provenance; c₀ and c₁ where computed |
| `helium_kinematics` | `pressure_bar=None` | the committed E5 results on the Godfrin et al. 2021 IN5 data |
| `theorem_22_6_bound` | `d=3`, `nu="3/2"`, `weight="tuned"`, `angles=12` | m/M, Λ_b and the bound 2√(Λ_b·m/M) |
| `list_protocols` | none | protocols, and the verification scripts the server may run |
| `get_retractions` | `entry=None` (e.g. `"R8"`) | withdrawn claims, which must not be re-made |
| `run_verification` | `name` | exit code and output tail of one whitelisted script |

These documents are also available as resources: `agora://roadmap`,
`agora://protocol-registry`, `agora://retractions` and `agora://theory-experiment-links`.

**Pass exact inputs as strings.** `"93/10"`, `"10.279"` and `"12"` are all converted exactly to
rationals. If a JSON float such as `9.3` is sent, the server refuses it with an explanation, just
as the engine raises `ScientificHonestyException`. The exception is `theorem_22_6_bound`: it is a
floating-point numerical check, and `nu` may be sent as a float.

**Timing.** Most calls take less than 3 s. `theorem_22_6_bound` takes about 1 to 3 s at the
default 12 angles and more with a denser grid (at most 60 angles). `run_verification` takes 10 to
100 s depending on the script.

## Safety

- **No shell and no arbitrary code.** `run_verification` accepts only the names in
  `VERIFICATIONS` (`agora_mcp/server.py`). It passes them no arguments and runs them with a
  minimal environment.
- **No network by default.** `helium_kinematics_data` downloads from arXiv, so it is refused
  unless the server was started with `AGORA_MCP_ALLOW_NETWORK=1`.
- **No writes to the repository.** The whitelisted scripts only read committed files. A script
  that downloads data writes only to its cache, `~/.cache/agora`.
- **Fixed paths only.** Files are read only from fixed paths inside the repository.

## Claude Code

The repository root holds `.mcp.json`, which registers the server for anyone who opens the
project in Claude Code. Claude Code asks you to approve project servers the first time:

```json
{
  "mcpServers": {
    "agora-physics": {
      "type": "stdio",
      "command": "python3",
      "args": ["-m", "agora_mcp"],
      "env": {}
    }
  }
}
```

Start Claude Code from the repository root, because the module is imported from there. To
register the server for your user from any directory instead:

```bash
claude mcp add agora-physics --scope user -e PYTHONPATH=/path/to/SocrateAI-Scientific-Agora-Physique-Cinetique \
  -- python3 -m agora_mcp
```

## Gemini CLI

Add this to `~/.gemini/settings.json`, or to `.gemini/settings.json` in the repository:

```json
{
  "mcpServers": {
    "agora-physics": {
      "command": "python3",
      "args": ["-m", "agora_mcp"],
      "cwd": "/path/to/SocrateAI-Scientific-Agora-Physique-Cinetique",
      "timeout": 600000
    }
  }
}
```

## Other clients

Any stdio MCP client can start the server with command `python3`, arguments `-m agora_mcp`, and
the repository root as its working directory, or with `PYTHONPATH` set to it. You can also test
the server by hand:

```bash
npx @modelcontextprotocol/inspector python3 -m agora_mcp
```

## Google Jules and other cloud agents

Google Jules runs in a cloud VM against a clone of the repository. It cannot reach a server on
your machine, so it should follow `AGENTS.md` and call the same code directly, e.g.
`python3 -c "from agora_mcp.server import zero_sound_root; print(zero_sound_root('93/10', M=1))"`.
It can also run the scripts under `verification/` and the test suite
(`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/ -q`).

## Example calls

```jsonc
// tools/call zero_sound_root {"F0s": "93/10", "M": 1}
{"root_found": true, "u_exact": "10/37", "s_exact": "sqrt(370)/10", "dispersion_polynomial": "1 - 37*u/10", ...}

// tools/call zero_sound_root {"F0s": "10.279", "F1s": "5.259", "M": 4}      (real 3He, 0 bar)
{"root_found": true, "model": "F0s and F1s", "s_numeric": "3.33201587517...", ...}

// tools/call zero_sound_root {"F0s": 9.3}
isError: "F0s was sent as a floating-point number (9.3). The engine works exactly over Q ..."

// tools/call he3_landau_parameters {"pressure_bar": 0}
{"F0s": 10.2788, "F1s": 5.2601, "sound_m_per_s": {"c0_F0_F1": 200.07, "c1_landau": 193.18, "c0_over_c1": 1.0357, ...}, ...}

// tools/call theorem_22_6_bound {"d": 3, "nu": "3/2"}
{"bound": 4.3546, "m_over_M": 0.9804, ...}

// tools/call get_retractions {"entry": "R8"}
{"id": "R8", "title": "\"Theorem 22.6\" attribution checked against the source: mismatched", "text": "..."}
```

The tests are in `tests/test_mcp_server.py`. They call every tool in-process and also make a real
stdio JSON-RPC round trip: `initialize`, `tools/list`, `tools/call` and `resources/list`.
