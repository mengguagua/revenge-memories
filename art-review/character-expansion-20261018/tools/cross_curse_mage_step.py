#!/usr/bin/env python3
"""Pair each raised sleeve with the opposite existing lower-robe step."""
import json
from PIL import Image, ImageDraw
from revise_curse_mage_map import ROOT, PALETTE
from inset_curse_mage_sleeves import asset

REVISION = 'curse-mage-cross-step-v5-20261020'
OUT = ROOT / REVISION
PREVIOUS = ROOT / 'curse-mage-low-arm-v4-20261020'
ACCEPTED_WALK = ROOT / 'curse-mage-map-v2-20261020'
HEM_Y = 65
ALIASES = [0, 1, 2, 1, 0, 1]
LOWER_PHASES = [2, 1, 0]


def create():
    for folder in ['source', 'idle', 'walk']:
        (OUT / folder).mkdir(parents=True, exist_ok=True)
    previous = [Image.open(PREVIOUS / f'idle/frame-{i:03}.png').convert('RGBA') for i in range(3)]
    poses = []
    for phase, lower_phase in enumerate(LOWER_PHASES):
        frame = previous[phase].copy()
        lower = previous[lower_phase].crop((0, HEM_Y, 96, 96))
        # Replace the full lower layer, including its transparent margins.
        # Hood, eyes, torso and the newly approved low sleeves are untouched.
        frame.paste(lower, (0, HEM_Y))
        lower.save(OUT / f'source/hem-for-pose-{phase:03}.png', optimize=True)
        poses.append(frame)
    records = []
    atlas = Image.new('RGBA', (576, 96))
    for index, phase in enumerate(ALIASES):
        records.append(asset(OUT / f'idle/frame-{index:03}.png', index, poses[phase]))
        atlas.alpha_composite(poses[phase], (96 * index, 0))
    atlas.save(OUT / 'idle-atlas.png', optimize=True)
    down_records = []
    walk = Image.new('RGBA', (1408, 96))
    for index in range(11):
        if index in [4, 5, 8, 9, 10]:
            phase = {4: 0, 5: 1, 8: 0, 9: 1, 10: 2}[index]
            frame = Image.new('RGBA', (128, 96))
            frame.alpha_composite(poses[phase], (16, 16))
            down_records.append(asset(OUT / f'walk/frame-{index:03}.png', index, frame))
        else:
            frame = Image.open(ACCEPTED_WALK / f'walk/frame-{index:03}.png').convert('RGBA')
        walk.alpha_composite(frame, (128 * index, 0))
    walk.save(OUT / 'walk-atlas.png', optimize=True)
    manifest = {
        'revision': REVISION, 'runtime_integrated': False,
        'image_generation_invoked': False, 'chat_image_output': False,
        'method': 'Swap only existing left/right lower-robe step phases below y65; no transforms or recoloring.',
        'previous_revision': PREVIOUS.name, 'lower_layer_y': HEM_Y,
        'lower_source_phase_for_each_pose': LOWER_PHASES,
        'pairing': ['screen-left hand raised / screen-right leg step', 'both arms lowered / neutral step',
                    'screen-right hand raised / screen-left leg step'],
        'raised_arm_degrees_kept': 24, 'inward_pixels_kept': 6,
        'palette': PALETTE, 'idle_frames': records, 'down_frames': down_records,
        'preserved': ['all pixels above y65', 'neutral pose', 'hood and eyes', 'torso and sleeves',
                      'original lower-step shapes', 'palette', 'timing', 'accepted up/right/left artwork']
    }
    (OUT / 'asset-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'revision': REVISION, 'lower_phase_pairing': LOWER_PHASES}, ensure_ascii=False))


def preview():
    from export_gallery import font
    sheet = Image.new('RGB', (1040, 816), (14, 21, 26))
    draw = ImageDraw.Draw(sheet)
    draw.text((520, 16), '咒法师 · 手脚交错', font=font(22), anchor='mt', fill='#e9f0f0')
    for row, (folder, label) in enumerate([(PREVIOUS, '修改前'), (OUT, '本轮交错')]):
        for phase, title in enumerate(['左手／右腿', '双臂放下', '右手／左腿']):
            x, y = 16 + 340 * phase, 64 + 368 * row
            draw.rounded_rectangle((x, y, x + 328, y + 348), radius=10, fill=(32, 45, 53))
            text = label + ' · ' + title if row else label + ' · 姿势' + str(phase + 1)
            draw.text((x + 164, y + 12), text, font=font(16), anchor='mt', fill='#e9f0f0')
            frame = Image.open(folder / f'idle/frame-{phase:03}.png').convert('RGBA')
            frame = frame.resize((288, 288), Image.Resampling.NEAREST)
            sheet.paste(frame, (x + 20, y + 45), frame)
            bounds = draw.textbbox((x + 164, y + 12), text, font=font(16), anchor='mt')
            assert bounds[0] >= x + 16 and bounds[2] <= x + 312
    sheet.save(OUT / 'before-after.png', optimize=True)


if __name__ == '__main__':
    create()
    preview()
