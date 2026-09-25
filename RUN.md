# RUN — setup + how to run games

## 0. One-time setup (2 min)
- Python 3.8+ (we use 3.12.3). No other system deps.
- `pip install kaggle-environments==1.32.7`  (the ONLY dependency;
  `fast_kaggr_env.py` drives its official kaggriculture interpreter directly,
  ~33x faster than the framework path, bit-exact trajectories).
- `cd` into this folder. Everything resolves relative paths — no editing needed.

Verify the engine import (must print no assertion error):
```
python3 -c "import fast_kaggr_env as f; print(f.FastKaggrEnvPy)"
```

## 1. Files
- `agent_current.py` — the agent you improve. Self-contained (stdlib only),
  exposes `agent(observation, configuration)`. Optional `REPORT()` telemetry.
  `LINE_FORCE` env var pins the species line (`mixed|cow+|sheep`); unset = shop-drawn.
- `fast_kaggr_env.py` — engine. Do NOT modify (parity-gated against official).
- `harness.py` — matrix vs opponents + parity gates. Your main tool.
- `ab_pin.py` — pinned A/B of two variants vs opp_pipe19 (seat 1).
- `census_state.py` — per-day money/herd/shed/seeds/plants (the falsifier instrument).
- `opp_pipe19.py opp_pipe18.py opp_kagg.py opp_v57.py` — opponents, strongest first.
  Screen vs pipe19; confirm the winner vs pipe19 + pipe18.
- `var_sched6.py var_sched5.py agent_base.py` — lineage (what each change did).
- `SPEC.md FINDINGS.md STATE.md` — read in that order; STATE.md wins on conflicts.

## 2. Commands (run from this folder)
Setup check — MUST reproduce these exact numbers before changing anything
(~4 min, 3 games vs PASS dummy):
```
python3 harness.py agent_current.py parity
```
Expected: rewards `[57255, 66496, 62566]`, gates d2-herd/d5-herd/d6-herd+land PASS x3,
d10 PASS on seed 0 / FAIL on seeds 1-2, d0-plants/d12/d15 FAIL (see STATE.md).
If your numbers differ by even 1, your setup is wrong — stop and fix it,
do not "improve" the agent.

Screen a variant (3 seeds, pinned, vs pipe19, ~6 min):
```
LINE_FORCE=pinned python3 ab_pin.py pinned agent_current.py my_variant.py 200001 200002 200003
```
Report all 6 lines (A x3 + B x3), never the average alone.

Full matrix (2 seeds x 4 opps x 2 seats = 16 games, ~30 min, winner only):
```
python3 harness.py my_variant.py
```

Mechanism check (1 game, ~2 min):
```
python3 census_state.py 200001 my_variant.py
```

Timing: ~1-3 min/game (pure Python). Budget: screen on 200001-200003 ONLY;
5-seed confirm (200001-200005) for the winner only. Max 3 variants per round.

## 3. Rules for variants
- ONE variable per variant, always diffed against `agent_current.py`
  (`diff -u agent_current.py my_variant.py`), paste-ready complete diff.
- Cite `agent_current.py:<line>` for every code claim.
- Label anything you did NOT run PREDICTION + one falsifier
  (`census_state.py` line that would prove you wrong).
- STATE.md constraints + rejected list are binding.
