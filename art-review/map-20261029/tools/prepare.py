"""Prepare existing production sprites for an isolated, offline MAP art review."""
import json, math, shutil, hashlib
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parents[1]
ACTUAL=ROOT/'actual'
r=json.loads((ACTUAL/'data/reviewed_animations.json').read_text())
runtime=json.loads((OUT/'sources/runtime.json').read_text())
manifest=[]

def record(path, purpose, source):
    im=Image.open(path)
    manifest.append(dict(path=str(path.relative_to(OUT)),purpose=purpose,pixels=list(im.size),bytes=path.stat().st_size,source=source))

def map_sprite(spec, name):
    source=ACTUAL/spec['path'].removeprefix('res://')
    target=OUT/'assets'/f'{name}.png'
    shutil.copy2(source,target)
    record(target,'复用现行地图人物',str(source.relative_to(ROOT)))
    return {**spec,'path':str(target.relative_to(OUT))}

def battle_sprite(key, variant, name):
    spec=r['battle'][key]
    v=r['variants'][spec['reviewed_variants'][variant]]
    poses=list(dict.fromkeys([spec['sequences']['idle'][0]]+[f['frame'] for f in v['frames']]))
    image=Image.open(ACTUAL/spec['path'].removeprefix('res://')).convert('RGBA')
    sheet=Image.new('RGBA',(160*8,144*math.ceil(len(poses)/8)))
    for i,p in enumerate(poses):
        x=(p%spec['columns'])*320;y=(p//spec['columns'])*288
        crop=image.crop((x,y,x+320,y+288)).resize((160,144),Image.Resampling.NEAREST)
        sheet.paste(crop,((i%8)*160,(i//8)*144))
    target=OUT/'assets'/f'{name}-body.png';sheet.save(target,optimize=True)
    record(target,'复用现行动作关键姿势，等比采样为预览图集',spec['path'])
    return dict(path=str(target.relative_to(OUT)),frame_size=[160,144],columns=8,idle=0,anchor=[80,128],
                contact=v['contact_tick'],frames=[dict(frame=poses.index(f['frame']),flip=f.get('flip',False)) for f in v['frames']],
                source=spec['path'],source_variant=variant,source_poses=poses)

variants=[('21_ally','original_class_21_normal'),('23_ally','original_class_21_promoted'),
          ('eileen','class_11_ally_item_23'),('eileen_promoted','class_11_ally_item_23')]
jobs=[]
for j,(key,variant) in zip(runtime['jobs'],variants):
    j['hero_sprite']=map_sprite(j['hero_sprite'],j['key']+'-map')
    j['friend_sprite']=map_sprite(j['friend_sprite'],j['key']+'-friend')
    j['enemy_sprite']=map_sprite(j['enemy_sprite'],j['key']+'-enemy')
    j['body']=battle_sprite(key,variant,j['key'])
    for kind in ['terrain']:
        p=OUT/'assets'/f"{j['key']}-{kind}.png";record(p,'后台引擎视口原尺寸地图底图','tools/capture.gd')
    j['fx']='assets/'+j['key']+'-fx.png'
    j['name']=('破晓·破阵' if j['advanced'] else '破阵') if j['hero']=='hunapu' else ('引光·焰环' if j['advanced'] else '焰环')
    j['profession']=('破晓勇士' if j['advanced'] else '战士') if j['hero']=='hunapu' else ('引光剑使' if j['advanced'] else '女魔剑士')
    j['duration']=5.8 if j['advanced'] else 5.4
    jobs.append(j)

bow=json.loads(json.dumps(jobs[1]));bow['key']='hunapu-bow';bow['bow']=True
bow['body']=battle_sprite('23_ally','class_21_ally_bow','hunapu-bow')
bow['fx']='assets/hunapu-advanced-fx.png';bow['name']='破晓·破阵';jobs.append(bow)

# Reuse the production arrow bitmap; the bow variant never emits a sword wave.
arrow_variant=r['variants'][r['battle']['23_ally']['reviewed_variants']['class_21_ally_bow']]
effects=[e for frame in arrow_variant['frames'] for e in frame.get('effects',[])]
(OUT/'sources/bow-effects.json').write_text(json.dumps(effects[:8],ensure_ascii=False,indent=2))
data=dict(version='MAP art review 2026-10-29',width=1280,height=784,jobs=jobs,
          steps=[0,2,4],advanced_steps=[0,3,6],hp_cost=[0,.25,.4],female_center_bonus=4,
          scope='独立美术设计模拟；现行 Godot 后台截图与角色素材＋新增MAP特效。非机制实装、非手机录屏。')
(OUT/'data.js').write_text('window.MAP_DATA='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n')
(OUT/'sources/asset-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print(json.dumps(dict(cases=len(jobs),images=len(manifest),max_bytes=max(x['bytes'] for x in manifest)),ensure_ascii=False))
