#!/usr/bin/env python3
"""Refresh isolated production counts from audited original references."""
from pathlib import Path
import hashlib
import json
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'catalog/production-units.json'
plan = json.loads(path.read_text())
ally = json.loads((ROOT / 'source-input/original-motion/full-original-motion.json').read_text())
enemy = json.loads((ROOT / 'source-input/enemy-motion/full-enemy-motion.json').read_text())
overlay_path = ROOT / 'source-input/corrected-ally-motion/overlay.json'
if overlay_path.exists():
    overlay = json.loads(overlay_path.read_text())
    ally['variants'].update(overlay['variants'])
excluded = {v['key'] for v in enemy.get('excluded_variants', [])}
excluded.update(key for key in ally['variants'] if key.startswith('class_6_ally_javelin'))
for unit in plan['units']:
    data = ally if unit['side'] == 'ally' else enemy
    meta = data['original_bodies'][str(unit['source_class_id'])]
    removed = [key for key in unit['bound_action_keys'] if key in excluded]
    unit['bound_action_keys'] = [key for key in unit['bound_action_keys'] if key not in excluded]
    if removed:
        unit['excluded_reference_actions'] = sorted(set(unit.get('excluded_reference_actions', [])) | set(removed))
        unit['exclusion_reason'] = 'Current can_use rules exclude class6 thrown javelins; not a required action or newly granted ability.'
    keys = unit['bound_action_keys']
    missing = [key for key in keys if key not in data['variants']]
    assert not missing, (unit['id'], missing)
    used = sorted({row['frame'] for key in keys for row in data['variants'][key]['frames']} | set(meta['sequences']['idle']))
    atlas = ROOT / unit['source_atlas']
    im = Image.open(atlas).convert('RGBA')
    w, h = meta['frame_size']
    cols = meta.get('columns', 16)
    canonical = {}
    aliases = {}
    for index in used:
        frame = im.crop(((index % cols)*w, (index//cols)*h, (index % cols + 1)*w, (index//cols + 1)*h))
        key = hashlib.sha256(frame.tobytes()).hexdigest()
        canonical.setdefault(key, index)
        aliases[str(index)] = canonical[key]
    unit.update(required_source_frames=used, exact_pixel_aliases=aliases,
                unique_art_frames=sorted(set(aliases.values())), reference_status='native_selector_audited')
plan['exact_distinct_pose_count_by_unit'] = sum(len(u['unique_art_frames']) for u in plan['units'])
plan['required_pose_count_by_unit'] = sum(len(u['unique_art_frames']) for u in plan['units'] if u['required_for_game_scope'])
plan['count_note'] = 'Counts include each profession entry separately; Hunapu class21/23 share approved drawings where source geometry is identical. No palette-only reskins are counted as independent designs.'
path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k:plan[k] for k in ['required_unit_count','reference_only_unit_count','required_pose_count_by_unit']},ensure_ascii=False))
