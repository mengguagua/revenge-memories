from pathlib import Path
from PIL import Image, ImageOps, ImageDraw
import json, hashlib, shutil, subprocess

ROOT = Path(__file__).resolve().parent
FPS = 60.0988

def clean_invisible_rgb(im):
    # Visibility-preserving PNG normalization; alpha and all visible colors unchanged.
    im = im.convert('RGBA')
    im.putdata([(0, 0, 0, 0) if p[3] == 0 else p for p in im.getdata()])
    return im

def sole(im, box):
    a = im.getchannel('A')
    pts = [(x, y) for y in range(box[1], box[3]) for x in range(box[0], box[2]) if a.getpixel((x, y)) >= 128]
    bottom = max(y for x, y in pts) + 1
    pts = [(x, y) for x, y in pts if y >= bottom - 3]
    return [min(x for x, y in pts), bottom - 3, max(x for x, y in pts) + 1, bottom]

def paired_soles(im, boxes):
    # Rotated/raised source boots have a higher toe than heel. Use each isolated
    # visible boot's complete bounds so its raised toe is not silently discarded.
    b = []
    for box in boxes:
        local = im.getchannel('A').crop(box).point(lambda v: 255 if v >= 128 else 0).getbbox()
        b.append([local[0] + box[0], local[1] + box[1], local[2] + box[0], local[3] + box[1]])
    return {'visible_boot_boxes': b, 'roi_boxes': boxes, 'center_x': (min(x[0] for x in b) + max(x[2] for x in b)) / 2, 'bottom_y': max(x[3] for x in b)}

def file_record(p):
    im = Image.open(p)
    return {'size': list(im.size), 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}

selected = {
    'idle': [ROOT / f'source/idle-v2-nearest-{i:02}.png' for i in range(3)],
    'walk': [ROOT / 'source/walk-v4-00.png', ROOT / 'source/walk-v3-01.png'],
}
canonical = {'idle': [], 'walk': []}
registration = []
for kind, paths in selected.items():
    for index, p in enumerate(paths):
        im = Image.open(p).convert('RGBA')
        ref = Image.open(ROOT / f'reference/{kind}-source-{index:02}.png').convert('RGBA')
        ref = ref.resize((ref.width * 4, ref.height * 4), Image.Resampling.NEAREST)
        if kind == 'walk':
            # Native movement slot appearance is authoritative. The program's
            # unmirrored 'right' label does not prescribe the face/spear direction.
            # Both source feet measured separately: raised boot remains represented.
            ref_boxes = [(32, 88, 64, 96), (64, 84, 96, 92)]
            cur_boxes = [(16, 88, 64, 96), (64, 84, 112, 96)]
            current = paired_soles(im, cur_boxes)
            target = paired_soles(ref, ref_boxes)
            reason = 'Native source slot direction retained; no extra art mirror. Original paired visible boot bounds center/baseline includes raised toes. Runtime left mirror applies equally to source/new.'
        else:
            current_box = sole(im, (26, 64, 56, 86))
            target_box = sole(ref, (28, 68, 52, 80))
            current = {'sole_boxes': [current_box], 'center_x': (current_box[0] + current_box[2]) / 2, 'bottom_y': current_box[3]}
            target = {'sole_boxes': [target_box], 'center_x': (target_box[0] + target_box[2]) / 2, 'bottom_y': target_box[3]}
            reason = 'Fixed native idle facing preserved; planted visible boot anchor excludes diagonal spear butt.'
        xy = (round(target['center_x'] - current['center_x']), target['bottom_y'] - current['bottom_y'])
        out = Image.new('RGBA', im.size)
        out.paste(im, xy)
        # No opaque character pixels lost during translation; transparent padding may change.
        assert sum(v >= 128 for v in out.getchannel('A').getdata()) == sum(v >= 128 for v in im.getchannel('A').getdata())
        out = clean_invisible_rgb(out)
        canonical[kind].append(out)
        registration.append({'kind': kind, 'canonical_index': index, 'selected_source': str(p.relative_to(ROOT)), 'mirror_x': False, 'before': current, 'native_target': target, 'translation': list(xy), 'result_anchor': [current['center_x'] + xy[0], current['bottom_y'] + xy[1]], 'reason': reason})

aliases = {'walk': [0, 1, 0, 1, 0, 1], 'idle': [0, 1, 2, 1, 0, 1]}
for kind, indices in aliases.items():
    size = canonical[kind][0].size
    atlas = Image.new('RGBA', (size[0] * 6, size[1]))
    for slot, index in enumerate(indices):
        im = canonical[kind][index]
        im.save(ROOT / f'deliverables/tactical-{kind}-{slot:02}.png')
        atlas.paste(im, (slot * size[0], 0))
    atlas.save(ROOT / f'deliverables/tactical-{kind}.png')
for slot in [4, 5]:
    ImageOps.mirror(canonical['walk'][slot % 2]).save(ROOT / f'deliverables/tactical-walk-{slot:02}-left.png')
subprocess.run(['/opt/homebrew/bin/oxipng', '-o', '3', '--quiet', *map(str, (ROOT / 'deliverables').glob('*.png'))], check=True)

mapping = {'schema_version': 1, 'actor_id': 'enemy-spearman', 'character_id': 'enemy-spearman', 'display_name': '敌方枪兵', 'class_id': 6, 'original_class_id': 6, 'source_side': 'enemy', 'width_height_scale': 4, 'status': 'complete_art_review_ready', 'runtime_integrated': False, 'source_originals_unchanged': True, 'art_mode': 'Built-in ImageGen; rectangular slicing, isotropic scaling, whole-frame translation and native direction mirror; oxipng lossless. Alpha-zero RGB normalization changes no visible pixel.', 'identity_reference': '../battle/frames/frame-019.png', 'registration': 'source/final-foot-registration.json', 'scenarios': []}
for kind in ['walk', 'idle']:
    sid = 'tactical-' + kind
    size = [128, 96] if kind == 'walk' else [96, 96]
    s = {'id': sid, 'class_id': 6, 'original_class_id': 6, 'source_side': 'enemy', 'character_id': 'enemy-spearman', 'display_name': '敌方枪兵', 'source_atlas': f'reference/{kind}-source-atlas.png', 'original_source_path': '../../../source-input/' + ('original-motion/original-walk-6.png' if kind == 'walk' else 'legacy-assets/assets/original/graphics/map_units/class_6_enemy.png'), 'source_frame_size': [size[0] // 4, 24], 'source_anchor': [16, 24] if kind == 'walk' else [12, 20], 'output_atlas': f'deliverables/{sid}.png', 'output_frame_size': size, 'output_anchor': [64, 96] if kind == 'walk' else [48, 80], 'logical_render_scale': 0.25, 'output_atlas_bytes': (ROOT / f'deliverables/{sid}.png').stat().st_size, 'canonical_count': len(canonical[kind]), 'source_alias_to_canonical': aliases[kind], 'frame_mapping': []}
    for slot, index in enumerate(aliases[kind]):
        p = ROOT / f'deliverables/{sid}-{slot:02}.png'
        r = next(x for x in registration if x['kind'] == kind and x['canonical_index'] == index)
        s['frame_mapping'].append({'source_index': slot, 'canonical_source_index': index, 'output_index': slot, 'path': str(p.relative_to(ROOT)), 'output_path': str(p.relative_to(ROOT)), 'selected_source': r['selected_source'], 'whole_frame_mirror_x': r['mirror_x'], 'registration_offset': r['translation'], 'registered_foot_anchor': r['result_anchor'], 'alpha': 'RGBA; original generated alpha retained, transparent RGB normalized only', 'compression': 'oxipng -o3 lossless; no quantization', **file_record(p)})
    if kind == 'walk':
        s.update({'directions': {'down': [0, 1], 'up': [2, 3], 'right': [4, 5], 'left': [4, 5]}, 'direction_mirror_x': {'left': True}, 'default_facing': 'native', 'source_program_direction_basis': 'right=unmirrored native slot, not mandatory face direction', 'static_facing': False, 'timing': {'native_fps': FPS, 'frame_ticks': 16, 'cycle_ticks': 32, 'move_ticks_per_tile': 16, 'phase': 'continuous-clock'}, 'idle': {'kind': 'hold-current-direction-first-frame', 'directions': {'down': [0], 'up': [2], 'right': [4], 'left': [4]}}, 'adaptation_note': 'Native CHR26 has only two independent movement steps; all three direction pairs reuse them. Original ROM step1 upper-right8x8 tile is FF transparent, leaving an incomplete head/shoulder. ImageGen restores coherent identity using complete step0 while retaining visible limbs/boot anchors. Frozen source unchanged. No claim of exact pixel reconstruction of missing anatomy.', 'explicit_left_frames': [{'path': f'deliverables/tactical-walk-{i:02}-left.png', 'source_index': i, 'derived_from': f'deliverables/tactical-walk-{i:02}.png', 'transform': 'horizontal-mirror-about-frame-center', **file_record(ROOT / f'deliverables/tactical-walk-{i:02}-left.png')} for i in [4, 5]]})
    else:
        s.update({'directions': {'all': [0, 1, 2, 1]}, 'direction_mirror_x': {}, 'default_facing': 'fixed', 'static_facing': True, 'timing': {'native_fps': FPS, 'cycle_frames': [0, 1, 2, 1], 'frame_ticks': [14, 8, 14, 8]}, 'idle': {'kind': 'original-fixed-facing-cycle', 'frames': [0, 1, 2, 1]}, 'adaptation_note': 'Native fixed idle remains left/front facing with one continuous upper-right/lower-left spear, occluded at torso. It is not mirrored to match movement canonical right.'})
    s['preview_dark'] = f'previews/{sid}-dark.gif'
    s['preview_light'] = f'previews/{sid}-light.gif'
    mapping['scenarios'].append(s)

(ROOT / 'source/final-foot-registration.json').write_text(json.dumps({'method': 'Visible boot ROIs only, alpha>=128; raised and planted walk boots measured separately by full isolated boot bounds then combined, retaining raised toes. Idle planted boot uses bottom3px sole band. Whole image integer translation. No weapon alpha centering or limb deformation.', 'records': registration}, ensure_ascii=False, indent=2) + '\n')
for name in ['mapping.json', 'frame_mapping.json']:
    (ROOT / name).write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + '\n')

# Same-size source/new boards on both backgrounds; nearest enlargement is review-only.
board = Image.new('RGB', (1280, 576), (230, 225, 216))
draw = ImageDraw.Draw(board)
for col, (kind, index) in enumerate([('walk', 0), ('walk', 1), ('idle', 0), ('idle', 1), ('idle', 2)]):
    ref = Image.open(ROOT / f'reference/{kind}-source-{index:02}.png').convert('RGBA')
    ref = ref.resize((ref.width * 4, ref.height * 4), Image.Resampling.NEAREST)
    for row, im in enumerate([ref, canonical[kind][index], canonical[kind][index]]):
        bg = (40, 43, 50) if row == 1 else (230, 225, 216)
        board.paste(bg, (col * 256, row * 192, (col + 1) * 256, (row + 1) * 192))
        im = im.resize((im.width * 2, im.height * 2), Image.Resampling.NEAREST)
        x = col * 256 + (256 - im.width) // 2
        board.paste(im, (x, row * 192), im)
        draw.text((col * 256 + 3, row * 192 + 3), f'{kind}{index} ' + ['native', 'new dark', 'new light'][row], fill='white' if row == 1 else 'black')
board.save(ROOT / 'previews/all-map-original-dark-light.png')
direction_board = Image.new('RGB', (1024, 384), (40, 43, 50))
d = ImageDraw.Draw(direction_board)
for row in range(2):
    for col in range(4):
        q = canonical['walk'][col % 2]
        if col >= 2:
            q = ImageOps.mirror(q)
        if row:
            direction_board.paste((230, 225, 216), (col * 256, 192, col * 256 + 256, 384))
        q = q.resize((256, 192), Image.Resampling.NEAREST)
        direction_board.paste(q, (col * 256, row * 192), q)
        d.text((col * 256 + 3, row * 192 + 3), ('native base ' if col < 2 else 'left mirror ') + str(col % 2), fill='black' if row else 'white')
direction_board.save(ROOT / 'previews/walk-right-left-dark-light.png')
for kind in ['walk', 'idle']:
    ids, ticks = ([0, 1], [16, 16]) if kind == 'walk' else ([0, 1, 2, 1], [14, 8, 14, 8])
    for tone, bg in [('dark', (40, 43, 50)), ('light', (230, 225, 216))]:
        frames = []
        for i in ids:
            im = canonical[kind][i]
            c = Image.new('RGB', (384, 288), bg)
            q = im.resize((im.width * 3, im.height * 3), Image.Resampling.NEAREST)
            c.paste(q, ((384 - q.width) // 2, 0), q)
            frames.append(c)
        frames[0].save(ROOT / f'previews/tactical-{kind}-{tone}.gif', save_all=True, append_images=frames[1:], duration=[round(t * 1000 / FPS) for t in ticks], loop=0, disposal=2, optimize=False)
print(json.dumps(registration, indent=2))
