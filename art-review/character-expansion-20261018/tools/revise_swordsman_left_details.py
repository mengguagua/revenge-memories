#!/usr/bin/env python3
"""Register three ImageGen corrections into the approved left walk phases."""
import argparse,copy,json
from PIL import Image,ImageDraw
from build_gallery import ROOT,file_hash
from export_gallery import font
from revise_swordsman_left_profile import save,write
from rebuild_swordsman_maps import COLORS,ENEMY,faction
from import_knight_redraw_v3 import parts

REV='swordsman-left-detail-v4-20261022';OUT=ROOT/REV
OLD=ROOT/'swordsman-left-profile-v3-20261022'
HEAD=(45,31,71,54)
SHIELDS={6:(64,36,88,72),7:(68,48,92,84)}
FOOT=(66,80,76,90)

def crop_art(master,box,size,palette):
    im=master.crop(box).resize(size,Image.Resampling.NEAREST)
    im.putdata([(*min(palette,key=lambda c:sum((p[i]-c[i])**2 for i in range(3))),255)if p[3]>=128 else(0,0,0,0)for p in im.getdata()])
    return im

def build(publish=False):
    if not(OUT/'baseline.json').exists():
        d=json.loads((ROOT/'demos/gallery-data.json').read_text())
        write(OUT/'baseline.json',{'actions':{a['id']:a for a in d['actions']},'mappings':{s:json.loads((ROOT/f'professions/class-9-{s}/maps/frame_mapping.json').read_text())for s in['ally','enemy']}})
    base=json.loads((OUT/'baseline.json').read_text());master=Image.open(OUT/'source/detail-master.png').convert('RGBA')
    # Only the three edited anatomical/object layers are taken from ImageGen.
    # Whole-sprite downsampling would replace already approved torso and sword.
    head=crop_art(master,(524,350,800,604),(25,23),[COLORS[0],COLORS[3]])
    shield=crop_art(master,(790,544,1048,934),(24,36),COLORS[:3])
    rear=crop_art(master,(746,894,856,1000),(10,10),[COLORS[0]])
    # Transfer the approved front boot's blue material to the new rear boot
    # contour. Pure navy alone vanished against the actual dark review ground.
    boot=Image.open(OLD/'ally/walk-07.png').convert('RGBA').crop((53,81,64,91)).resize(rear.size,Image.Resampling.NEAREST)
    for y in range(rear.height):
        for x in range(rear.width):
            if rear.getpixel((x,y))[3] and boot.getpixel((x,y))[:3]==COLORS[1]:rear.putpixel((x,y),(*COLORS[1],255))
    assets=[save(im,OUT/'source'/f'{name}.png')for name,im in[('rounded-head',head),('complete-shield',shield),('rear-boot',rear)]]
    frames={};drafts={}
    for side in['ally','enemy']:
        mapping=copy.deepcopy(base['mappings'][side]);scene=next(s for s in mapping['scenarios']if s['id']=='tactical-walk')
        for i in[6,7]:
            old=Image.open(OLD/side/f'walk-{i:02}.png').convert('RGBA');im=old.copy()
            im.paste((0,0,0,0),SHIELDS[i]);im.paste((0,0,0,0),HEAD)
            im.alpha_composite(faction(head,side),HEAD[:2])
            # Sword is in front of the left edge of the head: keep its exact
            # previous pixels, without restoring the old rear-neck skin specks.
            im.paste(old.crop((45,43,48,55)),(45,43))
            if i==7:im.alpha_composite(faction(rear,side),FOOT[:2])
            im.alpha_composite(faction(shield,side),SHIELDS[i][:2])
            cs=parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))[3]);assert len(cs)==1,(side,i,list(map(len,cs)))
            assets.append(save(im,OUT/side/f'walk-{i:02}.png'));frames[side,i]=im
            row=next(r for r in scene['frame_mapping']if r['source_index']==i);row.update(path='../../../'+assets[-1]['path'],output_path='../../../'+assets[-1]['path'],revision=REV,bytes=assets[-1]['bytes'],sha256=assets[-1]['sha256'])
        atlas=Image.new('RGBA',(1024,96))
        for row in scene['frame_mapping']:
            i=row['source_index'];im=frames[side,i]if i in[6,7]else Image.open((ROOT/f'professions/class-9-{side}/maps'/row['path']).resolve()).convert('RGBA');atlas.alpha_composite(im,(i*128,0))
        assets.append(save(atlas,OUT/side/'tactical-walk-atlas.png'))
        scene.update(output_atlas='../../../'+assets[-1]['path'],revision=REV,review_note='左行细节修正：盾牌四周完整米白边；交叉步后脚露出；后脑轮廓更饱满，清除后脑及后颈多余肤色。原时序与人物基准保持。')
        scene.setdefault('motion_review',{})['left_detail_fix']={'revision':REV,'source_slots':[6,7],'head_box':list(HEAD),'shield_boxes':{str(k):list(v)for k,v in SHIELDS.items()},'rear_boot_box':list(FOOT),'shared_head_and_shield_art':True,'head_and_body_anchor_unchanged':True}
        drafts[f'professions/class-9-{side}/maps/frame_mapping.json']=mapping
    for light in[True,False]:
        board=Image.new('RGB',(1024,700),(220,222,216)if light else(32,45,53));draw=ImageDraw.Draw(board)
        for n,(side,i)in enumerate([('ally',6),('ally',7),('enemy',6),('enemy',7)]):
            im=frames[side,i].resize((384,288),Image.Resampling.NEAREST);x=n%2*512+64;y=n//2*350+5;board.paste(im,(x,y),im)
            draw.text((n%2*512+256,n//2*350+322),('盟军'if side=='ally'else'敌方')+f' · 左行 {i-6}',anchor='mm',font=font(18),fill=(23,38,56)if light else(235,243,242))
        path=OUT/f'left-details-{"light"if light else"dark"}.png';board.save(path,optimize=True);assets.append({'path':path.relative_to(ROOT).as_posix(),'size':list(board.size),'bytes':path.stat().st_size,'sha256':file_hash(path)})
    write(OUT/'mapping-drafts.json',drafts);write(OUT/'asset-manifest.json',{'revision':REV,'source':'built-in image_gen local edit; only head, shield and rear boot layers retained','assets':assets,'head_box':list(HEAD),'shield_boxes':{str(k):list(v)for k,v in SHIELDS.items()},'rear_boot_box':list(FOOT),'runtime_integrated':False,'user_visual_acceptance':'pending'})
    if publish:
        for path,mapping in drafts.items():write(ROOT/path,mapping)
    print(json.dumps({'frames':4,'assets':len(assets),'published':publish}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');build(p.parse_args().publish)
