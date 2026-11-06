from pathlib import Path
import json
import shutil
import subprocess
import tempfile
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'source/prologue-d00-20261026'
OUT = ROOT / 'actual/assets/prologue-d00-20261026'
OUT.mkdir(parents=True, exist_ok=True)
MAGICK = '/opt/homebrew/bin/magick'
records = json.loads((SOURCE / 'generation.json').read_text())
if (SOURCE / 'generation-selected.json').exists():
    records.update(json.loads((SOURCE / 'generation-selected.json').read_text()))
manifest = []

def run(*args):
    subprocess.run([MAGICK, *map(str, args)], check=True)

def record(path, purpose):
    with Image.open(path) as image:
        dimensions = list(image.size)
        alpha = image.getchannel('A') if 'A' in image.getbands() else None
        box = alpha.getbbox() if alpha is not None else None
    manifest.append({'path': str(path.relative_to(ROOT)), 'purpose': purpose, 'dimensions': dimensions,
                     'bytes': path.stat().st_size, 'alpha_content_bounds': box, 'source_method': 'built-in imagegen' if path.name != 'rowboat.png' else 'existing campaign boat, exact 90-degree rotation'})

def prepare_pose(image_path, target, crop=None):
    # ImageMagick performs ordinary asset cutting/resizing. Pillow only reads
    # alpha measurements to align the feet without clipping the open hand.
    with tempfile.TemporaryDirectory(prefix='d00-pose-') as folder:
        body = Path(folder) / 'body.png'
        raw = Path(folder) / 'raw.png'
        args = [image_path]
        if crop: args += ['-crop', crop, '+repage']
        run(*args, raw)
        with Image.open(raw) as image:
            alpha = image.convert('RGBA').getchannel('A')
            support = alpha.point(lambda value: 255 if value >= 64 else 0).getbbox()
            assert support is not None
            left, top, right, bottom = support
            left, top = max(0, left - 4), max(0, top - 4)
            right, bottom = min(image.width, right + 4), min(image.height, bottom + 4)
        run(raw, '-crop', f'{right-left}x{bottom-top}+{left}+{top}', '+repage', '-resize', '104x104', '+repage', body)
        with Image.open(body) as image:
            alpha = image.convert('RGBA').getchannel('A')
            width, height = image.size
            pixels = alpha.load()
            support = alpha.point(lambda value: 255 if value >= 160 else 0).getbbox()
            foot_y = support[3]
            feet = [x for y in range(max(0, foot_y - 5), foot_y) for x in range(width) if pixels[x, y] >= 160]
            foot_x = (min(feet) + max(feet)) / 2 if feet else width / 2
        x = round(80 - foot_x)
        y = 124 - foot_y
        assert x >= 0 and x + width <= 160 and y >= 0, (target, width, height, x, y)
        run('-size', '160x128', 'canvas:none', body, '-geometry', f'{x:+d}{y:+d}', '-compose', 'over', '-composite', target)
        subprocess.run(['/opt/homebrew/bin/oxipng', '-q', '-o', '3', str(target)], check=True)
        record(target, 'D00专用关键姿势；160×128，脚点(80,124)，以40×32逻辑像素等比显示；不接入战斗动画')

for key, info in records.items():
    shutil.copy2(info['path'], SOURCE / (key + '-source.png'))

for actor in ['hunapu', 'eileen']:
    source = SOURCE / (actor + '-poses-source.png')
    with Image.open(source) as image: width, height = image.size
    cell_w, cell_h = width // 2, height // 2
    for index in range(4):
        prepare_pose(source, OUT / f'{actor}-{index}.png', f'{cell_w}x{cell_h}+{index % 2 * cell_w}+{index // 2 * cell_h}')

herlan_key = 'herlan-clean' if 'herlan-clean' in records else 'herlan'
prepare_pose(SOURCE / (herlan_key + '-source.png'), OUT / 'herlan.png')
for key in ['wrist-knot', 'east-evacuation']:
    path = OUT / (key + '.webp')
    run(SOURCE / (key + '-source.png'), '-resize', '960x540>', '-quality', '92', path)
    record(path, 'D00专用16:9特写／神幕背景，保持比例完整显示，非九宫格复用背景')

boat = OUT / 'rowboat.png'
run(ROOT / 'actual/assets/chapter2/modules/rowboat.png', '-rotate', '90', boat)
record(boat, '复用第二章木船；独立移动与上下船演出，不烘焙到背景')
(OUT / 'manifest.json').write_text(json.dumps({'assets': manifest, 'reference_sizes': {'background': 200000, 'character': 50000}}, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(manifest, ensure_ascii=False))
