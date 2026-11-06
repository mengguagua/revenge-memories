"""Cut ImageGen inbetweens to the existing 16px map-body scale, feet aligned."""
from pathlib import Path
import json
import subprocess
import tempfile
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'source/prologue-small-20261026'
OUT = ROOT / 'actual/assets/prologue-small-20261026'
OUT.mkdir(parents=True, exist_ok=True)
MAGICK = '/opt/homebrew/bin/magick'

def run(*args):
    subprocess.run([MAGICK, *map(str, args)], check=True)

def body_bounds(alpha):
    # Measurements only: ignore isolated generated flecks outside the body.
    pixels = alpha.load()
    remaining = {(x,y) for y in range(alpha.height) for x in range(alpha.width) if pixels[x,y] >= 160}
    largest = []
    while remaining:
        todo = [remaining.pop()]
        component = []
        while todo:
            x,y = todo.pop()
            component.append((x,y))
            for point in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
                if point in remaining:
                    remaining.remove(point)
                    todo.append(point)
        if len(component) > len(largest):
            largest = component
    return min(x for x,y in largest), min(y for x,y in largest), max(x for x,y in largest)+1, max(y for x,y in largest)+1

records = []
actors = {}
names = {
    'hunapu': ['站立', '起步', '跨步', '抬臂阻挡', '挡击后仰', '收势', '开始伸手', '伸手停点'],
    'eileen': ['束腕', '挣脱起势', '挣开', '施法准备', '抬手', '释放', '收势', '望向赫兰'],
    'herlan': ['站立', '呼吸', '察觉', '收肩', '抬手', '回稳', '放手', '站定'],
}
for actor in names:
    source = SOURCE / f'{actor}-atlas-source.png'
    slim = actor == 'herlan' and (SOURCE / 'herlan-slim-atlas-source.png').exists()
    if slim:
        source = SOURCE / 'herlan-slim-atlas-source.png'
    with Image.open(source) as image:
        w, h = image.size
    # Cell bounds follow the generated 4x2 layout, including odd source sizes.
    with tempfile.TemporaryDirectory(prefix='d00-small-') as temp:
        frames = []
        measurements = []
        for n in range(8):
            x0, x1 = round(n % 4 * w / 4), round((n % 4 + 1) * w / 4)
            y0, y1 = round(n // 4 * h / 2), round((n // 4 + 1) * h / 2)
            raw = Path(temp) / f'raw-{n}.png'
            body = Path(temp) / f'body-{n}.png'
            frame = Path(temp) / f'frame-{n}.png'
            # Remove only the generated very-low-alpha surrounding haze.
            run(source, '-crop', f'{x1-x0}x{y1-y0}+{x0}+{y0}', '+repage',
                '-channel', 'A', '-threshold', '25%', '+channel', raw)
            with Image.open(raw) as image:
                box = body_bounds(image.getchannel('A'))
                assert box
            left, top, right, bottom = box
            target_height = [64, 64, 64, 62, 60, 62, 64, 64][n] if actor == 'hunapu' else 64
            run(raw, '-crop', f'{right-left}x{bottom-top}+{left}+{top}', '+repage',
                '-filter', 'point', '-resize', f'x{target_height}', body)
            with Image.open(body) as image:
                alpha = image.getchannel('A')
                width, height = image.size
                feet = [x for y in range(height-3, height) for x in range(width) if alpha.getpixel((x, y)) >= 160]
                foot_x = (min(feet) + max(feet) + 1) / 2
            x, y = round(64-foot_x), 96-height
            assert 0 < x and x+width < 128 and y >= 24
            run('-size', '128x96', 'canvas:none', body, '-geometry', f'+{x}+{y}', '-composite', frame)
            frames.append(frame)
            measurements.append({'frame': n, 'pose': names[actor][n], 'content': [x, y, width, height], 'logical_height': height/4})
        target = OUT / ('herlan-slim.png' if slim else f'{actor}.png')
        run('-size', '512x192', 'canvas:none', *[part for n, f in enumerate(frames) for part in (f, '-geometry', f'+{n%4*128}+{n//4*96}', '-composite')], target)
        subprocess.run(['/opt/homebrew/bin/pngquant', '--quality=90-100', '--speed', '1', '--nofs', '--force', '--output', str(target), str(target)], check=True)
        subprocess.run(['/opt/homebrew/bin/oxipng', '-q', '-o', '3', str(target)], check=True)
    records.append({'actor': actor, 'path': str(target.relative_to(ROOT)), 'purpose': 'D00与D31专用小地图人物，8帧过渡；非战斗动作',
                    'dimensions': [512,192], 'bytes': target.stat().st_size, 'frames': measurements,
                    'source_method': 'built-in imagegen; ImageMagick grid cutting, alpha-haze cleanup, proportional resizing and foot alignment'})
    actors[actor] = {'path': 'res://' + str(target.relative_to(ROOT/'actual')), 'frame_size': [128,96], 'frames': 8, 'columns': 4,
                     'anchor': [16,24], 'native_density': 4, 'body_scale': '16px-small-map', 'poses': names[actor]}
(OUT/'manifest.json').write_text(json.dumps({'assets': records, 'guard_reuse': 'reviewed maps 22_enemy tactical-idle/tactical-walk, unchanged blue-purple bastion guardian'}, ensure_ascii=False, indent=2)+'\n')
(ROOT/'actual/data/prologue_cast.json').write_text(json.dumps({'version': 1, 'actors': actors, 'guard_class': 22, 'guard_side': 'enemy'}, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(records, ensure_ascii=False))
