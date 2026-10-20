#!/usr/bin/env python3
"""Move only raised robe sleeves inward; preserve accepted body and gaits."""
import hashlib,json
from PIL import Image,ImageDraw
from revise_curse_mage_map import ROOT,mirror,place,connected,PALETTE,EYES

REVISION='curse-mage-sleeve-inset-v3-20261020'
OUT=ROOT/REVISION
PREVIOUS=ROOT/'curse-mage-map-v2-20261020'
INSET=6
ALIASES=[0,1,2,1,0,1]


def asset(path,index,im):
    im.save(path,optimize=True)
    return {'source_index':index,'path':path.relative_to(ROOT).as_posix(),'size':list(im.size),
      'visible_bounds':list(im.getbbox()),'bytes':path.stat().st_size,
      'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}


def create():
    for folder in ['source','idle','walk']:(OUT/folder).mkdir(parents=True,exist_ok=True)
    original=[Image.open(PREVIOUS/f'idle/frame-{i:03}.png').convert('RGBA')for i in range(3)]
    body=Image.open(PREVIOUS/'source/fixed-front-body.png').convert('RGBA')
    down=Image.open(PREVIOUS/'source/left-down.png').convert('RGBA')
    previous_up=Image.open(PREVIOUS/'source/left-up.png').convert('RGBA')
    left_up=place(previous_up,(INSET,0))
    sleeves={'left-up':left_up,'right-up':mirror(left_up,48),'left-down':down,'right-down':mirror(down,48)}
    for name,im in sleeves.items():im.save(OUT/f'source/{name}.png',optimize=True)
    result=[]
    for i,(left,right)in enumerate([('left-up','right-down'),('left-down','right-down'),('left-down','right-up')]):
        frame=Image.new('RGBA',(96,96));frame.alpha_composite(sleeves[left]);frame.alpha_composite(sleeves[right])
        # Keep the already reviewed hem in each pose, including its pixels at
        # the sleeve overlap; the translated raised sleeves end above this.
        frame.alpha_composite(original[i].crop((0,65,96,96)),(0,65));frame.alpha_composite(body)
        for x0,y0,x1,y1 in EYES:
            frame.paste(original[i].crop((x0,y0,x1+1,y1+1)),(x0,y0))
        result.append(connected(frame))
    assert result[1].tobytes()==original[1].tobytes()
    idle_records=[];atlas=Image.new('RGBA',(576,96))
    for i,phase in enumerate(ALIASES):
        idle_records.append(asset(OUT/f'idle/frame-{i:03}.png',i,result[phase]));atlas.alpha_composite(result[phase],(96*i,0))
    atlas.save(OUT/'idle-atlas.png',optimize=True)
    down_records=[];walk=Image.new('RGBA',(1408,96))
    for i in range(11):
        if i in [4,5,8,9,10]:
            phase={4:0,5:1,8:0,9:1,10:2}[i]
            im=Image.new('RGBA',(128,96));im.alpha_composite(result[phase],(16,16))
            down_records.append(asset(OUT/f'walk/frame-{i:03}.png',i,im))
        else:im=Image.open(PREVIOUS/f'walk/frame-{i:03}.png').convert('RGBA')
        walk.alpha_composite(im,(128*i,0))
    walk.save(OUT/'walk-atlas.png',optimize=True)
    old_box=previous_up.getbbox();new_box=left_up.getbbox()
    manifest={'revision':REVISION,'runtime_integrated':False,'image_generation_invoked':False,'chat_image_output':False,
      'method':'integer inward translation of raised sleeve layer; no angle, height, scale or palette change',
      'inward_translation_output_pixels':{'left':[INSET,0],'right':[-INSET,0]},
      'inward_translation_native_pixels':INSET/4,'mirror_axis':48,
      'left_raised_layer_before_bounds':list(old_box),'left_raised_layer_after_bounds':list(new_box),
      'outward_reach_from_shoulder_before':34-old_box[0],'outward_reach_from_shoulder_after':34-new_box[0],
      'palette':PALETTE,'preserved':['hood','face and eyes','torso','lower robe','both arms lowered pose','timing','accepted up/right/left gaits'],
      'idle_frames':idle_records,'down_frames':down_records}
    (OUT/'asset-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:manifest[k]for k in ['revision','inward_translation_native_pixels','left_raised_layer_before_bounds','left_raised_layer_after_bounds']},ensure_ascii=False))


def preview():
    from export_gallery import font
    sheet=Image.new('RGB',(1040,816),(14,21,26));draw=ImageDraw.Draw(sheet)
    draw.text((520,16),'咒法师 · 袖袍外摆收拢',font=font(22),anchor='mt',fill='#e9f0f0')
    for row,(folder,label)in enumerate([(PREVIOUS,'修改前'),(OUT,'本轮收拢')]):
        for i,title in enumerate(['左臂抬起','双臂放下','右臂抬起']):
            x=16+340*i;y=64+368*row
            draw.rounded_rectangle((x,y,x+328,y+348),radius=10,fill=(32,45,53))
            text=label+' · '+title
            draw.text((x+164,y+12),text,font=font(17),anchor='mt',fill='#e9f0f0')
            image=Image.open(folder/f'idle/frame-{i:03}.png').convert('RGBA').resize((288,288),Image.Resampling.NEAREST)
            sheet.paste(image,(x+20,y+45),image)
            box=draw.textbbox((x+164,y+12),text,font=font(17),anchor='mt')
            assert box[0]>=x+16 and box[2]<=x+312
    sheet.save(OUT/'before-after.png',optimize=True)


if __name__=='__main__':
    create()
    preview()
