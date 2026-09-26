"""Observation-only movement trace. The original agent's actions are unchanged.

Usage: LINE_FORCE=pinned python3 tools/motion_trace.py agent_current.py 200001
"""
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import harness
from fast_kaggr_env import FastKaggrEnvPy as Env

path = sys.argv[1]
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 200001
ns = harness.load(path, "TRACE_AGENT")
env = Env({"seed": seed, "episodeSteps": 720})
env.reset(2)
dummy = {"farmer": ["PASS"], "hands": [], "market": []}
totals = Counter()
daily = Counter()
last_day = -1
last_commands = {}
destinations = Counter()
directions = {"NORTH", "SOUTH", "EAST", "WEST"}
reverse = {"NORTH": "SOUTH", "SOUTH": "NORTH", "EAST": "WEST", "WEST": "EAST"}
shed_tiles = set(tuple(tile) for tile in ns.get("SHED_TILES", [(4, 4), (5, 4), (4, 5), (5, 5)]))
trace_supported = hasattr(ns.get("STIG"), "walk_to")

if trace_supported:
    original_walk = ns["STIG"].walk_to

    def traced_walk(dirs, index, pos, target):
        destinations[tuple(target)] += 1
        return original_walk(dirs, index, pos, target)

    ns["STIG"].walk_to = traced_walk

while not env.done:
    observation = env.state[0].observation
    if observation.day != last_day:
        if last_day >= 0:
            print("TRACE d%02d %s" % (last_day, json.dumps(dict(daily), sort_keys=True)), flush=True)
        last_day = observation.day
        daily.clear()
        last_commands.clear()
    destinations.clear()
    # Copy kinds before step: the engine can mutate observations in place.
    before = {
        (x, y): tile.get("kind") if isinstance(tile, dict) else tile
        for y, row in enumerate(observation.farms[0]["tiles"])
        for x, tile in enumerate(row)
    }
    action = ns["agent"](observation, None)
    commands = [action.get("farmer")] + list(action.get("hands") or [])
    for index, command in enumerate(commands):
        if not isinstance(command, list) or not command:
            continue
        verb = command[0]
        key = "MOVE" if verb in directions else verb
        daily[key] += 1
        totals[key] += 1
        if verb in directions and last_commands.get(index) == reverse[verb]:
            daily["immediate_reversals"] += 1
            totals["immediate_reversals"] += 1
        last_commands[index] = verb
    duplicates = sum(max(0, count - 1) for count in destinations.values())
    daily["duplicate_walk_to_intents"] += duplicates
    totals["duplicate_walk_to_intents"] += duplicates
    totals["walk_to_calls"] += sum(destinations.values())
    for target, count in destinations.items():
        key = "shared_shed_intents" if target in shed_tiles else "duplicate_field_intents"
        daily[key] += max(0, count - 1)
        totals[key] += max(0, count - 1)
    env.step([action, dict(dummy)])
    for y, row in enumerate(env.state[0].observation.farms[0]["tiles"]):
        for x, tile in enumerate(row):
            if not isinstance(tile, dict) or tile.get("kind") != "WEED":
                continue
            previous = before[(x, y)]
            if previous == "WEED":
                continue
            # Count transitions only, never a standing weed again the next day.
            key = "new_weeds_from_plant" if previous == "PLANT" else "new_weeds_from_empty" if previous is None else "new_weeds_other"
            daily[key] += 1
            totals[key] += 1

print("TRACE d%02d %s" % (last_day, json.dumps(dict(daily), sort_keys=True)))
print("TRACE_JSON " + json.dumps({"seed": seed, "reward": env.state[0].reward, "counts": dict(totals), "walk_to_hook": trace_supported}))
print("TRACE NOTE: walk_to intents cover that helper only. Verbs count issued actions, not confirmed successful work.")
print("TRACE NOTE: shared shed destinations are not classified as waste. Plant-to-weed transitions can include expiry as well as thirst.")