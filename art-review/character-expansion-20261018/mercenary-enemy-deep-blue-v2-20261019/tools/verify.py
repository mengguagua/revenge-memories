from pathlib import Path
from PIL import Image
from fractions import Fraction
import json, subprocess, ast

V = Path(__file__).resolve().parents[1]; R = V.parent
a = {x['id']: x for x in json.loads((V / 'reference/gallery-before.json').read_text())['actions']}
after = json.loads((R / 'demos/gallery-data.json').read_text()); b = {x['id']: x for x in after['actions']}
assert a.keys() == b.keys()
targets = {k for k, x in b.items() if x['profile'] == 'professions-class-8-enemy-battle'}
for k in a:
    for field in ['frames', 'origin', 'fps', 'contactTick', 'duration']:
        assert a[k][field] == b[k][field], (k, field)
    assert (a[k]['contentDigest'] != b[k]['contentDigest']) == (k in targets), k
assert json.loads((V / 'reference/gallery-before.json').read_text())['effects'] == after['effects']
reg = json.loads((V / 'registration.json').read_text())
cmap = {tuple(bytes.fromhex(a[1:])): tuple(bytes.fromhex(b[1:]))
        for a, b in reg['color_map'].items()}
skin = {tuple(bytes.fromhex(c)) for c in ['c08c62', 'efbd8b', 'f2d3a4']}
frames = []; changed_pixels = 0
for k in [0, 1, 2, 3, 4, 5, 6, 7, 8, 15, 16]:
    p = V / f'deliverables/enemy/frame-{k:03d}.png'
    im = Image.open(p).convert('RGBA'); old = Image.open(V / f'reference/frame-{k:03d}.png').convert('RGBA')
    assert im.size == old.size == (320, 256)
    assert im.getchannel('A').tobytes() == old.getchannel('A').tobytes()
    assert im.getbbox() == old.getbbox()
    record = {'frame': k, 'alpha_and_coordinates_identical': True, 'bytes': p.stat().st_size}
    if k in [0, 1, 2, 3, 4, 5, 7, 16]:
        mask = Image.open(V / f'source/working/protection-{k}.png').convert('L')
        changed = 0; old_mapped = 0; new_old_colors = 0
        for oc, nc, m in zip(old.getdata(), im.getdata(), mask.getdata()):
            if not oc[3]:
                continue
            if m:
                assert oc == nc, (k, 'protected head/blade')
            else:
                assert nc[:3] == cmap.get(oc[:3], oc[:3]), (k, oc, nc)
                old_mapped += oc[:3] in cmap
                new_old_colors += nc[:3] in cmap
            if oc[:3] in skin:
                assert oc == nc, (k, 'warm skin')
            changed += oc != nc
        assert changed > 150 and old_mapped > 150 and new_old_colors == 0
        changed_pixels += changed
        record.update(changed_equipment_pixels=changed,
                      protected_head_and_blade_rgba_equal=True,
                      warm_skin_tones_equal=True,
                      old_brown_and_silver_palette_pixels_outside_protection=old_mapped,
                      remaining_old_palette_pixels_outside_protection=new_old_colors)
    assert p.stat().st_size < 50000
    frames.append(record)
arc = Image.open(V / 'reference/slash-006.png').convert('RGBA')
body = Image.open(V / 'deliverables/enemy/frame-007.png').convert('RGBA').crop((4, 0, 324, 256))
frame6 = Image.open(V / 'deliverables/enemy/frame-006.png').convert('RGBA')
for a0, b0, c0 in zip(arc.getdata(), body.getdata(), frame6.getdata()):
    if a0[3] and not b0[3]:
        assert a0 == c0
assert (V / 'deliverables/enemy/frame-008.png').read_bytes() == (
    V / 'deliverables/enemy/frame-015.png').read_bytes()
videos = []
for key in sorted(targets):
    action = b[key]
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
assert len(videos) == 14
for p in [*(V / 'tools').glob('*.py'), R / 'tools/export_gallery.py']:
    ast.parse(p.read_text(), filename=str(p))
assert not subprocess.check_output(['git', 'diff', '--name-only', '--', 'actual'],
                                    cwd=R.parents[1], text=True).strip()
report = {'revision': V.name, 'status': 'pending_user_visual_acceptance',
          'scope': 'Enemy mercenary equipment only; brown/silver boots, bracers, shoulder armor, belts and trim become deep navy.',
          'equipment_palette': reg['equipment_palette'], 'frames': frames,
          'changed_equipment_pixels_in_eight_body_poses': changed_pixels,
          'all_alpha_positions_airborne_heights_and_timelines_preserved': True,
          'head_and_sword_protected': True, 'source_slash_and_external_lightning_preserved': True,
          'changed_actions': len(targets), 'other_actions_preserved': len(b)-len(targets),
          'videos': videos, 'ally_or_map_or_game_changes': False, 'new_package_created': False,
          'browser_inspection': 'Not performed; existing local-file restriction honored. Offline deep/light comparisons and rendered poses inspected.',
          'validation_scope': 'Targeted color-only pixel/alpha, source timeline and video frame-count/FPS checks; no broad gameplay regression.'}
(V / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'pass': True, 'enemy_actions': len(targets), 'other_actions_preserved': len(b)-len(targets),
                  'videos': len(videos), 'changed_equipment_pixels': changed_pixels}))
