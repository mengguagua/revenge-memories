from pathlib import Path
from types import SimpleNamespace
import json, sys

V = Path(__file__).resolve().parents[1]; R = V.parent
sys.path.insert(0, str(R / 'tools'))
from export_gallery import export, render_frame
from build_gallery import build

data = build()
targets = [x for x in data['actions'] if x['profile'] in
           ['professions-class-8-ally-battle', 'professions-class-8-enemy-battle']]
reports = []
close_keys = ['original_class_8_normal', 'original_class_8_enemy_normal',
              'class_8_ally_levin', 'class_8_enemy_levin', 'idle']
for action in targets:
    args = SimpleNamespace(close=False, scale=2, light=False, stills_only=False)
    reports.append(export(data, action, args))
    print(json.dumps(reports[-1], ensure_ascii=False), flush=True)
    if action['key'] in close_keys:
        args.close = True; args.scale = 4
        reports.append(export(data, action, args))
        print(json.dumps(reports[-1], ensure_ascii=False), flush=True)
    if action['key'] not in ['original_class_8_normal', 'original_class_8_enemy_normal',
                             'class_8_ally_levin', 'class_8_enemy_levin']:
        continue
    profile = next(x for x in data['profiles'] if x['id'] == action['profile'])
    seen = set()
    for tick, row in enumerate(action['frames']):
        if row['frame'] in seen:
            continue
        seen.add(row['frame'])
        for light in [False, True]:
            path = V / 'reviews' / f'{profile["side"]}-pose-{row["frame"]:03d}-{"light" if light else "dark"}.png'
            render_frame(data, profile, action, tick, 4, light, True).save(path, optimize=True)
    render_frame(data, profile, action, action['contactTick'], 3, False, False).save(
        V / 'reviews' / f'{profile["side"]}-{action["key"]}-contact.png', optimize=True)
(V / 'export-report.json').write_text(json.dumps({'exports': reports}, ensure_ascii=False, indent=2) + '\n')
build()
