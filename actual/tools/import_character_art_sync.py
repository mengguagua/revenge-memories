#!/usr/bin/env python3
"""Import the published character review snapshot without modifying combat rules."""
import copy
import gzip
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

from PIL import Image

GAME = Path(__file__).resolve().parents[1]
REVIEW = GAME.parent / 'art-review/character-expansion-20261018'
REV = 'character-art-sync-20261024'
OUT = GAME / 'assets' / REV
REPORT = GAME / 'reports' / REV


def read(path):
    return json.loads(path.read_text())


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')) + '\n')


def digest(value):
    return hashlib.sha256(value).hexdigest()


def pixels(image):
    return digest(image.convert('RGBA').tobytes())


def resource(path):
    return 'res://' + path.relative_to(GAME).as_posix()


def cycle(rows):
    """Keep one exact repeated period, then run-length encode its poses."""
    period = len(rows)
    for n in range(1, period + 1):
        if period % n == 0 and all(rows[i] == rows[i % n] for i in range(period)):
            period = n
            break
    frames, ticks = [], []
    for frame in rows[:period]:
        if frames and frames[-1] == frame:
            ticks[-1] += 1
        else:
            frames.append(frame)
            ticks.append(1)
    return {'frames': frames, 'ticks': ticks}


def profile_key(profile):
    pid = profile['id']
    if pid.startswith('eileen-promoted-'):
        return 'eileen_promoted'
    if pid.startswith('eileen-'):
        return 'eileen'
    if pid.startswith('hunapu-promoted-'):
        return '23_ally'
    return profile['classId'] + '_' + profile['side']


def main():
    REPORT.mkdir(parents=True, exist_ok=True)
    snapshot = REPORT / 'source-gallery.json.gz'
    if not snapshot.exists():
        with gzip.open(snapshot, 'wb') as f:
            f.write((REVIEW / 'demos/gallery-data.json').read_bytes())
    with gzip.open(snapshot, 'rt') as f:
        gallery = json.load(f)
    runtime_path = GAME / 'data/reviewed_animations.json'
    before_path = REPORT / 'before-reviewed-animations.json.gz'
    if not before_path.exists():
        with gzip.open(before_path, 'wb') as f:
            f.write(runtime_path.read_bytes())
    data = read(runtime_path)
    source = read(REVIEW / 'source-input/original-motion/full-original-motion.json')
    source['variants'].update(read(REVIEW / 'source-input/corrected-ally-motion/overlay.json')['variants'])
    native = {'ally': source['variants'], 'enemy': read(REVIEW / 'source-input/enemy-motion/full-enemy-motion.json')['variants']}
    actions = defaultdict(list)
    for action in gallery['actions']:
        assert action['ready'] and not action.get('sourceReviewPending'), action['id']
        actions[action['profile']].append(action)
    OUT.mkdir(parents=True, exist_ok=True)
    inventory, effect_inventory, action_inventory = [], {}, []
    image_cache = {}

    def image(path):
        if path not in image_cache:
            src = (REVIEW / path).resolve()
            src.relative_to(REVIEW)
            image_cache[path] = Image.open(src).convert('RGBA')
        return image_cache[path]

    def effect(eid, profile):
        meta = copy.deepcopy(profile.get('revisedEffects', {}).get(eid, gallery['effects'][eid]))
        identity = digest(json.dumps(meta, sort_keys=True).encode())[:20]
        alias = 'character-sync-' + identity
        if alias not in effect_inventory:
            src = REVIEW / meta['path']
            im = image(meta['path'])
            target = OUT / 'effects' / (identity + '.png')
            target.parent.mkdir(exist_ok=True)
            # The review compositor reads RGBA8. Save those exact pixels so
            # Godot's 16-bit PNG rounding cannot subtly change glow colours.
            im.save(target, optimize=True)
            density = im.width / meta['frame_size'][0]
            normalized = density != im.height / meta['frame_size'][1]
            if normalized:
                # Preserve the review's independent display axes for tiny skull
                # fragments. The runtime consumes this explicit logical size.
                meta['logical_frame_size'] = meta['frame_size']
                density = 1
            assert density > 0
            logical_size = meta['frame_size']
            meta.update(path=resource(target), frame_size=list(im.size), native_density=density,
                        frames=1, columns=1, source_effect_id=eid, art_revision=REV)
            data['sprites'][alias] = meta
            effect_inventory[alias] = {'id': alias, 'path': resource(target), 'source': str(src.relative_to(REVIEW)),
                                       'size': list(im.size), 'logical_size': logical_size, 'bytes': target.stat().st_size,
                                       'rgba_sha256': pixels(im), 'normalized_review_display_size': normalized}
        return alias

    for profile in gallery['profiles']:
        pid, context = profile['id'], profile['context']
        assert not profile.get('frameErrors') and not profile.get('sourceReviewPending'), pid
        key = profile_key(profile)
        w, h = profile['outputFrameSize']
        count = max(profile['sourceFrameCount'], max(map(int, profile['newFrames'])) + 1)
        columns = min(16, count)
        packed = Image.new('RGBA', (columns * w, ((count + columns - 1) // columns) * h))
        hashes = {}
        for slot, path in profile['newFrames'].items():
            im = image(path)
            assert im.size == (w, h), (pid, slot)
            i = int(slot)
            packed.paste(im, (i % columns * w, i // columns * h))
            hashes[slot] = pixels(im)
        target = OUT / (pid + '.png')
        packed.save(target, optimize=True)
        art = {'path': resource(target), 'frame_size': [w, h], 'frames': count, 'columns': columns,
               'anchor': profile['anchor'], 'native_density': 4, 'reviewed_profile': pid,
               'source_oam_frame_count': profile['sourceOamCutoff'], 'oam_flip_origin_offset': profile['flipOriginOffset'],
               'original_motion': True, 'art_revision': profile.get('revision') or 'accepted-original-review',
               'review_sync': REV}
        item = {'profile': pid, 'key': key, 'context': context, 'revision': art['art_revision'],
                'path': resource(target), 'size': list(packed.size), 'bytes': target.stat().st_size,
                'frame_hashes': hashes, 'lossless_review_pixels': True}
        if context == 'battle':
            art.update(reviewed_variants={}, reviewed_reactions={}, reviewed_class_id=int(profile['classId']),
                       reviewed_side=profile['side'])
            for action in actions[pid]:
                if action['kind'] not in ['attack', 'reaction']:
                    continue  # Reference-only skill presentations do not create gameplay abilities.
                rows = copy.deepcopy(action.get('revisedFrames', action['frames']))
                rows += copy.deepcopy(action.get('reviewTailFrames', []))
                original = native[profile['side']].get(action['key'], {})
                same_ticks = (len(original.get('frames', [])) == len(action['frames'])
                              and original.get('contact_tick') == action['contactTick'])
                for i, row in enumerate(rows):
                    assert str(row['frame']) in hashes, (pid, action['key'], row['frame'])
                    if same_ticks and i < len(original['frames']):
                        for extra in ['sound_requests', 'target_palette']:
                            if extra in original['frames'][i]:
                                row[extra] = copy.deepcopy(original['frames'][i][extra])
                    effects = []
                    for e in row.get('effects', []):
                        eid = e['sprite']
                        if eid.endswith('-target-reference'):
                            continue
                        e['sprite'] = effect(eid, profile)
                        if eid.startswith('review-slime-') and '-color-' not in eid:
                            e['bind_target'] = True
                        effects.append(e)
                    row['effects'] = effects
                runtime_key = 'reviewed/' + pid + '/' + action['key']
                variant = {'native_fps': action['fps'], 'contact_tick': action['contactTick'], 'frames': rows,
                           'review_origin': action['origin'], 'reviewed_action': action['id'],
                           'source_frame_count': len(action['frames']), 'visual_tail_frames': len(action.get('reviewTailFrames', [])),
                           'art_revision': art['art_revision'], 'content_digest': action['contentDigest']}
                data['variants'][runtime_key] = variant
                field = 'reviewed_variants' if action['kind'] == 'attack' else 'reviewed_reactions'
                action_key = action['key'].removeprefix('reaction-') if field == 'reviewed_reactions' else action['key']
                art[field][action_key] = runtime_key
                if action_key == 'idle':
                    art['sequences'] = {'idle': [rows[0]['frame']]}
                    art['idle_flip'] = rows[0].get('flip', False)
                action_inventory.append({'id': action['id'], 'key': key, 'profile': pid, 'kind': action['kind'],
                                         'runtime_key': runtime_key, 'fps': action['fps'], 'contact_tick': action['contactTick'],
                                         'frames': len(rows), 'content_digest': action['contentDigest'],
                                         'review_rows_sha256': digest(json.dumps(action.get('revisedFrames', action['frames']) + action.get('reviewTailFrames', []), sort_keys=True).encode())})
            assert art.get('sequences'), pid
            innate = {'3_enemy': {'1001': 'stone-claw', '1002': 'stone-spit', '1002_far': 'stone-spit-far'},
                      '5_enemy': {'1003': 'innate-bone-bite', '1004': 'innate-eroding-breath'},
                      '21_enemy': {'1005': 'wing-beak', '1006': 'sun-crown', '1006_far': 'sun-crown-far'}}.get(key)
            if innate:
                art['innate_variants'] = {k: art['reviewed_variants'][v] for k, v in innate.items()}
                art['default_facing'] = 'left'  # Review row.flip retains right-facing legacy bodies explicitly.
                if 'empowered' in art['reviewed_reactions']:
                    art['empowered_idle'] = data['variants'][art['reviewed_reactions']['empowered']]['frames'][0]['frame']
            data['battle'][key] = art
        else:
            art.update(tile_origin=[profile['anchor'][0] - 8, profile['anchor'][1] - 16],
                       directions={}, direction_cycles={}, default_facing='right', static_facing=True)
            if context == 'tactical-idle' or not any(a['kind'] == 'map_walk' for a in actions[pid]):
                action = next(a for a in actions[pid] if a['kind'] == 'map_idle')
                rows = action.get('revisedFrames', action['frames'])
                c = cycle([row['frame'] for row in rows])
                art.update(native_cycle=c['frames'], cycle_ticks=c['ticks'])
                art['directions'] = {d: [c['frames'][0], c['frames'][0]] for d in ['up', 'down', 'left', 'right', 'side']}
            else:
                # Bake only explicitly requested map flips into dedicated atlas slots.
                # Tactical and story renderers can then share exact poses without double mirroring.
                aliases = {}
                for direction in ['up', 'right', 'down', 'left']:
                    action = next(a for a in actions[pid] if a['key'] == 'walk-' + direction)
                    indices = []
                    for row in action.get('revisedFrames', action['frames']):
                        assert row['offset'] == [0, 0]
                        slot = row['frame']
                        if row.get('flip', False):
                            if slot not in aliases:
                                aliases[slot] = count
                                count += 1
                            slot = aliases[slot]
                        indices.append(slot)
                    c = cycle(indices)
                    art['direction_cycles'][direction] = c
                    art['directions'][direction] = c['frames'] if len(c['frames']) > 1 else c['frames'] * 2
                if aliases:
                    expanded = Image.new('RGBA', (columns * w, ((count + columns - 1) // columns) * h))
                    expanded.paste(packed, (0, 0))
                    for old, new in aliases.items():
                        flipped = image(profile['newFrames'][str(old)]).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                        expanded.paste(flipped, (new % columns * w, new // columns * h))
                        hashes[str(new)] = pixels(flipped)
                    packed = expanded
                    packed.save(target, optimize=True)
                    art['frames'] = count
                    item.update(size=list(packed.size), bytes=target.stat().st_size)
                art['directions']['side'] = art['directions']['right']
                art['native_move_ticks'] = 16
            if profile.get('mapShadow'):
                shadow = copy.deepcopy(profile['mapShadow'])
                st = OUT / (pid + '-shadow.png')
                st.write_bytes((REVIEW / shadow['path']).read_bytes())
                shadow['path'] = resource(st)
                art['ground_shadow'] = shadow
            data['maps'].setdefault(key, {})[context] = art
        inventory.append(item)
        print(pid, flush=True)
    data['revision'] = REV
    data.setdefault('map_revisions', {})[REV] = {i['profile']: i['revision'] for i in inventory}
    write(runtime_path, data)
    for settings in OUT.rglob('*.png.import'):
        text = settings.read_text()
        settings.write_text(text.replace('process/fix_alpha_border=true', 'process/fix_alpha_border=false'))
    report = {'revision': REV, 'source_gallery_sha256': digest(gzip.decompress(snapshot.read_bytes())),
              'profiles': len(inventory), 'battle_profiles': sum(i['context'] == 'battle' for i in inventory),
              'map_profiles': sum(i['context'] != 'battle' for i in inventory), 'runtime_actions': len(action_inventory),
              'attack_variants': sum(i['kind'] == 'attack' for i in action_inventory),
              'effects': list(effect_inventory.values()), 'inventory': inventory, 'actions': action_inventory,
              'stone_wing_battle': 'User-selected legacy eight poses, pixel exact',
              'reference_only_skill_actions': [a['id'] for a in gallery['actions'] if a['kind'] == 'skill'],
              'rules_and_save_data_modified': False, 'device_updated': False}
    write(REPORT / 'import.json', report)
    print(json.dumps({k: v for k, v in report.items() if k not in ['inventory', 'effects', 'actions']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
    from build_runtime_animations import build as build_runtime
    build_runtime()
