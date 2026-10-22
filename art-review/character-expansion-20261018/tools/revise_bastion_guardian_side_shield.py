#!/usr/bin/env python3
"""Side walk rig: fixed upper body, original two-phase legs, attached arm/shield."""
import argparse,copy,json
from pathlib import Path
from PIL import Image,ImageDraw
from build_gallery import ROOT
from export_gallery import font
from revise_cavalry_map import digest
import import_knight_redraw_v3 as h
import import_bastion_guardian_v1 as art

REV='bastion-guardian-side-shield-v4-20261022';OUT=ROOT/REV;SRC=OUT/'source'
PIVOT=[48,48];ANGLES=[-12,16];ASSETS=[]

def write(p,d):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')

def save(im,name,purpose):
    p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);im.save(p,optimize=True)
    ASSETS.append({'path':p.relative_to(ROOT).as_posix(),'purpose':purpose,'size':list(im.size),'bytes':p.stat().st_size,'sha256':digest(p)})
    return '../../../'+p.relative_to(ROOT).as_posix()

def matte(im):
    out=im.copy();out.putdata([(*art.COLORS[art.material(p[:3])],p[3])if p[3]else(0,0,0,0)for p in im.getdata()]);return out

def build(publish=False):
    baseline=json.loads((OUT/'baseline.json').read_text());h.SRC=SRC
    raw=sorted(h.figures('side-walk-rig-master-v1.png',4),key=lambda r:r[1]['source_bounds'][0]);h.REG=[]
    (im,meta),head=art.matte(raw[0]);core_scale=34/(325-head[1])
    core=h.register((im,meta),(128,96),head,[64,32],core_scale,'shared-static-upper-body')
    legs=[];leg_scale=30/(318-35)
    for i,point in enumerate([[255,35],[198,35]]):legs.append(h.register((matte(raw[i+1][0]),raw[i+1][1]),(128,96),point,[65,66],leg_scale,f'legs-{i}'))
    assembly=matte(raw[3][0]);p=assembly.load()
    # The shared core already supplies the pauldron. Remove only the duplicate
    # pauldron from its purpose-drawn socket layer, keeping the full shield rim.
    for y in range(155):
        for x in range(assembly.width):
            if y<120 or x>=150:p[x,y]=(0,0,0,0)
    attached=h.register((assembly,raw[3][1]),(128,96),[173,82],PIVOT,core_scale,'shared-attached-arm-shield')
    swings=[attached.rotate(angle,resample=Image.Resampling.NEAREST,center=tuple(PIVOT),expand=False)for angle in ANGLES]
    # Protect the common head and pauldrons in front of the attachment socket.
    upper_occlusion=Image.new('RGBA',(128,96));upper_occlusion.paste(core.crop((0,0,128,54)),(0,0))
    right=[]
    for i in range(2):
        frame=legs[i].copy();frame.alpha_composite(core);frame.alpha_composite(swings[i]);frame.alpha_composite(upper_occlusion);right.append(frame)
        assert frame.crop((40,24,94,46)).tobytes()==core.crop((40,24,94,46)).tobytes()
    drafts={};review={};motion={}
    for side in ['ally','enemy']:
        shared_core=art.faction(core,side);shared_assembly=art.faction(attached,side)
        core_path=save(shared_core,f'{side}/shared-upper-body.png','one fixed head/torso, spear arm and lance')
        arm_path=save(shared_assembly,f'{side}/shared-arm-shield.png','shield and holding arm form one connected immutable rig layer')
        for i in range(2):
            save(art.faction(legs[i],side),f'{side}/legs-{i}.png','native two-phase stride, waist attachment registered')
            save(art.faction(swings[i],side),f'{side}/arm-shield-{i}.png','same connected arm/shield layer rotated around common shoulder pivot')
        rendered={2:art.faction(right[0],side),3:art.faction(right[1],side)}
        for i in [2,3]:rendered[i+4]=rendered[i].transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        mapping=copy.deepcopy(baseline[side]);s=next(s for s in mapping['scenarios']if s['id']=='tactical-walk');atlas=Image.new('RGBA',(1024,96))
        for rec in s['frame_mapping']:
            i=rec['source_index']
            if i in rendered:
                path=save(rendered[i],f'{side}/frame-{i:03}.png','shield carried by its swinging arm; fixed upper body')
                rec.update(path=path,output_path=path,revision=REV,sha256=ASSETS[-1]['sha256'],bytes=ASSETS[-1]['bytes'])
            im=rendered[i]if i in rendered else Image.open((ROOT/f'professions/class-22-{side}/maps'/rec['path']).resolve()).convert('RGBA')
            atlas.alpha_composite(im,(i*128,0))
        atlas_path=save(atlas,f'{side}/walk-atlas.png','all8 source slots: corrected sides and unchanged up/down')
        s.update(revision=REV,output_atlas=atlas_path,output_atlas_bytes=ASSETS[-1]['bytes'],review_note='左右行走的盾牌与持盾手臂作为同一整体，围绕固定肩部共同前后摆动，盾牌不再原地悬停。固定头部与躯干，保留两相步态及每相16帧；左右严格整图镜像。已确认待机及向上、向下保持。',action_note='本轮只修正左右摆臂带盾，保持原两相行走节奏。',motion_review={'runtime_integrated':False,'shared_fixed_core':core_path,'shared_connected_arm_shield':arm_path,'shoulder_pivot':PIVOT,'rig_angles_degrees':ANGLES,'arm_and_shield_transform_together':True,'whole_body_offset':[0,0],'left_is_exact_mirror':True})
        drafts[f'professions/class-22-{side}/maps/frame_mapping.json']=mapping
        review[side]=rendered
        boxes=[list(art.faction(swings[i],side).getbbox())for i in range(2)]
        motion[side]={'pivot':PIVOT,'angles':ANGLES,'assembly_bounds':boxes,'shared_core_sha256':digest(OUT/f'{side}/shared-upper-body.png'),'shared_arm_shield_sha256':digest(OUT/f'{side}/shared-arm-shield.png')}
    for light in [False,True]:
        bg=(220,222,216)if light else(32,45,53);fg=(30,43,56)if light else(235,243,242)
        board=Image.new('RGB',(1152,548),bg);draw=ImageDraw.Draw(board)
        draw.text((576,24),'壁垒卫士 · 盾牌随手臂整体摆动',anchor='mm',font=font(23),fill=fg)
        for row,side in enumerate(['ally','enemy']):
            for col,i in enumerate([2,3,6,7]):
                im=review[side][i].resize((256,192),Image.Resampling.NEAREST);x=16+288*col;y=52+246*row;board.paste(im,(x,y),im)
                draw.text((144+288*col,y+198),('盟军'if side=='ally'else'敌方')+' · '+('向右'if i<4 else'向左')+' '+('A'if i in[2,6]else'B'),anchor='mt',font=font(16),fill=fg)
        save(board,f'poses-{"light"if light else"dark"}.png','both factions, right/left two-phase walk on dark/light')
    write(OUT/'mapping-drafts.json',drafts)
    write(OUT/'asset-manifest.json',{'revision':REV,'image_generation':'built-in image_gen','source_master':'source/side-walk-rig-master-v1.png','palette':{'ally':art.ALLY,'enemy':art.ENEMY},'registration':h.REG,'shared_arm_shield_rig':motion,'runtime_integrated':False,'assets':ASSETS})
    if publish:
        for key,m in drafts.items():write(ROOT/key,m)
    print(json.dumps({'status':'published'if publish else'staged','rig':motion,'assets':len(ASSETS)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');build(p.parse_args().publish)
