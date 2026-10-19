from pathlib import Path
from PIL import Image
from fractions import Fraction
import ast, json, subprocess

V = Path(__file__).resolve().parents[1]; R = V.parent
before = json.loads((V / 'reference/gallery-before.json').read_text())
after = json.loads((R / 'demos/gallery-data.json').read_text())
reg = json.loads((V / 'registration.json').read_text())
a = {x['id']: x for x in before['actions']}; b = {x['id']: x for x in after['actions']}
assert a.keys() == b.keys()
targets = {k for k, x in b.items() if x['profile'] in
           ['professions-class-8-ally-battle', 'professions-class-8-enemy-battle']}
repair = json.loads((V / 'reference/preexisting-preview-repair.json').read_text())
repair_ids = set(repair['action_ids'])
for k in a:
    for field in ['frames', 'origin', 'fps', 'contactTick', 'duration']:
        assert a[k][field] == b[k][field], (k, field)
    assert (a[k]['contentDigest'] != b[k]['contentDigest']) == (k in targets or k in repair_ids), k
assert before['effects'] == after['effects']

sides = {}; alpha_checks = []; protected_checks = []
for side in ['ally', 'enemy']:
    palette = {tuple(bytes.fromhex(c[1:])) for c in reg['palettes'][side]}
    used = set(); frames = []
    for k in [0, 1, 2, 3, 4, 5, 6, 7, 8, 15, 16]:
        p = V / f'deliverables/{side}/frame-{k:03d}.png'
        im = Image.open(p).convert('RGBA')
        old = Image.open(V / f'reference/{side}-{k:03d}.png').convert('RGBA')
        assert im.size == old.size == (320, 256)
        assert im.getchannel('A').tobytes() == old.getchannel('A').tobytes(), (side, k)
        assert im.getbbox() == old.getbbox(), (side, k)
        alpha_checks.append({'side': side, 'frame': k, 'alpha_bytes_equal': True,
                              'bounds': list(im.getbbox())})
        if k in [0, 1, 2, 3, 4, 5, 7, 16]:
            mask = Image.open(V / f'source/working/{side}-{k}-blade-mask.png').convert('L')
            for oldc, c, m in zip(old.getdata(), im.getdata(), mask.getdata()):
                if oldc[3] and m:
                    assert oldc == c, (side, k, 'protected blade')
                elif c[3]:
                    assert c[:3] in palette, (side, k, c)
                    used.add(c[:3])
            protected_checks.append({'side': side, 'frame': k,
                                      'source_sword_region_rgba_equal': True})
        frames.append({'frame': k, 'bytes': p.stat().st_size})
    assert len(used) == 14
    original_arc = Image.open(V / f'reference/{side}-slash-006.png').convert('RGBA')
    frame6 = Image.open(V / f'deliverables/{side}/frame-006.png').convert('RGBA')
    frame7 = Image.open(V / f'deliverables/{side}/frame-007.png').convert('RGBA')
    shifted7 = frame7.crop((4, 0, 324, 256))
    visible_arc_pixels = 0
    for arc, pixel, body in zip(original_arc.getdata(), frame6.getdata(), shifted7.getdata()):
        if arc[3] and not body[3]:
            assert arc == pixel, (side, 'slash layer pixel')
            visible_arc_pixels += 1
    assert visible_arc_pixels > 100
    if side == 'ally':
        assert (V / 'deliverables/ally/frame-000.png').read_bytes() == (
            V / 'deliverables/ally/frame-008.png').read_bytes() == (
            V / 'deliverables/ally/frame-015.png').read_bytes()
    else:
        frame0 = Image.open(V / 'deliverables/enemy/frame-000.png').convert('RGBA')
        frame8 = Image.open(V / 'deliverables/enemy/frame-008.png').convert('RGBA')
        shifted0 = frame0.crop((64, 0, 384, 256))
        assert frame8.getchannel('A').tobytes() == shifted0.getchannel('A').tobytes()
        for c, oldc in zip(frame8.getdata(), shifted0.getdata()):
            if c[3]:
                assert c == oldc
        assert (V / 'deliverables/enemy/frame-008.png').read_bytes() == (
            V / 'deliverables/enemy/frame-015.png').read_bytes()
    sides[side] = {'shared_body_colors': len(used), 'palette': reg['palettes'][side],
                   'frames': frames, 'source_slash_pixels_preserved': visible_arc_pixels,
                   'palette_exclusions': 'Protected original sword pixels and original slash layer are retained, not counted as outfit/body colors.'}

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
        videos.append({'path': action[mode], **meta, 'bytes': p.stat().st_size})
assert len(videos) == 28
for p in [*(V / 'tools').glob('*.py'), R / 'tools/export_gallery.py']:
    ast.parse(p.read_text(), filename=str(p))
assert not subprocess.check_output(['git', 'diff', '--name-only', '--', 'actual'],
                                    cwd=R.parents[1], text=True).strip()
report = {'revision': V.name, 'status': 'pending_user_visual_acceptance',
          'scope': '双方佣兵战斗场景服装简色，敌军蓝紫；地图与游戏未修改',
          'colors': sides, 'alpha_and_pose_checks': alpha_checks,
          'protected_sword_checks': protected_checks,
          'all_pose_alpha_positions_and_airborne_heights_preserved': True,
          'all_source_timelines_contacts_and_external_effects_preserved': True,
          'changed_actions': len(targets), 'other_actions_preserved': len(b)-len(targets),
          'prior_spear_preview_exports_refreshed': len(repair_ids),
          'prior_spear_repair': repair,
          'videos': videos, 'game_files_changed': False, 'new_package_created': False,
          'validation_scope': 'Color-only scope: exact alpha/coordinate identity, fixed palette, protected sword/source slash, source timelines and matching video frame count/FPS. No broad game regression.',
          'browser_visual_inspection': 'Not performed; local file restriction respected. Offline dark/light comparison and rendered battle moments used.'}
(V / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'pass': True, 'changed_actions': len(targets), 'other_actions_preserved': len(b)-len(targets),
                  'videos': len(videos), 'body_colors': {k: v['shared_body_colors'] for k, v in sides.items()}}))
