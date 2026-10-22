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
 for text in [field('地图调整'),field('AI与时机')]:
  if text and text not in notes and text!=' '.join(notes):notes.append(text)
 rec=dict(id=int(sid),code=code,name=d['name_zh'],chapter=int(d['chapter']),route=d['route'],optional=bool(d.get('optional',code.startswith('S'))),size=[int(d['map']['width']),int(d['map']['height'])],canvas=[rt['width'],rt['height']],padding=rt['padding'],image=f'images/{code}.png',thumbnail=f'thumbnails/{code}.webp',source=f'sources/{code}.json',source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),node=world['nodes'][str(int(d['node']))]['name_zh'],goal=d['goal'],conditions=field('目标／失败','目标与判定','目标与失败')or d['goal'],story=field('剧情推动','剧情与地图','剧情与缺席分支'),next=field('招募与下一步','战后与下一步','战后／下一步'),reward=field('奖励与返回'),fixed_rewards=[items[int(v)]['name_zh']for v in supply.get(sid,[])],notes=notes,initial_objectives=rt['objective_status'],deploy=d['player_positions'],deploy_by_route=d.get('player_positions_by_route',{}),boss_id=d['boss_id'],enemies=[unit(u)for u in d['enemies']],enemy_summary=dict(grouped),reinforcements=[unit(u)for u in d['reinforcements']],reinforcement_turn=int(d['reinforcement_turn']),npcs=[unit(u)for u in d['npc_units']],boats=d.get('event_boats',[]),transport_path=d.get('transport_path',[]),objects=objects,exit_marker=rt['exit_marker'],classes=rt['classes'],terrain=table,terrain_indices=indices,version=d.get('tactical_review_version',d.get('art_style_version','')),location_theme=d.get('location_theme',''))
 assert len(indices)==rec['size'][0]*rec['size'][1]
 records.append(rec);images.append({'code':code,'file':str(png.relative_to(OUT)),'size':list(im.size),'bytes':png.stat().st_size,'thumbnail_bytes':(OUT/f'thumbnails/{code}.webp').stat().st_size,'sha256':hashlib.sha256(png.read_bytes()).hexdigest()})
assert len(records)==40 and sum(not x['optional']for x in records)==31 and sum(x['optional']for x in records)==9
payload={'title':'全部战斗地图 · 场景与行动说明','date':'2026-10-22','version':re.search(r'config/version="([^"]+)"',(ACTUAL/'project.godot').read_text()).group(1),'map_revision':'0.10.3','maps':records,'chapters':[{'id':i,'count':sum(x['chapter']==i for x in records)}for i in range(1,6)],'notes':'当前关卡初始地形与配置；2026-10-22分两轮优化M11之后全部39图，M11保留；本轮新增第3至5章25图。场景由Godot后台绘制，人物以可切换标注展示。正式出阵成员随存档名册和伤情变化。'}
(OUT/'maps-data.js').write_text('window.MAP_CATALOG='+json.dumps(payload,ensure_ascii=False,separators=(',',':'))+';\n')
(OUT/'manifest.json').write_text(json.dumps({'passed':True,'count':40,'main':31,'side':9,'chapters':payload['chapters'],'images':images,'map_hashes':{m['code']:m['source_sha256']for m in records},'render':'Godot native tile and architecture renderer; no UI or character sprites','reference':'../character-expansion-20261018/index.html','palette':'chapter5 muted-v2','source_date':'2026-10-22','landscape_review':'../../actual/reports/map-polish-late-20261022/index.html'},ensure_ascii=False,indent=2)+'\n')
lines=['# 全部战斗地图 · 逐关说明','', '2026-10-22，当前40张运行地图。说明摘自 docs2/完整游戏流程.md，对照同版关卡配置与引擎地形规则；本页包含剧情及奖励信息。','']
for m in records:
 lines += [f"## {m['code']} · {m['name']}",'',f"第{m['chapter']}章 · {'支线' if m['optional'] else '主线'} · {m['size'][0]}×{m['size'][1]}格",'',f"场景：../{m['image']}",'',f"**目标与失败：**{m['conditions']}",'',f"**剧情：**{m['story']}",'',f"**战后与下一步：**{m['next']}",'']
 for note in m['notes']:lines += ['- '+note]
 lines += ['',f"**部署与兵力：**候选部署{len(m['deploy'])}格，初始敌军{len(m['enemies'])}名，剧情友军{len(m['npcs'])}名。",'']
 for obj in m['objects']:
  lines += [f"- {obj['number']}. {obj['title']}：实体位置{obj['position']}；{obj['mode']}；指定操作格{obj['fronts'] or '按站格／邻接规则'}。"]
 lines += ['',f"**固定补给：**{'、'.join(m['fixed_rewards']) or '无独立固定通关补给'}。",'',f"配置快照：{m['source'].removeprefix('sources/')}；SHA-256 {m['source_sha256']}",'']
(OUT/'sources/flow-notes.md').write_text('\n'.join(lines))
print(json.dumps({'passed':True,'maps':len(records),'main':31,'side':9,'data_bytes':(OUT/'maps-data.js').stat().st_size,'max_png':max(x['bytes']for x in images)},ensure_ascii=False))
