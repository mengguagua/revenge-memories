#!/usr/bin/env python3
"""Review-only downward gallop registration using existing native pixel layers.

No image-generation or chat-image output. One existing front-view body is
reused; the existing raised / planted leg pixels are isolated and registered
as paired layers. No runtime resources are written.
"""
import hashlib
import json
from PIL import Image
from revise_gold_knight_idle import ROOT, PALETTE

REVISION = 'gold-knight-down-v4-20261020'
OUT = ROOT / REVISION
PREVIOUS = ROOT / 'gold-knight-walk-v3-20261020'
AXIS = 64
FLOOR = 92
BODY_BOB = 4
LEG_WINDOW = (55, 73, 79, 96)


def mirror(image):
    """Reflect around pixel-center x=64, not the canvas edge x=63.5."""
    result = Image.new('RGBA', (128, 96))
    result.alpha_composite(image.transpose(Image.Transpose.FLIP_LEFT_RIGHT), (1, 0))
    return result


def place(image, point):
    result = Image.new('RGBA', (128, 96))
    result.alpha_composite(image, point)
    return result


def create():
    (OUT/'frames').mkdir(exist_ok=True)
    (OUT/'source').mkdir(exist_ok=True)
    original = Image.open(PREVIOUS/'frames/frame-004.png').convert('RGBA')
    # The old first down pose has a clear front-view body and an intact planted
    # foreleg, but its other foreleg is lifted. Share the same body in both phases.
    body = Image.new('RGBA', original.size)
    body.alpha_composite(original, (-1, 0))
    body.paste((0, 0, 0, 0), LEG_WINDOW)
    body.save(OUT/'source/fixed-body.png', optimize=True)

    # Reuse the actual planted and bent limb artwork from the existing sprite.
    # These crops include the existing outline, white shin and gold fetlock.
    planted = original.crop((59, 73, 69, 95))
    bent = original.crop((68, 73, 78, 87))
    # The two old legs touch in this crop. Remove the neighboring raised leg's
    # edge column before pairing the planted limb; keep its actual contour.
    right_edge = [7,7,7,7,6,6,6,7,8,8,7,6,6,6,6,7,7,8,8,8,8,8]
    for y, edge in enumerate(right_edge):
        for x in range(edge+1, planted.width): planted.putpixel((x,y),(0,0,0,0))
    planted.save(OUT/'source/planted-leg.png', optimize=True)
    bent.save(OUT/'source/bent-leg.png', optimize=True)

    grounded = body.copy()
    left = place(planted, (53, 71))
    right = mirror(left)
    # Roots overlap the original chest by two rows; the front feet share y=92.
    grounded.alpha_composite(left)
    grounded.alpha_composite(right)

    airborne = Image.new('RGBA', (128, 96))
    airborne.alpha_composite(body, (0, -BODY_BOB))
    # Two smaller tucked hind legs sit behind two full-size bent forelegs.
    hind = bent.resize((8, 10), Image.Resampling.NEAREST)
    far_left = place(hind, (50, 68))
    far_right = mirror(far_left)
    near_left = place(bent, (55, 69))
    near_right = mirror(near_left)
    for name, layer in [('hind-left', far_left), ('hind-right', far_right),
                        ('fore-left', near_left), ('fore-right', near_right)]:
        layer.save(OUT/f'source/air-{name}.png', optimize=True)
        airborne.alpha_composite(layer)
    left.save(OUT/'source/ground-fore-left.png', optimize=True)
    right.save(OUT/'source/ground-fore-right.png', optimize=True)

    records = []
    frames = {4: airborne, 5: grounded}
    for index, frame in frames.items():
        path = OUT/f'frames/frame-{index:03}.png'
        frame.save(path, optimize=True)
        records.append({'source_index': index, 'path': path.relative_to(ROOT).as_posix(),
                        'size': list(frame.size), 'bytes': path.stat().st_size,
                        'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    atlas = Image.new('RGBA', (128*8, 96))
    for index in range(8):
        frame = frames.get(index)
        if frame is None: frame = Image.open(PREVIOUS/f'frames/frame-{index:03}.png').convert('RGBA')
        atlas.alpha_composite(frame, (128*index, 0))
    atlas.save(OUT/'walk-atlas.png', optimize=True)
    (OUT/'asset-manifest.json').write_text(json.dumps({
        'revision': REVISION, 'runtime_integrated': False,
        'method': 'existing native pixel layers; deterministic registration and compositing',
        'image_generation_invoked': False, 'chat_image_output': False,
        'palette': PALETTE, 'body_centerline': AXIS, 'body_vertical_bob': BODY_BOB,
        'leg_window': list(LEG_WINDOW), 'hoof_floor_row': FLOOR,
        'cycle': ['four legs airborne', 'two visible forelegs planted; hind legs occluded'],
        'frame_ticks': 16, 'preserved': ['accepted idle', 'up', 'right', 'left', 'fixed ground shadow'],
        'frames': records,
    }, ensure_ascii=False, indent=2)+'\n')
    return frames


if __name__ == '__main__':
    create()
