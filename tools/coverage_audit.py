"""Worker-system audit: is every plant watered, every animal fed, zero weeds/escapes?
Usage: LINE_FORCE=pinned python3 tools/coverage_audit.py [agent.py] [seed]
Agent plays seat 0 vs PASS dummy (clean, no shared-RNG noise). End-of-day
(hour 23) snapshot per day + full-game verb counts. Exit 0 = ALL PASS.

Checks (the bar for a finished worker system):
  WEEDS   — max standing weeds any day must be 0 (2x unwatered = WEED = dead tile)
  ESCAPES — herd must never shrink (2x unfed = escape; we never sell animals)
  FEED    — animals unfed at end of day must be 0 every day
  WATER   — production tiles unwatered at end of day: reported per crop;
            FAIL if any day has >5% of production tiles dry
  USEFUL  — PASS + walk share of all unit steps (informational; target: PASS <5%)
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
verbs = Counter()
worst = {'weeds': 0, 'unfed': 0, 'dry': 0, 'dry_day': -1, 'escapes': 0}
prev_herd = None
dry_days = []
while not env.done:
    o = env.state[0].observation
    day = o.day
    if o.hour == 23 and 0 <= day <= 29:
        f = o.farms[0]
        weeds = unfed = dry = prod = 0
        herd = 0
        per_crop = Counter()
        per_dry = Counter()
        for row in f['tiles']:
            for t in (row or []):
                if not isinstance(t, dict):
                    continue
                if t.get('kind') == 'WEED':
                    weeds += 1
                elif t.get('kind') == 'PLANT':
                    prod += 1
                    per_crop[t.get('crop')] += 1
                    if not t.get('watered_today'):
                        dry += 1
                        per_dry[t.get('crop')] += 1
                if t.get('animal') is not None:
                    herd += 1
                    if not t.get('fed_today'):
                        unfed += 1
        if prev_herd is not None and herd < prev_herd:
            worst['escapes'] += prev_herd - herd
        prev_herd = herd
        worst['weeds'] = max(worst['weeds'], weeds)
        worst['unfed'] = max(worst['unfed'], unfed)
        if prod and dry / prod > 0.05:
            dry_days.append(day)
        if prod and (not worst['dry_day'] or dry / max(1, prod) >= worst['dry'] / 100):
            worst['dry'] = round(100 * dry / prod)
            worst['dry_day'] = day
        print(f"d{day:02d} weeds={weeds} unfed_eod={unfed} herd={herd} "
              f"dry={dry}/{prod} {dict(per_dry) or '{}'} money={f['money']:.0f}", flush=True)
    if day > 29:
        break
    try:
        r = ns['agent'](o, None)
    except Exception:
        r = dict(D)
    for u in [r.get('farmer')] + list(r.get('hands') or []):
        if isinstance(u, list) and u:
            verbs['MOVE' if u[0] in ('NORTH', 'SOUTH', 'EAST', 'WEST') else u[0]] += 1
    env.step([r, dict(D)])

tot = sum(verbs.values())
moves = verbs.get('MOVE', 0)
ps = verbs.get('PASS', 0)
print(f"STEPS total={tot} PASS={ps} ({100*ps/max(1,tot):.1f}%) "
      f"walk={moves} ({100*moves/max(1,tot):.1f}%)")
ok = True
for name, bad, want in (('WEEDS', worst['weeds'], 0), ('ESCAPES', worst['escapes'], 0),
                        ('FEED', worst['unfed'], 0)):
    s = 'PASS' if bad == want else 'FAIL'
    ok = ok and bad == want
    print(f"{name}: {s} (worst={bad}, want={want})")
s = 'PASS' if not dry_days else 'FAIL'
ok = ok and not dry_days
print(f"WATER: {s} (days>5% dry: {dry_days or 'none'}; worst day {worst['dry_day']}: {worst['dry']}% dry)")
print('AUDIT:', 'ALL PASS' if ok else 'FAILURES PRESENT')
sys.exit(0 if ok else 1)
