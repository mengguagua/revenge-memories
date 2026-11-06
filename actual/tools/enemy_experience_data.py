# -*- coding: utf-8 -*-
"""Use the same approved table as the runtime; no per-chapter XP constants."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES = json.loads((ROOT / 'data/enemy_experience_20261104.json').read_text())


def enemy_value(stage_id, unit):
    if unit.get('training_opponent'):
        return 0
    boss = RULES['bosses'].get(str(stage_id), {})
    if boss and unit['id'] == boss['unit_id']:
        base = int(boss['base'])
    else:
        base = int(RULES['class_bases'][str(unit['class_id'])]['base'])
    return min(255, base + base * (max(1, int(unit['level'])) - 1) // 10)


def apply_stage_experience(stage):
    if not isinstance(stage, dict) or not {'id', 'code', 'enemies'} <= stage.keys() or stage.get('training'):
        return stage
    actors = stage.get('enemies', []) + stage.get('reinforcements', [])
    if isinstance(stage.get('summon_template'), dict):
        actors.append(stage['summon_template'])
    for unit in actors:
        if unit.get('side', 'enemy') == 'enemy':
            unit['exp_value'] = enemy_value(stage['id'], unit)
    return stage
