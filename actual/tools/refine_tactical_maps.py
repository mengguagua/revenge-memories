# -*- coding: utf-8 -*-
"""Idempotent tactical review patch, preserving original story anchors and stats.
The frozen 0.2.0 inputs live under source/tactical-review; normal resource
builders may be run first, then this patch applied to restore reviewed layouts.
"""
from pathlib import Path
from collections import deque
import json, math, copy
R=Path(__file__).resolve().parents[1]
OUT=R/'reports/review-0.2.1';BACK=R/'source/tactical-review'
OUT.mkdir(parents=True,exist_ok=True);BACK.mkdir(parents=True,exist_ok=True)
(BACK/'.gdignore').touch()
PACK=json.loads((R/'assets/battle_tiles/battle-tiles.json').read_text())
MOD={m['name']:m for m in PACK['modules']}
NATURE={m['key']:m for m in json.loads((R/'assets/nature/nature.json').read_text())['sprites']}
IDS={'.':48,'f':172,'^':94,'d':242,'~':96,'#':196,'=':208,'s':191,'b':66,'+':218}
SOLID={'grain_sacks','crates','grain_wagon','medicine_wagon','brazier','lit_brazier','boulders'}
NOTES={
'M11':['雪林回避+40；骑兵穿林更慢，石路适合追赶和护送。'],
'M12':['粮仓外墙可护住侧翼。先拦焚毁兵，再集中兵力进入前庭。'],
'M13':['南院两处缺口可守，东侧外廊可绕到北院。不要把获释劳工的出口堵住。'],
'M14':['沿中路推进较快；林地可掩护远程部队，左右目标可分队控制。'],
'M15':['中路缺口通往指挥所，东西外廊可接近两处劳工区。骑兵可先占北门，堵住科兰退路；突击前可在整备中装备已获得的钢剑、钢枪。'],
'S11':['矿道狭窄，近战守住拐口，弓手在后支援；矿工等待前路安全后撤离。'],
'S12':['药车沿路前进。骑兵走外侧主路，步兵与法师可借林地掩护。'],
'F21':['上下两条跳板均可登舰。近战守桥口，法师在后支援，也可由另一条跳板包抄。'],
'F22':['囚舱总闸控制两处出口；备用跳板是另一条进攻路线。先清理出口附近守军再放人。'],
'F23':['林地回避+40，沙地减慢地面部队。守住营地路口，远程优先压制飞行敌人。'],
'F24':['重装守灯前的石路，远程在后压制夺灯兵；东岸飞兵可能绕过正面防线。'],
'F25':['仓库间隙可守，西侧装卸道与东侧外廊可分路包抄。箱车会阻挡地面部队。'],
'F26':['石堤与木架形成两条连接路线。部队走陆路清岸，居民船沿平行海路前进。'],
'S21':['两条跳板都能交战；飞行魔物可绕开桥口，伤者后方仍需有人保护。'],
'S22':['岩脊把洞室分成两路，在窄口挡住魔物，另一队可绕过岩脊接近遗物与藏身处。']}
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def footprint(m):
 x,y=m['origin'];w,h=m['footprint'];return {(xx,yy) for yy in range(y,y+h) for xx in range(x,x+w)}
def connectivity(d,grid):
 w=d['map']['width'];h=d['map']['height'];opened={tuple(p) for o in d['objects'] for p in o.get('opens',[o['position']] if o['kind'] in ['door','rescue'] else [])}
 start=tuple(d['player_positions'][0]);q=deque([start]);seen={start}
 while q:
  x,y=q.popleft()
  for dx,dy in [(0,1),(1,0),(0,-1),(-1,0)]:
   p=x+dx,y+dy
   if 0<p[0]<w-1 and 0<p[1]<h-1 and p not in seen and (grid[p[1]][p[0]] not in '#^~' or p in opened):seen.add(p);q.append(p)
 anchors=d['player_positions']+[d['exit']]+[u['position'] for u in d['enemies']+d['npc_units']+d.get('reinforcements',[])]
 missing=[p for p in anchors if tuple(p) not in seen]
 adjacent=[o['id'] for o in d['objects'] if not any((o['position'][0]+dx,o['position'][1]+dy) in seen for dx,dy in [(0,1),(1,0),(0,-1),(-1,0)])]
 return seen,missing,adjacent
report={}
for p in sorted((R/'data/stages').glob('*.json')):
 if p.stem not in NOTES:continue
 backup=BACK/p.name
 if not backup.exists():backup.write_bytes(p.read_bytes())
 d=json.loads(backup.read_text());g=[list(row) for row in d['logic_grid']];w=d['map']['width'];h=d['map']['height']
 changes=[];blocked={tuple(q) for q in d['player_positions']+[d['exit']]+[u['position'] for u in d['enemies']+d['npc_units']+d.get('reinforcements',[])]}
 for o in d['objects']:
  x,y=o['position'];blocked.add((x,y))
  # Keep the front step for all current production-card interactions.
  if y+1<h:blocked.add((x,y+1))
 for m in d['art_modules']:
  if m['name'] not in SOLID or m.get('logic')=='#':continue
  cells=footprint(m)
  if cells&blocked:
   changes.append({'kind':'retained interaction approach','module':m['name'],'cells':sorted(cells&blocked)});continue
  for x,y in cells:g[y][x]='#'
  m['logic']='#';changes.append({'kind':'solid prop collision','module':m['name'],'cells':sorted(cells)})
 props=d.setdefault('art_props',[])
 def stamp(name,at,purpose):
  m=MOD[name];mw,mh=m['footprint'];x,y=at;cells={(xx,yy) for yy in range(y,y+mh) for xx in range(x,x+mw)}
  assert not cells&blocked,(d['code'],name,'production anchor overlap',cells&blocked)
  assert all(0<xx<w-1 and 0<yy<h-1 and g[yy][xx] not in '~^' for xx,yy in cells)
  for xx,yy in cells:g[yy][xx]='#'
  props.append({'path':'res://assets/battle_tiles/modules/'+name+'.png','position':[x*16,y*16]})
  d['art_modules'].append({'name':name,'origin':at,'footprint':[mw,mh],'logic':'#','cells':[list(q) for q in sorted(cells)],'runtime_prop':True,'purpose':purpose})
  changes.append({'kind':'tactical structure','module':name,'position':at,'purpose':purpose})
 if d['code']=='M13':
  # An earth exercise yard and stone corridors make defensible floor distinct
  # from the exposed assembly ground, using unchanged original avoidance.
  for y in range(9,20):
   for x in range(3,25):
    if g[y][x]!='=' or (x,y) in blocked:continue
    corridor=(6<=x<=8) or (13<=x<=15) or y in [9,13]
    if not corridor:
     g[y][x]='.';d['art_layers'][0][y][x]=PACK['base']['dirt'][(x*17+y*7)%4]
  for at in [[3,12],[9,12],[15,12]]:stamp('north_wall',at,'Two two-cell entrances and an eastern bypass')
  stamp('barracks',[22,11],'Eastern barracks split outer passage without closing it')
 if d['code']=='M15':
  for at in [[8,15],[15,15]]:stamp('north_wall',at,'Main three-cell assault gate stays aligned with shortest northward route')
  stamp('barracks',[4,12],'Western inner court cover with a surrounding flank route')
  stamp('barracks',[24,10],'Eastern quarter leaves prisoner approaches and north exit accessible')
 if d['code']=='F25':
  stamp('grain_store',[15,7],'Warehouse and existing cargo leave a one-cell defensible passage at x18')
  stamp('barracks',[24,11],'Eastern side road bypasses warehouse toward the pilot prison')
  stamp('crates',[18,14],'Cargo breaks up the parade ground without blocking the objective')
  stamp('grain_sacks',[23,14],'Prison-side cover offers a second approach')
 if d['code']=='M12':
  x,y=15,12;cells={(xx,yy) for yy in range(y,y+2) for xx in range(x,x+2)}
  if not cells&blocked and all(g[yy][xx]=='.' for xx,yy in cells):
   for xx,yy in cells:g[yy][xx]='f'
   d.setdefault('natural_props',[]).append({'key':'pine_broad','position':[x*16,y*16],'flip':False})
   changes.append({'kind':'forest cover','position':[x,y],'footprint':[2,2]})
 if d['code']=='S22':
  # Extend the existing central rib with an intact 32x24 outcrop. The two
  # sides remain connected at both ends, so this is a flank choice, not a maze.
  cells={(x,y) for y in range(8,10) for x in range(10,12)}
  assert not cells&blocked
  for x,y in cells:
   g[y][x]='^';d['art_layers'][0][y][x]=PACK['base']['rock'][(x+y)%4]
  d.setdefault('natural_props',[]).append({'key':'outcrop','position':[160,128],'flip':False})
  changes.append({'kind':'intact cave rib','position':[10,8],'footprint':[2,2]})
 d['logic_grid']=[''.join(row) for row in g];d['map']['tiles']=[IDS[ch] for row in g for ch in row]
 d['tactical_notes']=NOTES[d['code']];d['tactical_review_version']='0.2.1'
 seen,missing,adjacent=connectivity(d,g)
 assert not missing,(d['code'],'disconnected anchors',missing)
 assert not adjacent,(d['code'],'unapproachable interactions',adjacent)
 # Campaign identities, stats, enemy numbers, deployments and goals are exact.
 old=json.loads(backup.read_text())
 for field in ['enemies','npc_units','reinforcements','player_positions','objects','boss_id','exit','goal']:
  assert d[field]==old[field],(d['code'],field)
 write(p,d)
 report[d['code']]={'changes':changes,'connected_ground_cells':len(seen),'all_anchors_connected':True,'all_objects_approachable':True,'stats_enemies_objectives_unchanged':True}
write(OUT/'map-refinements.json',report)
print(json.dumps({k:len(v['changes']) for k,v in report.items()},indent=2))
