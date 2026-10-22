#!/usr/bin/env python3
"""One fixed guardian body/front shield, purpose-drawn arm layers and rigid spear."""
import argparse,copy,json
from pathlib import Path
from PIL import Image,ImageDraw
from build_gallery import ROOT
from export_gallery import font
from revise_cavalry_map import digest
import import_knight_redraw_v3 as h
import import_bastion_guardian_v1 as art

REV='bastion-guardian-idle-front-v3-20261022';OUT=ROOT/REV;SRC=OUT/'source'
ARM_BOX=[17,34,40,57]
GRIPS=[[40,326],[40,266],[42,130]]
TARGETS=[[22,52],[22,46],[22,40]]
SPEAR_POSITIONS=[[18,12],[18,6],[18,0]]
ASSETS=[]

def write(p,d):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')

def save(im,name,purpose):
    p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);im.save(p,optimize=True)
    ASSETS.append({'path':p.relative_to(ROOT).as_posix(),'purpose':purpose,'size':list(im.size),'bytes':p.stat().st_size,'sha256':digest(p)})
    return '../../../'+p.relative_to(ROOT).as_posix()

def flat_material(im):
    out=im.copy();out.putdata([(*art.COLORS[art.material(p[:3])],p[3])if p[3]else(0,0,0,0)for p in im.getdata()]);return out

def build(publish=False):
    baseline=json.loads((OUT/'baseline.json').read_text());h.SRC=SRC
    raw=sorted(h.figures('static-body-arm-layers-master-v1.png',4),key=lambda r:r[1]['source_bounds'][0])
    (body,body_meta),head=art.matte(raw[0]);scale=64/(body.height-head[1]);h.REG=[]
    fixed=h.register((body,body_meta),(96,96),head,[48,16],scale,'one-shared-static-body')
    registration=list(h.REG);arms=[]
    # Purpose-drawn separate arm assets, each attached beneath the common pauldron.
    # The static body is never shifted, rescaled, or replaced between frames.
    for i,(im,meta)in enumerate(raw[1:]):
        arm=h.register((flat_material(im),meta),(96,96),GRIPS[i],TARGETS[i],.075,f'arm-layer-{i}')
        visible=Image.new('RGBA',(96,96));visible.paste(arm.crop(ARM_BOX),(ARM_BOX[0],ARM_BOX[1]));arms.append(visible)
    registration=list(h.REG)
    spear=Image.open(ROOT/'bastion-guardian-idle-v2-20261022/ally/shared-spear.png').convert('RGBA')
    drafts={};frames={};proof={}
    for side in ['ally','enemy']:
        base=art.faction(fixed,side);weapon=art.faction(spear,side);dynamic=[art.faction(im,side)for im in arms]
        base_path=save(base,f'{side}/shared-fixed-body.png','one shared head, torso, planted legs and full front-facing shield, immutable across all phases')
        spear_path=save(weapon,f'{side}/shared-spear.png','same complete spear, translated without scaling')
        phases=[];hand_masks=[]
        for i in range(3):
            im=base.copy();im.alpha_composite(dynamic[i])
            hand=Image.new('RGBA',im.size);box=[18,TARGETS[i][1]-4,27,TARGETS[i][1]+4];hand.paste(im.crop(box),(box[0],box[1]))
            im.alpha_composite(weapon,tuple(SPEAR_POSITIONS[i]));im.alpha_composite(hand)
            phases.append(im);hand_masks.append(hand)
            save(dynamic[i],f'{side}/arm-{i:03}.png','detached armored arm layer, fixed attachment region beneath pauldron')
            save(hand,f'{side}/hand-occlusion-{i:03}.png','own arm grip drawn in front of rigid spear')
        # Verify every fixed-body pixel outside its arm socket is byte-identical.
        protected=[(x,y)for y in range(96)for x in range(96)if base.getpixel((x,y))[3]and not(ARM_BOX[0]<=x<ARM_BOX[2]and ARM_BOX[1]<=y<ARM_BOX[3])]
        assert all(im.getpixel(point)==base.getpixel(point)for im in phases for point in protected)
        proof[side]={'shared_body_sha256':digest(OUT/f'{side}/shared-fixed-body.png'),'protected_body_pixels':len(protected),'protected_body_pixels_identical_every_phase':True,'arm_motion_box':ARM_BOX,'spear_positions':SPEAR_POSITIONS,'body_offset_all_phases':[0,0]}
        frames[side]=phases
        mapping=copy.deepcopy(baseline[side]);s=next(s for s in mapping['scenarios']if s['id']=='tactical-idle');atlas=Image.new('RGBA',(576,96))
        for rec,phase in zip(s['frame_mapping'],[0,1,2,1,0,1]):
            i=rec['source_index'];path=save(phases[phase],f'{side}/frame-{i:03}.png','fixed body and outward full shield; only arm and complete spear move')
            rec.update(path=path,output_path=path,revision=REV,bytes=ASSETS[-1]['bytes'],sha256=ASSETS[-1]['sha256'],source_phase=phase);atlas.alpha_composite(phases[phase],(i*96,0))
        path=save(atlas,f'{side}/idle-atlas.png','six original alias slots, unchanged native idle timing')
        s.update(revision=REV,output_atlas=path,output_atlas_bytes=ASSETS[-1]['bytes'],review_note='盾牌完整正面朝外，盟军蓝白、敌方蓝紫。共用同一张固定头部、躯干、双腿和盾牌底图，仅持枪手臂与等长完整长枪运动；身体没有逐相上下或左右位移。保留原14／8／14／8帧循环。',action_note='本轮修正正面盾牌，固定完整身体，仅手臂和长枪运动。',semantic_note='Full shield front faces viewer. One immutable static body, independently drawn arm animation layers, same complete rigid spear.',motion_review={'revision':REV,'registration':'one shared fixed body, not three independently registered whole-body drawings','shared_body':base_path,'shared_spear':spear_path,'body_offsets':[[0,0],[0,0],[0,0]],'arm_motion_box':ARM_BOX,'spear_positions':SPEAR_POSITIONS,'spear_size':list(weapon.size),'static_pixel_proof':proof[side],'runtime_integrated':False})
        drafts[f'professions/class-22-{side}/maps/frame_mapping.json']=mapping
    for light in [False,True]:
        bg=(220,222,216)if light else(32,45,53);fg=(30,43,56)if light else(235,243,242)
        board=Image.new('RGB',(960,670),bg);draw=ImageDraw.Draw(board)
        draw.text((480,24),'壁垒卫士 · 正面盾牌与固定身体待机',anchor='mm',font=font(23),fill=fg)
        for row,side in enumerate(['ally','enemy']):
            for col,im in enumerate(frames[side]):
                im=im.resize((288,288),Image.Resampling.NEAREST);x=16+320*col;y=54+304*row;board.paste(im,(x,y),im)
                draw.text((160+320*col,y+282),('盟军'if side=='ally'else'敌方')+' · '+['低位','中位','高位'][col],anchor='mt',font=font(16),fill=fg)
        save(board,f'poses-{"light"if light else"dark"}.png','both factions three phases, fixed body and complete outward shield, dark/light')
    write(OUT/'mapping-drafts.json',drafts)
    write(OUT/'asset-manifest.json',{'revision':REV,'image_generation':'built-in image_gen','source_master':'source/static-body-arm-layers-master-v1.png','palette':{'ally':art.ALLY,'enemy':art.ENEMY},'registration':registration,'static_body_proof':proof,'arm_motion_box':ARM_BOX,'source_arm_grips':GRIPS,'target_arm_grips':TARGETS,'shared_spear_size':list(spear.size),'shared_spear_positions':SPEAR_POSITIONS,'body_offset_all_phases':[0,0],'runtime_integrated':False,'assets':ASSETS})
    if publish:
        for key,m in drafts.items():write(ROOT/key,m)
    print(json.dumps({'status':'published'if publish else'staged','static_body_proof':proof,'assets':len(ASSETS)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');build(p.parse_args().publish)
