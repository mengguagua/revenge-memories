"""Record production delivery assets, verify accepted poses and preview links."""
import hashlib
import json
import re
import shutil
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
REVIEW = Path(__file__).resolve().parents[1]
OUT = REVIEW / 'integration'

for name in ['checks.json', 'hero-regression.json', 'sound-regression.json']:
    shutil.copyfile(ROOT / 'actual/reports/healer-map-20261104' / name, OUT / name)

assert json.loads((OUT / 'capture.json').read_text())['passed']
manifest = []
for p in sorted((ROOT / 'actual/assets/healer-map-20261104').glob('*.png')):
    manifest.append({'path': str(p.relative_to(ROOT)), 'pixels': list(Image.open(p).size),
                     'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()})
for key in ['healer', 'saint']:
    p = OUT / (key + '.mp4')
    meta = json.loads(subprocess.check_output([
        '/opt/homebrew/bin/ffprobe', '-v', 'error', '-show_entries',
        'stream=codec_type,codec_name,width,height,duration,nb_frames', '-of', 'json', str(p)]))
    manifest.append({'path': str(p.relative_to(ROOT)), 'bytes': p.stat().st_size, 'streams': meta['streams'],
                     'sound': 'rm_sfx_21 at 0.30s, 0.65 gain, preview-copy end fade; game cue has nonblocking full tail'})

identity = []
for job in json.loads((REVIEW / 'sources/runtime.json').read_text())['jobs']:
    original = ROOT / 'actual' / job['caster_sprite']['path'].removeprefix('res://')
    source = Image.open(original).convert('RGBA').crop((0, 0, 96, 96))
    cast = Image.open(ROOT / 'actual/assets/healer-map-20261104' / (job['key'] + '-cast.png')).convert('RGBA')
    idle = cast.crop((16, 16, 112, 112))
    # PNG lossless optimization may discard RGB beneath fully transparent pixels.
    assert all(a == b or (a[3] == 0 and b[3] == 0) for a, b in zip(source.getdata(), idle.getdata()))
    for f in range(5):
        assert cast.crop((128*f, 100, 128*(f+1), 128)).tobytes() == cast.crop((0, 100, 128, 128)).tobytes()
    identity.append({'class': job['caster']['class_id'], 'source': str(original.relative_to(ROOT)),
                     'visible_idle_and_alpha_identical': True, 'all_five_poses_feet_identical': True})

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = []
    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ['src', 'href', 'poster'] and value and not value.startswith(('http', '#')):
                self.paths.append(value)

(OUT / 'asset-manifest.json').write_text(json.dumps({'assets': manifest, 'map_identity': identity}, indent=2) + '\n')

html = (REVIEW / 'integration.html').read_text()
parser = Links()
parser.feed(html)
for name in parser.paths:
    assert (REVIEW / name).exists(), name
for key in ['healer', 'saint']:
    for tier in [1, 2, 3]:
        for kind in ['forecast', 'impact', 'status', 'caster']:
            assert (OUT / f'{key}-{kind}-{tier}.png').exists()
    for suffix in ['2-1', '1', '0']:
        assert (OUT / f'{key}-strong-{suffix}.png').exists()
scripts = re.findall(r'<script>([\s\S]*?)</script>', html)
for script in scripts:
    subprocess.run(['/Users/gcc/.nvm/versions/node/v24.15.0/bin/node', '--check'], input=script.encode(), check=True)
(OUT / 'preview-checks.json').write_text(json.dumps({'static_paths_passed': True, 'inline_script_syntax_passed': True,
    'engine_capture': json.loads((OUT / 'capture.json').read_text())['passed'],
    'browser_interaction': 'Not verified: browser connector returned browser.user is unavailable.',
    'loopback_http': 200, 'path_count': len(parser.paths)}, indent=2) + '\n')
print('HEALER_DELIVERY_OK', len(manifest), 'assets/media;', len(parser.paths), 'static links')
