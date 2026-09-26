"""Parallel paired screen: A vs B (or single file) over N fresh seeds, solo vs PASS.
Usage: LINE_FORCE=pinned python3 tools/pscreen.py <A.py> [B.py] [n=16] [seed0=300001]
Prints per-seed A,B,delta + mean delta + paired t-stat. Fresh seeds avoid
cherry-seed (200001-6) tuning bias. 8 workers; ~4s/game.
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
    path, seed = args
    from fast_kaggr_env import FastKaggrEnvPy as Env
    import harness
    nsA = harness.load(path, 's')
    aA = nsA['agent']
    aO = lambda o, c: {'farmer': ['PASS'], 'hands': [], 'market': []}  # noqa
    env = Env({'seed': seed, 'episodeSteps': 720})
    env.reset(2)
    while not env.done:
        oA = env.state[0].observation
        oB = env.state[1].observation
        try:
            rA = aA(oA, None)
        except Exception:
            rA = {'farmer': ['PASS'], 'hands': [], 'market': []}
        try:
            rB = aO(oB, None)
        except Exception:
            rB = {'farmer': ['PASS'], 'hands': [], 'market': []}
        env.step([rA, rB])
    return seed, round(env.state[0].reward)


def main():
    A = sys.argv[1]
    if len(sys.argv) > 2 and sys.argv[2].endswith('.py'):
        B, rest = sys.argv[2], sys.argv[3:]
    else:
        B, rest = None, sys.argv[2:]
    n = int(rest[0]) if rest else 16
    seed0 = int(rest[1]) if len(rest) > 1 else 300001
    seeds = [seed0 + i for i in range(n)]
    with Pool(WORKERS) as p:
        ra = dict(p.map(play_one, [(A, s) for s in seeds]))
    if B:
        with Pool(WORKERS) as p:
            rb = dict(p.map(play_one, [(B, s) for s in seeds]))
        ds = [rb[s] - ra[s] for s in seeds]
        for s in seeds:
            print('seed=%d A=%d B=%d d=%+d' % (s, ra[s], rb[s], rb[s] - ra[s]), flush=True)
        m = sum(ds) / n
        sd = math.sqrt(sum((x - m) ** 2 for x in ds) / max(1, n - 1))
        t = m / (sd / math.sqrt(n)) if sd > 0 else 0.0
        wins = sum(1 for x in ds if x > 0)
        print('B-A mean=%+.0f sd=%.0f t=%.2f wins=%d/%d' % (m, sd, t, wins, n), flush=True)
    else:
        for s in seeds:
            print('seed=%d A=%d' % (s, ra[s]), flush=True)
        m = sum(ra.values()) / n
        print('mean=%.0f' % m, flush=True)


if __name__ == '__main__':
    main()
