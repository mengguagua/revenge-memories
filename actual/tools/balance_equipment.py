#!/usr/bin/env python3
"""Idempotently apply the campaign equipment schedule after any map rebuild."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def main():
    schedule = json.loads((ROOT / 'data/equipment_progression.json').read_text())
    path = ROOT / 'data/campaign.json'
    campaign = json.loads(path.read_text())
    for key, item in schedule['starter_items'].items():
        campaign['characters'][key]['item_id'] = item
    campaign['equipment_progression'] = 'res://data/equipment_progression.json'
    write(path, campaign)
    for path in sorted((ROOT / 'data/stages').glob('*.json')):
        stage = json.loads(path.read_text())
        for key, unit in stage['characters'].items():
            if key in schedule['starter_items']:
                unit['item_id'] = schedule['starter_items'][key]
        for unit in stage['npc_units']:
            if unit['id'] in schedule['starter_items']:
                unit['item_id'] = schedule['starter_items'][unit['id']]
        loadouts = schedule['enemy_loadouts'][stage['code']]
        for unit in stage['enemies'] + stage['reinforcements']:
            # Remove the previous schedule first; applying this file is idempotent.
            unit['item_id'] = 0
            unit.pop('drop_chance', None)
            if unit['id'] in loadouts:
                unit['item_id'], unit['drop_chance'] = loadouts[unit['id']]
        for obj in stage['objects']:
            if obj['id'] in schedule['visit_rewards']:
                obj['reward_item'] = schedule['visit_rewards'][obj['id']]
        stage['equipment_revision'] = schedule['revision']
        write(path, stage)
    print('Applied equipment schedule ' + schedule['revision'])


if __name__ == '__main__':
    main()
