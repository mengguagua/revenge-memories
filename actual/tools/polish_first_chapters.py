#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reproducible campaign pacing pass. Freeze previous geometry for old saves."""
from pathlib import Path
from collections import deque
import copy
import json
import heapq

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'source/playtest-0.5.0/baseline'
OUT=ROOT/'reports/playtest-0.5.0'
BASE.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
(BASE.parent/'.gdignore').touch()

def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

def category(stage,point):
    x,y=point;w=stage['map']['width']
    return int(stage['terrain']['tile_categories'][str(stage['map']['tiles'][y*w+x])])

def neighbours(stage,point):
    for dx,dy in [(0,-1),(1,0),(0,1),(-1,0)]:
        p=point[0]+dx,point[1]+dy
        if 0<p[0]<stage['map']['width']-1 and 0<p[1]<stage['map']['height']-1 and category(stage,p) not in [5,7,12]:yield p

def distances(stage,start):
    costs={start:0};previous={};pending=[(0,start)]
    while pending:
        cost,point=heapq.heappop(pending)
        if cost!=costs[point]:continue
        for p in neighbours(stage,point):
            new=cost+(2 if category(stage,p)==1 else 1)
            if new<costs.get(p,10**8):costs[p]=new;previous[p]=point;heapq.heappush(pending,(new,p))
    return costs,previous

def crop_first(stage):
    # Preserve the existing snow valley and bridges, remove the long empty
    # southern/western approach; all art and collision coordinates move together.
    ox,oy,w,h=14,0,22,18;oldw=stage['map']['width']
    stage['map']={'width':w,'height':h,'tiles':[stage['map']['tiles'][y*oldw+x] for y in range(oy,oy+h) for x in range(ox,ox+w)]}
    stage['logic_grid']=[row[ox:ox+w] for row in stage['logic_grid'][oy:oy+h]]
    stage['art_layers']=[[row[ox:ox+w] for row in layer[oy:oy+h]] for layer in stage['art_layers']]
    for key in ['natural_props','art_props']:
        props=[]
        for raw in stage[key]:
            p=copy.deepcopy(raw);p['position']=[p['position'][0]-ox*16,p['position'][1]-oy*16]
            if -64<p['position'][0]<w*16 and -64<p['position'][1]<h*16:props.append(p)
        stage[key]=props
    stage['art_modules']=[]
    stage['nature_layout']={'biome':'snow','props':[],'excluded':[]}
    for obj in stage['objects']:
        for key in ['position','approach']:
            if key in obj:obj[key]=[obj[key][0]-ox,obj[key][1]-oy]
        for key in ['approaches','entrance_cells']:
            if key in obj:obj[key]=[[p[0]-ox,p[1]-oy] for p in obj[key]]
    stage['player_positions']=[[x,y] for y in [13,14] for x in range(6,11)]
    stage['exit']=[16,3];stage['targets']=[[16,3]]
    for i,npc in enumerate(stage['npc_units']):npc['position']=[8+i,12]
    # Gate's three other neighbours are real impassable rock, leaving the
    # captain's tile as the only entrance to the extraction square.
    gate={(15,y) for y in range(2,5)}|{(17,y) for y in range(2,5)}|{(16,2)}
    for x,y in gate:
        stage['map']['tiles'][y*w+x]=196
        row=list(stage['logic_grid'][y]);row[x]='#';stage['logic_grid'][y]=''.join(row)
        for layer in stage['art_layers']:
            if layer[y][x] is not None:layer[y][x]=None
        stage['art_layers'][0][y][x]=4+(x+y)%4
        stage['natural_props'].append({'key':'snow_boulder','position':[x*16,y*16],'flip':False})
    boss=stage['enemies'][0]
    boss.update(name_zh='追击队长',position=[16,4],level=4,hp=32,max_hp=32,strength=10,skill=6,speed=4,defence=5,item_id=2,exp_value=100,behavior='guard_exit',drop_chance=100)
    placements=[[10,11],[12,11],[14,10],[10,5],[13,5],[13,9],[15,5],[9,5],[12,5]]
    originals=stage['enemies'][1:]
    stage['enemies']=[boss]
    for i,point in enumerate(placements):
        enemy=copy.deepcopy(originals[i%len(originals)])
        enemy.update(id=f'M11_e{i+1}',position=point,item_id=0,exp_value=50,behavior='skirmish' if enemy['class_id'] in [12,13,20] else 'advance')
        enemy.pop('drop_chance',None)
        enemy['hp']=enemy['max_hp']=18 if i<3 else 20
        enemy['strength']=6 if i<3 else 7
        enemy['defence']=2 if i<3 else 3
        if i==4 and enemy['class_id'] in [12,13,20]:enemy['item_id']=63;enemy['drop_chance']=100
        stage['enemies'].append(enemy)
    for i,enemy in enumerate(stage['reinforcements']):enemy.update(position=[[14,6],[13,5]][i],exp_value=50)
    stage['escort_move']=3;stage['clear_training_exp']=60
    stage['goal']='护送两组流民抵达东北旗标出口；击败出口前的追击队长。流民任一组全灭则失败。'
    stage['before']='达恩：流民在前面。东北的旗标就是出口。／奥托：追击队长守着最后那道隘口，必须先把他打退。／胡纳普：先清桥边的追兵，别让弓手拖住他们。'
    stage['ai_and_timing']='流民每次移动3格，遇敌停步；弓手主动寻找射击位置。追击队长固守出口唯一入口。第3回合预警、第4敌回合一次增援。'
    stage['tactical_notes']=['东北旗标是流民出口；S菜单可定位出口和追击队长。','追击队长携带铁枪，数值高于普通士兵，守在唯一入口。','首战胜利追加60经验训练奖励，能正常升级并学习法术；濒死者不领取。']
    stage['river_layout']={'channel':'雪原融水','bridges':[{'id':'west_bridge','bounds':[1,9,2,12],'width':2},{'id':'east_bridge','bounds':[10,6,12,9],'width':3}],'revision':'0.5.0'}
    stage['production_anchors']={'revision':'0.5.0','deployment':stage['player_positions'],'exit':stage['exit'],'boss':boss['position'],'targets':stage['targets']}
    stage['tactical_routes']={}

def advance_formation(stage):
    start=tuple(stage['player_positions'][0]);costs,previous=distances(stage,start)
    enemy_points=[tuple(e['position']) for e in stage['enemies']]
    goals=[p for p in costs if min(abs(p[0]-e[0])+abs(p[1]-e[1]) for e in enemy_points)==9]
    if not goals:return False
    anchor=min(goals,key=lambda p:costs[p])
    if costs[anchor]<5:return False
    occupied={tuple(u['position']) for u in stage['enemies']+stage['npc_units']+stage['reinforcements']}
    occupied|={tuple(o['position']) for o in stage['objects']}
    nearby,_=distances(stage,anchor)
    valid=[p for p in nearby if p not in occupied and nearby[p]<=7 and min(abs(p[0]-e[0])+abs(p[1]-e[1]) for e in enemy_points)>=7 and p in costs]
    valid.sort(key=lambda p:(nearby[p],costs[p],p[1],p[0]))
    if len(valid)<len(stage['player_positions']):return False
    stage['player_positions']=[list(p) for p in valid[:len(stage['player_positions'])]]
    if 'production_anchors' in stage:
        stage['production_anchors']['deployment']=stage['player_positions']
        stage['production_anchors']['deploy']=stage['player_positions']
    return True

records=[]
for path in sorted((ROOT/'data/stages').glob('*.json')):
    backup=BASE/path.name
    if not backup.exists():backup.write_bytes(path.read_bytes())
    stage=json.loads(backup.read_text());old=copy.deepcopy(stage)
    compat=ROOT/'data/compat'/stage.get('tactical_review_version','0.2.0')/path.name
    if not compat.exists():write(compat,stage)
    if stage['code']=='M11':crop_first(stage)
    else:advance_formation(stage)
    for enemy in stage['enemies']+stage['reinforcements']:
        if enemy['class_id'] in [12,13,20] and enemy.get('behavior')=='guard':enemy['behavior']='skirmish'
    if stage['code'] in ['S11','S12','F22','S21','S22']:stage['escort_move']=3
    if stage['code']=='F22':
        stage['exit']=[29,16]
        stage['production_anchors']['exit']=[29,16]
        stage['goal']+='接应出口位于敌舰中段、囚舱总闸旁的旗标。'
        stage['tactical_notes'].append('登船同伴在囚舱总闸旁接应俘虏；到达接应旗标即可获救，无须绕行己船最南端。')
    if stage['code']=='S22':
        for npc in stage['npc_units']:
            npc['position']=[23,17] if npc['id']=='old_sailor' else [23,18]
        stage['tactical_notes'].append('旧船员和伤者就在藏身处旁，打开藏身处后沿北路护送至出口旗标。')
    if stage['code']=='F21':stage['clear_training_exp']=35
    if stage['code']=='F26':stage['tactical_notes'].append('清除全部沿岸敌军和增援后，居民船加速到每回合6格；交战时保持原速，遇敌仍会停船。')
    if stage['code']=='F21':
        # Keep the captain on the boarded vessel, closer to its approach.
        stage['enemies'][0]['position']=[29,13]
        stage['enemies'][0].update(name_zh='搜捕指挥官',hp=28,max_hp=28,strength=10,defence=5)
        for enemy in stage['enemies'][1:]:
            enemy.update(strength=6,hp=19,max_hp=19,defence=2)
            if enemy['id']=='F21_e8':enemy['behavior']='advance'
        stage['production_anchors']['boss']=[29,13]
        # Move an existing recovery square; the total does not increase.
        width=stage['map']['width']
        stage['map']['tiles'][4*width+27]=191
        stage['map']['tiles'][13*width+25]=218
        stage['art_layers'][0][13][25]=old['art_layers'][0][22][8]
        stage['recovery_sites']=[{'position':[25,13],'label':'船医补给点'}]
        stage['before']+='／船医：补给点就在上层跳板旁，受伤后轮换回来包扎。'
        stage['tactical_notes'].append('船医补给点位于上层跳板内侧，每回合恢复5生命；只治疗普通伤势，不能救治濒死。')
    stage['tactical_review_version']='0.5.0'
    nearest=lambda d:min(abs(p[0]-e['position'][0])+abs(p[1]-e['position'][1]) for p in d['player_positions'][:4] for e in d['enemies'])
    record={'code':stage['code'],'old_size':[old['map']['width'],old['map']['height']],'new_size':[stage['map']['width'],stage['map']['height']],'old_deployment':old['player_positions'],'deployment':stage['player_positions'],'old_first_contact_distance':nearest(old),'first_contact_distance':nearest(stage),'old_enemies':len(old['enemies']),'enemies':len(stage['enemies']),'compatibility':str(compat.relative_to(ROOT))}
    records.append(record);write(path,stage)
write(OUT/'pacing-changes.json',records)
print(json.dumps([{k:r[k] for k in ['code','old_first_contact_distance','first_contact_distance','old_enemies','enemies']} for r in records],ensure_ascii=False))
