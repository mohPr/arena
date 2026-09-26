"""Water-capacity meter: per day, labor spent vs irrigation outcome.
Usage: python3 tools/water_meter.py [agent.py] [seed]
Per day: acts by verb, hands; EOD: plants, watered cover, dry, dry&cu>=1
(at-risk: one more dry day -> WEED), weeds. Answers: capacity or mistarget?
"""
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from collections import Counter
from fast_kaggr_env import FastKaggrEnvPy as Env
import harness

AGENT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(HERE) + '/agent_current.py'
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 200001
ns = harness.load(AGENT, 'A')
env = Env({'seed': SEED, 'episodeSteps': 720})
env.reset(2)
D = {'farmer': ['PASS'], 'hands': [], 'market': []}
perday = {}
while not env.done:
    o = env.state[0].observation
    day = o.day
    if day > 29:
        break
    c = perday.setdefault(day, Counter())
    try:
        r = ns['agent'](o, None)
    except Exception:
        r = dict(D)
    for u in [r.get('farmer')] + list(r.get('hands') or []):
        if isinstance(u, list) and u:
            v = u[0]
            c['MOVE' if v in ('NORTH', 'SOUTH', 'EAST', 'WEST') else v] += 1
    c['hands'] = max(c.get('hands', 0), len(list(r.get('hands') or [])) + 1)
    if o.hour == 23:
        f = o.farms[0]
        plants = dry = risk = weeds = 0
        for row in f['tiles']:
            for t in (row or []):
                if not isinstance(t, dict):
                    continue
                if t.get('kind') == 'WEED':
                    weeds += 1
                elif t.get('kind') == 'PLANT':
                    plants += 1
                    if not t.get('watered_today'):
                        dry += 1
                        if int(t.get('consecutive_unwatered', 0) or 0) >= 1:
                            risk += 1
        c['eod_plants'] = plants
        c['eod_dry'] = dry
        c['eod_risk'] = risk
        c['eod_weeds'] = weeds
        try:
            shed = dict(f.get('shed') or {})
        except Exception:
            shed = {}
        c['eod_shed'] = {k: int(v or 0) for k, v in shed.items() if int(v or 0) > 0}
    env.step([r, dict(D)])
SHOW = ('WATER', 'HARVEST', 'PLANT', 'FEED', 'DIG', 'FERTILIZE', 'CARE',
        'COLLECT_FERTILIZER', 'VISIT', 'BUILD_PASTURE', 'BUILD_COOP', 'DROP',
        'PLACE', 'PICKUP')
print('acts/day by verb (hands | ... | MOVE PASS | plants dry risk weeds | shed top3)')
for d in sorted(perday):
    c = perday[d]
    acts = ' '.join(f'{v}={c.get(v,0)}' for v in SHOW)
    shed = c.get('eod_shed', {})
    top = ','.join(f'{k}:{v}' for k, v in sorted(shed.items(), key=lambda kv: -kv[1])[:3])
    print(f"d{d:>2} h={c.get('hands',0):>2} {acts} "
          f"MOVE={c.get('MOVE',0)} PASS={c.get('PASS',0)} | "
          f"pl={c.get('eod_plants','-')} dry={c.get('eod_dry','-')} "
          f"risk={c.get('eod_risk','-')} wd={c.get('eod_weeds','-')} | {top}")
print('rewards', [round(x) for x in (env.state[0].reward, env.state[1].reward)])
