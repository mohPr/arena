# STATE — current truth, 2026-09-25 (base = `agent_current.py`, STIG v1)

Base is a stigmergic executor (StigExec) + DSM-spec macro (Scheduler/MarketEmit,
byte-identical to the frozen role-based base). Lineage in repo:
`agent_base.py` -> `var_sched5.py` -> `var_sched6.py` -> `agent_prev_role.py`
(role-based, 62k) -> `agent_current.py` (STIG v1, ~90k). The role-based base is
kept as `agent_prev_role.py` for A/B only — do not develop on it.
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
Parity vs PASS dummy, seeds 0/1/2 — rewards **88793 / 90031 / 90503** (total 269327):
- PASS: d5 herd 2C+3S x3; d6 LAND x3; d10 money>=2500 x3 (melon spike FIRES).
- FAIL: d0 plants 14 vs 15 x3 — STALE gate (DSM d0 stands ~9-14; the 15 was
  Boey-flavored; the shed-ring reservation costs 1 plant for ~+17k, keep it);
  d6 herd 5-6 vs 7 (wave cash arrives late); d5 money ~$200-500 vs 634-901;
  d12 ~$1.7-3.7k vs $8k; d15 ~$1.9-2.8k vs $20k (curve shifted late: money
  grinds d20+, no d10-15 spike yet).
Pinch, seed 200001, LINE_FORCE=pinned, opp seat 0 / us seat 1 (`ab_pin_opp.py`):
- vs pipe19: **62444 vs 179413, margin -116969**.
- vs pipe18: 62436 vs 179412, margin -116976. vs v57: identical line.
  (All three opps saturate ~179.4k on this seed; margin moves ONLY via OUR score.)
- Old role base same setup: 27385 vs 147891, margin -120506. STIG gains +35k
  absolute, +3.5k margin. Frozen tape `main_v60` (not in repo): margin -1838.
- Production meters (seed 0, `tools/prod_meters.py`): d11-15 acts 150-165/d,
  mv/act 0.5-0.9, FEED 17-24/d, gap-hist 53/27/12 (DSM 50/35/9). d1 weak
  (acts ~24-38, mv/act 2-3.8, FEED 0-1): sparse-work wandering.

## Open stages (the work — all of it is yours)
1. d6 wave cash: herd 5-6 vs 7-12. d5 money ~$200-500 vs $750; d1-2 feed hole
   (FEED 0-1, escapes d2-3) cascades into no-milk d2/d4, no-wool d3, late wave.
   Hunger gate + full wheat cap contain it; the d0-1 cash allocation is still fragile.
2. Curve timing: d12/d15 bands. Money arrives d20+, not d10-15. Melon converts now
   but yields stall 3-5 vs 6 (water/fert coverage d8-12 on the wall).
3. d1 wandering: sparse-work diffusion (mv/act 2-4). DSM idles (PASS) instead of
   trekking; ours treks.
4. Terminal weeds (~46 by d27-29 on some seeds): late water coverage under max scale.
5. THEN: margin screens (pipe19/18/v57, 5 seeds) and optimization BEYOND DSM
   (DSM is the target to beat, not the ceiling).

## Recently landed (in the base — resubmitting any of these = instant reject)
- One actor per TILE per step (shed excepted): +44% total (187k->269k), killed
  ~800 no-op acts/game (14-unit WATER piles, 50-HARVEST spam on 5 melons).
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
never the average alone.
