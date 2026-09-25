"""Pinned A/B vs any opponent: both variants play seat 1, opp sits seat 0.
Usage: LINE_FORCE=pinned python3 ab_pin_opp.py pinned <A.py> <B.py> <opp.py> [seeds...]
Default seeds: 200001-200005. Prints per-seed lines + totals (never average alone).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

line = sys.argv[1]
A = sys.argv[2]
B = sys.argv[3]
O = sys.argv[4]
seeds = tuple(int(x) for x in sys.argv[5:]) or (200001, 200002, 200003, 200004, 200005)
os.environ['LINE_FORCE'] = line
from fast_kaggr_env import FastKaggrEnvPy as Env
import harness


def score(path, tag, seed):
    nsA = harness.load(path, tag)
    nsO = harness.load(O, 'opp')
    a0, a1 = nsO['agent'], nsA['agent']
    env = Env({'seed': seed, 'episodeSteps': 720})
    env.reset(2)
    while not env.done:
        o0, o1 = env.state[0].observation, env.state[1].observation
        try:
            r0 = a0(o0, None)
        except Exception:
            r0 = {'farmer': ['PASS'], 'hands': [], 'market': []}
        try:
            r1 = a1(o1, None)
        except Exception:
            r1 = {'farmer': ['PASS'], 'hands': [], 'market': []}
        env.step([r0, r1])
    return env.state[1].reward, env.state[0].reward


for name, path in [('A', A), ('B', B)]:
    out = []
    for s in seeds:
        v, o = score(path, f'{name}{line}{s}', s)
        out.append((v, o))
        print(f"  {name}[{line}] seed{s} us={v:7.0f} opp={o:7.0f} margin={v - o:7.0f}", flush=True)
    tu = sum(v for v, _ in out)
    to = sum(o for _, o in out)
    print(f"{name}[{line}] " + " ".join(f"{v:7.0f}" for v, _ in out)
          + f"   total={tu:8.0f} opp={to:8.0f} margin={tu - to:8.0f}", flush=True)
