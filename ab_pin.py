"""Pinned A/B: LINE_FORCE=<line> for both variants, given seeds, vs opp_pipe19 (seat 1).
Usage: LINE_FORCE=pinned python3 ab_pin.py pinned <A.py> <B.py> [seeds...]
Default seeds: 200001-200005. A/B each play seat 1 (opp_pipe19 sits seat 0)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

line = sys.argv[1]
A = sys.argv[2]
B = sys.argv[3]
seeds = tuple(int(x) for x in sys.argv[4:]) or (200001, 200002, 200003, 200004, 200005)
os.environ['LINE_FORCE'] = line
from fast_kaggr_env import FastKaggrEnvPy as Env
import harness


def score(path, tag, seed):
    nsA = harness.load(path, tag)
    nsO = harness.load(HERE + '/opp_pipe19.py', 'opp')
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
    return env.state[1].reward


for name, path in [('A', A), ('B', B)]:
    out = []
    for s in seeds:
        v = score(path, f'{name}{line}{s}', s)
        out.append(v)
        print(f"  {name}[{line}] seed{s}={v:7.0f}", flush=True)
    print(f"{name}[{line}] " + " ".join(f"{v:7.0f}" for v in out) + f"   avg={sum(out)/len(out):8.0f}", flush=True)
