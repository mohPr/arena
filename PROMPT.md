# TASK BRIEF — beat the DSM champion: `agent_current.py` (~62k, margin −120.5k) -> ~107k and positive

Repo: https://github.com/mohPr/arena.git — `git clone` it, work ONLY inside it.

## STEP 0 — reproduce before you think
1. `pip install kaggle-environments==1.32.7`, `cd` into the repo.
2. Run `python3 harness.py agent_current.py parity` and confirm rewards
   EXACTLY `[57255, 66496, 62566]`. If off by even 1, your setup is wrong — fix it first.
3. Read in this order: `RUN.md`, `STATE.md`, then `SPEC.md`, `FINDINGS.md`,
   then `agent_current.py`, then lineage `var_sched6.py`/`var_sched5.py`.

## THE SCOREBOARD (measurements — moving them is your job; HOW is entirely up to you)
- Production vs PASS dummy: `[57255, 66496, 62566]`. Gates: d2/d5-herd, d6-herd+land
  PASS x3; d10 PASS seed 0, FAIL seeds 1-2; d0-plants/d12/d15 FAIL (STATE.md).
- Competitive vs `opp_pipe19.py`, seed 200001: **27385 vs 147891 both seats
  (margin −120506)**. Frozen tape on the same seed: margin −1838.
  The ~118.7k gap lives in OUR agent. That is the result we want closed.
- DSM reference rates (SPEC.md/FINDINGS.md): d0 2C+3S + melon wall; d5 money 634-901;
  d6 land + wave; d10-15 melon spike ($3k->$26k); d15 herd 20-30; ~95 units sold/day;
  ~20+ feeds/day with the crew we feed ~13 with; CARE 0.12 moves/act vs our 0.82.
- Open shortfalls, by cash size (data, not instructions — attack where YOUR traces
  point, in whatever order you choose): d12 ~$4k vs $8k / d15 ~$4-7k vs $20k;
  feed delivery ~13/day vs 20+; d0 plants 11 vs 15; geese 0-2 vs 8-10;
  CARE cost, sale volume, wheat scale, land discipline.

## ALREADY LANDED (in the base — resubmitting any of these is instant REJECT)
Urgency-first feeding (cu>=1 before cu=0); melon sale batch 6; d2/d3 melon catch-up;
farmer d1 fert pull; d0 trickle caps; hire burst; feed_cap; `_fib` fix.
If you believe one of these is done badly, prove it with a trace first — a variant
that re-lands them without proof is rejected unread.

## DEAD THEORIES (tested negative or byte-identical — reopening is instant REJECT)
Stale shared claims; wallet-gated shopping; chain-planting; hire-gates; carry-12;
ripe-only wheat reserve; ENROUTE_MAX 3->6; holding produce for price; land before
income; goose-heavy herds at current delivery; tomato walls >~12 standing;
var_fertcol / var_fertval / var_enroute / var_shed executor variants.

## YOUR JOB — find mechanisms nobody has named
We will not tell you what to try. The scoreboard, the landed list and the dead list
are everything we know, and our hints have run out — the last round's winner simply
re-derived our own fix. New cash must come from a mechanism YOU discover through
traces and census lines, not from reshuffling landed fixes or from clever shapes
with no meter reading behind them.

## RESULT BAR (no exceptions, no partial credit)
- ADOPT requires ALL of: (1) a mechanism trace showing the block BEFORE the fix;
  (2) a 3-seed pinned screen (`LINE_FORCE=pinned ... ab_pin.py` vs `opp_pipe19`,
  seeds 200001-200003) beating the base TOTAL by >=5000 with no seed worse than -2000;
  (3) a falsifier (`census_state.py` line that would prove you wrong) that did NOT print;
  (4) a stated COST (what got worse: water/acts/moves, measured or predicted).
- If nothing clears the bar, return REJECT ALL plus the single most informative
  failed trace and what it rules out. A round that rules something out is a good
  round. A round of predictions is a wasted round.
- Max 3 variants per round, ONE variable each, always `diff -u agent_current.py`.
  5-seed confirm (200001-200005) for the winner only.
- NEVER present unrun numbers as measured. Unrunnable = PREDICTION + falsifier +
  risk, and predictions NEVER earn ADOPT.
- STATE.md constraints are binding. Short answers, simple words. Every score per
  seed — never the average alone.

## Output format (exact, nothing else per variant)
### Variant N: <name> — ADOPT / SCREEN / REJECT (you rank them, we decide)
MECHANISM: <what changes in the game, 3 sentences max, with trace/census evidence>
DIFF: <complete unified diff vs agent_current.py, paste-ready>
CITES: <agent_current.py:line for every code claim>
SCREEN: <the exact ab_pin.py command + all 6 per-seed lines, or PREDICTION + falsifier + risk>
COST: <what got worse (water/acts/moves), measured or predicted>

Final verdict last: ranked list + which ONE to adopt (or REJECT ALL) + the single
fact you would check next. The gap is ~119k. We pay for mechanisms with meter
readings, not for ideas.
