#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Assemble the forty-map review from current runtime data and guarded Godot scenery captures."""
from pathlib import Path
from collections import Counter
from datetime import datetime
from PIL import Image
import json,re,hashlib,shutil,subprocess,zipfile
ROOT=Path(__file__).resolve().parents[3];ACTUAL=ROOT/'actual';OUT=Path(__file__).resolve().parents[1]
def load(p):return json.loads(p.read_text())
def plain(text):
 text=re.sub(r'\[([^\]]+)\]\([^)]*\)',r'\1',text).replace('`','').replace('**','')
 for key,value in {'friendly_ship':'己方船体','prison_door':'囚舱门','myth_box':'记录箱','targets[0]':'诊所目标','clear_M51':'王都胜利','east_network_ready':'地方循环已接手','west_palace_gate':'西门已开启','east_palace_gate':'东门已开启','final_access':'神座通路已开启'}.items():text=text.replace(key,value)
 return text.strip()
flow=(ROOT/'docs2/完整游戏流程.md').read_text();heads=list(re.finditer(r'^#### ([MFJS]\d{2}) .*$',flow,re.M));sections={}
for i,m in enumerate(heads):
 end=heads[i+1].start() if i+1<len(heads) else flow.find('\n## 七、',m.end())
 sections[m.group(1)]=dict(re.findall(r'\*\*([^*\n]+?)：\*\*([^\n]+)',flow[m.end():end]))
runtime=load(OUT/'runtime-info.json');assert runtime['passed'] and len(runtime['maps'])==40
runtime={m['code']:m for m in runtime['maps']};campaign=load(ACTUAL/'data/campaign.json');world=load(ACTUAL/'data/formal_world.json');items=load(ACTUAL/'data/legacy/rules_full.json')['items']+load(ACTUAL/'data/equipment_progression.json')['items'];supply=load(ACTUAL/'data/equipment_progression.json')['clear_rewards']
(OUT/'thumbnails').mkdir(exist_ok=True);(OUT/'sources').mkdir(exist_ok=True)
material_review={m['code']:m for m in load(ACTUAL/'reports/chapter5-spatial-20261022/material-summary.json')['maps']}
# Current first-chapter seasonal review supersedes only these five outdoor maps.
climate_review={
 'M12':'日返前的雪原粮道：积雪、雪松、冬岩与雪顶建筑统一；主运粮道与卸粮坪为清扫裸土，建筑内石地保留。',
 'M13':'寒地押送营：雪地与连贯裸土车场分开，冬季屋顶、围墙和植被一致；牢房内石地、开门后门槛、木桥与开放流水保持各自材质。',
 'M14':'旧塔外营覆盖积雪，勤务路、营帐前场与粮仓院为压实裸土；寝帐、冬季营房和雪松映衬，控制口与部署不变。',
 'M15':'冬季海崖旧堡：积雪、冬岩、雪顶建筑与远景一致；工棚和石地牢房不铺雪，栈桥保留木材，海面保持水面。',
 'S12':'雪林诊所与村道统一寒地气候：松冠、岩脚、屋顶积雪，药车道为清扫土路；两座木桥和开放流水清楚区分。'}
for code,conclusion in climate_review.items():material_review[code]=dict(material_review[code],conclusion=conclusion)
# Current chapter-two environment review only supersedes these six changed maps.
chapter2_environment_review={
 'F21':'海上双舰保持露天风化木甲板和木跳板；船医恢复格改为木板，船员舱采用同占地低矮木船舱与圆舷窗，不在船上摆陆地尖顶小屋。',
 'F22':'押送舰囚舱采用较平整的室内横木板，与露天旧甲板清楚区分；两扇南门打开后仍是同一木门槛。船医区为木板，低矮木舱、总闸和备用跳板关系保持。',
 'F23':'礁岛沙滩、草地与木码头用途正确，保留原地面；按长时间黑昼初现加入轻冷暗环境，与世界图及战后据点衔接。',
 'F25':'军港剖面牢室六格与门槛换室内磨损石板，开门后保持同一石材；外部土路、石院和风化木码头分开。军港延续黑昼冷暗环境，与H26一致。',
 'S21':'漂泊渔船保留木甲板、双跳板和真实沙岸停泊口；低矮木船舱替代陆地尖顶小屋，船舱、甲板和岸地材质用途清楚。',
 'S22':'碎石海洞主巷改为裸露灰岩，湿沉积地、岩壁和潮水保持；去除地下的户外黄土路观感，不向洞内引入草地或沙岸铺装。'}
for code,conclusion in chapter2_environment_review.items():material_review[code]=dict(material_review[code],conclusion=conclusion)

# Current third-chapter material conclusions supersede the earlier all-map audit.
for reviewed in load(ACTUAL/'reports/chapter3-environment-20261023/material-review.json')['maps']:
 material_review[reviewed['code']]=dict(material_review[reviewed['code']],conclusion=reviewed['conclusion'])

# Fourth-chapter environment conclusions supersede the earlier material audit.
for reviewed in load(ACTUAL/'reports/chapter4-environment-20261023/material-review.json')['maps']:
 material_review[reviewed['code']]=dict(material_review[reviewed['code']],conclusion=reviewed['conclusion'])


records=[];images=[];errors=[]
for sid,meta in sorted(campaign['stages'].items(),key=lambda p:int(p[0])):
 source=ACTUAL/meta['path'].removeprefix('res://');d=load(source);code=d['code'];rt=runtime[code];fields=sections[code]
 def field(*names):return next((plain(fields[k])for k in names if k in fields),'')
 png=OUT/f'images/{code}.png';im=Image.open(png).convert('RGBA');assert im.size==(rt['width'],rt['height'])
 raw=im.tobytes();subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(png)],check=True);assert Image.open(png).convert('RGBA').tobytes()==raw
 thumb=im.copy();thumb.thumbnail((360,280),Image.Resampling.NEAREST);thumb.save(OUT/f'thumbnails/{code}.webp',lossless=True,method=6)
 shutil.copy2(source,OUT/f'sources/{code}.json')
 table=[];indices=[];lookup={}
 for cell in rt['cells']:
  key=tuple(cell[k]for k in ['name','category','avoid','foot','horse','fly'])
  if key not in lookup:lookup[key]=len(table);table.append(cell)
  indices.append(lookup[key])
 objects=[]
 for index,o in enumerate(d['objects']):
  fronts=o.get('approaches',[o['approach']] if 'approach'in o else [])
  objects.append(dict(o,number=index+1,fronts=fronts,title=o.get('name_zh',o['label']),mode='站位守护' if code=='F41' else '到指定格确认' if fronts else '邻接或站格确认' if o.get('adjacent',False) else '站在目标格确认',reward_name=items[int(o['reward_item'])]['name_zh'] if o.get('reward_item',0) else ''))
 def unit(u):return {k:u[k] for k in ['id','name_zh','class_id','level','hp','max_hp','position','quest_kind','locked','event_object','temporary','controllable','behavior','advance_after'] if k in u}
 grouped=Counter(rt['classes'][str(int(u['class_id']))] for u in d['enemies'])
 notes=[plain(x)for x in d.get('tactical_notes',d.get('visual_notes',[]))]
 for note in d.get('climate_notes',[]):
  if plain(note) not in notes:notes.append(plain(note))
 notes.append('地面材质复查：'+material_review[code]['conclusion'])
 for text in [field('地图调整'),field('AI与时机')]:
  if text and text not in notes and text!=' '.join(notes):notes.append(text)
 rec=dict(id=int(sid),code=code,name=d['name_zh'],chapter=int(d['chapter']),route=d['route'],optional=bool(d.get('optional',code.startswith('S'))),size=[int(d['map']['width']),int(d['map']['height'])],canvas=[rt['width'],rt['height']],padding=rt['padding'],image=f'images/{code}.png',thumbnail=f'thumbnails/{code}.webp',source=f'sources/{code}.json',source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),node=world['nodes'][str(int(d['node']))]['name_zh'],goal=d['goal'],conditions=field('目标／失败','目标与判定','目标与失败')or d['goal'],story=field('剧情推动','剧情与地图','剧情与缺席分支'),next=field('招募与下一步','战后与下一步','战后／下一步'),reward=field('奖励与返回'),fixed_rewards=[items[int(v)]['name_zh']for v in supply.get(sid,[])],notes=notes,initial_objectives=rt['objective_status'],deploy=d['player_positions'],deploy_by_route=d.get('player_positions_by_route',{}),boss_id=d['boss_id'],enemies=[unit(u)for u in d['enemies']],enemy_summary=dict(grouped),reinforcements=[unit(u)for u in d['reinforcements']],reinforcement_turn=int(d['reinforcement_turn']),npcs=[unit(u)for u in d['npc_units']],boats=d.get('event_boats',[]),transport_path=d.get('transport_path',[]),objects=objects,exit_marker=rt['exit_marker'],classes=rt['classes'],terrain=table,terrain_indices=indices,version=d.get('tactical_review_version',d.get('art_style_version','')),location_theme=d.get('location_theme',''))
 rec['material_revision']=d.get('material_review_version',d.get('tactical_review_version',''));rec['material_review']=material_review[code]['conclusion']
 assert len(indices)==rec['size'][0]*rec['size'][1]
 records.append(rec);images.append({'code':code,'file':str(png.relative_to(OUT)),'size':list(im.size),'bytes':png.stat().st_size,'thumbnail_bytes':(OUT/f'thumbnails/{code}.webp').stat().st_size,'sha256':hashlib.sha256(png.read_bytes()).hexdigest()})
assert len(records)==40 and sum(not x['optional']for x in records)==31 and sum(x['optional']for x in records)==9
payload={'title':'全部战斗地图 · 场景与行动说明','date':'2026-10-23','version':re.search(r'config/version="([^"]+)"',(ACTUAL/'project.godot').read_text()).group(1),'map_revision':'0.10.14-environment','maps':records,'chapters':[{'id':i,'count':sum(x['chapter']==i for x in records)}for i in range(1,6)],'notes':'当前关卡初始地形与配置；2026-10-22分两轮优化M11之后全部39图，M11保留；第3至5章25图已调整，M41重设计样板已确认；第一章M12—M15与S11/S12现按该方法重新组织地形、建筑、部署和任务点，M11保持；第二章F21—F26与S21/S22现也完成舰船、海岸、灯庭、军港和水道重设计；第三章M31—M33、F31—F33及S31/S32现完成街区救援、军需截运、沿海石堡、码头盐路、提炼水庭与双院支线重设计。第四章现保留M41样板，并完成其余九图的铁骑营地、日塔、王都护院、沙城、观测台、沼泽与祭所重设计。第五章七图现完成内廷双病房、三段长桥、地下修复院、日宫水庭、旧书库、两军前庭和神座重设计。2026-10-22追加空间与材质复查：旧书库与日宫下层统一室内表达，病房、桥头和阶台修正；全部40图逐张核对贴图用途，另修正前四章9图的地面材质，布局与规则保持。2026-10-23第一章寒地一致性修订：M12—M15与S12改为雪地、冬季屋顶和雪松，清扫土路、室内石地、木桥与开放水面保持各自材质；M11原图和S11地下矿道保持。世界按故事时间选景：第一章仪式前和第二章回到半年前的前段保留冬景；押送舰战后确认继续航行后，西大陆日返转暖、东群岛进入黑昼；第一章室外据点仍按自身剧情阶段显示冬景。2026-10-23第二章环境一致性复查：船战木舱与甲板、囚舱和军港牢室门槛、海洞裸岩材质已修正；礁岛与军港延续剧情黑昼，世界全图和据点同步。F24航灯防卫与F26古道材质经检查保留。2026-10-23第三章环境一致性复查：西大陆日返自然光与东线盐原黑昼衔接，盐原营地大地图补盐地；六图修正露天石堡院、无雪村舍、船舱、工房去顶室内及门槛与冷暗环境；M31/M32原图保留，九据点环境同步。2026-10-23第四章环境一致性复查：寒区雪地与日照交通带、大地图沙地／盐原／湿沼／祭所石地对应；十图中九图统一冬季外观、室外石铺和黑昼，M42原样保留；日塔控制室与东楼为真正室内石地，十个战后据点和共享营站同步。祭所局部试验及两岸验证后，按剧情旗标恢复祭所和邻近湿地亮光。场景由Godot后台绘制，人物以可切换标注展示。正式出阵成员随存档名册和伤情变化。'}
(OUT/'maps-data.js').write_text('window.MAP_CATALOG='+json.dumps(payload,ensure_ascii=False,separators=(',',':'))+';\n')
(OUT/'manifest.json').write_text(json.dumps({'passed':True,'count':40,'main':31,'side':9,'chapters':payload['chapters'],'images':images,'map_hashes':{m['code']:m['source_sha256']for m in records},'render':'Godot native tile and architecture renderer; no UI or character sprites','reference':'../character-expansion-20261018/index.html','palette':'chapter5 muted-v2','source_date':'2026-10-23','landscape_review':'../../actual/reports/map-polish-late-20261022/index.html','climate_review':'../../actual/reports/chapter1-climate-20261022/index.html','environment_review':'../../actual/reports/chapter4-environment-20261023/index.html','chapter3_environment_review':'../../actual/reports/chapter3-environment-20261023/index.html','chapter2_environment_review':'../../actual/reports/chapter2-environment-20261023/index.html','map_revision':payload['map_revision']},ensure_ascii=False,indent=2)+'\n')
lines=['# 全部战斗地图 · 逐关说明','', '2026-10-23，当前40张运行地图；本次第四章环境修订0.10.14；第一至第三章环境修订保留。说明摘自 docs2/完整游戏流程.md，对照同版关卡配置与引擎地形规则；本页包含剧情及奖励信息。','']
for m in records:
 lines += [f"## {m['code']} · {m['name']}",'',f"第{m['chapter']}章 · {'支线' if m['optional'] else '主线'} · {m['size'][0]}×{m['size'][1]}格",'',f"场景：../{m['image']}",'',f"**目标与失败：**{m['conditions']}",'',f"**剧情：**{m['story']}",'',f"**战后与下一步：**{m['next']}",'']
 for note in m['notes']:lines += ['- '+note]
 lines += ['',f"**部署与兵力：**候选部署{len(m['deploy'])}格，初始敌军{len(m['enemies'])}名，剧情友军{len(m['npcs'])}名。",'']
 for obj in m['objects']:
  lines += [f"- {obj['number']}. {obj['title']}：实体位置{obj['position']}；{obj['mode']}；指定操作格{obj['fronts'] or '按站格／邻接规则'}。"]
 lines += ['',f"**固定补给：**{'、'.join(m['fixed_rewards']) or '无独立固定通关补给'}。",'',f"配置快照：{m['source'].removeprefix('sources/')}；SHA-256 {m['source_sha256']}",'']
(OUT/'sources/flow-notes.md').write_text('\n'.join(lines))
print(json.dumps({'passed':True,'maps':len(records),'main':31,'side':9,'data_bytes':(OUT/'maps-data.js').stat().st_size,'max_png':max(x['bytes']for x in images)},ensure_ascii=False))
