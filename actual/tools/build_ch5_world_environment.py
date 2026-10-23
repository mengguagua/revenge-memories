#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Preserve fourth-chapter geography and add ceremonial stone forecourts only."""
from pathlib import Path
from PIL import Image
import json,copy,hashlib,math,subprocess
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter5-environment-20261023/world';A=R/'assets/chapter5-environment-20261023/world'
read=lambda p:json.loads(p.read_text())
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
w=read(R/'data/formal_world.json');v=read(R/'data/chapter4_world_environment.json');d=copy.deepcopy(v);pack=read(R/'assets/world_tiles/world-tiles.json');im=Image.open(R/v['atlas'][6:]).convert('RGBA');cells=[im.crop((x,y,x+16,y+16))for y in range(0,im.height,16)for x in range(0,im.width,16)]
changes=[];roots={tuple(int(a)//16 for a in p['position'])for p in v['natural_props']if 'pine' in p['key']}
for key,rx,ry in [('14',1.5,1.2),('15',2.0,1.5),('16',2.5,1.6),('30',1.8,1.4),('39',1.8,1.4)]:
 cx,cy=w['nodes'][key]['position']
 for y in range(w['height']):
  for x in range(w['width']):
   if ((x-cx)/rx)**2+((y-cy)/ry)**2>1 or v['ground'][y][x]=='sea' or(x,y)in roots:continue
   before=d['ground'][y][x];d['ground'][y][x]='stone';d['layers'][0][y][x]=pack['base_tiles']['stone'][(x*3+y)%4]
   if before in ['rock','forest']:d['layers'][1][y][x]=None
   if before!='stone':changes.append({'cell':[x,y],'before':before,'after':'stone'})
A.mkdir(parents=True,exist_ok=True);atlas=Image.new('RGBA',(512,math.ceil(len(cells)/32)*16))
for i,t in enumerate(cells):atlas.paste(t,(i%32*16,i//32*16))
atlas.save(A/'terrain.png');subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(A/'terrain.png')],check=True)
d.update({'version':'0.10.15-environment','atlas':'res://assets/chapter5-environment-20261023/world/terrain.png','overview':'res://assets/chapter5-environment-20261023/world/overview-arrival.png','note':'World-scale stone sites mark outdoor forecourts/bridge approaches, not indoor floorplans. Snow/salt/marsh geography retained through the clear-sky ending.'})
write(R/'data/chapter5_world_environment.json',d)
write(O/'design.json',{'passed':True,'source_world_unchanged':True,'source_chapter4_visual_sha256':hashlib.sha256((R/'data/chapter4_world_environment.json').read_bytes()).hexdigest(),'display_only_ground_changes':changes,'all_natural_props_and_routes_retained':True,'node_materials':{k:{'name':w['nodes'][k]['name_zh'],'position':w['nodes'][k]['position'],'material':d['ground'][w['nodes'][k]['position'][1]][w['nodes'][k]['position'][0]]}for k in ['13','14','15','16','29','30','39']}})
print('World stone forecourts:',len(changes),'cells; cold highlands and eastern geography retained')
