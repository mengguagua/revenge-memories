#!/usr/bin/env python3
"""S51 only: roofless indoor archive. Never rewrites another stage or shared atlas."""
from pathlib import Path
from collections import deque
from PIL import Image
import copy, hashlib, json, math, shutil, subprocess
R=Path(__file__).resolve().parents[1]
O=R/'reports/chapter5-spatial-20261022/library'
BASE=O.parent/'baseline'
ART=R/'assets/chapter5-spatial-20261022/library'
W,H=30,28
read=lambda p:json.loads(p.read_text())
def write(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=read(BASE/'S51.json');d=copy.deepcopy(old)
other_hashes={p.name:sha(p)for p in (R/'data/stages').glob('*.json')if p.stem!='S51'}
pack=read(R/'assets/battle_tiles/battle-tiles.json')
modules={m['name']:m for m in pack['modules']}
source=Image.open(R/'assets/battle_tiles/battle-tiles.png').convert('RGBA')
temple=Image.open(R/'assets/chapter5/temple-tiles.png').convert('RGBA')
temple_ids=read(R/'assets/chapter5/terrain.json')['materials']
cells=[];lookup={}
indoor={key:Image.open(ART/name).convert('RGBA')for key,name in [('wood','interior-parquet.png'),('stone','interior-stone.png')]}
def floor_tile(material,x,y):
 key=('generated-floor',material,x%4,y%4)
 if key not in lookup:
  lookup[key]=len(cells);cells.append(indoor[material].crop((x%4*16,y%4*16,x%4*16+16,y%4*16+16)))
 return lookup[key]
def tile(native,temple_source=False):
 key=(native,temple_source)
 if key not in lookup:
  im=temple if temple_source else source
  lookup[key]=len(cells);cells.append(im.crop((native%32*16,native//32*16,native%32*16+16,native//32*16+16)))
 return lookup[key]
def variant(x,y):return int(hashlib.sha256(f'S51:interior:{x}:{y}'.encode()).hexdigest()[:8],16)%4
g=[['#']*W for _ in range(H)];ground=[['void']*W for _ in range(H)];wallset=set();props=[];structures=[];routes=[]
def rect(x0,y0,x1,y1,logic='w',material='wood'):
 for y in range(y0,y1+1):
  for x in range(x0,x1+1):g[y][x]=logic;ground[y][x]=material;wallset.discard((x,y))
def wall(x0,y0,x1,y1):
 for y in range(y0,y1+1):
  for x in range(x0,x1+1):g[y][x]='#';ground[y][x]='wall';wallset.add((x,y))
def prop(name,x,y,blocking=True,purpose=''):
 m=modules.get(name,{'footprint':[3,3]});fw,fh=m['footprint'];coords=[[xx,yy]for yy in range(y,y+fh)for xx in range(x,x+fw)]
 assert all(0<xx<W-1 and 0<yy<H-1 for xx,yy in coords)
 if blocking:
  for xx,yy in coords:assert g[yy][xx]!='#',(name,xx,yy);g[yy][xx]='#'
 path='res://assets/chapter5-spatial-20261022/library/archive-bay.png'if name=='archive_bay'else'res://assets/battle_tiles/modules/'+name+'.png'
 props.append({'path':path,'position':[x*16,y*16]})
 structures.append({'name':name,'origin':[x,y],'footprint':[fw,fh],'cells':coords,'logic':'#'if blocking else'inherits_ground','runtime_prop':True,'purpose':purpose})
# A continuous building footprint; the whole outside ring is solid masonry.
wall(1,1,28,26);rect(3,3,26,24)
# Continuous central stone hall, never an outdoor road painted onto a void.
rect(13,3,17,24,'b','stone');rect(11,23,20,26,'b','stone');wall(11,26,20,26)
# North archive room and sealed side stores, bounded by thick partition walls.
wall(9,3,10,8);wall(20,3,21,8);wall(3,9,26,10)
rect(13,9,17,10,'b','stone')
# West reading wing: side door plus south door form a circulation loop.
wall(11,11,12,22);wall(3,21,12,22)
rect(11,14,12,15);rect(6,21,7,22)
# East wing is staggered, offering a second approach to the northern hall.
wall(18,11,26,12);wall(18,13,19,23);wall(20,22,26,23)
rect(18,16,19,17);rect(22,22,23,23)
# Real indoor stairs in the southern stairwell; keep its walkable steps intact.
prop('stairs_down',14,24,False,'南楼梯间通向下层，完整2×2下行楼梯全部可走')
# Archive desk and shelves replace the former roofed building entirely.
for x,y,purpose in [(14,3,'北原件台与上方书架'),(11,3,'北档案室西排书架'),(17,3,'北档案室东排书架'),(4,3,'封存西侧室藏书'),(23,3,'封存东侧室藏书'),(4,11,'西阅览翼北组书架与阅览桌'),(8,16,'西阅览翼南组书架与阅览桌'),(20,13,'东阅览翼北组书架与阅览桌'),(24,18,'东阅览翼南组书架与阅览桌')]:prop('archive_bay',x,y,True,purpose)
for x,y in [(11,6),(18,6),(3,18),(25,15)]:prop('ritual_lamp',x,y,True,'室内立灯，不放在门洞或通道中')
# The two existing rest tiles stay inside the southern landing.
for x,y in[(11,24),(20,24)]:g[y][x]='+';ground[y][x]='sacred'
# No actor or interaction rule is changed; only coordinates follow the rooms.
d['player_positions']=[[12,23],[13,23],[14,23],[16,23],[17,23],[18,24],[12,24],[13,24],[16,24],[17,24]]
for u,p in zip(d['enemies'],[[15,7],[8,13],[23,17],[17,18],[5,18],[15,12],[21,20]]):u['position']=p
for o in d['objects']:
 if o['id']=='old_record':o['position']=[15,5];o['approach']=[15,6]
 else:o['position']=[15,25]
d['exit']=[15,25];d['targets']=[o['position']for o in d['objects']]
# Floor and walls use original native bitmap tiles, copied into an independent compact atlas.
base=[];hwall=[[None]*W for _ in range(H)];vwall=[[None]*W for _ in range(H)]
for y in range(H):
 row=[]
 for x in range(W):
  mat=ground[y][x];v=variant(x,y)
  if mat in indoor:n=floor_tile(mat,x,y)
  else:n=tile(pack['base'][{'wall':'stone','void':'cave','sacred':'sacred'}[mat]][v])
  row.append(n)
  if(x,y)in wallset:
   if any(0<=y+dy<H and g[y+dy][x]!='#'for dy in[-1,1]):hwall[y][x]=tile(459)
   if any(0<=x+dx<W and g[y][x+dx]!='#'for dx in[-1,1]):vwall[y][x]=tile(463)
 base.append(row)
# All movement uses unchanged original tile categories.
ids={'#':196,'w':48,'b':48,'+':218}
notes=[
 '统一去顶室内：连续木地板与石质中厅由两格厚的实体墙分隔，北档案室、左右阅览翼、南楼梯间全部位于同一建筑内部；不再使用屋顶建筑、室外地坪或庭院。',
 '北档案台南面取回原件，西阅览翼经南门或东侧门换线，东翼错位门洞提供另一侧接近路线；完整书架与阅览桌均按真实3×3占地阻挡。',
 '从南楼梯平台出阵，完成取档与击败守卫后回到南端下行楼梯交接，表达撤回下层；封存旁室没有假门、新交互或额外奖励。剧情、人物和敌军数值、支线关闭时机及现有动画保持。']
routes=[{'name':'楼梯间—中厅—北档案室','waypoints':[[15,25],[15,20],[15,10],[15,6]],'width':3,'surface':'b'},
 {'name':'西阅览翼环线','waypoints':[[15,23],[7,23],[7,20],[7,14],[12,14],[15,14]],'width':2,'surface':'w'},
 {'name':'东阅览翼环线','waypoints':[[15,24],[23,24],[23,20],[23,17],[18,17],[15,17]],'width':2,'surface':'w'}]
structures.append({'name':'roofless_interior_masonry','cells':[list(p)for p in sorted(wallset)],'logic':'#','runtime_prop':False,'purpose':'连续双格厚墙与实际门洞，外侧为剖面实体背景'})
d.update(map={'width':W,'height':H,'tiles':[ids[q]for row in g for q in row]},logic_grid=[''.join(row)for row in g],visual_ground=[''.join({'void':'v','wall':'#','wood':'w','stone':'b','sacred':'+'}[m]for m in row)for row in ground],art_layers=[base,hwall,vwall],art_modules=structures,art_props=props,natural_props=[],art_atlas='res://assets/chapter5-spatial-20261022/library/terrain.png',art_columns=32,tactical_review_version='0.10.10-spatial',art_style_version='chapter5-spatial-20261022',landscape_revision='Roofless indoor library with connected reading wings and descending stairwell',tactical_routes=routes,tactical_notes=notes.copy(),visual_notes=notes.copy(),nature_layout={'biome':'rock','props':[],'excluded':[[0,0,W*16,H*16]]},surroundings='cave')
# Strict spatial and unchanged-content audit before writing runtime data.
seen={tuple(d['player_positions'][0]):0};q=deque(seen)
while q:
 x,y=q.popleft()
 for dx,dy in[(1,0),(-1,0),(0,1),(0,-1)]:
  p=x+dx,y+dy
  if 0<p[0]<W-1 and 0<p[1]<H-1 and p not in seen and g[p[1]][p[0]]!='#':seen[p]=seen[x,y]+1;q.append(p)
actors=d['player_positions']+[u['position']for u in d['enemies']+d['npc_units']+d['reinforcements']]
assert len(actors)==len(set(map(tuple,actors)))
for p in actors+[d['exit']]+[o.get('approach',o['position'])for o in d['objects']]:assert tuple(p)in seen,('unreachable',p)
for m in structures:
 if m['logic']=='#':assert all(g[y][x]=='#'for x,y in m['cells']),('split structure',m['name'])
for group in['enemies','npc_units','reinforcements']:
 assert len(d[group])==len(old[group])
 assert all({k:v for k,v in a.items()if k!='position'}=={k:v for k,v in b.items()if k!='position'}for a,b in zip(old[group],d[group]))
for a,b in zip(old['objects'],d['objects']):assert {k:v for k,v in a.items()if k not in['position','approach']}=={k:v for k,v in b.items()if k not in['position','approach']}
mutable={'map','logic_grid','art_atlas','art_layers','art_modules','art_props','natural_props','tactical_review_version','surroundings','nature_layout','player_positions','enemies','npc_units','objects','reinforcements','exit','targets','visual_notes','tactical_notes','tactical_routes','art_style_version','landscape_revision','visual_ground'}
for k,v in old.items():
 if k not in mutable:assert d[k]==v,('changed semantic',k)
assert sum(row.count('+')for row in g)==sum(row.count('+')for row in old['logic_grid'])==2
assert not any('archive.png' in p['path']for p in props)
ART.mkdir(parents=True,exist_ok=True)
shutil.copy2(R/'assets/chapter5-redesign-20261022/east/archive-bay.png',ART/'archive-bay.png')
atlas=Image.new('RGBA',(512,math.ceil(len(cells)/32)*16))
for i,im in enumerate(cells):atlas.paste(im,(i%32*16,i//32*16))
atlas.save(ART/'terrain.png');subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(ART/'terrain.png')],check=True)
write(ART/'terrain.json',{'tile_count':len(cells),'native_tile_size':16,'source_pixels_preserved':True,'purpose':'Compact independent S51 interior atlas: generated indoor parquet and honed stone, native stone wall caps/faces and sacred tiles','size':list(atlas.size),'bytes':(ART/'terrain.png').stat().st_size})
write(R/'data/stages/S51.json',d)
assert all(sha(R/'data/stages'/name)==h for name,h in other_hashes.items())
write(O/'S51-design.json',{'passed':True,'code':'S51','size':[W,H],'map_sha256':sha(R/'data/stages/S51.json'),'connected_inner_cells':len(seen),'all_anchors_inside_reachable':True,'actors_identity_order_stats_equipment_AI_preserved':True,'story_rules_timing_rewards_preserved':True,'other_stages_unchanged':len(other_hashes),'no_roofed_buildings':True,'notes':notes,'routes':routes,'objects':d['objects'],'exit':d['exit'],'deployment_before':old['player_positions'],'deployment_after':d['player_positions'],'coordinate_changes':{'enemies':[{'id':b['id'],'before':a['position'],'after':b['position']}for a,b in zip(old['enemies'],d['enemies'])]},'structures':structures,'source_story_evidence':['docs2/完整台词汇总.md S51:撤回下层、房间相连','docs2/规划索引.json S51:守书室、侧室、可选支房']})
print(json.dumps({'passed':True,'map':'S51','sha256':sha(R/'data/stages/S51.json'),'connected_cells':len(seen),'atlas_bytes':(ART/'terrain.png').stat().st_size},ensure_ascii=False))
