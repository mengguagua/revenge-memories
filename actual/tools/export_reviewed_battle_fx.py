"""Export the approved R5 effects as native Godot layers and audio cues.

The gallery case is evidence for visual timing and registration only.
Runtime routing uses the native animation program and the actual strike.
"""
import argparse
import base64
import json
import math
import shutil
from pathlib import Path

from PIL import Image, ImageColor

ACTUAL = Path(__file__).resolve().parents[1]
ART = ACTUAL / 'assets/battle-fx'
SOUND = ACTUAL / 'assets/sfx/battle-fx'
DATA = ACTUAL / 'data/battle_fx.json'
FPS = 60
BATTLE_X = 191


def javascript(path):
    source = path.read_text()
    return json.loads(source[source.index('{'):source.rindex('}') + 1])


def case_data(path):
    return json.loads(path.read_text().split(']=', 1)[1].rstrip(';\n'))


def seconds(value):
    return round(value, 5)


def capture_for(source, key):
    for folder in ('pixel-reference-r4-20261107/captures-clean',
                   'weapon-magic-r2-20261107/captures', 'full-battle-20261107/captures'):
        path = source / folder / key / 'capture.json'
        if path.is_file():
            return json.loads(path.read_text())
    raise FileNotFoundError(key)


def visual_cues(case, effects, contact, register):
    layers = []
    for item in case['fxPlan']:
        if item['effect'].startswith('r5-damage-'):
            continue
        layers.append(item)
    projectile = case.get('projectile')
    if projectile:
        layers.append(dict(effect=projectile.get('effect', projectile['kind']),
                           start=projectile['start'], track=projectile['anchors'],
                           projectile=projectile['kind'], flip=projectile['flip'],
                           alpha=.6 if projectile['kind'] == 'wake' else 1))
    def impact_layer(item):
        name = item['effect']
        return (name in ('hit', 'blunt', 'stone', 'void', 'holy', 'core', 'legacy-water')
                or name.startswith(('r2-bowhit-', 'r2-javelin-hit-', 'r2-lance-')))
    result = []
    for item in layers:
        name = item['effect']
        effect = effects[name]
        row = {key: item[key] for key in
               ('effect', 'layer', 'alpha', 'flip', 'rate', 'offset', 'fadeIn', 'fadeOut', 'projectile')
               if key in item}
        start = item['start']
        rate = item.get('rate', 1)
        until = item.get('until')
        if until is None:
            until = start + (effect['frames'] / effect['fps'] - item.get('offset', 0)) / rate
        row.update(start=seconds(start-contact), end=seconds(until-contact))
        if abs(row['start']) < .021 and 'track' not in item and not projectile:
            row['end'] = seconds(until-start)
            row['start'] = 0
        if impact_layer(item):
            row['hit'] = True
        if 'anchor' in item:
            row['at'] = register(item['anchor'])
        else:
            first = max(0, math.floor(start*FPS))
            last = min(len(item['track']), math.ceil(until*FPS))
            track = item['track'][first:last]
            if track and track[0] and all(p == track[0] for p in track):
                row['at'] = register(track[0])
            else:
                row['track'] = [first, [register(p) if p else None for p in track]]
        if 'trailLimit' in item:
            row['limit'] = register([item['trailLimit'], 0])[0]
        result.append(row)
    return result


def plan_for(case, capture, effects):
    event = case['source']['event']
    contact = case['contact']
    is_cinema = case['family'] == 'cinema'
    if is_cinema:
        shot = next(row['cinema'] for row in capture['frames'] if row.get('contact') and row.get('cinema'))
        origin, density = shot['origin'], shot['scale']
        register = lambda p: [round((v-o)/density, 3) for v,o in zip(p, origin)]
        first = 0
    else:
        row = capture['frames'][0]
        a, b = row['actor'][0], row['target'][0]
        distance = b - a
        # One-unit heals draw the caster and recipient at the same position.
        if abs(distance) < 1:
            distance = -112 if capture['job']['actor']['side'] == 'player' else 112
        register = lambda p: [round((p[0]-a)/distance, 5), round(p[1], 2)]
        first = next((row['t'] for row in capture['frames'] if row['tick'] == 0), .4)
    result = {'case': case['key'], 'contact': contact, 'first': seconds(first-contact),
              'layers': visual_cues(case, effects, contact, register)}
    if is_cinema:
        result['density'] = density
    else:
        result['left'] = distance > 0
    start = case.get('replaceEffectsFrom')
    if case.get('fullReplacement') or case.get('suppressFlash'):
        start = first
    if start is not None:
        result['replace'] = [seconds(start-contact),
                             seconds(case.get('replaceEffectsUntil', case['duration'])-contact)]
    if case.get('visualRevision') == 'levin':
        result['weapon_front'] = True
    if case.get('visualRevision') == 'drain':
        result['positive_damage'] = True
    if 'actorPositions' in case:
        result['ghosts'] = True
    if 'actorPlan' in case:
        actor = case['actorPlan']
        result['actor'] = {
            'effect': actor['effect'], 'first': actor['startFrame'],
            'frames': [[frame, *register([x,y]), flip, alpha] if row else None
                       for row in actor['frames']
                       for frame,x,y,flip,alpha in ([row] if row else [[0,0,0,False,0]])],
        }
    audio = []
    for cue in case.get('audioCues', []):
        if cue['id'].startswith('r5-hp-ticks-'):
            continue
        audio.append({'key':cue['id'], 'time':seconds(cue['at']-contact),
                      'gain':cue['gain'], 'duration':cue['duration'],
                      'on_hit': cue['label'] in ('结果','收尾') and not event.get('visual_only', False)})
    if audio:
        result['audio'] = audio
    result['end'] = max([0] + [p['end'] for p in result['layers']])
    return result


def save_art(effect_names, effects, preview):
    used = {}
    sizes = {}
    for name in sorted(effect_names):
        old = effects[name]
        files = old['paths'] if 'paths' in old else [old['path']]
        paths = []
        for i, rel in enumerate(files):
            image = preview / rel
            dest = ART / f'{name}-{i:02d}.png'
            shutil.copyfile(image, dest)
            paths.append('res://' + dest.relative_to(ACTUAL).as_posix())
            with Image.open(dest) as pix:
                sizes[dest.name] = [pix.width, pix.height, dest.stat().st_size]
        used[name] = dict(paths=paths, size=old['frameSize'], pivot=old['pivot'],
                          fps=old['fps'], frames=old['frames'], columns=old['columns'],
                          cells=old.get('atlasFrames',old['frames']), loop=old.get('loop',False))
    return used, sizes


def water_sprites(palette):
    effect_data = json.loads((ACTUAL/'data/mechanical_puppets_art.json').read_text())
    colors = [ImageColor.getrgb(color) for color in palette]
    paths = {}
    for name, spec in effect_data['effects'].items():
        if not name.startswith('water-monkey-water-'):
            continue
        with Image.open(ACTUAL / spec['path'].removeprefix('res://')) as source:
            rgba = source.convert('RGBA')
        pixels = []
        for r,g,b,a in rgba.getdata():
            if a >= 7 and ((b-r >= 8 and g-r >= 5) or (r>160 and g>170 and b>175 and b>=r-12)):
                r,g,b = colors[round((.2126*r+.7152*g+.0722*b)/255*(len(colors)-1))]
            pixels.append((r,g,b,a))
        rgba.putdata(pixels)
        dest = ART / f'{name}.png'
        rgba.save(dest, optimize=True)
        paths[name] = 'res://' + dest.relative_to(ACTUAL).as_posix()
    return paths


def compile_review(preview):
    source = preview.parent/'source'
    catalog = javascript(preview/'catalog.js')
    effects = catalog['effects']
    approved = javascript(preview/'approved-data.js')
    for key, value in approved['effects'].items():
        effects['legacy-'+key] = dict(value, path='assets/base/assets/approved/'+value['path'].removeprefix('assets/'))
    battle = {}
    cinema = {}
    effect_names = {'hit','dust','blunt','map-hit','map-heal','map-warp','r2-map-hero-bow',
                    'legacy-water','legacy-cannon','legacy-core'}
    sound_names = set()
    cases = [case_data(f) for f in sorted((preview/'cases').glob('*.js'))]
    conflicts = []
    for case in cases:
        family = case['family']
        if family in ('reaction', 'map'):
            sound_names.update(q['id'] for q in case.get('audioCues', []))
            continue
        capture = capture_for(source, case['key'])
        plan = plan_for(case, capture, effects)
        program = case['source']['program']
        if family == 'cinema':
            cinema[program] = plan
        else:
            event = case['source']['event']
            weapon = str(int(event['weapon_index']))
            # A recoil strike uses its own overlay even when it shares the swing.
            if event.get('self_damage',0) > 0:
                weapon += ':recoil'
            key = program+'|'+weapon
            if key in battle:
                # Ordinary and non-cinematic critical examples share the pose.
                # Keep the ordinary one as the base for both.
                conflicts.append((key,battle[key]['case'],case['key']))
                if event.get('critical', False):
                    continue
            battle[key] = plan
    for plan in list(battle.values())+list(cinema.values()):
        effect_names.update(row['effect'] for row in plan['layers'])
        sound_names.update(row['key'] for row in plan.get('audio', []))
        if 'actor' in plan:
            effect_names.add(plan['actor']['effect'])
    for name in effects:
        if name.startswith('r5-damage-'):
            effect_names.add(name)

    ART.mkdir(parents=True, exist_ok=True)
    SOUND.mkdir(parents=True, exist_ok=True)
    packed, sizes = save_art(effect_names, effects, preview)
    source_audio = javascript(preview/'spell-audio-bank.js')
    source_audio.update(javascript(preview/'r4-audio-bank.js'))
    sounds = {}
    for key in sorted(sound_names):
        clip = source_audio[key]
        dest = SOUND / f'{key}.wav'
        dest.write_bytes(base64.b64decode(clip['wav']))
        sounds[key] = 'res://' + dest.relative_to(ACTUAL).as_posix()
    water = next(c for c in approved['cases'] if c['key']=='water')
    routes = {
        'effects':packed, 'audio':sounds, 'battle':battle, 'cinema':cinema,
        'water':water_sprites(water['waterTint']['palette']),
    }
    for name in routes['water'].values():
        path = ACTUAL / name.removeprefix('res://')
        with Image.open(path) as image:
            sizes[path.name] = [image.width, image.height, path.stat().st_size]
    (ART/'LICENSE.txt').write_bytes((preview/'LICENSE').read_bytes())
    (ART/'NOTICE.txt').write_text(
        'Selected battle effects derived from patch-gg/pixelfx v0.3.0, commit '
        'a84159688af3ca37a4be05a0d422b94451b2e24e. MIT License.\n'
        'Particle simulation and certain effects adapt Sprite Fusion pixel-art VFX, '
        'Copyright (c) 2026 Hugo Duprez, MIT License.\n'
        'Act timing adapts Hollow Crown by rehan-remade, Copyright (c) 2026, MIT License.\n'
        'Game actor artwork is from Revenge Memories. No PixelFX demo actors or gallery fonts ship.\n')
    print(f'{len(battle)} battle routes, {len(cinema)} criticals, {len(packed)} effect sheets, '
          f'{len(sounds)} sounds, {len(sizes)} PNG files')
    return routes, {'image_sizes':sizes, 'shared_programs':conflicts}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('preview', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    routes, report = compile_review(args.preview)
    DATA.write_text(json.dumps(routes,ensure_ascii=False,separators=(',',':'))+'\n')
    if args.report:
        args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
