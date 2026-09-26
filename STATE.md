# STATE — current truth, 2026-09-26 (base = `agent_current.py`, STIG v7)

Base is a stigmergic executor (StigExec) + DSM-spec macro (Scheduler/MarketEmit,
byte-identical to the frozen role-based base). Lineage in repo:
`agent_base.py` -> `var_sched5.py` -> `var_sched6.py` -> `agent_prev_role.py`
(role-based, 62k) -> STIG v1 (~90k, one-actor-per-tile) -> STIG v2 (same-day
fert cash) -> STIG v3 (harvest age-gate) -> STIG v4 (fert_pays + fert keep)
-> STIG v5 (eve-water 8.0) -> STIG v6 (melon program) -> STIG v7 (seed-pile
cut, this file; +3.7k/6 perfect-control).
The role-based base is kept as `agent_prev_role.py` for
A/B only — do not develop on it.
`FINDINGS.md` + `SPEC.md` are older rate tables; `DSM_OS_SPEC.md` (mined replay
STRUCTURE) + `STIG_DESIGN.md` (this base's design) + this file override them.
The 41 DSM replay JSONs (`dsm games/`, ~1.4GB) are NOT in the repo — their
distilled structure is `DSM_OS_SPEC.md`; `tools/` replays the mining method.

## Reference: DSM champion (mined from replays, engine-verified)
- d0: 2 COW + 3 SHEEP + 6 MELON seed + 15 WHEAT seed + 9 prod wheat + 4 hires, spend to ~$0.
- d5: money 634-901, herd still 2C+3S. d6: ALWAYS 1st LAND + herd wave (7-12 head).
- d10-15 melon spike: money ~$3k->$7k->$10k->$26k on d10/11/12/15. d15 herd 20-30.
- Structure (DSM_OS_SPEC.md, first mined 2026-09-25): ALL field work is ON-tile;
  crew reborn daily (index does not persist); NO roles ever (every unit mixes
  anim+crop); coordination = work consumption (stigmergy, zero claims); sweep
  46% directional persistence; 94% of inter-action gaps <= 2 moves; dawn
  shed-start diffusion; carry-along supply (pickup 2-4 wheat, ~2 feeds/pickup).
- Rates: sells ~95 units/day; feeds ~20/day; acts ~150/d at mv/act 0.74-0.79;
  CARE 0.28 moves (follows FEED same visit); PICKUP 0.25; WATER 0.85.

## Engine rules (kaggle-environments 1.32.7, verified in code)
- 720 steps, 24/day, 30 days, start $3000, board 10x10, 10 market orders/step.
- HIRE cost = engine `_fib` (1,1,2,3,5...). FEED = 1 WHEAT/animal/day, all species.
- 2 consecutive unfed days = escape (permanent). Hands reset nightly (fresh crew).
- WATER ticks yield ONLY in window `[(maxday+1)//2, maxday]` (+2 if fertilized, else +1),
  capped at maxyield. MELON: window age 6-12, first harvest day 10, one-shot.
- One-shot crops are SINGLE harvest (plant removed). FERTILIZER active 3 days.
- SELL fills partial (no wallet wall). PLANT is atomic against a shared per-step seed budget.
- Shed tiles: (4,4),(5,4),(4,5),(5,5). PICKUP/DROP only ON shed tiles. PLANT
  consumes seed stock directly (units never carry seeds).

## Measured numbers (reproduce before changing anything, see RUN.md)
Pinned parity vs PASS dummy (`LINE_FORCE=pinned`, mixed line), seeds 0/1/2 —
rewards **89412 / 92105 / 105625** (total 287142, v6 was 286042 = +1100):
- PASS: d5 herd 2C+3S x3; d6 LAND x3; d6 herd>=7 x3; d10 money>=2500 x3.
- FAIL: d0 plants (STALE); d5 money; d12 ~$2k vs $8k; d15 vs $20k.
- Competitive screen vs pipe19 pinned 200001-6 (seat 1, 6-seed standard):
  **326207 vs v6 322459 = +3748 abs** (+3903 margin; per-seed
  -200/+400/+2548/+500/+500/+0 — 5/6 positive, none worse than -200).
  Opp tickets IDENTICAL both halves (362991/500265 vs 362991/500420):
  the cut barely moves the field so RNG holds constant (perfect control).
- Mechanism (`/tmp/opencode/census_seed.py`, seed 0 pinned): stands identical
  to v6 (d15 S25/W13/C9/T9, d20 S22, d25 S16); buys 8-9 straw/d -> ~3.7/d
  against ~2/d replacement need (weeds); drawer pile stops growing.
- STIG v5 ADOPT NOTE (floor breach, explicit + lottery-documented): 5-seed
  screen +10403, parity +10655, mechanism +22pp, gates held — but 200001 is
  -2349 (breach). Late-trace audit (`/tmp/opencode/late_trace.py`): d05-d12
  IDENTICAL (money/herd/shops), divergence starts d13 (-739, eve labor
  reallocated pre-returns), then the d15 shop unlock RE-DEALS (field
  diverged -> different empty tiles -> different draw): v4 draws SMOOTHIE,
  v5 draws a dupe; v5 also misses the d21 PIZZA and d24 2nd-ICE unlocks. On
  a 9-cow milk line (ICE+SMOO+PIZZA all want MILK) three missed demand
  unlocks >> any field effect. Verdict: lottery, not mechanism. Adopted;
  v4 revert condition CLOSED (eve-water works: 59->81%, 200003 +4407).
  Standing warning: two straight adopts with one breached seed each (v4
  200003 real, v5 200001 lottery). The bar holds — next variant needs a
  clean 3/3 or it doesn't land, no third exception.
- Older tapes: STIG v4 screen 52772/38707/57997 (+10253 vs v3; 200003 -4178
  real-ticket loss now repaired by v5's eve pass on the same seed: +4407).
- Older tapes: unpinned pinch v2 62444 vs 179413 (-116969); role base pinned
  28852 vs 137754; frozen `main_v60` (not in repo) margin -1838.

## Open stages (the work — all of it is yours)
1. d6 wave cash: DONE for herd (d6 herd>=7 passes pinned 3/3, unpinned 2/3).
   OPEN for money: d5 ~$200-500 vs $750; d10/d12/d15 bands.
2. Curve timing: MELON SPIKE DONE (v3 age-gate + v6 program: d10 money
   PASSES, +42.5k). SCALE: opp d15 = 57 plants + 17 head (32-33 STRAW);
   ours post-v6 ~50 + spree. REMAINING: d5 money, d12/d15 bands, terminal
   (opp liquidates d29 to 0 plants + carrot rotation; weeds 0 all game).
3. d1 wandering: CLOSED as ~$0 lever (PASS-if-idle rule FALSIFIED, do not
   resubmit). Falsifier read confirmed: base d02 money = $301 exactly (vs
   pipe19, seat 1, 200001, pinned); idle variant = $202. REJECTED at mechanism
   level (d1 PASS 0->1, moves -1). Autopsy (`/tmp/opencode/dbg_idle.py`): d1
   walks are to-work 166 + wheat-load 69 + bank 2 — legitimate dispersed travel
   (15-plant field + herd errands), NOT idle drift; and the shed-drift is
   LOAD-BEARING positioning (idlers scattered, paid +$99 travel later). d1
   mv/act 4.67 is a crew-size artifact (9 units vs DSM 5) + cosmetic: extra
   hands cost no wages, only ~$54 fib. No dollar lever here; mv/act ignored.
4. Terminal weeds: v4 freed water labor (WATER d13 51 vs 40 on their trace);
   mid-game deaths fall; terminal (d29 ~32-42) remains. Ruled out: urgency
   escalation. Candidates: eve program sizing (above), late water coverage.
5. THEN: margin screens (pipe19/18/v57, 5 seeds, ALL pinned) and optimization
   BEYOND DSM (DSM is the target to beat, not the ceiling).

## Recently landed (in the base — resubmitting any of these = instant reject)
- Fert pays + fert keep (STIG v4, outside-agent fp_fb mechanisms, verified at
  engine level and ported): (1) `fert_pays()` gates FERTILIZE — never on an
  active tile (engine max()es fertilized_until_day: repeats are silent
  no-ops, and the on-tile rule camped units dumping whole pockets);
  ongoing (STRAW/TOMATO) only when a production eve falls in the 3-day
  window (end-of-day ticks +1/eve, +1 more iff watered that eve while fert
  active; max 8/plant); melon only in-window with yield<=max-2.
  (2) keep-logic: fert banks intraday only pre-d9 (cash); d9+ it rides
  pockets to paying applications (no shed round-trip: PICKUP acts + clogged
  pockets), surplus sells via nightly auto-drop; produce_load excludes
  post-d9 pocket fert (phantom bank trips). My d1-trip kept (pre-d9 bank
  path). Interacts with v3 age-gate (complementary: gate blocks harvest
  trap, pays blocks fert waste). Screen +10253 (see measured numbers).
- Melon program (STIG v6, `ripe()` + `plant_need`): (1) in-window melons
  (age 6-12) unwatered score 7.0 (above routine 5.0, below eve/HARVEST 8.0;
  conflict-free pre-d12); (2) melon ripe = age>=10 with any bank (liquidate
  d0-cohort d10, d1-cohort d11 — time value + tile reuse beat waiting for
  6.0). Sales follow via shed stock + 6-batches. Screen +42543 (see above).
- Eve-water 8.0 (STIG v5, `prod_eve()` + `plant_need`): unwatered strawberry
  on a production eve scores 8.0 (ties ripe HARVEST, below hungry FEED 10.0).
  Engine: ongoing ticks +1/eve, +1 more iff watered-while-fert-active; fert
  applied d covers eves d..d+2. Strawberry-only (tomato eves are daily — that
  would be a blanket raise, not targeting). Closes the v4 gap (200003 now
  +4407 on the same seed).
- Harvest age-gate (STIG v3, `ripe()`): non-ongoing crops need age>=first
  (melon 10). Engine HARVEST fails below first_yield_day even with yield
  banked; acting on it camped units all day spamming no-ops (d9: 6 acts on
  one age-9 melon; d13: 50 HARVEST cmds on 5 tiles) AND pulled walkers
  map-wide via plant_need scoring. Screen vs pipe19 pinned 200001-3:
  49399/27649/62175 vs base 41052/29340/54204 = **+14627 total** (+8347/
  -1691/+7971, clears the bar).
- Same-day fert cash (STIG v2): FERTILIZER banks intraday (was pockets-only
  till the nightly auto-drop, delaying all fert cash a full day) + a d1-only
  fert>=2 shed trip. d1 FEED 0->4, d6 herd 5-6->7+, pinned total +5754
  (257026->262780, worst seed -1780), mid-game acts +30%, mv/act halved.
- One actor per TILE per step (shed excepted): +44% total, killed ~800
  no-op acts/game (14-unit WATER piles, 50-HARVEST spam on 5 melons).
- Hunger gate, SOFT form: starving (cu>=1 + wheat shelf < herd) => wheat P-cap
  FULL quota + seed S-cap 1 (a hard seed-skip stalled the melon wall: -13k seed 2).
- Shed-ring reservation (no PLANT within 2 of shed while outer room exists):
  pastures stay shed-adjacent (~1 move/feed vs ~5 from the corner): +17k.
- Distance-dominated scoring (value - 2*dist, persist bonus 1.5, radius 3):
  nearest-work-first keeps units spread; only val>=9 pierces the radius.
- No NEED_WHEAT blindness (VISIT 3.0): wheat-less units still CARE/COLLECT/
  HARVEST (collect-fert is broke-day income); explicit wheat-load shed trip.
- Unplaced-triggered animal pickup (deficit-vs-target reads shed stock as owned
  and never fetches) with deliverer caps (d0: 2 so planting survives, later: 5
  so the wave places).
- Older (from role base, still in macro): urgency-first feeding; melon sale
  batch 6; d2/d3 melon catch-up; d0 trickle caps; hire burst; feed_cap; `_fib` fix.

## Rejected (never re-propose, all A/B'd negative or byte-identical)
- d11+ wheat targets 12->24 (unslash): -10370 total (+929/-1722/-9577).
  Stands rose (11->19 by d15) but buys never fell (hair-trigger still fires
  on micro-zeros) while the fixed water budget spread thinner. Lesson: stands
  without water labor = weeds + turnover cost. See field-passivity note.
- Late wheat emergency gate (pockets must cover unfed, d11+): -4271 total
  (-5687/+10650/-9234) WITH the early ticket held identical (stream-diff: 0
  diffs in d0-10). Kills the churn AND the insurance: delayed buys leave the
  herd chronically cu=1 (no escapes, but growth freezes via feed_cap=
  owned_now, seeds cap via hunger gate, FEED 10.0 distorts labor). Churn is
  feed-insurance premium for cu=0; the fix is field-side (shed never hits 0),
  never buy-side. Early-gated form also REJECTED (inverted gate removed d0-10
  buys by accident, then correctly-split form is this one).
- Ungated pocket gate (all days): +14438 total but -8579 worst seed — the
  d5 $300 save re-dealt the shop lottery (BAKERY vs YARNx2). Correct
  mechanism, unmeasurable form. Superseded by the d11+ form above (also
  rejected — the gate itself is wrong, see previous).
- Yield-window melon WATER 8.5 (two forms): ungated -12577 (-16096/+1381/
  +2138); age>=8-gated -22430 (-20045/+3595/-5979). Mechanism FIRES
  (d9 coverage 3/11->10/11, wall yields on schedule) but the effect (~+$500
  melon) drowns in the shop lottery (see methodology). PARKED, not wrong —
  revisit only as part of a big-effect variant.
- d6 crew diversion (found via the bump): d6 age-6 wall water pulled units
  off bank trips (DROP 5->3) -> MarketEmit missed 2nd LAND + 2 animals
  (LANDx2->x1, 7 head->5). d6/d7 crew is untouchable: first LAND + wave buys
  need every DROP. Any future variant that moves d6 units must re-verify
  d6 LAND count in market trace.
- Never-fert-melon: -5186 total (-12110/+1220/+5704). Lesson: fert is our
  water-miss crutch (d9/d11 collapses) — removing it before fixing coverage
  caps the wall at 3-4. DSM never ferts because DSM never misses water.
  Sequence is coverage FIRST (Stage 2b), fert removal after.
- Unconditional fert shuttle (fert>=2 trip all game): early fixed but wave
  3 days late + late labor tax, -8.7k pinned total.
- Crisis-gated fert trip (unfed + no shed wheat): gate too strict when broke
  (shedW 1 shuts it off), -20.5k pinned total.
- Banking-only fert (no trip): d1 FEED still 0 (nothing reaches the shed d1),
  +428 pinned total (noise) — mechanism absent without the d1 trip.
- d0 wheat opening-quote rotation (-12k: sold feed wheat, d1 starved).
- Index-jitter symmetry break (-7k: scattered feeding coordination).
- Hard hunger seed-skip (seed-fragile -13k seed 2; soft form landed instead).
- Zero-move FEED/CARE enroute port (fired 95 acts, -3.4k parity: each service
  costs an arrival step under saturation).
- Melon-wall fert program at d4 (-2.2k: targeting without supply moves nothing).
- Older: wallet-gated shopping; chain-planting; hire gates; carry-12; ripe-only
  wheat reserve; ENROUTE_MAX 3->6; holding produce for price; land before income;
  goose-heavy at capped delivery; tomato walls >12; var_fertcol/var_fertval/
  var_enroute/var_shed; stale shared claims.

## Hard constraints (DSM parity, inviolable)
d0 = 5 head (2C+3S); melon wall d0-1; strawberry from d3; land exactly d6+d9+d10;
day-1 hands ~4; herd follows INCOME. d0-plants-15 gate is STALE (see above).
One variable per variant; production meters before money; TOTAL per seed,
never the average alone. ALL screens `LINE_FORCE=pinned` (see below).

## Methodology note: shared-RNG contamination (found 2026-09-26, binding;
independently confirmed by outside agent at engine level)
_end_of_day builds ONE Random((seed*1_000_003)^day) per day; _spawn_weeds
consumes rng.random() per EMPTY tile of BOTH farms in player order, and only
then a shop unlock is drawn (every 3rd day: d3,6,9,12,..., with replacement).
So any code change that alters EITHER farm's empty tiles re-deals weeds AND
shops from that day on — including the OPPONENT's game (measured: same opp
scores 147k/158k/179k/188k on seed 200001 across our variants, opp code
untouched). Observed here: same seed 0, BASE draws ICE_CREAM (cow+ line)
while a variant draws YARN d9 (late switch to sheep line). Consequences:
- Unpinned parity conflates shop luck with field fixes — it is NOT the gate.
- The gate is PINNED parity (mixed line fixed): exact rewards above.
- Shops still differ across variants even pinned (demand noise) — treat
  <5k pinned-total deltas as noise; the adopt bar (total >=5000, no seed
  worse than -2000) already accounts for this.
- Competitive margins are interactive (opp weeds/shops shift with OUR field
  via the shared stream; measured +33k opp swing same seed) — single-seed
  margins carry ±30k luck. Confirm winners on 5 seeds x 3 opps, all pinned.
- SHOP LOTTERY dominates (found 2026-09-26, binding): any field delta re-deals
  weed draws -> shop unlocks from ~d8 on. Measured: identical play to d7,
  one d8 planting delta (PLANT 13 vs 8) -> d9 ICE_CREAM_SHOP becomes PET_CAFE,
  d12 PIZZA_SHOP becomes SMOOTHIE_SHOP -> -20k final on 200001 while mid-game
  was AHEAD (+$2.4k d11). Lottery is ±15k per seed — LARGER than the 5k
  adopt bar. Consequences: only big-effect variants (>>10k) are measurable
  through it; micro-fixes (~$500) are unmeasurable — park them, swing big.
  A mechanism can be CORRECT (coverage/yields improve on trace) and still
  fail the screen; that is the bar doing its job, not a wrong diagnosis.
- LOTTERY-NEUTRAL STANDARD (2026-09-26, binding after bankonly): 200001-3 are
  CHERRY seeds (v6 scores 197.9k there vs 124.6k on 200004-6 — ±35k/game
  lottery scale). Any field-divergent variant is penalized there (fresh
  tickets vs base's lucky ones). Adoption standard is now 6-seed totals
  (200001-6) absolute + margin; adopt iff mechanism verified AND 6-seed not
  contradictory AND parity holds. Minimal-field variants (seed quotas) hold
  opp tickets IDENTICAL (perfect control) — small clean gains adoptable.
- STAGE-4B REJECTIONS (all vs v6, all pinned): purity S32/W24 (h2h margin -4k
  nose, parity +3k nose; C/T are cheap-labor fillers, not dead weight);
  melon12 12-d0-melons (parity -26.5k REAL: htgt still bought 2C+3S d0 so
  melon seeds capped at ~7 by wallet; herd-deferral retry broke the d6 wave);
  nogeese (parity +17.7k BUT h2h 6-seed abs -9.3k/margin +10k = nose; eggs pay
  for their labor; d6 herd gate fails — gate discipline holds the reject);
  bankonly wheat-out-of-bank (parity +8k lottery; h2h 6-seed -48.6k/-68.8k
  CLEAN reject); big-carry 12-loads (parity -65%: 12-wheat pockets trip
  BANK_LOAD=8 -> infinite shed shuttle PASS 133/FEED 7; LESSON: small carry
  is a kanban pull — big loads overstock the 100-cap shed -> destruction);
  wheat-churn fix (parity flat, h2h -102k UNIFORM: reserve/fragile across
  shop draws; ALSO found + fixed the dawn-crisis bug — hands are 0 at dawn
  so reserve collapsed daily — fix retained? NO: whole variant rejected,
  bugfix parked inside it).
- STIG v7 (seed-pile cut): d13+ S(STRAW) 8->3 (+4->+2 pulse). Drawer held
  $2420 dead (17 straw seeds) while stands SHRINK by policy. +3.7k/6-seed,
  perfect RNG control, parity +1.1k. Smallest adoption; hygiene compounds.
- Stage 4c-1 (DSM d0-d1 anatomy, replay 112076061 audited): DSM d0 = 1C+5W,
  then 1C+3S+4H, SELL-W-1/step cycling, 6 MELON (h7/h9/h12), 15 W-seed,
  ends $6/15 plants. DSM d1 = 8 HIRE + SELL FERT 1+1+3 ($500 by h11) +
  12x BUY MELON-2 attempts h8-h13 (~5-6 fill) + 6 feed wheat; ends $1/
  20 plants. DSM d2 = 6 HIRE + SELL FERT 4 + 9 STRAWBERRY-1 + 3 MELON-1.
  Correction to old "d0 trilemma" note: d1-melon money EXISTS (d1 fert
  ~$500); the gap is TIMING (we bank/sell a day late), not d0 budget.
  Ours d1: wallet $0-4 all day, fert 3 by h23, melon fills 0; d2 dawn $12.
- var_shed2 REJECTED (dawn-stock reserve: leave 2W in shed d0-d1 when
  pockets cover all unfed; diagnosed shed-0 d1 dawn from pocket stranding
  + 1-day auto-drop delay): trace moved +1 melon d1/+2 d3 then converged
  (d6 money identical); totals ~10 vs 11. Peashooter, no parity run.
- var_fertup REJECTED (COLLECT_FERTILIZER 4.5->7.5 d0-d1): d1 cash $12->224,
  d10 gate PASSES 3/3 first time, parity +8.2k solo [86966,98522,109830]
  vs [89412,92105,105625]. BUT 6-seed h2h CLEAN reject: abs -68.2k
  (257963 vs 326207), margin -23.7k, opp lottery -44k. LESSON: solo-parity
  gains from earlier selling do NOT survive shared-pool price competition
  (town MARKET pool is shared; vs pipe19's heavy selling our early spike
  sells into crashed quotes). Solo parity alone never adopts spike work.
- CAUTION rerun 2026-09-26: `python -c harness.parity` WITHOUT
  LINE_FORCE set runs UNPINNED (line=mixed) — scores ~8k off pinned.
  Always `LINE_FORCE=pinned` prefix; never compare mixed vs pinned.
- Stage 4c-2 (walk split, instrumented trip decisions d0-15 solo 200001):
  trip_field 1674, trip_drift 188 (46% of shed-bound!), trip_wheat 151 (37%),
  trip_bank 68 (17%). Shed PICKUPs 222, of which WHEAT 182. Mid/late walks
  ~90% supply-shuttle; d0-d1 mostly positioning.
- var_bank8 REJECTED (exclude pocket WHEAT from bank-trip test; wheat is keep
  so 4W+4P should not trip BANK_LOAD=8): bank acts 48->34 BUT walks unchanged
  (system compensates via wheat/drift trips). Attacked the smallest slice.
- var_stay REJECTED alone (drift->PASS): walks -3.2pp, escapes fixed, BUT
  weeds 30->39 (drift walks gave incidental coverage) and fert loads 19->5
  (piggyback starvation). Audit regression, no parity run.
- var_weed-pierce NO-OP (weeds exempt from radius cap): byte-identical game.
  Reason found: binding constraint is PRIORITY (1.0 vs water 5.0), not radius;
  late labor saturated by watering so weeds never win. Drift (early, no weeds)
  and weeds (late, no drift) don't overlap in time.
- var_weedstay REJECTED (stay + weed 5.5 priority + pierce): audit weeds
  30->19, walk 51.2->47.5%, escapes fixed — BUT parity -17.3k
  [59520,101726,108592] and d6 herd>=7 FAILS 3/3. LESSON: shed visits are the
  animal-delivery channel (deliveries piggyback on presence); cutting visits
  stalls the d6 wave (~10-30k). Any walk-cut must preserve d6 delivery
  throughput (explicit delivery trips or keep drift until wave done).
- Standing facts: pockets empty nightly (wheat reload trips ~9/d structural);
  dry tiles are the weed SOURCE (57% worst day -> nightly spawns outpace DIGs);
  labor pie fits on paper (~120 work + walks in 312 steps) so walks are the
  only fat — but they carry deliveries+fert-loading piggybacks.
- INFRA 2026-09-26: full games are ~4s, not minutes. tools/pscreen.py (paired
  solo A/B, 8 workers) + tools/hscreen.py (paired h2h A/B vs opp, margin-delta
  t-stat). Fresh seeds 300001+ avoid cherry bias. SE for solo ~1300 at n=48,
  ~3-4k at n=16. Bar: |t|>=2, wins majority. 6-seed screens retired for
  decisions (only ±8k+ visible); parity 0,1,2 kept as the 120k gate.
- ENGINE VERIFIED (kaggriculture.py): WATER on ongoing crops banks NOTHING
  (438-443: only one-shots bank in-window; ongoing just set watered_today);
  ongoing +1 ticks nightly unconditionally, fert +2 needs watered+fert-active
  (786-801); 2x unwatered -> WEED; fertilizer_available=True OUTSIDE the fed
  branch (829: starving animals still print fert); one-shot decay past
  maxyield -> WEED every 2 steps (752-766); per-unit re-quote loop (596-618);
  shed overflow DISCARDED at cap 100 (_drop_inventories_to_shed).
- var_h2o REJECTED (water S/T only fert-active eves): solo -10.1k/16 t=-5.0.
  Sync-skip synchronized the wall into the same thirst day (rescue stampede,
  weeds 30->39). var_h2o2 REJECTED (desync cohorts by planted parity):
  solo -9.6k/16 t=-2.6, sd DOUBLED. var_combo1 (h2o2+weedstay) REJECTED:
  solo -14k/16 t=-4.0. Failure mode named: SPAWN SPIRAL — skipped tiles open
  holes, empty tiles spawn weeds by RNG, DIG labor < spawn rate on some seeds
  (-27..-32k tails on 4/16 seeds: straw wall 119->70u). The streak-0 buffer of
  daily watering is load-bearing robustness, not waste. Direction dead.
- var_fertup REJECTED FINAL (16 fresh seeds): solo -13.5k t=-3.1 wins 1/16;
  h2h margin -5.5k t=-1.8. The +8k on seeds 0-2 was cherry luck. d10-gate 3/3
  noted but worthless without money.
- var_weedstay REJECTED FINAL: solo -13.4k t=-4.0 wins 2/16; h2h -12.2k
  t=-3.5. Audit progress (weeds 30->19, walk -3.7pp) does not survive money.
- BRIEF CORRECTIONS (both sides measured): d28-29 starvation is CASH-POSITIVE
  (unfed prints $75 fert/d x2d; feeding it back -2.3k). Goal is "no escapes",
  never "feed d28". "No dry days" contradicts the engine (ongoing water = $0
  yield); usefulness = water only when it pays or prevents streak-2.
- External replication (second agent, 48 seeds): goose-cutoff-d11 +2.4k t=1.8
  (below bar; convergent with our nogeese h2h reject — stays dead); wheat
  buy-caps negative (churn is productive: fed animal ~$125-155/d on ~$50
  feed); trickling sales monotonically worse (shed cap discards); 13 hands
  -839 (flat), 14+ catastrophic (fib+slots+collisions). Nothing over t=2.
