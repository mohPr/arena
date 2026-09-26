"""Repeat probe: are animal verbs (FEED/CARE/COLLECT) repeated on the same tile-day?
Usage: python3 tools/repeat_probe.py [agent.py] [seed]
Reports per-verb acts/day, distinct tiles touched/day, and top repeat tiles.
"""
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from collections import Counter, defaultdict
from fast_kaggr_env import FastKaggrEnvPy as Env
import harness

AGENT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(HERE) + '/agent_current.py'
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 200001
ns = harness.load(AGENT, 'A')
env = Env({'seed': SEED, 'episodeSteps': 720})
env.reset(2)
D = {'farmer': ['PASS'], 'hands': [], 'market': []}
touch = defaultdict(Counter)  # (day, verb) -> Counter(xy)
tot = Counter()
while not env.done:
    o = env.state[0].observation
    day = o.day
    if day > 29:
        break
    try:
        r = ns['agent'](o, None)
    except Exception:
        r = dict(D)
    f = o.farms[0]
    pos = [tuple(f['farmer'])] + [tuple(p) for p in (f.get('hands') or [])]
    ops = [r.get('farmer')] + list(r.get('hands') or [])
    for xy, op in zip(pos, ops):
        if isinstance(op, list) and op and op[0] in ('FEED', 'CARE', 'COLLECT_FERTILIZER', 'WATER'):
            touch[(day, op[0])][xy] += 1
            tot[(day, op[0])] += 1
    env.step([r, dict(D)])
print('day verb total distinct_tiles max_per_tile n_repeat_tiles')
for (day, verb) in sorted(tot):
    c = touch[(day, verb)]
    mx = max(c.values())
    rep = sum(1 for v in c.values() if v > 1)
    extra = ''
    if day >= 12 and verb in ('FEED', 'CARE'):
        top = c.most_common(3)
        extra = f' top={top}'
    print(f'd{day:>2} {verb:<18} {tot[(day,verb)]:>4} {len(c):>4} {mx:>3} {rep:>3}{extra}')
