#!/usr/bin/env python3
"""Import the completed 2026-10-18 art review snapshot without changing rules/saves."""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from PIL import Image

GAME = Path(__file__).resolve().parents[1]
REVIEW = GAME.parent / 'art-review/character-expansion-20261018'
OUT = GAME / 'assets/reviewed-animation-20261018'
REPORT = GAME / 'reports/animation-test-20261018'


def read(path):
    return json.loads(path.read_text())


def resource(path):
    return 'res://' + path.relative_to(GAME).as_posix()


def build():
    gallery = read(REVIEW / 'demos/gallery-data.json')
    ally = read(REVIEW / 'source-input/original-motion/full-original-motion.json')
    ally['variants'].update(read(REVIEW / 'source-input/corrected-ally-motion/overlay.json')['variants'])
    enemy = read(REVIEW / 'source-input/enemy-motion/full-enemy-motion.json')
    data = {'revision': '20261018-sol', 'battle': {}, 'maps': {}, 'variants': {}, 'sprites': {}}
    inventory = []
    for profile in gallery['profiles']:
        assert not profile.get('frameErrors') and not profile.get('sourceReviewPending'), profile['id']
        pid = profile['id']
        frame_size = profile['outputFrameSize']
        frame_count = profile['sourceFrameCount']
        columns = min(16, frame_count)
        atlas = Image.new('RGBA', (columns * frame_size[0], ((frame_count + columns - 1) // columns) * frame_size[1]))
        frame_hashes = {}
        for index, name in profile['newFrames'].items():
            path = (REVIEW / name).resolve()
            path.relative_to(REVIEW)
            image = Image.open(path).convert('RGBA')
            assert list(image.size) == frame_size
            index = int(index)
            atlas.paste(image, (index % columns * frame_size[0], index // columns * frame_size[1]))
            frame_hashes[str(index)] = hashlib.sha256(image.tobytes()).hexdigest()
        target = OUT / (pid + '.png')
        target.parent.mkdir(parents=True, exist_ok=True)
        atlas.save(target, optimize=True)
        subprocess.run(['/opt/homebrew/bin/oxipng', '-q', '-o', '3', str(target)], check=True)
        # Lossless packing check, including transparency and repeated source aliases.
        packed = Image.open(target).convert('RGBA')
        for index, expected in frame_hashes.items():
            index = int(index)
            x, y = index % columns * frame_size[0], index // columns * frame_size[1]
            assert hashlib.sha256(packed.crop((x, y, x + frame_size[0], y + frame_size[1])).tobytes()).hexdigest() == expected
        art = {'path': resource(target), 'frame_size': frame_size, 'frames': frame_count, 'columns': columns,
               'anchor': profile['anchor'], 'native_density': 4, 'reviewed_profile': pid,
               'source_oam_frame_count': profile['sourceOamCutoff'], 'oam_flip_origin_offset': profile['flipOriginOffset'],
               'original_motion': True}
        key = profile['classId'] + '_' + profile['side']
        if profile['context'] == 'battle':
            actions = [a for a in gallery['actions'] if a['profile'] == pid and a['kind'] == 'attack']
            assert actions and all(a['ready'] for a in actions)
            art['reviewed_variants'] = {}
            source = enemy if profile['side'] == 'enemy' else ally
            for action in actions:
                variant = source['variants'][action['key']]
                assert variant['contact_tick'] == action['contactTick']
                assert len(variant['frames']) == len(action['frames'])
                assert all(str(int(f['frame'])) in frame_hashes for f in variant['frames'])
                runtime_key = 'reviewed/' + pid + '/' + action['key']
                data['variants'][runtime_key] = variant
                art['reviewed_variants'][action['key']] = runtime_key
            idle = next(a for a in gallery['actions'] if a['profile'] == pid and a['key'] == 'idle')
            art['sequences'] = {'idle': [idle['frames'][0]['frame']]}
            art['reviewed_class_id'] = int(profile['classId'])
            art['reviewed_side'] = profile['side']
            data['battle'][key] = art
        else:
            mapping = read(REVIEW / profile['mapping'])
            scenario = next(s for s in mapping['scenarios'] if s['id'] == profile['context'])
            art['tile_origin'] = [profile['anchor'][0] - 8, profile['anchor'][1] - 16]
            art['directions'] = dict(scenario['directions'])
            if 'right' in art['directions']:
                art['directions']['side'] = art['directions']['right']
            art['default_facing'] = 'right'
            art['static_facing'] = bool(scenario.get('static_facing', False))
            if profile['context'] == 'tactical-idle':
                art['native_cycle'] = scenario['timing']['cycle_frames']
                art['cycle_ticks'] = scenario['timing']['frame_ticks']
                art['directions'] = {'down': [0, 0], 'up': [0, 0], 'side': [0, 0]}
            data['maps'].setdefault(key, {})[profile['context']] = art
        inventory.append({'profile': pid, 'context': profile['context'], 'path': resource(target),
                          'size': list(packed.size), 'bytes': target.stat().st_size,
                          'source_slots': len(frame_hashes), 'lossless_pixel_check': True,
                          'size_note': 'Losslessly packed animation atlas; individual selected drawings retain their original pixels.'})
    effect_ids = {effect['sprite'] for variant in data['variants'].values()
                  for frame in variant['frames'] for effect in frame.get('effects', [])}
    for effect_id in sorted(effect_ids):
        effect = dict(gallery['effects'][effect_id])
        target = OUT / 'effects' / (effect_id + '.png')
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REVIEW / effect['path'], target)
        effect['path'] = resource(target)
        data['sprites'][effect_id] = effect
    (GAME / 'data/reviewed_animations.json').write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')))
    REPORT.mkdir(parents=True, exist_ok=True)
    report = {'revision': data['revision'], 'battle_profiles': len(data['battle']), 'map_profiles': len(inventory) - len(data['battle']),
              'attack_variants': len(data['variants']), 'effect_textures': len(effect_ids), 'inventory': inventory,
              'scope': '20 completed class/faction bodies; Hunapu story/world; completed native tactical walk and idle. Unfinished professions and story identities keep existing art.',
              'rules_and_save_data_modified': False, 'lossless_pixel_checks_passed': True}
    (REPORT / 'import.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != 'inventory'}, ensure_ascii=False))


if __name__ == '__main__':
    build()
