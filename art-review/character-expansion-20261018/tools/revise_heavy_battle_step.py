#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Register drawn leg poses to native knees/soles; lock the accepted upper body."""
import argparse,copy,json,math
from PIL import Image,ImageDraw
from build_gallery import ROOT
import import_knight_redraw_v3 as helper
from import_heavy_infantry_v1 import matte,faction
from revise_cavalry_map import digest,translate
from export_gallery import font

REV='heavy-infantry-battle-step-v3-20261022';OUT=ROOT/REV;SRC=OUT/'source'
SLOTS=[0,4,5,6,7,8,9,10,16,29]
NATIVE={
 0:[[(42.5,53.5),(42.5,62.5)],[(50,53.5),(54,63.5)]],
 4:[[(42.5,53.5),(41.5,62.5)],[(50,53.5),(54,63.5)]],
 5:[[(42.5,53.5),(47.5,57.5)],[(47,53.5),(50.5,63.5)]],
 6:[[(44.5,53.5),(43.5,63.5)],[(49,53.5),(53.5,62.5)]]}
ALIASES={7:5,8:4,9:4,10:4,16:0,29:0}
# Landmarks on the generated leg art, before rigid two-point registration.
DRAWN={0:[[(187.5,214),(187,253)],[(216,217),(228,253)]],
       5:[[(188,212),(202,236)],[(213,217),(220,253)]],
       6:[[(189,214),(187.5,253)],[(218,217),(237,249)]]}
CORE_BOX=(0,0,320,204)

def write(p,v):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')

def project(p):
    # Native local geometry around the fixed pelvis; one scale for every phase.
    return [203+(p[0]-47)*52/14,200+(p[1]-49.5)*52/14]

def rigid(piece,source,target):
    """Two-point similarity registration, no shear or independent axis scaling."""
    (sx,sy),(ex,ey)=source;(tx,ty),(ux,uy)=target
    vx,vy=ex-sx,ey-sy;wx,wy=ux-tx,uy-ty;n=vx*vx+vy*vy
    a=(vx*wx+vy*wy)/n;b=(vx*wy-vy*wx)/n
    dx,dy=tx-a*sx+b*sy,ty-b*sx-a*sy;den=a*a+b*b
    inverse=(a/den,b/den,(-a*dx-b*dy)/den,-b/den,a/den,(b*dx-a*dy)/den)
    out=piece.transform((320,256),Image.Transform.AFFINE,inverse,resample=Image.Resampling.NEAREST)
    return out,{'source_knee_and_sole':source,'target_knee_and_sole':target,'uniform_scale':math.sqrt(den),'rotation_degrees':math.degrees(math.atan2(b,a)),'shear':0}

def build(publish=False):
    base=json.loads((OUT/'baseline.json').read_text());helper.SRC=SRC;raw=helper.figures('gait-master-v2.png',3);pts=[helper.landmark(f[0])[0]for f in raw]
    scale=94/max(f[0].height-p[1]for f,p in zip(raw,pts));helper.REG=[];drawings={}
    for i,f,p in zip([0,5,6],raw,pts):drawings[i]=helper.register(matte(f,p),(320,256),p,[188,160],scale,f'drawn-gait-{i}')
    accepted=Image.open(SRC/'before-000.png').convert('RGBA')
    # The accepted helmet, face, arms, hands and continuous spear are immutable.
    # Retain the overlapping skirt plates, then assemble the drawn whole legs
    # behind them. Only rigid similarity transforms articulate the leg artwork.
    upper=accepted.copy();upper.paste((0,0,0,0),(150,204,265,256))
    skirt_mask=Image.new('L',(320,256));ImageDraw.Draw(skirt_mask).polygon([(178,195),(229,195),(233,201),(229,206),(218,209),(213,215),(196,214),(185,209),(178,205)],fill=255)
    skirt=Image.new('RGBA',(320,256));skirt.paste(accepted,(0,0),skirt_mask)
    poses={};registrations=[]
    for i in[0,4,5,6]:
        source_id=0 if i==4 else i;draw=drawings[source_id];layers=[]
        for leg in[1,0]:
            split=208 if source_id==5 else 203
            box=(150,201,split,256)if leg==0 else(split,201,265,256)
            piece=Image.new('RGBA',draw.size);piece.paste(draw.crop(box),box[:2]);target=[project(p)for p in NATIVE[i][leg]]
            layer,record=rigid(piece,DRAWN[source_id][leg],target);layers.append(layer)
            registrations.append({'pose':i,'leg':'screen-left'if leg==0 else'screen-right',**record})
        out=Image.new('RGBA',(320,256))
        for layer in layers:out.alpha_composite(layer)
        out.alpha_composite(upper);out.alpha_composite(skirt);poses[i]=out
        assert out.crop(CORE_BOX).tobytes()==accepted.crop(CORE_BOX).tobytes()
    for i,alias in ALIASES.items():poses[i]=poses[alias].copy()
    drafts={};assets=[];images={}
    for side in['ally','enemy']:
        mapping=copy.deepcopy(base['mappings'][side]);folder=ROOT/f'professions/class-2-{side}/battle';images[side]={}
        for i,draw in sorted(poses.items()):
            im=faction(draw,side);shift=-64 if side=='enemy'and i in[16,29]else 0
            if shift:im=translate(im,[shift,0])
            p=OUT/side/f'frame-{i:03}.png';p.parent.mkdir(parents=True,exist_ok=True);im.save(p,optimize=True);path='../../../'+p.relative_to(ROOT).as_posix();mapping['frame_mapping'][str(i)]=path
            rec=next(r for r in mapping['records']if r['source_frame']==i);rec.update(path=path,sha256=digest(p),revision=REV,art_status='review_candidate')
            images[side][i]=im;assets.append({'path':p.relative_to(ROOT).as_posix(),'purpose':f'native battle gait pose {i}','size':list(im.size),'bytes':p.stat().st_size,'sha256':digest(p)})
        order=mapping['output_atlas_frame_order'];atlas=Image.new('RGBA',(320*len(order),256))
        for n,i in enumerate(order):atlas.alpha_composite(Image.open((folder/mapping['frame_mapping'][str(i)]).resolve()).convert('RGBA'),(n*320,0))
        p=OUT/side/'battle-atlas.png';atlas.save(p,optimize=True);assets.append({'path':p.relative_to(ROOT).as_posix(),'purpose':'packed original battle slots, other attack/throw poses unchanged','size':list(atlas.size),'bytes':p.stat().st_size,'sha256':digest(p)})
        mapping.update(revision=REV,output_atlas='../../../'+p.relative_to(ROOT).as_posix(),review_note='按原作膝盖与脚底位置重做接近、回位的交替步态：前脚抬起屈膝向后收，再换另一脚；4/8/9/10共用原站姿，5/7共用抬脚姿势。固定已确认的头部、躯干、双手与长枪；原顺序、时长、攻击及投枪保持。',motion_review={'revision':REV,'native_leg_aliases':ALIASES,'fixed_upper_body_box':list(CORE_BOX),'native_program_modified':False,'geometry':'native knee/sole landmarks; common pelvis projection; drawn whole legs use rigid similarity registration only'},art_provenance='Built-in image_gen edited three leg poses; rigid whole-leg registration under immutable accepted torso/skirt; no shear, procedural body drawing or independent axis scaling.',batches=[{'id':'native-battle-gait','review':f'../../../{REV}/{side}-gait-dark.png','status':'pending_user_visual_acceptance'}])
        drafts[side]=mapping
    for side in['ally','enemy']:
        for light in[False,True]:
            bg=(220,222,216)if light else(32,45,53);fg=(30,43,56)if light else(235,243,242);board=Image.new('RGB',(1600,650),bg);d=ImageDraw.Draw(board)
            for n,i in enumerate([0,4,5,6,7,8,9,10]):
                x=n%4*400;y=n//4*325;im=images[side][i].crop((95,126,280,256)).resize((370,260),Image.Resampling.NEAREST);board.paste(im,(x+15,y+16),im);d.text((x+200,y+295),f'原姿势 {i}',anchor='mm',font=font(18),fill=fg)
            p=OUT/f'{side}-gait-{"light"if light else"dark"}.png';board.save(p,optimize=True);assets.append({'path':p.relative_to(ROOT).as_posix(),'purpose':'native gait full-body dark/light inspection','size':list(board.size),'bytes':p.stat().st_size,'sha256':digest(p)})
    write(OUT/'mapping-drafts.json',drafts);write(OUT/'asset-manifest.json',{'revision':REV,'image_generation':'built-in image_gen','source_master':'source/gait-master-v2.png','prompt':'source/imagegen-prompt-v2.json','registration':helper.REG,'leg_registration':registrations,'native_knees_and_soles':NATIVE,'native_leg_aliases':ALIASES,'fixed_upper_body_box':list(CORE_BOX),'upper_body_and_spear_pixel_identical':True,'native_timing_modified':False,'runtime_integrated':False,'assets':assets})
    if publish:
        for side,m in drafts.items():write(ROOT/f'professions/class-2-{side}/battle/frame_mapping.json',m)
    print(json.dumps({'status':'published'if publish else'staged','frames':len(poses)*2,'assets':len(assets)}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');build(p.parse_args().publish)
