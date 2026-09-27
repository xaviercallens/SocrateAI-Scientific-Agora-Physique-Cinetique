## What changed

<!-- One focused change. Link the issue: Closes #NN. Cite a roadmap ID (RM-nn) if applicable. -->

## Claims and evidence level

<!-- Every new claim with its level: 1 exact computation, 2 independent validation, 3 Lean proof, 4 data comparison. -->

| Claim | Level | Where checked |
|---|---|---|

## Commands run

```
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/ -q
```

## Checklist

- [ ] Tests green; CI verification scripts still run
- [ ] No floats in `agora_swarm/` derivations; no numbers typed from memory
- [ ] No retracted claim re-introduced (RETRACTIONS.md); retractions propagated repo-wide if any
- [ ] Lean (if touched): `lake build` clean, `#print axioms` without `sorryAx`
- [ ] Agent-authored? Name the agent (e.g. Co-Authored-By trailer)
