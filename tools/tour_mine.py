"""Mine per-unit tours from a DSM replay. Usage: tour_mine.py <json> <side> [day_lo-day_hi]"""
import json, sys
from collections import defaultdict, Counter

MOVES = {'NORTH','SOUTH','EAST','WEST'}
ANIMAL_OPS = {'FEED','CARE','COLLECT_FERTILIZER','PLACE','BUILD_PASTURE','BUILD_COOP'}
CROP_OPS = {'PLANT','WATER','HARVEST','DIG','FERTILIZE','PICKUP'}

def load(path):
    d = json.load(open(path))
    return d

def unit_traj(steps, side, t_lo, t_hi):
    """per unit: list of (t, pos_before, op, pos_after). farmer key='F', hands by index."""
    traj = defaultdict(list)
    prev = None  # (farmer_pos, hands_list)
    for t in range(t_lo, t_hi + 1):
        e = steps[t][side]
        obs = e['observation']['farms'][side]
        fpos = tuple(obs['farmer'])
        hpos = [tuple(h) for h in obs['hands']]
        act = e['action']
        if prev is not None:
            pf, ph = prev
            traj['F'].append((t, pf, act['farmer'][0], fpos))
            ha_list = act['hands']
            n = max(len(ha_list), len(hpos))
            for i in range(n):
                if i < len(ha_list) and i < len(hpos):
                    traj[i].append((t, ph[i] if i < len(ph) else hpos[i], ha_list[i][0], hpos[i]))
                elif i < len(hpos):
                    pass  # hired this step, no action yet
                else:
                    # dawn step: yesterday's hand acts then vanishes
                    traj[i].append((t, ph[i], ha_list[i][0], None))
        prev = (fpos, hpos)
    return traj

def main():
    path, side = sys.argv[1], int(sys.argv[2])
    d = load(path)
    steps = d['steps']
    print('teams', d['info']['TeamNames'], 'rewards', d['rewards'])
    if len(sys.argv) > 3:
        lo, hi = map(int, sys.argv[3].split('-'))
    else:
        lo, hi = 0, 719
    traj = unit_traj(steps, side, lo, hi)
    # per unit-day: counts
    perday = defaultdict(Counter)
    for u, seq in traj.items():
        for t, b, op, a in seq:
            day = t // 24
            perday[(day, u)][op] += 1
            perday[(day, u)]['MV'] += 1 if op in MOVES else 0
            perday[(day, u)]['ACT'] += 0 if op in MOVES or op == 'PASS' else 1
    days = sorted(set(k[0] for k in perday))
    for day in days:
        print(f'--- day {day} ---')
        for (d_, u), c in sorted(perday.items(), key=lambda kv: (kv[0][0], str(kv[0][1]))):
            if d_ != day: continue
            tot = sum(v for k, v in c.items() if k not in ('MV','ACT'))
            print(f'  u={u} steps={tot} acts={c["ACT"]} mv={c["MV"]} ' +
                  ' '.join(f'{k}{v}' for k, v in sorted(c.items()) if k not in ('MV','ACT') and v))

if __name__ == '__main__':
    main()
