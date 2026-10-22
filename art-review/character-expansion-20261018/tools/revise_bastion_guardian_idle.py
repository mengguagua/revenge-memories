#!/usr/bin/env python3
"""Correct the edge-on shield idle, with one immutable shared complete spear."""
import argparse,copy,json,colorsys
from pathlib import Path
from PIL import Image,ImageDraw
from build_gallery import ROOT
from export_gallery import font
import import_knight_redraw_v3 as h
import import_bastion_guardian_v1 as art
from revise_cavalry_map import digest

REV='bastion-guardian-idle-v2-20261022';OUT=ROOT/REV;SRC=OUT/'source'
ASSETS=[]

def write(p,d):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')

def save(im,name,purpose):
    p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);im.save(p,optimize=True)
    ASSETS.append({'path':p.relative_to(ROOT).as_posix(),'purpose':purpose,'size':list(im.size),'bytes':p.stat().st_size,'sha256':digest(p)})
    return '../../../'+p.relative_to(ROOT).as_posix()

def source_grip(im):
    pts=[]
    for y in range(im.height):
        for x in range(int(im.width*.18)):
            r,g,b,a=im.getpixel((x,y));hh,s,v=colorsys.rgb_to_hsv(r/255,g/255,b/255)
            if a and .02<hh<.12 and .25<v<.65 and .3<s:pts.append((x,y))
    parts=h.parts(pts)[:2]
    parts.sort(key=lambda c:min(y for x,y in c))
    bounds=[[min(x for x,y in c),min(y for x,y in c),max(x for x,y in c)+1,max(y for x,y in c)+1]for c in parts]
    upper,lower=bounds
    x=(upper[0]+upper[2]+lower[0]+lower[2])/4;y=(upper[3]+lower[1])/2
    return [x,y],[max(0,int(x-32)),upper[3]+3,min(im.width,int(x+34)),lower[1]-3]

def build(publish=False):
    baseline=json.loads((OUT/'baseline.json').read_text());h.SRC=SRC
    raw=sorted(h.figures('idle-shield-edge-master-v1.png',4),key=lambda r:r[1]['source_bounds'][0])
    bodies=[art.matte(f)for f in raw[:3]]
    scale=64/max(fig[0].height-point[1]for fig,point in bodies)
    weapon=raw[3][0];weapon=weapon.resize((round(weapon.width*76/weapon.height),76),Image.Resampling.NEAREST)
    flat=weapon.copy();flat.putdata([(*art.COLORS[art.material(p[:3])],p[3])if p[3]else(0,0,0,0)for p in weapon.getdata()]);weapon=flat
    body_frames=[];occlusion=[];positions=[];registration=[]
    for i,((fig,point),(original,meta))in enumerate(zip(bodies,raw[:3])):
        art.helper.REG=[];body=art.helper.register(fig,(96,96),point,[48,16],scale,f'idle-body-{i}');registration.extend(art.helper.REG)
        rec=registration[-1];ratios=[rec['resampled_size'][0]/original.width,rec['resampled_size'][1]/original.height]
        grip,box=source_grip(original)
        # Preserve the hand of this exact full pose, at its own original coordinates.
        # This is a glove occlusion layer, never a limb borrowed from another pose.
        box=[round(box[j]*ratios[j%2]+rec['translation'][j%2])for j in range(4)]
        gx=round(grip[0]*ratios[0]+rec['translation'][0])
        pos=[gx-weapon.width//2,[10,5,0][i]]
        assert pos[0]>=0 and pos[0]+weapon.width<=96 and pos[1]+weapon.height<=96
        hand=Image.new('RGBA',(96,96));hand.paste(body.crop(box),(box[0],box[1]))
        body_frames.append(body);occlusion.append(hand);positions.append(pos)
    frames={};layers={};drafts={}
    for side in ['ally','enemy']:
        body=[art.faction(im,side)for im in body_frames];hand=[art.faction(im,side)for im in occlusion];spear=art.faction(weapon,side)
        layers[side]=save(spear,f'{side}/shared-spear.png','one immutable complete spear used by every idle phase')
        frames[side]=[]
        for i in range(3):
            im=body[i].copy();im.alpha_composite(spear,tuple(positions[i]));im.alpha_composite(hand[i])
            frames[side].append(im)
            save(body[i],f'{side}/body-{i:03}.png','whole ImageGen body with clear bent arms and horizontal edge-on shield')
            save(hand[i],f'{side}/glove-occlusion-{i:03}.png','same-pose glove occlusion in original position')
        mapping=copy.deepcopy(baseline[side]);s=next(s for s in mapping['scenarios']if s['id']=='tactical-idle');atlas=Image.new('RGBA',(576,96))
        for rec,phase in zip(s['frame_mapping'],[0,1,2,1,0,1]):
            i=rec['source_index'];path=save(frames[side][phase],f'{side}/frame-{i:03}.png','full constant-length spear slides against narrow edge-on shield')
            rec.update(path=path,output_path=path,revision=REV,sha256=ASSETS[-1]['sha256'],bytes=ASSETS[-1]['bytes'],source_phase=phase)
            atlas.alpha_composite(frames[side][phase],(i*96,0))
        path=save(atlas,f'{side}/idle-atlas.png','six original alias slots, no changes to native cycle')
        s.update(revision=REV,output_atlas=path,output_atlas_bytes=ASSETS[-1]['bytes'],review_note='盾牌横在身前侧持，仅露窄边；双臂屈肘可见。完整长枪沿盾边上下摩擦，三相共用同一张枪图，枪头、连续枪杆与枪尾均完整且等长。人物头部与中心固定，保留14／8／14／8帧循环及既有蓝白／蓝紫配色。',action_note='本轮纠正侧盾与长枪摩擦动作。',semantic_note='Horizontal narrow shield rim, not a frontal shield face; vertical full spear, shared rigid weapon layer. Lower/middle/upper grip and spear positions.',motion_review={'registration':'whole-body hair landmark fixed; immutable spear translates, same-pose glove occludes grip','runtime_integrated':False,'shared_spear':layers[side],'spear_size':list(spear.size),'spear_positions':positions,'native_timing_modified':False})
        drafts[f'professions/class-22-{side}/maps/frame_mapping.json']=mapping
    for light in [False,True]:
        bg=(220,222,216)if light else(32,45,53);fg=(30,43,56)if light else(235,243,242)
        board=Image.new('RGB',(960,670),bg);draw=ImageDraw.Draw(board)
        draw.text((480,24),'壁垒卫士 · 侧持盾边与完整长枪摩擦',anchor='mm',font=font(23),fill=fg)
        for row,side in enumerate(['ally','enemy']):
            for col,im in enumerate(frames[side]):
                im=im.resize((288,288),Image.Resampling.NEAREST);x=16+320*col;y=54+304*row;board.paste(im,(x,y),im)
                draw.text((160+320*col,y+282),('盟军'if side=='ally'else'敌方')+' · '+['低位','中位','高位'][col],anchor='mt',font=font(16),fill=fg)
        save(board,f'poses-{"light"if light else"dark"}.png','both factions, all three phases, actual sprites at3x')
    write(OUT/'mapping-drafts.json',drafts)
    write(OUT/'asset-manifest.json',{'revision':REV,'image_generation':'built-in image_gen','source_master':'source/idle-shield-edge-master-v1.png','palette':{'ally':art.ALLY,'enemy':art.ENEMY},'registration':registration,'shared_spear_size':list(weapon.size),'shared_spear_positions':positions,'shared_spear_layer':layers,'weapon_scaling_between_phases':False,'same_pose_glove_occlusion':True,'body_or_limb_warping':False,'assets':ASSETS,'runtime_integrated':False})
    if publish:
        for key,value in drafts.items():write(ROOT/key,value)
    print(json.dumps({'status':'published'if publish else'staged','positions':positions,'spear_size':list(weapon.size),'assets':len(ASSETS)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');build(p.parse_args().publish)
