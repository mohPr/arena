# STATE — current truth, 2026-09-25 (base = `agent_current.py`)

Base is a generative scheduler/executor agent (Scheduler/MarketEmit/FieldExec).
Lineage in repo: `agent_base.py` -> `var_sched5.py` -> `var_sched6.py` -> `agent_current.py`.
`FINDINGS.md` + `SPEC.md` are older analysis; this file overrides them where they differ.
Round history: P0 (d1 sheep escape) FIXED via urgency-first feeding — base now
contains it; parity rewards changed, do not compare against pre-fix numbers.

## Reference: DSM champion (mined from replays, engine-verified)
- d0: 2 COW + 3 SHEEP + 6 MELON seed + 15 WHEAT seed + 9 prod wheat + 4 hires, spend to ~$0.
- d5: money 634-901, herd still 2C+3S. d6: ALWAYS 1st LAND + herd wave (~8 head).
- d10-15 melon spike: money ~$3k->$7k->$10k->$26k on d10/11/12/15. d15 herd 20-30.
- Mid-game rates: sells ~95 units/day (ours ~35), feeds ~20+/day (ours ~12-13),
  herd 21-25 (ours capped 13), CARE 0.12 moves/act (ours 0.82).
- d1 behavior (replay 112076061): hires 8 at h1, farmer collects fert h1/h2/h4,
  thin-wallet trickle (money $1-42 all day), BUY_SEED MELON 2/step, BUY_PRODUCT WHEAT 2.

## Engine rules (kaggle-environments 1.32.7, verified in code)
- 720 steps, 24/day, 30 days, start $3000, board 10x10, 10 market orders/step.
- HIRE cost = engine `_fib` (1,1,2,3,5...). FEED = 1 WHEAT/animal/day, all species.
- 2 consecutive unfed days = escape (permanent). Hands reset nightly.
- WATER ticks yield ONLY in window `[(maxday+1)//2, maxday]` (+2 if fertilized, else +1),
  capped at maxyield. MELON: window age 6-12, first harvest day 10.
- One-shot crops are SINGLE harvest (plant removed). FERTILIZER active 3 days.
- SELL fills partial (no wallet wall). PLANT is atomic against a shared per-step seed budget.
- Shed tiles: (4,4),(5,4),(4,5),(5,5). Structures cluster near shed (free_tile weights manhattan-to-(4,4) x4).

## Measured numbers (reproduce before changing anything, see RUN.md)
Parity vs PASS dummy, seeds 0/1/2 — rewards **57255 / 66496 / 62566**:
- PASS: d2 herd 2C+3S x3 (P0 fixed); d5 herd 2C+3S x3; d6 herd 8-10 + LAND x3;
  d10 money>=2500 on seed 0 ($2937) but FAIL on seeds 1 ($2088) and 2 ($103).
- FAIL: d0 plants 11 vs 15 x3; d5 money ~$1388-1395 (above the 634-901 band mined
  vs real opponents — the P0 fix moved spend earlier into a bigger d6 wave; vs PASS
  the band is advisory); d12 money ~$3.8-4.2k vs $8k; d15 money ~$4-7.2k vs $20k.
Matrix vs `opp_pipe19.py`, seed 200001: **27385 vs 147891, margin -120506 (both
seats)**. Frozen tape `main_v60` (not in repo) on same seed: 109558 vs 111396
(margin -1838). Gap to close is ~118.7k/game, all in OUR agent.
External intel (measured by a helper agent, not yet re-verified here): vs pipe19
the base suffers ~16-17 escapes/game (bleed all game, not just d1); seed 200003
loses pinned but GAINS unpinned (+4.2k) — pinned/unpinned disagree there.

## Open shortfalls, by cash size (the scoreboard — HOW is your call)
- d12/d15 curve: d12 ~$4k vs $8k, d15 ~$4-7k vs $20k. Biggest money, cause unknown.
- Feed delivery: same crew serves ~13 feeds/day that DSM serves 20+ with.
- d0 plants 11 vs 15 (only 5/9 prod-wheat planted d0; 4 hands arrive h1).
- Geese 0-2 vs DSM 8-10 (~$8-10k egg floor, needs escape-proof delivery).
- CARE cost 0.82 moves/act vs DSM 0.12; sells ~35 units/day vs ~95.
- Wheat replant scale, 4th-land discipline. Downstream of the above.

## Recently landed (in the base — resubmitting any of these = instant reject)
Urgency-first feeding (feed cu>=1 animals before cu=0, fixed the d1 escape);
melon sale batch 30->6; d2/d3 melon catch-up quota (top-up to 12 standing+seeds);
farmer fert collection d1 (income $43->$133); d0 trickle caps; hire burst; feed_cap;
`_fib` off-by-one fix.

## Rejected (never re-propose, all A/B'd negative or byte-identical)
Wallet-gated shopping (-11.8k); chain-planting (-10.9k); hire gates (-26k, bistable);
goose-heavy herds at current delivery; tomato walls >~12 standing; holding produce for
price (DSM has no sale timing); land before income (land stays d6/d9/d10);
carry-12 (strands co-feeders); ripe-only wheat reserve; ENROUTE_MAX 3->6 (-11.1k);
var_fertcol/var_fertval/var_enroute/var_shed executor variants (all lost money).

## Hard constraints (DSM parity, inviolable)
d0 = 5 head (2C+3S); melon wall d0-1; strawberry from d3; land exactly d6+d9+d10;
day-1 hands ~4; herd follows INCOME (never wallet-gated buys, never pre-bought mouths).
