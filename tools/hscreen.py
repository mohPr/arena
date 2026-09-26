"""Parallel paired h2h screen: A vs B, both seat 1 vs OPP seat 0, same seeds.
Usage: LINE_FORCE=pinned python3 tools/hscreen.py <A.py> <B.py> <opp.py> [n=16] [seed0=300001]
Prints per-seed us/opp/margin both files + paired margin-delta t-stat.
"""
import os
import sys
import math
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.dirname(HERE)
sys.path.insert(0, PARENT)
sys.path.insert(0, HERE)
WORKERS = 8


def play_one(args):
    path, opp, seed = args
    from fast_kaggr_env import FastKaggrEnvPy as Env
    import harness
    nsA = harness.load(path, 'v')
    nsO = harness.load(opp, 'o')
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
    return seed, round(env.state[1].reward), round(env.state[0].reward)


def main():
    A, B, O = sys.argv[1], sys.argv[2], sys.argv[3]
    rest = sys.argv[4:]
    n = int(rest[0]) if rest else 16
    seed0 = int(rest[1]) if len(rest) > 1 else 300001
    seeds = [seed0 + i for i in range(n)]
    with Pool(WORKERS) as p:
        ra = dict((s, (u, o)) for s, u, o in p.map(play_one, [(A, O, s) for s in seeds]))
    with Pool(WORKERS) as p:
        rb = dict((s, (u, o)) for s, u, o in p.map(play_one, [(B, O, s) for s in seeds]))
    ds = []
    for s in seeds:
        ua, oa = ra[s]
        ub, ob = rb[s]
        dma, dmb = ua - oa, ub - ob
        ds.append(dmb - dma)
        print('seed=%d A:us=%d opp=%d m=%+d | B:us=%d opp=%d m=%+d | dm=%+d'
              % (s, ua, oa, dma, ub, ob, dmb, dmb - dma), flush=True)
    m = sum(ds) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in ds) / max(1, n - 1))
    t = m / (sd / math.sqrt(n)) if sd > 0 else 0.0
    print('margin-delta mean=%+.0f sd=%.0f t=%.2f' % (m, sd, t), flush=True)


if __name__ == '__main__':
    main()
