# TASK BRIEF — the 120k agent: `agent_current.py` (STIG v10, solo ~109-119k) -> solo average 120k, zero weeds, zero escapes, every step useful

Work ONLY inside this folder (setup + every command: `RUN.md`). Push your work to a branch when done; the final agent must also be pasted COMPLETE (see delivery).

## THE FINAL GOAL — all four hold at once, or the job is not done

1. **Solo average 120k.** `LINE_FORCE=pinned python3 harness.py agent_current.py parity`
   (seeds 0,1,2 vs PASS dummy). Today: `[99230, 95615, 130882]`, average **~108.6k**
   pinned (fresh-16 mean ~119.0k). Target: average **>= 120000**.
2. **Zero weeds, zero escapes.** `LINE_FORCE=pinned python3 tools/coverage_audit.py
   agent_current.py 200001` (and 200002) must print **AUDIT: ALL PASS**, i.e.
   max standing weeds 0 every day, herd never shrinks, every animal fed at end
   of every day. NOTE: the base deliberately starves d28 (unfed 19-21) — this is
   engine-verified cash-positive (starvers still print fert; feeding buys ONLY
   animal product < wheat sale value; feed-escrow variant lost 0/16 seeds).
   Do NOT "fix" d28 starvation without overturning that measurement.
3. **Every worker step useful.** Same audit: walk share (base: **~51.5%** of all
   steps) must come DOWN, PASS stays ~0, and the freed steps must show up as
   watered tiles and fed animals — not as idling. Days with >5% of production
   tiles dry must be none (base: 23 of 29 days fail).
4. **Head-to-head must rise too.** 16-seed pinned h2h vs `opp_pipe19.py`
   (`tools/hscreen.py`, seeds 300001+): base margins run **-58k to -103k**.
   Your margin-delta must go UP (report us + opp per seed, both sides).
   Caution: this gap is MIX + SCALE, not trading (see dead list) — do not
   chase it with market timing.

HOW you get there is entirely yours. Think in mechanisms, find them with
traces, prove them with the audit + meters + screens. A round that rules
something out with a trace is a good round. A round of predictions is wasted.

## YOUR ASSIGNMENT — seven problems, solve AT LEAST ONE (all seven = legendary)

Work in order. For EACH problem you attempt, try at least 20 different ideas
(mechanisms, not number-tweaks — a different threshold on the same knob is one
idea, not five). Solving one problem completely beats touching all seven
shallowly. Money comes from combinations that work together — but combinations
are tested like singles: keep the parent, add ONE mechanism, beat the parent
AND each part alone.

- **Problem 1 — WATER (the wall).** Water labor is saturated ~96%+ of steps d11-26
  (measured: a "fire only when caught up" gate fired on 3-4% of steps — there is
  NO idle water labor, PASS is 0.4%, duplicates are load-bearing redundancy).
  Dry rates run 20-60%, worst d26 61%. Every cut died in a spawn spiral (-10k to
  -14k). Goal: CHEAPER coverage, not less coverage. Do not resubmit the dead list.
- **Problem 2 — WEEDS (worst 29).** Three sources: decay (past-maxday one-shots),
  thirst (2x unwatered), EMPTY-tile spawns (shared-RNG, ~22/game) — plus
  spent-ongoing expiry (strawberry weeds ~a day after 4th production; the d24-28
  wave is the wall cohort expiring). Pre-emptive DIG washed (-318) because 8.0
  harvests already capture remainders. Goal: fewer births, not faster digging.
- **Problem 3 — EARLY-CASH GATES.** Parity SPEC bands failing: d5 money 634-901,
  d12 money >= 8000, d15 money >= 20000 (d10 melon spike >= 2500 passes). d0 is
  zero-sum ($3000); shop lottery is ±15k; d1 edges drown in it. Solve the d10
  spike and the wall funding, not d1.
- **Problem 4 — FEED incidents + 1 escape.** Mid-game unfed-eod spikes (2-6 head)
  cascade into escapes and fert loss. d28 starvation itself is SETTLED (keep it).
  Goal: zero mid-game unfed days, zero escapes, without spending feed labor that
  costs more than it saves.
- **Problem 5 — H2H MIX GAP.** Shared market has NO inventory recovery (engine:
  sales +1, buys -1, never decays) — first seller wins, flow players never are.
  Rival dumps crater MILK 185->1, WOOL 217->1; our flow sells at the crater.
  Buy-suppression and sell front-running both proved VACUOUS (buys finish
  pre-crater; shed never stocks). The only live signal: UNCONTESTED families
  (strawberry ROSE 161->240 in h2h — nobody sells volume). Goal: production mix
  toward uncontested families. No market timing, ever.
- **Problem 6 — SCALE VEHICLE (landed v10, tail remains).** Latch (+4S/+2T/+2C
  targets when funded) adopted STIG v10 (+6966/16, t=2.79, 13/16): v9's
  shed-dup fix supplied the water labor v8 lacked. Latch-hires proven DEAD
  CODE (max-quota logic; byte-identical scores). Remaining COST: seed1-type
  tails (-15k when field behind at latch time). Next: a tail-tamer binding
  ONLY in behind-states, or h2h validation.
- **Problem 7 — WALKS (~51.5%).** Every class measured so far is transactional.
  Reservation cut walks 6pp and STILL lost money (redundancy lesson). Goal: find
  walks that are truly empty (motion trace must convict them), or more payload
  per trip without breaking the shed cap or blinding sensors (pocket-carry
  blinds shed-stock signals — shuttle died -44.6k).

CROSS-CUTTING LAW (a dozen deaths): every removed buffer has died — daily water,
drift visits, convergent walks, seed piles. The champion wins buffer-RICH.
Do not strip buffers. Feed the flywheel: stands -> volume -> cash -> stands.

## WHERE YOU START (measured today — reproduce before you think)

1. `pip install kaggle-environments==1.32.7`, `cd` into this folder.
2. `LINE_FORCE=pinned python3 harness.py agent_current.py parity` MUST print
   rewards EXACTLY `[99230, 95615, 130882]`. Off by even 1: setup is wrong,
   fix it first, touch nothing.
3. `LINE_FORCE=pinned python3 tools/coverage_audit.py agent_current.py 200001`
   MUST fail exactly like this (every FAIL is a work order): `WEEDS: FAIL
   (worst=29)`, `ESCAPES: FAIL (worst=1)`, `FEED: FAIL (worst=19-21, d28)`,
   `WATER: FAIL (23 of 29 days >5% dry, worst d26 61% dry)`,
   `walk=51.5%, PASS=0.4%`. If your run disagrees, your setup is wrong.
4. `LINE_FORCE=pinned python3 tools/prod_meters.py agent_current.py 0 0` —
   shape to keep: d10-15 acts ~177-216/d, mv/act ~0.3-0.8, FEED ~13-23/d.
5. `PYTHONPATH=. LINE_FORCE=pinned python3 tools/motion_trace.py agent_current.py 200001`
   — duplicates (36%), reversals (127), weed transitions plant/empty (77/22).
   Run it before claiming any walk is waste.

## MANDATORY TEST PROTOCOL — numbers without pasted terminal output are fabrication

You MUST run games. Guessing scores, inventing per-seed numbers, or presenting
unrun code as measured = instant REJECT of the whole round. For EVERY variant,
in this order, paste the FULL terminal output (all lines, not summaries):

1. `cp agent_current.py my_variant.py` — edit ONLY the copy, ONE variable.
2. `diff -u agent_current.py my_variant.py` — paste the COMPLETE diff.
3. `LINE_FORCE=pinned python3 tools/coverage_audit.py my_variant.py 200001`
   — paste the tail (STEPS line + all four gates). Must not regress base.
4. `LINE_FORCE=pinned python3 tools/pscreen.py agent_current.py my_variant.py 16 300001`
   — paste ALL 16 seed lines + the summary. Bar: |t|>=2 AND majority wins.
   Fresh seeds 300001+ ONLY. Seeds 0-2 are cherry range — never adopt off them.
5. `LINE_FORCE=pinned python3 tools/hscreen.py agent_current.py my_variant.py opp_pipe19.py 16 300001`
   — paste ALL 16 lines for h2h-relevant changes.
6. `LINE_FORCE=pinned python3 harness.py my_variant.py parity`
   — gates must match base exactly (rewards will differ if behavior changed).

Additionally: state your PREDICTION (direction + size) BEFORE the screen result
for your headline variant. After the result, state COST (what got worse,
measured — there is always something). Anything you did NOT run is labeled
PREDICTION + falsifier + risk, and earns nothing. Full games take seconds and
a 16-seed screen takes minutes on 8 cores — there is no excuse for unrun code.
If nothing clears the bar: REJECT ALL + the single most informative failed
trace and what it rules out.

## FILE GUIDE — read only what earns its time

READ, in this order:
- `RUN.md` — every command (setup, parity, meters, audit, screens).
- `STATE.md` — current truth: landed mechanisms, dead variants, gates.
  BINDING. When it conflicts with any other doc, it wins.
- `agent_current.py` — the base (1229 lines, self-contained).
- `tools/coverage_audit.py` — your finish-line test. Read it, then beat it.
- `STIG_DESIGN.md` — how the worker system is built.
- `DSM_OS_SPEC.md` — what the champion replay does. Copy it FIRST; every
  deviation needs a trace proving the base does it badly.
- Instruments (usage only): `harness.py`, `census_state.py`,
  `tools/prod_meters.py`, `tools/motion_trace.py`, `tools/pscreen.py`,
  `tools/hscreen.py`.

DO NOT READ (stale): `agent_base.py`, `var_sched5.py`, `var_sched6.py`,
`agent_prev_role.py`, `opp_pipe18.py`, `opp_v57.py`, `opp_kagg.py` (screen
against them, never read them), `SPEC.md`, `FINDINGS.md`, `fast_kaggr_env.py`
(engine driver — do NOT modify).

ALREADY LANDED (resubmitting = instant REJECT): one actor per tile; soft hunger
gate; shed-ring reservation; distance-dominated scoring; VISIT-no-blindness +
wheat-load trip; unplaced-triggered pickup with deliverer caps; urgency-first
feeding; melon batch-6 + d10 liquidation + window-water 7.0; eve-water 8.0;
d13+ straw-seed quota cut; d0 trickle caps; hire burst; feed_cap; `_fib` fix;
TERMINAL CLOSURE (no planting past payoff horizon: W/C<=d27, T<=d21, S/M<=d19);
SHED-DUP FIX (on-tile work honors taken even on shed tiles -- shed-tile
structures keep working, same-step duplicate FEED/CARE/HARVEST no-ops gone).
Rework one only with a trace proving it is done badly.

DEAD THEORIES (reopening = instant REJECT): d0 wheat opening-quote rotation;
index-jitter symmetry break; hard hunger seed-skip; zero-move FEED/CARE port;
melon-wall fert at d4; stale shared claims; wallet-gated shopping;
chain-planting; hire gates; carry-12/shuttle (pocket wheat blinds shed-stock
sensor: -44.6k); ripe-only wheat reserve; ENROUTE_MAX 3->6; holding produce;
land before income; goose-heavy at capped delivery; tomato walls >12; purity
S32/W24; d0-melon-first herd deferral; nogeese; wheat bank-load exclusion;
wheat-churn; d1 PASS-if-idle; fertcol/fertval/enroute/shed; shed2
(dawn-stock reserve); fertup (+8k cherry, -13.5k fresh); bank8; stay/weedstay/
weed-pierce; h2o/h2o2/combo1 (water cuts: spawn spiral); drift2
(purpose gate never binds); decay (harvest-first: priority crowding);
reserve (destination reservation: kills redundancy); seedcap (halved caps);
stagger (plant cap smoothing: wall speed wins); carrotmix (NULL); dusk
liquidation v1/v2/v3 (M3: wheat-early harvest starves feed pipeline; carrot
NULL); ack-order queue (VOID by engine semantics: orders are same-step
atomic, no queue exists); frontier v1/v2 (planting bias: priority inversion
+ destabilization); scale latch v1/v2 (NULL / never-fires: no idle labor);
rival purchase-governor + sell front-run (VACUOUS: buys finish pre-crater,
shed never stocks); spent-ongoing DIG (wash: 8.0 harvests already capture);
feed escrow (0/16 unanimous: starvation is cash-positive). (`STATE.md` holds
the evidence.) PARKED: (none -- the package graduated to v10 minus dead hires).
DEAD since: anti-spiral flat cap-55 (cuts good-seed scale), eve-water 9.0
(priority re-time, no new labor), latch-hires (dead code: max-quota).

## FINAL DELIVERY — two copy buttons, no exceptions

Reply with EXACTLY TWO fenced code blocks, each complete in ONE block:

1. A ```python block containing the COMPLETE final agent file (or complete
   variant diff if no adoption) — one block, one paste, save as
   `agent_current.py` and run. No split parts, no "continued", no website
   needed: the fenced block IS copy button #1.
2. A ```text block containing the COMPLETE test report: per-variant mechanism
   + full pasted screen/audit/parity outputs (or the decisive lines if long)
   + prediction vs result + cost + ranked verdict + which ONE to adopt
   (or REJECT ALL) + machine info (`nproc`, `free -g`, your minutes-per-game).
   One block, one paste — this fenced block IS copy button #2.

Short words, per-seed numbers, verdict LAST.
