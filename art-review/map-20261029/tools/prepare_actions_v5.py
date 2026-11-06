"""Animate the approved Eileen map bitmap with a larger forearm/sword sweep.

Mechanical bitmap rig: no redraw, no changes to game/runtime resources.  Only
the existing weapon/forearm layer rotates; the original body and feet stay put.
"""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1]
data_file = OUT / 'data.js'
data = json.loads(data_file.read_text().split('=', 1)[1].strip().removesuffix(';'))
angles = [0, -15, -30, -20, -5, 12, 30, 48, 63, 72, 60, 45, 30, 16, 6, 0]
times = [0, .95, 1.20, 1.62, 1.70, 1.76, 1.82, 1.88, 1.94, 2.00,
         2.46, 2.60, 2.74, 2.88, 3.02, 3.18]
report = []

for job in data['jobs']:
    if job['hero'] != 'eileen':
        continue
    original = Image.open(OUT / job['hero_sprite']['path']).convert('RGBA').crop((0, 0, 96, 96))
    # Measured native-pixel separation, along the gap between sword/gauntlet
    # and hair. The two professions have different grips and elbow anchors.
    if job['advanced']:
        cuts = {**{y: 95 for y in range(19)}, 19: 50, 20: 47, 21: 45,
                22: 43, 23: 41, 24: 36, 25: 36, 26: 35, 27: 35,
                28: 31, **{y: 31 for y in range(29, 36)}}
        pivot = (29, 36)
    else:
        cuts = {**{y: 95 for y in range(24)}, 24: 46, 25: 43, 26: 42,
                27: 42, 28: 37, 29: 36, **{y: 35 for y in range(30, 37)}}
        pivot = (33, 37)
    mask = Image.new('L', (96, 96))
    md = ImageDraw.Draw(mask)
    for y, right in cuts.items():
        md.line((0, y, right, y), fill=255)
    empty = Image.new('L', (96, 96))
    arm = original.copy()
    arm.putalpha(Image.composite(original.getchannel('A'), empty, mask))
    body = original.copy()
    body.putalpha(Image.composite(empty, original.getchannel('A'), mask))
    body_pad = Image.new('RGBA', (128, 128))
    body_pad.paste(body, (16, 16))
    arm_pad = Image.new('RGBA', (128, 128))
    arm_pad.paste(arm, (16, 16))
    rig_pivot = (pivot[0] + 16, pivot[1] + 16)
    atlas = Image.new('RGBA', (128 * len(angles), 128))
    original_padded = Image.new('RGBA', (128, 128))
    original_padded.paste(original, (16, 16))
    original_feet = original_padded.crop((0, 84, 128, 128)).tobytes()
    frames = []
    for i, angle in enumerate(angles):
        rotated = arm_pad.rotate(-angle, resample=Image.Resampling.NEAREST, center=rig_pivot)
        # The full sweep fits the padded canvas and stays above the boots.
        assert rotated.crop((0, 84, 128, 128)).getbbox() is None, ('weapon reaches feet', job['key'], angle)
        cell = body_pad.copy()
        cell.alpha_composite(rotated)
        assert cell.crop((0, 84, 128, 128)).tobytes() == original_feet
        if angle == 0:
            assert cell.tobytes() == original_padded.tobytes(), ('idle identity', job['key'])
        atlas.paste(cell, (i * 128, 0))
        frames.append(cell)
    target = OUT / 'assets' / (job['key'] + '-map-action-v5.png')
    atlas.save(target, optimize=True)
    job['map_action'] = {
        'path': str(target.relative_to(OUT)), 'frame_size': [128, 128],
        'frames': len(frames), 'columns': len(frames), 'tile_origin': [8, 8],
        'native_density': 4, 'kind': 'casting', 'timeline': list(map(list, zip(times, range(len(frames))))),
        'foot_lock_y': 84, 'idle': 0, 'source': job['hero_sprite']['path'],
        'rig': {'part': 'native bitmap forearm and sword', 'pivot': list(rig_pivot),
                'angles_clockwise': angles, 'sweep_degrees': max(angles) - min(angles),
                'body': 'unchanged original pixels', 'effect_release_seconds': 1.8}
    }
    report.append({'key': job['key'], 'path': str(target.relative_to(OUT)), 'pixels': list(atlas.size),
                   'bytes': target.stat().st_size, 'foot_frames_equal': True,
                   'foot_sha256': hashlib.sha256(original_feet).hexdigest(),
                   'idle_equals_approved': True, 'sweep_degrees': 102,
                   'source': job['hero_sprite']['path'],
                   'note': '仅拆分既有前臂与剑并旋转；头发、服装、身体、双脚保持原图。单次下劈释放，无追加攻击。'})

data['version'] = 'MAP art review 2026-10-29 / identity audit and larger Eileen sweep revision 5'
data_file.write_text('window.MAP_DATA=' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n')
(OUT / 'sources/actions-v5.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))

# A six-key-pose contact sheet, for visual review of every MAP variant.
review = Image.new('RGB', (1152, 1180), '#15232d')
draw = ImageDraw.Draw(review)
font = ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc', 17)
caption_font = ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc', 13)
for row, job in enumerate(data['jobs']):
    action = job['map_action']
    atlas = Image.open(OUT / action['path']).convert('RGBA')
    name = ('胡纳普' if job['hero'] == 'hunapu' else '艾琳') + ' · ' + job['profession']
    name += ' · 持弓' if job.get('bow') else ''
    draw.text((12, row * 236 + 3), name, font=font, fill='#c7e3e5')
    order = ([0, 1, 2, 3, 4, 0] if job.get('bow') else
             [0, 2, 6, 9, 12, 15] if job['hero'] == 'eileen' else [0, 2, 0, 3, 4, 0])
    captions = (['持弓准备', '抬弓', '拉满弓弦', '松弦放箭', '收势', '准备'] if job.get('bow') else
                ['准备', '举剑蓄势', '向前挥出', '下劈完成', '收剑', '准备'] if job['hero'] == 'eileen' else
                ['准备', '举剑蓄势', '挥剑起手', '挥出／释放', '收势', '准备'])
    for col, (pose, caption) in enumerate(zip(order, captions)):
        draw.text((col * 192 + 50, row * 236 + 24), caption, font=caption_font, fill='#9fbac6')
        frame = atlas.crop((pose * 128, 0, pose * 128 + 128, 128)).resize((192, 192), Image.Resampling.NEAREST)
        review.paste(frame, (col * 192, row * 236 + 39), frame)
review.save(OUT / 'sources/actions-v5-review.png', optimize=True)
print(json.dumps(report, ensure_ascii=False))
