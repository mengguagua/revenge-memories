from pathlib import Path
from PIL import Image, ImageOps, ImageDraw
import json, hashlib, subprocess

ROOT = Path(__file__).resolve().parent
FPS = 60.0988

def bounds(im, box):
    b = im.getchannel('A').crop(box).point(lambda v: 255 if v >= 128 else 0).getbbox()
    return [b[0] + box[0], b[1] + box[1], b[2] + box[0], b[3] + box[1]]

def boots(im, boxes, sole=False):
    result = []
    for box in boxes:
        b = bounds(im, box)
        if sole:
            b = bounds(im, (box[0], b[3] - 3, box[2], b[3]))
        result.append(b)
    return {'boot_boxes': result, 'roi_boxes': boxes, 'center_x': (min(b[0] for b in result) + max(b[2] for b in result)) / 2, 'bottom_y': max(b[3] for b in result)}

def info(p):
    return {'size': list(Image.open(p).size), 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}

selected = {'walk': [ROOT / f'source/walk-selected-{i:02}.png' for i in range(2)], 'idle': [ROOT / f'source/idle-v2-{i:02}.png' for i in range(3)]}
canonical = {'walk': [], 'idle': []}
registrations = []
for kind, paths in selected.items():
    for i, p in enumerate(paths):
        im = Image.open(p).convert('RGBA')
        ref = Image.open(ROOT / f'reference/{kind}-source-{i:02}.png').convert('RGBA')
        ref = ref.resize((ref.width * 4, 96), Image.Resampling.NEAREST)
        if kind == 'idle':
            current = boots(im, [(54, 68, 84, 88)], sole=True)
            target = boots(ref, [(56, 72, 80, 80)], sole=True)
            method = 'Fixed idle planted right boot lower3px sole band; upright sword excluded.'
        elif i == 0:
            current = boots(im, [(48, 88, 72, 96), (72, 80, 96, 96)])
            target = boots(ref, [(52, 88, 72, 96), (72, 80, 88, 92)])
            method = 'Native phase0 visible two boots only; left-side weapon/forearm column excluded.'
        else:
            current = boots(im, [(28, 88, 56, 96), (60, 80, 84, 96)])
            target = boots(ref, [(32, 88, 60, 96), (60, 84, 80, 96)])
            method = 'Native phase1 two boots only; right-side lowered blade excluded.'
        xy = (round(target['center_x'] - current['center_x']), target['bottom_y'] - current['bottom_y'])
        out = Image.new('RGBA', im.size)
        out.paste(im, xy)
        assert sum(v >= 128 for v in out.getchannel('A').getdata()) == sum(v >= 128 for v in im.getchannel('A').getdata())
        out.putdata([(0, 0, 0, 0) if p[3] == 0 else p for p in out.getdata()])
        canonical[kind].append(out)
        registrations.append({'kind': kind, 'canonical_index': i, 'selected_source': str(p.relative_to(ROOT)), 'whole_frame_mirror_x': False, 'before': current, 'native_target': target, 'translation': list(xy), 'registered_foot_anchor': [current['center_x'] + xy[0], current['bottom_y'] + xy[1]], 'method': method})

aliases = {'walk': [0, 1, 0, 1, 0, 1], 'idle': [0, 1, 2, 1, 0, 1]}
for kind, ids in aliases.items():
    size = canonical[kind][0].size
    atlas = Image.new('RGBA', (size[0] * 6, size[1]))
    for slot, index in enumerate(ids):
        canonical[kind][index].save(ROOT / f'deliverables/tactical-{kind}-{slot:02}.png')
        atlas.paste(canonical[kind][index], (slot * size[0], 0))
    atlas.save(ROOT / f'deliverables/tactical-{kind}.png')
for slot in [4, 5]:
    ImageOps.mirror(canonical['walk'][slot % 2]).save(ROOT / f'deliverables/tactical-walk-{slot:02}-left.png')
subprocess.run(['/opt/homebrew/bin/oxipng', '-o', '3', '--quiet', *map(str, (ROOT / 'deliverables').glob('*.png'))], check=True)

mapping = {'schema_version': 1, 'actor_id': 'enemy-mercenary', 'character_id': 'enemy-mercenary', 'display_name': '敌方佣兵', 'class_id': 8, 'original_class_id': 8, 'source_side': 'enemy', 'width_height_scale': 4, 'status': 'complete_art_review_ready', 'runtime_integrated': False, 'source_originals_unchanged': True, 'art_mode': 'Built-in ImageGen; rectangular crop, uniform scale, whole-frame translation, original runtime direction mirror and lossless oxipng. Alpha-zero RGB canonicalization changes no visible pixels.', 'identity_reference': '../battle/frames/frame-000.png', 'registration': 'source/final-foot-registration.json', 'scenarios': []}
sizes = []
for kind in ['walk', 'idle']:
    sid = 'tactical-' + kind
    size = [128, 96] if kind == 'walk' else [96, 96]
    s = {'id': sid, 'class_id': 8, 'original_class_id': 8, 'source_side': 'enemy', 'character_id': 'enemy-mercenary', 'display_name': '敌方佣兵', 'source_atlas': f'reference/{kind}-source-atlas.png', 'original_source_path': '../../../source-input/' + ('original-motion/original-walk-8.png' if kind == 'walk' else 'legacy-assets/assets/original/graphics/map_units/class_8_enemy.png'), 'source_frame_size': [size[0] // 4, 24], 'source_anchor': [16, 24] if kind == 'walk' else [12, 20], 'output_atlas': f'deliverables/{sid}.png', 'output_frame_size': size, 'output_anchor': [64, 96] if kind == 'walk' else [48, 80], 'logical_render_scale': 0.25, 'output_atlas_bytes': (ROOT / f'deliverables/{sid}.png').stat().st_size, 'canonical_count': len(canonical[kind]), 'source_alias_to_canonical': aliases[kind], 'frame_mapping': []}
    for slot, index in enumerate(aliases[kind]):
        path = ROOT / f'deliverables/{sid}-{slot:02}.png'
        reg = next(x for x in registrations if x['kind'] == kind and x['canonical_index'] == index)
        if kind == 'idle':
            generated, prompt, initial = 'idle-generated-v2.png', 'idle-prompt-v2.txt', 'idle-registration-v2.json'
        elif index == 0:
            generated, prompt, initial = 'walk-generated-v2.png', 'walk-prompt-v2.txt', 'walk-selected-registration.json'
        else:
            generated, prompt, initial = 'walk-one-generated-v3.png', 'walk-one-prompt-v3.txt', 'walk-selected-registration.json'
        rec = {'source_index': slot, 'canonical_source_index': index, 'output_index': slot, 'path': str(path.relative_to(ROOT)), 'output_path': str(path.relative_to(ROOT)), 'selected_source': reg['selected_source'], 'generated_source': 'source/' + generated, 'prompt': 'source/' + prompt, 'initial_registration_record': 'source/' + initial, 'whole_frame_mirror_x': False, 'registration_offset': reg['translation'], 'registered_foot_anchor': reg['registered_foot_anchor'], 'alpha': 'RGBA; generated alpha retained; invisible RGB normalized only', 'compression': 'oxipng -o3 lossless, no quantization', **info(path)}
        s['frame_mapping'].append(rec)
        sizes.append({'path': rec['path'], 'purpose': sid, 'pixels': size, 'bytes': rec['bytes']})
    if kind == 'walk':
        s.update({'directions': {'down': [0, 1], 'up': [2, 3], 'right': [4, 5], 'left': [4, 5]}, 'direction_mirror_x': {'left': True}, 'default_facing': 'native', 'source_program_direction_basis': 'right is the unmirrored native-program baseline, not a mandatory face direction for each phase', 'static_facing': False, 'timing': {'native_fps': FPS, 'frame_ticks': 16, 'cycle_ticks': 32, 'move_ticks_per_tile': 16, 'phase': 'continuous-clock'}, 'idle': {'kind': 'hold-current-direction-first-frame', 'directions': {'down': [0], 'up': [2], 'right': [4], 'left': [4]}}, 'adaptation_note': 'Native2phase motion and visible per-phase weapon side/torso presentation retained; no extra whole-art mirror. Phase0 face information is sparse in original complete CHR, not a missing-tile defect. Phase1 upper-body placement and right-side lowered blade were locally redrawn against source. No new direction/view slots.', 'source_integrity': {'missing_tile_repair': False, 'oam_phase0': 'L0AA54D:A8/A9/B8/B9', 'oam_phase1': 'L0AA55E:AA/AB/BA/BB', 'attributes': '03', 'note': 'All tiles present; noFF empty-tile substitution.'}, 'explicit_left_frames': [{'path': f'deliverables/tactical-walk-{slot:02}-left.png', 'source_index': slot, 'derived_from': f'deliverables/tactical-walk-{slot:02}.png', 'transform': 'horizontal-mirror-about-frame-center', **info(ROOT / f'deliverables/tactical-walk-{slot:02}-left.png')} for slot in [4, 5]]})
    else:
        s.update({'directions': {'all': [0, 1, 2, 1]}, 'direction_mirror_x': {}, 'default_facing': 'fixed', 'static_facing': True, 'timing': {'native_fps': FPS, 'cycle_frames': [0, 1, 2, 1], 'frame_ticks': [14, 8, 14, 8]}, 'idle': {'kind': 'original-fixed-facing-cycle', 'frames': [0, 1, 2, 1]}, 'adaptation_note': 'Original fixed left/front-left idle with waist-side grip and3upright sword-tilt phases. No battle down-sword pose substituted.'})
    s['preview_dark'] = f'previews/{sid}-dark.gif'
    s['preview_light'] = f'previews/{sid}-light.gif'
    mapping['scenarios'].append(s)

mapping['qa'] = {'review': 'previews/all-map-original-dark-light.png', 'direction_review': 'previews/walk-native-left-dark-light.png', 'unique_art_count': 5, 'orientation': 'Native slot appearance retained, then the same original runtime direction mirror applied to source and new. Program labels never force a whole-art face turn.', 'native_defect': 'None: class8 OAM tables contain all4tiles in each phase; no missing-head claim or repair.', 'limits': ['Original tiny-map silhouettes contain ambiguous internal detail; new hair/cloth detail is designed without claiming exact hidden anatomy.', 'Minor sword/hand/boot contour differences remain; visible poses and native timing/aliases are retained.'], 'checks': ['All output paths loadRGBA with exact4x dimensions', 'Exact6-slot aliases for2walk/3idle poses', 'Explicit left files are exact horizontal mirrors', 'Visible boot ROIs exclude weapon extrema', 'Deep/light alpha edge and full weapons visually inspected', 'No game integration or frozen-source modification'], 'max_frame_bytes': max(x['bytes'] for x in sizes)}
for name in ['mapping.json', 'frame_mapping.json']:
    (ROOT / name).write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + '\n')
(ROOT / 'source/final-foot-registration.json').write_text(json.dumps({'method': 'Manual visible boot ROIs; alpha>=128; whole-frame integer translations only; weapon alpha excluded.', 'records': registrations}, ensure_ascii=False, indent=2) + '\n')
(ROOT / 'qa-summary.json').write_text(json.dumps({'status': mapping['status'], 'character_id': 'enemy-mercenary', 'display_name': '敌方佣兵', 'class_id': 8, 'source_side': 'enemy', 'qa': mapping['qa'], 'sizes': sizes}, ensure_ascii=False, indent=2) + '\n')

board = Image.new('RGB', (1280, 576), (230, 225, 216))
d = ImageDraw.Draw(board)
for col, (kind, i) in enumerate([('walk', 0), ('walk', 1), ('idle', 0), ('idle', 1), ('idle', 2)]):
    ref = Image.open(ROOT / f'reference/{kind}-source-{i:02}.png').convert('RGBA')
    ref = ref.resize((ref.width * 4, 96), Image.Resampling.NEAREST)
    for row, im in enumerate([ref, canonical[kind][i], canonical[kind][i]]):
        board.paste((40, 43, 50) if row == 1 else (230, 225, 216), (col * 256, row * 192, col * 256 + 256, row * 192 + 192))
        q = im.resize((im.width * 2, 192), Image.Resampling.NEAREST)
        board.paste(q, (col * 256 + (256 - q.width) // 2, row * 192), q)
        d.text((col * 256 + 3, row * 192 + 3), f'{kind}{i} ' + ['native', 'new dark', 'new light'][row], fill='white' if row == 1 else 'black')
board.save(ROOT / 'previews/all-map-original-dark-light.png')
board = Image.new('RGB', (1024, 384), (40, 43, 50))
d = ImageDraw.Draw(board)
for row in range(2):
    for col in range(4):
        q = canonical['walk'][col % 2]
        if col >= 2:
            q = ImageOps.mirror(q)
        if row:
            board.paste((230, 225, 216), (col * 256, 192, col * 256 + 256, 384))
        q = q.resize((256, 192), Image.Resampling.NEAREST)
        board.paste(q, (col * 256, row * 192), q)
        d.text((col * 256 + 3, row * 192 + 3), ('native base ' if col < 2 else 'left mirror ') + str(col % 2), fill='black' if row else 'white')
board.save(ROOT / 'previews/walk-native-left-dark-light.png')
for kind in ['walk', 'idle']:
    ids, ticks = ([0, 1], [16, 16]) if kind == 'walk' else ([0, 1, 2, 1], [14, 8, 14, 8])
    for tone, bg in [('dark', (40, 43, 50)), ('light', (230, 225, 216))]:
        frames = []
        for i in ids:
            im = canonical[kind][i]
            c = Image.new('RGB', (384, 288), bg)
            q = im.resize((im.width * 3, 288), Image.Resampling.NEAREST)
            c.paste(q, ((384 - q.width) // 2, 0), q)
            frames.append(c)
        frames[0].save(ROOT / f'previews/tactical-{kind}-{tone}.gif', save_all=True, append_images=frames[1:], duration=[round(t * 1000 / FPS) for t in ticks], loop=0, disposal=2, optimize=False)

for s in mapping['scenarios']:
    for slot, canonical_index in enumerate(s['source_alias_to_canonical']):
        a = Image.open(ROOT / s['frame_mapping'][slot]['path'])
        b = Image.open(ROOT / s['frame_mapping'][canonical_index]['path'])
        assert a.tobytes() == b.tobytes()
for slot in [4, 5]:
    assert ImageOps.mirror(Image.open(ROOT / f'deliverables/tactical-walk-{slot:02}.png')).tobytes() == Image.open(ROOT / f'deliverables/tactical-walk-{slot:02}-left.png').tobytes()
print(json.dumps(registrations, indent=2))
print('Verified frame bytes', min(x['bytes'] for x in sizes), max(x['bytes'] for x in sizes))
