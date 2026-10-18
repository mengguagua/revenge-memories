#!/usr/bin/env python3
"""Build isolated mercenary battle deliverables from reviewed ImageGen art."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import hashlib, json, shutil, subprocess, sys

R = Path(__file__).resolve().parents[1]
E, B = R.parents[1], R / 'battle'
passed = '--review-passed' in sys.argv
status = 'complete_art_review_passed' if passed else 'review_candidate'
def write(p, d):
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
def info(p):
    im = Image.open(p)
    return {'path': str(p.relative_to(R)), 'size': list(im.size), 'bytes': p.stat().st_size,
            'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'alpha_bounds': im.convert('RGBA').getbbox()}

for folder in ['frames', 'deliverables', 'reviews']:
    (B / folder).mkdir(exist_ok=True)
unit = next(u for u in json.loads((E / 'catalog/production-units.json').read_text())['units'] if u['id'] == 'class-8-ally')
meta = json.loads((E / 'source-input/original-motion/full-original-motion.json').read_text())['original_bodies']['8']
canonical, required = unit['unique_art_frames'], unit['required_source_frames']
for f in [0, 7, 16]:
    shutil.copy2(B / f'candidate-keys-v2/frame-{f:03d}.png', B / f'frames/frame-{f:03d}.png')
for f in range(1, 6):
    shutil.copy2(B / f'candidate-motion-v4/frame-{f:03d}.png', B / f'frames/frame-{f:03d}.png')

# Exact source subset proof. No artistic parts are synthesized by code.
source6 = Image.open(B / 'reference/original-006.png').convert('RGBA')
source7 = Image.open(B / 'reference/original-007.png').convert('RGBA')
shifted = Image.new('RGBA', source7.size)
shifted.alpha_composite(source7, (-4, 0))
arc = source6.copy()
checked = 0
for y in range(source6.height):
    for x in range(source6.width):
        p = shifted.getpixel((x, y))
        if p[3]:
            assert p == source6.getpixel((x, y)), (x, y, 'source subset differs')
            arc.putpixel((x, y), (0, 0, 0, 0))
            checked += 1
arc.save(B / 'reference/original-slash-only-006.png')
proof = {'source_body_frame': 7, 'source_effect_frame': 6, 'body_shift_output_pixels': [-4, 0],
         'body_shift_native_pixels': [-1, 0], 'occupied_rgba_pixels_checked': checked,
         'all_occupied_source7_pixels_equal_source6_after_shift': True,
         'arc_alpha_bounds': arc.getbbox(), 'method': 'Direct per-pixel RGBA equality, not RGBA alpha-only difference bounding box.'}
write(B / 'reference/slash-reuse-proof.json', proof)
new6 = arc.copy()
new6.alpha_composite(Image.open(B / 'frames/frame-007.png').convert('RGBA'), (-4, 0))
new6.save(B / 'frames/frame-006.png')
for f in [8, 15]:
    shutil.copy2(B / 'frames/frame-000.png', B / f'frames/frame-{f:03d}.png')
atlas = Image.new('RGBA', (320 * len(canonical), 256))
for n, f in enumerate(canonical):
    atlas.alpha_composite(Image.open(B / f'frames/frame-{f:03d}.png').convert('RGBA'), (n * 320, 0))
atlas.save(B / 'deliverables/battle-canonical.png')
delivery = [*sorted((B / 'frames').glob('frame-*.png')), B / 'deliverables/battle-canonical.png']
subprocess.run(['/opt/homebrew/bin/oxipng', '-o', '4', '--strip', 'safe', '--quiet', *map(str, delivery)], check=True)
regs = json.loads((B / 'candidate-keys-v1/registration.json').read_text())
regs = [r for r in regs if r['frame'] != 16]
regs += [json.loads((B / 'candidate-keys-v2/registration-016.json').read_text())]
regs += json.loads((B / 'candidate-motion-v4/registration.json').read_text())
byframe = {r['frame']: r for r in regs}
records = []
for f in required:
    c = unit['exact_pixel_aliases'][str(f)]
    rec = {'source_frame': f, 'canonical_frame': c, **info(B / f'frames/frame-{f:03d}.png')}
    if c in byframe:
        rec['registration'] = byframe[c]
    if f == 6:
        rec['composition'] = {'body_frame': 7, 'body_shift': [-4, 0], 'original_arc': 'reference/original-slash-only-006.png', 'proof': 'reference/slash-reuse-proof.json'}
    records.append(rec)
write(B / 'frame_mapping.json', {
    'schema_version': 1, 'character_id': 'class-8-ally', 'display_name': '佣兵（职业样板）',
    'original_class_id': 8, 'source_side': 'ally', 'status': status, 'runtime_integrated': False,
    'source_atlas': '../../../source-input/original-motion/class-8.png', 'source_frame_size': [80, 64],
    'output_frame_size': [320, 256], 'source_anchor': [40, 64], 'output_anchor': [160, 256],
    'source_columns': 16, 'source_oam_frame_count': 8, 'source_idle_frame': 8, 'source_frame_count': meta['frames'],
    'frame_mapping': {str(f): f'frames/frame-{f:03d}.png' for f in required},
    'canonical_frames': canonical, 'required_source_frames': required, 'variant_keys': unit['bound_action_keys'],
    'records': records, 'output_atlas': 'deliverables/battle-canonical.png', 'output_atlas_frame_order': canonical,
    'external_effects': 'Original lightning remains external. Frame6 retains the exact original slash layer behind frame7 body translated by -4 output pixels.',
    'art_generator': 'built-in image_gen', 'identity_scope': 'Profession exemplar only; no named actor equipment or abilities added.'})
font = ImageFont.truetype('/System/Library/Fonts/STHeiti Light.ttc', 18)
for theme, bg in [('dark', (30, 44, 53)), ('light', (229, 230, 220))]:
    board = Image.new('RGBA', (1648, 1248), bg + (255,))
    draw = ImageDraw.Draw(board)
    fg = (235, 242, 244) if theme == 'dark' else (34, 43, 47)
    for g, frames in enumerate([canonical[:5], canonical[5:]]):
        y = g * 624
        draw.text((24, y + 14), '佣兵原作：' + ' / '.join(map(str, frames)), font=font, fill=fg)
        draw.text((24, y + 326), '四倍像素重绘 · 原握姿、步相与剑弧', font=font, fill=fg)
        for j, f in enumerate(frames):
            board.alpha_composite(Image.open(B / f'reference/original-{f:03d}.png').convert('RGBA'), (24 + j * 320, y + 44))
            board.alpha_composite(Image.open(B / f'frames/frame-{f:03d}.png').convert('RGBA'), (24 + j * 320, y + 356))
    board.convert('RGB').save(B / f'reviews/final-canonical-{theme}.png', optimize=True)
errors = []
for f in required:
    im = Image.open(B / f'frames/frame-{f:03d}.png')
    if im.size != (320, 256) or im.mode != 'RGBA':
        errors.append(f'invalid frame {f}')
for f in [8, 15]:
    if Image.open(B / f'frames/frame-{f:03d}.png').tobytes() != Image.open(B / 'frames/frame-000.png').tobytes():
        errors.append(f'alias {f} mismatch')
write(B / 'qa-report.json', {'structural_pass': not errors, 'errors': errors, 'status': status,
      'native_canonical_frames': 9, 'new_body_drawings': 8, 'required_source_frames': 11, 'bound_attack_programs': 7,
      'source_reuse_proof': proof, 'selected_registration_basis': 'Visible selected boot/support and head; never sword bbox centering or clamping.',
      'geometry_limit': 'Not pixel-identical anatomy. Per-boot, blade shaping and garment differences remain. Frame16 tip is5 outputpx above source; frame3 blade tip is about12px below source; frame4 blade tip differs by about11outputpx horizontally. Chosen registration point does not certify all joints.',
      'review': 'Root approved keys0/7/16 and motion1/2/3/5; final4 reviewed separately.' if passed else 'Final frame4 root review pending.',
      'browser_or_game_screenshot': 'Not run. Isolated art only; existing browser restriction respected.', 'runtime_integrated': False})
inventory = []
for p in sorted(R.rglob('*.png')):
    x = info(p)
    x['role'] = 'delivery' if p in delivery else 'review_preview' if '/reviews/' in str(p) else 'raw_history_or_reference'
    x['size_note'] = 'Losslessly optimized; atlas may exceed soft50KB target to retain visual quality.' if p in delivery else 'Isolated source/history/reference; not runtime asset.'
    inventory.append(x)
write(R / 'image-inventory.json', {'images': inventory, 'count': len(inventory)})
print(json.dumps({'battle_frames': len(required), 'canonical': len(canonical), 'errors': errors, 'max_single_bytes': max(p.stat().st_size for p in delivery if p.parent.name == 'frames'), 'atlas_bytes': delivery[-1].stat().st_size}))
