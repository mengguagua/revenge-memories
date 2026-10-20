#!/usr/bin/env python3
"""Review-only material recolor: match accepted walking armor, keep geometry."""
import hashlib
import json
from collections import Counter
from PIL import Image,ImageDraw
from revise_gold_knight_idle import ROOT,PALETTE

REVISION='gold-knight-idle-style-v6-20261020'
OUT=ROOT/REVISION
OLD=ROOT/'gold-knight-idle-v2-20261020/frames'
# Material regions only: horse coat, face/eyes, mane, tail, moving legs and spear
# remain outside these masks. The collar and saddle edging retain dark cloth.
ARMOR={
 'helmet':[(48,17),(54,17),(59,22),(59,25),(54,27),(52,25),(44,25),(44,23)],
 'helmet_neck_guard':[(54,24),(58,24),(59,29),(55,31),(53,28)],
 'chest':[(47,31),(53,30),(58,33),(60,38),(57,42),(52,43),(48,39),(46,34)],
 'shoulder':[(58,28),(63,28),(66,31),(66,35),(62,35),(59,33)],
 'arm':[(62,34),(67,35),(67,39),(64,43),(60,44),(58,42),(61,39)],
 'gauntlet':[(57,42),(61,41),(65,44),(64,47),(59,47),(57,45)],
 'greave':[(55,47),(60,48),(63,54),(62,63),(57,64),(55,58)],
}
TRIM={
 'breast_collar':[(35,54),(41,53),(47,54),(47,58),(43,61),(36,60),(33,57)],
 'saddle_edging':[(64,45),(72,46),(79,51),(80,61),(66,62),(63,56)],
}


def region(polygons):
    mask=Image.new('L',(96,96));draw=ImageDraw.Draw(mask)
    for points in polygons.values():draw.polygon(points,fill=255)
    return mask


def create():
    (OUT/'frames').mkdir(exist_ok=True)
    (OUT/'source').mkdir(exist_ok=True)
    original=[Image.open(OLD/f'idle-{i:03}.png').convert('RGBA')for i in range(6)]
    armor=region(ARMOR);trim=region(TRIM)
    colors=[tuple(bytes.fromhex(c))for c in PALETTE]
    gold,shadow=colors[5],colors[6]
    replacement={colors[i]:gold for i in [3,4,7]}
    replacement.update({colors[i]:shadow for i in [1,2]})
    changes={};counts=Counter()
    for y in range(96):
        for x in range(96):
            old=original[1].getpixel((x,y))
            if old[3]!=255 or any(im.getpixel((x,y))!=old for im in original):continue
            new=None
            if armor.getpixel((x,y)):new=replacement.get(old[:3])
            elif trim.getpixel((x,y)):
                # The saddle cloth remains dark; only its metallic edging changes.
                new={colors[3]:gold,colors[4]:gold,colors[7]:gold,colors[2]:shadow}.get(old[:3])
            if new and new!=old[:3]:changes[(x,y)]=(*new,255);counts[bytes(old[:3]).hex()+'->'+bytes(new).hex()]+=1
    material_mask=Image.new('L',(96,96))
    for point in changes:material_mask.putpixel(point,255)
    material_mask.save(OUT/'source/recolored-materials-mask.png')
    armor.save(OUT/'source/armor-region-mask.png');trim.save(OUT/'source/trim-region-mask.png')
    atlas=Image.new('RGBA',(96*6,96));records=[]
    for i,source in enumerate(original):
        frame=source.copy()
        for point,color in changes.items():frame.putpixel(point,color)
        assert frame.getchannel('A').tobytes()==source.getchannel('A').tobytes()
        path=OUT/f'frames/idle-{i:03}.png';frame.save(path,optimize=True)
        atlas.alpha_composite(frame,(i*96,0))
        records.append({'source_index':i,'path':path.relative_to(ROOT).as_posix(),
                        'size':list(frame.size),'bytes':path.stat().st_size,
                        'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    atlas.save(OUT/'idle-atlas.png',optimize=True)
    (OUT/'asset-manifest.json').write_text(json.dumps({
      'revision':REVISION,'runtime_integrated':False,'image_generation_invoked':False,'chat_image_output':False,
      'method':'material-only palette remap on static rider armor and gold equipment edging',
      'reference':'gold-knight-side-anchor-v5-20261020/frames/frame-006.png',
      'palette':PALETTE,'armor_regions':ARMOR,'trim_regions':TRIM,
      'changed_pixels_per_frame':len(changes),'color_replacements':dict(counts),
      'preserved':['horse gray-white coat','mane/tail','rider face','weapon','pose geometry','leg animation','registration','timing','walking frames'],
      'frames':records},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'changed_pixels_per_frame':len(changes),'replacements':dict(counts)},ensure_ascii=False))


def review_sheet():
    """Save the review on the gallery filesystem; never emit a chat image."""
    from export_gallery import font
    sheet=Image.new('RGB',(1272,856),(14,21,26));draw=ImageDraw.Draw(sheet)
    title='黄金骑士 · 待机与行走材质对照'
    draw.text((636,24),title,font=font(22),fill='#e5edef',anchor='mt')
    entries=[
      ('修改前待机',OLD/'idle-000.png','白灰高光较多'),
      ('本轮待机 · 行走配色',OUT/'frames/idle-000.png','低饱和金色盔甲 · 灰白马身保留'),
      ('配色参考 · 向左行走',ROOT/'gold-knight-side-anchor-v5-20261020/frames/frame-006.png','已验收行走稿 · 本轮保持'),
    ]
    for row,bg in enumerate([(32,45,53),(220,222,216)]):
        ink='#e5edef' if row==0 else '#26323b'
        for col,(label,path,note) in enumerate(entries):
            x=20+col*416;y=64+row*388
            draw.rounded_rectangle((x,y,x+400,y+372),radius=10,fill=bg)
            draw.text((x+200,y+18),label,font=font(18),fill=ink,anchor='mt')
            image=Image.open(path).convert('RGBA')
            padded=Image.new('RGBA',(128,96))
            padded.alpha_composite(image,((128-image.width)//2,0))
            sprite=padded.resize((384,288),Image.Resampling.NEAREST)
            sheet.paste(sprite,(x+8,y+50),sprite)
            draw.text((x+200,y+345),note,font=font(14),fill=ink,anchor='mt')
            assert draw.textbbox((x+200,y+18),label,font=font(18),anchor='mt')[0]>=x+16
            assert draw.textbbox((x+200,y+345),note,font=font(14),anchor='mt')[2]<=x+384
    sheet.save(OUT/'style-comparison.png',optimize=True)


if __name__=='__main__':
    create()
    review_sheet()
