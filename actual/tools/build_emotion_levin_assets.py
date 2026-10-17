#!/usr/bin/env python3
"""Compile cumulative native BG uploads and versioned 48px expressions."""
from pathlib import Path
import hashlib, json, sys
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'tools'))
from extract_full_graphics import Source, bg_entries
from build_clarity_assets import battle_cell, HEADS, C, save

SOURCE = ROOT / 'source/emotion-levin-0.5.3'
REPORT = ROOT / 'reports/emotion-levin-0.5.3'
OUT = ROOT / 'assets/hunapu-0.5.3'
FACES = ROOT / 'assets/portraits-0.5.3'
EXPRESSIONS = ['present_concern', 'present_firm', 'memory_grief', 'memory_resolve', 'memory_anger', 'victory_relief']
EMOTIONS = {
    '……艾琳？把绳子解开。': 'concern',
    '你先告诉我发生了什么。': 'firm',
    '名字还没刻完。': 'grief',
    '科兰回旧塔堡了。我明天走。': 'resolve',
    '……我先送他们出去。你把弓带上。': 'resolve',
    '科兰扣了粮，还把领粮的人抓走了。': 'anger',
    '我会去旧塔堡。我要他说明凯尔的事。': 'resolve',
    '凯尔回营的时候，你答应过放人。': 'resolve',
    '所以你把他挂在营门外。': 'anger',
}

def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

def main():
    for directory in [SOURCE, REPORT, OUT / 'frames', FACES]: directory.mkdir(parents=True, exist_ok=True)
    src = Source(ROOT.parent / '.reference/fe2-source-956365ef')
    graphics = json.loads((ROOT / 'data/legacy/graphics.json').read_text())
    entry = graphics['battle']['class_21_ally']
    bank = src.b[15]['L0FE436']['db'][20]
    typ = src.b[15]['L0FE44C']['db'][20]
    table = src.ptr(bank, 0xbffa)
    maps = src.ptr(bank, 0xbffc)
    poses = src.b[bank][src.b[bank][maps]['dw'][typ]]['db']
    tiles = src.tiles[src.b[5]['L058E98']['db'][20]]
    palette_ref = src.b[5]['L05BCF1']['dw'][entry['source_palette_id']]
    palette = src.b[5][palette_ref]['db'][:4]
    # A BG pose is a tile upload, not a replacement picture. Transparent
    # tiles explicitly erase their 8x8 area; all unaddressed tiles persist.
    canvas = Image.new('RGBA', (80, 72))
    sheet = Image.open(ROOT / 'assets/hunapu-0.5.2/battle.png').convert('RGBA')
    writes = []
    native = {}
    for pose in [0, 60, 61, 62, 63, 64]:
        ref = src.b[bank][table]['dw'][poses[pose]]
        entries = bg_entries(src.b[bank][ref]['db'], tiles, palette)
        for x, y, tile in entries: canvas.paste(tile, (x + 40, y + 32))
        frame = pose + 60
        save(canvas, SOURCE / f'levin-source-{frame}.png')
        if pose == 0: continue
        HEADS[frame] = (45, 32, 53, 40)
        colored = battle_cell(canvas, frame)
        if frame in [123, 124]:
            for y in range(30):
                for x in range(80):
                    pixel = canvas.getpixel((x, y))
                    if pixel[3] and pixel[:3] != (0, 0, 0): colored.putpixel((x, y), (*C['steel'], 255))
        assert colored.getchannel('A').tobytes() == canvas.getchannel('A').tobytes()
        sheet.paste(colored, (frame * 80, 0))
        native[frame] = canvas.copy()
        save(colored, SOURCE / f'levin-personal-{frame}.png')
        writes.append({'frame': frame, 'source_upload': ref, 'tiles_written': len(entries), 'opaque_pixels': sum(p[3] > 0 for p in canvas.getdata()), 'native_alpha_sha256': hashlib.sha256(canvas.getchannel('A').tobytes()).hexdigest()})
    save(sheet, OUT / 'battle.png')
    for frame in range(133): save(sheet.crop((frame * 80, 0, (frame + 1) * 80, 72)), OUT / 'frames' / f'battle-{frame}.png')
    before = Image.open(ROOT / 'assets/hunapu-0.5.2/battle.png').convert('RGBA')
    for frame in range(133):
        if 120 <= frame <= 124: continue
        box = (frame * 80, 0, (frame + 1) * 80, 72)
        assert sheet.crop(box).tobytes() == before.crop(box).tobytes()
    assert all(sum(native[frame].getpixel((x, y))[3] > 0 for y in range(40, 65) for x in range(80)) > 90 for frame in native)
    visuals = json.loads((ROOT / 'data/hunapu_visuals.json').read_text())
    visuals['version'] = '0.5.3'
    visuals['battle']['path'] = 'res://assets/hunapu-0.5.3/battle.png'
    visuals['cumulative_bg_frames'] = [120, 121, 122, 123, 124]
    visuals['registration'] = 'Original native geometry and timing. Levin BG uploads60..64 compiled cumulatively, preserving body and explicit blank tile erasure; every other frame is pixel-identical to 0.5.2.'
    write(ROOT / 'data/hunapu_visuals.json', visuals)
    portraits = json.loads((ROOT / 'data/portraits.json').read_text())
    rows = []
    preview = Image.new('RGB', (1440, 262), (31, 44, 54)); draw = ImageDraw.Draw(preview)
    for i, expression in enumerate(EXPRESSIONS):
        raw = SOURCE / f'hunapu_{expression}-generated.png'
        face = Image.open(raw).convert('RGB').resize((48, 48), Image.Resampling.NEAREST)
        face = face.quantize(colors=24, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        dest = FACES / f'hunapu_{expression}.png'; save(face, dest)
        key = 'hunapu_' + expression
        phase = expression.split('_')[0]
        record = dict(portraits['assets']['hunapu_' + phase])
        record.update(path='res://' + str(dest.relative_to(ROOT)), expression=expression.split('_')[1], facial_features='Readable shaped mouth, eyebrows and eyes; native 48px grid, no horizontal-bar mouth.', colors=24)
        portraits['assets'][key] = record
        rows.append({'key': key, 'path': str(dest.relative_to(ROOT)), 'pixels': [48, 48], 'bytes': dest.stat().st_size, 'opaque_colors': len(face.getcolors(256)), 'source': str(raw.relative_to(ROOT)), 'emotion': record['expression']})
        preview.paste(face.convert('RGB').resize((240, 240), Image.Resampling.NEAREST), (i * 240, 0)); draw.text((i * 240 + 6, 245), expression, fill='white')
    for phase, expression in [('present', 'firm'), ('memory', 'resolve'), ('victory', 'relief')]:
        portraits['assets']['hunapu_' + phase] = dict(portraits['assets']['hunapu_' + phase + '_' + expression])
    portraits['version'] = '0.5.3'; portraits['dialogue_emotions'] = EMOTIONS
    write(ROOT / 'data/portraits.json', portraits)
    campaign_path = ROOT / 'data/campaign.json'; campaign = json.loads(campaign_path.read_text()); dialogue = []
    for scene, pages in campaign['scenes'].items():
        for page in pages:
            if page.get('speaker') == '胡纳普':
                page['emotion'] = EMOTIONS[page['text']]
                dialogue.append(dict(scene=scene, **page))
    write(campaign_path, campaign)
    save(preview, REPORT / 'expression-design.png')
    plate = Image.new('RGB', (1600, 310), (31, 44, 54)); d = ImageDraw.Draw(plate)
    for i, frame in enumerate(range(120, 125)):
        cell = sheet.crop((frame * 80, 0, (frame + 1) * 80, 72)).resize((320, 288), Image.Resampling.NEAREST)
        plate.paste(cell, (i * 320, 0), cell); d.text((i * 320 + 8, 292), str(frame) + ' cumulative BG', fill='white')
    save(plate, REPORT / 'levin-body-design.png')
    write(REPORT / 'portrait-manifest.json', rows)
    write(REPORT / 'source-checks.json', {'passed': True, 'source_revision': '956365ef', 'body_uploads': writes, 'unchanged_frame_count': 128, 'corrected_frames': [120, 121, 122, 123, 124], 'damage_contacts': 'Original program22: one contact at tick226, 298 total ticks. No gameplay or effect timing changes.', 'dialogue': dialogue, 'story_relation': '凯尔是胡纳普的兄长；D11悲伤表情对应刻兄长纪念碑。'})
    assets = []
    for path in [OUT / 'battle.png'] + sorted((OUT / 'frames').glob('*.png')):
        im = Image.open(path).convert('RGBA'); colors = {p[:3] for p in im.getdata() if p[3]}
        assert colors <= set(C.values())
        assets.append({'path': str(path.relative_to(ROOT)), 'pixels': list(im.size), 'bytes': path.stat().st_size, 'opaque_colors': len(colors), 'purpose': 'Hunapu native battle atlas/frame'})
    write(REPORT / 'asset-manifest.json', assets)
    print(json.dumps({'body_frames': len(writes), 'expressions': len(rows), 'dialogue_annotations': len(dialogue), 'assets': len(assets)}))

if __name__ == '__main__': main()
