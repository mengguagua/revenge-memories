#!/usr/bin/env python3
"""Review-only pixel-layer edit: veiled face, muted enemy robe, fixed head."""
from pathlib import Path
from collections import Counter
import hashlib,json
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
REVISION='curse-mage-idle-v1-20261020'
OUT=ROOT/REVISION
SOURCE=ROOT/'professions/class-15-enemy/maps/idle-frames'
PALETTE={
    'outline':'1c2135',
    'hood_void':'151827',
    'robe_shadow':'343552',
    'robe_mid':'595a78',
    'robe_light':'8b89a5',
    'eye_light':'bfc4dc',
}
MOVING={
    'left_sleeve':[(14,39),(28,39),(35,44),(36,65),(31,68),(14,68)],
    'right_sleeve':[(62,37),(79,37),(81,65),(60,65),(58,57),(58,47)],
    'lower_robe':[(24,65),(67,65),(73,81),(18,81)],
}
# A single dark interior replaces all face/beard pixels, inside the hood rim.
FACE=[(42,26),(48,27),(52,31),(55,36),(53,40),(49,43),(43,43),(38,39),(36,34),(38,29)]
EYES=[(41,32,43,33),(48,32,50,33)]
ALIASES=[0,1,2,1,0,1]


def color(key):return (*bytes.fromhex(PALETTE[key]),255)


def simplify(source):
    result=Image.new('RGBA',source.size)
    for y in range(source.height):
        for x in range(source.width):
            red,green,blue,alpha=source.getpixel((x,y))
            if alpha<128:continue
            luminance=.2126*red+.7152*green+.0722*blue
            key='outline' if luminance<30 else 'robe_shadow' if luminance<75 else 'robe_mid' if luminance<145 else 'robe_light'
            result.putpixel((x,y),color(key))
    return result


def create():
    (OUT/'frames').mkdir(parents=True,exist_ok=True)
    (OUT/'source').mkdir(exist_ok=True)
    plates=[simplify(Image.open(SOURCE/f'frame-{i:03}.png').convert('RGBA'))for i in range(3)]
    motion=Image.new('L',(96,96));draw=ImageDraw.Draw(motion)
    for polygon in MOVING.values():draw.polygon(polygon,fill=255)
    motion.save(OUT/'source/moving-robe-mask.png',optimize=True)
    face=Image.new('L',(96,96));ImageDraw.Draw(face).polygon(FACE,fill=255)
    face.save(OUT/'source/hood-interior-mask.png',optimize=True)
    eye_mask=Image.new('L',(96,96));draw=ImageDraw.Draw(eye_mask)
    for rect in EYES:draw.rectangle(rect,fill=255)
    eye_mask.save(OUT/'source/eyes-mask.png',optimize=True)
    canonical=[]
    for i in range(3):
        frame=plates[0].copy()
        frame.paste(plates[i],(0,0),motion)
        draw=ImageDraw.Draw(frame);draw.polygon(FACE,fill=color('hood_void'))
        for rect in EYES:
            draw.rectangle(rect,fill=color(['eye_light','robe_light','hood_void'][i]))
        canonical.append(frame)
    atlas=Image.new('RGBA',(576,96));assets=[]
    for index,phase in enumerate(ALIASES):
        frame=canonical[phase];path=OUT/f'frames/idle-{index:03}.png'
        frame.save(path,optimize=True);atlas.alpha_composite(frame,(96*index,0))
        assets.append({'source_index':index,'canonical_frame':phase,'path':path.relative_to(ROOT).as_posix(),
          'size':list(frame.size),'visible_bounds':list(frame.getbbox()),'bytes':path.stat().st_size,
          'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
          'palette_colors':len(Counter(p for p in frame.getdata()if p[3]))})
    atlas.save(OUT/'idle-atlas.png',optimize=True)
    manifest={'revision':REVISION,'runtime_integrated':False,'image_generation_invoked':False,'chat_image_output':False,
      'method':'existing pixel layers; explicit robe motion masks; shared head and torso; material recolor; dark hood interior',
      'reference_palette':'catalog/enemy-troop-palette.json; lower-saturation midtone and highlight',
      'palette':PALETTE,'canvas':[96,96],'source_anchor':[12,24],'output_anchor':[48,96],
      'fixed_parts':['hood','head silhouette','central torso','chest fastening'],
      'moving_regions':MOVING,'face_region':FACE,'eyes':EYES,
      'eye_cycle':['both bright','both dim','both hidden','both dim'],
      'cycle':[0,1,2,1],'ticks':[14,8,14,8],'fps':60.0988,
      'original_artwork_retained_at':SOURCE.relative_to(ROOT).as_posix(),'frames':assets}
    (OUT/'asset-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'revision':REVISION,'palette':PALETTE,'frames':assets},ensure_ascii=False))
    return canonical


def review_sheet():
    from export_gallery import font
    source=Image.open(ROOT/'source-input/legacy-assets/assets/original/graphics/map_units/class_15_enemy.png').convert('RGBA')
    sheet=Image.new('RGB',(1368,728),(14,21,26));draw=ImageDraw.Draw(sheet)
    draw.text((684,18),'咒法师 · 固定兜帽、袖袍摆动与眼睛明暗',font=font(22),anchor='mt',fill='#e9f0f0')
    for row,bg in enumerate([(32,45,53),(220,222,216)]):
        ink='#e9f0f0' if row==0 else '#26323b'
        for i,phase in enumerate(['亮眼','暗眼','隐于兜帽']):
            x=20+448*i;y=64+324*row
            draw.rounded_rectangle((x,y,x+432,y+300),radius=10,fill=bg)
            title=f'姿势 {i+1} · {phase}'
            draw.text((x+216,y+14),title,font=font(18),anchor='mt',fill=ink)
            original=source.crop((24*i,0,24*(i+1),24)).resize((192,192),Image.Resampling.NEAREST)
            revised=Image.open(OUT/f'frames/idle-{i:03}.png').convert('RGBA').resize((192,192),Image.Resampling.NEAREST)
            for offset,im,label in [(16,original,'原作'),(224,revised,'本轮六色稿')]:
                sheet.paste(im,(x+offset,y+48),im)
                draw.text((x+offset+96,y+256),label,font=font(14),anchor='mt',fill=ink)
            box=draw.textbbox((x+216,y+14),title,font=font(18),anchor='mt')
            assert box[0]>=x+16 and box[2]<=x+416
    draw.text((684,705),'固定中轴 · 亮→暗→熄灭→暗 · 原14／8／14／8帧节奏',font=font(14),anchor='mt',fill='#a0b2bd')
    sheet.save(OUT/'pose-review.png',optimize=True)


if __name__=='__main__':
    create()
    review_sheet()
