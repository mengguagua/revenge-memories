"""Compare approved gallery frames, shipped map atlases and MAP-preview idles."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1]
ROOT = OUT.parents[1]
GALLERY = ROOT / 'art-review/character-expansion-20261018'
s = (GALLERY / 'gallery-data.js').read_text()
gallery = json.loads(s[s.index('{'):s.rindex('}') + 1])
runtime = json.loads((ROOT / 'actual/data/animation_runtime/reviewed.json').read_text())
jobs = json.loads((OUT / 'data.js').read_text().split('=', 1)[1].strip().removesuffix(';'))['jobs']
keys = ['21_ally', '23_ally', 'eileen', 'eileen_promoted']
identity = OUT / 'assets/identity'
identity.mkdir(exist_ok=True)
report = {'revision': 5,
          'finding': '四组地图素材均取图正确；用户截图展示进阶后的破晓勇士与引光剑使。未进阶战士的大头比例来自现行已确认素材。',
          'method': 'RGBA pixel equality for all six map poses; exact preview idle registration; no production changes.',
          'profiles': []}
sheet = Image.new('RGB', (1152, 672), '#15232d')
draw = ImageDraw.Draw(sheet)
font = ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc', 18)
small = ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc', 14)
for i, (job, runtime_key) in enumerate(zip(jobs[:4], keys)):
    live = runtime['metadata']['maps'][runtime_key]['tactical-idle']
    profile = next(p for p in gallery['profiles'] if p['id'] == live['reviewed_profile'])
    shipped = Image.open(ROOT / 'actual' / live['path'].removeprefix('res://')).convert('RGBA')
    preview = Image.open(OUT / job['hero_sprite']['path']).convert('RGBA')
    record = {'case': job['key'], 'profession': job['profession'], 'promoted': job['advanced'],
              'gallery_profile': profile['id'], 'gallery_revision': profile['revision'],
              'runtime_key': runtime_key, 'runtime_path': live['path'],
              'preview_path': job['hero_sprite']['path'], 'frames': []}
    for frame in range(6):
        approved = Image.open(GALLERY / profile['newFrames'][str(frame)]).convert('RGBA')
        crop = (frame * 96, 0, frame * 96 + 96, 96)
        pixels = approved.tobytes()
        same_runtime = shipped.crop(crop).tobytes() == pixels
        same_preview = preview.crop(crop).tobytes() == pixels
        assert same_runtime and same_preview, (job['key'], frame)
        record['frames'].append({'frame': frame, 'runtime_equals_approved': same_runtime,
                                 'preview_equals_approved': same_preview,
                                 'approved_path': str((GALLERY / profile['newFrames'][str(frame)]).relative_to(ROOT)),
                                 'rgba_sha256': hashlib.sha256(pixels).hexdigest()})
    approved = Image.open(GALLERY / profile['newFrames']['0']).convert('RGBA')
    action = Image.open(OUT / job['map_action']['path']).convert('RGBA').crop((16, 16, 112, 112))
    assert action.tobytes() == approved.tobytes(), ('action idle identity', job['key'])
    record['action_idle_equals_approved'] = True
    record['gallery_frame0'] = record['frames'][0]['approved_path']
    for suffix, image in [('approved', approved), ('preview-idle', action)]:
        image.save(identity / (job['key'] + '-' + suffix + '.png'), optimize=True)
    report['profiles'].append(record)
    x, y = (i % 2) * 576, (i // 2) * 336
    stage = '进阶后' if job['advanced'] else '进阶前'
    title = ('胡纳普' if job['hero'] == 'hunapu' else '艾琳') + ' · ' + job['profession'] + ' / ' + stage
    draw.text((x + 16, y + 16), title, font=font, fill='#d5e5e4')
    for col, (caption, image) in enumerate(zip(['已确认对照页', '当前游戏地图', 'MAP待机'],
                                               [approved, shipped.crop((0, 0, 96, 96)), action])):
        draw.text((x + col * 192 + 48, y + 55), caption, font=small, fill='#9fbac6')
        thumb = image.resize((192, 192), Image.Resampling.NEAREST)
        sheet.paste(thumb, (x + col * 192, y + 90), thumb)
    draw.text((x + 16, y + 300), '三者逐像素一致 · 6个原地图姿势全部匹配', font=small, fill='#a9d0bf')
(OUT / 'sources/identity-audit-v5.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
sheet.save(OUT / 'sources/identity-v5-review.png', optimize=True)
print(json.dumps({'profiles': len(report['profiles']), 'original_poses_matched': 24,
                  'action_idles_matched': 4, 'passed': True}, ensure_ascii=False))
