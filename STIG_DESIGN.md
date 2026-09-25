# STIG design — stigmergic executor (paper design, review before/while coding)

Status: design approved in plan; v1 implements exactly this, nothing more.
File: `new_agent/stig.py` (NEW). `new_agent/agent.py` frozen as fallback/submit.
Keep from old agent: `Ctx` scan, `Scheduler` day-script, `MarketEmit` macro schedule
(d0 2C+3S, hires, land d6/d9/d10, wave response, melon wall). The macro is already
DSM-shaped; the FIELD layer is what's replaced.

## 1. Core loop (same policy for farmer + every hand, no roles)

Per step, per unit:
1. **On-tile work first.** Read tile at own pos + own inventory:
   - Pasture/coop: `!fed && wheat>0` -> FEED; elif `fed && !cared && care-pays` -> CARE;
     elif `fert-available` -> COLLECT; elif `yield>0` -> HARVEST.
   - Plant: `ripe` -> HARVEST; `thirsty && fert-window && fert>0` -> FERTILIZE;
     `thirsty` -> WATER.
   - Empty unlocked: `scheduler wants structure here` -> BUILD/PLACE; elif
     `seed budget && crop scheduled` -> PLANT.
   - Shed tile: dawn-load (PICKUP wheat 2-4 if any unfed herd; PICKUP scheduled
     animals/seeds first-come from day budgets; DROP only on overflow).
2. If an action fired -> done. (Chains emerge: still on tile next step.)
3. **Else move.** Candidates = work tiles within manhattan radius 3.
   Score = need_value - dist + (0.75 if dir == last move dir).
   Step one tile toward best. If no candidate in radius -> step toward nearest
   work anywhere (v1; PASS-only-if-nothing observable).
4. Per-step shared `taken` set: a tile targeted by one unit this step is skipped
   by others. On-tile work is never blocked. No other coordination. No claims,
   no aclaim, no pres, no budgets except day-level seed/animal quotas from Scheduler.

## 2. Numbers the design must reproduce (from DSM_OS_SPEC)

- Gap histogram: 50% gap-0 / 35% gap-1 / 9% gap-2 (radius 3 cap).
- Direction persistence ~46%; reversals rare (bonus, not hard constraint).
- Bigrams FEED->CARE, CARE->COLLECT, HARVEST->PLANT->WATER fall out of §1 order.
- Carry 2-4 wheat, ~2 feeds per pickup; feed along tour, no shed shuttles.

## 3. Explicit non-goals (v1)

- No market/sale changes (Stage 2). No fert-tier changes. No layout/column logic:
  units go where work is; block solidity must EMERGE from BUILD-on-empty-nearest.
- No cross-day memory (crew is reborn daily; per-step taken only).
- No role, no column, no tier-priority-across-distance, no ENROUTE_MAX, no batching
  thresholds. If v1 meters miss, the fix is scoring weights, not new mechanisms.

## 4. Meters (production ONLY — money is not measured in Stage 1)

- d11-17: acts/day >= 200, mv/act <= 0.9, feeds/d >= 18, gap-0 >= 40%.
- Falsifier: any meter worse than old agent on same seeds -> revert to tuning,
  never to adding mechanisms.

## 5. First tuning knobs (weights only)

`RADIUS=3`, `PERSIST_BONUS=0.75`, need values: escape-risk (cu>=1 feed/water) top,
then ripe harvest, then plant/build, then care/collect, then water routine.
Fit order from bigrams if v1 misbehaves.
