from pathlib import Path
from PIL import Image
from fractions import Fraction
import json, subprocess, hashlib, ast

V = Path(__file__).resolve().parents[1]; R = V.parent
before = json.loads((V / 'reference/gallery-before.json').read_text())
after = json.loads((R / 'demos/gallery-data.json').read_text())
reg = json.loads((V / 'registration.json').read_text())
a = {x['id']: x for x in before['actions']}
b = {x['id']: x for x in after['actions']}
assert a.keys() == b.keys()
ids = {k for k, x in b.items() if x['profile'] in
       ['professions-class-6-ally-battle', 'professions-class-6-enemy-battle']}
for k in a:
    for field in ['frames', 'origin', 'fps', 'contactTick', 'duration']:
        assert a[k][field] == b[k][field], (k, field)
    assert (a[k]['contentDigest'] != b[k]['contentDigest']) == (k in ids), k
assert before['effects'] == after['effects']

colors_report = {}; images = []
for side, keys in [('ally', [0, 1, 2, 3, 4, 5, 12]),
                   ('enemy', [6, 7, 8, 9, 10, 11, 19])]:
    palette = {tuple(bytes.fromhex(c[1:])) for c in reg['palettes'][side]}
    all_colors = set(); old_colors = set(); frame_report = []
    for k in keys:
        p = V / f'deliverables/{side}/frame-{k:03d}.png'
        im = Image.open(p).convert('RGBA')
        previous = Image.open(V / f'reference/{side}-{k}.png').convert('RGBA')
        assert im.size == previous.size == (320, 256)
        record = next(x for x in reg['records'] if x['side'] == side and x['source_frame'] == k)
        box = im.getbbox()
        assert box[2]-box[0] == record['target_size'][0]
        assert box[3]-box[1] == record['target_size'][1]
        assert record['height_preserved'] and abs(record['width_factor'] - 1.08) < .005
        cs = {c[:3] for c in im.getdata() if c[3]}
        all_colors |= cs
        old_colors |= {c[:3] for c in previous.getdata() if c[3] >= 128}
        assert cs <= palette and set(im.getchannel('A').getdata()) == {0, 255}
        feet = im.getchannel('A').crop((0, record['foot_measurement_top'], 320, 256)).getbbox()
        center = (feet[0]+feet[2])/2
        assert abs(center-record['target_foot_anchor'][0]) <= .5
        assert box[3] == record['target_foot_anchor'][1] == 256
        frame_report.append({'frame': k, 'visible_colors': len(cs), 'bounds': list(box),
                             'width_factor': record['width_factor'],
                             'foot_anchor': [center, box[3]]})
    assert len(all_colors) == 14 and len(old_colors) > len(all_colors)
    idle = 12 if side == 'ally' else 19
    assert (V / f'deliverables/{side}/frame-023.png').read_bytes() == (
        V / f'deliverables/{side}/frame-{idle:03d}.png').read_bytes()
    colors_report[side] = {'shared_colors_before': len(old_colors),
                          'shared_colors_after': len(all_colors),
                          'palette': reg['palettes'][side], 'frames': frame_report}

for p in sorted((V / 'deliverables').rglob('*.png')):
    assert p.stat().st_size < 50000
    images.append({'path': str(p.relative_to(R)), 'pixels': list(Image.open(p).size),
                   'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()})

video_probes = []
for k in sorted(ids):
    action = b[k]
    assert action['video'] and action['still']
    for mode in ['video', 'closeVideo']:
        if not action.get(mode):
            continue
        p = R / action[mode]
        assert json.loads(p.with_suffix('.json').read_text())['contentDigest'] == action['contentDigest']
        meta = json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe', '-v', 'error',
            '-select_streams', 'v:0', '-show_entries', 'stream=nb_frames,r_frame_rate,width,height',
            '-of', 'json', str(p)], text=True))['streams'][0]
        assert int(meta['nb_frames']) == len(action['frames'])
        assert abs(float(Fraction(meta['r_frame_rate'])) - action['fps']) < .00001
        video_probes.append({'path': action[mode], **meta, 'bytes': p.stat().st_size})

validation = json.loads((R / 'demos/validation-report.json').read_text())
assert validation['pass']
assert not subprocess.check_output(['git', 'diff', '--name-only', '--', 'actual'],
                                    cwd=R.parents[1], text=True).strip()
for p in [*(V / 'tools').glob('*.py'), R / 'tools/export_gallery.py']:
    ast.parse(p.read_text(), filename=str(p))
report = {'revision': V.name, 'status': 'pending_user_visual_acceptance',
          'scope': '双方枪兵战斗场景横向加宽与统一减色；未接入游戏',
          'method': 'Existing pose pixels preserved; only horizontal resize, fixed palette remap and whole-frame registration. Generated sheet is a simplification reference, not replacement poses.',
          'colors': colors_report, 'all_source_timelines_and_contacts_preserved': True,
          'height_preserved': True, 'width_target_factor': 1.08,
          'foot_anchor_max_error_4x_pixels': .5, 'original_effects_preserved': True,
          'changed_actions': len(ids), 'unchanged_actions': len(b)-len(ids),
          'videos': video_probes, 'images': images,
          'geometry_validation': {'pass': True, 'checks': validation['real_alpha_extent_checks'],
                                  'errors': len(validation['geometry_errors'])},
          'game_files_changed': False, 'new_package_created': False,
          'browser_visual_inspection': 'Not performed; prior local-file browser restriction honored. Offline dark/light sprite and key-moment comparisons used.',
          'notes': ['Faction costumes preserved: blue-gray allied armor, burgundy enemy armor, divided skirt armor and exposed thighs.',
                    '14 shared opaque colors per faction; no dither or new attack effects.',
                    'Native ordinary spear actions and reactions only. Previously excluded javelin variants remain excluded.',
                    'Disconnected original top-row noise outside the enemy preparation pose was excluded during alpha crop.']}
(V / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'pass': True, 'actions': len(ids), 'other_actions_preserved': len(b)-len(ids),
                  'videos': len(video_probes), 'colors': {k: v['shared_colors_after']
                   for k, v in colors_report.items()}}, ensure_ascii=False))
