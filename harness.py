# new_agent harness: fresh-load runner, both seats, matrix + gates, layer telemetry.
# Usage: python3 harness.py <agent_path> [n_seeds]  (opponents = iter set, seats alternate)
import sys

sys.path.insert(0, '/home/moh/Desktop/glm2/result/agent4_trainer_v2')
from fast_kaggr_env import FastKaggrEnvPy as Env

R = '/home/moh/Desktop/glm2/result/v77-pack/'
OPPS = {'pipe19': R + 'opp_pipe19.py', 'pipe18': R + 'opp_pipe18.py',
        'kagg': R + 'opp_kagg.py', 'v57': R + 'opp_v57.py'}
SEEDS = [200001, 200002]

def load(path, tag):
    ns = {'__name__': tag}
    exec(compile(open(path).read(), tag, 'exec'), ns)
    return ns

def play(ns0, ns1, seed, trace_money=False):
    a0, a1 = ns0['agent'], ns1['agent']
    env = Env({'seed': seed, 'episodeSteps': 720})
    env.reset(2)
    money = []
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
        if trace_money and o0.step % 48 == 0:
            money.append((o0.step, round(env.state[0].observation.farms[0]['money']),
                          round(env.state[1].observation.farms[1]['money'])))
    rep0 = rep1 = None
    for f in ('REPORT',):
        if f in ns0:
            try: rep0 = ns0[f]()
            except Exception: pass
        if f in ns1:
            try: rep1 = ns1[f]()
            except Exception: pass
    return [env.state[0].reward, env.state[1].reward], money, rep0, rep1

def matrix(agent_path, seeds=None, opps=None, seats=(0, 1), trace=False):
    seeds = seeds or SEEDS
    opps = opps or OPPS
    total = 0
    rows = []
    for oname, opath in opps.items():
        for seed in seeds:
            for seat in seats:
                nsA = load(agent_path, 'newA')
                nsO = load(opath, 'opp')
                if seat == 0:
                    (r, money, repA, _) = play(nsA, nsO, seed, trace_money=trace)
                    margin = r[0] - r[1]
                else:
                    (r, money, _, repA) = play(nsO, nsA, seed, trace_money=trace)
                    margin = r[1] - r[0]
                total += margin
                rows.append((oname, seed, seat, r, margin))
                print('%s seed=%d seat=%d rewards=%s margin=%+.0f' % (oname, seed, seat, [round(x) for x in r], margin), flush=True)
                if trace and money:
                    print('   money trace:', money, flush=True)
    print('TOTAL=%+.0f over %d games' % (total, len(rows)), flush=True)
    try:
        print('telemetry:', repA, flush=True)
    except Exception:
        pass
    return total, rows

if __name__ == '__main__':
    ap = sys.argv[1] if len(sys.argv) > 1 else R + '../new_agent/agent.py'
    trace = len(sys.argv) > 2 and sys.argv[2] == 'trace'
    matrix(ap, trace=trace)
