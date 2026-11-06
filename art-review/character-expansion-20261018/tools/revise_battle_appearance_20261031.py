#!/usr/bin/env python3
"""Register the three ImageGen revisions without changing native action tracks."""
import argparse
import colorsys
import copy
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from build_gallery import ROOT, file_hash
from export_gallery import font
from import_knight_redraw_v3 import parts

REV = 'battle-appearance-v1-20261031'
OUT = ROOT / REV
SRC = OUT / 'source'
BASE = json.loads((OUT / 'baseline.json').read_text())
C = [tuple(bytes.fromhex(v)) for v in ['172638', '3976b5', 'e4e1c8', 'dda77d', '8c6b45']]
PC = C[:4] + [(185, 99, 105)]
ASSETS = []
REG = []
FACE = {0:(179,123,193,138),1:(154,128,169,140),2:(157,126,173,142),3:(152,129,170,143),
        4:(186,125,202,140),5:(170,125,186,141),6:(191,124,204,137),7:(189,126,203,138),
        9:(179,123,193,138),16:(179,123,193,138),17:(142,125,157,139),19:(137,127,152,138)}


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def bbox(points):
    return [min(x for x, y in points), min(y for x, y in points),
            max(x for x, y in points) + 1, max(y for x, y in points) + 1]


def inside(x, y, b):
    return b[0] <= x < b[2] and b[1] <= y < b[3]


def hull(points):
    pts = sorted(set(points))
    def cross(o, a, b):
        return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1]+upper[:-1]


def quant(im, palette):
    table = {p[:3]: min(palette, key=lambda c: sum((a-b)**2 for a, b in zip(c, p[:3]))) for p in im.getdata()}
    q = Image.new('RGBA', im.size)
    q.putdata([(*table[p[:3]], 255) if p[3] >= 170 else (0, 0, 0, 0) for p in im.getdata()])
    return q


def save(im, name, purpose):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    colors = sorted(set(im.getdata()))
    if im.mode == 'RGBA' and len(colors) <= 256:
        q = Image.new('P', im.size)
        q.putpalette([v for c in colors for v in c[:3]] + [0] * (768 - len(colors)*3))
        indices = {c: i for i, c in enumerate(colors)}
        q.putdata([indices[c] for c in im.getdata()])
        q.info['transparency'] = bytes(c[3] for c in colors)
        assert q.convert('RGBA').tobytes() == im.tobytes()
    else:
        q = im
    q.save(path, optimize=True)
    ASSETS.append({'path': path.relative_to(ROOT).as_posix(), 'purpose': purpose,
                   'size': list(im.size), 'bytes': path.stat().st_size, 'sha256': file_hash(path)})
    return '../../../' + path.relative_to(ROOT).as_posix()


def old_frame(cid, frame):
    return Image.open(ROOT / BASE['profiles'][str(cid)]['newFrames'][str(frame)]).convert('RGBA')


def cavalry():
    # ImageGen established white coat / mane and blue-white material placement.
    # Apply that color treatment to the original registered raster, preserving
    # every alpha value, lance, skin feature, leather fitting and pixel position.
    poses = {}
    for key in BASE['profiles']['1']['newFrames']:
        f = int(key)
        im = old_frame(1, f)
        q = im.copy()
        fx0, fy0, fx1, fy1 = FACE[f]
        cx = (fx0 + fx1) / 2
        head = (fx0-5, fy0-17, fx1+5, fy1+2)
        rider_mask = Image.new('L', im.size)
        ImageDraw.Draw(rider_mask).polygon([(cx-10, fy1-1), (cx+14, fy1-1), (cx+26, fy1+11),
                                           (cx+24, fy1+33), (cx+12, fy1+30), (cx+14, fy1+65),
                                           (cx-2, fy1+65), (cx-6, fy1+28), (cx-12, fy1+22)], fill=255)
        inner = im.getchannel('A').filter(ImageFilter.MinFilter(3))
        counts = {'white_horse': 0, 'blue_uniform': 0, 'ivory_armor': 0}
        for y in range(im.height):
            for x in range(im.width):
                r, g, b, a = im.getpixel((x, y))
                if not a or inside(x, y, head):
                    continue
                h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
                rgb = (r, g, b)
                blue = .52 < h < .77 and b > r*1.13
                warm = (h < .18 or h > .94) and s > .22 and r > b*1.13
                in_rider = bool(rider_mask.getpixel((x, y)))
                if blue:
                    # Preserve shading while moving all uniform blue to the
                    # actual allied swordmaster's medium blue family.
                    k = .90 + .15*v
                    rgb = tuple(round(c*k) for c in C[1])
                    counts['blue_uniform'] += 1
                elif in_rider and not warm and v > .24:
                    # Shoulder/chest/forearm and thigh plates remain ivory;
                    # the formerly charcoal sleeves and tunic become blue.
                    if v > .60 and s < .28:
                        k = .78 + .22*v
                        rgb = tuple(round(c*k) for c in C[2])
                        counts['ivory_armor'] += 1
                    elif v < .57 and (y < fy1+22 or x < cx+10):
                        k = .85 + .20*v
                        rgb = tuple(round(c*k) for c in C[1])
                        counts['blue_uniform'] += 1
                elif not in_rider and not warm and s < .28:
                    # Keep the dark exterior contour and delicate muzzle/eye
                    # details. Interior gray coat, mane and tail become white.
                    if inner.getpixel((x, y)) > 180:
                        value = round(182 + 61*(v**.63))
                        rgb = (max(0, value-5), value, min(255, value+3))
                        counts['white_horse'] += 1
                q.putpixel((x, y), (*rgb, a))
        assert q.getchannel('A').tobytes() == im.getchannel('A').tobytes()
        poses[f] = q
        REG.append({'class_id': 1, 'frame': f, 'source': BASE['profiles']['1']['newFrames'][key],
                    'source_sha256': file_hash(ROOT / BASE['profiles']['1']['newFrames'][key]),
                    'alpha_unchanged': True, 'pixel_positions_unchanged': True, 'materials': counts})
    return poses


def archers():
    poses = {}
    generated = Image.open(SRC / 'archer-generated.png').convert('RGBA')
    for n, f in enumerate([1, 4, 5]):
        cell = generated.crop((round(n*generated.width/3), 0, round((n+1)*generated.width/3), generated.height))
        bounds = cell.getchannel('A').point(lambda a: 255 if a >= 170 else 0).getbbox()
        q = quant(cell.crop(bounds), C)
        # Largest upper skin component is the face, never the drawn bow hand.
        skin = [(x, y) for y in range(q.height//2) for x in range(q.width)
                if q.getpixel((x, y)) == (*C[3], 255)]
        comp = max(parts(skin), key=len)
        fb = bbox(comp)
        # Consistent body scale and foot line, independent of the bow silhouette.
        scale = 127 / (q.height - round(fb[1]-22))
        small = q.resize((round(q.width*scale), round(q.height*scale)), Image.Resampling.NEAREST)
        foot = [(x, y) for y in range(max(0, small.height-5), small.height) for x in range(small.width)
                if small.getpixel((x, y))[3]]
        feet = bbox(foot)
        at = (round(208-(feet[0]+feet[2])/2), 256-small.height)
        im = Image.new('RGBA', (320, 256))
        im.alpha_composite(small, at)
        poses[f] = im
        REG.append({'class_id': 12, 'frame': f, 'generated_cell': n, 'source_crop': list(bounds),
                    'face_component': fb, 'scale': scale, 'registered_at': list(at),
                    'foot_y': 256, 'foot_center_x': 208, 'palette': [bytes(c).hex() for c in C],
                    'hair': 'low flat dark crew cut', 'bow_state': 'one nocked arrow' if f == 4 else 'empty bow'})
    return poses


def pegasus():
    specs = json.loads((SRC / 'pegasus-head-cells.json').read_text())
    gen = Image.open(SRC / 'pegasus-generated-v2.png').convert('RGBA')
    first = quant(gen.crop((0, 0, round(gen.width/4), round(gen.height/3))).resize((80, 60), Image.Resampling.NEAREST), PC)
    origin = specs[0]['crop'][:2]
    # Extract one generated crown, circlet, face and slender ponytail as a native
    # reusable head layer. All poses share this layer, eliminating AI volume drift.
    template = Image.new('RGBA', (80, 60))
    seed = Image.new('L', (80, 60))
    for y in range(60):
        for x in range(80):
            gx, gy = x+origin[0], y+origin[1]
            p = first.getpixel((x, y))
            if p[3] and inside(gx, gy, (171, 124, 215, 157)) and (p[:3] == PC[4] or inside(gx, gy, (176, 134, 194, 154))):
                seed.putpixel((x, y), 255)
    mask = seed.filter(ImageFilter.MaxFilter(3))
    for y in range(60):
        for x in range(80):
            if mask.getpixel((x, y)) and first.getpixel((x, y))[3]:
                template.putpixel((x, y), first.getpixel((x, y)))
    save(template, 'layers/pegasus-canonical-head.png', 'registered ImageGen crown/circlet/face/ponytail layer shared by all 12 poses')
    hair_points = [(x, y) for y in range(60) for x in range(80) if template.getpixel((x, y)) == (*PC[4], 255)]
    hair_count = len(hair_points)
    hair_box = bbox(hair_points)
    poses = {}
    for s in specs:
        f = int(s['frame'])
        im = old_frame(3, f)
        q = im.copy()
        b, face = s['head'], s['face']
        old_mask = Image.new('L', im.size)
        cap_points = []
        # Hair is one explicit material, face and circlet have hand-reviewed ROI.
        for y in range(max(0, b[1]-2), b[3]+2):
            for x in range(max(0, b[0]-2), b[2]+2):
                p = im.getpixel((x, y))
                if p[3] and (p[:3] in [PC[4], PC[3]] or inside(x, y, (face[0]-3, face[1]-5, face[2]+4, face[3]+1))):
                    old_mask.putpixel((x, y), 255)
                if p[3] and p[:3] == PC[4] and y <= face[1]+2:
                    cap_points.append((x, y))
        cap_points.extend([(face[0]-1, face[1]), (face[2], face[1]),
                           (face[0]-1, face[3]), (face[2], face[3])])
        cap_mask = Image.new('L', im.size)
        ImageDraw.Draw(cap_mask).polygon(hull(cap_points), fill=255)
        grown = old_mask.filter(ImageFilter.MaxFilter(3))
        cap_mask = cap_mask.filter(ImageFilter.MaxFilter(3))
        for y in range(q.height):
            for x in range(q.width):
                p = im.getpixel((x, y))
                remove = bool(cap_mask.getpixel((x, y)) or old_mask.getpixel((x, y)))
                if grown.getpixel((x, y)) and p[:3] == PC[0] and (y < face[3] or x > face[2]+13):
                    remove = True
                if remove:
                    # Where the former long side lock occluded the collar,
                    # keep the established navy underpaint below the chin.
                    q.putpixel((x, y), (*PC[0], 255) if y >= face[3] and x < face[2]+8 else (0, 0, 0, 0))
        # Register the common head on the original face center. Constant source
        # layer and scale guarantee identical crown and ponytail thickness.
        dx = round((face[0]+face[2])/2 - (specs[0]['face'][0]+specs[0]['face'][2])/2)
        dy = round((face[1]+face[3])/2 - (specs[0]['face'][1]+specs[0]['face'][3])/2)
        at = (origin[0]+dx, origin[1]+dy)
        q.alpha_composite(template, at)
        # Retired outline/diadem fragments can become isolated when the large
        # old hair silhouette is removed. Limit cleanup to that old head ROI.
        opaque = [(x, y) for y in range(q.height) for x in range(q.width) if q.getpixel((x, y))[3]]
        for comp in parts(opaque):
            cb = bbox(comp)
            if len(comp) < 32 and cb[0] >= b[0]-5 and cb[1] >= b[1]-5 and cb[2] <= b[2]+5 and cb[3] <= b[3]+5:
                for x, y in comp:
                    q.putpixel((x, y), (0, 0, 0, 0))
        poses[f] = q
        REG.append({'class_id': 3, 'frame': f, 'head_layer': 'layers/pegasus-canonical-head.png',
                    'translation': [dx, dy], 'head_scale': 1, 'hair_pixels': hair_count,
                    'local_hair_bounds': hair_box, 'body_wings_lance_motion_preserved': True,
                    'modified_region': [min(b[0]-4, at[0]), min(b[1]-4, at[1]), max(b[2]+4, at[0]+80), max(b[3]+4, at[1]+60)]})
    return poses


def review(cid, poses):
    order = list(poses)
    cols = min(4, len(order))
    tilew, tileh = (360, 330) if cid != 3 else (360, 440)
    for light in [False, True]:
        board = Image.new('RGB', (cols*tilew, ((len(order)+cols-1)//cols)*tileh), (220, 222, 216) if light else (32, 45, 53))
        d = ImageDraw.Draw(board)
        for n, f in enumerate(order):
            x, y = n % cols * tilew, n // cols * tileh
            d.text((x+tilew/2, y+18), f'源姿势 {f}', font=font(17), anchor='mm', fill=(23, 38, 56) if light else (235, 239, 239))
            im = poses[f]
            board.paste(im, (x+(tilew-im.width)//2, y+38), im)
        save(board, f'review/class-{cid}-'+('light' if light else 'dark')+'.png', 'all poses / native display size / dark-light transparency inspection')


def main(publish=False):
    allposes = {1: cavalry(), 3: pegasus(), 12: archers()}
    for cid, poses in allposes.items():
        mapping = copy.deepcopy(BASE['mappings'][str(cid)])
        order = list(mapping['frame_mapping'])
        mapping['previous_revision'] = mapping.get('revision')
        mapping['frame_mapping'] = {str(f): save(im, f'class-{cid}/frame-{f:03}.png', 'registered review animation source pose') for f, im in poses.items()}
        atlas = Image.new('RGBA', (len(order)*320, poses[int(order[0])].height))
        for n, key in enumerate(order):
            atlas.alpha_composite(poses[int(key)], (n*320, 0))
        mapping['output_atlas'] = save(atlas, f'class-{cid}/battle-atlas.png', 'offline multi-pose atlas')
        notes = {1: '战马、鬃毛与尾巴统一白色，骑兵增加剑豪中蓝与米白；保留原像素轮廓、长枪与动作。',
                 3: '全部战斗姿势共用固定尺寸红发头部层，统一头顶、鬓发和马尾厚度；保留身体、飞马、翅膀和攻击时序。',
                 12: '身体重制为狙击手的中蓝／米白／深蓝配色，发型改为深蓝板寸；待机、满弓搭箭和松弦空弓三姿势同步。'}
        mapping.update(revision=REV, modified_by='Codex', status='review_candidate', runtime_integrated=False,
                       review_note=notes[cid], art_mode='ImageGen targeted edit, native registration and material normalization',
                       qa_report='../../../'+REV+'/verification.json',
                       batches=[{'id': '2026-10-31 外观修订', 'review': '../../../'+REV+f'/review/class-{cid}-light.png', 'status': 'pending_user_visual_acceptance'}])
        mapping.pop('runtime_integration', None)
        mapping['records'] = [{**a, 'path': mapping['frame_mapping'][str(a['frame'])]} for a in REG if a['class_id'] == cid]
        write(OUT/f'class-{cid}-mapping.json', mapping)
        review(cid, poses)
        if publish:
            write(ROOT / BASE['profiles'][str(cid)]['mapping'], mapping)
    write(OUT/'registration.json', {'revision': REV, 'frames': REG})
    write(OUT/'asset-manifest.json', {'revision': REV, 'image_generation': 'built-in imagegen', 'assets': ASSETS,
                                    'runtime_integrated': False, 'source_generated_images_preserved': True})
    print(json.dumps({'poses': {k: len(v) for k, v in allposes.items()}, 'published': publish}))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--publish', action='store_true')
    main(p.parse_args().publish)
