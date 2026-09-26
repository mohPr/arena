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

## YOUR ASSIGNMENT — four problems, solve at least one (all four = best result ever)

Work these four in order. For EACH problem you must try at least 20 different
ideas (mechanisms, not number-tweaks — a different threshold on the same knob
is one idea, not five). Solving one problem completely beats touching all four
shallowly. Try hard: this is complex, no single change delivers 120k; money
comes from combinations of changes that work together. But combinations are
tested like singles: keep the parent, add ONE mechanism, compare the combo
against the parent AND against each part alone.

- **Problem 1 — WATER.** Ongoing crops tick yield nightly for free; engine-verified
  watering them banks $0 (see `STATE.md` engine notes). But every cut tested so far
  died in a spawn spiral (skipped tiles open holes, empty tiles spawn weeds by RNG,
  DIG labor can't keep up: -10k to -14k, t up to -5). Goal: full coverage at lower
  cost, or coverage that cannot spiral. Read the dead list first — do not resubmit it.
- **Problem 2 — WALKS.** Audit says 51.2% of steps are moves. Every move class measured
  so far is transactional (mid/late supply shuttles, d0-d1 delivery runs, purposeful
  drift). Coordinator's starting target: ~40% walks, every action useful. Kills so far:
  bank-trip gating, drift-to-PASS, purpose-gated drift, destination reservation (that one
  even cut walks 6pp and STILL lost money — redundancy lesson in `STATE.md`). Find
  walks that are truly empty, or make each trip carry more without breaking the shed cap.
- **Problem 3 — EARLY-CASH.** d0 budget is zero-sum ($3000 fixed); d1 edges (~$500 fert
  cash) drown in shop lottery (±15k). The +8k d1-melon variant was cherry luck (-13.5k
  on fresh seeds). Real early cash must exceed ~10k to be measurable, or compound: the
  d10 spike ($3k -> $26k in DSM) is where early advantages multiply. Spike audit in
  `STATE.md` shows cash locked in seed piles while the wallet starves — but cutting the
  piles starved the planters worse. Solve the spike, not d1.
- **Problem 4 — DECAY.** 8-22 ripe one-shots stand unharvested every dawn (policy waits
  for full yield; engine banks stop at maxday). Harvest-first died by priority crowding
  (-12.5k, all parity gates FAIL): 8.0-priority slots are the scarcest resource. Kill
  decay without spending 8.0 slots, or prove which half of weed births is cheapest to
  prevent (`tools/motion_trace.py` splits plant-origin vs empty-origin transitions).

CROSS-CUTTING LAW (5 deaths and counting): every removed buffer has died — daily water,
drift visits, convergent walks, seed piles. DSM wins buffer-RICH ($13k piles, 75 stands,
water-everything). Do not strip buffers. Feed the flywheel instead: stands -> volume ->
cash -> stands. We sit just below its threshold (~96k vs DSM ~105k solo).

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
5. `PYTHONPATH=. LINE_FORCE=pinned python3 tools/motion_trace.py agent_current.py 200001`
   — the movement trace: duplicate same-step walk intents (base: 1343/3722 = 36%),
   immediate reversals (127), NEW weed transitions split plant-origin (77) vs
   empty-origin (22). Observation-only; run it before claiming any walk is waste.

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
  spike, 32-strawberry wall, zero weeds, d29 liquidation). DSM is the best agent
  alive right now and it is carefully designed — nothing in it is random. Copy it
  FIRST; every deviation needs a trace proving the base does it badly.
- Instruments (usage only, not internals): `harness.py`, `ab_pin.py`,
  `ab_pin_opp.py`, `census_state.py`, `tools/prod_meters.py`,
  `tools/motion_trace.py`, `tools/pscreen.py`, `tools/hscreen.py`.

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
var_enroute/var_shed; var_shed2 (dawn-stock reserve); var_fertup (d0-d1 fert
collection push: +8k cherry, -13.5k fresh); var_bank8 (bank-trip wheat
exclusion); var_stay / var_weedstay (drift-to-PASS + weed priority);
var_weed-pierce (no-op); var_h2o / var_h2o2 / var_combo1 (S/T water cuts:
spawn spiral); var_drift2 (purpose-gated drift: gate never binds);
var_decay (harvest-first: priority crowding); var_reserve (destination
reservation: kills redundancy, doubles variance); var_seedcap (halved seed
caps: starves wall through broke days). (`STATE.md` has the evidence.)

## WORK RULES

- Audit FIRST, before changing code: `coverage_audit.py` failures ARE the task
  list (30 weeds, dry tiles 23/29 days, 51% walking, d28 starvation). Every
  variant must move at least one audit line toward PASS without regressing
  the others — attach before/after audit tails to every variant report.
- Meters BEFORE money, every variant (`tools/prod_meters.py`): if acts/day,
  mv/act, FEED/day break, money will follow — check shape first.
- Motion trace BEFORE any walk claim (`tools/motion_trace.py`): duplicates,
  reversals, and weed-birth splits decide whether a walk is waste. Coordinate
  waste is guilty only if the trace convicts it.
- ONE variable per variant, always `diff -u agent_current.py my_variant.py`.
  Max 3 variants per round. Every score per seed, never the average alone.
- Decisions by 16-seed screens on FRESH seeds (300001+, never the 0-2 cherry
  range for adoption): `tools/pscreen.py` solo (bar: |t|>=2 with majority of
  wins) and `tools/hscreen.py` h2h margin-delta vs `opp_pipe19.py`. Full games
  take seconds — a 16-seed screen costs minutes, so there is no excuse for
  cherry seeds. Cherry luck has killed four "promising" variants already.
- Adopt bar per variant: mechanism trace showing the block BEFORE the fix +
  audit progress + 16-seed screen clearing the bar + parity not down +
  a falsifier line that did NOT print + a stated COST (what got worse, measured).
- Combinations: keep the parent, add ONE mechanism, beat the parent AND each
  part alone. A negative single change may still interact — but the combo must
  clear the same bar, no discounts.
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
5. Full games PLAYED per variant (solo + screens), not just written: test the
   agent in games before you present it. An unplayed variant is a prediction.
6. Final verdict LAST: ranked variants + which ONE to adopt (or REJECT ALL) +
   the single fact you would check next. Short answers, simple words.
