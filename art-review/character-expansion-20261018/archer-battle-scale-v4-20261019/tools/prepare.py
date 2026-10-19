"""User-requested 90% uniform scaling of existing sprites; no artwork regeneration."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import copy
import hashlib
import json
import shutil
import subprocess

V = Path(__file__).resolve().parents[1]
R = V.parent
G = R.parents[1] / 'actual'
PREVIOUS = R / 'archer-battle-light-armor-v3-20261019'
SCALE = 0.90
REPORT = G / 'reports/archer-battle-scale-test-20261019'


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def visible_hash(image):
    pixels = bytearray(image.convert('RGBA').tobytes())
    for i in range(0, len(pixels), 4):
        if pixels[i + 3] == 0:
            pixels[i:i + 3] = b'\0\0\0'
    return hashlib.sha256(pixels).hexdigest()


def main():
    reference = V / 'reference'
    reference.mkdir(exist_ok=True)
    (V / 'reviews').mkdir(exist_ok=True)
    (REPORT / 'before').mkdir(parents=True, exist_ok=True)
    gallery = read(R / 'demos/gallery-data.json')
    runtime_path = G / 'data/reviewed_animations.json'
    before = read(runtime_path)
    if (reference / 'gallery-before.json').exists():
        raise RuntimeError('Revision already prepared; keep the prior registration intact.')
    shutil.copy2(R / 'demos/gallery-data.json', reference / 'gallery-before.json')
    shutil.copy2(runtime_path, REPORT / 'before/reviewed_animations.json')
    data = copy.deepcopy(before)
    records, inventory = [], []
    for side, keys, pivot, head_x in [('ally', [1, 4, 5], [208, 256], [190, 232]),
                                     ('enemy', [1, 5, 6], [144, 256], [127, 172])]:
        out = V / 'deliverables' / side
        out.mkdir(parents=True, exist_ok=True)
        mapping_path = R / f'professions/class-12-{side}/battle/frame_mapping.json'
        mapping = read(mapping_path)
        assert mapping['revision'] == PREVIOUS.name
        shutil.copy2(mapping_path, reference / f'{side}-mapping-before.json')
        frames = {}
        for n in keys:
            old_path = PREVIOUS / f'deliverables/{side}/frame-{n:03d}.png'
            old = Image.open(old_path).convert('RGBA')
            shutil.copy2(old_path, reference / f'{side}-{n}.png')
            # One transform for every pose, about the registered sole baseline.
            inverse = (1 / SCALE, 0, pivot[0] * (1 - 1 / SCALE),
                       0, 1 / SCALE, pivot[1] * (1 - 1 / SCALE))
            image = old.transform(old.size, Image.Transform.AFFINE, inverse,
                                  Image.Resampling.NEAREST)
            target = out / f'frame-{n:03d}.png'
            image.save(target, optimize=True)
            frames[str(n)] = image
            colors = {p for p in old.getdata() if p[3]}
            assert {p for p in image.getdata() if p[3]} <= colors
            assert set(image.getchannel('A').getdata()) == {0, 255}
            assert image.getbbox()[3] == 256
            feet = image.crop((0, 247, 320, 256)).getbbox()
            # Cropped foot silhouette may be asymmetric; the transform pivot itself is exact.
            def top_in_head(im, left, right):
                return im.crop((left, 80, right, 164)).getbbox()[1] + 80
            old_head = top_in_head(old, *head_x)
            new_x = [round(pivot[0] + SCALE * (x - pivot[0])) for x in head_x]
            new_head = top_in_head(image, *new_x)
            records.append({'side': side, 'source_frame': n, 'scale': SCALE,
                            'pivot_4x': pivot, 'old_bounds': old.getbbox(),
                            'new_bounds': image.getbbox(), 'old_head_top': old_head,
                            'new_head_top': new_head, 'new_body_height_4x': 256 - new_head,
                            'spearman_body_height_4x': 128,
                            'body_height_error_native_pixels': abs(256 - new_head - 128) / 4,
                            'foot_center_4x': (feet[0] + feet[2]) / 2,
                            'visible_rgba_sha256': visible_hash(image)})
        compact = Image.new('RGBA', (320 * len(keys), 256))
        for i, n in enumerate(keys): compact.paste(frames[str(n)], (320 * i, 0))
        compact.save(out / 'battle-atlas.png', optimize=True)
        # The free-flying arrows keep the accepted image, native size and trajectory.
        shutil.copy2(PREVIOUS / f'deliverables/{side}/flying-arrow.png', out / 'flying-arrow.png')
        profile = next(p for p in gallery['profiles'] if p['id'] == f'professions-class-12-{side}-battle')
        art = data['battle'][f'12_{side}']
        atlas_path = G / art['path'].removeprefix('res://')
        shutil.copy2(atlas_path, REPORT / 'before' / atlas_path.name)
        atlas = Image.new('RGBA', (art['columns'] * 320,
                                  ((art['frames'] + art['columns'] - 1) // art['columns']) * 256))
        for slot, image in frames.items():
            n = int(slot); atlas.paste(image, ((n % art['columns']) * 320, (n // art['columns']) * 256))
        atlas.save(atlas_path, optimize=True)
        art['art_revision'] = V.name
        item = {'profile': profile['id'], 'key': f'12_{side}', 'revision': V.name,
                'path': art['path'], 'frame_size': [320, 256], 'size': list(atlas.size),
                'frames': art['frames'], 'columns': art['columns'],
                'frame_hashes': {n: visible_hash(im) for n, im in frames.items()},
                'effect_aliases': art['effect_aliases'], 'effects': [],
                'attack_variants': len(art['reviewed_variants'])}
        for original_id, scoped_id in art['effect_aliases'].items():
            effect = data['sprites'][scoped_id]
            image = Image.open(G / effect['path'].removeprefix('res://')).convert('RGBA')
            item['effects'].append({'id': scoped_id, 'source_id': original_id, 'path': effect['path'],
                                    'visible_rgba_sha256': visible_hash(image)})
        inventory.append(item)
        base = f'../../../{V.name}/deliverables/{side}/'
        mapping['frame_mapping'] = {str(n): base + f'frame-{n:03d}.png' for n in keys}
        mapping['records'] = [{**rec, 'path': base + f'frame-{rec["source_frame"]:03d}.png',
                               'output_path': base + f'frame-{rec["source_frame"]:03d}.png',
                               'kind': 'uniform_90_percent_existing_pixel_art',
                               'scale_registration': '../../../' + V.name + '/registration.json'}
                              for rec in records if rec['side'] == side]
        mapping.update(revision=V.name, output_atlas=base + 'battle-atlas.png',
                       qa_report='../../../' + V.name + '/verification.json',
                       status='runtime_integrated_for_device_review', runtime_integrated=True,
                       art_review='Uniform scale correction requested by user; pending device acceptance.',
                       review_note='双方弓箭手人物与持弓整体等比缩至90%，以枪兵约32原生像素的人物高度对齐；固定脚底锚点，简洁配色、姿势、动作与命中时序保留。飞箭素材、轨迹及地图形象保持。已接入0.8.11测试包，等待实机验收。',
                       runtime_integration={'version': '0.8.11', 'device_review_pending': True,
                                            'report': '../../../../../actual/reports/archer-battle-scale-test-20261019/delivery.json'},
                       batches=[{'id': '枪兵与弓箭手等高对照', 'review': '../../../' + V.name + '/reviews/height-comparison-dark.png'}])
        mapping['foot_anchor_registration'] = {'method': 'Uniform 0.90 nearest-neighbor affine transform about fixed foot pivot', 'pivot': pivot, 'scale': SCALE, 'record': '../../../' + V.name + '/registration.json'}
        save(mapping_path, mapping)
    for p in [*V.joinpath('deliverables').rglob('*.png'),
              *(G / i['path'].removeprefix('res://') for i in inventory)]:
        subprocess.run(['/opt/homebrew/bin/oxipng', '-q', '-o', '3', str(p)], check=True)
    for i in inventory:
        p = G / i['path'].removeprefix('res://'); i.update(bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    for section in ['maps', 'map_revisions', 'variants', 'sprites']:
        assert data[section] == before[section]
    assert {k: v for k, v in data['battle'].items() if not k.startswith('12_')} == {k: v for k, v in before['battle'].items() if not k.startswith('12_')}
    runtime_path.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')))
    save(V / 'registration.json', {'scale': SCALE, 'sampling': 'nearest, no colors added',
                                  'records': records, 'body_reference': 'Spearman head-to-sole 128 pixels at density 4; exclude weapon tips.'})
    save(REPORT / 'import.json', {'version': '0.8.11', 'inventory': inventory, 'body_profiles': 2,
                                 'source_frame_slots_checked': 6, 'source_attack_variants': 18,
                                 'scoped_arrow_textures': 2, 'scale': SCALE,
                                 'maps_variants_effects_unchanged': True, 'gameplay_logic_changed': False})
    comparisons(gallery)
    print(json.dumps({'scale': SCALE, 'frames': 6, 'all_body_heights_native': [x['new_body_height_4x'] / 4 for x in records]}, ensure_ascii=False))


def comparisons(gallery):
    # Three same-baseline figures per faction: reference, old archer, corrected archer.
    font_path = next(p for p in ['/System/Library/Fonts/PingFang.ttc',
                                 '/System/Library/Fonts/STHeiti Light.ttc'] if Path(p).is_file())
    font = ImageFont.truetype(font_path, 20)
    for name, bg, fg in [('dark', '#202d35', '#e9f0f0'), ('light', '#dcded8', '#27323c')]:
        canvas = Image.new('RGBA', (1160, 700), bg); draw = ImageDraw.Draw(canvas)
        for row, side in enumerate(['ally', 'enemy']):
            gun = next(p for p in gallery['profiles'] if p['id'] == f'professions-class-6-{side}-battle')
            gun_frame = '12' if side == 'ally' else '19'
            source = [Image.open(R / gun['newFrames'][gun_frame]).convert('RGBA'),
                      Image.open(PREVIOUS / f'deliverables/{side}/frame-001.png').convert('RGBA'),
                      Image.open(V / f'deliverables/{side}/frame-001.png').convert('RGBA')]
            pivots = [196 if side == 'ally' else 124, 208 if side == 'ally' else 144, 208 if side == 'ally' else 144]
            top = 48 + row * 330
            for col, (image, px) in enumerate(zip(source, pivots)):
                center = 190 + col * 386
                canvas.alpha_composite(image, (center - px, top))
                label = ['枪兵基准', '弓箭手 · 修改前', '弓箭手 · 90%'][col]
                label = ('盟军 · ' if side == 'ally' else '敌军 · ') + label
                draw.text((center, top - 12), label, font=font, fill=fg, anchor='ms')
        canvas.convert('RGB').save(V / f'reviews/height-comparison-{name}.png', optimize=True)


if __name__ == '__main__': main()
