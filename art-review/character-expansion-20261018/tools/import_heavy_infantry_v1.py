#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stage whole ImageGen heavy-infantry poses with native programs unchanged."""
import argparse,copy,colorsys,json,math
from functools import lru_cache
from pathlib import Path
from PIL import Image,ImageDraw
from build_gallery import ROOT
import import_knight_redraw_v3 as helper
from revise_cavalry_map import digest,translate
from export_gallery import font

REV='heavy-infantry-redraw-v1-20261022';OUT=ROOT/REV;SRC=OUT/'source'
ALLY=['172638','304461','3976b5','6e8fb0','a7b9ca','f1f0e6','614538','925e46','d09873','f0c6a0','795a43','493b38','8296ac','c5d2db']
ENEMY=['151b2c','2d344f','484d7c','63678d','7f849f','b1b7d0','45415e','785b60','ad8590','dcc0b9','424361','2b304a','6b7597','949fbd']
COLORS=[tuple(bytes.fromhex(v)) for v in ALLY];ECOLORS=[tuple(bytes.fromhex(v)) for v in ENEMY]
ASSETS=[];REG=[]

def write(p,v):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')

@lru_cache(maxsize=8)
def figures(name,count):
    helper.SRC=SRC
    return helper.figures(name,count)

def face(im):
    return helper.landmark(im)[0]

def back_helmet(im):
    pts=[];p=im.load()
    for y in range(round(im.height*.12),round(im.height*.48)):
        for x in range(round(im.width*.08),round(im.width*.72)):
            r,g,b,a=p[x,y]
            if a and min(r,g,b)>155 and max(r,g,b)-min(r,g,b)<65:pts.append((x,y))
    candidates=[c for c in helper.parts(pts)if len(c)>100]
    assert candidates,'Missing rear helmet registration landmark'
    c=min(candidates,key=lambda c:min(y for x,y in c))
    return [(min(x for x,y in c)+max(x for x,y in c)+1)/2,(min(y for x,y in c)+max(y for x,y in c)+1)/2]

@lru_cache(maxsize=100000)
def material(rgb):
    r,g,b=rgb;h,s,v=colorsys.rgb_to_hsv(r/255,g/255,b/255)
    if v<.24:return 0
    if b>r*1.25 and b>g*1.10 and s>.35:return 1 if v<.38 else 2
    if r>g*1.12 and g>b*1.08 and .02<h<.14:
        if v<.43:return 11
        if v<.67:return 10 if s>.55 else 7
        return 8 if v<.82 else 9
    return min([0,1,3,4,5,12,13],key=lambda i:sum((a-b)**2 for a,b in zip(rgb,COLORS[i])))

def matte(fig,point,back=False):
    raw,meta=fig;out=Image.new('RGBA',raw.size);pix=[];hair_pixels=0
    for y in range(raw.height):
        for x in range(raw.width):
            r,g,b,a=raw.getpixel((x,y))
            if not a:pix.append((0,0,0,0));continue
            # One brown material on the small temple hair area; preserve light face.
            hair=(not back and abs(x-point[0])<raw.width*.13 and abs(y-point[1])<raw.height*.13 and r>g*1.14 and g>b*1.08 and max(r,g,b)<155)
            index=6 if hair else material((r,g,b));hair_pixels+=hair;pix.append((*COLORS[index],255))
    out.putdata(pix)
    return out,{**meta,'hair_material_pixels':hair_pixels,'hair_swatch':ALLY[6],'cloth_finish':'matte blue base with necessary dark folds; no highlight swatch'}

def register(fig,size,point,target,scale,label,back=False):
    converted=matte(fig,point,back);helper.REG=[];im=helper.register(converted,size,point,target,scale,label);REG.extend(helper.REG);return im

def map_poses():
    raw=figures('map-idle-master-v1.png',3);points=[face(f[0])for f in raw];scale=(84-35)/max(f[0].height-p[1]for f,p in zip(raw,points))
    idle=[register(f,(96,96),p,[48,35],scale,f'map-idle-{i}')for i,(f,p)in enumerate(zip(raw,points))]
    raw=figures('map-walk-master-v2.png',6);walk={}
    pair=raw[:2];points=[back_helmet(f[0])for f in pair];scale=88/max(f[0].height for f in pair);target=[64,round(4+points[0][1]*scale)]
    for i,(f,p)in enumerate(zip(pair,points)):walk[i]=register(f,(128,96),p,target,scale,f'map-walk-{i}',True)
    for ids in [[2,3],[4,5]]:
        points=[face(raw[i][0])for i in ids];scale=(94-48)/max(raw[i][0].height-p[1]for i,p in zip(ids,points))
        for i,p in zip(ids,points):walk[i]=register(raw[i],(128,96),p,[64,48],scale,f'map-walk-{i}')
    for i in [2,3]:walk[i+4]=walk[i].transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    return {'tactical-idle':{i:idle[n]for i,n in enumerate([0,1,2,1,0,1])},'tactical-walk':walk}

def battle_poses():
    raw={i:f for i,f in zip([0,4,5,6,7,8],figures('battle-march-master-v1.png',6))}
    raw.update({i:f for i,f in zip([9,10,11,12,30,32],figures('battle-action-master-v1.png',6))})
    points={i:face(f[0])for i,f in raw.items()};scale=(254-160)/max(raw[i][0].height-points[i][1]for i in raw)
    result={i:register(f,(320,256),points[i],[188,160],scale,f'battle-{i}')for i,f in raw.items()}
    result[16]=result[0].copy();result[29]=result[0].copy()
    return result

def faction(im,side):
    if side=='ally':return im.copy()
    table=dict(zip(COLORS,ECOLORS));out=im.copy();out.putdata([(*table[p[:3]],p[3])if p[3]else(0,0,0,0)for p in im.getdata()]);return out

def save(im,name,purpose):
    p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);im.save(p,optimize=True)
    ASSETS.append({'path':p.relative_to(ROOT).as_posix(),'purpose':purpose,'size':list(im.size),'bytes':p.stat().st_size,'sha256':digest(p),'colors':len({v[:3]for v in im.convert('RGBA').getdata()if v[3]})})
    return '../../../'+p.relative_to(ROOT).as_posix()

def projectile(side):
    # Reuse the accepted drawn wood/steel lance, preserving the native64x16 canvas.
    im=Image.open(ROOT/'knight-redraw-v3-20261021/ally/flying-lance.png').convert('RGBA');out=im.copy();out.putdata([(*COLORS[material(p[:3])],p[3])if p[3]else(0,0,0,0)for p in im.getdata()])
    return save(faction(out,side),f'{side}/flying-lance.png','accepted complete wood/steel javelin; original64x16 canvas and32x8 anchor retained')

def boards(images):
    for side in ['ally','enemy']:
        for kind,entries in images[side].items():
            for light in [False,True]:
                cw,ch=(288,250)if kind=='maps'else(344,296);bg=(220,222,216)if light else(32,45,53);fg=(30,43,56)if light else(235,243,242)
                board=Image.new('RGB',(cw*3,56+ch*math.ceil(len(entries)/3)),bg);d=ImageDraw.Draw(board);d.text((board.width//2,25),('盟军'if side=='ally'else'敌方')+'重装兵 · '+('地图'if kind=='maps'else'战斗'),anchor='mm',font=font(20),fill=fg)
                for n,(label,im)in enumerate(entries):
                    if kind=='maps':im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
                    x=n%3*cw+(cw-im.width)//2;y=56+n//3*ch;board.paste(im,(x,y),im);d.text((n%3*cw+cw//2,y+ch-26),label,anchor='mt',font=font(14),fill=fg)
                save(board,f'{side}-{kind}-{"light"if light else"dark"}.png','whole pose inspection on dark/light background')

def build(publish=False):
    base_maps=json.loads((SRC/'ally-maps-mapping-before.json').read_text());base_battle=json.loads((SRC/'ally-battle-mapping-before.json').read_text());maps=map_poses();battle=battle_poses();drafts={};images={}
    for side in ['ally','enemy']:
        actor='class-2-'+side;name=('盟军'if side=='ally'else'敌方')+'重装兵';images[side]={'maps':[],'battle':[]}
        m=copy.deepcopy(base_maps);m.update(character_id=actor,actor_id=actor,display_name=name,display_class_name='重装兵',source_side=side,revision=REV,status='review_candidate',runtime_integrated=False,modified_by='codex',author='codex')
        for s in m['scenarios']:
            kind=s['id'];w,h=s['output_frame_size'];atlas=Image.new('RGBA',(w*len(maps[kind]),h));records=[]
            for i,raw in sorted(maps[kind].items()):
                im=faction(raw,side);path=save(im,f'{side}/{kind}/frame-{i:03}.png','complete ImageGen map pose: '+kind);atlas.alpha_composite(im,(i*w,0));records.append({'source_index':i,'source_frame':i,'path':path,'output_path':path,'revision':REV,'size':[w,h],'bytes':ASSETS[-1]['bytes'],'sha256':ASSETS[-1]['sha256'],'art_status':'review_candidate'})
                if kind=='tactical-walk'or i<3:images[side]['maps'].append((('待机'if kind=='tactical-idle'else['向上','向上','向右','向右','向下','向下','向左','向左'][i])+f' {i}',im))
            s.update(source_side=side,character_id=actor,display_name=name,source_atlas=s['source_atlas'].replace('class_2_ally','class_2_'+side).replace('class-2-ally','class-2-'+side),revision=REV,frame_mapping=records,output_atlas=save(atlas,f'{side}/{kind}-atlas.png','packed native map slots'),output_atlas_bytes=ASSETS[-1]['bytes'],status='review_candidate',art_review_status='review_candidate',review_note='重新绘制中阶重装兵；固定头部和中轴，完整姿势按原相位登记；蓝白／蓝紫14色，纯色发色和哑光衣料。',action_note='本轮完整重绘，待验收；原顺序和节奏保持。',motion_review={'center':'one face/helmet landmark per direction, fixed target and shared pair scale','native_timing_changed':False,'shield':'attached to the same forearm in the whole drawn pose','runtime_integrated':False})
            if kind=='tactical-walk':
                native=json.loads((ROOT/'source-input/corrected-tactical-walk/overlay.json').read_text())['records'][actor];s['source_audit']=dict(native,status='verified_native_tactical',overlay='../../../source-input/corrected-tactical-walk/overlay.json');s['source_aliases']={str(i):i for i in range(8)}
        drafts[f'professions/{actor}/maps/frame_mapping.json']=m
        m=copy.deepcopy(base_battle);paths={};records=[];atlas=Image.new('RGBA',(320*len(battle),256))
        for n,(i,raw)in enumerate(sorted(battle.items())):
            im=faction(raw,side);shift=-64 if side=='enemy'and i in[16,29,30,32]else 0
            if shift:
                shifted=translate(im,[shift,0]);assert sum(p[3]>0 for p in shifted.getdata())==sum(p[3]>0 for p in im.getdata());im=shifted
            paths[str(i)]=save(im,f'{side}/battle/frame-{i:03}.png','complete battle pose; native background-slot displacement retained');atlas.alpha_composite(im,(n*320,0));records.append({'source_frame':i,'path':paths[str(i)],'native_background_translation':[shift,0],'art_status':'review_candidate','sha256':ASSETS[-1]['sha256']})
            if i not in[16,29]:images[side]['battle'].append((f'原姿势 {i}',im))
        keys=[f'original_class_2_{"enemy_"if side=="enemy"else""}normal']+[f'class_2_{side}_javelin'+s for s in['','_vs_heavy','_far_ally','_far_ally_vs_heavy','_far_enemy','_far_enemy_vs_heavy']]
        m.update(character_id=actor,display_name=name,display_class_name='重装兵',source_side=side,source_atlas='../../../source-input/'+('original-motion/class-2.png'if side=='ally'else'enemy-motion/class-2-enemy.png'),revision=REV,frame_mapping=paths,records=records,canonical_frames=sorted(battle),required_source_frames=sorted(battle),output_atlas_frame_order=sorted(battle),variant_keys=keys,output_atlas=save(atlas,f'{side}/battle-atlas.png','all required native battle slots'),effect_overrides={('821da2c74511b4'if side=='ally'else'native-47ac810355f872'):projectile(side)},palette=ALLY if side=='ally'else ENEMY,status='review_candidate',runtime_integrated=False,modified_by='codex',author='codex',limitations=[],batches=[{'id':'full-pose-redraw','review':f'../../../{REV}/{side}-battle-dark.png','status':'review_candidate'}],review_note='全新中阶板甲重装兵：厚度介于士兵和壁垒卫士之间；战斗双手持枪，地图盾牌随左臂；哑光蓝白／蓝紫、纯色头发，原作攻击、投枪及结算时刻保持。',source_semantics={'0/4-10':'two-handed low spear carry and native march leg phases','11':'pull back straight spear toward chest, point upper-left and butt lower-right, helmet plume trails behind','12':'one forward thrust, both hands on continuous spear','16/29':'native idle background alias of0; enemy-16 logical pixels','30':'one horizontal overhead javelin','32':'empty forward hand after release; no held shaft','enemy30/32':'native background displacement-16 logical pixels'},art_provenance='Built-in ImageGen whole figure sprite sheets, uniform scale and rigid registration only; material palette and alpha matte; no limb slicing or warping.')
        drafts[f'professions/{actor}/battle/frame_mapping.json']=m
    boards(images);write(OUT/'mapping-drafts.json',drafts);write(OUT/'asset-manifest.json',{'revision':REV,'image_generation':'built-in image_gen','runtime_integrated':False,'native_timing_modified':False,'palette':{'ally':ALLY,'enemy':ENEMY},'registration':REG,'assets':ASSETS,'body_splicing':False,'limb_warping':False,'source_masters':'source/*-master-v1.png retained offline'})
    if publish:
        for path,mapping in drafts.items():write(ROOT/path,mapping)
        for side in ['ally','enemy']:
            write(ROOT/f'professions/class-2-{side}/manifest.json',{'id':'class-2-'+side,'class_id':2,'display_name':('盟军'if side=='ally'else'敌方')+'重装兵','revision':REV,'status':'review_candidate','runtime_integrated':False,'maps':'maps/frame_mapping.json','battle':'battle/frame_mapping.json'})
    print(json.dumps({'status':'published'if publish else'staged','mappings':len(drafts),'whole_pose_registrations':len(REG),'assets':len(ASSETS)}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');build(p.parse_args().publish)
