# TASK BRIEF — the 120k agent: `agent_current.py` (STIG v7, solo ~96k) -> solo average 120k, zero weeds, zero escapes, every step useful

Repo: https://github.com/mohPr/arena.git — `git clone` it, work ONLY inside it. Everything you need is already in this folder (setup + commands: `RUN.md`). Push your work to a branch when done; the final agent must also be pasted COMPLETE (see delivery).

## THE FINAL GOAL — all four hold at once, or the job is not done

1. **Solo average 120k.** `LINE_FORCE=pinned python3 harness.py agent_current.py parity`
   (seeds 0,1,2 vs PASS dummy). Today: `[89412, 92105, 105625]`, average **95.7k**.
   Target: average **>= 120000**. That is +24k of REAL cash, measured, per seed
   reported (never the average alone).
2. **Zero weeds, zero escapes.** `LINE_FORCE=pinned python3 tools/coverage_audit.py
   agent_current.py 200001` (and 200002) must print **AUDIT: ALL PASS**, i.e.
   max standing weeds 0 every day, herd never shrinks, every animal fed at end
   of every day (yes, including d28-29 — the base deliberately starves the
   terminal days; decide consciously and defend it or fix it).
3. **Every worker step useful.** Same audit: walk share (base: **51.2%** of all
   steps) must come DOWN, PASS stays ~0, and the freed steps must show up as
   watered tiles and fed animals — not as idling. Every plant watered every day
   it pays (audit: days with >5% of production tiles dry must be none).
4. **Head-to-head must rise too.** 6-seed pinned screen vs `opp_pipe19.py`
   (seeds 200001-200006, `ab_pin_opp.py`): base totals 322459 (you) vs 863411
   (opp). Your total must go UP without the opponent's collapsing from lottery
   (report both sides per seed). Winner confirms vs all three opponents.

HOW you get there is entirely yours. We will not prescribe fixes. Think in
mechanisms (water coverage -> banked yield -> cash timing -> reinvestment ->
more coverage), find them with traces, prove them with the audit + meters +
screens. Swing big: the shop lottery is ±35k/game (see `STATE.md`), so only
real effects survive — this is a filter, not an excuse. A round that rules
something out with a trace is a good round. A round of predictions is wasted.

## WHERE YOU START (measured today — reproduce before you think)

1. `pip install kaggle-environments==1.32.7`, `cd` into the repo.
2. `LINE_FORCE=pinned python3 harness.py agent_current.py parity` MUST print
   rewards EXACTLY `[89412, 92105, 105625]`. Off by even 1: setup is wrong,
   fix it first, touch nothing.
3. `LINE_FORCE=pinned python3 tools/coverage_audit.py agent_current.py 200001`
   MUST fail exactly like this (your starting task list — every FAIL is a work
   order): `WEEDS: FAIL (worst=30)`, `ESCAPES: FAIL (worst=1)`,
   `FEED: FAIL (worst=21, d28)`, `WATER: FAIL (23 of 29 days >5% dry)`,
   `walk=51.2%, PASS=0.4%`. If your run disagrees, your setup is wrong.
4. `LINE_FORCE=pinned python3 tools/prod_meters.py agent_current.py 0 0` —
   shape to keep: d10-15 acts ~177-216/d, mv/act ~0.3-0.8, FEED ~13-23/d.

## FILE GUIDE — read only what earns its time

READ, in this order:
- `RUN.md` — every command you need (setup, parity, meters, audit, screens).
- `STATE.md` — current truth: landed mechanisms, dead variants, gates, the
  lottery methodology. BINDING. When it conflicts with any other doc, it wins.
- `agent_current.py` — the base you improve (1216 lines, self-contained).
- `tools/coverage_audit.py` — your finish-line test. Read it, then beat it.
- `STIG_DESIGN.md` — how the worker system is built (one actor per tile,
  need-2*dist scoring, shed logistics).
- `DSM_OS_SPEC.md` — what the 104k champion replay does (melon wall, d10
  spike, 32-strawberry wall, zero weeds, d29 liquidation).
- Instruments (usage only, not internals): `harness.py`, `ab_pin.py`,
  `ab_pin_opp.py`, `census_state.py`, `tools/prod_meters.py`.

DO NOT READ (stale — opening them wastes your round):
- `agent_base.py`, `var_sched5.py`, `var_sched6.py` — dead lineage.
- `agent_prev_role.py` — old 62k role base, superseded.
- `opp_pipe18.py`, `opp_v57.py`, `opp_kagg.py` — screen against them, never
  read them (same core as pipe19; behavior is measured, not read).
- `SPEC.md`, `FINDINGS.md` — old rate tables, superseded by `STATE.md`.
- `fast_kaggr_env.py` — engine driver. Do NOT modify (parity-gated).

ALREADY LANDED (in the base — resubmitting any of these is instant REJECT):
one actor per tile; soft hunger gate; shed-ring reservation; distance-dominated
scoring; VISIT-no-blindness + wheat-load trip; unplaced-triggered pickup with
deliverer caps; urgency-first feeding; melon batch-6 + d10 liquidation +
window-water 7.0; eve-water 8.0; d13+ straw-seed quota cut; d0 trickle caps;
hire burst; feed_cap; `_fib` fix. Rework one only with a trace proving it is
done badly — otherwise rejected unread.

DEAD THEORIES (tested negative — reopening is instant REJECT): d0 wheat
opening-quote rotation; index-jitter symmetry break; hard hunger seed-skip;
zero-move FEED/CARE port; melon-wall fert at d4; stale shared claims;
wallet-gated shopping; chain-planting; hire gates; carry-12 (kanban: small
loads are a pull system, big loads overstock the 100-cap shed); ripe-only
wheat reserve; ENROUTE_MAX 3->6; holding produce for price; land before
income; goose-heavy at capped delivery; tomato walls >12; purity S32/W24;
d0-melon-first herd deferral; nogeese; wheat bank-load exclusion;
wheat-churn reserve rewrite; d1 PASS-if-idle; var_fertcol/var_fertval/
var_enroute/var_shed. (`STATE.md` has the evidence for each.)

## WORK RULES

- Audit FIRST, before changing code: `coverage_audit.py` failures ARE the task
  list (30 weeds, dry tiles 23/29 days, 51% walking, d28 starvation). Every
  variant must move at least one audit line toward PASS without regressing
  the others — attach before/after audit tails to every variant report.
- Meters BEFORE money, every variant (`tools/prod_meters.py`): if acts/day,
  mv/act, FEED/day break, money will follow — check shape first.
- ONE variable per variant, always `diff -u agent_current.py my_variant.py`.
  Max 3 variants per round. Every score per seed, never the average alone.
- Adopt bar per variant: mechanism trace showing the block BEFORE the fix +
  audit progress + 6-seed h2h total up + parity not down + a falsifier line
  that did NOT print + a stated COST (what got worse, measured).
- NEVER present unrun numbers as measured. Anything unrun = PREDICTION +
  falsifier + risk. Predictions never earn ADOPT.
- If nothing clears the bar: REJECT ALL + the single most informative failed
  trace and what it rules out.

## FINAL DELIVERY

1. Stage by stage: mechanism + trace/audit evidence + screen lines for each win.
2. The 3 most important facts about this game nobody had written down, each
   with file:line or replay proof.
3. The final agent: COMPLETE file content, and if you present it as a website,
   that page MUST have ONE copy button that copies the ENTIRE agent code in
   one click — no split blocks, no "part 1/3", one button, one paste, ready to
   save as `agent_current.py` and run.
4. machine info for our planning: CPU core count (`nproc`), RAM (`free -g`),
   and YOUR measured minutes-per-game on that machine.
5. Final verdict LAST: ranked variants + which ONE to adopt (or REJECT ALL) +
   the single fact you would check next. Short answers, simple words.
