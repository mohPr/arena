"""Chain analysis: action runs, 0-move chains, op bigrams per unit-day."""
import json, sys
from collections import Counter, defaultdict

MOVES = {'NORTH','SOUTH','EAST','WEST'}

import os as _o; sys.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
from tour_mine import load, unit_traj

def main():
    path, side = sys.argv[1], int(sys.argv[2])
    lo, hi = map(int, sys.argv[3].split('-')) if len(sys.argv) > 3 else (0, 719)
    d = load(path)
    traj = unit_traj(d['steps'], side, lo, hi)
    bigrams = Counter()
    runlen = Counter()   # run length -> count
    runmv = defaultdict(list)  # run length -> list of moves inside run (should be 0 for pure chains)
    chain_pos_same = 0
    chain_total = 0
    mv_since_act = defaultdict(list)  # op -> [moves since unit's last action]
    for u, seq in traj.items():
        # per unit-day split
        byday = defaultdict(list)
        for rec in seq:
            byday[rec[0] // 24].append(rec)
        for day, recs in byday.items():
            # runs of consecutive non-move non-PASS
            run = []
            for t, b, op, a in recs:
                if op in MOVES or op == 'PASS':
                    if run:
                        runlen[len(run)] += 1
                        run = []
                else:
                    run.append((t, b, op, a))
            if run:
                runlen[len(run)] += 1
            # bigrams + moves-since-last-action
            last_act_i = None
            mv = 0
            for i, (t, b, op, a) in enumerate(recs):
                if op in MOVES:
                    mv += 1
                elif op == 'PASS':
                    pass
                else:
                    mv_since_act[op].append(mv)
                    mv = 0
                    if last_act_i is not None:
                        _, _, pop, _ = recs[last_act_i]
                        bigrams[(pop, op)] += 1
                        # consecutive steps, same before-pos?
                        pt, pb, _, pa = recs[last_act_i]
                        if t == pt + 1 and b == pa:
                            chain_total += 1
                            if a == b:
                                chain_pos_same += 1
                    last_act_i = i
    print('RUN LENGTHS (consecutive non-move actions):')
    for L in sorted(runlen):
        print(f'  len {L}: {runlen[L]}')
    print(f'SAME-POS CHAINS: {chain_pos_same}/{chain_total} consecutive actions with zero walk between at same tile')
    print('TOP BIGRAMS:')
    for (a, b), c in bigrams.most_common(20):
        print(f'  {a}->{b}: {c}')
    print('MOVES-SINCE-LAST-ACTION per op (mean):')
    for op, vs in sorted(mv_since_act.items()):
        print(f'  {op}: n={len(vs)} mean={sum(vs)/len(vs):.2f}')

if __name__ == '__main__':
    main()
