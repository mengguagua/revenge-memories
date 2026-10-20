#!/usr/bin/env python3
"""Review-only registered pixel layers for the caster's idle and four gaits."""
from pathlib import Path
from collections import deque
import hashlib,json
from PIL import Image,ImageDraw
from revise_curse_mage_idle import ROOT,PALETTE,color,simplify,EYES

REVISION='curse-mage-map-v2-20261020'
OUT=ROOT/REVISION
OLD=ROOT/'professions/class-15-enemy/maps/tactical-native-frames'
ALIASES=[0,1,2,1,0,1]
ARM_POLYGON=[(23,39),(29,39),(35,43),(38,49),(38,63),(32,66),(24,64),(19,59),(18,51),(19,44)]
ARM_PIVOT=(34,44)
SIDE_FACE=[(73,40),(77,41),(80,45),(79,49),(77,52),(77,56),(73,59),(68,57),(66,53),(68,48),(70,44)]


def mask(size,polygon):
    im=Image.new('L',size);ImageDraw.Draw(im).polygon(polygon,fill=255);return im


def place(im,xy):
    out=Image.new('RGBA',im.size);out.alpha_composite(im,xy);return out


def mirror(im,axis):
    # Reflection about integer pixel-center x=axis rather than a canvas edge.
    out=Image.new('RGBA',im.size)
    out.alpha_composite(im.transpose(Image.Transpose.FLIP_LEFT_RIGHT),(2*axis-(im.width-1),0))
    return out


def layer(im,region):
    result=Image.new('RGBA',im.size);result.paste(im,(0,0),region);return result


def connected(im):
    """Remove disconnected alpha crumbs from thresholded original artwork."""
    remaining={(x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))[3]}
    parts=[]
    while remaining:
        q=deque([remaining.pop()]);part=[]
        while q:
            x,y=q.popleft();part.append((x,y))
            for dx in [-1,0,1]:
                for dy in [-1,0,1]:
                    if (x+dx,y+dy)in remaining:
                        remaining.remove((x+dx,y+dy));q.append((x+dx,y+dy))
        parts.append(part)
    if len(parts)>1:
        for part in sorted(parts,key=len,reverse=True)[1:]:
            if len(part)>12:raise ValueError('Detached garment part requires repair')
            for p in part:im.putpixel(p,(0,0,0,0))
    return im


def idle_poses():
    previous=[Image.open(ROOT/f'curse-mage-idle-v1-20261020/frames/idle-{i:03}.png').convert('RGBA')for i in range(3)]
    sleeve=layer(previous[0],mask((96,96),ARM_POLYGON))
    raised=sleeve.rotate(-52,resample=Image.Resampling.NEAREST,center=ARM_PIVOT)
    sleeves={'left-down':sleeve,'left-up':raised,'right-down':mirror(sleeve,48),'right-up':mirror(raised,48)}
    for name,im in sleeves.items():im.save(OUT/f'source/{name}.png',optimize=True)
    body=previous[0].copy()
    # Clear both complete shoulder/sleeve windows, not just the wrist.
    body.paste((0,0,0,0),(0,39,38,66));body.paste((0,0,0,0),(59,39,96,66))
    body.paste((0,0,0,0),(0,65,96,96))
    shoulder=Image.new('RGBA',(96,96))
    shoulder.paste(previous[0].crop((34,39,40,52)),(34,39))
    body.alpha_composite(shoulder);body.alpha_composite(mirror(shoulder,48))
    body.save(OUT/'source/fixed-front-body.png',optimize=True)
    hem=Image.new('L',(96,96));ImageDraw.Draw(hem).rectangle((0,65,95,95),fill=255)
    lower=[layer(previous[0],hem),layer(previous[1],hem),layer(mirror(previous[0],48),hem)]
    result=[]
    for phase,(left,right)in enumerate([('left-up','right-down'),('left-down','right-down'),('left-down','right-up')]):
        frame=Image.new('RGBA',(96,96))
        frame.alpha_composite(sleeves[left]);frame.alpha_composite(sleeves[right])
        frame.alpha_composite(lower[phase]);frame.alpha_composite(body)
        draw=ImageDraw.Draw(frame)
        for rect in EYES:draw.rectangle(rect,fill=color(['eye_light','robe_light','hood_void'][phase]))
        result.append(connected(frame))
    return result


def walk_poses(idle):
    original=[simplify(Image.open(OLD/f'frame-{i:03}.png').convert('RGBA'))for i in range(4)]
    # Up: register one hood at x=64 and use a common upper body. The lower
    # robe sweeps to alternating sides without translating that body plate.
    up_plate=place(original[0],(10,0));up_body=up_plate.copy()
    left=Image.new('RGBA',(128,96));left.paste(up_plate.crop((0,0,65,68)),(0,0))
    up_body=left.copy();up_body.alpha_composite(mirror(left,64))
    up_hem_mask=Image.new('L',(128,96));ImageDraw.Draw(up_hem_mask).rectangle((0,68,127,95),fill=255)
    up_hem=layer(up_plate,up_hem_mask)
    walk={}
    for index,hem in enumerate([up_hem,mirror(up_hem,64)]):
        frame=hem.copy();frame.alpha_composite(up_body);walk[index]=connected(frame)
    up_body.save(OUT/'source/fixed-up-body.png',optimize=True)
    up_hem_mask.save(OUT/'source/up-robe-mask.png',optimize=True)

    # Side: preserve the existing two lower-robe poses after registration;
    # the hood and torso come from the same first side-view plate.
    side0=original[2];side1=place(original[3],(4,0))
    moving=Image.new('L',(128,96));draw=ImageDraw.Draw(moving)
    for rect in [(0,78,127,95),(0,60,57,77),(74,60,127,77)]:draw.rectangle(rect,fill=255)
    for index,source in [(2,side0),(3,side1)]:
        frame=side0.copy();frame.paste(source,(0,0),moving)
        draw=ImageDraw.Draw(frame);draw.polygon(SIDE_FACE,fill=color('hood_void'))
        draw.rectangle((75,45,77,46),fill=color('robe_light'))
        walk[index]=connected(frame)
    walk[6]=mirror(walk[2],64);walk[7]=mirror(walk[3],64)
    moving.save(OUT/'source/side-robe-mask.png',optimize=True)
    side_body=walk[2].copy();side_body.paste((0,0,0,0),(0,78,128,96))
    side_body.save(OUT/'source/fixed-side-body.png',optimize=True)

    # Three real idle poses are reused pixel-for-pixel for requested down gait.
    for index,phase in [(4,0),(5,1),(8,0),(9,1),(10,2)]:
        frame=Image.new('RGBA',(128,96));frame.alpha_composite(idle[phase],(16,16));walk[index]=frame
    return walk


def reference_atlas():
    original=Image.open(ROOT/'source-input/corrected-tactical-walk/class-15-enemy.png').convert('RGBA')
    idle=Image.open(ROOT/'source-input/legacy-assets/assets/original/graphics/map_units/class_15_enemy.png').convert('RGBA')
    atlas=Image.new('RGBA',(352,24));atlas.alpha_composite(original)
    for phase in range(3):
        plate=idle.crop((24*phase,0,24*(phase+1),24))
        atlas.alpha_composite(plate,(32*(8+phase)+4,4))
    atlas.save(OUT/'source/review-reference.png',optimize=True)
    assert atlas.crop((0,0,256,24)).tobytes()==original.tobytes()


def save_frames(frames,folder,size):
    records=[];atlas=Image.new('RGBA',(size[0]*len(frames),size[1]))
    for i,frame in sorted(frames.items()):
        path=OUT/f'{folder}/frame-{i:03}.png';frame.save(path,optimize=True)
        atlas.alpha_composite(frame,(i*size[0],0))
        records.append({'source_index':i,'path':path.relative_to(ROOT).as_posix(),'size':list(size),'bytes':path.stat().st_size,
          'visible_bounds':list(frame.getbbox()),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    atlas.save(OUT/f'{folder}-atlas.png',optimize=True)
    return records


def create():
    for folder in ['source','idle','walk']:(OUT/folder).mkdir(parents=True,exist_ok=True)
    idle=idle_poses();walk=walk_poses(idle);reference_atlas()
    idle_records=save_frames({i:idle[p]for i,p in enumerate(ALIASES)},'idle',(96,96))
    walk_records=save_frames(walk,'walk',(128,96))
    manifest={'revision':REVISION,'runtime_integrated':False,'image_generation_invoked':False,'chat_image_output':False,
      'palette':PALETTE,'idle_arm_cycle':['screen-left raised / right lowered','both lowered','left lowered / screen-right raised','both lowered'],
      'arm_mirror_axis':48,'arm_pivot':list(ARM_PIVOT),'arm_raise_degrees':-52,
      'idle_cycle':[0,1,2,1],'idle_ticks':[14,8,14,8],'up_axis':64,'up_robe_start_y':68,
      'side_registration':{'2':[0,0],'3':[4,0]},'side_fixed_torso_region':[58,31,74,78],
      'down_idle_reuse':{'8':0,'9':1,'10':2},'down_translation':[16,16],
      'down_reference':'Appended slots8-10 contain genuine original idle0-2 at native offset[4,4]. Original walking slots0-7 remain pixel-identical.',
      'down_cycle':[8,9,10,9],'down_ticks':[14,8,14,8],'down_repeats':2,
      'idle_frames':idle_records,'walk_frames':walk_records}
    (OUT/'asset-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'revision':REVISION,'idle_frames':len(idle_records),'walk_frames':len(walk_records),'palette':PALETTE},ensure_ascii=False))


def review_sheets():
    from export_gallery import font
    sheet=Image.new('RGB',(1040,816),(14,21,26));draw=ImageDraw.Draw(sheet)
    draw.text((520,18),'咒法师 · 左右对称抬臂三姿势',font=font(22),fill='#e9f0f0',anchor='mt')
    for row,bg in enumerate([(32,45,53),(220,222,216)]):
        ink='#e9f0f0'if row==0 else '#26323b'
        for i,label in enumerate(['画面左臂抬起','双臂放下','画面右臂抬起']):
            x=16+340*i;y=64+368*row
            draw.rounded_rectangle((x,y,x+328,y+348),radius=10,fill=bg)
            draw.text((x+164,y+12),label,font=font(18),fill=ink,anchor='mt')
            image=Image.open(OUT/f'idle/frame-{i:03}.png').convert('RGBA').resize((288,288),Image.Resampling.NEAREST)
            sheet.paste(image,(x+20,y+45),image)
            assert draw.textbbox((x+164,y+12),label,font=font(18),anchor='mt')[0]>=x+16
    sheet.save(OUT/'idle-poses.png',optimize=True)
    sheet=Image.new('RGB',(920,1160),(14,21,26));draw=ImageDraw.Draw(sheet)
    rows=[('向上 · 固定中线、交替袍摆',[0,1]),('向下 · 完整复用待机三姿势',[8,9,10]),('向右 · 固定头部和躯干',[2,3]),('向左 · 固定头部和躯干',[6,7])]
    for row,(label,indices)in enumerate(rows):
        y=16+row*284
        draw.text((460,y+10),label,font=font(20),fill='#e9f0f0',anchor='mt')
        start=(920-len(indices)*280-(len(indices)-1)*12)//2
        for col,index in enumerate(indices):
            x=start+col*292
            draw.rounded_rectangle((x,y+46,x+280,y+268),radius=10,fill=(32,45,53))
            image=Image.open(OUT/f'walk/frame-{index:03}.png').convert('RGBA').resize((256,192),Image.Resampling.NEAREST)
            sheet.paste(image,(x+12,y+56),image)
    sheet.save(OUT/'walk-poses.png',optimize=True)


if __name__=='__main__':
    create()
    review_sheets()
