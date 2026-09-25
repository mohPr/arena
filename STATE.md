# STATE — current truth, 2026-09-25 (base = `agent_current.py`)

Base is a generative scheduler/executor agent (Scheduler/MarketEmit/FieldExec).
Lineage in repo: `agent_base.py` -> `var_sched5.py` -> `var_sched6.py` -> `agent_current.py`.
`FINDINGS.md` + `SPEC.md` are older analysis; this file overrides them where they differ.

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
Parity vs PASS dummy, seeds 0/1/2 — rewards **57484 / 58916 / 51435**:
- PASS: d5 herd 2C+3S x3, d6 herd>=7 + LAND x3, d10 money>=2500 x3 (~$3.1-3.5k).
- FAIL: d0 plants 11 vs 15 x3; d5 money ~$560-571 (band 634-901 was mined vs real
  opponents — vs PASS prices run higher, treat as advisory);
  d12 money $0.8-3.7k vs $8k; d15 money ~$4-11k vs $20k.
Matrix vs `opp_pipe19.py`, seed 200001: **31880 vs 151643, margin -119763 (both seats)**.
Frozen tape `main_v60` (not in repo) on same seed: 109558 vs 111396 (margin -1838).
So the gap to close is ~118k/game. Production parity got us from ~25k to ~55-65k vs
PASS; competitive money lags badly.

## Ranked open problems (work in this order)
- **P0 LIVE REGRESSION — d1 sheep escape.** d2 herd shows 2C+2S on all 3 parity seeds
  (a sheep escapes d1->d2 rollover; deficit logic rebuys ~d5, costing ~$350+ output).
  Introduced by the farmer-fert-pull change. Trace: d1h20-23, two feeders carry wheat,
  hungry cu1 sheep 2 walks away, both return idle. A claim-hygiene fix attempt produced
  byte-identical games (zero effect) — that theory is DEAD, do not re-propose it.
  Fix this first; it confounds everything else (~-6k).
- **P1 melon volume + d12/d15 curve.** d9 melon tiles 9-11 (need 12+), d10 money OK,
  but d12 $0.8-3.7k (need $8k), d15 ~$4-11k (need $20k). Drivers: late melon seeds
  (d1 wallet $7-133 fills ~1 of MELON-12 quota), sale execution (fixed: MELON batch 6,
  DSM trickles 12/6/6/6/6 — never dump 30).
- **P2 d0 plants 11 vs 15.** Only 5 of 9 prod-wheat gets planted d0 (labor shape, 4 hands
  arrive h1). DSM plants 15 d0.
- **P3 geese 0-2 vs 8-10.** Goose line OFF over delivery fears; DSM runs 8-10 (~$8-10k
  egg floor). Re-enable only with escape-proof delivery.
- **P4 feed-delivery ceiling.** Same crew feeds ~13/day that DSM feeds 20+ with.
  Best known lead: zero-move service (crop units FEED/CARE from pocket when already
  standing on the structure — our enroute path only COLLECTs today).
- **P5 wheat replant scale + P6 4th-land discipline.** Downstream of P0-P2.

## Recently landed (do not revert without A/B)
Melon sale batch 30->6; d2/d3 melon catch-up quota (top-up to 12 standing+seeds);
farmer fert collection d1 (income $43->$133); d0 trickle caps; hire burst; feed_cap;
`_fib` off-by-one fix.

## Rejected (never re-propose, all A/B'd negative)
Wallet-gated shopping (-11.8k); chain-planting (-10.9k); hire gates (-26k, bistable);
goose-heavy herds at current delivery; tomato walls >~12 standing; holding produce for
price (DSM has no sale timing); land before income (land stays d6/d9/d10);
carry-12 (strands co-feeders); ripe-only wheat reserve; ENROUTE_MAX 3->6 (-11.1k);
var_fertcol/var_fertval/var_enroute/var_shed executor variants (all lost money).

## Hard constraints (DSM parity, inviolable)
d0 = 5 head (2C+3S); melon wall d0-1; strawberry from d3; land exactly d6+d9+d10;
day-1 hands ~4; herd follows INCOME (never wallet-gated buys, never pre-bought mouths).
