"""Day-boundary state census: money/hands/herd/shed/seeds/plants per day.
Usage: python3 census_state.py <seed> <agent.py>   (agent plays seat 1 vs opp_pipe19)
Falsifier instrument: check herd/shedW/plants bands day by day."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 200001
AGENT = sys.argv[2] if len(sys.argv) > 2 else HERE + '/agent_current.py'
from fast_kaggr_env import FastKaggrEnvPy as Env
import harness
nsA = harness.load(AGENT, 'newA')
nsO = harness.load(HERE + '/opp_pipe19.py', 'opp')
a0, a1 = nsO['agent'], nsA['agent']
env = Env({'seed': SEED, 'episodeSteps': 720})
env.reset(2)
day = -1
lasthands = 1  # hands reset nightly: boundary snapshots see dawn (0 hands),
while not env.done:  # so print the previous day's last crew size instead
    o0, o1 = env.state[0].observation, env.state[1].observation
    try:
        r0 = a0(o0, None)
    except Exception:
        r0 = {'farmer': ['PASS'], 'hands': [], 'market': []}
    try:
        r1 = a1(o1, None)
    except Exception:
        r1 = {'farmer': ['PASS'], 'hands': [], 'market': []}
    dy = o1.day
    if dy != day:
        day = dy
        f1 = o1.farms[1]
        priv = o1.private if hasattr(o1, 'private') else {}
        try:
            shed = dict(priv.get('shed', {}))
        except Exception:
            shed = {}
        try:
            seeds = dict(priv.get('seeds', {}))
        except Exception:
            seeds = {}
        money = f1.get('money', 0)
        hands = lasthands
        nplants = nanimals = 0
        crops = {}
        for row in (f1.get('tiles', []) or []):
            for t in (row or []):
                if not isinstance(t, dict):
                    continue
                if t.get('kind') == 'PLANT':
                    nplants += 1
                    c = t.get('crop', '?')
                    crops[c] = crops.get(c, 0) + 1
                if t.get('animal') is not None:
                    nanimals += 1
        placed = nanimals + sum(int(shed.get(a, 0) or 0) for a in ('COW', 'SHEEP', 'GOOSE'))
        try:
            invs = priv.get('inventories', []) or []
            carried = sum(int((inv or {}).get(a, 0) or 0) for inv in invs for a in ('COW', 'SHEEP', 'GOOSE'))
        except Exception:
            carried = 0
        print(f"d{day:02d} ${money:7.0f} units={hands} herd={placed + carried}(pl={nanimals}) "
              f"shedW={shed.get('WHEAT')} shedF={shed.get('FERTILIZER')} seeds={seeds} plants={nplants} {crops}", flush=True)
    try:
        lasthands = len(o1.farms[1].get('hands', []) or []) + 1
    except Exception:
        pass
    env.step([r0, r1])
print('reward:', round(env.state[1].reward))
