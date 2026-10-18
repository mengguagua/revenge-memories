#!/usr/bin/env python3
"""Import the completed 2026-10-18 art review snapshot without changing rules/saves."""
import hashlib
import argparse
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


def map_preview_metadata(art, profile):
    """Keep the reviewed ground projection separate from the character atlas."""
    if profile.get('mapShadow'):
        shadow = dict(profile['mapShadow'])
        target = OUT / ('hunapu-story-ground-shadow.png' if profile['id'] in ['hunapu-maps-story', 'hunapu-maps-world'] else 'hunapu-ground-shadow.png')
        shutil.copy2(REVIEW / shadow['path'], target)
        shadow['path'] = resource(target)
        art['ground_shadow'] = shadow
    if profile.get('revision'):
        art['art_revision'] = profile['revision']


def import_hunapu_maps():
    """Update only the four approved male map profiles in the existing test pack."""
    gallery = read(REVIEW / 'demos/gallery-data.json')
    runtime_path = GAME / 'data/reviewed_animations.json'
    data = read(runtime_path)
    original_other = {key: value for key, value in data.items() if key not in ['maps', 'map_revisions']}
    original_other_maps = {key: value for key, value in data['maps'].items() if key != '21_ally'}
    inventory = []
    for context in ['story', 'world', 'tactical-walk', 'tactical-idle']:
        pid = 'hunapu-maps-' + context
        profile = next(p for p in gallery['profiles'] if p['id'] == pid)
        assert profile['revision'] == 'hero-map-v3-side-arms' and not profile['frameErrors']
        scenario = next(s for s in read(REVIEW / profile['mapping'])['scenarios'] if s['id'] == context)
        art = data['maps']['21_ally'][context]
        assert art['frame_size'] == profile['outputFrameSize']
        assert art['anchor'] == profile['anchor'] and art['frames'] == profile['sourceFrameCount']
        # The review atlases already contain all source aliases in native order.
        source = (REVIEW / profile['mapping']).parent / scenario['output_atlas']
        target = GAME / art['path'].removeprefix('res://')
        shutil.copy2(source, target)
        packed = Image.open(target).convert('RGBA')
        w, h = art['frame_size']
        assert packed.size == (w * art['frames'], h)
        for slot, name in profile['newFrames'].items():
            expected = Image.open(REVIEW / name).convert('RGBA')
            index = int(slot)
            assert packed.crop((index*w, 0, (index+1)*w, h)).tobytes() == expected.tobytes()
        map_preview_metadata(art, profile)
        inventory.append({'context': context, 'path': art['path'], 'source_atlas': str(source.relative_to(REVIEW)),
            'size': list(packed.size), 'bytes': target.stat().st_size, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
            'all_frames_pixel_identical_to_review': True})
    story = GAME / data['maps']['21_ally']['story']['path'].removeprefix('res://')
    world = GAME / data['maps']['21_ally']['world']['path'].removeprefix('res://')
    assert story.read_bytes() == world.read_bytes()
    assert {key: value for key, value in data.items() if key not in ['maps', 'map_revisions']} == original_other
    assert {key: value for key, value in data['maps'].items() if key != '21_ally'} == original_other_maps
    data.setdefault('map_revisions', {})['hunapu'] = 'hero-map-v3-side-arms'
    runtime_path.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')))
    report = GAME / 'reports/hunapu-map-test-20261018'
    report.mkdir(parents=True, exist_ok=True)
    result = {'scope': 'Only Hunapu story/world/tactical-walk/tactical-idle and independent shadow',
        'source_review': 'map-motion-review-v3', 'inventory': inventory, 'story_world_identical': True,
        'battle_and_other_map_profiles_unchanged': True, 'gameplay_save_data_changed': False}
    (report / 'import.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))


def import_hunapu_story_shadow():
    """Use the approved compact projection in story and world maps."""
    gallery = read(REVIEW / 'demos/gallery-data.json')
    profile = next(p for p in gallery['profiles'] if p['id'] == 'hunapu-maps-story')
    runtime_path = GAME / 'data/reviewed_animations.json'
    data = read(runtime_path)
    map_preview_metadata(data['maps']['21_ally']['story'], profile)
    data['maps']['21_ally']['world']['ground_shadow'] = dict(data['maps']['21_ally']['story']['ground_shadow'])
    runtime_path.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')))
    print('Updated Hunapu story/world shadow; tactical shadows and all character atlases retained')


def import_reviewed_class_maps(class_id, label, revision=None, report_name=None):
    """Import one approved class's maps, retaining unrelated runtime art."""
    gallery = read(REVIEW / 'demos/gallery-data.json')
    runtime_path = GAME / 'data/reviewed_animations.json'
    before = read(runtime_path)
    data = read(runtime_path)
    report = GAME / ('reports/' + (report_name or label + '-map-test-20261018'))
    backup = report / 'before'
    backup.mkdir(parents=True, exist_ok=True)
    if not (backup / runtime_path.name).exists():
        shutil.copy2(runtime_path, backup / runtime_path.name)
    hashes_before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.rglob('*.png')}
    changed = set()
    inventory = []
    for side in ['ally', 'enemy']:
        key = class_id + '_' + side
        contexts = ['tactical-walk', 'tactical-idle'] + (['story'] if side == 'ally' else [])
        for context in contexts:
            pid = 'professions-class-' + class_id + '-' + side + '-maps-' + context
            profile = next(p for p in gallery['profiles'] if p['id'] == pid)
            expected_revision = revision or ('archer-down-hand-v4-20261018' if context == 'tactical-walk' else 'archer-arms-step-v3-20261018')
            assert profile['revision'] == expected_revision and not profile['frameErrors']
            mapping = REVIEW / profile['mapping']
            scenario = next(s for s in read(mapping)['scenarios'] if s['id'] == context)
            source = (mapping.parent / scenario['output_atlas']).resolve()
            source.relative_to(REVIEW)
            target = OUT / (pid + '.png')
            if target.exists() and not (backup / target.name).exists():
                shutil.copy2(target, backup / target.name)
            packed = Image.open(source).convert('RGBA')
            w, h = profile['outputFrameSize']
            count = profile['sourceFrameCount']
            assert packed.size == (w * count, h)
            assert len(profile['newFrames']) == count
            for slot, name in profile['newFrames'].items():
                expected = Image.open(REVIEW / name).convert('RGBA')
                index = int(slot)
                assert packed.crop((index*w, 0, (index+1)*w, h)).tobytes() == expected.tobytes()
            shutil.copy2(source, target)
            changed.add(target)
            art = {'path': resource(target), 'frame_size': [w, h], 'frames': count, 'columns': count,
                   'anchor': profile['anchor'], 'native_density': 4, 'reviewed_profile': pid,
                   'source_oam_frame_count': 0, 'oam_flip_origin_offset': [0, 0], 'original_motion': True,
                   'tile_origin': [profile['anchor'][0]-8, profile['anchor'][1]-16],
                   'directions': dict(scenario['directions']), 'default_facing': 'right',
                   'static_facing': bool(scenario.get('static_facing', False)), 'art_revision': expected_revision}
            if context == 'tactical-walk':
                art['directions']['side'] = art['directions']['right']
            else:
                art['directions'] = {direction: [0, 0] for direction in ['down', 'up', 'side', 'left', 'right']}
            if context == 'tactical-idle':
                art['native_cycle'] = scenario['timing']['cycle_frames']
                art['cycle_ticks'] = scenario['timing']['frame_ticks']
            # Each class owns its shadow file, preserving previously accepted art.
            shadow = dict(profile['mapShadow'])
            shadow_target = OUT / (label + '-ground-shadow.png')
            shutil.copy2(REVIEW / shadow['path'], shadow_target)
            changed.add(shadow_target)
            shadow['path'] = resource(shadow_target)
            art['ground_shadow'] = shadow
            data['maps'][key][context] = art
            inventory.append({'profile': pid, 'path': resource(target), 'source_atlas': str(source.relative_to(REVIEW)),
                              'size': list(packed.size), 'bytes': target.stat().st_size,
                              'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                              'all_frames_pixel_identical_to_review': True})
    data.setdefault('map_revisions', {})[label] = revision or 'archer-down-hand-v4-20261018'
    assert {k: v for k, v in before.items() if k not in ['maps', 'map_revisions']} == {k: v for k, v in data.items() if k not in ['maps', 'map_revisions']}
    selected_keys = [class_id + '_ally', class_id + '_enemy']
    assert {k: v for k, v in before['maps'].items() if k not in selected_keys} == {k: v for k, v in data['maps'].items() if k not in selected_keys}
    assert all(hashlib.sha256(p.read_bytes()).hexdigest() == digest for p, digest in hashes_before.items() if p not in changed)
    runtime_path.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')))
    shadow_image = Image.open(shadow_target)
    result = {'scope': 'Both ' + label + ' tactical idle/walk; friendly story static pose; separate ground shadow',
              'inventory': inventory, 'shadow': {'path': resource(shadow_target), 'size': list(shadow_image.size), 'bytes': shadow_target.stat().st_size},
              'other_maps_and_battle_data_unchanged': True, 'unrelated_asset_hashes_unchanged': True,
              'rules_and_save_data_modified': False}
    (report / 'import.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))


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
            map_preview_metadata(art, profile)
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
    parser = argparse.ArgumentParser()
    parser.add_argument('--hunapu-maps-only', action='store_true')
    parser.add_argument('--hunapu-story-shadow-only', action='store_true')
    parser.add_argument('--archer-maps-only', action='store_true')
    parser.add_argument('--spearman-maps-only', action='store_true')
    parser.add_argument('--body-volume-maps-only', action='store_true')
    args = parser.parse_args()
    if args.body_volume_maps_only:
        for cid, label in [('12', 'archer'), ('6', 'spearman')]:
            import_reviewed_class_maps(cid, label, 'body-volume-motion-20261018', 'body-volume-map-test-20261018/' + label)
    elif args.spearman_maps_only:
        import_reviewed_class_maps('6', 'spearman', 'spearman-stance-v3-20261018')
    elif args.archer_maps_only:
        import_reviewed_class_maps('12', 'archer')
    elif args.hunapu_story_shadow_only:
        import_hunapu_story_shadow()
    else:
        import_hunapu_maps() if args.hunapu_maps_only else build()
