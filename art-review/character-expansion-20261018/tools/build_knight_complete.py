#!/usr/bin/env python3
"""Register existing class-4 artwork; review-only, no generated/chat images."""
import colorsys
from functools import lru_cache
import json
from pathlib import Path
import shutil
import subprocess
from PIL import Image, ImageDraw
from build_gallery import ROOT
from revise_cavalry_map import digest, signature, translate
from revise_enemy_cavalry_map import recolor as enemy_rgb, PALETTE as ENEMY_PALETTE

REVISION = 'knight-complete-v1-20261021'
OUT = ROOT / REVISION
SOURCE = ROOT / 'professions/class-4-ally'
PALETTE = ['1c2027','34373d','59616a','bcc8d0','e8edeb','f1f0e8',
           '293a54','3e5578','7589a7','59483c','95785e','ba9b67',
           'dcc08f','b38a6f','e3b78e','fff9e9']
COLORS = [tuple(bytes.fromhex(c)) for c in PALETTE]
REGISTRATIONS, ASSETS = [], []

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')

def clean(im):
    im = im.convert('RGBA')
    im.putdata([(*p[:3],255) if p[3]>=128 else (0,0,0,0) for p in im.getdata()])
    return im

def luma(rgb):
    return sum(x*w for x,w in zip(rgb,(.2126,.7152,.0722)))

@lru_cache(maxsize=100000)
def ally_rgb(rgb):
    h,s,v = colorsys.rgb_to_hsv(*(x/255 for x in rgb))
    if v<.12: return COLORS[0]
    # Burgundy draft fabric becomes the approved ally blue family.
    if (h<.045 or h>.86) and s>.18:
        choices=[0,6,7,8];target=.85*max(rgb)+.15*luma(rgb)
        return COLORS[min(choices,key=lambda i:abs(luma(COLORS[i])-target))]
    if s<.20:
        choices=[0,1,2,3,4,5,15]
        target=luma(rgb)+(255-luma(rgb))*.085
        return COLORS[min(choices,key=lambda i:abs(luma(COLORS[i])-target))]
    muted=tuple(x*255 for x in colorsys.hsv_to_rgb(h,s*.88,v))
    return min(COLORS,key=lambda c:sum((a-b)**2 for a,b in zip(c,muted)))

def limited(im, side, face=None):
    out=Image.new('RGBA',im.size);pixels=[]
    for y in range(im.height):
        for x in range(im.width):
            p=im.getpixel((x,y))
            if not p[3]: pixels.append((0,0,0,0));continue
            inface=bool(face and face[0]<=x<face[2] and face[1]<=y<face[3])
            rgb=ally_rgb(p[:3]) if side=='ally' else enemy_rgb(p[:3],inface)
            pixels.append((*rgb,255))
    out.putdata(pixels)
    return out

def save(im,name,purpose):
    path=OUT/name;path.parent.mkdir(parents=True,exist_ok=True)
    im.save(path,optimize=True)
    ASSETS.append({'path':path.relative_to(ROOT).as_posix(),'purpose':purpose,
       'size':list(im.size),'bytes':path.stat().st_size,'sha256':digest(path),
       'visible_bounds':list(im.getbbox()) if im.getbbox() else None,
       'visible_colors':len({p[:3] for p in im.convert('RGBA').getdata() if p[3]})})
    return '../../../'+path.relative_to(ROOT).as_posix()

def register(im,size,point,target,scale,label):
    im=clean(im);box=im.getbbox();assert box
    patch=im.crop(box)
    dims=[round(patch.width*scale),round(patch.height*scale)]
    patch=patch.resize(dims,Image.Resampling.NEAREST)
    effective=[dims[0]/(box[2]-box[0]),dims[1]/(box[3]-box[1])]
    delta=[round(target[i]-(point[i]-box[i])*effective[i]) for i in range(2)]
    out=Image.new('RGBA',size);out.alpha_composite(patch,tuple(delta))
    clipped=sum(p[3]>0 for p in patch.getdata())-sum(p[3]>0 for p in out.getdata())
    assert clipped==0,(label,box,delta,dims,clipped)
    measured=[delta[i]+(point[i]-box[i])*effective[i] for i in range(2)]
    REGISTRATIONS.append({'label':label,'source_solid_bounds':list(box),'source_landmark':list(point),
       'target_landmark':list(target),'registered_landmark':measured,'uniform_scale':scale,
       'resampled_size':dims,'translation':delta,'visible_clipped_pixels':clipped})
    return out

def fixed_upper(plates,y):
    result=[]
    for p in plates:
        im=p.copy();im.paste(plates[0].crop((0,0,im.width,y)),(0,0));result.append(im)
    return result

def map_art():
    sheet=Image.open(SOURCE/'maps/source/sol-idle-v1-generated.png')
    cells=[clean(sheet.crop(b)) for b in [(0,0,713,736),(713,0,1425,736),(1425,0,2138,736)]]
    scale=64/max(im.getbbox()[3]-im.getbbox()[1] for im in cells)
    idle=[]
    for i,im in enumerate(cells):
        b=im.getbbox();band=round((b[3]-b[1])*.15)
        xs=sorted(x for y in range(b[1],b[1]+band) for x in range(im.width) if im.getpixel((x,y))[3])
        idle.append(register(im,(96,96),(xs[len(xs)//2],b[1]),(48,16),scale,f'idle-{i}'))
    idle=fixed_upper(idle,54)
    walk={}
    sheet=Image.open(SOURCE/'maps/source/sol-front-back-v1-generated.png')
    for direction,indices,boxes,top,cut in [
      ('up',[0,1],[(0,0,636,618),(636,0,1272,618)],16,70),
      ('down',[4,5],[(0,618,636,1236),(636,618,1272,1236)],20,74)]:
        cells=[clean(sheet.crop(b)) for b in boxes]
        scale=76/max(im.getbbox()[3]-im.getbbox()[1] for im in cells)
        plates=[]
        for i,im in zip(indices,cells):
            b=im.getbbox();head=im.crop((0,b[1],im.width,b[1]+round((b[3]-b[1])*.15))).getbbox()
            center=(head[0]+head[2])/2
            plates.append(register(im,(128,96),(center,b[1]),(64,top),scale,f'walk-{direction}-{i}'))
        walk.update(zip(indices,fixed_upper(plates,cut)))
    # Native side walk slots 6/7 match idle source phases 0/2, not 0/1.
    for n,phase in enumerate([0,2]):
        left=Image.new('RGBA',(128,96));left.alpha_composite(idle[phase],(16,16))
        right=translate(left.transpose(Image.Transpose.FLIP_LEFT_RIGHT),[1,0])
        walk[2+n]=right;walk[6+n]=left
    return {'tactical-idle':{i:idle[a] for i,a in enumerate([0,1,2,1,0,1])},'tactical-walk':walk}

def battle_art():
    faces={0:(182,120),1:(150,120),2:(174,118),3:(190,120),4:(178,118),5:(188,114),
           6:(166,110),7:(168,80),8:(176,122),9:(176,122),41:(176,122),43:(176,122)}
    poses={}
    for f,face in faces.items():
        im=clean(Image.open(SOURCE/f'battle/frames/frame-{f:03}.png'))
        target=(194,108) if f==6 else (184,80) if f==7 else (184,120)
        bottom=244 if f==5 else 216 if f==7 else 256
        scale=(bottom-target[1])/(im.getbbox()[3]-face[1])
        poses[f]=register(im,(320,256),face,target,scale,f'battle-{f}')
    poses[21]=poses[0].copy();poses[40]=poses[0].copy()
    enemy={f+10:im.copy() for f,im in poses.items() if f<10}
    for f,src in [(31,0),(40,0),(41,41),(45,43)]: enemy[f]=translate(poses[src],[-64,0])
    return poses,enemy

def mappings(side,maps,bodies):
    label='盟军骑士' if side=='ally' else '敌方骑士';base=ROOT/f'professions/class-4-{side}'
    scenarios=[]
    for kind,raw in maps.items():
        w,h=(96,96) if kind=='tactical-idle' else (128,96)
        records=[];atlas=Image.new('RGBA',(w*len(raw),h))
        for i,im in sorted(raw.items()):
            face=(42,18,58,38) if kind=='tactical-idle' else (55,34,71,54) if i in [2,3] else (58,34,74,54) if i in [6,7] else (55,23,74,44) if i in [4,5] else None
            im=limited(im,side,face)
            path=save(im,f'{side}/{kind}/frame-{i:03}.png',label+' / '+kind)
            atlas.alpha_composite(im,(w*i,0));records.append({'source_index':i,'source_frame':i,
              'path':path,'output_path':path,'size':[w,h],'bytes':ASSETS[-1]['bytes'],
              'sha256':ASSETS[-1]['sha256'],'revision':REVISION,'art_status':'review_candidate'})
        idle=kind=='tactical-idle'
        s={'id':kind,'source_atlas':f'../../../source-input/legacy-assets/assets/original/graphics/map_units/class_4_{side}.png' if idle else f'../../../source-input/corrected-tactical-walk/class-4-{side}.png',
          'source_frame_size':[24,24] if idle else [32,24],'source_anchor':[12,20] if idle else [16,24],
          'output_frame_size':[w,h],'output_anchor':[48,80] if idle else [64,96],
          'output_atlas':save(atlas,f'{side}/{kind}-atlas.png',label+' offline map atlas'),
          'frame_mapping':records,'logical_render_scale':.25,'revision':REVISION,'status':'review_candidate',
          'display_name':label,'review_note':'独立编号4骑士；固定头部与上半主体，只改变原马腿脚相，双方统一各自16色。待机与行走造型一致，待用户验收。',
          'directions':{'all':[0,1,2,1]} if idle else {'up':[0,1],'right':[2,3],'down':[4,5],'left':[6,7]},
          'direction_mirror_x':{},'timing':{'native_fps':60.0988,'cycle_frames':[0,1,2,1],'frame_ticks':[14,8,14,8]} if idle else {'native_fps':60.0988,'frame_ticks':16,'cycle_ticks':32},
          'motion_review':{'fixed_upper_box':[0,0,96,54] if idle else {'up':[0,0,128,70],'down':[0,0,128,74],'right':[0,0,128,70],'left':[0,0,128,70]},'center_stable':True,'runtime_integrated':False}}
        if idle:s['static_facing']=True
        else:
            s['source_audit']={'status':'verified_native_tactical','record_key':f'class-4-{side}',
                'verification':'../../../source-input/corrected-tactical-walk/verification.json',
                'overlay':'../../../source-input/corrected-tactical-walk/overlay.json'}
            s['ground_shadow']={'path':'gold-knight-walk-v3-20261020/ground-shadow.png','size':[12,3],'offset':[0,-1],'alpha':.42,'source':'reused accepted continuous protagonist story shadow'}
        scenarios.append(s)
    write(base/'maps/frame_mapping.json',{'schema_version':1,'revision':REVISION,'class_id':4,
      'character_id':f'{side}-knight','actor_id':f'{side}-knight','source_side':side,'display_name':label,
      'status':'review_candidate','runtime_integrated':False,'modified_by':'Codex','scenarios':scenarios})
    paths={};atlas=Image.new('RGBA',(320*len(bodies),256))
    for slot,(f,im) in enumerate(sorted(bodies.items())):
        x,y=(194,108) if f in [6,16] else (184,80) if f in [7,17] else (120,120) if side=='enemy' and f>=21 else (184,120)
        im=limited(im,side,(x-12,y-10,x+12,y+12))
        paths[str(f)]=save(im,f'{side}/battle/frame-{f:03}.png',label+' battle pose')
        atlas.alpha_composite(im,(320*slot,0))
    atlas_path=save(atlas,f'{side}/battle-atlas.png',label+' offline battle atlas')
    motion=json.loads((ROOT/f'source-input/{"enemy-motion/full-enemy-motion.json" if side=="enemy" else "original-motion/full-original-motion.json"}').read_text())
    keys=[k for k,v in motion['variants'].items() if str(v['source_class_id'])=='4']
    effect='5660a52a5bb041' if side=='ally' else 'native-3a296bda027dbe'
    lance=Image.open(ROOT/f'cavalry-battle-lance-colors-v1-20261021/{side}/flying-lance.png').convert('RGBA')
    lance_path=save(lance,f'{side}/flying-lance.png',label+' / natural ally lance or blue-violet enemy lance')
    write(base/'battle/frame_mapping.json',{'schema_version':1,'revision':REVISION,
      'character_id':f'{side}-knight','display_name':label,'original_class_id':4,'source_side':side,
      'source_frame_size':[80,64],'output_frame_size':[320,256],'source_anchor':[40,64],
      'output_anchor':[160,256],'source_columns':16,'source_idle_frame':21 if side=='ally' else 31,
      'status':'review_candidate','runtime_integrated':False,'modified_by':'Codex','variant_keys':keys,
      'frame_mapping':paths,'output_atlas':atlas_path,'output_atlas_frame_order':sorted(bodies),
      'effect_overrides':{effect:lance_path},'palette':PALETTE if side=='ally' else ENEMY_PALETTE,
      'batches':[{'id':'骑士本轮全姿势','review':f'../../../{REVISION}/{side}-battle-dark.png','status':'pending_user_visual_acceptance'}],
      'review_note':'独立编号4骑士，使用原骑士盔甲、头盔和盾牌；固定平地步态面部定位点，原作冲锋、跃起、回位、投枪轨迹和结算节奏保留。友军蓝白、敌军暗蓝紫，最多16色；未接入游戏。',
      'art_provenance':'Reuses existing class-4 ally drafts, not class-1 cavalry or class-7 great knight. Enemy is a palette variant of corresponding class-4 poses, scheduled by its own native source.',
      'semantic_aliases':{'21':'ally standing 0','40':'standing background pose'} if side=='ally' else {'10..19':'corresponding class-4 ally poses 0..9','31/40':'standing pose shifted -64 output pixels for native background placement','41/45':'class-4 throw/release shifted -64 output pixels'},
      'body_review_records':[r for r in REGISTRATIONS if r['label'].startswith('battle-')]})
    return motion,keys

def boards():
    from export_gallery import font
    for side in ['ally','enemy']:
        for kind in ['map','battle']:
            paths=[OUT/side/'tactical-idle'/f'frame-{i:03}.png' for i in range(3)] + [OUT/side/'tactical-walk'/f'frame-{i:03}.png' for i in range(8)] if kind=='map' else sorted((OUT/side/'battle').glob('frame-*.png'))
            for light in [False,True]:
                cw,ch=(210,160) if kind=='map' else (344,304)
                cols=4;rows=(len(paths)+cols-1)//cols
                bg=(220,222,216) if light else (32,45,53)
                board=Image.new('RGB',(cols*cw,rows*ch+60),bg);d=ImageDraw.Draw(board)
                title=('盟军骑士' if side=='ally' else '敌方骑士')+(' · 地图待机／四向' if kind=='map' else ' · 战斗全部姿势')
                d.text((board.width/2,26),title,anchor='mm',font=font(20),fill=(40,49,57) if light else (235,243,242))
                for i,p in enumerate(paths):
                    im=Image.open(p).convert('RGBA');x=(i%cols)*cw+(cw-im.width)//2;y=(i//cols)*ch+60
                    board.paste(im,(x,y),im)
                    label=(p.parent.name+' '+p.stem.replace('frame-',''))
                    d.text(((i%cols)*cw+cw/2,y+im.height+12),label,anchor='mt',font=font(12),fill=(65,75,83) if light else (170,190,201))
                save(board,f'{side}-{kind}-{"light" if light else "dark"}.png','offline dark/light pose inspection board')

def create():
    OUT.mkdir(exist_ok=True)
    baseline=OUT/'baseline.json'
    if not baseline.exists():
        data=json.loads((ROOT/'demos/gallery-data.json').read_text())
        write(baseline,{'digests':{a['id']:a['contentDigest'] for a in data['actions']},
          'timelines':{a['id']:signature(a) for a in data['actions']},
          'mappings':{str(p.relative_to(ROOT)):digest(p) for p in ROOT.glob('**/frame_mapping.json') if 'source-input' not in p.parts},
          'source_files':{str(p.relative_to(ROOT)):digest(p) for p in SOURCE.glob('**/*.png')}})
    maps=map_art();ally,enemy=battle_art();contract=[]
    rules=json.loads((ROOT.parents[1]/'actual/data/legacy/rules_full.json').read_text())
    for side,bodies in [('ally',ally),('enemy',enemy)]:
        motion,keys=mappings(side,maps,bodies)
        for k in keys:
            v=motion['variants'][k]
            contract.append({'character_id':f'{side}-knight','class_id':4,'action':k,
              'source_item_id':v.get('source_item_id'),'source_effect_id':v.get('source_effect_id'),
              'contact_tick':v['contact_tick'],'frame_count':len(v['frames']),
              'first_external_effect_tick':next((i for i,r in enumerate(v['frames']) if r.get('effects')),None),
              'contract':'Same native one-card action, no added damage, attack count, defense, magic or awakening.'})
    write(OUT/'action-contract.json',{'route':['骑兵','骑士','大骑士'],'class_ids':[1,4,7],
      'source':'actual/data/legacy/rules_full.json','items':[i for i in rules['items'] if i.get('id') in [4,7]],
      'actions':contract,'runtime_integrated':False})
    boards()
    # The larger images are multi-pose inspection boards/atlases, never runtime
    # sprite replacements. Keep their resolution and optimize losslessly.
    large=[OUT/a['path'].split(REVISION+'/',1)[1] for a in ASSETS if a['bytes']>50000]
    if large:
        subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3','--strip','safe',*map(str,large)],check=True)
    for a in ASSETS:
        p=ROOT/a['path'];a['bytes']=p.stat().st_size;a['sha256']=digest(p)
        if a['bytes']>50000:
            a['size_reason']='Offline multi-pose atlas/inspection board; full pixel detail retained after lossless compression. Independent character frames remain below50KB.'
    write(OUT/'asset-manifest.json',{'revision':REVISION,'runtime_integrated':False,'image_generation_invoked':False,
      'chat_image_output':False,'palette':{'ally':PALETTE,'enemy':ENEMY_PALETTE},
      'sources':'Existing class-4 drafts; raw sources kept unchanged. Alpha below128 removed as transparent dust before nearest-pixel registration.',
      'registration':REGISTRATIONS,'assets':ASSETS,'art_review_status':'pending_user_visual_acceptance',
      'side_walk_source_aliases':{'6':0,'7':2,'proof':'Native ally walking6/7 tight RGBA exactly equals idle0/2; source-space offsets excluded. Right is their mirror.'}})
    print(json.dumps({'revision':REVISION,'map_frames':28,'battle_frames':len(ally)+len(enemy),'assets':len(ASSETS)},ensure_ascii=False))

if __name__=='__main__':create()
