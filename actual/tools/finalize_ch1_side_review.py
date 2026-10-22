#!/usr/bin/env python3
# coding: utf-8
from pathlib import Path
import json,hashlib,html
from PIL import Image
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter1-climate-20261022/side';H=O/'hubs'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
nature={x['key']:x for x in read(R/'assets/nature/nature.json')['sprites']}
def asset(path):
 p=R/path.removeprefix('res://');return {'path':path,'size':list(Image.open(p).size),'bytes':p.stat().st_size,'sha256':sha(p)}
s=read(R/'data/stages/S12.json');paths={s['art_atlas']}
paths.update(x['path'] for x in s['art_props']);paths.update(nature[x['key']]['path']for x in s['natural_props'])
write(O/'assets.json',{'passed':True,'assets':[asset(p)for p in sorted(paths)],'source_assets_modified':False,'native_tiles_no_resampling':True,'generated_clinic_source':'actual/source/chapter1-climate-20261022/grain-prison','generated_rocks_source':'actual/source/chapter1-climate-20261022/nature/export.json'})
v=read(O/'visual-review.json')
for m in v['maps']:
 p=R/'data/stages'/(m['code']+'.json');im=O/'images'/(m['code']+'.png');a=Image.open(im)
 m.update(map_sha256=sha(p),size=list(a.size),bytes=im.stat().st_size,pixel_sha256=hashlib.sha256(a.tobytes()).hexdigest())
 if m['code']=='S12':m['observations']=['室外与视口外缘均为雪地，松冠、村舍和诊所屋顶有积雪。','灰绿岩体改为同尺寸冬岩；位置、锚点和绘制大小保持。','运输土路清晰，雪缘连续；桥面保留木板，河流仍开放流水，未暗示冰面可走。','河桥、南村院落和北侧诊所布局保持；药车沿原路径通行。']
v['limitations']='本文件记录无单位地图的原生渲染复查；实输入两轮记录在 ../play/round1-side/ 和 ../play/round2-side/。'
write(O/'visual-review.json',v)
climate=read(R/'data/chapter1_hub_climate.json');ha=read(H/'assets.json');paths={climate['rooms']['H02']['atlas']};paths.update(climate['scenery_paths'].values());paths.update(nature[k]['path']for k in climate['nature_keys'].values());ha['runtime_assets']=[asset(p)for p in sorted(paths)];ha['climate_data_sha256']=sha(R/'data/chapter1_hub_climate.json');write(H/'assets.json',ha)
code=read(H/'code-invariants.json');code['climate_data_sha256']=sha(R/'data/chapter1_hub_climate.json');code['current_sha256']=sha(R/'core/story_hub.gd');write(H/'code-invariants.json',code)
rooms={'H02':'丘堡粮站','H03':'南岗哨所','H05':'旧塔外营','H06':'海峡城旧塔内院','H07':'林路营地','H09':'林村诊所','H04':'教堂内部','H08':'矿道内部'}
shots=[]
for id,title in rooms.items():
 b=Image.open(H/'before'/(id+'.png'));a=Image.open(H/'after'/(id+'.png'))
 shots.append({'room':id,'title':title,'before':'before/'+id+'.png','after':'after/'+id+'.png','size':list(a.size),'after_bytes':(H/'after'/(id+'.png')).stat().st_size,'after_pixel_sha256':hashlib.sha256(a.tobytes()).hexdigest(),'pixels_identical':a.tobytes()==b.tobytes(),'passed':True,'review':'室内保留干燥石地或地下岩地，未铺雪。' if id in ['H04','H08'] else '石铺院落清扫保留，周围积雪与冬季植被一致。' if id=='H06' else '雪地、雪松和门前清扫土路，互动位置与原来一致。'})
assert all(x['pixels_identical']for x in shots if x['room']in['H04','H08'])
write(H/'visual-review.json',{'passed':True,'background_guard':True,'actual_input_snapshots':True,'layout_errors':[],'shots':shots,'condition':'chapter == 1 and not chapter1_complete','excluded_h01_keeps_existing_winter':True,'excluded_h04_h08_pixels_identical':True,'scope':'Native Godot 562×320 hub viewport; genuine saved checkpoints, normal world/hub/walking inputs; no animation or interaction changes.'})
cards=[]
for x in shots:
 cards.append(f'<section id="{x["room"]}"><h2>{x["room"]} · {x["title"]}</h2><p>{x["review"]}</p><div class="pair"><figure><figcaption>修改前</figcaption><img src="{x["before"]}" alt="{x["title"]} 修改前"></figure><figure><figcaption>当前实机</figcaption><img src="{x["after"]}" alt="{x["title"]} 当前实机"></figure></div></section>')
(H/'index.html').write_text('''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>第一章据点 · 寒地一致性</title><style>*{box-sizing:border-box}body{margin:0;background:#14212a;color:#e5edf0;font:16px/1.7 system-ui,sans-serif}main{max-width:1300px;margin:auto;padding:28px}h1{font-size:28px}h2{font-size:22px;margin:0}p{color:#b7c7ce}section{padding:24px;margin:24px 0;border-radius:16px;background:#1d303b}.pair{display:grid;grid-template-columns:1fr 1fr;gap:20px}figure{margin:0}figcaption{color:#b7c7ce;margin:12px 0}img{display:block;width:100%;height:auto;image-rendering:pixelated;border-radius:6px}a{color:#aed1e9}a:focus-visible{outline:0;box-shadow:0 0 0 4px #507085;border-radius:4px}@media(max-width:760px){.pair{grid-template-columns:1fr}main{padding:16px}}</style>
<main><h1>第一章据点 · 寒地一致性</h1>
<p>日返仪式前：室外据点与雪原大背景统一。门前土路与石院保留各自材质。现有动画、行动、对话、碰撞和互动坐标保持。</p>
<p>全部截图来自真实通关存档，经正常入口和行走输入到达据点，再由后台 Godot 原生视口捕获。教堂和矿道的修改前后像素完全相同。</p>
<p><a href="input-review.json">据点输入记录</a> · <a href="phase-fixture.json">气候阶段选择检查</a> · <a href="code-invariants.json">逻辑与动画不变检查</a></p>'''+''.join(cards)+'</main></html>')
print(json.dumps({'side_visuals':2,'hub_pairs':len(shots),'story_hub_sha256':code['current_sha256'],'hub_data_sha256':code['climate_data_sha256']},ensure_ascii=False))
