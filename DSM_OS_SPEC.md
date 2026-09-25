# DSM Operating System — Stage 1 field-work spec

Mined 2026-09-25 from `dsm games/` replays (primary: `112076061.json` DSM-vs-DSM
seed 0; validated on `112106757`, `112569777`, `112123892`). Scripts:
`/tmp/opencode/tour_mine.py`, `/tmp/opencode/chain_mine.py`.
Scope: the PHYSICAL economy only (movement + field acts). Market timing is Stage 2.

## 1. Verified mechanics (engine facts, first mined structurally here)

- **Action locus is ON-tile.** WATER/FEED/CARE/COLLECT/HARVEST(plant)/PLANT all
  fire standing on the target tile (clean single-action-step samples: 13/13, 19/19,
  14/14, 20/20, 32+/40, 34/34 at rel (0,0)). Animal-product HARVEST changes no tile.
  Movement = tile-to-tile walk between work tiles, nothing else.
- **Crew is fresh daily; index does not persist.** At dawn h0 yesterday's hands act
  blind (4 acts, obs 0 hands) then vanish; new hires appear h2+ appended on shed
  tiles with no action that step. Any cross-day unit identity is ours, not DSM's.
- **Hires act from the shed immediately.** h2 crew acts from (4-5,4-5):
  PICKUP/PLACE/CARE/COLLECT/HARVEST/WATER on the shed neighborhood, then diffuses
  outward h3-h5 in all directions.

## 2. The OS: stigmergic local greedy, no roles

- **No roles, ever.** d0 every unit does BUILD+FEED+CARE+PLANT+WATER+PICKUP+PLACE.
  Mid-game every unit mixes anim+crop (typical 5-12 anim + 3-16 crop acts/day).
  There is no animal crew, no crop crew, no farmer-crop lock.
- **Neighborhood footprints.** Each unit acts on 4-9 tiles/day inside a compact
  ~3x3 box. Boxes are NOT stable by index across days (u0: x5-7 -> x2-4 -> x1-4
  -> x5-9 over d8-d13). Zones are emergent, not assigned.
- **Coordination = work consumption (stigmergy).** All units run the same local
  greedy; an acted tile stops being work, so the next unit walks past it. Overlap
  stays low with zero communication, zero claims, zero exclusion walks.
- **Sweep, not nearest.** Same-direction persistence 46% (1454/3140; random = 25%);
  reversals rare (E-W 103, N-S 220 vs ~360 persists per axis). Units walk rows and
  turn at ends, watering/acting tile-to-tile: 1 move per action, not converge-and-return.
- **On-tile batch chains.** Top action bigrams: WATER->WATER 295, PLANT->WATER 155,
  FEED->CARE 153, WATER->HARVEST 140, CARE->COLLECT 126, HARVEST->PLANT 89,
  PICKUP->FEED 70, FERTILIZE->WATER 66, COLLECT->FEED 58. One pasture visit =
  FEED+CARE+COLLECT. One crop stop = HARVEST+PLANT+WATER. Per-op moves-since-last-
  action: CARE 0.28, PICKUP 0.25, HARVEST 0.51, COLLECT 0.54, PLANT 0.83,
  WATER 0.85, FEED 0.99, FERTILIZE 1.25.
- **Small-batch supply.** PICKUP WHEAT amounts 2-4 (43x3, 19x4, 16x2); ~2.2 FEEDs
  per PICKUP per unit-day; unit FEED counts/day cluster 1-3. Units carry wheat
  along the tour, not in shed-shuttle runs.
- **Redundant acts tolerated.** Same-tile repeat WATERs observed; no
  re-walk to fix them (0 moves wasted). PASS rare overall (3-4% of steps) because
  mid-game work is dense; early-game idle units PASS (u1 d2: 11 PASS) instead of
  trekking — idleness beats distance.
- **Aggregate (4 games, DSM side):** ~4100 acts, ~3100 moves, mv/act 0.74-0.79.

## 3. Why ours can't do this (contrast, for Phase-2 design)

1. Role locks break stigmergy: animal crew walks past crops, crop crew past animals
   — work in front of a unit is invisible to it, so units pile onto distant shared
   targets (convergence -> claims -> exclusion walks).
2. Tier-priority-across-distance breaks sweep: HARVEST 5 tiles away outranks WATER
   underfoot -> reversals and long legs (our WATER 1.42 vs 0.85, FEED 1.27 vs 0.99,
   CARE 0.82 vs 0.28, PICKUP 1.27 vs 0.25).
3. Column partition + static day-roles freeze what should be emergent: footprints
   assigned by headcount math instead of work consumption.
4. Shed-star supply (burst_fetch, bank runs) vs dawn-load + carry-along-tour.

## 4. Open for Phase-2 design

- Exact local rule (nearest-work-any-type? radius cap? type weights?) — fit from data.
- Pasture-block solidity mechanism (where BUILD picks as center fills).
- Fert targeting (which tiles get d10 21 / d11 81 applications).
- Market timing + sale execution (Stage 2, not here).
