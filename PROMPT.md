# TASK BRIEF — finish the DSM champion: `agent_current.py` (STIG v1, ~90k, margin −117k) -> ~107k and positive, then BEYOND

Repo: https://github.com/mohPr/arena.git — `git clone` it, work ONLY inside it. Push is already done, just clone.

## STEP 0 — reproduce before you think
1. `pip install kaggle-environments==1.32.7`, `cd` into the repo.
2. Run `python3 harness.py agent_current.py parity` and confirm rewards
   EXACTLY `[88793, 90031, 90503]`. If off by even 1, your setup is wrong — fix it first.
3. Run `python3 tools/prod_meters.py agent_current.py 0 0` and confirm the shape:
   d11-15 acts ~150-165/d, mv/act ~0.5-0.9, FEED ~17-24/d. This is the production
   shape — your variants must keep it.
4. Read in this order: `RUN.md`, `STATE.md`, `STIG_DESIGN.md`, `DSM_OS_SPEC.md`,
   then `SPEC.md`, `FINDINGS.md`, then `agent_current.py`, then `agent_prev_role.py`
   (the old 62k role-based base, A/B reference only).

## THE SCOREBOARD (measured, 2026-09-25 — moving them is your job; HOW is entirely up to you)
- Production vs PASS dummy: `[88793, 90031, 90503]`. Gates: d5-herd, d6-land,
  d10 PASS x3; FAIL: d6-herd (5-6 vs 7), d5/d12/d15 money (curve arrives late,
  grinds d20+ instead of spiking d10-15); d0-plants 14 vs 15 is a STALE gate,
  ignore it (`STATE.md` explains why).
- Competitive, seed 200001, `LINE_FORCE=pinned`, opp seat 0 / us seat 1: vs pipe19
  62444 vs 179413 (margin −116969); vs pipe18 and vs v57: same lines (all three
  opps saturate ~179.4k on this seed — margin moves ONLY through YOUR score,
  the opponent is fixed). Old role base same setup: 27385 vs 147891 (margin −120506).
- DSM reference (`SPEC.md` + `DSM_OS_SPEC.md`): d0 2C+3S + melon wall; d5 money
  634-901; d6 land + wave 7-12 head; d10-15 melon spike ($3k->$26k); d15 herd 20-30;
  ~95 sold/day; ~20 feeds/day; acts ~150/d at mv/act 0.74-0.79.
- Open stages, by cash size (data, not instructions — attack where YOUR traces point,
  in whatever order you choose, and finish ALL of them): (1) d6 wave cash — herd 5-6
  vs 7-12, d1-2 feed hole (FEED 0-1, escapes d2-3) cascades into no-milk d2/d4 and a
  late wave; (2) curve timing — melon yields stall 3-5 vs 6 (water/fert coverage d8-12
  on the wall), money grinds d20+; (3) d1 wandering — sparse-work diffusion (mv/act 2-4),
  DSM idles instead of trekking; (4) terminal weeds (~46 by d27-29 on some seeds);
  (5) THEN margin screens on all three opponents and optimization BEYOND DSM (~107k
  is the target to beat, not the ceiling).

## ALREADY LANDED (in the base — resubmitting any of these is instant REJECT)
One actor per tile per step; soft hunger gate (wheat full-cap + seeds trickle-1);
shed-ring reservation; distance-dominated scoring (value − 2*dist, persist 1.5,
radius 3); VISIT-no-blindness + wheat-load trip; unplaced-triggered animal pickup
with deliverer caps (d0: 2, later: 5); urgency-first feeding; melon sale batch 6;
d2/d3 melon catch-up; d0 trickle caps; hire burst; feed_cap; `_fib` fix. If you
believe one is done badly, prove it with a trace first — a variant that re-lands
them without proof is rejected unread.

## DEAD THEORIES (tested negative — reopening is instant REJECT)
d0 wheat opening-quote rotation; index-jitter symmetry break; hard hunger seed-skip;
zero-move FEED/CARE port; melon-wall fert at d4; stale shared claims; wallet-gated
shopping; chain-planting; hire gates; carry-12; ripe-only wheat reserve;
ENROUTE_MAX 3->6; holding produce for price; land before income; goose-heavy at
capped delivery; tomato walls >12; var_fertcol/var_fertval/var_enroute/var_shed.

## YOUR JOB — finish all five stages, then beat DSM, not join it
We will not tell you what to try. The scoreboard, the landed list and the dead list
are everything we know — new cash must come from a mechanism YOU discover through
traces, census lines and `tools/prod_meters.py`, not from reshuffling landed fixes
or shapes with no meter reading. Production meters BEFORE money, every variant: if
`tools/prod_meters.py` shape breaks (acts/day, mv/act, FEED/day, gap-hist), money
will follow — check it first.

## RESULT BAR (no exceptions, no partial credit)
- ADOPT requires ALL of: (1) a mechanism trace showing the block BEFORE the fix;
  (2) production meters kept-or-better PLUS a 3-seed pinned screen
  (`LINE_FORCE=pinned ab_pin.py` vs opp_pipe19, seeds 200001-200003) beating the base
  TOTAL by >=5000 with no seed worse than −2000; (3) a falsifier (`census_state.py`
  line that would prove you wrong) that did NOT print; (4) a stated COST (what got
  worse, measured).
- CONFIRM (winner only): 5 seeds (200001-200005) vs ALL THREE opponents
  (`opp_pipe19.py`, `opp_pipe18.py`, `opp_v57.py`) with `ab_pin_opp.py` — all 30 lines
  (your score + opp score per seed per opp) in the report. A result is REAL only if
  measured against all three. Anything unrun = PREDICTION + falsifier + risk, and
  predictions NEVER earn ADOPT.
- If nothing clears the bar, return REJECT ALL plus the single most informative
  failed trace and what it rules out. A round that rules something out is a good round.
  A round of predictions is a wasted round.
- Max 3 variants per round, ONE variable each, always `diff -u agent_current.py`.
  `STATE.md` constraints are binding. Every score per seed — never the average alone.
  NEVER present unrun numbers as measured.

## FINAL DELIVERY (after the winner confirms on all three opponents)
1. What you did, stage by stage (1-5 + beyond-DSM): mechanism + trace evidence +
   screen lines for each.
2. What you found: the 3 most important facts about this game nobody had written
   down, with file:line or replay proof each.
3. The final agent: COMPLETE file content, and if you present it as a website, that
   page MUST have one copy button that copies the ENTIRE agent code in one click —
   no split blocks, no "part 1/3", one button, one paste, ready to save as
   `agent_current.py` and run.
4. Final verdict last: ranked variants + which ONE to adopt (or REJECT ALL) + the
   single fact you would check next. Short answers, simple words.
