"""Production meters for our agent: acts/day, mv/act, gap hist, feeds/d."""
import sys
import os as _o; sys.path.insert(0, _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), ".."))
from fast_kaggr_env import FastKaggrEnvPy as Env
from collections import Counter, defaultdict

agent_path, seat, seed = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
ns = {}
exec(compile(open(agent_path).read(), 'a', 'exec'), ns)
ag = ns['agent']
env = Env({'seed': seed, 'episodeSteps': 720})
env.reset(2)
MOVES = {'NORTH', 'SOUTH', 'EAST', 'WEST'}
perday = defaultdict(Counter)
gap = Counter()
lastmv = defaultdict(int)
acted = defaultdict(bool)
while not env.done:
    oA = env.state[seat].observation
    day = oA['day']
    try:
        r = ag(oA, None)
    except Exception:
        r = {'farmer': ['PASS'], 'hands': [], 'market': []}
    ops = [r['farmer']] + r['hands']
    for i, op in enumerate(ops):
        o = op[0]
        perday[day][o] += 1
        if o in MOVES:
            lastmv[(day, i)] += 1
        elif o == 'PASS':
            pass
        else:
            if acted[(day, i)]:
                gap[lastmv[(day, i)]] += 1
            acted[(day, i)] = True
            lastmv[(day, i)] = 0
    env.step([r, {'farmer': ['PASS'], 'hands': [], 'market': []}] if seat == 0 else [{'farmer': ['PASS'], 'hands': [], 'market': []}, r])
print('rewards', [round(x) for x in (env.state[0].reward, env.state[1].reward)])
for d in sorted(perday):
    c = perday[d]
    A = sum(v for k, v in c.items() if k not in MOVES and k != 'PASS')
    M = sum(v for k, v in c.items() if k in MOVES)
    if d in (0, 1, 5, 6, 10, 11, 12, 13, 15):
        print(f'd{d}: acts={A} mv={M} mv/act={M/max(1,A):.2f} FEED={c["FEED"]} CARE={c["CARE"]} WATER={c["WATER"]}')
tot = sum(gap.values())
print('gap hist:', {g: round(gap[g]/tot, 2) for g in sorted(gap)[:8]}, 'n=', tot)
