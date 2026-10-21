#!/usr/bin/env python3
"""Review-only cavalry registration and shared, muted sixteen-color palette."""
import colorsys
from functools import lru_cache
import hashlib
import json
from PIL import Image, ImageDraw
from build_gallery import ROOT

REVISION = 'cavalry-map-anchor-palette-v1-20261021'
OUT = ROOT / REVISION
MAPPING = ROOT / 'professions/class-1-ally/maps/frame_mapping.json'
PALETTE = ['1c2027', '34373d', '56595e', '838588', 'b2b3af', 'dedbcf',
           '2b394e', '435772', '74859c', '57493f', '8e7761', 'ae9567',
           'd0bb91', 'ad8870', 'dbb695', 'efeadb']
IDLE_FRONT = [(32, 53), (51, 53), (50, 70), (50, 82), (27, 82), (27, 62), (31, 59)]
IDLE_HIND = [(55, 58), (76, 58), (83, 64), (83, 83), (51, 83), (51, 63)]
WALK = {
    'up': {'frames': [0, 1], 'translations': [[0, 0], [1, -3]], 'leg_start': 70, 'fixed_point': [64, 44]},
    'right': {'frames': [2, 3], 'translations': [[5, 0], [0, 0]], 'leg_start': 74, 'fixed_point': [64, 54]},
    'down': {'frames': [4, 5], 'translations': [[0, 0], [0, -5]], 'leg_start': 74, 'fixed_point': [64, 48]},
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signature(action):
    keys = ['frames', 'revisedFrames', 'reviewTailFrames', 'fps', 'origin',
            'contactTick', 'duration', 'viewport', 'closeCamera']
    return hashlib.sha256(json.dumps({k: action.get(k) for k in keys}, sort_keys=True).encode()).hexdigest()


@lru_cache(maxsize=50000)
def limited_rgb(rgb):
    h, s, v = colorsys.rgb_to_hsv(*(x/255 for x in rgb))
    s *= .80
    muted = tuple(x*255 for x in colorsys.hsv_to_rgb(h, s, v))
    # Neutral horse/metal shading must not become flesh-colored speckles.
    indices = [0, 1, 2, 3, 4, 5, 15] if s < .18 else range(len(PALETTE))
    choices = [tuple(bytes.fromhex(PALETTE[i])) for i in indices]
    return min(choices, key=lambda c: sum((a-b)**2 for a, b in zip(c, muted)))


def limited(image):
    result = Image.new('RGBA', image.size)
    result.putdata([(*limited_rgb(p[:3]), 255) if p[3] >= 128 else (0, 0, 0, 0) for p in image.getdata()])
    return result


def translate(image, delta):
    result = Image.new('RGBA', image.size)
    result.alpha_composite(image, tuple(delta))
    assert sum(p[3] > 0 for p in result.getdata()) == sum(p[3] > 0 for p in image.getdata()), 'Translation clips contour'
    return result


def polygon(size, points):
    mask = Image.new('L', size)
    ImageDraw.Draw(mask).polygon(points, fill=255)
    return mask


def create():
    OUT.mkdir(exist_ok=True)
    baseline_path = OUT / 'baseline.json'
    if not baseline_path.exists():
        mapping = json.loads(MAPPING.read_text())
        data = json.loads((ROOT / 'demos/gallery-data.json').read_text())
        sources = {r['output_path']: digest((MAPPING.parent/r['output_path']).resolve())
                   for s in mapping['scenarios'] for r in s['frame_mapping']}
        baseline_path.write_text(json.dumps({'mapping': mapping, 'sources': sources,
            'digests': {a['id']: a['contentDigest'] for a in data['actions']},
            'timelines': {a['id']: signature(a) for a in data['actions']}}, ensure_ascii=False, indent=2)+'\n')
    before = json.loads(baseline_path.read_text())
    mapping = json.loads(json.dumps(before['mapping']))
    old = {s['id']: s for s in before['mapping']['scenarios']}
    source_frames = {key: {r['source_index']: limited(Image.open((MAPPING.parent/r['output_path']).resolve()).convert('RGBA'))
                         for r in scenario['frame_mapping']} for key, scenario in old.items()}
    inventory = []
    registrations = []

    def save(image, relative, purpose):
        path = OUT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path, optimize=True)
        inventory.append({'path': path.relative_to(ROOT).as_posix(), 'purpose': purpose, 'size': list(image.size),
            'bytes': path.stat().st_size, 'sha256': digest(path), 'visible_bounds': list(image.getbbox()),
            'visible_colors': len({p[:3] for p in image.getdata() if p[3]})})
        return '../../../'+path.relative_to(ROOT).as_posix()

    # Keep the standing rider, lance, horse head and barrel fixed. Only the
    # original foreleg / hindleg windows exchange their lift poses.
    idle = source_frames['tactical-idle']
    stand = idle[1]
    fore = polygon(stand.size, IDLE_FRONT)
    hind = polygon(stand.size, IDLE_HIND)
    canon = [stand.copy(), stand.copy(), stand.copy()]
    canon[0].paste(idle[0], (0, 0), fore)
    canon[2].paste(translate(idle[2], [-1, 0]), (0, 0), hind)
    canon = [translate(im, [-6, 0]) for im in canon]
    aliases = [0, 1, 2, 1, 0, 1]
    idle_frames = {i: canon[pose] for i, pose in enumerate(aliases)}

    walk = source_frames['tactical-walk']
    walk_frames = {}
    for direction, config in WALK.items():
        ids = config['frames']
        plates = [translate(walk[i], delta) for i, delta in zip(ids, config['translations'])]
        for i, plate in zip(ids, plates):
            revised = plate.copy()
            fixed_box = (0, 0, plate.width, config['leg_start'])
            revised.paste(plates[0].crop(fixed_box), (0, 0))
            walk_frames[i] = revised
            registrations.append({'direction': direction, 'frame': i, 'translation': config['translations'][ids.index(i)],
                'fixed_upper_box': list(fixed_box), 'fixed_point': config['fixed_point'], 'legs_from_original_phase': True})
    # Mirror around the explicit body axis x=64, rather than x=63.5.
    for right, left in [(2, 6), (3, 7)]:
        walk_frames[left] = translate(walk_frames[right].transpose(Image.Transpose.FLIP_LEFT_RIGHT), [1, 0])
        registrations.append({'direction': 'left', 'frame': left, 'mirror_of': right, 'mirror_axis': 64,
            'fixed_upper_box': [0, 0, 128, 74], 'fixed_point': [64, 54], 'legs_from_original_phase': True})

    for scenario in mapping['scenarios']:
        key = scenario['id']
        frames = idle_frames if key == 'tactical-idle' else walk_frames
        size = tuple(scenario['output_frame_size'])
        atlas = Image.new('RGBA', (size[0]*len(frames), size[1]))
        for record in scenario['frame_mapping']:
            i = record['source_index']
            path = save(frames[i], f'{key}/frame-{i:03}.png', 'allied cavalry / fixed rider and limited muted palette / '+key)
            atlas.alpha_composite(frames[i], (size[0]*i, 0))
            previous = dict(record)
            record.clear()
            record.update(source_index=i, source_frame=previous.get('source_frame', i), path=path, output_path=path,
                kind='registered_existing_art_with_limited_palette', previous_record=previous,
                previous_output_path=previous['output_path'], size=list(size), bytes=inventory[-1]['bytes'],
                sha256=inventory[-1]['sha256'], visible_bounds=list(frames[i].getbbox()), revision=REVISION,
                art_review_status='pending_user_visual_acceptance')
        scenario['output_atlas'] = save(atlas, key+'-atlas.png', 'offline review pose atlas / '+key)
        scenario['output_atlas_bytes'] = inventory[-1]['bytes']
        scenario.update(revision=REVISION, status='review_candidate', art_review_status='pending_user_visual_acceptance',
            registration_note='Fixed rider/upper-body plate; original leg phases registered with integer translations. Shared sixteen-color palette without dithering.',
            review_note='盟军骑兵主体和中心点固定，保留原马腿姿势与节奏；待机和四向行走统一16色低饱和蓝白、灰色马匹与少量米金、自然肤色。仅对照页，未接入游戏。')
    mapping.update(revision=REVISION, runtime_integrated=False, status='review_candidate',
        art_mode='existing pixel art; integer registration; fixed upper plates; no-dither shared sixteen-color palette')
    MAPPING.write_text(json.dumps(mapping, ensure_ascii=False, indent=2)+'\n')
    (OUT/'asset-manifest.json').write_text(json.dumps({'revision': REVISION, 'runtime_integrated': False,
        'image_generation_invoked': False, 'chat_image_output': False, 'palette': PALETTE, 'prequantize_saturation_factor': .80,
        'idle_fixed_point': [48, 48], 'idle_translation': [-6, 0], 'idle_foreleg_mask': IDLE_FRONT,
        'idle_hindleg_mask': IDLE_HIND, 'idle_aliases': aliases, 'walk_registration': registrations,
        'assets': inventory}, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'revision': REVISION, 'individual_frames': 14, 'palette_colors': len(PALETTE)}, ensure_ascii=False))
    return idle_frames, walk_frames


if __name__ == '__main__':
    create()
