# TASK BRIEF — close the gap: `agent_current.py` (~55-65k, -120k margin) -> DSM (~107k)

Repo: https://github.com/mohPr/arena.git — `git clone` it, work ONLY inside it.

## STEP 0 — reproduce before you think
1. `pip install kaggle-environments==1.32.7`, `cd` into the repo.
2. Run `python3 harness.py agent_current.py parity` and confirm rewards
   EXACTLY `[57484, 58916, 51435]`. If off by even 1, your setup is wrong — fix it first.
3. Read in this order: `RUN.md`, `STATE.md`, then `SPEC.md`, `FINDINGS.md`,
   then `agent_current.py` (2006 lines), then lineage `var_sched6.py`/`var_sched5.py`.

## The situation (full detail in STATE.md — this is the short version)
- Matrix vs `opp_pipe19.py` seed 200001: we score 31880 vs 151643 (margin -119763, both
  seats). A frozen tape on the same seed scores 109558 vs 111396 (margin -1838).
  The gap is real, in OUR agent, and worth ~118k/game. Production parity (vs PASS dummy)
  is at ~55-65k with gates d5-herd/d6-herd+land/d10 PASS, d0-plants/d12/d15 FAIL.
- DSM reference: d0 2C+3S + melon wall, d5 money 634-901, d6 land+wave, d10-15 melon
  spike ($3k->$26k), d15 herd 20-30, ~95 units sold/day, ~20+ feeds/day with the crew
  we feed ~13 with, CARE at 0.12 moves/act vs our 0.82.

## Work these in order (do not skip P0 — it confounds all measurement)
- **P0 — d1 sheep escape (LIVE REGRESSION, ~-6k).** d2 herd 2C+2S on all parity seeds.
  Trace: d1h20-23, two feeders carry wheat, hungry cu1 sheep 2 walks away, both return
  idle. WARNING: the stale-shared-claim theory was tested and produced byte-identical
  games — it is DEAD. Find the real block with `census_state.py` + per-unit command
  tracing (wrap `FieldExec.animal_work`, print role/pos/inv/claims/command like the
  repo owner did). No fix without a trace showing the mechanism.
- **P1 — melon volume + d12/d15 curve** (d9 tiles 9-11, need 12+; d12 $0.8-3.7k need $8k).
- **P2 — d0 plants 11 vs 15.** **P3 — geese 0-2 vs 8-10** (only with escape-proof
  delivery). **P4 — feed-delivery ceiling** (~13/day vs DSM 20+; best lead: zero-move
  FEED/CARE from pocket when a unit already stands on the structure — our enroute path
  only COLLECTs today). **P5 — wheat scale. P6 — 4th-land discipline.**

## How to think (enforced)
- Think from EVIDENCE, not shape: every claim starts from a trace, census line, or
  replay behavior. Copy what DSM DOES (rates, timing, volumes), not what its code
  looks like. Our executor already differs structurally from DSM — that is fine.
- One variable per variant, always `diff -u agent_current.py my_variant.py`.
  Max 3 variants per round. Screen each on 200001-200003 pinned
  (`LINE_FORCE=pinned ... ab_pin.py`, ~6 min); 5-seed confirm for the winner only.
- Verify through execution: every variant must show a mechanism trace (census/census
  delta or command trace) BEFORE you claim cash. A cash gain with no mechanism is luck.
- State falsifiers: for each variant, one `census_state.py` line that would prove you
  wrong. If it prints that line, say so and revert.
- NEVER present unrun numbers as measured. Unrunnable = PREDICTION + falsifier + risk.
- Respect STATE.md constraints + rejected list. Violating either = instant reject.
- Short answers, simple words. No averages alone — every score per seed.

## Output format (exact, nothing else per variant)
### Variant N: <name> — ADOPT / SCREEN / REJECT (you rank them, we decide)
MECHANISM: <what changes in the game, 3 sentences max, with trace/census evidence>
DIFF: <complete unified diff vs agent_current.py, paste-ready>
CITES: <agent_current.py:line for every code claim>
SCREEN: <the exact ab_pin.py command + all 6 per-seed lines, or PREDICTION + falsifier + risk>
COST: <what got worse (water/acts/moves), measured or predicted>

Final verdict last: ranked list + which ONE to adopt + what to try next.
Think hard. The gap is 118k and every previous round left score flat — find the
mechanism the traces point at, not the change that looks clever.
