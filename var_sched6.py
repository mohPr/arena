# new_agent v0.1 — DSM-spec scheduler (generative intentions) + greedy field executor.
# Architecture: harness-first, scheduler/executor split, layer contracts w/ telemetry.
# Spec: new_agent/SPEC.md (mined from 34 DSM replays).

# ---- engine tables (kaggle-environments 1.32.7 semantics) ----
CROPS = {
    'WHEAT':      {'seed': 10,  'first': 2,  'maxday': 4,  'interval': 0, 'maxyield': 6, 'ongoing': False},
    'CARROT':     {'seed': 20,  'first': 2,  'maxday': 3,  'interval': 0, 'maxyield': 4, 'ongoing': False},
    'TOMATO':     {'seed': 50,  'first': 8,  'maxday': 8,  'interval': 1, 'maxyield': 4, 'ongoing': True},
    'STRAWBERRY': {'seed': 100, 'first': 10, 'maxday': 10, 'interval': 2, 'maxyield': 4, 'ongoing': True},
    'MELON':      {'seed': 80,  'first': 10, 'maxday': 12, 'interval': 0, 'maxyield': 6, 'ongoing': False},
}
ANIMALS = {
    'GOOSE': {'cost': 300, 'structure': 'COOP',    'product': 'EGG',  'interval': 1},
    'COW':   {'cost': 400, 'structure': 'PASTURE', 'product': 'MILK', 'interval': 2},
    'SHEEP': {'cost': 500, 'structure': 'PASTURE', 'product': 'WOOL', 'interval': 3},
}
PRODUCTS = ['WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'MELON', 'EGG', 'MILK', 'WOOL', 'FERTILIZER']
SELLABLE = list(PRODUCTS)
SHED_TILES = [(4, 4), (5, 4), (4, 5), (5, 5)]

# ---- telemetry + layer contracts ----
T = {'steps': 0, 'errors': 0, 'sched_fire': {}, 'exec_tasks': {}, 'market_orders': 0,
     'alarms': []}

def REPORT():
    out = dict(T)
    out['sched_fire'] = dict(T['sched_fire'])
    out['exec_tasks'] = dict(T['exec_tasks'])
    return out

class Layer:
    """Contract: trigger() decides, run() acts, every fire is counted.
    Harness fails loudly on never-fire."""
    NAME = 'base'
    def __init__(self):
        self.fired = 0
    def trigger(self, ctx):
        return True
    def run(self, ctx):
        raise NotImplementedError
    def __call__(self, ctx):
        if self.trigger(ctx):
            self.fired += 1
            T['sched_fire'][self.NAME] = T['sched_fire'].get(self.NAME, 0) + 1
            self.run(ctx)

# ---- per-seat persistent state (fresh namespace per game => safe) ----
STATE = {}

def getst(seat):
    st = STATE.get(seat)
    if st is None:
        st = STATE[seat] = {'day': -1, 'req': {}, 'line': None}
    return st

# ---- world model (ctx) ----
class Ctx:
    def __init__(self, obs):
        self.obs = obs
        self.seat = int(obs.get('player', 0)) if isinstance(obs, dict) else int(getattr(obs, 'player', 0))
        g = (lambda k, d=None: obs.get(k, d)) if isinstance(obs, dict) else (lambda k, d=None: getattr(obs, k, d))
        self.day = int(g('day', 0)); self.hour = int(g('hour', 0)); self.step = int(g('step', 0))
        farms = g('farms', [])
        self.farm = farms[self.seat]
        self.rival = farms[1 - self.seat] if len(farms) > 1 else {}
        priv = g('private', {})
        pg = (lambda k, d=None: priv.get(k, d)) if isinstance(priv, dict) else (lambda k, d=None: getattr(priv, k, d))
        self.shed = dict(pg('shed', {}) or {})
        self.seeds = dict(pg('seeds', {}) or {})
        self.invs = list(pg('inventories', []) or [])
        mk = g('market', {}) or {}
        mkg = (lambda k, d=None: mk.get(k, d)) if isinstance(mk, dict) else (lambda k, d=None: getattr(mk, k, d))
        self.prices = dict(mkg('prices', {}) or {})
        town = g('town', {}) or {}
        tg = (lambda k, d=None: town.get(k, d)) if isinstance(town, dict) else (lambda k, d=None: getattr(town, k, d))
        self.shops = list(tg('unlocked_shops', []) or [])
        fg = (lambda k, d=None: self.farm.get(k, d)) if isinstance(self.farm, dict) else (lambda k, d=None: getattr(self.farm, k, d))
        self.money = float(fg('money', 0))
        self.farmer = list(fg('farmer', [4, 4]))
        self.hands = [list(h) for h in (fg('hands', []) or [])]
        self.hires_today = int(fg('hires_today', 0))
        self.tiles = fg('tiles', []) or []
        self.orders = []          # market orders emitted this step
        self.unit_cmds = {}       # actor_idx -> command
        # derived
        self.herd = {'COW': 0, 'SHEEP': 0, 'GOOSE': 0}
        self.standing_crops = {}
        self.scan_tiles()
        while len(self.invs) < 1 + len(self.hands):
            self.invs.append({})
        # owned animals incl shed + carried (for on-demand building)
        self.owned = dict(self.herd)
        for a in ANIMALS:
            self.owned[a] = self.owned.get(a, 0) + int(self.shed.get(a, 0) or 0)
            for inv in self.invs:
                self.owned[a] += int((inv or {}).get(a, 0) or 0)

    def scan_tiles(self):
        self.empty_tiles = []
        self.plants = []      # (x, y, tile)
        self.structs = []     # (x, y, tile)
        self.weeds = []
        for y, row in enumerate(self.tiles):
            for x, t in enumerate(row):
                if t == 'LOCKED' or t == 'LOCKED':
                    continue
                if t is None:
                    self.empty_tiles.append((x, y))
                elif isinstance(t, dict):
                    if t.get('kind') == 'WEED':
                        self.weeds.append((x, y))
                    elif t.get('kind') == 'PLANT':
                        self.plants.append((x, y, t))
                        self.standing_crops[t.get('crop')] = self.standing_crops.get(t.get('crop'), 0) + 1
                    elif 'animal' in t:
                        self.structs.append((x, y, t))
                        a = t.get('animal')
                        if a in self.herd:
                            self.herd[a] += 1
                    elif t.get('kind') in ('COOP', 'PASTURE'):
                        self.structs.append((x, y, t))

    def price(self, item):
        try:
            return float(self.prices.get(item, 1) or 1)
        except Exception:
            return 1.0

# ---- helpers ----
def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def step_toward(pos, tgt):
    x, y = pos
    tx, ty = tgt
    if x < tx: return ['EAST']
    if x > tx: return ['WEST']
    if y < ty: return ['SOUTH']
    if y > ty: return ['NORTH']
    return None

def shed_adjacent(pos):
    # engine _is_shed_adjacent: standing ON one of the 4 inner-corner access tiles.
    # (Neighbors are NOT adjacent: PICKUP/DROP/PLACE-shed emitted there silently fail.)
    return tuple(pos) in [(4, 4), (5, 4), (4, 5), (5, 5)]

def nearest_shed_tile(pos):
    return min(SHED_TILES, key=lambda t: manhattan(pos, t))

def bank_cmd(ctx, st, inv, exclude=('WHEAT', 'FERTILIZER')):
    """Cap-safe shed bank. DROP dumps the whole inventory and the engine
    destroys whatever doesn't fit past the 100-slot cap; ['PLACE', item, n]
    moves only what fits and keeps the excess carried. So: DROP when the
    whole load fits (one action, everything), PLACE the biggest stack when
    only part fits, hold (None) when the shed is full -- holding is free,
    a shed trip for a destroyed bank is not. A per-step room budget (same
    pattern as sleft/wleft/aleft) keeps siblings banking in the same step
    from overselling the same room."""
    if st.get('roomstep') != ctx.step:
        try:
            total = sum(int(v or 0) for v in ctx.shed.values())
        except Exception:
            total = 0
        st['roomstep'] = ctx.step
        st['roomleft'] = 100 - total
    room = int(st.get('roomleft', 0) or 0)
    no = set(exclude) | set(ANIMALS)
    stacks = [(int(v or 0), k) for k, v in inv.items()
              if int(v or 0) > 0 and k not in no]
    if not stacks:
        return None
    carried = sum(int(v or 0) for v in inv.values())
    # DROP-destroys protected stacks: DROP empties the WHOLE inventory, so
    # an excluded item riding a DROP is banked anyway and sold by the next
    # market pass -- the second root cause of FERTILIZE 0/day (a feeder's
    # pocket dumped with its produce). Only DROP when nothing excluded is
    # carried; otherwise PLACE the biggest unprotected stack (one action,
    # same cost, the protected stack stays in the pocket for its own path).
    protected = sum(int(v or 0) for k, v in inv.items()
                    if int(v or 0) > 0 and k in exclude)
    if carried <= room and protected == 0:
        st['roomleft'] = room - carried
        return ['DROP']
    stacks.sort(reverse=True)
    v, k = stacks[0]
    n = min(v, room)
    if n <= 0:
        return None
    st['roomleft'] = room - n
    return ['PLACE', k, n]

# ---- scheduler: DSM-spec day script (strategy #1) ----
# day -> shopping list in priority order (HIRE, LAND, ANIMAL, PROD, SEED), plus crop targets.
def d6_branch(shops):
    yarn = 'YARN_STORE' in shops
    pizza = 'PIZZA_SHOP' in shops
    egg = 'BAKERY' in shops or 'BRUNCH_SPOT' in shops
    ice = 'ICE_CREAM_SHOP' in shops or 'SMOOTHIE_SHOP' in shops
    if yarn:
        return 'sheep'
    if pizza or ice:
        return 'cow+'
    if egg:
        return 'mixed'  # geese earn with bakeries; cows fill rest
    return 'mixed'

# Match town drain (day-24, 8 shops): milk ~19/day ≈ 12-14 cows, wool ~13/day
# ≈ 10 sheep with yarn, egg ~13/day ≈ 6-8 geese. Overproducing linear/sq goods
# floors them at $1 (+59 wool / +76 milk / +62 straw net over I0).
LINE_HERD = {
    'sheep': {'COW': 8,  'SHEEP': 12, 'GOOSE': 5},
    'cow+':  {'COW': 12, 'SHEEP': 3,  'GOOSE': 6},
    'mixed': {'COW': 9,  'SHEEP': 4,  'GOOSE': 8},
}

def herd_target(day, line):
    """Cumulative owned-animal targets (shed+carried+placed). Self-healing deficit."""
    if day == 0:
        return {'COW': 2, 'SHEEP': 3, 'GOOSE': 0}  # DSM d0: 2C+3S ($2300); the 3rd sheep's d6 wool (~6u w/ care bank) funds LAND
    if day < 6:
        return {'COW': 2, 'SHEEP': 3, 'GOOSE': 0}
    # ramp: d6 bulk buy is deficit-closed over d6-d12 (budget-capped each step)
    t = dict(LINE_HERD.get(line, LINE_HERD['mixed']))
    if line == 'sheep':
        # progressive sheep fill (DSM: 6-8 d6, +3 d8, +3-4 d9-10, +1-4 d12)
        if day < 8:   t['SHEEP'] = min(t['SHEEP'], 8)
        elif day < 10: t['SHEEP'] = min(t['SHEEP'], 11)
        elif day < 12: t['SHEEP'] = min(t['SHEEP'], 14)
        if day >= 22:
            t = dict(t); t['SHEEP'] = 6  # endgame: let crashed wool herd go
    else:
        if day < 8:   t['COW'] = min(t['COW'], 6); t['GOOSE'] = min(t['GOOSE'], 4)
        elif day < 10: t['COW'] = min(t['COW'], 9)
        elif day < 12: t['COW'] = min(t['COW'], 11)
    if day >= 26:
        t['GOOSE'] = 0  # stop egg replacements; crash-prone late
    if day >= 28:
        t = {k: 0 for k in t}  # terminal: no replacements
    return t

# HERD LADDER (agent1 Change-3 core, adapted): cap TOTAL owned head by day so
# the d6 wave lands inside measured feed-delivery capacity (~13 fed/day with
# 4 animal units). Existing gates (feed_cap on shed wheat, herd_cap on crew,
# 4/day buy cap, unplaced-blocks-buys) still let owned jump 5->21 at d6 on a
# cash wave; the bought mouths then outrun delivery -> unfed streaks ->
# escapes (sched3/sched4 ablations). DSM paces to 21 by d11 because DSM
# DELIVERS 21; we deliver ~13, so fit the herd to our delivery. If this wins,
# delivery is confirmed as THE wall and the next step is raising the ceiling,
# then releasing the ladder. A/B isolator: sched5 base tied (-1.9k), so any
# delta here is the ladder alone.
LADDER = [(0, 5), (6, 8), (7, 9), (8, 10), (9, 11), (10, 12), (11, 13)]

def ladder_cap(day):
    c = 5
    for d, v in LADDER:
        if d <= day:
            c = v
    return c

def land_want(day, st):
    """Cumulative land target: DSM buys exactly 3 (d6+d9+d10). Extra quadrants
    only when genuinely rich (sustained income, not one payday)."""
    w = (1 if day >= 6 else 0) + (1 if day >= 9 else 0) + (1 if day >= 10 else 0)
    return w

def shopping(day, ctx, st):
    """Return list of (kind, item, qty) in priority order for this day."""
    L = []
    def H(n): L.append(('HIRE', '', n))
    def LD(n): L.append(('LAND', '', n))
    def A(sp, n): L.append(('A', sp, n))
    def P(it, n): L.append(('P', it, n))
    def S(cr, n): L.append(('S', cr, n))
    if day == 0:
        # DSM d0 (mined 7 games): 2C+3S ($2300) + 6 MELON ($480) + ~10 WHEAT
        # seed ($100) + ~9 prod wheat ($225) + 4 hires; sells 6 wheat; ends ~$0.
        # The 3rd sheep is the d6 LAND money (d6 wool ~18u w/ care bank).
        # Feed trimmed 9->6: the 10-orders/step cap fragmented d0 buys across
        # t0-t2 and seeds landed late (seedlings died unwatered). 8 orders now
        # all fire t0; d1 tops feed back up (new animals survive d0 unfed).
        H(4); A('COW', 2); A('SHEEP', 3); S('MELON', 6); S('WHEAT', 10); P('WHEAT', 6)
    elif day == 1:
        # DSM d1: 9 hires, ~6 feed wheat, melon top-up, NO straw (cash -> d2-3
        # wall). Income = ~5 fert sales only; straw seed now would starve hires.
        H(9); P('WHEAT', 6); S('MELON', 6); S('WHEAT', 6)
    elif day == 2:
        # NO seed restocking while the field is full: d2 income (fert sales)
        # must become d3 hires, not seeds. The replay champion buys 0 wheat
        # seed and ~4 melon top-up d2 with 20 tiles standing, hires 5/5/6 on
        # d2/d3/d4, and only then starts the strawberry wall (d3). Buying
        # seeds into an unwaterable field starved d3 hires and the d3-4 crop
        # died into weeds (mature-harvest economics: no green wheat cash d2).
        H(6); P('WHEAT', 4); S('STRAWBERRY', 4)
    elif day == 3:
        H(6); S('STRAWBERRY', 6)
    elif day == 4:
        H(6); P('WHEAT', 2); S('STRAWBERRY', 2)
    elif day == 5:
        H(6); P('WHEAT', 2)
    elif day == 6:
        H(8)
        P('WHEAT', 12); S('STRAWBERRY', 8); S('WHEAT', 12)
        # species branch at d6 (herd buy follows in MarketEmit via htgt)
    elif day == 7:
        H(9); P('WHEAT', 14); S('WHEAT', 6); S('STRAWBERRY', 8)
    elif day == 8:
        H(9); P('WHEAT', 16); S('WHEAT', 8)
    elif day == 9:
        H(10); P('WHEAT', 12); S('WHEAT', 18)
        S('TOMATO', 3); S('CARROT', 4); S('STRAWBERRY', 8); P('FERTILIZER', 10)
        if 'YARN_STORE' in ctx.shops and st['line'] != 'sheep' and ctx.herd['SHEEP'] < 7 and not LINE_FORCE:
            st['line'] = 'sheep'  # late yarn: switch to sheep line, deficit logic tops up
    elif day == 10:
        H(14); P('WHEAT', 40); S('WHEAT', 16)
        S('CARROT', 6); S('TOMATO', 2); S('STRAWBERRY', 8)
    elif day == 11:
        H(11); S('WHEAT', 16); P('WHEAT', 16); P('FERTILIZER', 24)
        S('CARROT', 6); S('TOMATO', 2); S('STRAWBERRY', 8)
    elif day == 12:
        H(11); S('WHEAT', 12); P('WHEAT', 16); P('FERTILIZER', 22)
        S('CARROT', 6); S('TOMATO', 5); S('STRAWBERRY', 6)
    elif 13 <= day <= 27:
        H(12 if day < 26 else 10)
        S('WHEAT', 12); S('CARROT', 8); P('WHEAT', 16)
        if day % 2 == 0: P('FERTILIZER', 16)
        S('TOMATO', 4); S('STRAWBERRY', 8)
        if day % 3 == 0: S('STRAWBERRY', 4)
    elif day >= 28:
        H(6)
        # d28-29: final bank-rush hands. Hands are DAY-LABOR (farm['hands']
        # resets nightly), so d29 hires act d29 (hired step s acts from s+1)
        # and earn their fib back harvesting/banking the final field. Cutting
        # d29 hires left the farmer alone on the last day (-1.4k on 200003).
        # Seeds/animals stay unbought: they can never pay back.
        # no feed buys — starve crashed lines, keep profitable cows fed via shed wheat only
    return L

CROP_TARGETS = [
    (0,  {'WHEAT': 12, 'MELON': 12}),
    (1,  {'WHEAT': 20, 'MELON': 12, 'STRAWBERRY': 6}),
    (2,  {'WHEAT': 22, 'MELON': 14, 'STRAWBERRY': 14}),
    (6,  {'WHEAT': 28, 'MELON': 14, 'STRAWBERRY': 24}),
    (9,  {'WHEAT': 24, 'MELON': 12, 'STRAWBERRY': 24, 'TOMATO': 6, 'CARROT': 6}),
    # d11+: wheat is feed-only ($25 flour vs $233 straw). Slash targets to free
    # water/plant/harvest labor for the straw wall (price NEVER crashes).
    (11, {'WHEAT': 12, 'STRAWBERRY': 24, 'TOMATO': 10, 'CARROT': 10}),
    (15, {'WHEAT': 16, 'STRAWBERRY': 16, 'TOMATO': 12, 'CARROT': 10}),
]

def crop_targets(day):
    t = {}
    for d, tt in CROP_TARGETS:
        if d <= day:
            t = tt
    return t

class Scheduler(Layer):
    NAME = 'dsm_script'
    def run(self, ctx):
        st = getst(ctx.seat)
        if st['day'] != ctx.day:
            st['day'] = ctx.day
            st['req'] = {}
            if ctx.day == 6:
                st['line'] = LINE_FORCE or d6_branch(ctx.shops)
        if st['line'] is None:
            st['line'] = (LINE_FORCE or (d6_branch(ctx.shops) if ctx.day >= 6 else 'mixed'))
        # one-shot rush latches (evaluated intraday, latched once)
        if ctx.day == 10 and st['line'] == 'sheep' and ctx.money > 3000:
            st['rush10'] = True
        if ctx.day == 11 and st['line'] == 'sheep' and ctx.money > 4000:
            st['rush11'] = True
        st['shop'] = shopping(ctx.day, ctx, st)
        st['crops'] = crop_targets(ctx.day)
        st['htgt'] = herd_target(ctx.day, st['line'])
        st['lwant'] = land_want(ctx.day, st)

import os as _os
# Experiment control: LINE_FORCE=mixed|cow+|sheep pins the species line so
# A/B compares aren't confounded by shop-draw RNG (shop unlocks share the
# game RNG stream with weed spawns, so the same seed can deal different
# shops to different code versions). Unset for real games.
LINE_FORCE = _os.environ.get('LINE_FORCE') or None

def _fib(n):
    a, b = 1, 1
    for _ in range(max(0, n - 1)):
        a, b = b, a + b
    return a

class MarketEmit(Layer):
    NAME = 'market'
    def run(self, ctx):
        st = getst(ctx.seat)
        if 'quad0' not in st:
            try:
                st['quad0'] = len(list(ctx.farm.get('unlocked_quadrants', []) if isinstance(ctx.farm, dict) else getattr(ctx.farm, 'unlocked_quadrants', [])))
            except Exception:
                st['quad0'] = 0
        orders = []
        # 0) emergency feed: unfed animals + no shed wheat + cash -> wheat first
        try:
            unfed = sum(1 for _, _, t in ctx.structs if 'animal' in t and not t.get('fed_today'))
        except Exception:
            unfed = 0
        shed_wheat = int(ctx.shed.get('WHEAT', 0) or 0)
        if unfed > 0 and shed_wheat <= 0 and ctx.day < 28 and len(orders) < 10:
            orders.append(['BUY_PRODUCT', 'WHEAT', min(unfed * 2, 30)])
        # 1) sells first (raise cash, free shed). ALWAYS dump shed produce —
        #    price-hold gates re-learned as catastrophic (melon gate at 1.0x
        #    froze the whole cash engine after first sales; wool same).
        #    Batch only when quote is healthy; when weak still SELL (DSM-style
        #    continuous dump beats hold: ablations -10k..-13k).
        #    Wheat reserve = feed runway only (never 2*herd which starved sales).
        herd_n = sum(ctx.herd.values())
        quota0 = 0
        for k, item, qty in st.get('shop', []):
            if k == 'HIRE':
                quota0 = max(quota0, qty)
        crisis = len(ctx.hands) < max(1, quota0 // 2)
        # feed runway: enough wheat for ~1.5 days of herd (FEED buys can top up).
        # FEED=1 wheat/animal/day ALL species (engine-verified): herd_n units
        # is exactly ~1 day of feed, so herd_n+1 is a 1-day runway + 1 spare.
        reserve = 0 if ctx.day >= 28 else (max(1, herd_n) if crisis else herd_n + 1)
        liquidate = ctx.day >= 27
        # healthy-quote batching (soft): sell full shed when weak or liquidating
        BATCH = {'MILK': 20, 'WOOL': 12, 'MELON': 30, 'STRAWBERRY': 24,
                 'TOMATO': 20, 'CARROT': 20, 'FERTILIZER': 20, 'EGG': 40, 'WHEAT': 40}
        BASE = {'MILK': 160, 'WOOL': 200, 'MELON': 250, 'STRAWBERRY': 120,
                'TOMATO': 60, 'CARROT': 35, 'FERTILIZER': 100, 'EGG': 50, 'WHEAT': 25}
        for item in SELLABLE:
            have = int(ctx.shed.get(item, 0) or 0)
            if item == 'WHEAT':
                q = have - reserve
            else:
                q = have
            if q <= 0 or len(orders) >= 10:
                continue
            # batch only while price still >= 0.92 * base (early scarcity);
            # at/below that sell everything (never hold into the crater).
            try:
                px = float(ctx.price(item))
            except Exception:
                px = BASE.get(item, 1)
            if liquidate or px < BASE.get(item, 1) * 0.92:
                pass  # full dump
            else:
                q = min(q, BATCH.get(item, 30))
            orders.append(['SELL', item, int(q)])
        # owned counts (exact, observable) for deficit-driven durables
        try:
            quads = len(list(ctx.farm.get('unlocked_quadrants', []) if isinstance(ctx.farm, dict) else getattr(ctx.farm, 'unlocked_quadrants', [])))
        except Exception:
            quads = st['quad0']
        lands_owned = max(0, quads - st['quad0'])
        owned_animals = dict(ctx.herd)
        for a in ANIMALS:
            owned_animals[a] = owned_animals.get(a, 0) + int(ctx.shed.get(a, 0) or 0)
            for inv in ctx.invs:
                owned_animals[a] += int((inv or {}).get(a, 0) or 0)
        hands_now = len(ctx.hands)
        # 2) durables: pure deficit (self-healing after broke days, never overbuys)
        # 2a) HIRE daily quota, no request memory (hands observable; retry until filled)
        # SEEDS-FIRST ORDER (DSM d1: seeds funded before hire-retries; engine
        # fills the list in order, so intraday fert cash was drunk by hires
        # while seed quotas burned on broke emits). Emission itself is
        # deferred to 2a2 AFTER consumables; only the count is reserved here
        # so animal pacing (2c) sees the same crew math as before.
        quota = 0
        for k, item, qty in st.get('shop', []):
            if k == 'HIRE':
                quota = max(quota, qty)
        hire_n = 0
        if hands_now < quota:
            hire_n = min(quota - hands_now, 2)
            hands_now += hire_n
        # hire reserve: only reserve the NEXT 1-2 hires (partial fill is OK;
        # a full-quotum fib reserve gated shopping 62% of steps → $0 spiral).
        rem = max(0, quota - len(ctx.hands))
        next2 = sum(_fib(ctx.hires_today + k) for k in range(1, min(rem, 2) + 1))
        # never gate when we already have most of the day's hands, or when broke
        # (broke must SELL/shop, not freeze). Gate only rich-side overbuy of hires
        # relative to remaining cash for seeds.
        soft_gated = rem > 2 and ctx.money < (next2 + 800)
        if soft_gated and rem > 0:
            T['exec_tasks']['hire_soft_gate'] = T['exec_tasks'].get('hire_soft_gate', 0) + 1
        # 2b) LAND cumulative want — LAST (capacity is deferrable; seeds/animals
        #    earn, land only holds). Moved after consumables; see 2d.
        # 2c) ANIMALS deficit vs cumulative herd target, labor-paced AND feed-paced.
        #    No wallet gate: the d6 wave must fire on a thin wallet (feed_cap
        #    already blocks mouths we can't feed; feed wheat is pre-bought).
        htgt = st.get('htgt', {})
        if not soft_gated:
            hands_now2 = len(ctx.hands)
            # d0: hires trickle in 2/step but the quota (4) is committed cash;
            # cap on anticipated crew so the 5th head (3rd sheep = d6 LAND
            # money) is bought day 0 instead of stalling at 4 head on wallet.
            hands_eff = hands_now2
            if ctx.day == 0:
                for k, item, qty in st.get('shop', []):
                    if k == 'HIRE':
                        hands_eff = max(hands_eff, qty)
            herd_cap = 4 + 2 * hands_eff
            try:
                # Escape-aware, not instantaneous. Escape fires at
                # consecutive_unfed >= 2, so an animal that ate yesterday
                # (consecutive 0) and simply hasn't eaten yet today is NOT a
                # feed risk -- it will be fed before midnight. Keying this gate
                # on raw fed_today starved the herd: a role-separated crew feeds
                # by mid-morning, so the gate saw "unfed" every dawn and froze
                # every animal purchase, capping the whole economy at 4 head.
                unfed_now = sum(1 for _, _, t in ctx.structs
                                if 'animal' in t and not t.get('fed_today')
                                and int(t.get('consecutive_unfed', 0) or 0) >= 1)
            except Exception:
                unfed_now = 0
            shedW = int(ctx.shed.get('WHEAT', 0) or 0)
            owned_now = sum(owned_animals.get(a, 0) for a in ('COW', 'SHEEP', 'GOOSE'))
            # d0: P10 covers 4 head x 2d = 8 feed and lands same-step (market
            # before units), so the empty-shed feed_cap must not push $1800 of
            # animal buys to t1 where they collide with the melon top-up and
            # leave $98 (killing d1 hires $33 -> water collapse -> 806).
            if ctx.day == 0:
                feed_cap = herd_cap
            else:
                feed_cap = owned_now if unfed_now > 0 else max(owned_now, min(herd_cap, shedW + (6 if ctx.money > 3000 else 0)))
            if ctx.day < 10:
                feed_cap = min(feed_cap, 10)
            # Paced buys (seed-200001 lesson): cash waves must NOT convert into
            # one-day splurges the barns can't absorb (d10: $5300 of animals,
            # half never placed, feed demand doubled -> late collapse 40k->26k).
            # DSM paces +7 d6 then ~2/day to 21 by d11, always placed. Two gates:
            # (1) no new buys while any owned animal is unplaced (shed/carried);
            # (2) at most 4 head/day so BUILD+PLACE+feed keep up.
            unplaced = 0
            for a in ANIMALS:
                unplaced += int(ctx.shed.get(a, 0) or 0)
            for inv in ctx.invs:
                for a in ANIMALS:
                    unplaced += int((inv or {}).get(a, 0) or 0)
            bought_key = ('A', ctx.day)
            bought_today = int(st['req'].get(bought_key, 0) or 0)
            # d0 needs 2C+3S = 5 head same-day (5 units place in parallel);
            # later waves stay at 4/day so BUILD+PLACE+feed keep up.
            daycap = 5 if ctx.day == 0 else 4
            buy_room = max(0, daycap - bought_today)
            if unplaced > 0:
                buy_room = 0
            # AFFORDABILITY gate (200002 lesson): BUY_ANIMAL fails SILENTLY on
            # short wallet or full shed, but st['req'] counts EMISSIONS -- d10
            # room opened on $233, 4 broke buys burned the daycap, and the
            # funded afternoon bought nothing (-18k). Emit only what wallet +
            # shed cover this step; retries across steps land the wave when
            # sales arrive. $100 cushion keeps a hire/seed slice alive.
            spend = 0
            try:
                shed_free = 100 - sum(int(v or 0) for v in ctx.shed.values())
            except Exception:
                shed_free = 0
            # GOOSE_LINE: the shared loop below runs COW/SHEEP first and eats
            # all daily slots, so goose deficits (mixed wants 8) never fill --
            # census showed 0 geese placed all game. Reserve 1 slot/day d6-21
            # under the SAME gates (feed room, zero unplaced, deficit vs htgt).
            # Coop coverage needs no new code: build_kind/place_animal already
            # build on demand for waiting geese. Buy-stop d21: first yield +4d,
            # reward locks d29 22:00, so later geese never pay back $300.
            if (GOOSE_LINE_ON and 6 <= ctx.day <= 21 and len(orders) < 10
                    and buy_room > 0 and unplaced == 0):
                gwant = max(0, int(htgt.get('GOOSE', 0) or 0)
                            - owned_animals.get('GOOSE', 0))
                groom = max(0, min(herd_cap, feed_cap, ladder_cap(ctx.day)) - owned_now)
                g = min(gwant, groom, buy_room, 1, 10 - len(orders))
                if g > 0 and (not AFFORD_GATE_ON or (
                        ctx.money - spend >= 300 * g + 100 and shed_free >= g)):
                    orders.append(['BUY_ANIMAL', 'GOOSE', g])
                    owned_animals['GOOSE'] = owned_animals.get('GOOSE', 0) + g
                    owned_now += g
                    buy_room -= g
                    spend += 300 * g
                    shed_free -= g
                    st['req'][bought_key] = int(st['req'].get(bought_key, 0) or 0) + g
            for a in ('COW', 'SHEEP', 'GOOSE'):
                if len(orders) >= 10 or buy_room <= 0:
                    break
                want = max(0, int(htgt.get(a, 0) or 0) - owned_animals.get(a, 0))
                room = max(0, min(herd_cap, feed_cap, ladder_cap(ctx.day)) - owned_now)
                want = min(want, room, buy_room)
                if want > 0:
                    n = min(want, 10 - len(orders), 3)
                    if AFFORD_GATE_ON:
                        while n > 0 and (ctx.money - spend < ANIMALS[a]['cost'] * n + 100
                                         or shed_free < n):
                            n -= 1  # shrink to affordable: partial fills keep
                        if n <= 0:
                            continue  # the wave moving; retry a later step,
                    cost = ANIMALS[a]['cost'] * n  # don't burn daycap on fails
                    orders.append(['BUY_ANIMAL', a, n])
                    owned_animals[a] = owned_animals.get(a, 0) + n
                    owned_now += n
                    buy_room -= n
                    spend += cost
                    shed_free -= n
                    st['req'][bought_key] = int(st['req'].get(bought_key, 0) or 0) + n
        # 3) consumables: request-counted slices. Never fully gated — seed/feed
        #    purchases ARE the income loop; only trim qty when cash is thin.
        for k, item, qty in st.get('shop', []):
            if len(orders) >= 10:
                break
            if k not in ('P', 'S'):
                continue
            key = (k, item)
            done = st['req'].get(key, 0)
            if done >= qty:
                continue
            if k == 'P':
                # cash-aware: always allow small top-ups (feed/fert), cap big ones.
                # Never 0: $20 of wheat seed breaks a broke-then-empty-tiles spiral.
                # Fertilizer is a yield BOOST, not survival: only when rich, and
                # never stockpile (buy+sell same-day round-trips bled cash:
                # shed passes straight through to the dump when application
                # lags supply). Buy only when the shed holds < 8.
                if item == 'FERTILIZER' and ctx.money < 2500:
                    continue
                if item == 'FERTILIZER' and int(ctx.shed.get('FERTILIZER', 0) or 0) >= 8:
                    continue
                cap = 20 if ctx.money >= 2000 else (6 if ctx.money >= 400 else 2)
                n = min(qty - done, 10 - len(orders), cap)
                if n > 0:
                    orders.append(['BUY_PRODUCT', item, n])
                    st['req'][key] = done + n
            elif k == 'S':
                # never stockpile: seeds are dead capital ($13k piles observed).
                # Buy only below on-hand caps; planters pull from stock first.
                # d0 melon burst (10) must clear the cap; straw buffer 14 for the
                # d9-11 wall burst (planters pull ~4-6/day; never-crash $233).
                SEEDCAP = {'WHEAT': 20, 'CARROT': 10, 'TOMATO': 8, 'STRAWBERRY': 14, 'MELON': 14}
                if int(ctx.seeds.get(item, 0) or 0) >= SEEDCAP.get(item, 10):
                    continue
                cap = 10 if ctx.money >= 1500 else (4 if ctx.money >= 400 else 2)
                n = min(qty - done, 10 - len(orders), cap)
                if n > 0:
                    orders.append(['BUY_SEED', item, n])
                    st['req'][key] = done + n
        # 2a2) deferred HIRE emission: seeds (section 3 above) already took
        # their slots, so funded steps fill seeds before hire-retries.
        if hire_n > 0 and len(orders) < 10:
            for _ in range(min(hire_n, 10 - len(orders))):
                orders.append(['HIRE'])
        # 2d) LAND last: capacity never outranks income on a thin wallet.
        #     Self-healing deficit (retries until filled), but only when rich
        #     enough that land can't starve hires/seeds/feed. First plot costs
        #     only $1000 (LAND_PRICES=[1000,2000,4000]) so DSM buys it d6 with
        #     wool money; gate it at 1200, later plots at 2500.
        if lands_owned < st.get('lwant', 0) and len(orders) < 10:
            gate = 1200 if lands_owned == 0 else 2500
            if ctx.money >= gate:
                orders.append(['BUY_LAND'])
        ctx.orders = orders
        T['market_orders'] += len(orders)

# ---- executor: sticky-assignment field loop ----
# Greedy-nearest re-planned each step livelocks (units oscillate: 1652 walks,
# 26 plants). Assignments persist in STATE until done or invalid.
# ---- executor: role-separated field loop (clean rewrite) ----
# Day-start role assignment splits the crew into two DISJOINT roles so FEED/CARE
# can no longer steal the planting crew. That theft was the single bug every
# greedy variant shared: on d0 all 6 units rush 4 animals, nobody plants, and
# the farm ends d0 with 9 plants instead of Boey's 20 -- which IS the d10
# payday gap.
#
#   animal units (1-3): PLACE, FEED->CARE, CAPHARV, HARVEST-animal,
#                       COLLECT/apply FERTILIZER, BUILD, PKA. Self-contained:
#                       nothing the herd needs lives outside this role.
#   crop units (rest + the farmer): a column-locked PLANT->WATER->HARVEST->DIG
#                       sweep. NEVER touch an animal, so the sweep cannot be
#                       starved. Idle animal units help crops (bonus, not theft).
#
# Engine truths this relies on (verified in kaggriculture.py):
#   * pending_care_bonus += 1 only when fed_today AND cared_today; pays out
#     1+bonus at production, capped at max_held, and ONLY if fed that day.
#     => CARE same-day as FEED is a 3x/4x/2x multiplier, not a nicety.
#   * stored yield stops at max_held (6 cow/sheep, 4 goose): a full tile
#     wastes tonight's production entirely => harvest before the cap (CAPHARV).
#   * consecutive_unfed >= 2 escapes; >=1 today + unfed today = gone tonight.
#   * PLANT requests are atomic per crop: over-requesting seeds drops ALL of
#     that crop's PLANTs to PASS => per-step shared seed budget.
#   * a plant unwatered two days running dies into a WEED => water before plant.
#   * hands reset nightly => roles are recomputed at every dawn.

ANIMAL_MAXHELD = {'GOOSE': 4, 'COW': 6, 'SHEEP': 6}

# ---- fertilizer pipeline (P1/P2): collect en-route, apply from the pocket,
# never let fert touch the shed (the market sweeps it at dawn and a DROP
# buries it -- the two root causes of FERTILIZE 0/day) ----
ENROUTE_ON  = True     # P1: spend walk steps on work the tile underfoot needs
ENROUTE_MAX = 3        # opportunistic actions per crop unit per day
FERT_ON     = True     # P2: apply carried fert to a plant worth the hurdle
FERT_CARRY  = 4        # max FERTILIZER a crop unit holds
FERT_HURDLE = 1.20     # apply only if crop gain x price > hurdle x fert price
FERT_MIN_DAY = 9       # DSM embargo: no field fert before d9 (it sells then)

# A/B flag: feed stride (skip cu==0/yield==0 feeds at herd>=10).
# A/B 5-seed: ON 22983 vs OFF 22887 -- net zero with high variance, and it
# forfeits banked CARE income. OFF until labor accounting proves otherwise.
STRIDE_ON = False

# A/B flag: goose line (reserve 1 animal-buy slot/day for GOOSE d6-21).
# FEED=1 wheat/animal/day ALL species (engine-verified: _inv_take WHEAT 1):
# goose margin ~= 2*egg - 1*wheat ~= +$78-98/d even glutted, first yield d4,
# most glut-robust product. Geese substitute inside the existing herd cap
# (room formula counts all species), so no extra wheat demand vs current mix.
# STATUS: ON+afford-gate scored 32.9k vs 40.4k OFF (feed-delivery ceiling:
# bigger landing herds need ~10 steps/visit, 4 units x 24 steps can't cover
# 15+ head + dump trips -> chronic 1-3 shortfall -> escapes). OFF until the
# delivery ceiling is fixed; see BUY_SEASON below.
GOOSE_LINE_ON = False

# A/B flag: affordability gate on BUY_ANIMAL emission (cash + shed space).
# Diagnosed a REAL bug (200002: room opened on $233, 4 broke emissions burned
# the emission-counted daycap, funded afternoon bought nothing, -18k), but
# the fix EXPOSES the feed-delivery ceiling: every emission lands -> herds
# outgrow delivery -> escapes (gate-only 24.5k vs 40.4k). OFF until paired
# with a demand-side fix (buy season / feed capacity). Kept for the combo.
AFFORD_GATE_ON = False


class FieldExec(Layer):
    NAME = 'field'
    SHED_TILES = {(4, 4), (5, 4), (4, 5), (5, 5)}

    def tile_at(self, ctx, x, y):
        try:
            return ctx.tiles[y][x]
        except Exception:
            return 'LOCKED'

    def free_tile(self, ctx, taken, p):
        # compact farm: prefer tiles near the shed (short supply trips), then
        # near the unit.
        cands = [t for t in ctx.empty_tiles if t not in taken]
        if not cands:
            return None
        return min(cands, key=lambda t: (manhattan(t, (4, 4)) * 4 + manhattan(p, t)))

    # ---------------- fertilizer pipeline (P1 collect / P2 apply) ----------------
    def _claimed_by_other(self, st, key, idx):
        for store in ('claim', 'aclaim'):
            d = st.get(store)
            if not isinstance(d, dict):
                continue
            for owner, c in d.items():
                if owner == idx or not c:
                    continue
                try:
                    if (c[0], c[1]) == key:
                        return True
                except Exception:
                    continue
        return False

    def enroute_cmd(self, ctx, st, idx, pos, tgt):
        """P1: a crop unit mid-walk is standing on a real tile every step.
        Spend that step on work the tile needs WITHOUT releasing the claim,
        so the unit arrives one step later at the same destination. Converts
        a WALK step into an ACTION step. The COOP/PASTURE branch is the
        fertilizer supply: it COLLECTs straight into carried inventory,
        bypassing the shed entirely (the market sweeps the shed at dawn and
        a DROP buries protected stacks -- both root causes of FERTILIZE 0)."""
        if not ENROUTE_ON or ctx.day >= 29:
            return None
        if tgt is not None and (pos[0], pos[1]) == (tgt[0], tgt[1]):
            return None                      # on target: the normal path owns it
        if st.get('erday') != ctx.day:
            st['erday'] = ctx.day
            st['erused'] = {}
        if st.get('erstep') != ctx.step:
            st['erstep'] = ctx.step
            st['erseen'] = set()
        if st['erused'].get(idx, 0) >= ENROUTE_MAX:
            return None
        if tgt is not None:
            if manhattan(pos, tgt) + 1 > max(0, 23 - ctx.hour):
                return None                  # no slack left: keep walking
        key = (pos[0], pos[1])
        if key in st['erseen'] or self._claimed_by_other(st, key, idx):
            return None
        t = self.tile_at(ctx, pos[0], pos[1])
        if not isinstance(t, dict):
            return None
        inv = ctx.invs[idx] if idx < len(ctx.invs) else {}
        kind = t.get('kind')
        cmd = None
        if kind == 'WEED':
            cmd = ['DIG']
        elif kind == 'PLANT':
            if int(t.get('consecutive_unwatered', 0) or 0) >= 1 \
                    and not t.get('watered_today'):
                cmd = ['WATER']              # survival water: never a loss
            elif (int(inv.get('FERTILIZER', 0) or 0) > 0
                  and self.fert_gain(ctx, t) > 0
                  and int(t.get('fertilized_until_day', -1) or -1) < ctx.day + 1):
                cmd = ['FERTILIZE']
        elif kind in ('COOP', 'PASTURE'):
            # the only animal action a crop unit emits: reads/clears
            # fertilizer_available only. No feed flag, no cared_today, no
            # pending_care_bonus -- every gate the economy samples is intact.
            if (FERT_ON and t.get('animal') is not None
                    and t.get('fertilizer_available')
                    and int(inv.get('FERTILIZER', 0) or 0) < FERT_CARRY
                    and ctx.day >= FERT_MIN_DAY):
                cmd = ['COLLECT_FERTILIZER']
        if cmd is None:
            return None
        st['erseen'].add(key)
        st['erused'][idx] = st['erused'].get(idx, 0) + 1
        return cmd

    def fert_gain(self, ctx, tile):
        """Expected EXTRA units from fertilizing this plant right now
        (engine: WATER banks +2 fert vs +1 unfert for one-shots inside the
        window, line 442; ongoing banks 2 vs 1 at the production tick when
        watered+fert, line 799; FERTILIZE covers day..day+2, line 481)."""
        crop = tile.get('crop')
        if crop is None or tile.get('kind') != 'PLANT':
            return 0.0
        if int(tile.get('fertilized_until_day', -1) or -1) >= ctx.day + 1:
            return 0.0                       # still covered tomorrow
        age = ctx.day - int(tile.get('planted_day', ctx.day) or 0)
        held = int(tile.get('yield_units', 0) or 0)
        cd = CROPS.get(crop, {})
        if not cd.get('ongoing'):
            maxday = int(cd.get('maxday', 99))
            maxy = int(cd.get('maxyield', 6))
            lo = (maxday + 1) // 2
            if age < lo or age > maxday:
                return 0.0                   # outside the bonus window
            room = maxy - held
            if room <= 0:
                return 0.0
            days = min(maxday - age + 1, 3)
            return float(min(room, days))
        first = int(cd.get('first', 99))
        interval = max(1, int(cd.get('interval', 1)))
        maxy = int(cd.get('maxyield', 4))
        room = maxy - held
        if room <= 0:
            return 0.0
        since = age - first
        ticks = 0
        for d in (0, 1, 2):
            s = since + d
            if s >= 0 and s % interval == 0:
                ticks += 1
        if ticks == 0:
            return 0.0
        return float(min(room, ticks))

    def fert_cmd(self, ctx, st, idx, pos):
        """P2: apply carried fert while standing on a plant the unit is
        about to WATER anyway. FERTILIZE must land on an earlier STEP than
        WATER (the engine reads fertilized_until_day at WATER time), so this
        returns FERTILIZE now and the on-plant block returns WATER next step.
        Zero movement; the claim is untouched."""
        if not FERT_ON or ctx.day < FERT_MIN_DAY or ctx.day >= 29:
            return None
        inv = ctx.invs[idx] if idx < len(ctx.invs) else {}
        if int(inv.get('FERTILIZER', 0) or 0) <= 0:
            return None
        t = self.tile_at(ctx, pos[0], pos[1])
        if not t or t.get('kind') != 'PLANT':
            return None
        gain = self.fert_gain(ctx, t)
        if gain <= 0:
            return None
        worth = gain * float(ctx.price(t.get('crop')) or 0)
        if worth < FERT_HURDLE * float(ctx.price('FERTILIZER') or 0):
            return None
        return ['FERTILIZE']

    # ---------------- role assignment (dawn; hands reset nightly) ----------------
    def assign_roles(self, ctx, st, n_units):
        placed = sum(1 for _, _, t in ctx.structs if t.get('animal') is not None)
        owned = sum(ctx.owned.get(a, 0) for a in ANIMALS)
        unplaced = max(0, owned - placed)
        # FEED+CARE per animal ~= 3 unit-steps/day (2 actions + walk), plus
        # placement ~= 4 each (PKA + walk + BUILD + PLACE), plus the fert loop.
        # One unit gets ~10 useful animal-steps a day after its own commute, so
        # size the crew that the whole herd is fed by mid-morning (the market's
        # feed gate reads unfed status each step and blocks herd purchases
        # while any animal is still hungry) and still has slack to place, care
        # and collect. Under-sizing here made one unit the whole bottleneck.
        total = placed + unplaced
        nA = -(-(total * 3) // 10)
        if unplaced:
            # PLACEMENT BURST: an unplaced animal produces nothing yet still
            # counts against `owned`, which fools the market's deficit logic
            # into thinking the target is met. Size the burst to the backlog
            # (throughput, not quota: pdone was removed so a unit places all
            # day when the shed is full). d0 keeps ONE crop unit safe by the
            # n_units-1 cap only; planting-first ordering (crop units fetch
            # only when the sweep is clean) is what protects seedlings, not
            # shrinking the animal crew -- shrinking it to 2 stalled waves at
            # ~2 placed/day, backlog blocked buys, herd froze at ~12 head.
            nA = max(nA, unplaced)
        nA = min(nA, n_units - 1, 3)          # never take the last unit
        if total >= 12:
            # big herds need a 4th animal unit: 3 units x 24 steps cannot
            # cover 12+ head x (feed+care+harvest+collect+walks). Idle animal
            # units fall through to the crop sweep, so the 4th only costs
            # when herd work actually exists (it does: feed < herd d12+).
            nA = min(nA, n_units - 1, 4)
        if (placed or unplaced) and nA < 2:
            nA = 2
        roles = {i: ('animal' if 0 < i <= nA else 'crop') for i in range(n_units)}
        roles[0] = 'crop'   # farmer always sweeps (Boey's farmer: zero animal
                            # logistics, first PLANT at t=6)
        # spread crop units over distinct columns, shed-outward over ALL
        # unlocked columns (shed at x=4,5). The old 4-(k%5) only covered the
        # west half, so east-quadrant work fell to the global fallback sweep
        # and units crossed the map for it.
        unlocked = set()
        H = len(ctx.tiles)
        for y in range(H):
            for x in range(len(ctx.tiles[y])):
                if self.tile_at(ctx, x, y) != 'LOCKED':
                    unlocked.add(x)
        col_order = [c for c in (4, 5, 3, 6, 2, 7, 1, 8, 0, 9) if c in unlocked]
        if not col_order:
            col_order = [4]
        cols = {}
        crop_ids = [i for i in range(n_units) if roles[i] == 'crop']
        for k, i in enumerate(crop_ids):
            cols[i] = col_order[k % len(col_order)]
        st['cols'] = cols
        return roles

    # ---------------- animal role ----------------
    def needy_plant(self, ctx, p, taken):
        """Nearest plant that would actually bank the fertilizer bonus, by
        tier: one-shot crops inside their bank window first (a single
        application covers every remaining bank day and doubles the crop:
        wheat 3->6, carrot 2->4), then ongoing crops in production
        (acceleration + faster rotation), then anything else uncovered.
        Melons that are watered daily hit their cap without fertilizer, so
        they sink to the bottom. Re-application is automatic: a tile whose
        coverage lapsed is uncovered again, ~every 3 days through the
        production run.
        DSM embargo: NO field fertilizer before d9 (mined: FERTILIZE 0/d
        until d9, 21 on d10, 81 on d11). Early fert is sold (~$100/u,
        ~$500/day = the d1-6 hire/seed engine); a +3 wheat bonus later is
        worth less than a hire today. Collectors keep collecting (shed ->
        sold); only application and shed-pull are gated."""
        if ctx.day < 9:
            return None
        cands = []
        for x, y, t in ctx.plants:
            if (x, y) in taken:
                continue
            try:
                if int(t.get('fertilized_until_day', -1) or -1) >= ctx.day:
                    continue
                age = ctx.day - int(t.get('planted_day', 99) or 99)
                if age < 1:
                    continue
            except Exception:
                continue
            crop = t.get('crop')
            cd = CROPS.get(crop, {})
            if cd.get('ongoing'):
                tier = 1
            else:
                wstart = (cd.get('maxday', 99) + 1) // 2
                tier = 0 if wstart <= age <= cd.get('maxday', 99) else 2
                if crop == 'MELON':
                    tier = 2
            cands.append((tier, manhattan(p, (x, y)), x, y))
        if not cands:
            return None
        cands.sort()
        return (cands[0][2], cands[0][3])

    def structure_deficit(self, ctx):
        need_p = sum(ctx.owned.get(s, 0) for s in ('COW', 'SHEEP')) \
            + (1 if (ctx.owned.get('COW', 0) + ctx.owned.get('SHEEP', 0)) > 0 else 0)
        have_p = sum(1 for _, _, t in ctx.structs if t.get('kind') == 'PASTURE')
        need_c = ctx.owned.get('GOOSE', 0) + (1 if ctx.owned.get('GOOSE', 0) > 0 else 0)
        have_c = sum(1 for _, _, t in ctx.structs if t.get('kind') == 'COOP')
        return have_p < need_p or have_c < need_c

    def build_kind(self, ctx):
        need_p = sum(ctx.owned.get(s, 0) for s in ('COW', 'SHEEP')) \
            + (1 if (ctx.owned.get('COW', 0) + ctx.owned.get('SHEEP', 0)) > 0 else 0)
        have_p = sum(1 for _, _, t in ctx.structs if t.get('kind') == 'PASTURE')
        need_c = ctx.owned.get('GOOSE', 0) + (1 if ctx.owned.get('GOOSE', 0) > 0 else 0)
        have_c = sum(1 for _, _, t in ctx.structs if t.get('kind') == 'COOP')
        if have_p < need_p or have_c < need_c:
            # build for whoever is actually waiting (shed+carried); the old
            # pasture-first rule starved coops so geese never placed.
            try:
                wait_p = int(ctx.shed.get('COW', 0) or 0) + int(ctx.shed.get('SHEEP', 0) or 0)
                wait_c = int(ctx.shed.get('GOOSE', 0) or 0)
                for inv in ctx.invs:
                    wait_p += int((inv or {}).get('COW', 0) or 0) + int((inv or {}).get('SHEEP', 0) or 0)
                    wait_c += int((inv or {}).get('GOOSE', 0) or 0)
            except Exception:
                wait_p, wait_c = 1, 0
            if wait_c > 0 and have_c < need_c and (have_p >= need_p or wait_c >= wait_p):
                return 'BUILD_COOP'
        return 'BUILD_PASTURE' if have_p < need_p else 'BUILD_COOP'

    def place_animal(self, ctx, st, i, p, taken, carry):
        """BUILD then PLACE in one motion, with a per-unit tile reservation so
        carriers don't stack on one structure (that race stranded units PASSing
        for half a day). Ports Boey's d0 t=5-6 placement."""
        pres = st.setdefault('pres', {})
        kind = ANIMALS[carry]['structure']
        claimed = set()
        for u, t_ in pres.items():
            if u != i and t_:
                claimed.add(tuple(t_))
        cands = [(x, y) for x, y, t in ctx.structs
                 if t.get('kind') == kind and t.get('animal') is None
                 and (x, y) not in taken and (x, y) not in claimed]
        if cands:
            r = tuple(pres.get(i) or ())
            tgt = min(cands, key=lambda t2: (0 if (t2[0], t2[1]) == r else 1,
                                             manhattan(p, t2)))
            if (p[0], p[1]) == tgt:
                pres.pop(i, None)
                taken.add(tgt)   # hold through the step: the PLACE has not
                return ['PLACE', carry]   # been applied yet, so a sibling
            pres[i] = tgt       # must not grab the same structure this step
            taken.add(tgt)
            return step_toward(p, tgt) or ['PASS']
        # no free structure: build one. Reserve the tile so other carriers
        # don't converge on it.
        bt = self.free_tile(ctx, set(taken) | claimed, p)
        if bt is None:
            return ['PASS']
        pres[i] = bt
        taken.add(bt)
        if (p[0], p[1]) == bt:
            pres.pop(i, None)
            return [self.build_kind(ctx)]
        return step_toward(p, bt) or ['PASS']

    def burst_fetch(self, ctx, st, i, p):
        """Fetch one shed animal for placement. No per-day quota: a unit
        places all day while the shed holds animals (the fed-or-noon gate
        below protects morning feed; pres reservations serialize structures
        so parallel fetchers don't collide). Gated on the herd being fed
        (an ungated dawn burst starved feeding and stalled the herd) or
        noon, whichever first. An urgent-only gate was tried and lost ~10k:
        pre-noon placement displaced feed carriers even though the skipped
        animals were "safe", and feeding slipped late. PICKUP is unconditional on free structures:
        place_animal BUILDs when none is free, so refusing pickup strands
        the shed instead of filling the field."""
        if ctx.hour < 12 and any(t.get('animal') is not None and not t.get('fed_today')
                                 for _, _, t in ctx.structs):
            return None
        if int(st.get('aleft', 0) or 0) <= 0:
            return None
        for a in ANIMALS:
            if int(ctx.shed.get(a, 0) or 0) <= 0:
                continue
            # commit the budget on intent (walk or pickup): aleft resets
            # every step, so a diverted unit only undercounts this step,
            # while without the commit the whole crew chases one animal.
            st['aleft'] = int(st.get('aleft', 0) or 0) - 1
            if shed_adjacent(p):
                return ['PICKUP', a, 1]
            return step_toward(p, nearest_shed_tile(p)) or ['PASS']
        return None

    def _aclaim_valid(self, ctx, tile):
        """Work-based validation for a shared animal-crew target: an animal
        tile with unfinished business, or a still-ripe standing wheat tile
        (5b feed-direct). NOTE: tile may be a 5-tuple (x, y, step, px, py);
        compare on coordinates only."""
        tx, ty = tile[0], tile[1]
        for x, y, t in ctx.structs:
            if (x, y) != (tx, ty) or t.get('animal') is None:
                continue
            if not t.get('fed_today'):
                return True
            try:
                yld = int(t.get('yield_units', 0) or 0)
            except Exception:
                yld = 0
            mh = ANIMAL_MAXHELD.get(t.get('animal'), 6)
            if t.get('fed_today') and not t.get('cared_today') and yld < mh:
                return True
            if yld > 0 or t.get('fertilizer_available'):
                return True
            return False
        wcd = CROPS.get('WHEAT', {})
        for x, y, t in ctx.plants:
            if (x, y) != (tx, ty) or t.get('crop') != 'WHEAT':
                continue
            try:
                age = ctx.day - int(t.get('planted_day', 0) or 0)
                yld = int(t.get('yield_units', 0) or 0)
            except Exception:
                continue
            if yld >= wcd.get('maxyield', 6) or age > wcd.get('maxday', 4) or \
                    (age == wcd.get('maxday', 4) and t.get('watered_today') and yld > 0):
                return True
            return False
        return False

    def endgame_work(self, ctx, st, i, p, inv_i, taken):
        """Day 29: the reward locks at 22:00, before dusk processing, so no
        production runs again and nothing fed/watered/cared/planted today can
        ever pay. Harvest every standing yield unit, bank everything early
        (the deadline is 22:00, not midnight), skip everything else."""
        # 1) bank any sellable load now (wheat/fert included: feed is over,
        #    everything converts to money)
        if any(int(v or 0) > 0 for k, v in inv_i.items() if k in SELLABLE):
            bc = bank_cmd(ctx, st, inv_i, exclude=())
            if bc is not None:
                if shed_adjacent(p):
                    return bc
                return step_toward(p, nearest_shed_tile(p)) or ['PASS']
        # 2) nearest standing yield (animals + plants, ripe or not: unripe
        #    yield still banks, and there is no tomorrow to protect)
        best = None
        for x, y, t in ctx.structs:
            if not isinstance(t, dict) or t.get('animal') is None:
                continue
            if (x, y) in taken:
                continue
            if int(t.get('yield_units', 0) or 0) > 0:
                d = manhattan(p, (x, y))
                if best is None or d < best[0]:
                    best = (d, x, y, 'HARVEST')
            elif t.get('fertilizer_available'):
                d = manhattan(p, (x, y)) + 0.5
                if best is None or d < best[0]:
                    best = (d, x, y, 'COLLECT_FERTILIZER')
        for x, y, t in ctx.plants:
            if not isinstance(t, dict):
                continue
            if (x, y) in taken:
                continue
            if int(t.get('yield_units', 0) or 0) > 0:
                d = manhattan(p, (x, y))
                if best is None or d < best[0]:
                    best = (d, x, y, 'HARVEST')
        if best is None:
            # nothing left to harvest: drift shed-ward for the final bank
            if shed_adjacent(p):
                return ['PASS']
            return step_toward(p, nearest_shed_tile(p)) or ['PASS']
        _, x, y, cmd = best
        taken.add((x, y))
        if (p[0], p[1]) == (x, y):
            return [cmd]
        return step_toward(p, (x, y)) or ['PASS']

    def animal_work(self, ctx, st, i, p, inv_i, taken, sibpos):
        """The whole herd economy. Returns a command, or None when idle (the
        unit then helps the crop sweep -- bonus labour, never a theft)."""
        if ctx.day >= 29:
            return self.endgame_work(ctx, st, i, p, inv_i, taken)
        # shared feed/visit targets (first-come): `taken` is per-step only,
        # so without this two animal units converge on the same unfed animal
        # across steps and the loser re-walks -- the same hole shared crop
        # claims closed. Work-based validation; no fallback, no stealing,
        # no distance games (a nearer-claimant filter collapsed two seeds
        # below baseline: the far claimant kept walking, so every far claim
        # drew two walkers instead of one).
        have_wheat = int(inv_i.get('WHEAT', 0) or 0) > 0
        aclaims = st.setdefault('aclaim', {})
        mine = aclaims.get(i)
        if mine is not None and not self._aclaim_valid(ctx, mine):
            aclaims.pop(i, None)
            mine = None
        if mine is not None and not have_wheat:
            # holding an unfed-animal target without wheat blocks siblings
            # that HAVE wheat from feeding it (the claim is valid work, but
            # not work THIS unit can do). Release; re-claim after fetching.
            for x, y, t in ctx.structs:
                if (x, y) == (mine[0], mine[1]) and t.get('animal') is not None \
                        and not t.get('fed_today'):
                    aclaims.pop(i, None)
                    mine = None
                    break
        others_a = set()
        for u, v in aclaims.items():
            if u != i and v:
                try:
                    others_a.add((v[0], v[1]))
                except Exception:
                    pass
        # 1) carrying an animal -> place it now (long BUILD trips: release
        #    the feed target so a sibling serves it meanwhile)
        for a in ANIMALS:
            if int(inv_i.get(a, 0) or 0) > 0:
                aclaims.pop(i, None)
                return self.place_animal(ctx, st, i, p, taken, a)
        # 1b) PLACEMENT BURST: an animal sitting in the shed produces nothing
        #     but still counts against `owned`, so the market's deficit logic
        #     sees the target as met and stops buying.
        c = self.burst_fetch(ctx, st, i, p)
        if c is not None:
            aclaims.pop(i, None)  # placement trip: release the feed target
            return c
        # 2) carried produce -> shed (the sell pipeline). Wheat is working
        #    stock and rides until d28; fert is handled at (9).
        load = sum(v for k, v in inv_i.items()
                   if k in PRODUCTS and k not in ('WHEAT', 'FERTILIZER') and v)
        if load:
            bc = bank_cmd(ctx, st, inv_i)
            if bc is None:
                pass  # shed full: hold cargo, do field work, retry later
            elif shed_adjacent(p):
                return bc
            else:
                return step_toward(p, nearest_shed_tile(p)) or ['PASS']
        # 3) ON-TILE BATCH: standing on an animal tile -> do everything
        #    here before leaving (FEED->CARE->HARVEST->COLLECT). The old code
        #    made four separate visits per animal per day (feed sweep, care
        #    sweep, value-density harvest sweep, collect sweep): ~3 wasted
        #    walks/head/day, the whole walk gap to v76 (62% vs 42%). One
        #    visit does all four. Non-feed actions wait until the herd is fed
        #    (the market's feed gate blocks buys while any animal is hungry)
        #    or h10, whichever first; FEED itself is always allowed so the
        #    morning feed sweep never stalls.
        #    FEED STRIDE (herd >= 10): an animal at cu==0 with nothing stored
        #    is deliberately skipped today (DSM feeds ~75%: 1827 gap-0 vs 623
        #    gap-1). Skipping is escape-safe by construction (cu 0->1, fed
        #    tomorrow before it can reach 2) and payout-safe (tomorrow's feed
        #    covers tomorrow's production); it only forgoes one banked CARE
        #    unit, worth less than the saved visit on crunch days. Small
        #    herds feed everything (bank growth is cheap when labor is free).
        placed_n = sum(1 for _, _, t in ctx.structs if t.get('animal') is not None)
        stride = STRIDE_ON and placed_n >= 10
        def _urgent(t):
            return int(t.get('consecutive_unfed', 0) or 0) >= 1 \
                or int(t.get('yield_units', 0) or 0) > 0
        unfed = [(x, y) for x, y, t in ctx.structs
                 if t.get('animal') is not None and not t.get('fed_today')
                 and (x, y) not in taken and (x, y) not in others_a
                 and (not stride or _urgent(t))]
        unfed_any = any(t.get('animal') is not None and not t.get('fed_today')
                        and (not stride or _urgent(t))
                        for _, _, t in ctx.structs)
        here = self.tile_at(ctx, p[0], p[1])
        if isinstance(here, dict) and here.get('animal') is not None \
                and (p[0], p[1]) not in taken:
            mh = ANIMAL_MAXHELD.get(here.get('animal'), 6)
            yld = int(here.get('yield_units', 0) or 0)
            if not here.get('fed_today') and have_wheat \
                    and (not stride or _urgent(here)):
                taken.add((p[0], p[1]))
                aclaims[i] = (p[0], p[1])
                return ['FEED']
            if not unfed_any or ctx.hour >= 10:
                if here.get('fed_today') and not here.get('cared_today') \
                        and yld < mh:
                    taken.add((p[0], p[1]))
                    aclaims[i] = (p[0], p[1])
                    return ['CARE']
                if yld > 0:
                    taken.add((p[0], p[1]))
                    aclaims[i] = (p[0], p[1])
                    return ['HARVEST']
                if here.get('fertilizer_available'):
                    taken.add((p[0], p[1]))
                    aclaims[i] = (p[0], p[1])
                    return ['COLLECT_FERTILIZER']
        # 4) FEED: escape is permanent and free to prevent. Feed the nearest
        #    unfed animal (shared target: siblings serve other tiles).
        if have_wheat and unfed:
            x, y = min(unfed, key=lambda z: manhattan(p, z))
            if (p[0], p[1]) == (x, y):
                taken.add((x, y))
                aclaims[i] = (x, y)  # hold through the batch (care/harvest)
                return ['FEED']
            taken.add((x, y))
            aclaims[i] = (x, y)
            return step_toward(p, (x, y)) or ['PASS']
        # 5) no wheat but animals hungry and the shed has wheat -> fetch it.
        #    Carry four: one shed trip feeds four animals (the replay
        #    champion's modal carry), so feeding costs a quarter of the trips
        #    of one-at-a-time fetching.
        #    REVERTED herd-scaled carry to 12 (A/B: 29.2k vs 40.4k, 200002
        #    38.2k->23.0k, 200005 48.3k->17.4k): big grabs empty the shed
        #    mid-day, stranding co-feeders at wleft=0 (they pin on unfed
        #    tiles carrying nothing); feeders serve ~4-8 head each, so
        #    carry-4 was 1-2 trips/day, never the dominant visit term.
        #    The binding term is pasture-to-pasture travel, not shed trips.
        if not have_wheat and unfed and int(st.get('wleft', 0) or 0) > 0:
            if shed_adjacent(p):
                q = min(4, int(st.get('wleft', 0) or 0))
                if q > 0:
                    st['wleft'] = int(st['wleft']) - q
                    return ['PICKUP', 'WHEAT', q]
                return ['PASS']
            return step_toward(p, nearest_shed_tile(p)) or ['PASS']
        # 5b) FEED-DIRECT: shed wheat is empty but ripe standing wheat
        #     exists -> harvest it now and feed from hands. Without this the
        #     crew deadlocks: hungry animals pin every animal unit (they walk
        #     to unfed tiles carrying nothing) while the wheat they need sits
        #     unharvested in the fields, so the shed stays empty and nobody
        #     ever feeds (200001 d12+: feed 8-10/day for 12-15 head ->
        #     escapes -> weeds -> 19k).
        if not have_wheat and unfed and int(st.get('wleft', 0) or 0) <= 0:
            # MATURITY ONLY (same rule as the crop sweep): harvesting green
            # wheat for feed destroys up to ~3u of future yield per tile
            # (K2-verified: unfert wheat lifetime is 4u total) to save one
            # walk, collapsing the wheat economy into a death spiral
            # (unfertilized trial of this block: 44.8k -> 8.9k on 200004).
            wcd = CROPS.get('WHEAT', {})
            wmx = wcd.get('maxyield', 6)
            wmaxday = wcd.get('maxday', 4)
            # skip wheat a crop unit already walks (its day-claim): without
            # this the crop unit treks to an empty tile when this harvests
            # first -- the same stale-target waste shared claims fixed.
            cclaimed = set()
            for u, v in (st.get('claim', {}) or {}).items():
                if u != i and v:
                    try:
                        cclaimed.add((v[0], v[1]))
                    except Exception:
                        pass
            ripe = []
            for x, y, t in ctx.plants:
                if t.get('crop') != 'WHEAT' or (x, y) in taken \
                        or (x, y) in cclaimed:
                    continue
                try:
                    age = ctx.day - int(t.get('planted_day', 0) or 0)
                    yld = int(t.get('yield_units', 0) or 0)
                except Exception:
                    continue
                if yld >= wmx or age > wmaxday or \
                        (age == wmaxday and t.get('watered_today') and yld > 0):
                    ripe.append((x, y))
            if ripe:
                x, y = min(ripe, key=lambda z: manhattan(p, z))
                taken.add((x, y))
                aclaims[i] = (x, y)
                if (p[0], p[1]) == (x, y):
                    return ['HARVEST']
                return step_toward(p, (x, y)) or ['PASS']
        # 6) VISIT: nearest animal tile with unfinished work. The batch
        #    at (3) finishes tiles in one visit, so the CAPHARV sweep, the
        #    CARE sweep and the value-density harvest sweep collapse into this
        #    single traveler -- value-density ranking across the farm was
        #    sending units on cross-map trips (the walk disease). A unit
        #    standing on an unfinished tile never reaches here: the batch
        #    acts first. Same gate as the batch: herd fed or h10.
        if not unfed_any or ctx.hour >= 10:
            visit = [(x, y) for x, y, t in ctx.structs
                     if t.get('animal') is not None and (x, y) not in taken
                     and (x, y) not in others_a
                     and ((t.get('fed_today') and not t.get('cared_today')
                           and int(t.get('yield_units', 0) or 0)
                           < ANIMAL_MAXHELD.get(t.get('animal'), 6))
                          or int(t.get('yield_units', 0) or 0) > 0
                          or t.get('fertilizer_available'))]
            if visit:
                x, y = min(visit, key=lambda z: manhattan(p, z))
                taken.add((x, y))
                aclaims[i] = (x, y)
                return step_toward(p, (x, y)) or ['PASS']
        # 7) carried fertilizer -> onto a needy plant now (an animal standing
        #    in the crop rows applies it where it doubles yield); else shed it
        #    so it sells instead of stranding.
        fert = int(inv_i.get('FERTILIZER', 0) or 0)
        if fert:
            fz = self.needy_plant(ctx, p, taken)
            if fz:
                x, y = fz
                if (p[0], p[1]) == (x, y):
                    return ['FERTILIZE']
                return step_toward(p, (x, y)) or ['PASS']
            bc = bank_cmd(ctx, st, inv_i, exclude=('WHEAT',))
            if bc is None:
                pass  # shed full: hold, retry after the market sells
            elif shed_adjacent(p):
                return bc
            else:
                return step_toward(p, nearest_shed_tile(p)) or ['PASS']
        # 8) COLLECT_FERTILIZER (every animal makes 1/day)
        cf = [(x, y) for x, y, t in ctx.structs
              if t.get('animal') is not None and t.get('fertilizer_available')
              and (x, y) not in taken and (x, y) not in others_a]
        if cf:
            x, y = min(cf, key=lambda z: manhattan(p, z))
            if (p[0], p[1]) == (x, y):
                taken.add((x, y))
                aclaims[i] = (x, y)
                return ['COLLECT_FERTILIZER']
            taken.add((x, y))
            aclaims[i] = (x, y)
            return step_toward(p, (x, y)) or ['PASS']
        # 9) BUILD if there is a structure deficit (BUILD is free; only the
        #    walk + action). Above the fert pull: a waiting animal produces
        #    nothing and blocks herd growth, while fertilizer keeps. Reserve
        #    the tile across both pres (persist the walk) and taken (hold it
        #    for the step): without this, two animal units run identical
        #    deterministic free_tile() and converge on one tile, so one BUILD
        #    silently fails every time.
        if self.structure_deficit(ctx) and ctx.empty_tiles:
            pres = st.setdefault('pres', {})
            claimed = set()
            for u, t_ in pres.items():
                if u != i and t_:
                    claimed.add(tuple(t_))
            tgt = self.free_tile(ctx, set(taken) | claimed, p)
            if tgt:
                pres[i] = tgt
                taken.add(tgt)
                if (p[0], p[1]) == tgt:
                    pres.pop(i, None)
                    return [self.build_kind(ctx)]
                return step_toward(p, tgt) or ['PASS']
        # 10) shed fertilizer -> pull it out whenever a plant can bank it
        #    (crop units never touch fert, so the animal role owns the loop).
        #    The old >15 stockpile threshold starved the fields: the replay
        #    champion pulls 2-6 at a time, ~20/day, and puts ~200/game mostly
        #    on wheat bank days. Carry six; the apply step sheds the surplus.
        if int(ctx.shed.get('FERTILIZER', 0) or 0) > 0 \
                and self.needy_plant(ctx, p, taken) is not None:
            if shed_adjacent(p):
                return ['PICKUP', 'FERTILIZER', min(6, int(ctx.shed.get('FERTILIZER', 0) or 0))]
            return step_toward(p, nearest_shed_tile(p)) or ['PASS']
        return None   # idle -> help the crop sweep

    # ---------------- crop role ----------------
    def sweep_order(self, ctx, col):
        """Tiles in a column, ordered away from the shed (y=4 first = nearest
        the supply point). Without col, a continuous snake over the whole
        unlocked farm."""
        out = []
        if col is not None:
            H = len(ctx.tiles)
            return [(col, y) for y in range(H)
                    if self.tile_at(ctx, col, y) != 'LOCKED']
        H = len(ctx.tiles)
        home = [y for y in range(H) if y <= 4]
        ext = [y for y in range(H) if y > 4]
        rows = sorted(home, reverse=True) + sorted(ext, reverse=True)
        for k, y in enumerate(rows):
            xs = [x for x in range(len(ctx.tiles[y]))
                  if self.tile_at(ctx, x, y) != 'LOCKED']
            if k % 2 == 0:
                xs.reverse()
            out.extend((x, y) for x in xs)
        return out

    def sweep_work(self, ctx, col, crop, taken):
        """Work in a column: ripe (harvest), thirsty/bank-day (water), weed or
        expired (dig), empty (plant). Water outranks plant so tiles never die
        into weeds; harvest maturity is per crop so one-shots are never taken
        green (harvesting clears the tile and destroys the remaining bank
        days -- the replay champion takes wheat at 0.8-1.0 fill, never 0.3)."""
        out = []
        for x, y in self.sweep_order(ctx, col):
            if (x, y) in self.SHED_TILES or (x, y) in taken:
                continue
            t = self.tile_at(ctx, x, y)
            if isinstance(t, dict) and t.get('kind') == 'PLANT':
                cd = CROPS.get(t.get('crop'), {})
                try:
                    age = ctx.day - int(t.get('planted_day', 0) or 0)
                    yld = int(t.get('yield_units', 0) or 0)
                except Exception:
                    age, yld = -1, 0
                if cd.get('ongoing'):
                    # expired ongoing (all productions banked) -> free the
                    # tile for replanting instead of watering a corpse.
                    if age > cd.get('first', 99) + cd.get('maxyield', 4) * max(1, cd.get('interval', 1)):
                        out.append((x, y, 'DIG'))
                        continue
                    # harvest at ANY yield (a threshold-3 was tried: our cash
                    # engine is timing-sensitive -- delaying strawberry banks
                    # 2-4 days slips the land/herd ramp, net -1.1k with -4.3k
                    # on 200002; early dollars compound).
                    if age >= cd.get('first', 99) and yld > 0:
                        out.append((x, y, 'HARV'))
                    elif not t.get('watered_today'):
                        # survival, plus the production eve for FERTILIZED
                        # ongoing only: an unfertilized crop banks +1 on
                        # production days whether or not it is watered, so
                        # watering it outside survival is wasted labor. A
                        # fertilized crop only banks the doubling on a
                        # watered production day.
                        cu = int(t.get('consecutive_unwatered', 0) or 0)
                        fert = int(t.get('fertilized_until_day', -1) or -1) >= ctx.day
                        dsf = ctx.day + 1 - int(t.get('planted_day', 0) or 0) - cd.get('first', 99)
                        if cu >= 1 or (fert and dsf >= 0 and dsf % max(1, cd.get('interval', 1)) == 0):
                            out.append((x, y, 'WATER'))
                else:
                    mx = cd.get('maxyield', 6)
                    maxday = cd.get('maxday', 99)
                    if yld >= mx or age > maxday or \
                            (age == maxday and t.get('watered_today') and yld > 0):
                        out.append((x, y, 'HARV'))
                    elif not t.get('watered_today'):
                        # survival-minimum watering. A plant dies at
                        # consecutive_unwatered >= 2 (end of day), and planting day
                        # already counts as 1, so a tile that skipped yesterday --
                        # or was just planted -- MUST be watered today or it dies
                        # into a weed. A tile watered yesterday can wait, EXCEPT
                        # inside the bank window: a one-shot only banks yield on
                        # watered days, so every skipped window day is -1 (-2
                        # fertilized) units lost forever.
                        cu = int(t.get('consecutive_unwatered', 0) or 0)
                        wstart = (maxday + 1) // 2
                        if cu >= 1 or (wstart <= age <= maxday and yld < mx):
                            out.append((x, y, 'WATER'))
            elif isinstance(t, dict) and t.get('kind') == 'WEED':
                out.append((x, y, 'DIG'))
            elif t is None and crop is not None:
                out.append((x, y, 'PLANT'))
        return out

    def crop_work(self, ctx, st, i, p, inv_i, taken, sibpos):
        """Column-locked PLANT->WATER sweep with batched delivery. Never emits
        an animal action except placement (the farmer places too: the replay
        champion's farmer places ~11 animals a game) and the escape guard
        (permanent loss outranks any crop), and only late in the day so the
        sweep isn't punctured."""
        if ctx.day >= 29:
            return self.endgame_work(ctx, st, i, p, inv_i, taken)
        # a0) carrying an animal -> place it now; the farmer also fetches
        #     one from the shed when the burst gate allows (replay champion's
        #     farmer places ~11/game). Other crop units do NOT fetch here:
        #     d0 plant/water is same-day survival (planted cu=1 dies unwatered
        #     overnight) while a new animal survives its first day unfed, so
        #     planting+watering outranks fetching; crop units only fetch once
        #     the sweep is clean (see (f) below).
        for a in ANIMALS:
            if int(inv_i.get(a, 0) or 0) > 0:
                return self.place_animal(ctx, st, i, p, taken, a)
        if i == 0:
            c = self.burst_fetch(ctx, st, i, p)
            if c is not None:
                return c
        # P1 walk wrapper: before spending a step on movement, try to spend it
        # on work the tile underfoot needs (survival water, weed, or lifting
        # fertilizer off an animal tile into the pocket). The claim and the
        # target are untouched -- the unit resumes its walk next step. This is
        # what converts a WALK step into an ACTION step; the COOP/PASTURE
        # branch is the fertilizer supply that never touches the shed.
        def walk(tgt):
            c = self.enroute_cmd(ctx, st, i, p, tgt)
            if c is not None:
                return c
            return step_toward(p, tgt) or ['PASS']

        # a) escape guard: an animal already unfed yesterday AND today will
        #    escape tonight. Feed it even at crop labour's expense.
        if ctx.day < 28 and ctx.hour >= 18 and int(inv_i.get('WHEAT', 0) or 0) > 0:
            for x, y, t in ctx.structs:
                if t.get('animal') is None or t.get('fed_today'):
                    continue
                if int(t.get('consecutive_unfed', 0) or 0) >= 1 and (x, y) not in taken:
                    if (p[0], p[1]) == (x, y):
                        taken.add((x, y))
                        return ['FEED']
                    taken.add((x, y))
                    return step_toward(p, (x, y)) or ['PASS']
        # b) carried fert -> apply, else shed (kept out of the produce path so
        #    it reaches the field rather than the sell pile)
        fert = int(inv_i.get('FERTILIZER', 0) or 0)
        if fert:
            fz = self.needy_plant(ctx, p, taken)
            if fz:
                x, y = fz
                if (p[0], p[1]) == (x, y):
                    return ['FERTILIZE']
                return walk((x, y))
            bc = bank_cmd(ctx, st, inv_i, exclude=('WHEAT',))
            if bc is None:
                pass  # shed full: hold, retry after the market sells
            elif shed_adjacent(p):
                return bc
            else:
                return walk(nearest_shed_tile(p))
        # c) batched delivery: a real load, or late enough that the midnight
        #    shed drop would destroy cargo past the 100-slot cap. Immediate
        #    drop-after-every-harvest was tried and lost ~2k: the extra shed
        #    round-trips cost more than a day of better prices returns.
        load = sum(v for k, v in inv_i.items()
                   if k in PRODUCTS and k not in ('WHEAT', 'FERTILIZER') and v)
        if ctx.day >= 28:
            load += int(inv_i.get('WHEAT', 0) or 0)   # feed is over; wheat sells
        if load and (load >= 6 or ctx.hour >= 21):
            # d28+: wheat sells too (feed is over), so it joins the bank.
            bc = bank_cmd(ctx, st, inv_i,
                          exclude=('FERTILIZER',) if ctx.day >= 28 else ('WHEAT', 'FERTILIZER'))
            if bc is None:
                pass  # shed full: hold cargo, do field work, retry later
            elif shed_adjacent(p):
                return bc
            else:
                return walk(nearest_shed_tile(p))
        # d) crop choice for planting (same targets the scheduler already set)
        tgts = st.get('crops', {}) or {}
        if ctx.day == 0:
            order = ('MELON', 'WHEAT', 'STRAWBERRY', 'TOMATO', 'CARROT')
        elif ctx.day <= 1:
            order = ('WHEAT', 'MELON', 'STRAWBERRY', 'TOMATO', 'CARROT')
        else:
            order = ('MELON', 'STRAWBERRY', 'WHEAT', 'TOMATO', 'CARROT')
        # FEED FLOOR: wheat is the herd's survival input, and the animal
        # purchase gate keys on shed wheat (feed_cap = max(herd, min(cap,
        # shedW))). Below the floor, wheat outranks everything. Floor is 1x
        # herd, period (FEED=1 wheat/animal/day: 1x herd IS one day of feed).
        # Static 1.5x: +6-8k on 2 seeds, -13k/-22k on 2 others
        # (net -3.9k). A crisis-latched 1.5x (shed-empty trigger) was WORSE
        # (net -8.5k): it plants extra wheat exactly when the system is
        # stressed, displacing cash crops at the worst moment -- insurance
        # built during a crunch compounds the crunch. Feed insurance must be
        # built in surplus (early/calm planting) or bought (emergency wheat
        # buy), never planted into stress.
        if ctx.day < 28:
            herd_n = sum(1 for _, _, t in ctx.structs if t.get('animal') is not None)
            # REVERTED ripe-only reserve (A/B: 30.8k vs 40.4k, 200005
            # 48.3k->14.7k): ripe standing is transient (the sweep harvests
            # at maturity the same day), so shed+ripe < herd fires almost
            # every day and wheat jumps the queue whenever its target is
            # unmet -- systematic early over-planting that displaces
            # melon/straw at the compounding stage. The "phantom" standing
            # count was accidentally a wheat throttle: targets (WHEAT
            # 28/24/12/16) already size the machine; the floor stays rare.
            if int(ctx.shed.get('WHEAT', 0) or 0) + ctx.standing_crops.get('WHEAT', 0) < herd_n:
                order = ('WHEAT',) + tuple(c for c in order if c != 'WHEAT')
        crop = None
        for c in order:
            want = tgts.get(c, 0)
            if want and ctx.standing_crops.get(c, 0) < want \
                    and int(st['sleft'].get(c, 0) or 0) > 0:
                crop = c
                break
        # ROOM GUARD: planting the last free tiles while bought animals sit
        # in the shed deadlocks the herd (no room to build structures, and
        # the market keeps buying into the jam). Keep two spares for
        # structures until the backlog is placed.
        unplaced = sum(int(ctx.owned.get(a, 0) or 0) for a in ANIMALS) \
            - sum(1 for _, _, t in ctx.structs if t.get('animal') is not None)
        if unplaced > 0 and len(ctx.empty_tiles) <= 2:
            crop = None
        # e) the sweep: own column, help anywhere when it is clean
        col = st.get('cols', {}).get(i)
        work = self.sweep_work(ctx, col, crop, taken)
        if not work:
            work = self.sweep_work(ctx, None, crop, taken)
        if not work:
            # sweep clean -> join the placement burst (no quota; the fed-gate
            # keeps mornings safe). Keeps wave days absorbing 4 buys/day
            # without stealing plant/water labor while the sweep has work.
            c = self.burst_fetch(ctx, st, i, p)
            if c is not None:
                return c
            return None
        harvs = [w for w in work if w[2] == 'HARV']
        waters = [w for w in work if w[2] == 'WATER']
        digs = [w for w in work if w[2] == 'DIG']
        plants_ = [w for w in work if w[2] == 'PLANT']
        # nearest-within-tier: column-scan order walks past closer work
        # (a unit crosses 3 harvestable tiles to reach the scan-first one).
        # Priority across tiers is unchanged (HARV>WATER>DIG>PLANT); within a
        # tier go nearest. Compounds with sticky claims (claims pin the walk
        # once chosen; this chooses the shortest walk).
        harvs.sort(key=lambda w: manhattan(p, (w[0], w[1])))
        waters.sort(key=lambda w: manhattan(p, (w[0], w[1])))
        digs.sort(key=lambda w: manhattan(p, (w[0], w[1])))
        plants_.sort(key=lambda w: manhattan(p, (w[0], w[1])))
        # (Farm-compaction planting was tried: preferring blob-adjacent
        # tiles packed plants around the shed, leaving no room for nearby
        # structures; pastures went far, feed walks exploded, avg 39.3k ->
        # 29.0k. The column-snake spread is load-bearing for structure room.
        # A repaired version would compact while reserving the shed ring.)
        here = self.tile_at(ctx, p[0], p[1])
        on_plant = isinstance(here, dict) and here.get('kind') == 'PLANT'
        claims = st.setdefault('claim', {})
        # shared claims, first-come wins: sibling units' walk targets are
        # invisible in `taken` (per-step only), so two units chase the same
        # tile across steps and the loser re-walks every time. Skip tiles a
        # sibling already walks. (Stealing and distance filters both tried,
        # both lost: thrash and double-walking respectively.)
        owner_of = {}
        for u, v in claims.items():
            if u != i and v:
                try:
                    owner_of[(v[0], v[1])] = u
                except Exception:
                    pass
        # animal-crew feed-direct targets are also served: an animal unit
        # harvesting this wheat tile makes a crop trip here wasted (it is
        # harvested when the crop unit arrives). Same first-come rule.
        # (No small-herd gate here: the wheat contention it prevents exists
        # at every herd size, and bisect showed this side carries 200003's
        # gain while the animal-side exclusion carried 200004's loss.)
        for u, v in (st.get('aclaim', {}) or {}).items():
            if u != i and v:
                try:
                    owner_of.setdefault((v[0], v[1]), u)
                except Exception:
                    pass

        def act_on(q, cmd):
            if not q:
                return None
            best = None
            for w in q:
                t = (w[0], w[1])
                owner = owner_of.get(t)
                if owner is not None and owner != i:
                    continue  # sibling walks it: commitment wins
                dme = abs(p[0] - t[0]) + abs(p[1] - t[1])
                if best is None or dme < best[0]:
                    best = (dme, w)
            if best is None:
                return None
            _, (x, y, _) = best
            if (p[0], p[1]) == (x, y):
                claims.pop(i, None)
                return [cmd]
            # persist the walk target: without memory two units chase the
            # same tile across steps and one PASSes every time (~11 wasted
            # walks/day). The claim is re-validated below each step, so a
            # stale target is dropped, never stuck.
            claims[i] = (x, y, cmd)
            return walk((x, y))

        # sticky claim: keep walking a validated target instead of
        # re-planning (and oscillating) every step. HARVEST/WATER/DIG only;
        # PLANT claims are skipped (crop choice + seed budget shift per step).
        ck = claims.get(i)
        if ck is not None:
            cx, cy, ca = ck
            lst = {'HARVEST': harvs, 'WATER': waters, 'DIG': digs}.get(ca, [])
            if any((x, y) == (cx, cy) for x, y, _ in lst) and (cx, cy) not in taken:
                taken.add((cx, cy))
                if (p[0], p[1]) == (cx, cy):
                    claims.pop(i, None)
                    return [ca]
                return walk((cx, cy))
            claims.pop(i, None)

        # standing on a ripe/unwatered tile -> act now, no walk wasted
        if on_plant and (p[0], p[1]) not in self.SHED_TILES:
            cd = CROPS.get(here.get('crop'), {})
            try:
                age = ctx.day - int(here.get('planted_day', 0) or 0)
                yld = int(here.get('yield_units', 0) or 0)
            except Exception:
                age, yld = -1, 0
            if cd.get('ongoing'):
                ripe = age >= cd.get('first', 99)
            else:
                mx = cd.get('maxyield', 6)
                maxday = cd.get('maxday', 99)
                ripe = yld >= mx or age > maxday or \
                    (age == maxday and here.get('watered_today'))
            if ripe and yld > 0:
                return ['HARVEST']
            if not here.get('watered_today'):
                # P2: the engine reads fertilized_until_day at WATER time, so
                # FERTILIZE must land on an EARLIER step. Emit it now and the
                # block returns WATER next step on the same tile (zero
                # movement, claim untouched). The hurdle refuses crops whose
                # gain cannot beat the fertilizer quote.
                c = self.fert_cmd(ctx, st, i, p)
                if c is not None:
                    return c
                return ['WATER']
        # bank ripe yield before anything else: a dead ripe tile loses the crop
        # (an emergency-water-above-harvest tier was tried: +12k on weedy
        # 200002 but -18k on clean 200004, net -2k. Prioritization is
        # zero-sum under saturation; weeds need labor, not reordering.)
        c = act_on(harvs, 'HARVEST')
        if c:
            return c
        # keep-alive: water before planting, always
        c = act_on(waters, 'WATER')
        if c:
            return c
        # clear weeds (a weed is a dead tile until dug)
        c = act_on(digs, 'DIG')
        if c:
            return c
        # plant: standing on an empty tile with seeds -> PLANT (claim against
        # the shared per-step seed budget so the atomic PLANT check never fires)
        if crop is not None and here is None and (p[0], p[1]) not in self.SHED_TILES:
            st['sleft'][crop] = int(st['sleft'].get(crop, 0) or 0) - 1
            return ['PLANT', crop]
        c = act_on(plants_, 'PLANT')
        if c and crop is not None:
            return c
        return None

    # ---------------- main dispatch ----------------
    def run(self, ctx):
        st = getst(ctx.seat)
        # per-step wheat budget: feeders claim shed wheat as they go, so the
        # whole workforce doesn't converge on the shed for crumbs.
        if st.get('wstep') != ctx.step:
            st['wstep'] = ctx.step
            st['wleft'] = int(ctx.shed.get('WHEAT', 0) or 0)
        n_units = 1 + len(ctx.hands)
        pos = [ctx.farmer] + ctx.hands
        inv = ctx.invs
        # per-step seed budget (atomic PLANT guard)
        if st.get('sstep') != ctx.step:
            st['sstep'] = ctx.step
            st['sleft'] = dict(ctx.seeds)
        # per-step shed-animal budget: without pdone quota, every unit sees
        # the same step-start shed snapshot and stampedes it (4 units walk
        # for 2 animals; the losers walk back empty). Budget it like wheat.
        if st.get('astep') != ctx.step:
            st['astep'] = ctx.step
            st['aleft'] = sum(int(ctx.shed.get(a, 0) or 0) for a in ANIMALS)
        # roles: recompute at dawn (hands reset nightly), when the crew size
        # changes, or when animals are waiting with no animal crew assigned
        owned = sum(ctx.owned.get(a, 0) for a in ANIMALS)
        placed_n = sum(1 for _, _, t in ctx.structs if t.get('animal') is not None)
        unplaced = max(0, owned - placed_n)
        roles = st.get('roles')
        need_reassign = (st.get('role_day') != ctx.day
                         or not roles or len(roles) != n_units
                         or (unplaced > 0 and not any(r == 'animal' for r in roles.values())))
        if need_reassign:
            st['role_day'] = ctx.day
            st['roles'] = self.assign_roles(ctx, st, n_units)
            st.pop('pres', None)   # tile reservations are per-day
            st.pop('claim', None)  # walk-target memory is per-day too
            st.pop('aclaim', None)  # animal-crew targets likewise
            roles = st['roles']
        # mid-day hires default to crops; the farmer always crops
        for u in list(roles):
            if u >= n_units:
                del roles[u]
        while len(roles) < n_units:
            roles[len(roles)] = 'crop'
        roles[0] = 'crop'

        cmds = {}
        taken = set()
        for i in range(n_units):
            if i in cmds:
                continue
            p = pos[i]
            inv_i = inv[i] or {}
            c = None
            if roles.get(i) == 'animal':
                c = self.animal_work(ctx, st, i, p, inv_i, taken, pos)
            if c is None:
                c = self.crop_work(ctx, st, i, p, inv_i, taken, pos)
            if c is None:
                cmds[i] = ['PASS']
            else:
                op = c[0]
                T['exec_tasks'][op] = T['exec_tasks'].get(op, 0) + 1
                cmds[i] = c
        ctx.unit_cmds = cmds

SCHED = Scheduler()
MARKET = MarketEmit()
FIELD = FieldExec()

def agent(observation, configuration=None):
    try:
        T['steps'] += 1
        ctx = Ctx(observation)
        SCHED(ctx)
        MARKET(ctx)
        FIELD(ctx)
        n = 1 + len(ctx.hands)
        hands = [ctx.unit_cmds.get(i, ['PASS']) for i in range(1, n)]
        return {'farmer': ctx.unit_cmds.get(0, ['PASS']), 'hands': hands, 'market': ctx.orders}
    except Exception:
        T['errors'] += 1
        return {'farmer': ['PASS'], 'hands': [], 'market': []}
