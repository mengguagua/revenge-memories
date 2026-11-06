# -*- coding: utf-8 -*-
"""Audit authored enemy V; --write refreshes only exp_value in the40 stages."""
import argparse
import copy
import json
from enemy_experience_data import ROOT, apply_stage_experience

parser = argparse.ArgumentParser()
parser.add_argument('--write', action='store_true')
args = parser.parse_args()
campaign = json.loads((ROOT / 'data/campaign.json').read_text())
changed = []
for metadata in campaign['stages'].values():
    path = ROOT / metadata['path'].removeprefix('res://')
    original = json.loads(path.read_text())
    updated = apply_stage_experience(copy.deepcopy(original))
    if updated != original:
        changed.append(updated['code'])
        if args.write:
            path.write_text(json.dumps(updated, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'stages':len(campaign['stages']), 'changed':changed, 'written':args.write}))
if changed and not args.write:
    raise SystemExit(1)
