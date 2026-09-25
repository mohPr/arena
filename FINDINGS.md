# Session findings — execution-side diagnosis (baseline md5 0b9235a05a4fbe886c3388dd07548f4a)

## The binding metric: moves-per-action (mv/act)
Built `our_walkcost.py` / `mine_walkcost.py` — same metric for us (live) and DSM (replays).

| metric | DSM | ours | gap |
|---|---|---|---|
| acts/unit/day (d11-17) | 11.6 | 7.5 | -4.1 |
| moves/unit/day | 9.3 | 13.2 | +3.9 |
| mv/act | 0.80 | 1.75 | +0.95 |
| 0-move actions | 51.7% | 34.8% | -17pp |
| 2+-move actions | 12.8% | 30.1% | +17pp |
| dawn commute | 1.22 | 2.09 | +0.87 |

~13 units each => ~51 moves/day that should be actions. Same step budget (both
~275 of 312 used): DSM converts 64% of steps to actions, we convert 35%.

## Per-action move cost (d11-17)
| action | ours | DSM | our vol/day | wasted moves/day |
|---|---|---|---|---|
| WATER | 1.42 | 0.84 | ~34 | ~19.7 |
| FERTILIZE | 3.57 | 1.19 | ~7 | ~15 |
| PICKUP | 1.27 | 0.36 | ~5 | ~5 |
| CARE | 0.82 | 0.12 | ~8 | ~5 |
| COLLECT_FERT | 0.99 | 0.38 | ~10 | ~6 |

Role split (var_rolecost.py): WATER and FERTILIZE waste are both crop-role.
35% of expensive (>=2 move) actions follow WATER->long walk -> the thirsty
set is sparse (we water 34/day vs DSM 58, fewer plants + survival-min policy).
19% follow COLLECT_FERTILIZER (the fert pipeline round trips).

## Engine truths confirmed this session
- Dawn reset: farmer -> default_spawn (4,4); hands cleared, re-hire, spawn on
  the 4 shed-access tiles (4,4),(5,4),(4,5),(5,5), min-occupancy. ALL units
  start on those 4 tiles every dawn => commute is symmetric for us and DSM.
- DROP/PICKUP require _is_shed_adjacent (must stand on a shed-access tile).
- Ongoing production: banks +1 per tick regardless of water; fert gives +2
  ONLY if watered that day. STRAWBERRY first=10 interval=2 maxyield=4;
  TOMATO first=8 interval=1; WHEAT/CARROT one-shot first=2; MELON first=10.
- Crops: WHEAT/CARROT/STRAWBERRY/TOMATO/MELON prices are dynamic (market).

## Production reality (seed 200001, money gauge)
d12 "91 units sold" = one-time liquidation of 64 hoarded wheat. Steady state
d13-17 is ~25-35 units/day vs DSM ~95. d15 h12 field: 48 plants, 0 ripe,
38 unwatered, 17 at cu=1 (die tonight); almost all strawberry/tomato are
immature (straw a2-a5, tomato a3-a4). Deaths only ~2-5/day (weeds), not a
mass die-off — the limit is plant count + maturity, not survival alone.
Layout: the ENTIRE southern half (y6-9) is empty (~40 tiles); structures form
a wall at y3-5 around the shed; x=4 column has weeds at y0-2.

## REJECTED interventions (pinned A/B, all reverted, baseline verified clean)
1. var_fertcol.py — restrict crop fert delivery to own column / radius 3:
   FERTILIZE 3.57->1.81, WATER 1.42->1.24 (mechanism worked!) but MONEY
   32504 vs 36148 (-3.6k; 200003 +24k, 200001 -23k). The cross-map fert walk
   is PRODUCTIVE: it doubles tier-0 wheat/carrot which compounds into feed.
2. var_fertval.py — value-score + hurdle-gate needy_plant (stop fert on
   $75 wheat when fert sells for $100): 32853 vs 36148 (-3.3k). Fert is a
   FREE animal byproduct; its sell price understates its feed value.
3. var_enroute.py — water any unwatered plant en route + ENROUTE_MAX 3->6:
   25048 vs 36148 (-11.1k). Mass arrival delays; survival-only enroute water
   is load-bearing.
4. var_shed.py — forbid building on shed-access tiles (found PASTURE+COW on
   (4,4) and (5,4), paving 2 of 4 bank lanes): 18537 vs 36148 (-17.6k). The
   (4,4) pasture is the d0 initial placement; compact-farm deliberately
   builds at the shed and 2 bank lanes already suffice (DROP 21-72/game).

## Conclusion
The field-exec layer is at a strong local optimum: four well-mechanised
efficiency fixes all lost money because the "wasted" moves are productive.
The income gap is the PRODUCTION RAMP (plant count, crop maturity, herd size
12 vs 21-25) — scheduler territory (CROP_TARGETS / land / seed / herd), which
the delegated scheduler agent owns. DSM's cheap CARE/COLLECT (0.12/0.38)
implies its structures are interspersed with crops so one unit does both with
zero-move transitions; our column-sweep + separate animal role forces the
fert/animal round trips. Closing the last gap likely needs that layout
redesign, not micro-optimisation.

## Reusable tools (in ~/agentscratch/)
our_walkcost.py, mine_walkcost.py, mine_actcost_dsm.py — mv/act metric, us vs DSM.
var_rolecost.py — action cost by role. var_prevcost.py — preceding action of
high-cost actions. gauge_field.py — full field snapshot (crop/age/yld/water).
gauge_layout.py — ASCII farm map. gauge_deaths.py — weeds/plants per day.
gauge_sales.py — money + SELL orders per day. var_probe.py — work-found vs
executed per day. ab_pin.py — pinned A/B (judge on >=5k deltas; noise floor 5k).

## Session 2026-09-25: dead-code audit + day-0 DSM copy (var_d0)
DSM replays: new_agent/"new helper/new replays2"/ (31 JSON). Canonical staged
d0 (112829119 seat0): s1 1C+5 prod ($3000->~$2464), s2 4 hires + 1C+3S
(->$585), then SELL1/BUY1 wheat churn + MELON 2 at s7/s9/s12 + WHEAT seeds to
~10; ends $6-8 with 9W+6M standing, 5 head, 4 hands.

### Dead / hurting code confirmed in agent.py (all verified, none yet removed
### from agent.py — variants only)
1. `st['rush10'/'rush11']` (sched 351-354) SET but never READ — dead.
2. `t == 'LOCKED' or t == 'LOCKED'` (scan 106) — duplicated rot (harmless).
3. Qty capped by ORDER SLOTS: `min(qty-done, 10-len(orders), cap)` (P 604, S
   617) truncated d0 S10->5, P6->4 into broke retries — hurting (measured).
4. `st['req']` counts EMISSIONS not landings; engine unit-loop partial-fills
   (verified in kaggriculture._process_market/_commit_unit) make overcounts
   burn quota — hurting (d10 -18k same root; d0 $7 failing prod buys).
5. Wheat reserve on PLACED herd (397) sold 3 of 4 d0 feed (5 owned, 0 placed)
   into a $7 emergency-feed spiral — hurting (measured s0-s1).
6. HIRE 2/step cap (451) vs DSM 4-8 dawn burst; H9 needs 5 steps — hurting
   morning labor. (Fix in var_d0: burst 4.)
7. `soft_gated` animal block leaves `spend` unbound on gated days — latent
   NameError; var_d0 staging tripped it into 24 errors = a DEAD DAY 1.
8. `structure_deficit` +1 phantom (need = herd+1): 1 wasted pasture+coop
   (engine: 1 animal/structure, verified PLACE). Minor hurt.
9. OFF-flag branches (STRIDE/GOOSE_LINE/AFFORD_GATE ~40 lines) never execute —
   dead weight that makes the file hard to reason about.
10. HIRE-orders-vs-landings mining error: "DSM d1: 9 hires" comment mined
    EMITS; landed median is 4 hands (12 replays: 4,1,4,4,4,9,9,3,3,3,2,3).

### var_d0 (~/agentscratch/var_d0.py): staged d0-1 package
HIRE burst 4/step; 1C-first then rest (matches DSM 1+4 split, keeps $1849
buffer); P-before-S d0; wallet staging d0-1 (A60/P60/S30 buffers); reserve on
OWNED; wheat sells trickle-capped 2/step d<=2; d1 H9->H4; LOCKED dup fixed.
Census 200001 vs DSM: d0 13 (7W+6M) vs 15, d1 15 vs 20, d2 17 (9W+2S+6M, herd
5/5, 0 errors) vs 18 — herd survival FIXED (baseline lost a sheep d2), but a
MELON GAP opened (6 vs 10): d1 feed need (full feeding 5/day) + P-before-S
crowds out the $80 melon top-up, and fert collection runs 2/day vs DSM 5-6
(+$200 vs +$500), so the top-up never funds. DSM underfeeds ~75% (1827
gap-0 vs 623 gap-1); we feed 100% — safer but cash-hungry.
A/B pinned 5-seed: 32462 vs 36148 (-3.7k, INSIDE 5k noise => INCONCLUSIVE,
leaning neg; +5.7k on 200002, -3.3..-8.5k rest). Ablation var_d0b (H4->H9
restore): 32466 (-3.7k, same mean, seed signs flip +9.8k/-16.5k) => the H4
cut was NOT the loss; staging reshuffles ±16k/seed with zero mean gain.
NOT ADOPTED. Lesson: baseline's bugs accidentally fund labor (truncation
left $90 -> 9 hires land -> wins); copying DSM emits without DSM's
closed-loop deficit buying doesn't transfer. Next layer is d1 melon/fert
rate (collect 2->5/day) + walk efficiency, not market timing.

## Session 2026-09-25b: 4-step combined push (var_big) -- REJECTED
Plan: feed/fert cash (bank-first) + herd growth + farm growth + walks (hire
burst), all together in ~/agentscratch/var_big.py on top of agent.py.
Census found the stall: d1-5 income ~$100/day not DSM's ~$500 (fert collected
4-7/day = DSM rate, but banked at h20 not midday: carriedF=3 at h16, money
$4), so the d6 herd wave never funded (herd 4-6 until d12, money <$800).

### Changes tried (all conclusive, 10-seed pinned A/B)
1. Fert BANK-FIRST (bank pocket at 2+, or any at h12+): moves ~$300-400 from
   evening to midday. Alone (var_bank.py): 30700 vs 33452 (-2.8k, noise,
   but +-25k/seed: 200006 +24k, 200008 +17k, 200001 -25k, 200004 -19k).
2. HIRE burst 2->5/step (full crew by h2 not h12).
3. Feed runway cap (never hold > ~2 days feed: 2*herd+2-shedW).
4. REVERTED ordered-feed counting (-15.6k on 5-seed): counting promised feed
   as cover ran the herd to 14-16 unfunded -> escapes -> weeds (49->31
   plants on 200004). The strict in-hand gate is load-bearing.
5. Farm-paced herd cap (13 max until 50+ plants AND $2k): first version gave
   +25k on 200003 and +12k on 200002, still -13k on 200004.
6. Scaled afford cushion ($100 -> $100+25*herd): NEVER BINDS (splurges run on
   intraday flow, not savings) -- dead change, left in only as comment.
var_big 10-seed: 32439 vs 33452 (-1k, tie). var_bank 10-seed: 30700 (-2.8k,
tie). Both AMPLIFY variance (+-30k/seed) with zero mean gain.

### Mechanism learnt (the scale trap)
Every change that frees cash converts to head #14-21, which this farm's
income (~$1500/day at 40 sales/day) cannot feed: escapes -> weeds -> field
halves -> -13..-30k. Baseline survives by holding ~13-16 FED (banks $34k
late on 200004 with plants 55->18!). DSM sustains 21-25 because its farm
sells 95/day. Herd must follow farm income, not cash flow; timing-of-cash
tweaks cannot fix a labor-productivity gap -- they only move the boom/bust
earlier. The binding constraint remains: sales/day (labor) -> income ->
sustainable herd. Next: plant-count ramp + walk structure, not market timing.

## Session 2026-09-25c: walk forensics + scheduler push (5 variants)

### Walk forensics (all measured, seed 200001 unless noted)
- Same crew, 2.6x output: DSM hires 9->12/d d8-16, ours 9->12/d. DSM crew
  ~250 acts/d, ours ~95. NOT headcount: mv/act 1.75 vs 0.80 at same hires.
- Barn embed (var_layout: free_tile prefers crop-surrounded tiles; d10 layout
  verified DSM-like, barns inside crop mass): mv/act 1.73 vs 1.75. NO EFFECT.
  Barn position is not the driver. PARKED (not A/B'd, no mechanism).
- Per-action walk budget d11-17 (act_walk.py): WATER 226 acts/322 mv (34%,
  1.42/act), FERTILIZE 44/136 (15%, 3.09), FEED 84/107 (11%, 1.27), PLANT 67/69,
  DIG 30/62, COLLECT 68/60, CARE 56/44, PICKUP 38/42. WATER+FERTILIZE = 49%.
- Column discipline is GOOD (water_where.py): units water in 1-2 cols each,
  3-7 waters/d. Leak is WITHIN-column scatter, not roaming.
- DSM act mix from replay (d11-17/d): WATER 61, HARVEST 25, COLLECT 21,
  CARE 20, FEED 20, PLANT 12, FERTILIZE 11 = ~182 useful/d vs our ~99.
  EVERYTHING scales ~2x with assets (21 vs 12 head, 70 vs 45 plants).
  CONCLUSION: the act gap is an ASSET gap, not efficiency. mv/act gap follows
  from target density (nearest-target walks shrink when targets double).
- Chain-plant (plant underfoot when no HARV anywhere; post-plant water free
  via nearest): PLANT 1.03->0.69/act, HARVEST 0.53->0.35. BUT 5-seed A/B
  25281 vs 36148 (-10.9k, every seed worse). REJECTED. Mechanism: under water
  saturation every water act is urgent; chain-plant STEALS water meant for a
  dying tile and gives it to a fresh sprout (priority inversion). Any
  reordering that delays water loses; only same-water-fewer-moves can win.
- Parity water (row-parity survival gate) + fert modulo: REVERTED BEFORE A/B.
  Reasoning flaw found in time: cu>=1 tiles skipped on off-parity days die
  (cu=2). Weeds didn't explode only via the stand-and-water backstop
  (crop_work L1720 waters underfoot regardless) + churn. Fragile, unexplained,
  cut. Lesson: survival-minimum watering has NO freedom (cu>=1 set is forced);
  only the phase pattern is choosable, and only via planting dates.

### DSM ledger mined (dsm_ledger.py + our_ledger.py, replay 112829119)
- DSM d0: $6 end, 4 hires, 2C+3S, M6+W12 seeds, 9W feed, 15 plants.
  d1: 9 HIRE emits (4 land!), fert 5 sold (~$500 = the whole early economy),
  melon +12 (wall 10). d2-3: straw 10+10 (10 standing d3), wheat cashed out.
  d4-5: fert 5/d, money $13->$367. d6 WAVE: wool 18 + land + 5C + 4G (herd
  5->12, structs 12). d7: fert 13. d8: milk 12. d9: land #2, +2C+3G, herd 18.
  d10: melon 36 sold, land #3 (tiles 100), money $148 (spent all). d11+:
  eggs 10/d, money 3x every 2 days. Fert embargo till d9 CONFIRMED (sells
  4-13/d throughout; applies d10+ but keeps selling).
- OUR divergence line-by-line: d1 HIRE 40 emits + emergency wheat 138 (retry
  flood; DSM 9+6); melon wall 6-7 (seeds bought 12 but req burned on broke
  emits -> no retry when cash lands -> morning starve); straw 4 days late
  (underbought d2-3); d6 NO wave (shopping has no animals; +1C vs +9);
  no geese ever (egg engine missing: DSM 10-27 eggs/d late).

### Scheduler variants (all pinned 5-seed vs 36148)
- var_sched (shortfall re-emit + melon8 + straw8/8 + P16 + d6 wave): 22858
  (-13.3k). Shortfall attempt-1 was a FAUCET (planter consumption re-opened
  quota: 50 melon/163 wheat churn). Attempt-2 wallet-cover fixed the faucet
  but kept the loss. d6 wave landed (herd 12 by d11) then escape treadmill
  d15-27 (herd 16->14->16, replacements burn ~$1k/cycle). Delivery ceiling.
- var_sched2 (no wave): 22858 IDENTICAL to the digit (reproduced twice).
  Learning: htgt was never the lever; feed_cap/room gates bind first, so the
  wave ladder is dead code under pin. (Ledger-vs-AB confound warning: ledgers
  run without LINE_FORCE -> different shop line. Only pinned A/B judges.)
- var_sched3 (wallet-cover ONLY): 24386 (-11.8k). Wallet-cover is the poison,
  mechanism unexplained (early ledgers look RICHER: d13 +$2.6k; mid-game
  earnings halve anyway). Morning starve is a SYMPTOM of thin wallet; moving
  buy timing moves the thinness + breaks hidden dependencies. REJECTED.
- var_sched4 (hire-gate: hires wait while seeds unfunded): 9657 (-26k), three
  near-zero seeds (84/696/462) + one +11k win (44400). BISTABLE Russian
  roulette: gate delays hires on exactly the stressed games where morning
  water is life-or-death -> weed death-spiral; when it survives, seeds-first
  pays big. REJECTED (variance disqualifies, mean catastrophic).
- var_sched5 (seeds-first ORDER: HIRE emission deferred after consumables;
  engine fills list order): 34262 (-1.9k, TIE). +6.7k/-18k/+15k/+1k/-14k.
  Real mechanism (scores move, no wipeouts) but zero-sum across seeds:
  morning-seeds vs morning-hands is a seed-dependent trade, not a free fix.
  PARKED (only non-harmful scheduler change; needs variance taming to adopt).

### Net mechanism learnt (load-bearing equilibrium)
The baseline's bugs form a mutually-supporting equilibrium: hires drinking
afternoon cash (covers labor), req-burn (caps seed spend), trickle herd
(fits delivery). Each isolated "fix" breaks a hidden dependency:
wallet-cover -> ? (-12k, unexplained: respect it); chain-plant -> steals
urgent water; wave -> escape treadmill; hire-gate -> death spiral. DSM's
d1 (4 hands + full seeds) vs ours (9 + starved) is a different POINT on the
labor-vs-assets frontier, not a free upgrade. NEXT: feed-delivery ceiling
(field-side: what lets DSM feed 20/d with the same crew?) is the one wall
that unlocks herd 15+ and DSM-scale assets. Everything else is rearranged
thinness. If delivery can't be fixed, ~36k is this architecture's optimum.

## Session 2026-09-25d — agent1/scheduler verdict + HERD LADDER (var_sched6) ADOPTED
- External proposals judged: agent2 REJECTED as evidence (tables formatted as
  measurements but untestable from outside; hire-price curve invented; C3 herd
  cap needs nonexistent sales/day plumbing and never opens). Agent1 USEFUL
  (honest predictions, respected all 6 DSM constraints, falsifiers per change,
  Change-3 matches our scale-trap lesson) with overrides: its engine
  "corrections" (wheat 1.0x, fert 1.5x) contradict our engine-source reads;
  its tomato 24-41 standing exceeds measured water capacity; its 8 marginal
  geese contradict our delivery-ceiling A/B. Adopted 2 ideas only: seeds-first
  deficit loop (= sched5, already parked) + day-cap herd ladder.
- var_sched6 (sched5 base + LADDER: total owned cap 5 d0-5, 8/9/10/11/12 d6-10,
  13 d11+, applied in BOTH groom and room calcs): 5-seed 41164 vs sched5
  34262 (+6,902, 4/5 up, worst -1.4k tie). 10-seed 39024 vs 34104 (+4,920 >
  3.5k floor): deltas +13.1k/+5.3k/+12.7k/-1.4k/+4.8k/+10.9k/+0.4k/+0.6k/
  -8.0k/+10.7k (7 up, 2 ties, 1 loss on 200009). Vs true baseline 33452:
  +5,572. NEW BEST. ADOPTED as the base for delivery-ceiling work.
- Census 200001 (reward 63413): herd climbs 5->6->7->8->12->13 EXACTLY on the
  ladder, placed==herd every day from d7, ZERO escapes after d6, shedW
  positive all game, money compounds d15 $4k -> d20 $18k -> d29 $60k, plants
  40-56 mid-game. Mechanism confirmed: fitting the herd to OUR delivery
  (not DSM's) kills the escape treadmill. One early escape d1->d2 (5->4).
- Net update: delivery ceiling is now CONFIRMED binding (herd 13 fits, 21
  doesn't) AND partially bypassed. Next: raise the ceiling field-side
  (feed-trip batching? dedicated feeder? dump-trip separation?), then release
  the ladder toward DSM's 21. Seed 200009 (-8k) is the canary: ladder too
  tight where early income could have supported more — a money-released
  ladder (cap lifts when wallet proves income) is the follow-up variant.
