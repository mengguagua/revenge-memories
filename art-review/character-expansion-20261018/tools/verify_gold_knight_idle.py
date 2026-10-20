#!/usr/bin/env python3
"""Targeted review checks; never launches Godot or writes runtime resources."""
from pathlib import Path
import hashlib
import json
import subprocess
from PIL import Image, ImageChops, ImageDraw
from revise_gold_knight_idle import ROOT, OUT, REVISION, PALETTE, FRONT, HIND, mask
from export_gallery import font


def verify():
    data = json.loads((ROOT / 'demos/gallery-data.json').read_text())
    target = 'professions-class-7-ally-maps-tactical-idle--idle-cycle'
    action = next(a for a in data['actions'] if a['id'] == target)
    profile = next(p for p in data['profiles'] if p['id'] == action['profile'])
    assert action['ready'] and action['video'] and action['still']
    assert profile['revision'] == REVISION
    assert profile['mappingStatus'] == 'review_candidate'
    assert len(action['frames']) == 88
    expected = []
    for _ in range(2):
        for pose, count in zip([0, 1, 2, 1], [14, 8, 14, 8]):
            expected.extend([pose] * count)
    assert [r['frame'] for r in action['frames']] == expected
    assert all(r['offset'] == [0, 0] and not r['flip'] for r in action['frames'])
    frames = [Image.open(ROOT / profile['newFrames'][str(i)]).convert('RGBA') for i in range(6)]
    palette = {tuple(bytes.fromhex(c)) for c in PALETTE}
    for im in frames:
        assert im.size == (96, 96)
        assert set(im.getchannel('A').getdata()) == {0, 255}
        assert {p[:3] for p in im.getdata() if p[3]} == palette
        x0, y0, x1, y1 = im.getbbox()
        assert min(x0, y0, 96-x1, 96-y1) >= 8
    for i, moving_mask in [(0, mask(FRONT)), (2, mask(HIND))]:
        diff = ImageChops.difference(frames[i], frames[1])
        # Compare RGBA channels separately: transparent changes are significant.
        for channel in diff.split():
            assert ImageChops.multiply(channel, ImageChops.invert(moving_mask)).getbbox() is None
        assert any(channel.getbbox() for channel in diff.split())
    assert frames[1].tobytes() == frames[3].tobytes() == frames[5].tobytes()
    assert frames[0].tobytes() == frames[4].tobytes()
    assert frames[2].crop((31, 62, 55, 84)).tobytes() == frames[1].crop((31, 62, 55, 84)).tobytes()
    hoof_row = [frames[2].getpixel((x, 80))[3] != 0 for x in range(31, 55)]
    assert sum(value and (i == 0 or not hoof_row[i-1]) for i, value in enumerate(hoof_row)) == 2
    # Both lifted pairs leave their former contact rows empty.
    assert frames[0].getchannel('A').crop((31, 77, 55, 84)).getbbox() is None
    assert frames[2].getchannel('A').crop((56, 79, 78, 84)).getbbox() is None
    before = json.loads((OUT / 'baseline-digests.json').read_text())
    changed = [a['id'] for a in data['actions'] if before.get(a['id']) != a['contentDigest']]
    assert changed == [target], changed
    runtime = json.loads((OUT / 'baseline-actual-hashes.json').read_text())
    changed_runtime = [p for p, digest in runtime.items()
                       if not Path(p).is_file() or hashlib.sha256(Path(p).read_bytes()).hexdigest() != digest]
    assert not changed_runtime, changed_runtime
    # The exact renderer font metrics keep the title and both labels in safe areas.
    d = ImageDraw.Draw(Image.new('RGB', (584, 328)))
    heading = profile['actorName'] + ' · ' + action['name']
    heading_font = next((font(n) for n in range(22, 13, -1)
                         if d.textbbox((0, 0), heading, font=font(n))[2] <= 536), font(14))
    assert d.textbbox((0, 0), heading, font=heading_font)[2] <= 536
    for label in ['原作', '四倍像素重绘']:
        assert d.textbbox((0, 0), label, font=font(15))[2] <= 224
    video = ROOT / action['video']
    probe = json.loads(subprocess.check_output([
        '/opt/homebrew/bin/ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height,nb_frames,r_frame_rate,duration',
        '-of', 'json', str(video)]))['streams'][0]
    assert int(probe['nb_frames']) == 88
    assert abs(float(probe['duration']) - action['duration']) < 0.02
    assert [probe['width'], probe['height']] == [584, 328]
    html = (ROOT / 'index.html').read_text()
    assert f'data-default-action="{target}"' in html
    for name in ['overview.mp4', 'four-step-review.png', 'before-after.png']:
        assert (OUT / name).is_file()
        assert f'{REVISION}/{name}' in html
    assets = []
    for p in sorted(OUT.rglob('*.png')):
        with Image.open(p) as im:
            assets.append({'path': p.relative_to(ROOT).as_posix(), 'pixels': list(im.size),
                           'bytes': p.stat().st_size, 'purpose': 'preserved source / diagnostic' if p.parent.name == 'source' or p.name.startswith(('candidate-', 'reference-', 'leg-', 'stand-', 'registration-')) else 'review asset'})
    report = {'status': 'passed', 'runtime_integrated': False,
              'changed_actions': changed, 'unchanged_actions': len(data['actions'])-1,
              'unchanged_runtime_files': len(runtime), 'palette_colors': 8,
              'cycle': [0, 1, 2, 1], 'frame_ticks': [14, 8, 14, 8],
              'frames': 88, 'fixed_region_identical': True,
              'aliases_identical': True, 'lifted_hoof_contact_rows_clear': True,
              'third_pose_forelegs_identical_to_stand': True, 'third_pose_distinct_front_hooves': 2,
              'text_safe_area_metrics': 'passed', 'video': probe, 'assets': assets,
              'visual_check': 'Offline source/redraw still, four phases on light/dark grounds, and decoded animation montage inspected; no game window launched.',
              'browser_check': 'Not performed; existing file URL restriction respected.'}
    (OUT / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'assets'}, ensure_ascii=False))


if __name__ == '__main__':
    verify()
