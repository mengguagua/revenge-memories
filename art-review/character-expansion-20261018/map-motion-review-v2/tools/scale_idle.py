"""Apply one proportional nearest-neighbour transform to all three idle poses."""
from pathlib import Path
from PIL import Image
import json, subprocess

V = Path(__file__).resolve().parents[1]
G = '/opt/homebrew/bin/magick'
src = V / 'deliverables/hunapu'
out = V / 'deliverables/hunapu-idle-size2'
out.mkdir(parents=True, exist_ok=True)
# One shared crop includes all poses. Do not trim or centre each pose separately.
crop = (25, 9, 95, 80)
ratio = 64 / 71
offset = (27, 16)
def transform(source, target):
    subprocess.run([G, str(source), '-crop', '70x71+25+9', '+repage',
        '-filter', 'point', '-resize', f'{ratio * 100:.10f}%',
        '-background', 'none', '-gravity', 'northwest', '-extent', '96x96-27-16',
        '-background', 'black', '-alpha', 'background', str(target)], check=True)

files = []
for slot in (8, 9, 10):
    target = out / f'frame-{slot:02}.png'
    transform(src / target.name, target)
    im = Image.open(target).convert('RGBA')
    bbox = im.getbbox()
    assert im.size == (96, 96) and bbox[3] == 80 and bbox[3] - bbox[1] == 64, bbox
    assert set(im.getchannel('A').getdata()) == {0, 255}
    assert len({p[:3] for p in im.getdata() if p[3]}) == 4
    files.append({'slot': slot, 'path': str(target.relative_to(V)), 'bbox': list(bbox)})

# Transform the same motion mask with the same sampling. Fixed pixels must remain
# identical after resizing, including the stationary legs and foot baseline.
mask = out / 'movable-08.png'
transform(V / 'layers/hunapu/movable-08.png', mask)
m = Image.open(mask).convert('RGBA')
allowed = [p[0] if p[3] else 0 for p in m.getdata()]
base = Image.open(out / 'frame-08.png').convert('RGBA')
checks = []
for slot in (9, 10):
    im = Image.open(out / f'frame-{slot:02}.png').convert('RGBA')
    fixed = sum(a != b for a, b, moving in zip(base.getdata(), im.getdata(), allowed) if not moving)
    changed = sum(a != b for a, b in zip(base.getdata(), im.getdata()))
    feet = base.crop((0, 68, 96, 96)).tobytes() == im.crop((0, 68, 96, 96)).tobytes()
    assert fixed == 0 and changed > 0 and feet, (slot, fixed, changed, feet)
    checks.append({'slot': slot, 'fixed_pixels_changed': fixed, 'moving_pixels_changed': changed, 'legs_feet_equal': feet})
report = {'requested_change': 'Uniformly reduce male tactical idle size only',
    'scale': ratio, 'shared_source_crop': list(crop), 'scaled_crop_size': [63, 64],
    'destination_offset': list(offset), 'canvas_size': [96, 96],
    'source_native_height': 16, 'previous_redraw_height': 71, 'new_redraw_height': 64,
    'foot_baseline_before_after': [80, 80], 'resampling': 'nearest-neighbour',
    'files': files, 'fixed_region_checks': checks}
(V / 'idle-size-qa.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(report, ensure_ascii=False))
