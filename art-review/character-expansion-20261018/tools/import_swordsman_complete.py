#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Class9: retain whole drawn native poses, matte materials, stable map core.

Art masters are existing complete ImageGen figures plus the new blue-white
material master. This file performs material indexing, registration and packing;
it does not generate character anatomy or deform joints.
"""
import argparse, copy, colorsys, json, math
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFilter
from build_gallery import ROOT
from export_gallery import font
from import_knight_redraw_v3 import parts
from revise_cavalry_map import digest, translate

REV='swordsman-complete-v1-20261022';OUT=ROOT/REV;SRC=OUT/'source'
# Named material indices, shared by both sides. No hair highlight entry.
NAMES=['outline','navy_shadow','blue_fold','blue','white_shadow','soft_white',
       'steel_shadow','steel','skin_shadow','skin','hair','leather_shadow','leather','warm_edge']
HEX=['182837','2b3d51','2c5680','3c76ad','aabbc5','e8e8da',
     '8295a8','e2e9e7','b77f61','e7b28b','724b38','44342e','79563e','c1ae84']
EHEX=['171c31','292d4b','373f69','555784','7783a4','a8b3cb',
      '586486','b0bdd3','b07d67','deb092','49415e','29283d','514964','9386aa']
C=[tuple(bytes.fromhex(v))for v in HEX];EC=[tuple(bytes.fromhex(v))for v in EHEX]
ASSETS=[];PROOF={};STABLE={}
FACE={0:[190,158],1:[185,161.5],2:[175,162],3:[168.5,166.5],4:[188.5,149],
      5:[200,140],7:[173,191],8:[172.5,194.5],9:[175,193.5],10:[160.5,199],11:[164,198],24:[191,159]}
NATIVE_FACE={0:[190,148],1:[176,156],2:[176,156],3:[176,156],4:[190,148],5:[188,148],
             7:[190,188],8:[190,188],9:[190,188],10:[176,188],11:[176,188],24:[190,148]}
MAP_FACE={0:[68,42],1:[67,42],2:[56,47],3:[56,48],4:[65.5,46],5:[60.5,44.5],6:[65.5,47],7:[64,47]}

def write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')

def save(im,path,purpose):
    p=OUT/path;p.parent.mkdir(parents=True,exist_ok=True);encoded=im
    if im.mode=='RGBA':
        colors=sorted(set(im.getdata()))
        if len(colors)<=256:
            encoded=Image.new('P',im.size);encoded.putpalette([v for p in colors for v in p[:3]]+[0]*(768-len(colors)*3));idx={p:i for i,p in enumerate(colors)};encoded.putdata([idx[p]for p in im.getdata()]);encoded.info['transparency']=bytes(p[3]for p in colors)
            assert encoded.convert('RGBA').tobytes()==im.tobytes()
    encoded.save(p,optimize=True);ASSETS.append({'path':p.relative_to(ROOT).as_posix(),'purpose':purpose,'size':list(im.size),'bytes':p.stat().st_size,'sha256':digest(p)})
    return '../../../'+p.relative_to(ROOT).as_posix()

@lru_cache(maxsize=60000)
def material(rgb):
    r,g,b=rgb;h,s,v=colorsys.rgb_to_hsv(r/255,g/255,b/255)
    if v<.17:return 0
    if v<.29:return 1 if b>r or max(rgb)-min(rgb)<19 else 11
    # Sash belongs to the same blue cloth as the tunic and shield.
    if r>g*1.45 and b>g*1.10:return 2 if v<.38 else 3
    if .36<h<.75 and s>.28:return 2 if v<.28 else 3
    if s<.22:
        if v<.42:return 1
        if v<.60:return 6
        return 4 if v<.75 else 5
    if r>g*1.12 and g>b*1.08:
        if r>180 and g>r*.58 and b>r*.32:return 9
        if v>.46:return 5  # Former copper trim becomes restrained ivory trim.
        if v>.39:return 13 if s<.48 else 12
        return 11
    return min(range(len(C)),key=lambda i:sum((a-b)**2 for a,b in zip(rgb,C[i])))

def matte(old,face,label,back=False):
    pix=old.load();comp=parts((x,y)for y in range(old.height)for x in range(old.width)if pix[x,y][3]>=128);keep=set(comp[0]);out=Image.new('RGBA',old.size)
    for x,y in keep:out.putpixel((x,y),(*C[material(pix[x,y][:3])],255))
    # The warm hair material is isolated above/beside the own-pose face. Close
    # one-pixel holes between strands, while retaining the outer dark contour.
    cx,cy=face;ratio=1 if old.width>150 else .66
    roi=[round(cx-20*ratio),round(cy-26*ratio),round(cx+24*ratio),round(cy+3*ratio)]
    hair=Image.new('L',old.size);hp=hair.load()
    face_top=cy-(9 if old.width>150 else 3.5)
    for x,y in keep:
        if not(roi[0]<=x<roi[2]and roi[1]<=y<roi[3]):continue
        r,g,b,a=pix[x,y];h,s,v=colorsys.rgb_to_hsv(r/255,g/255,b/255)
        warm=r>g*1.14 and g>b*1.08 and v>.20
        skin=(r>180 and g>r*.58 and b>r*.32)
        if warm and(back or y<face_top or(not skin and y<cy-1)):hp[x,y]=255
    closed=hair.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))
    for x,y in keep:
        if closed.getpixel((x,y)) and out.getpixel((x,y))[:3]!=C[0]:out.putpixel((x,y),(*C[10],255))
    if not back:
        # The old tiny master has no readable eye after material reduction.
        # Preserve a drawn eye/nose/mouth from the new ImageGen master rather
        # than painting a procedural face. Use a rigid nearest-neighbour patch.
        patch=face_detail(old.width>150);point=[round(cx-patch.width*.48),round(cy-patch.height*.40)]
        out.alpha_composite(patch,tuple(point))
    tidy=tidy_highlights(out,face)
    PROOF[label]={'input_alpha_bounds':old.getbbox(),'retained_component_pixels':len(keep),'removed_subthreshold_or_detached_pixels':sum(p[3]>0 for p in old.getdata())-len(keep),'hair_roi':roi,'hair_material':'one chestnut fill + outline','palette_colors':len(set(p for p in out.getdata()if p[3])),'highlight_cleanup':tidy}
    return out

def tidy_highlights(im,face):
    """Remove isolated material glints only; leave skin/eyes/alpha untouched."""
    p=im.load();light={C[i]for i in[4,5,7]};cx,cy=face;large=im.width>150
    protected=[round(cx-(10 if large else 6)),round(cy-(10 if large else 5)),round(cx+(13 if large else 7)),round(cy+(13 if large else 7))]
    candidates=parts((x,y)for y in range(im.height)for x in range(im.width)if p[x,y][3]and p[x,y][:3]in light)
    changes=[];threshold=12 if large else 5
    for comp in candidates:
        if len(comp)>threshold:continue
        for x,y in comp:
            if protected[0]<=x<protected[2]and protected[1]<=y<protected[3]:continue
            neighbors=[]
            for yy in range(max(0,y-2),min(im.height,y+3)):
                for xx in range(max(0,x-2),min(im.width,x+3)):
                    rgb=p[xx,yy][:3]
                    if p[xx,yy][3]and rgb in[C[i]for i in[1,2,3,6,11,12]]:neighbors.append(rgb)
            if not neighbors:continue
            # Use the surrounding material (blue cloth/metal shadow/leather),
            # never convert a surviving skin pixel into a white fleck.
            color=max(set(neighbors),key=neighbors.count);p[x,y]=(*color,255);changes.append([x,y])
    return {'isolated_light_pixels_recolored':len(changes),'protected_skin_eye_box':protected,'alpha_changed':False}

@lru_cache(maxsize=2)
def face_detail(large):
    raw=Image.open(SRC/'map-head-crop.png').convert('RGBA').crop((67,126,178,191));result=Image.new('RGBA',raw.size)
    for y in range(raw.height):
        for x in range(raw.width):
            r,g,b,a=raw.getpixel((x,y))
            if a<128:continue
            v=max(r,g,b)/255
            if v<.24:index=0
            elif max(r,g,b)-min(r,g,b)<30:index=5 if v>.68 else 0
            elif r>160 and g>r*.53 and b>r*.26:index=9
            elif r>g*1.2:index=10
            else:index=8
            result.putpixel((x,y),(*C[index],255))
    scale=.13 if large else .075
    return result.resize((round(raw.width*scale),round(raw.height*scale)),Image.Resampling.NEAREST)

def faction(im,side):
    if side=='ally':return im.copy()
    table=dict(zip(C,EC));result=Image.new('RGBA',im.size);result.putdata([(*table[p[:3]],p[3])if p[3]else(0,0,0,0)for p in im.getdata()]);return result

def freeze(poses,ids,rects,label):
    base=poses[ids[0]]
    for i in ids[1:]:
        for rect in rects:poses[i].paste(base.crop(rect),rect[:2])
    for rect in rects:
        assert all(poses[i].crop(rect).tobytes()==base.crop(rect).tobytes()for i in ids)
    STABLE[label]={'frames':ids,'fixed_head_and_torso_regions':rects,'identical_rgba_verified':True,'whole_body_bob':[0,0]}

def maps():
    walk={}
    # Preserve eight independently drawn, native CPU-decoded slots. No mirror.
    for i in range(8):
        im=matte(Image.open(SRC/f'before-tactical-walk-{i:03}.png').convert('RGBA'),MAP_FACE[i],f'walk-{i}',i<2)
        dx={1:1,5:5,7:2}.get(i,0);walk[i]=translate(im,[dx,0]);PROOF[f'walk-{i}']['translation']=[dx,0]
    freeze(walk,[0,1],[[57,28,79,46],[59,46,74,64]],'walk-up')
    freeze(walk,[2,3],[[46,30,75,53],[56,53,70,68]],'walk-right')
    freeze(walk,[4,5],[[53,26,79,51],[60,51,72,67]],'walk-down')
    freeze(walk,[6,7],[[54,29,82,54],[64,54,78,69]],'walk-left')
    for i,im in walk.items():
        cc=parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))[3])
        for c in cc[1:]:
            assert len(c)<=3,(i,'disconnected limb or weapon')
            for pt in c:im.putpixel(pt,(0,0,0,0))
    idle={i:matte(Image.open(SRC/f'before-tactical-idle-{i:03}.png').convert('RGBA'),[53.5+(i>0),29.5],f'idle-{i}')for i in range(3)}
    for i in[1,2]:idle[i]=translate(idle[i],[-1,0])
    freeze(idle,[0,1,2],[[43,15,65,34],[47,34,62,54],[40,54,68,82]],'idle')
    return {'tactical-walk':walk,'tactical-idle':{i:idle[j]for i,j in enumerate([0,1,2,1,0,1])}}

def battle():
    poses={}
    for i in FACE:
        old=Image.open(SRC/f'before-battle-{i:03}.png').convert('RGBA');im=matte(old,FACE[i],f'battle-{i}');delta=[round(NATIVE_FACE[i][j]-FACE[i][j])for j in range(2)]
        poses[i]=translate(im,delta);before=sum(p[3]>0 for p in im.getdata());after=sum(p[3]>0 for p in poses[i].getdata());assert before==after,(i,'body clipped')
        PROOF[f'battle-{i}'].update(registration={'own_pose_face':FACE[i],'native_face_at_4x':NATIVE_FACE[i],'translation':delta,'uniform_scale':1,'clipped_pixels':0,'joint_deformation':False})
    # A source slash is an effect, not an additional attack. Frame6 contains the
    # identical frame7 body plus its exact native arc at the original positions.
    for side in['ally','enemy']:
        native6=Image.open(SRC/f'native-battle-{side}-006.png').convert('RGBA');native7=Image.open(SRC/f'native-battle-{side}-007.png').convert('RGBA');arc=native6.copy()
        for y in range(64):
            for x in range(80):
                p=native7.getpixel((x,y))
                if p[3]:assert native6.getpixel((x,y))==p;arc.putpixel((x,y),(0,0,0,0))
        arc=arc.resize((320,256),Image.Resampling.NEAREST);save(arc,f'{side}-native-slash-only.png','exact own-faction native slash effect, separated from the body')
        if side=='ally':poses[6]=arc.copy();poses[6].alpha_composite(poses[7])
    poses[12]=poses[0].copy();poses[23]=poses[0].copy()
    return poses

def board(entries,kind,side,light):
    bg=(220,222,216)if light else(32,45,53);fg=(28,44,58)if light else(234,242,241);cw,ch=(310,282)if kind=='maps'else(340,292);cols=4
    out=Image.new('RGB',(cw*cols,56+ch*math.ceil(len(entries)/cols)),bg);d=ImageDraw.Draw(out);d.text((out.width/2,26),('盟军'if side=='ally'else'敌方')+'剑士 · 全姿态',anchor='mm',font=font(21),fill=fg)
    for n,(label,im)in enumerate(entries):
        if kind=='maps':im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
        x=n%cols*cw+(cw-im.width)//2;y=56+n//cols*ch;out.paste(im,(x,y),im);d.text((n%cols*cw+cw/2,y+ch-22),label,anchor='mm',font=font(15),fill=fg)
    save(out,f'{side}-{kind}-{"light"if light else"dark"}.png','all-pose inspection on dark or light background')

def build(publish=False):
    base=json.loads((OUT/'baseline.json').read_text());mapart=maps();battleart=battle();drafts={}
    for side in['ally','enemy']:
        name=('盟军'if side=='ally'else'敌方')+'剑士';images={'maps':[],'battle':[]};mapping=copy.deepcopy(base['mappings']['maps'])
        mapping.update(character_id=f'class-9-{side}',actor_id=f'class-9-{side}',display_name=name,display_class_name='剑士',source_side=side,revision=REV,status='complete_art_review_passed',review_note='双方剑士：单手剑与小盾；固定地图头身与待机双脚；八个独立步态槽；纯色头发、哑光蓝白／蓝紫衣装。原作时序不变，待用户验收。',runtime_integrated=False)
        for scenario in mapping['scenarios']:
            kind=scenario['id'];scenario.update(revision=REV,review_note=mapping['review_note'],status='complete_art_review_passed');w,hh=scenario['output_frame_size'];atlas=Image.new('RGBA',(w*len(mapart[kind]),hh))
            scenario['source_atlas']=f'../../../source-input/corrected-tactical-walk/class-9-{side}.png'if kind=='tactical-walk'else f'../../../source-input/legacy-assets/assets/original/graphics/map_units/class_9_{side}.png'
            if kind=='tactical-walk':scenario['source_audit'].update(status='verified_native_tactical',record_key=f'class-9-{side}')
            for record in scenario['frame_mapping']:
                i=record['source_index'];im=faction(mapart[kind][i],side);path=save(im,f'{side}/{kind}/frame-{i:03}.png','native map slot with matte faction materials and fixed core');record.update(path=path,output_path=path,revision=REV,sha256=ASSETS[-1]['sha256'],bytes=ASSETS[-1]['bytes'],art_status='reviewed_selected');atlas.alpha_composite(im,(i*w,0))
                if kind=='tactical-walk'or i<3:images['maps'].append((('待机'if kind=='tactical-idle'else['向上','向上','向右','向右','向下','向下','向左','向左'][i])+f' {i}',im))
            path=save(atlas,f'{side}/{kind}-atlas.png','native slot order at exact 4x output size');scenario.update(output_atlas=path,output_atlas_bytes=ASSETS[-1]['bytes'],motion_review={'revision':REV,'fixed_core':STABLE,'native_timing_modified':False,'independent_direction_slots':True,'direction_mirroring':False})
        drafts[f'professions/class-9-{side}/maps/frame_mapping.json']=mapping
        mapping=copy.deepcopy(base['mappings']['battle']);mapping.update(character_id=f'class-9-{side}',display_name=name,display_class_name='剑士',source_side=side,revision=REV,status='complete_art_review_passed',runtime_integrated=False,review_note='逐相按原作面部基准登记完整姿态，保留剑盾、跑步、跃起、举剑、下斩和收势；不扭曲肢体。原作剑弧与雷之剑触发程序不变。',art_generator='built-in image_gen: complete retained pose masters + new matte material master',source_atlas=f'../../../source-input/{"original"if side=="ally"else"enemy"}-motion/class-9'+(''if side=='ally'else'-enemy')+'.png')
        if side=='enemy':mapping['variant_keys']=['original_class_9_enemy_normal']+[k.replace('_ally_levin','_enemy_levin')for k in mapping['variant_keys'][1:]]
        order=sorted(battleart);mapping['canonical_frames']=order;mapping['output_atlas_frame_order']=order;atlas=Image.new('RGBA',(320*len(order),256));records=[]
        for n,i in enumerate(order):
            # Native enemy background records12/23/24 are stored16 source
            # pixels left of OAM. Keep that storage offset; renderer applies the
            # original faction flip/origin correction at playback.
            im=faction(battleart[i],side)if i!=6 else battleart[6].copy()
            if i==6 and side=='enemy':
                im=Image.open(OUT/'enemy-native-slash-only.png').convert('RGBA');im.alpha_composite(faction(battleart[7],side))
            shift=-64 if side=='enemy'and i in[12,23,24]else 0
            if shift:im=translate(im,[shift,0])
            path=save(im,f'{side}/battle/frame-{i:03}.png','whole native sword/shield pose with fixed landmark and faction materials');mapping['frame_mapping'][str(i)]=path;atlas.alpha_composite(im,(n*320,0));records.append({'source_frame':i,'path':path,'size':[320,256],'bytes':ASSETS[-1]['bytes'],'sha256':ASSETS[-1]['sha256'],'alpha_bounds':im.getbbox(),'source_background_translation':[shift,0]})
            if i not in[12,23]:images['battle'].append((f'原姿势 {i}',im))
        mapping.update(records=records,output_atlas=save(atlas,f'{side}/battle-atlas.png','all required native battle slots, lossless indexed RGBA'),external_effects='Original source slash only behind frame7 in frame6. Original lightning remains external and is never duplicated.');drafts[f'professions/class-9-{side}/battle/frame_mapping.json']=mapping
        for kind in images:
            for light in[False,True]:board(images[kind],kind,side,light)
    write(OUT/'mapping-drafts.json',drafts);write(OUT/'asset-manifest.json',{'revision':REV,'generator':'built-in image_gen','new_master':'source/blue-white-material-master-v1.png','pose_sources':'existing professions/class-9-ally/{maps,battle}/source ImageGen full poses, immutable before copies retained','palette':dict(zip(NAMES,HEX)),'enemy_palette':dict(zip(NAMES,EHEX)),'matte_and_registration':PROOF,'fixed_map_regions':STABLE,'assets':ASSETS,'runtime_integrated':False,'user_visual_acceptance':'pending'})
    if publish:
        for path,m in drafts.items():write(ROOT/path,m)
    print(json.dumps({'revision':REV,'assets':len(ASSETS),'mapping_count':len(drafts),'published':publish}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');build(p.parse_args().publish)
