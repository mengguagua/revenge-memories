#!/usr/bin/env python3
"""Extract map 2, deployment, physical units and terrain from FE2 source.

Does not touch the localized opening or the first-battle data.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from extract_opening import Source, coordinates, tilemap


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, default=Path('/private/tmp/fe2-analysis-20261012'))
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / 'data/second_battle.json')
    args = parser.parse_args()
    src = Source(args.source)
    src.files[6] = (args.source / 'src/bank006.asm').read_text()
    first = json.loads((args.output.parent / 'first_battle.json').read_text())
    battlefield = tilemap(args.source, 'fleecers-forest.tmx')
    enemies_raw = src.db(8, 'L08947A')
    templates = re.findall(r'\.dw (\w+)', src.block(8, 'L089A5A'))
    stat_tables = re.findall(r'\.dw (\w+)', src.block(15, 'L0FED04'))
    move_values = src.db(15, 'L0FEDD3')
    positions = coordinates(src.db(8, 'L08AC00'), enemies_raw[0])
    enemies, counts = [], {}
    for index, template_index in enumerate(enemies_raw[1:1 + enemies_raw[0]]):
        template_label = templates[template_index]
        raw = src.db(8, template_label)
        class_id, level = raw[1:3]
        stats_label = stat_tables[class_id - 1]
        stats = src.db(15, stats_label)
        increase = (level - 1) // 2
        class_name = {12: 'archer', 14: 'brigand'}[class_id]
        counts[class_name] = counts.get(class_name, 0) + 1
        hp = min(52, stats[5] + increase * 3)
        enemies.append({
            'id': f'{class_name}_{counts[class_name]}',
            'name_ja': 'アーチャー' if class_id == 12 else 'さんぞく',
            'name_zh': '弓箭手' if class_id == 12 else '山贼',
            'class': class_name, 'class_id': class_id, 'level': level,
            'hp': hp, 'max_hp': hp, 'strength': stats[0] + increase,
            'skill': stats[1] + increase, 'speed': stats[2] + increase,
            'luck': stats[3], 'defence': stats[4] + increase,
            'move': move_values[class_id - 1], 'item_id': raw[3],
            'exp_value': min(255, stats[6] + stats[6] * (level - 1) // 10),
            'raw_ai_flags': raw[4], 'raw_magic_flags': raw[5],
            'position': positions[index], 'raw_template': raw,
            'provenance': [src.ref(8, 'L08947A'), src.ref(8, template_label),
                           src.ref(15, stats_label), src.ref(8, 'L08A31B'), src.ref(8, 'L08AC00')],
            'confidence': 'source_group_template_base_stats_and_enemy_constructor',
        })
    terrain_types = src.db(15, 'L0FE8DE')
    movement = src.db(15, 'L0FEADF')
    start = 0xEB0A - 0xEADF
    first.update({
        'id': 'fleecers_forest', 'map_id': 2, 'battle_number': 2,
        'name_ja': 'とうぞくのもり', 'name_zh': '盗贼森林',
        'map': battlefield,
        'player_positions': coordinates(src.db(8, 'L08ABEB')),
        'enemy_positions': positions, 'enemies': enemies,
        'provenance': [src.ref(2, 'L_TILEMAPS'), src.ref(8, 'L0892A1'),
                       src.ref(8, 'L0893C2'), src.ref(8, 'L08947A'),
                       src.ref(8, 'L08ABE3'), src.ref(8, 'L08ABEB'), src.ref(8, 'L08AC00')],
        'battle_identity': {'map_id': 2, 'enemy_group': 2,
                           'map_source': 'maps/fleecers-forest.tmx',
                           'confidence': 'source_route_map_lookup_and_deployment_tables'},
        'unverified': ['Exact RNG/frame synchronization', 'Full original AI priority and tie breaking',
                       'Original post-battle presentation timing'],
    })
    first.pop('first_battle_identity', None)
    first['terrain']['tile_categories'] = {str(tile): terrain_types[tile] for tile in sorted(set(battlefield['tiles']))}
    first['terrain']['movement_by_class_and_category'] = {
        str(cid): movement[start + (cid - 1) * 22:start + cid * 22] for cid in [6, 12, 14, 21]
    }
    first['rules']['attack_ranges'] = {'default_melee': [1, 1], 'default_bow': [1, 3]}
    first['rules']['range_provenance'] = [src.ref(6, 'L06ABFF'), src.ref(9, 'L09844A'), src.ref(9, 'L0984C7')]
    first['rules']['counter'] = 'Only within defender weapon range; a faster unit receives a follow-up only if it can strike.'
    first['rules']['experience']['unable_to_counter'] = '1 if the player survives the exchange; L0980CC no-hit branch'
    first['rules']['campaign'] = {
        'new_battle_healing': 'Fill current HP from maximum HP for surviving deployed characters',
        'growth_and_equipment': 'Preserve level, experience, stats and carried item',
        'dead_units': 'Do not redeploy',
        'provenance': [src.ref(6, 'L068BD5'), src.ref(6, 'L068C0C')],
    }
    assert (battlefield['width'], battlefield['height']) == (24, 22)
    assert counts == {'brigand': 6, 'archer': 1}
    assert [e['position'] for e in enemies] == [[14,3], [12,3], [16,3], [16,5], [9,9], [17,10], [12,11]]
    assert enemies[-1]['class_id'] == 12 and enemies[-1]['hp'] == 24
    args.output.write_text(json.dumps(first, ensure_ascii=False, indent=2) + '\n')
    print(f'Extracted {battlefield["width"]}x{battlefield["height"]}, {len(enemies)} enemies -> {args.output}')


if __name__ == '__main__':
    main()
