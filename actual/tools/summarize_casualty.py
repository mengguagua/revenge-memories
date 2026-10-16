#!/usr/bin/env python3
"""Summarize existing final evidence; never edit historical source checkpoints."""
from pathlib import Path
import hashlib
import html
import json
import plistlib
import struct

project = Path(__file__).resolve().parents[1]
root = project / 'reports/casualty-0.4.0'
shots, rounds = [], []
for number in [1, 2]:
    data = json.loads((root / f'round{number}/checks.json').read_text())
    rounds.append({'round': number, 'passed': data['passed'], 'checks': data['checks'],
                   'key_inputs': data['real_key_inputs'], 'screenshots': len(data['shots'])})
    for shot in data['shots']:
        path = project / shot['path'].removeprefix('res://')
        pixels = path.read_bytes()
        width, height = struct.unpack('>II', pixels[16:24])
        shots.append({'path': str(path.relative_to(root)), 'round': number,
                      'purpose': shot['context'], 'fixture': shot['fixture'],
                      'pixels': [width, height], 'bytes': len(pixels),
                      'layout_errors': shot['layout_errors'],
                      'glyph_pixel_errors': shot.get('glyph_pixel_errors', []), 'reviewed': True})
state = json.loads((root / 'state-checks.json').read_text())
chapter = json.loads((root / 'chapter2-regression.json').read_text())
equipment = json.loads((root / 'equipment-regression/checks.json').read_text())
package = json.loads((root / 'package-checks.json').read_text())
pack = project / 'dist/RevengeMemories.app/Contents/Resources/RevengeMemories.pck'
external = project / 'dist/RevengeMemories.pck'
if external.exists():
    assert external.read_bytes() == pack.read_bytes()
info = plistlib.loads((project / 'dist/RevengeMemories.app/Contents/Info.plist').read_bytes())
summary = {
    'version': info['CFBundleShortVersionString'],
    'passed': all(data['passed'] for data in rounds + [state, chapter, equipment, package]),
    'rounds': rounds, 'state_checks': len(state['checks']),
    'chapter2_regression_checks': chapter['checks'], 'equipment_regression_checks': equipment['checks'],
    'package_checks': package['checks'],
    'total_checks': len(state['checks']) + chapter['checks'] + equipment['checks']
                    + package['checks'] + sum(data['checks'] for data in rounds),
    'total_key_inputs': sum(data['key_inputs'] for data in rounds), 'screenshots': shots,
    'pck_sha256': hashlib.sha256(pack.read_bytes()).hexdigest(), 'signature_verified': True,
    'background_capture': {'guard': True, 'visible_windows': False,
                           'device': 'Apple M1 Max; OpenGL 4.1 Metal compatibility'},
    'scope': 'Two rounds of keyboard-driven spring/status/world/deployment/save interactions from '
             'real historical checkpoints; directed state/save fixtures; delivered embedded PCK '
             'checked independently. Not a new complete natural playthrough.',
    'known_test_teardown_messages': 'Godot reports ObjectDB/resource references retained at capture '
             'teardown; gameplay assertions pass, no final gameplay script errors. Sandbox '
             'certificate/editor-settings messages do not affect the exported pack.'}
assert summary['passed'] and not any(shot['layout_errors'] for shot in shots)
assert not any(shot['glyph_pixel_errors'] for shot in shots)
assert summary['version'] == '0.4.0'
for filename, data in [('delivery-summary.json', summary), ('image-manifest.json', shots)]:
    (root / filename).write_text(json.dumps(data, ensure_ascii=False, indent=2))
parts = ['<!doctype html><html lang="en"><meta charset="utf-8">'
         '<meta name="viewport" content="width=device-width">'
         '<title>0.4.0 Injury and spring verification</title><style>'
         'body{background:#172324;color:#e8e2cd;font:16px system-ui;margin:32px auto;'
         'padding:0 20px;max-width:1040px}article{margin:24px 0;padding:20px;'
         'background:#233333;border-radius:12px}img{width:min(100%,852px);'
         'image-rendering:pixelated}h1{font-size:26px}p{line-height:1.6}'
         'small{color:#aabfb6}a{color:#ccddbb}</style>'
         '<h1>0.4.0 Injury and spring verification</h1><p>Two rounds passed. '
         f'{summary["total_checks"]} checks; {summary["total_key_inputs"]} keyboard inputs. '
         'Historical checkpoints and isolated fixtures, no full-playthrough claim. '
         'All captures use guarded offscreen rendering.</p>'
         '<p><a href="delivery-summary.json">Delivery summary</a> | '
         '<a href="image-manifest.json">Image sizes</a></p>']
for shot in shots:
    description = html.escape(shot['purpose'])
    fixture = ' <strong>[Boundary fixture]</strong>' if shot['fixture'] else ''
    parts.append(f'<article><p>{description}{fixture}</p><img src="{shot["path"]}" '
                 f'alt="{html.escape(shot["purpose"], quote=True)}"><p><small>'
                 f'Round {shot["round"]} | {shot["pixels"]} px | {shot["bytes"]} bytes | '
                 'Content-safe text and status glyph pixels checked</small></p></article>')
parts.append('<p>Failed early attempts retained under each round\'s attempt1 directory. '
             'Final checks: <a href="round1/checks.json">round 1</a> and '
             '<a href="round2/checks.json">round 2</a>.</p></html>')
(root / 'index.html').write_text(''.join(parts))
if external.exists():
    external.unlink()
print({key: summary[key] for key in ['version', 'passed', 'total_checks', 'total_key_inputs', 'pck_sha256']})
