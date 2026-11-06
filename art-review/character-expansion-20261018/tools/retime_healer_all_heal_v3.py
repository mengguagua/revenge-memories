#!/usr/bin/env python3
"""Shorten the all-heal ring hold; keep native actors and resolution untouched."""
import copy
import json
from build_gallery import ROOT

REV = 'healer-all-heal-flow-v3-20261023'
OUT = ROOT / REV
PREVIOUS = ROOT / 'healer-support-vfx-v2-20261023'


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    data = json.loads((ROOT / 'demos/gallery-data.json').read_text())
    selected = [a for a in data['actions'] if a['profile'] in
                ['professions-class-17-ally-battle', 'professions-class-18-ally-battle']
                and a['key'].split('_item_')[-1].split('_')[0] == '44']
    assert len(selected) == 12
    old_contracts = {c['key']: c for c in json.loads(
        (PREVIOUS / 'spell-contracts.json').read_text())['actions']}
    mappings = {f'professions/class-{c}-ally/battle/frame_mapping.json':
                json.loads((ROOT / f'professions/class-{c}-ally/battle/frame_mapping.json').read_text())
                for c in [17, 18]}
    # Keep an immutable, narrowly scoped comparison record before publishing.
    assert not (OUT / 'baseline.json').exists(), 'This revision is already published'
    prior = json.loads((PREVIOUS / 'baseline.json').read_text())
    write(OUT / 'baseline.json', {
        'actions': selected, 'digests': {a['id']: a['contentDigest'] for a in data['actions']},
        'effects': data['effects'], 'mappings': mappings,
        'body_map_hashes': prior['body_map_hashes']})
    contracts = []
    for path, mapping in mappings.items():
        timeline = json.loads((ROOT / path).parent.joinpath(mapping['review_timeline']).resolve().read_text())
        timeline['revision'] = REV
        for action in selected:
            if action['profile'] != f"professions-class-{mapping['original_class_id']}-ally-battle":
                continue
            key = action['key']
            previous = old_contracts[key]
            old_rows = action['revisedFrames'] + action.get('reviewTailFrames', [])
            contact = action['contactTick']
            last_native_effect = max(t for t, row in enumerate(action['frames']) if row['effects'])
            rain_start, pool_start, pool_end = contact - 54, contact, contact + 60
            assert rain_start - last_native_effect - 1 == 13
            count = len(action['frames'])
            rows = copy.deepcopy(action['frames'])
            for _ in range(max(0, pool_end - count)):
                rows.append(copy.deepcopy(action['frames'][-1]))
            for tick, row in enumerate(rows):
                if tick < rain_start:
                    row['effects'] = copy.deepcopy(old_rows[tick]['effects'])
                elif tick < pool_start:
                    row['effects'] = copy.deepcopy(old_rows[previous['rain_start'] + tick - rain_start]['effects'])
                elif tick < pool_end:
                    row['effects'] = copy.deepcopy(old_rows[previous['pool_start'] + tick - pool_start]['effects'])
                else:
                    row['effects'] = []
            contract = {**previous, 'last_native_effect_tick': last_native_effect,
                        'previous_static_hold_ticks': previous['rain_start'] - last_native_effect - 1,
                        'static_hold_ticks': 13, 'rain_start': rain_start, 'rain_end': pool_start,
                        'pool_start': pool_start, 'pool_end': pool_end,
                        'pool_ticks': 60, 'review_tail_ticks': len(rows) - count,
                        'display_ticks': len(rows), 'pool_begins_on_native_contact': True}
            revised = copy.deepcopy(timeline['actions'][key])
            revised.update(frames=rows[:count], events=contract,
                           note='全体恢复：光环展开后的静止停留由75帧缩到13帧，随即化为54帧绿色雨滴；泉水汇聚从原恢复结算时刻开始，保留60帧水花与波纹。人物原动作、结算与效果位置保持。')
            revised.pop('tail_frames', None)
            revised.pop('tail_label', None)
            if len(rows) > count:
                revised.update(tail_frames=rows[count:], tail_label='泉水波纹收尾')
            timeline['actions'][key] = revised
            contracts.append(contract)
        class_id = mapping['original_class_id']
        write(OUT / f'class-{class_id}-motion.json', timeline)
        mapping.update(revision=REV, review_timeline=f'../../../{REV}/class-{class_id}-motion.json',
                       qa_report=f'../../../{REV}/verification.json',
                       review_note='全体恢复节奏优化：静止光环75帧缩为13帧，提前衔接绿色雨滴，原结算时刻开始汇成泉水。其它法术沿用已完成修订。')
        write(ROOT / path, mapping)
    assert len(contracts) == 12
    write(OUT / 'spell-contracts.json', {'revision': REV, 'actions': contracts,
          'mechanics_changed': False, 'runtime_integrated': False, 'new_images': 0})
    exporter = ROOT / 'tools/export_gallery.py'
    text = exporter.read_text()
    text = text.replace("'healer-support-vfx-v2-20261023'", "'healer-support-vfx-v2-20261023','" + REV + "'")
    exporter.write_text(text)
    print(json.dumps({'revision': REV, 'actions': len(contracts), 'hold_ticks': [75, 13]}), flush=True)


if __name__ == '__main__':
    main()
