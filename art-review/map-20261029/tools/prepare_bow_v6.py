"""Register the MAP-specific bow art to the accepted map height and leg layer.

ImageGen authored the equipment poses, sturdy waist and focused face. This
step only slices/registers bitmaps and reuses the original fixed leg layer.
"""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1]
ROOT = OUT.parents[1]
data_file = OUT / 'data.js'
data = json.loads(data_file.read_text().split('=', 1)[1].strip().removesuffix(';'))
preserved = json.dumps(data['jobs'][:4], sort_keys=True)
source_path = ROOT / 'source/map-20261029/hunapu-map-bow-v6c-original.png'
source = Image.open(source_path).convert('RGBA')
cw, ch = source.width // 2, source.height // 2
registrations = json.loads((OUT / 'reference/bow-v6/registration.json').read_text())
original = Image.open(OUT / data['jobs'][1]['hero_sprite']['path']).convert('RGBA').crop((0, 0, 96, 96))
native_legs = original.crop((0, 58, 96, 96))
frames = []
records = []

for i, r in enumerate(registrations):
    cell = source.crop((i % 2 * cw, i // 2 * ch, i % 2 * cw + cw, i // 2 * ch + ch))
    hard_alpha = cell.getchannel('A').point(lambda a: 255 if a > 200 else 0)
    hb = r['hair_bbox']
    head_center = (hb[0] + hb[2]) / 2
    # Measure the crown at the head center, excluding the bow/string above it.
    crown_region = (int(head_center - 25), hb[1] - 28, int(head_center + 25), hb[1] + 24)
    crown = hard_alpha.crop(crown_region).getbbox()[1] + crown_region[1]
    bottom = hard_alpha.crop((0, int(ch * .6), int(cw * .75), ch)).getbbox()[3] + int(ch * .6)
    scale = 65 / (bottom - crown)
    dx, dy = 47 - head_center * scale, 15 - crown * scale
    # Drop only very faint generation fringe, preserving real sprite opacity.
    cell.putalpha(cell.getchannel('A').point(lambda a: 0 if a < 100 else a))
    registered = cell.transform((96, 96), Image.Transform.AFFINE,
                                (1 / scale, 0, -dx / scale, 0, 1 / scale, -dy / scale),
                                resample=Image.Resampling.NEAREST)
    # The lowered ready bow crosses in front of the right knee. Keep that
    # small weapon region as a separate foreground layer over the native legs.
    weapon_mask = Image.new('L', (96, 96))
    md = ImageDraw.Draw(weapon_mask)
    md.rectangle((76, 58, 95, 67), fill=255)
    if i == 0:
        md.polygon([(67, 58), (73, 58), (73, 67), (63, 67), (63, 65), (65, 62)], fill=255)
    weapon = registered.copy()
    weapon.putalpha(Image.composite(registered.getchannel('A'), Image.new('L', (96, 96)), weapon_mask))
    registered.paste(native_legs, (0, 58))
    registered.alpha_composite(weapon)
    assert registered.crop((0, 68, 96, 96)).tobytes() == original.crop((0, 68, 96, 96)).tobytes()
    if i != 0:
        assert registered.crop((0, 58, 76, 96)).tobytes() == original.crop((0, 58, 76, 96)).tobytes()
    padded = Image.new('RGBA', (128, 128))
    padded.paste(registered, (16, 16))
    frames.append(padded)
    records.append({'pose': i, 'source_cell': [i % 2, i // 2], 'source_head_crown': crown,
                    'source_boot_bottom': bottom, 'scale': scale, 'translate': [dx, dy],
                    'target_person_head_top': 15, 'target_boot_bottom': 80,
                    'native_leg_layer_source_y': 58, 'fixed_boot_strip_y': 68,
                    'note': '原图腿层先完整恢复；低持弓姿势的弓下缘作为前景遮挡右膝，未改变腿的形状或长度。'})

order = [0, 1, 2, 3, 3, 0]
atlas = Image.new('RGBA', (768, 128))
for n, pose in enumerate(order):
    atlas.paste(frames[pose], (128 * n, 0))
target = OUT / 'assets/hunapu-bow-map-action-v6.png'
atlas.save(target, optimize=True)
job = data['jobs'][4]
job['map_action'] = {
    'path': str(target.relative_to(OUT)), 'frame_size': [128, 128], 'frames': 6,
    'columns': 6, 'tile_origin': [8, 8], 'native_density': 4, 'kind': 'bow',
    'timeline': [[0, 0], [1.05, 1], [1.30, 2], [1.94, 3], [2.12, 4], [2.72, 5], [3.15, 0]],
    'foot_lock_y': 84, 'idle': 0,
    'source': str(source_path.relative_to(ROOT)),
    'map_reference': data['jobs'][1]['hero_sprite']['path'],
    'person_height_native_pixels': 65, 'leg_layer_native_y': 58,
    'design': '与地图原型同身高、同腿长，腰腹加厚，眼神聚焦；仅弓箭动作改造。'
}
job['portrait_from_map'] = True
job['bow_muzzle_offset'] = [16, 4]
job['body'] = {'path': str(target.relative_to(OUT)), 'frame_size': [128, 128],
               'columns': 6, 'idle': 0, 'anchor': [64, 96],
               'frames': [{'frame': 0, 'flip': False}],
               'source': str(source_path.relative_to(ROOT)), 'source_variant': 'hunapu_tactical_map_bow_v6'}
data['version'] = 'MAP art review 2026-10-29 / compact map bow revision 6'
assert json.dumps(data['jobs'][:4], sort_keys=True) == preserved
data_file.write_text('window.MAP_DATA=' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n')

# Equal-size body/leg check. The bow itself can extend above the person's head.
proof = Image.new('RGB', (1440, 448), '#15232d')
draw = ImageDraw.Draw(proof)
font = ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc', 18)
small = ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc', 14)
for i, (image, label) in enumerate(zip([original] + [f.crop((16, 16, 112, 112)) for f in frames],
                                      ['已确认地图原型', '持弓准备', '抬弓搭箭', '拉满弓弦', '松弦放箭'])):
    x = i * 288
    draw.text((x + 70, 15), label, font=font, fill='#d6e7e5')
    thumb = image.resize((288, 288), Image.Resampling.NEAREST)
    proof.paste(thumb, (x, 68), thumb)
    for native_y, color in [(15, '#718d9b'), (58, '#415a68'), (80, '#86b2a0')]:
        y = 68 + native_y * 3
        draw.line((x + 10, y, x + 278, y), fill=color)
    draw.text((x + 64, 380), '同身高 · 同腿长 · 固定靴底', font=small, fill='#a8cdbd')
proof.save(OUT / 'sources/bow-v6-height-review.png', optimize=True)

# Rebuild the existing five-row action sheet, preserving accepted four rows.
review = Image.new('RGB', (1152, 1180), '#15232d')
rd = ImageDraw.Draw(review)
for row, j in enumerate(data['jobs']):
    a = j['map_action']
    art = Image.open(OUT / a['path']).convert('RGBA')
    name = ('胡纳普' if j['hero'] == 'hunapu' else '艾琳') + ' · ' + j['profession'] + (' · 持弓' if j.get('bow') else '')
    rd.text((12, row * 236 + 3), name, font=font, fill='#c7e3e5')
    poses = ([0, 1, 2, 3, 4, 0] if j.get('bow') else [0, 2, 6, 9, 12, 15] if j['hero'] == 'eileen' else [0, 2, 0, 3, 4, 0])
    captions = (['持弓准备', '抬弓搭箭', '拉满弓弦', '松弦放箭', '收势', '准备'] if j.get('bow') else
                ['准备', '举剑蓄势', '向前挥出', '下劈完成', '收剑', '准备'] if j['hero'] == 'eileen' else
                ['准备', '举剑蓄势', '挥剑起手', '挥出／释放', '收势', '准备'])
    for col, (pose, caption) in enumerate(zip(poses, captions)):
        rd.text((col * 192 + 50, row * 236 + 25), caption, font=small, fill='#9fbac6')
        frame = art.crop((pose * 128, 0, pose * 128 + 128, 128)).resize((192, 192), Image.Resampling.NEAREST)
        review.paste(frame, (col * 192, row * 236 + 39), frame)
review.save(OUT / 'sources/actions-v6-review.png', optimize=True)
report = {'revision': 6, 'purpose': '地图持弓造型修正：同身高、同腿长、固定原腿层、厚腰、聚焦眼神',
          'source': str(source_path.relative_to(ROOT)), 'reference': data['jobs'][1]['hero_sprite']['path'],
          'path': str(target.relative_to(OUT)), 'pixels': list(atlas.size), 'bytes': target.stat().st_size,
          'registration': records, 'frame_source_order': order, 'native_leg_layer': [0, 58, 96, 96],
          'all_boot_strips_equal_to_native': True,
          'foot_sha256': hashlib.sha256(frames[0].crop((0, 84, 128, 128)).tobytes()).hexdigest(),
          'preserved_four_cases': True, 'generation': 'built-in image_gen, prompts in bow-v6*.json'}
(OUT / 'sources/bow-v6.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(json.dumps({'path': report['path'], 'pixels': report['pixels'], 'bytes': report['bytes'],
                  'person_height': 65, 'native_leg_layer_y': 58, 'fixed_boots': True, 'preserved_four_cases': True}))
