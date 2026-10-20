#!/usr/bin/env python3
"""Lower only front-view raised sleeves; keep every accepted gait intact."""
import hashlib,json
from PIL import Image,ImageDraw
from revise_curse_mage_map import ROOT,mirror,place,connected,PALETTE,EYES,ARM_PIVOT
from inset_curse_mage_sleeves import asset

REVISION='curse-mage-low-arm-v4-20261020'
OUT=ROOT/REVISION
PREVIOUS=ROOT/'curse-mage-sleeve-inset-v3-20261020'
BODY_SOURCE=ROOT/'curse-mage-map-v2-20261020'
ANGLE=-24
INSET=6
ALIASES=[0,1,2,1,0,1]


def create():
    for folder in ['source','idle','walk']:(OUT/folder).mkdir(parents=True,exist_ok=True)
    original=[Image.open(PREVIOUS/f'idle/frame-{i:03}.png').convert('RGBA')for i in range(3)]
    body=Image.open(BODY_SOURCE/'source/fixed-front-body.png').convert('RGBA')
    down=Image.open(BODY_SOURCE/'source/left-down.png').convert('RGBA')
    # Re-render once from the intact lowered sleeve, avoiding repeated resampling.
    up=place(down.rotate(ANGLE,resample=Image.Resampling.NEAREST,center=ARM_PIVOT),(INSET,0))
    sleeves={'left-up':up,'right-up':mirror(up,48),'left-down':down,'right-down':mirror(down,48)}
    for name,im in sleeves.items():im.save(OUT/f'source/{name}.png',optimize=True)
    result=[]
    for phase,(left,right)in enumerate([('left-up','right-down'),('left-down','right-down'),('left-down','right-up')]):
        frame=Image.new('RGBA',(96,96));frame.alpha_composite(sleeves[left]);frame.alpha_composite(sleeves[right])
        frame.alpha_composite(original[phase].crop((0,65,96,96)),(0,65));frame.alpha_composite(body)
        for x0,y0,x1,y1 in EYES:frame.paste(original[phase].crop((x0,y0,x1+1,y1+1)),(x0,y0))
        result.append(connected(frame))
    assert result[1].tobytes()==original[1].tobytes()
    idle=[];atlas=Image.new('RGBA',(576,96))
    for i,phase in enumerate(ALIASES):
        idle.append(asset(OUT/f'idle/frame-{i:03}.png',i,result[phase]));atlas.alpha_composite(result[phase],(96*i,0))
    atlas.save(OUT/'idle-atlas.png',optimize=True)
    down_records=[];atlas=Image.new('RGBA',(1408,96))
    for i in range(11):
        if i in [4,5,8,9,10]:
            im=Image.new('RGBA',(128,96));im.alpha_composite(result[{4:0,5:1,8:0,9:1,10:2}[i]],(16,16))
            down_records.append(asset(OUT/f'walk/frame-{i:03}.png',i,im))
        else:im=Image.open(BODY_SOURCE/f'walk/frame-{i:03}.png').convert('RGBA')
        atlas.alpha_composite(im,(128*i,0))
    atlas.save(OUT/'walk-atlas.png',optimize=True)
    manifest={'revision':REVISION,'runtime_integrated':False,'image_generation_invoked':False,'chat_image_output':False,
      'method':'single nearest-neighbor shoulder rotation from original sleeve; shared fixed body; exact mirrored right arm',
      'previous_raise_degrees':52,'raise_degrees':abs(ANGLE),'inward_pixels':INSET,'shoulder_pivot':list(ARM_PIVOT),
      'mirror_axis':48,'palette':PALETTE,'idle_frames':idle,'down_frames':down_records,
      'preserved':['neutral pose','hood and face','eyes','torso','lower robe','inward registration','timing','accepted up/right/left artwork'],
      'left_raised_bounds_before':list(Image.open(PREVIOUS/'source/left-up.png').convert('RGBA').getbbox()),
      'left_raised_bounds_after':list(up.getbbox())}
    (OUT/'asset-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:manifest[k]for k in ['revision','previous_raise_degrees','raise_degrees','left_raised_bounds_before','left_raised_bounds_after']},ensure_ascii=False))


def preview():
    from export_gallery import font
    sheet=Image.new('RGB',(1040,816),(14,21,26));draw=ImageDraw.Draw(sheet)
    draw.text((520,16),'咒法师 · 降低抬臂幅度',font=font(22),anchor='mt',fill='#e9f0f0')
    for row,(folder,label)in enumerate([(PREVIOUS,'修改前'),(OUT,'本轮降低')]):
        for i,title in enumerate(['左臂小幅抬起','双臂放下','右臂小幅抬起']):
            x=16+340*i;y=64+368*row;draw.rounded_rectangle((x,y,x+328,y+348),radius=10,fill=(32,45,53))
            text=label+' · '+title;draw.text((x+164,y+12),text,font=font(16),anchor='mt',fill='#e9f0f0')
            im=Image.open(folder/f'idle/frame-{i:03}.png').convert('RGBA').resize((288,288),Image.Resampling.NEAREST)
            sheet.paste(im,(x+20,y+45),im)
            box=draw.textbbox((x+164,y+12),text,font=font(16),anchor='mt');assert box[0]>=x+16 and box[2]<=x+312
    sheet.save(OUT/'before-after.png',optimize=True)


if __name__=='__main__':
    create()
    preview()
