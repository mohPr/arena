# New-agent build spec — mined from 34 DSM replays (33W-0L + 1 self-play)

Source: `/home/moh/Desktop/glm2/result/dsm games/` (34 JSON, seeds 0..2114822375).
Scores: DSM 75k-166k, median ~107k. Closest game +783 (112122229 vs Majkel1337).
Scripts: `/tmp/dsm_audit.py`, `/tmp/dsm_deep.py`, `/tmp/dsm_deep2.py` (outputs in `/tmp/dsm_*_out.txt`).

## 1. DSM core loop (the system, in order)

### 1.1 Fixed opening d0-d5 — IDENTICAL in all 35 DSM seats
- d0: buy 2 COW + 3 SHEEP + 9 WHEAT(prod) + 6 MELON seed + 15 WHEAT seed + 4 HIRE. Spend to ~$0. Sell 6 WHEAT d0.
- d1: ~6 WHEAT(prod) + ~12 MELON seed + 6 STRAWBERRY seed (+2 FERT sometimes). Hire to ~9. Sales: FERT ~5, WOOL ~4, MILK ~3-4 (starter output at high early prices funds d1).
- d2: ~5 WHEAT(prod) + ~3 MELON + ~10 STRAWBERRY. Hires ~6.
- d3: ~10 STRAWBERRY seed. First shop unlock seen (unlocks at d3,6,9,...,24 = townShopUnlockInterval 3).
- d4: money ~$450 (strawberry first harvests). ~2 WHEAT(prod).
- d5: money ~$750-900 (band 634-901, ALL games). ~2 WHEAT(prod). Herd still 2 COW + 3 SHEEP.
- Seed prices (env): WHEAT 10, CARROT 20, TOMATO 50, STRAWBERRY 100, MELON 80.

### 1.2 d6 = BRANCH DAY (shops known = d3 + d6 unlocks). Spend to ~$0 intraday (sell first, buy later).
- ALWAYS: 1 LAND (first of exactly 3 in standard games: d6 + d9 + d10).
- ALWAYS: ~16 STRAWBERRY seed + ~10-15 WHEAT seed + ~7-21 WHEAT(prod). Hires ~8.
- Species branch (d6 herd buy; top-ups d7-d12 complete it):
  - YARN_STORE known by d6 -> SHEEP line: 6-8 SHEEP d6 (+3 d8, +3-4 d9-10, +1-4 d12; total 14-23) + COW 2-9 (pizza? more) + GOOSE ~4-5 (2 d9 + 2 d10 + 1 d11).
  - YARN at d9 -> partial: +4 SHEEP d9 +1-3 d10 (total ~8-11).
  - YARN at d12 -> +4 SHEEP d12 only.
  - YARN d15+ -> NO reaction (0-1 sheep).
  - No yarn: COW line: PIZZA known by d6 -> 10-12 COW d6; else 5-8 COW d6 (+1-2 d7, +1-4 d9 => total 6-18). GOOSE wave: 4 d6 + 4 d9 + 1-3 d10-11 (total 7-12). Sheep stay 3.
- Counts are budget-capped (spend-all): poor d5 (~650) -> 7-9 head d6; rich d5 (~850) + pizza -> 11-12 head.
- d15 herd targets: cow-line 9-15 COW + 7-12 GOOSE + 3 SHEEP (~20-26 head); sheep-line 5-9 COW + 14-23 SHEEP + 0-5 GOOSE (~24-30 head).

### 1.3 Melon line (standard: 30/34 games)
- Seeds: 6 (d0) + ~12 (d1) + ~3 (d2) ~= 21 total. Harvest sale: d10 ~36-42 + d11 ~18-36 + d12 ~6 = ~60 MELON sold (labor/weed-capped, NOT seed-capped).
- Money: d10 ~$3k -> d11 ~$7k -> d12 ~$10k -> d15 ~$26k. The spike funds d9-d11 land/animals/wheat.
- MEGA variant (4 games: 093028/109015/117053/119437): 79-86 MELON + 83-91 WHEAT(prod) + 24 hires on d1. MELON sold STILL 60. No score premium. VERDICT: waste (~$6.5k seeds + hires for nothing). DO NOT COPY. (Probable old version.)

### 1.4 Land rule
- Standard: EXACTLY 3 lands on d6, d9, d10 (24/26 standard games; 2 buy an extra d9).
- Sheep-line rush (feed-driven: 20+ sheep need ~600 wheat): up to 7-24 lands, all on d6(1) + d9(1-4) + d10(4-11) + d11(2-12), iff melon budget allows. Poor starts skip the rush.

### 1.5 Steady state d13+ (median/day)
- Buys: WHEAT seed ~6-10, CARROT seed 6, TOMATO ~1-2, STRAWBERRY ~1-4, WHEAT prod ~13 (feed), FERT spikes ~12-28 (to d25).
- Sells: WHEAT ~20 (growing to 35+ by d25), CARROT ~10-15, STRAWBERRY ~8-16, TOMATO ~6-13, MILK/WOOL/EGG per line (continuous dump, see §3), FERT ~13 tapering to ~4 by d24.
- Hires 11-12/day (d26+: 10-11). Replacement sheep 1-2 on some days d15-21 (escape replacement).
- Money grinds ~+$4-5k/day.

### 1.6 Endgame (adaptive liquidation — COPY THIS)
- Feed cutoff per commodity: crashed-line animals starved first (e.g. sheep feed stops ~d22 when wool crashes, herd 8->5->3->0 by d29; profitable cows fed through d27, kept at 15).
- Mass starvation d28-29 (2 unfed days -> escape), NOT sales (animals unsellable).
- Terminal dump d28-29: WHEAT 71-89, CARROT 38-68, everything to zero float. EGG/MILK/WOOL dumped to last step.

## 2. Shop-conditional summary (the adaptivity that matters)
| Signal (by d6 unless noted) | Response |
|---|---|
| YARN <= d6 | sheep line (14-23) |
| YARN d9/d12 | partial sheep (+4-8) |
| YARN d15+ | ignore |
| PIZZA by d6, no yarn | 10-18 cows |
| No pizza/yarn | 6-9 cows + 10-12 geese |
| Sheep line + budget | land rush d10-11 for wheat |
| Commodity price crashed | starve that species first (d22+) |

This independently CONFIRMS our yarn-gate finding: DSM only runs sheep with early yarn (= deep wool demand). Wool holds ~230-240 to ~d17, crashes d21+ (to 1-5). DSM rides it down (§3).

## 3. Sale timing: DSM HAS NONE (beat-DSM edge #1)
- WOOL/MILK/EGG sold CONTINUOUSLY d6-d29 into decaying prices (wool 242->5, milk 214->28). No pre-crash dump, no hold.
- EGG price nearly flat 55->41 all game (deep demand) -> goose line is the stable floor.
- Even 5x PIZZA can't absorb bonus-multiplied milk (crashes anyway).
- => A sale-timing layer (our sell_lead + crash-guard, fixed) on DSM volumes = pure alpha over DSM.

## 4. Micro (executor requirements)
- FEED+CARE same-day discipline: outputs imply full care bonus (7 geese -> up to ~200 EGG/day scale; EGG sold 1250 in one game). Non-negotiable.
- FERT bought in spikes (d9/d11/d12/d14-17) -> yield-boost program on crops.
- Strawberry = early cash engine (d4+); wheat = feed AND cash crop (sales 20-90/day); carrot/tomato = rotation as land opens d9+.
- FERT trickle sales d1+ (~5/day) = free income from worker COLLECT_FERTILIZER.

## 5. Beat-DSM edges already banked (do in v1)
1. Skip mega-melon (save ~$6.5k + 15 hires d1).
2. Sale timing on wool/milk (DSM dumps into crashes).
3. Crash-pivot: DSM never converts crashed-line herd; we can cut feed earlier (it already cuts d22 — move to price-triggered).
4. Our executor stack: sell_lead, SELL-reorders, opp predictor, trims, zero-float liquidation.

## 6. New-agent architecture (agreed)
- harness/ (fresh-load env, both seats, matrix runner, ship/kill gates, frozen-spec discipline) FIRST.
- world/ (demand + visible rival supply + EV WITH coupling term; single price-truth module).
- scheduler/ (DSM-spec §1 as strategy #1, generative: intentions, not tapes) + executor/ (atomic buy->pickup->place->build chains; port v76 sale/reorder/predictor/liquidation).
- strategies/ behind plan(state)->intentions interface + arbiter (shop-latched) + counterfactual H2H picker.
- Layer contracts: trigger/action/abstain-default/telemetry; harness fails loudly on never-fire/fire-without-effect.
- Phasing: harness -> DSM-spec scheduler -> port executor -> matrix vs v76-ship + notebook agents -> submit -> strategy #2 proves flexibility.
