from pathlib import Path
from PIL import Image
from fractions import Fraction
from urllib.parse import urlsplit, unquote
import json, subprocess, hashlib, ast, re

V = Path(__file__).resolve().parents[1]; R = V.parent
before = json.loads((V / 'reference/gallery-before.json').read_text())
after = json.loads((R / 'demos/gallery-data.json').read_text())
reg = json.loads((V / 'registration.json').read_text())
color_map = {tuple(bytes.fromhex(a[1:])): tuple(bytes.fromhex(b[1:]))
             for a, b in reg['color_map'].items()}
a = {x['id']: x for x in before['actions']}
b = {x['id']: x for x in after['actions']}
assert a.keys() == b.keys()
targets = {k for k, x in b.items() if x['profile'] == 'professions-class-6-enemy-battle'}
for k in a:
    for field in ['frames', 'origin', 'fps', 'contactTick', 'duration']:
        assert a[k][field] == b[k][field], (k, field)
    assert (a[k]['contentDigest'] != b[k]['contentDigest']) == (k in targets), k
assert before['effects'] == after['effects']
all_colors = set(); report_frames = []
for k in [6, 7, 8, 9, 10, 11, 19, 23]:
    p = V / f'deliverables/enemy/frame-{k:03d}.png'
    im = Image.open(p).convert('RGBA')
    old = Image.open(V / f'reference/frame-{k:03d}.png').convert('RGBA')
    assert im.size == old.size == (320, 256)
    assert im.getchannel('A').tobytes() == old.getchannel('A').tobytes()
    assert im.getbbox() == old.getbbox()
    for previous, current in zip(old.getdata(), im.getdata()):
        if previous[3]:
            assert current[:3] == color_map.get(previous[:3], previous[:3])
            all_colors.add(current[:3])
    report_frames.append({'frame': k, 'alpha_and_coordinates_identical': True,
                          'every_visible_pixel_matches_color_map': True,
                          'bytes': p.stat().st_size})
assert len(all_colors) == 13
assert (V / 'deliverables/enemy/frame-023.png').read_bytes() == (
    V / 'deliverables/enemy/frame-019.png').read_bytes()
assert not ({tuple(bytes.fromhex(c[1:])) for c in ['#4b1f2e', '#893143', '#b95b64']} & all_colors)

videos = []
for k in sorted(targets):
    action = b[k]
    for mode in ['video', 'closeVideo']:
        if not action.get(mode):
            continue
        p = R / action[mode]
        assert json.loads(p.with_suffix('.json').read_text())['contentDigest'] == action['contentDigest']
        meta = json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe', '-v', 'error',
            '-select_streams', 'v:0', '-show_entries', 'stream=nb_frames,r_frame_rate,width,height',
            '-of', 'json', str(p)], text=True))['streams'][0]
        assert int(meta['nb_frames']) == len(action['frames'])
        assert abs(float(Fraction(meta['r_frame_rate']))-action['fps']) < .00001
        videos.append({'path': action[mode], **meta})
assert len(videos) == 7
images = []
for p in sorted(V.rglob('*.png')):
    relative = str(p.relative_to(V)); size = list(Image.open(p).size)
    item = {'path': relative, 'pixels': size, 'bytes': p.stat().st_size}
    if relative.startswith('deliverables/'):
        assert item['bytes'] < 50000
        item['purpose'] = 'Candidate enemy battle frames or atlas; not in game package.'
    elif relative.startswith(('source/', 'reference/')):
        item['purpose'] = 'Offline generation or prior-frame reference, excluded from game.'
    else:
        item['purpose'] = 'Visual comparison.'
    if item['bytes'] > 50000:
        item['size_note'] = 'Keep full source/reference quality. Candidate sprites are losslessly optimized below 50KB.'
    images.append(item)
(V / 'image-inventory.json').write_text(json.dumps({'images': images}, indent=2) + '\n')
missing = []
for ref in re.findall(r'(?:href|src)="([^"]+)"', (R / 'index.html').read_text()):
    url = urlsplit(ref)
    if not url.scheme and url.path and not (R / unquote(url.path)).exists():
        missing.append(ref)
assert not missing, missing
for p in [*(V / 'tools').glob('*.py'), R / 'tools/export_gallery.py']:
    ast.parse(p.read_text(), filename=str(p))
assert not subprocess.check_output(['git', 'diff', '--name-only', '--', 'actual'],
                                    cwd=R.parents[1], text=True).strip()
report = {'revision': V.name, 'status': 'pending_user_visual_acceptance',
          'scope': 'Enemy spearman battle palette only. Future regular enemy troop blue-violet standard recorded.',
          'visible_colors': len(all_colors), 'frames': report_frames,
          'all_alpha_geometry_and_prior_width_preserved': True,
          'skin_hair_wood_colors_unchanged': True, 'timelines_contacts_and_effects_preserved': True,
          'changed_actions': len(targets), 'other_actions_preserved': len(b)-len(targets),
          'videos': videos, 'game_files_changed': False, 'new_package_created': False,
          'validation': 'Pixel-by-pixel color-only mapping; same alpha bytes and bounding boxes; source timelines and video frame count/FPS verified. No broad regression needed for recolor.',
          'browser_inspection': 'Not performed; local-file browser restriction respected. Offline light/dark and rendered battle comparisons checked.',
          'style_standard': '../catalog/enemy-troop-palette.json'}
(V / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'pass': True, 'enemy_actions': len(targets), 'other_actions_preserved': len(b)-len(targets),
                  'videos': len(videos), 'visible_colors': len(all_colors)}))
