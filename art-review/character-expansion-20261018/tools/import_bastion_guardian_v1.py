#!/usr/bin/env python3
"""Stage complete drawn poses; uniform whole-figure registration, matte materials."""
import argparse, copy, colorsys, json, math
from functools import lru_cache
from pathlib import Path
from PIL import Image, ImageDraw
from build_gallery import ROOT
import import_knight_redraw_v3 as helper
from revise_cavalry_map import digest, translate
from export_gallery import font

REV='bastion-guardian-v1-20261022'; OUT=ROOT/REV; SRC=OUT/'source'
ALLY=['172638','304461','3976b5','6e8fb0','a7b9ca','f1f0e6','6c6870','925e46','d09873','f0c6a0','795a43','493b38','8296ac','c5d2db']
ENEMY=['151b2c','2d344f','484d7c','63678d','7f849f','b1b7d0','55536c','785b60','ad8590','dcc0b9','424361','2b304a','6b7597','949fbd']
COLORS=[tuple(bytes.fromhex(v)) for v in ALLY]; ECOLORS=[tuple(bytes.fromhex(v)) for v in ENEMY]
ASSETS=[]; REG=[]

def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

@lru_cache(maxsize=8)
def figures(name,count):
    helper.SRC=SRC
    records=list(helper.figures(name,count))
    if count==8:
        rows=sorted(records,key=lambda z:z[1]['source_bounds'][1]);records=sorted(rows[:4],key=lambda z:z[1]['source_bounds'][0])+sorted(rows[4:],key=lambda z:z[1]['source_bounds'][0])
    return records

def hair_region(im):
    p=im.load();pts=[]
    for y in range(int(im.height*.65)):
        for x in range(im.width):
            r,g,b,a=p[x,y];h,s,v=colorsys.rgb_to_hsv(r/255,g/255,b/255)
            if a and s<.25 and .18<v<.67 and r>=.95*b and r>=g*.98:pts.append((x,y))
    c=helper.parts(pts)[0]
    box=[min(x for x,y in c),min(y for x,y in c),max(x for x,y in c)+1,max(y for x,y in c)+1]
    # Hair material is identified in the original generated art, before resampling.
    # Keep its dark outline; flatten all neutral interior tones, including shine.
    mask=set()
    for y in range(max(0,box[1]-3),min(im.height,box[3]+3)):
        for x in range(max(0,box[0]-3),min(im.width,box[2]+3)):
            r,g,b,a=p[x,y];h,s,v=colorsys.rgb_to_hsv(r/255,g/255,b/255)
            if a and s<.28 and v>.15 and r>=.94*b and r>=g*.98:mask.add((x,y))
    return [(box[0]+box[2])/2,box[1]],box,mask

@lru_cache(maxsize=100000)
def material(rgb):
    r,g,b=rgb;h,s,v=colorsys.rgb_to_hsv(r/255,g/255,b/255)
    if v<.24:return 0
    # Blue cloth has one matte base and a necessary dark fold color.
    if b>r*1.25 and b>g*1.12 and s>.35:return 1 if v<.38 else 2
    if r>g*1.16 and g>b*1.12 and .02<h<.13:
        if v<.43:return 11
        if v<.67:return 10 if s>.55 else 7
        return 8 if v<.82 else 9
    return min([0,1,3,4,5,7,8,9,10,11,12,13],key=lambda i:sum((a-b)**2 for a,b in zip(rgb,COLORS[i])))

def matte(figure):
    raw,meta=figure;point,box,mask=hair_region(raw);im=Image.new('RGBA',raw.size)
    im.putdata([(*COLORS[6 if (x,y) in mask else material(raw.getpixel((x,y))[:3])],255) if raw.getpixel((x,y))[3] else (0,0,0,0) for y in range(raw.height)for x in range(raw.width)])
    return (im,{**meta,'hair_material_box':box,'hair_color':ALLY[6],'hair_swatch_count':1}),point

def registered(fig,size,point,target,scale,label):
    helper.REG=[];im=helper.register(fig,size,point,target,scale,label);REG.extend(helper.REG);return im

def map_poses():
    idle=[matte(f)for f in figures('map-idle-master-v1.png',3)]
    scale=64/max(f[0].height-p[1]for f,p in idle)
    poses=[registered(f,(96,96),p,[48,16],scale,f'idle-{i}')for i,(f,p)in enumerate(idle)]
    walk={};raw=[matte(f)for f in figures('map-walk-master-v1.png',6)]
    for ids in [[0,1],[2,3],[4,5]]:
        scale=64/max(raw[i][0][0].height-raw[i][1][1]for i in ids)
        for i in ids:
            f,p=raw[i];walk[i]=registered(f,(128,96),p,[64,32],scale,f'walk-{i}')
    # Native left/right source silhouettes are reflected whole figures.
    for i in [2,3]:walk[i+4]=walk[i].transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    return {'tactical-idle':{i:poses[n]for i,n in enumerate([0,1,2,1,0,1])},'tactical-walk':walk}

def battle_poses():
    raw={i:matte(f)for i,f in enumerate(figures('battle-march-master-v2.png',6))}
    raw.update({i:matte(f)for i,f in zip([6,7,8,9,10,11,25,27],figures('battle-action-master-v1.png',8))})
    result={}
    for ids in [list(range(6)),[6,7,8],[9],[10],[11],[25,27]]:
        scale=124/max(raw[i][0][0].height-raw[i][1][1]for i in ids)
        for i in ids:
            f,p=raw[i];result[i]=registered(f,(320,256),p,[208,130],scale,f'battle-{i}')
    result[13]=result[0].copy();result[24]=result[0].copy()
    return result

def faction(im,side):
    if side=='ally':return im.copy()
    table=dict(zip(COLORS,ECOLORS));out=im.copy();out.putdata([(*table[p[:3]],p[3])if p[3]else(0,0,0,0)for p in im.getdata()]);return out

def save(im,name,purpose):
    path=OUT/name;path.parent.mkdir(parents=True,exist_ok=True);im.save(path,optimize=True)
    ASSETS.append({'path':path.relative_to(ROOT).as_posix(),'purpose':purpose,'size':list(im.size),'bytes':path.stat().st_size,'sha256':digest(path),'colors':len({p[:3]for p in im.convert('RGBA').getdata()if p[3]})})
    return '../../../'+path.relative_to(ROOT).as_posix()

def projectile(side):
    # Same accepted hand-drawn wood/steel javelin; keep class22's wider native canvas.
    old=ROOT/f'knight-redraw-v3-20261021/{side}/flying-lance.png'
    im=Image.open(ROOT/'knight-redraw-v3-20261021/ally/flying-lance.png').convert('RGBA')
    out=im.copy();out.putdata([(*COLORS[material(p[:3])],p[3])if p[3]else(0,0,0,0)for p in im.getdata()]);im=faction(out,side)
    canvas=Image.new('RGBA',(320,64));canvas.alpha_composite(im,(32,0))
    return save(canvas,f'{side}/flying-lance.png','approved hand-drawn spear; class22 native80x16 canvas and40x8 anchor')

def boards(images):
    for side in ['ally','enemy']:
        for kind in ['maps','battle']:
            entries=images[side][kind]
            for light in [False,True]:
                cw,ch=(288,250)if kind=='maps'else(344,296);bg=(220,222,216)if light else(32,45,53);fg=(30,43,56)if light else(235,243,242)
                board=Image.new('RGB',(cw*3,56+ch*math.ceil(len(entries)/3)),bg);d=ImageDraw.Draw(board)
                d.text((board.width//2,25),('盟军'if side=='ally'else'敌方')+'壁垒卫士 · '+('地图'if kind=='maps'else'战斗'),anchor='mm',font=font(20),fill=fg)
                for n,(label,im)in enumerate(entries):
                    if kind=='maps':im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
                    x=n%3*cw+(cw-im.width)//2;y=56+n//3*ch;board.paste(im,(x,y),im)
                    d.text((n%3*cw+cw//2,y+ch-26),label,anchor='mt',font=font(14),fill=fg)
                save(board,f'{side}-{kind}-{"light"if light else"dark"}.png','full pose visual inspection, dark/light background')

def build(publish=False):
    base=json.loads((OUT/'baseline.json').read_text());maps=map_poses();battle=battle_poses();drafts={};review={}
    for side in ['ally','enemy']:
        name=('盟军'if side=='ally'else'敌方')+'壁垒卫士';cid=side+'-bastion-guardian';review[side]={'maps':[],'battle':[]}
        m=copy.deepcopy(base['maps']);m.update(character_id=cid,display_name=name,display_class_name='壁垒卫士',source_side=side,revision=REV,status='review_candidate',runtime_integrated=False)
        for s in m['scenarios']:
            kind=s['id'];w,h=s['output_frame_size'];atlas=Image.new('RGBA',(w*len(maps[kind]),h));records=[]
            for i,raw in sorted(maps[kind].items()):
                im=faction(raw,side);path=save(im,f'{side}/{kind}/frame-{i:03}.png','complete drawn map pose: '+kind);atlas.alpha_composite(im,(i*w,0))
                records.append({'source_index':i,'source_frame':i,'path':path,'output_path':path,'revision':REV,'size':[w,h],'bytes':ASSETS[-1]['bytes'],'sha256':ASSETS[-1]['sha256'],'art_status':'review_candidate'})
                if kind=='tactical-walk' or i<3:review[side]['maps'].append((('待机'if kind=='tactical-idle'else['向上','向上','向右','向右','向下','向下','向左','向左'][i])+f' {i}',im))
            s.update(source_side=side,character_id=cid,display_name=name,source_atlas=s['source_atlas'].replace('enemy',side),revision=REV,frame_mapping=records,output_atlas=save(atlas,f'{side}/{kind}-atlas.png','packed map poses'),output_atlas_bytes=ASSETS[-1]['bytes'],art_review_status='review_candidate',status='review_candidate',motion_review={'registration':'complete whole-pose hair/torso reference; no limb splicing or deformation','runtime_integrated':False},review_note='完整姿势绘制，固定头部参照定位；盟军柔白甲、蓝衣，敌军蓝紫；纯色头发、衣料去高光，原姿态与相位顺序、循环、节奏保留。',action_note='本轮壁垒卫士全动作重绘，待验收。')
            if kind=='tactical-walk':s['source_audit'].update(unit_evidence='../../../source-input/corrected-tactical-walk/verification.json')
        drafts[f'professions/class-22-{side}/maps/frame_mapping.json']=m
        m=copy.deepcopy(base['battle']);paths={};atlas=Image.new('RGBA',(320*len(battle),256));records=[]
        for n,(i,raw)in enumerate(sorted(battle.items())):
            im=faction(raw,side)
            shift=-64 if side=='enemy'and i in [13,24]else(-96 if side=='enemy'and i in [25,27]else 0)
            if shift:
                shifted=translate(im,[shift,0]);assert sum(p[3]>0 for p in im.getdata())==sum(p[3]>0 for p in shifted.getdata());im=shifted
            paths[str(i)]=save(im,f'{side}/battle/frame-{i:03}.png','complete drawn battle pose; native background translation retained');atlas.alpha_composite(im,(n*320,0))
            records.append({'source_frame':i,'path':paths[str(i)],'native_background_translation':[shift,0],'art_status':'review_candidate','sha256':ASSETS[-1]['sha256']})
            if i not in [13,24]:review[side]['battle'].append((f'姿势 {i}',im))
        keys=[f'original_class_22_{"enemy_"if side=="enemy"else""}normal']+[f'class_22_{side}_javelin'+suffix for suffix in ['', '_vs_heavy','_far_ally','_far_ally_vs_heavy','_far_enemy','_far_enemy_vs_heavy']]
        m.update(character_id=cid,display_name=name,display_class_name='壁垒卫士',source_side=side,source_atlas=f'../../../source-input/{"original-motion/class-22.png"if side=="ally"else"enemy-motion/class-22-enemy.png"}',revision=REV,frame_mapping=paths,records=records,canonical_frames=sorted(battle),output_atlas_frame_order=sorted(battle),variant_keys=keys,output_atlas=save(atlas,f'{side}/battle-atlas.png','all sixteen native source slots'),effect_overrides={('fdf70ce5ad8318'if side=='ally'else'native-b99a752ee6f720'):projectile(side)},palette=ALLY if side=='ally'else ENEMY,source_semantics={'0-9':'Original marching phases and sideways turn, one held lance and shield.','10':'Shield extended left, spear prepared behind shoulder.','11':'Wide planted stance and forward spear thrust.','25':'One horizontal overhead javelin.','27':'Empty fist after release.','13/24':'Native background alias of0: ally0px / enemy-64px.','25/27 registration':'Enemy background shifts-96 output pixels relative to ally; native proven atlas placement.'},batches=[{'id':'完整姿势','review':f'../../../{REV}/{side}-battle-dark.png','status':'review_candidate'}],art_provenance='Built-in ImageGen complete figure edits. Uniform whole-pose registration, deterministic matte material palette and faction variant; no limb splice or warp.',review_note='双方壁垒卫士：纯色头发、去衣料高光，柔白蓝甲／蓝紫14色；固定头部参照登记，原作各自攻击、投枪、命中时刻及收势程序完整保留。',runtime_integrated=False,status='review_candidate')
        drafts[f'professions/class-22-{side}/battle/frame_mapping.json']=m
    boards(review);write(OUT/'mapping-drafts.json',drafts)
    write(OUT/'asset-manifest.json',{'revision':REV,'status':'staged_for_visual_review','image_generation':'built-in image_gen','runtime_integrated':False,'palette':{'ally':ALLY,'enemy':ENEMY},'registration':REG,'assets':ASSETS,'body_splicing':False,'limb_warping':False,'native_timing_modified':False})
    if publish:
        for key,value in drafts.items():write(ROOT/key,value)
    print(json.dumps({'status':'published'if publish else'staged','assets':len(ASSETS),'poses':len(REG),'mappings':len(drafts)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');build(p.parse_args().publish)
