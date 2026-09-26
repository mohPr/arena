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
- `agent_current.py` — the agent you improve (STIG v1, ~90k). Self-contained
  (stdlib only), exposes `agent(observation, configuration)`. Optional `REPORT()`
  telemetry. `LINE_FORCE` env var pins the species line (`mixed|cow+|sheep|pinned`);
  unset = shop-drawn. `agent_prev_role.py` = frozen 62k role-based base (A/B only).
- `fast_kaggr_env.py` — engine. Do NOT modify (parity-gated against official).
- `harness.py` — matrix vs opponents + parity gates. Your main tool.
- `ab_pin.py` — pinned A/B of two variants vs opp_pipe19 (seat 1).
- `ab_pin_opp.py` — pinned A/B vs ANY opponent: `ab_pin_opp.py <line> <A> <B> <opp> [seeds]`.
- `census_state.py` — per-day money/herd/shed/seeds/plants (the falsifier instrument).
- `opp_pipe19.py opp_pipe18.py opp_kagg.py opp_v57.py` — opponents, strongest first.
  Screen vs pipe19; confirm the winner vs pipe19 + pipe18 + v57 (all three, every seed).
- `agent_base.py var_sched5.py var_sched6.py agent_prev_role.py` — lineage.
- `SPEC.md FINDINGS.md` (old rate tables) `DSM_OS_SPEC.md` (replay structure)
  `STIG_DESIGN.md` (this base's design) `STATE.md` — read in that order; STATE.md wins.
- `tools/` — `prod_meters.py` (acts/mv/act/gaps/feeds per day), `tour_mine.py` +
  `chain_mine.py` (replay mining: per-unit tours, chains, bigrams; point at any
  kaggle agriculture replay JSON).

## 2. Commands (run from this folder)
Setup check — MUST reproduce these exact numbers before changing anything
(~4 min, 3 games vs PASS dummy):
```
LINE_FORCE=pinned python3 harness.py agent_current.py parity
```
Expected (pinned, mixed line — THE gate): rewards `[89112, 91805, 105125]`,
gates d5-herd/d6-herd/d6-land PASS x3, d0-plants/d5-money/d10/d12/d15 FAIL
(see STATE.md). Unpinned rewards vary with shop luck (shared-RNG
contamination, STATE.md methodology note) — never gate on unpinned.
If your PINNED numbers differ by even 1, your setup is wrong — stop and fix
it, do not "improve" the agent.

Production meters (1 game, ~3 min — run BEFORE looking at money):
```
LINE_FORCE=pinned python3 tools/prod_meters.py agent_current.py 0 0
```
Expected shape: d1 acts ~39 FEED 4 (shuttle tax mv ~4.7, one day only);
d10-15 acts ~177-216/d, mv/act ~0.3-0.8, FEED ~13-23/d, gap-0 ~67%.
If your variant breaks this shape, money will follow.

Screen a variant (3 seeds, PINNED, vs pipe19, ~6 min):
```
LINE_FORCE=pinned python3 ab_pin.py pinned agent_current.py my_variant.py 200001 200002 200003
```
Report all 6 lines (A x3 + B x3), never the average alone. Adopt bar: base
TOTAL +>=5000 with no seed worse than −2000 (<5k totals are RNG noise).

Confirm the winner vs all three strong opponents (200001-200005, ~30 min):
```
LINE_FORCE=pinned python3 ab_pin_opp.py pinned agent_current.py my_variant.py opp_pipe19.py 200001 200002 200003 200004 200005
LINE_FORCE=pinned python3 ab_pin_opp.py pinned agent_current.py my_variant.py opp_pipe18.py 200001 200002 200003 200004 200005
LINE_FORCE=pinned python3 ab_pin_opp.py pinned agent_current.py my_variant.py opp_v57.py 200001 200002 200003 200004 200005
```
All 30 lines (us + opp per seed per opp) go in the report. Results are only
real if measured against all three.

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
