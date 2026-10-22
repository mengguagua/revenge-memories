#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Replace class22 weapon layers with one drawn jousting lance; preserve motion."""
import argparse,copy,colorsys,json,math
from functools import lru_cache
from PIL import Image,ImageDraw
from build_gallery import ROOT
from export_gallery import font
import import_knight_redraw_v3 as h
import import_bastion_guardian_v1 as art
from revise_bastion_guardian_lance_rear import clear_old_rear
from revise_cavalry_map import digest,translate

REV='bastion-guardian-knight-lance-v6-20261022';OUT=ROOT/REV;SRC=OUT/'source'
EXTRA=['e7dfcb','8b7448','c5a668','f0d59a'];EEXTRA=['d1d4e1','56516c','9a8ea7','cabed0']
PALETTE=art.COLORS+[tuple(bytes.fromhex(x))for x in EXTRA]
EPALETTE=art.ECOLORS+[tuple(bytes.fromhex(x))for x in EEXTRA]
GRIP=[1338,174];ASSETS=[];PROOF={};PLACEMENTS={};TAIL_LAYERS={}

def write(p,v):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')

def save(im,path,purpose):
    p=OUT/path;p.parent.mkdir(parents=True,exist_ok=True);encoded=im
    if im.mode=='RGBA':
        colors=sorted(set(im.getdata()))
        if len(colors)<=256:
            # Lossless indexed PNG. Retain every RGBA value, including alpha,
            # rather than introducing another quantization or resizing pass.
            encoded=Image.new('P',im.size);encoded.putpalette([v for c in colors for v in c[:3]]+[0]*(768-3*len(colors)));table={c:i for i,c in enumerate(colors)};encoded.putdata([table[c]for c in im.getdata()]);encoded.info['transparency']=bytes(c[3]for c in colors)
            assert encoded.convert('RGBA').tobytes()==im.tobytes()
    encoded.save(p,optimize=True)
    ASSETS.append({'path':p.relative_to(ROOT).as_posix(),'purpose':purpose,'size':list(im.size),'bytes':p.stat().st_size,'sha256':digest(p)})
    return '../../../'+p.relative_to(ROOT).as_posix()

def faction(im,side):
    if side=='ally':return im.copy()
    table=dict(zip(PALETTE,EPALETTE));out=im.copy();out.putdata([(*table[p[:3]],p[3])if p[3]else(0,0,0,0)for p in im.getdata()]);return out

@lru_cache(maxsize=30000)
def weapon_color(rgb):
    r,g,b=rgb;hh,s,v=colorsys.rgb_to_hsv(r/255,g/255,b/255)
    if v<.24:return 0
    if .08<hh<.18 and s>.32:
        return 15 if v<.53 else 16 if v<.8 else 17
    if r>g*1.15 and g>b*1.1 and v<.69:return 11 if v<.38 else 10
    if b>r*1.2 and s>.3:return 0 if v<.4 else 1
    return min([0,1,3,4,5,12,13,14],key=lambda i:sum((a-b)**2 for a,b in zip(rgb,PALETTE[i])))

@lru_cache(maxsize=8)
def weapon(front):
    h.SRC=SRC;raw,meta=h.figures('knight-lance-master-v1.png',1)[0];scale=front/GRIP[0]
    dims=[round(raw.width*scale),round(raw.height*scale)];im=raw.resize(dims,Image.Resampling.NEAREST)
    im.putdata([(*PALETTE[weapon_color(p[:3])],255)if p[3]else(0,0,0,0)for p in im.getdata()])
    return im,[GRIP[0]*dims[0]/raw.width,GRIP[1]*dims[1]/raw.height]

def place(size,gp,front,direction,label):
    im,anchor=weapon(front);length=math.hypot(*direction);ux,uy=-direction[0]/length,-direction[1]/length
    # Rigid transform: positive local X goes from point to pommel. No skew.
    def transform(w,h,gx,gy,asset=im):
        return asset.transform((w,h),Image.Transform.AFFINE,(ux,uy,anchor[0]-ux*gx-uy*gy,-uy,ux,anchor[1]+uy*gx-ux*gy),resample=Image.Resampling.NEAREST)
    pad=64;large=transform(size[0]+2*pad,size[1]+2*pad,gp[0]+pad,gp[1]+pad);layer=large.crop((pad,pad,pad+size[0],pad+size[1]))
    before=sum(p[3]>0 for p in large.getdata());after=sum(p[3]>0 for p in layer.getdata());assert before==after,(label,'weapon clipped',before-after,gp,direction,front)
    cap=im.copy();cap.paste((0,0,0,0),(0,0,round(im.width*.91),im.height));TAIL_LAYERS[label]=transform(size[0],size[1],gp[0],gp[1],cap)
    PLACEMENTS[label]={'grip':gp,'front_length':front,'direction_to_tip':[direction[0]/length,direction[1]/length],'shared_asset_size':list(im.size),'clipped_pixels':0,'shaft_and_guard_and_pommel_present_in_layer':True}
    return layer

def check_tail(im,label):
    cap=TAIL_LAYERS[label];visible=sum(p[3]>0 and p==q for p,q in zip(cap.getdata(),im.getdata()));assert visible>0,(label,'pommel hidden')
    PLACEMENTS[label]['visible_pommel_pixels']=visible

def strip(im,gp,direction,radius=6,extent=145):
    out=im.copy();p=out.load();length=math.hypot(*direction);dx,dy=[v/length for v in direction];removed=[]
    for y in range(im.height):
        for x in range(im.width):
            vx,vy=x-gp[0],y-gp[1];along=vx*dx+vy*dy;dist=abs(vx*dy-vy*dx)
            if p[x,y][3]and 3<along<extent and dist<radius:
                p[x,y]=(0,0,0,0);removed.append([x,y])
    return out,removed

def glove(im,gp,r=8):
    layer=Image.new('RGBA',im.size)
    # Original own-pose gauntlet above the grip. Brown shaft pixels are excluded.
    for y in range(max(0,round(gp[1]-r)),min(im.height,round(gp[1]+r+1))):
        for x in range(max(0,round(gp[0]-r)),min(im.width,round(gp[0]+r+1))):
            p=im.getpixel((x,y))
            if p[3]and p[:3]not in[art.COLORS[i]for i in[7,8,10,11]]:layer.putpixel((x,y),p)
    return layer

def remove_old_fragments(im,weapon_layer,label):
    comps=h.parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))[3]);removed=[]
    for comp in comps[1:]:
        # All new lance pixels must remain; remove only detached old outline
        # fragments left by the differently angled leaf head/rear shaft.
        assert not any(weapon_layer.getpixel(p)[3]for p in comp),(label,'new lance became disconnected',len(comp))
        for p in comp:im.putpixel(p,(0,0,0,0));removed.append(list(p))
    PROOF.setdefault(label,{})['removed_old_detached_outline_pixels']=removed
    return im

def maps():
    result={};fixed=Image.open(ROOT/'bastion-guardian-idle-front-v3-20261022/ally/shared-fixed-body.png').convert('RGBA');phases=[]
    for phase,gp in enumerate([[22,52],[22,46],[22,40]]):
        arm=Image.open(ROOT/f'bastion-guardian-idle-front-v3-20261022/ally/arm-{phase:03}.png').convert('RGBA');hand=Image.open(ROOT/f'bastion-guardian-idle-front-v3-20261022/ally/hand-occlusion-{phase:03}.png').convert('RGBA');im=fixed.copy();im.alpha_composite(arm)
        layer=place(im.size,gp,39,[0,-1],f'map-idle-{phase}');im.alpha_composite(layer);im.alpha_composite(hand);check_tail(im,f'map-idle-{phase}');phases.append(im)
    result['tactical-idle']={i:phases[j]for i,j in enumerate([0,1,2,1,0,1])};walk={}
    specs={0:([88,57],[24,-30],38),1:([87,58],[24,-30],38),2:([81,66],[26,23],34),3:([81,66],[26,23],34),4:([37,60],[ -32,5],34),5:([39,60],[-32,5],34)}
    for i,(gp,direction,front)in specs.items():
        old=Image.open(SRC/f'before-tactical-walk-{i:03}.png').convert('RGBA');clean,removed=strip(old,gp,direction,4.5,65)
        # Remove only the old exposed stub behind the rear-view gauntlet.
        if i in[0,1]:
            for y in range(61,68):
                for x in range(83,91):
                    p=clean.getpixel((x,y))
                    if p[3]and p[:3]in[art.COLORS[j]for j in[7,10,11]]:clean.putpixel((x,y),(0,0,0,0));removed.append([x,y])
        layer=place(old.size,gp,front,direction,f'map-walk-{i}');im=clean.copy();im.alpha_composite(layer);im.alpha_composite(glove(old,gp,4));walk[i]=im
        PROOF[f'map-walk-{i}']={'old_weapon_removed_pixels':removed,'body_translation':[0,0],'hand_restored_from_own_pose':True}
        walk[i]=remove_old_fragments(im,layer,f'map-walk-{i}')
        check_tail(walk[i],f'map-walk-{i}')
    for i in[2,3]:walk[i+4]=walk[i].transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    result['tactical-walk']=walk;return result

def restoration():
    h.SRC=SRC;fig=h.figures('thrust-weapon-free-master-v1.png',1)[0];(im,meta),head=art.matte(fig);scale=124/(im.height-head[1]);h.REG=[]
    return h.register((im,meta),(320,256),head,[208,130],scale,'thrust-armour-restoration')

def battle(base):
    previous=json.loads((ROOT/'bastion-guardian-lance-rear-v5-20261022/baseline.json').read_text());poses={};restore=restoration();records=json.loads((ROOT/'bastion-guardian-lance-rear-v5-20261022/asset-manifest.json').read_text())['pose_repairs']
    for i in range(12):
        old=Image.open((ROOT/'professions/class-22-ally/battle'/previous['ally']['frame_mapping'][str(i)]).resolve()).convert('RGBA');gp=records[str(i)]['grip'];slope=records[str(i)]['axis_slope'];direction=[-1,-slope]
        if i==10:gp=[244,records[str(i)]['grip'][1]+slope*(244-248)];direction=[1,slope]
        clean,back_removed=clear_old_rear(old,i);clean,front_removed=strip(clean,gp,direction,8,150);restored=[]
        if i==11:
            # The old rear shaft crosses the breastplate/shield edge. Use only
            # its narrow band from the ImageGen restoration, preserving the
            # approved head, limbs, shield, cloth and all other existing pixels.
            for y in range(145,200):
                for x in range(180,280):
                    distance=abs((y-gp[1])-slope*(x-gp[0]))/math.sqrt(1+slope*slope)
                    if distance<=6.5:
                        clean.putpixel((x,y),restore.getpixel((x,y)));restored.append([x,y])
        layer=place(old.size,gp,82,direction,f'battle-{i}');im=clean.copy();im.alpha_composite(layer);im.alpha_composite(glove(old,gp,8));poses[i]=im
        PROOF[f'battle-{i}']={'old_front_removed_pixels':front_removed,'old_rear_removed_pixels':back_removed,'restored_old_shaft_band_pixels':restored,'body_translation':[0,0],'own_pose_gauntlet_layer':True}
        poses[i]=remove_old_fragments(im,layer,f'battle-{i}')
        check_tail(poses[i],f'battle-{i}')
    old=Image.open(SRC/'before-battle-025.png').convert('RGBA');gp=[189,108];clean=old.copy();clean.paste((0,0,0,0),(130,98,270,118));layer=place(old.size,gp,82,[-1,0],'battle-25');clean.alpha_composite(layer);clean.alpha_composite(glove(old,gp,8));poses[25]=clean;check_tail(clean,'battle-25')
    poses[27]=Image.open(SRC/'before-battle-027.png').convert('RGBA')
    poses[13]=poses[0].copy();poses[24]=poses[0].copy();return poses

def board(entries,kind,side,light):
    bg=(220,222,216)if light else(32,45,53);fg=(30,43,56)if light else(235,243,242);cw,ch=(300,266)if kind=='maps'else(344,296);cols=3
    out=Image.new('RGB',(cw*cols,56+ch*math.ceil(len(entries)/cols)),bg);d=ImageDraw.Draw(out);d.text((out.width/2,26),('盟军'if side=='ally'else'敌方')+'壁垒卫士 · 骑士长枪',anchor='mm',font=font(21),fill=fg)
    for n,(label,im)in enumerate(entries):
        if kind=='maps':im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
        x=n%cols*cw+(cw-im.width)//2;y=56+n//cols*ch;out.paste(im,(x,y),im);d.text((n%cols*cw+cw/2,y+ch-24),label,anchor='mm',font=font(15),fill=fg)
    save(out,f'{side}-{kind}-{"light"if light else"dark"}.png','complete weapon/hand/body inspection on dark or light background')

def build(publish=False):
    base=json.loads((OUT/'baseline.json').read_text());map_art=maps();battle_art=battle(base);drafts={}
    for side in['ally','enemy']:
        images={'maps':[],'battle':[]};mapping=copy.deepcopy(base['mappings'][side+'/maps'])
        for s in mapping['scenarios']:
            kind=s['id'];w,hh=s['output_frame_size'];atlas=Image.new('RGBA',(w*len(map_art[kind]),hh))
            for rec in s['frame_mapping']:
                i=rec['source_index'];im=faction(map_art[kind][i],side);path=save(im,f'{side}/{kind}/frame-{i:03}.png','same approved map pose, new conical knight lance');rec.update(path=path,output_path=path,revision=REV,sha256=ASSETS[-1]['sha256'],bytes=ASSETS[-1]['bytes']);atlas.alpha_composite(im,(i*w,0))
                if kind=='tactical-walk'or i<3:images['maps'].append((('待机'if kind=='tactical-idle'else['向上','向上','向右','向右','向下','向下','向左','向左'][i])+f' {i}',im))
            path=save(atlas,f'{side}/{kind}-atlas.png','unchanged native map slots with knight lance');s.update(revision=REV,output_atlas=path,output_atlas_bytes=ASSETS[-1]['bytes'],review_note='仅将武器统一为长锥形枪身、宽护手和配重尾端的骑士长枪；人物、正面盾牌、左右摆臂带盾、原步态与每相时长保持。',action_note='骑士长枪武器统一。',weapon_revision=REV)
            s.setdefault('motion_review',{}).update(weapon_revision=REV,weapon_source='one shared drawn knight lance, rigid transforms only',body_translation=[0,0],native_timing_modified=False)
            for k in['shared_spear','spear_positions','spear_size']:s['motion_review'].pop(k,None)
            s['motion_review']['shared_knight_lance']=f'../../../{REV}/{side}/shared-'+('idle-lance.png'if kind=='tactical-idle'else'walk-lance.png')
            if kind=='tactical-idle':
                s['motion_review'].get('static_pixel_proof',{}).pop('spear_positions',None)
                s['motion_review']['knight_lance_grips']=[[22,52],[22,46],[22,40]]
        mapping.update(revision=REV);drafts[f'professions/class-22-{side}/maps/frame_mapping.json']=mapping
        mapping=copy.deepcopy(base['mappings'][side+'/battle']);atlas=Image.new('RGBA',(320*len(mapping['frame_mapping']),256))
        for n,i in enumerate(mapping['output_atlas_frame_order']):
            im=faction(battle_art[i],side)
            shift=-64 if side=='enemy'and i in[13,24]else-96 if side=='enemy'and i in[25,27]else 0
            if shift:im=translate(im,[shift,0])
            if i!=27:
                path=save(im,f'{side}/battle/frame-{i:03}.png','new knight lance with original body pose and grip');mapping['frame_mapping'][str(i)]=path
                next(r for r in mapping['records']if r['source_frame']==i).update(path=path,sha256=ASSETS[-1]['sha256'],revision=REV)
            atlas.alpha_composite(im,(n*320,0))
            if i not in[13,24]:images['battle'].append((f'姿势 {i}'+(' · 释放后空手'if i==27 else''),im))
        projectile=Image.new('RGBA',(320,64));projectile.alpha_composite(place((320,64),[215,52],82,[-1,0],f'projectile-{side}'));path=save(faction(projectile,side),f'{side}/flying-lance.png','same drawn knight lance in native80x16 projectile canvas and40x8 anchor')
        mapping['effect_overrides']={k:path for k in mapping['effect_overrides']};mapping.update(revision=REV,output_atlas=save(atlas,f'{side}/battle-atlas.png','same native battle source order with new knight lance'),review_note='双方全部持枪、攻击、投枪与飞行图统一为参考图骑士长枪：长锥形浅色枪身、宽护手、完整握柄与配重尾端。人物、盾牌和四肢动作保持；普通攻击535帧与第246帧结算保持。',weapon_revision=REV,runtime_integrated=False,weapon_review={'shared_source':'source/knight-lance-master-v1.png','same_battle_weapon_all_phases':True,'front_length_pixels':82,'grip_and_body_not_translated':True,'release_pose_27_empty_hand_unchanged':True,'native_effect_positions_and_anchors_unchanged':True},batches=[{'id':'全动作骑士长枪','review':f'../../../{REV}/{side}-battle-dark.png','status':'pending_user_visual_acceptance'}]);drafts[f'professions/class-22-{side}/battle/frame_mapping.json']=mapping
        mapping.pop('rear_shaft_review',None)
        mapping['art_provenance']='Built-in ImageGen knight-lance asset and narrow old-shaft armour restoration; rigid weapon transforms on approved original body poses, own-pose gauntlets restored.'
        for front,name in[(82,'battle-lance'),(39,'idle-lance'),(38,'up-lance'),(34,'walk-lance')]:save(faction(weapon(front)[0],side),f'{side}/shared-{name}.png','same drawn knight lance; fixed scale within each original view')
        for kind in['maps','battle']:
            for light in[False,True]:board(images[kind],kind,side,light)
    write(OUT/'mapping-drafts.json',drafts);write(OUT/'asset-manifest.json',{'revision':REV,'image_generation':'built-in image_gen','source_master':'source/knight-lance-master-v1.png','prompt':'source/imagegen-prompt.json','restoration_master':'source/thrust-weapon-free-master-v1.png','palette':{'ally':[c.hex()for c in map(bytes,PALETTE)],'enemy':[c.hex()for c in map(bytes,EPALETTE)]},'placements':PLACEMENTS,'pose_changes':PROOF,'new_effects_or_damage_added':False,'native_timing_modified':False,'runtime_integrated':False,'assets':ASSETS})
    if publish:
        for path,m in drafts.items():write(ROOT/path,m)
    print(json.dumps({'status':'published'if publish else'staged','assets':len(ASSETS),'mappings':len(drafts),'weapon_placements':len(PLACEMENTS)}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');build(p.parse_args().publish)
