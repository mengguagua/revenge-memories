#!/usr/bin/env python3
"""S11 carved mine and S12 creek village; replayable from the turn baseline."""
from pathlib import Path
from collections import deque
from PIL import Image,ImageDraw
import copy,hashlib,importlib.util,json,math,random
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter1-redesign-20261022/side';BASE=O.parent/'baseline';ART=R/'assets/chapter1-redesign-20261022/side'
spec=importlib.util.spec_from_file_location('terrain_helpers',R/'tools/polish_chapter4_20261022.py');L=importlib.util.module_from_spec(spec);spec.loader.exec_module(L)
L.ART=ART;A=L.Atlas();B=L.B;IDS=B.IDS;MAT=B.MATERIAL
write=lambda p,d:(p.parent.mkdir(parents=True,exist_ok=True),p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n'))
def flood(g,start):
 w=len(g[0]);h=len(g);seen={tuple(start):0};q=deque([tuple(start)])
 while q:
  x,y=q.popleft()
  for dx,dy in [(0,1),(1,0),(0,-1),(-1,0)]:
   p=x+dx,y+dy
   if 0<=p[0]<w and 0<=p[1]<h and p not in seen and g[p[1]][p[0]]not in '#^~':seen[p]=seen[x,y]+1;q.append(p)
 return seen
def cave_wall(neighbors,v):
 key='mine-wall:'+''.join('1'if n else'0'for n in neighbors)
 if key not in A.add:
  ids=[]
  for n in range(4):
   im=A.cells[A.trans['mountain_ground']['cave']['255'][n]].copy()
   for y in range(16):
    for x in range(16):
     r,g,b,a=im.getpixel((x,y));shade=.82
     if neighbors[2]and y>=10:shade=.64 if y==10 else .56+(y-10)*.018
     if neighbors[0]and y<2:shade=.60
     if neighbors[1]and x>=13:shade=min(shade,.64)
     if neighbors[3]and x<3:shade=min(shade,.68)
     im.putpixel((x,y),(int(r*shade),int(g*shade),int(b*shade),a))
   ids.append(len(A.cells));A.cells.append(im)
  A.add[key]=ids
 return A.add[key][v]

def mine_rock_materials():
 """Preserve complete native silhouettes; neutralize only their grass fringe.
 The original outdoor assets remain untouched. Dedicated cave copies keep the
 original pixels/alpha/scale while preventing a green lawn inside the mine.
 """
 folder=ART/'mine-rims';folder.mkdir(parents=True,exist_ok=True);report=[]
 for key in ['ridge_bent','outcrop','boulder']:
  source=R/B.NATURE[key]['path'].removeprefix('res://');im=Image.open(source).convert('RGBA');alpha=im.getchannel('A').tobytes()
  for y in range(im.height):
   for x in range(im.width):
    r,g,b,a=im.getpixel((x,y))
    if not a:continue
    # Existing grey rock faces stay exact; brown-green ground tufts become
    # subdued neutral ore dust matching the surrounding cave rock material.
    if g>r*1.015 and g>b*1.10:
     grey=int((r*.32+g*.50+b*.18)*.80);im.putpixel((x,y),(grey,grey,int(grey*.94),a))
  assert im.getchannel('A').tobytes()==alpha
  path=folder/f'{key}.png';im.save(path)
  report.append({'path':str(path.relative_to(R.parent)),'source':str(source.relative_to(R.parent)),'size':list(im.size),'bytes':path.stat().st_size,'complete_source_alpha_preserved':True,'change':'Only green ground fringe neutralized; complete native rock face and original scale retained.'})
 write(O/'mine-rim-assets.json',{'passed':True,'assets':report})

def mine_rims(g,w,h):
 # Hand-placed joined lips follow hall corners and the narrow central pillar.
 # No random rock scattering in open halls and no sprite crosses a floor tile.
 groups=[('northwest_lip',[('ridge_bent',2,3),('outcrop',5,3),('ridge_bent',8,3),('outcrop',11,4)]),
         ('western_wall',[('outcrop',1,6),('outcrop',1,8),('outcrop',1,10),('boulder',1,12),('boulder',1,13)]),
         ('central_pillar',[('boulder',12,9),('boulder',13,9),('boulder',14,9),('boulder',15,9),('outcrop',10,11),('boulder',11,13),('boulder',11,14)]),
         ('northern_gallery',[('ridge_bent',13,0),('outcrop',16,0),('boulder',18,1)]),
         ('south_loading_lip',[('ridge_bent',17,16),('outcrop',20,16),('outcrop',22,16),('boulder',24,15)]),
         ('south_pillar',[('outcrop',12,18),('ridge_bent',13,20),('outcrop',16,19)])]
 props=[];notes=[]
 for name,items in groups:
  accepted=[]
  for key,x,y in items:
   sw,sh=B.NATURE[key]['size'];cells={(xx,yy)for yy in range(y,y+math.ceil(sh/16))for xx in range(x,x+math.ceil(sw/16))}
   assert all(0<=xx<w and 0<=yy<h and g[yy][xx]=='^'for xx,yy in cells),(name,key,x,y,'rock rim crossed a walkable floor')
   props.append({'path':f'res://assets/chapter1-redesign-20261022/side/mine-rims/{key}.png','position':[x*16,y*16],'purpose':name})
   accepted.append({'key':key,'origin':[x,y],'full_bitmap_footprint':[list(p)for p in sorted(cells)]})
  notes.append({'name':name,'complete_modules':accepted})
 write(O/'mine-rim-placement.json',{'passed':True,'groups':notes,'all_full_bitmap_extents_inside_existing_blocked_rock':True,'walkable_tiles_changed':False,'unit_or_object_coordinates_changed':False})
 return props

class Field:
 def __init__(self,c,w,h):
  self.c=c;self.old=json.loads((BASE/f'{c}.json').read_text());self.d=copy.deepcopy(self.old);self.w=w;self.h=h
  self.g=[list(('^'if c=='S11'else'.')*w)for _ in range(h)];self.under={};self.bridges={};self.routes=[];self.modules=[];self.props=[];self.channel=set()
 def rect(self,x0,y0,x1,y1,ch):
  for y in range(max(0,y0),min(self.h,y1+1)):
   for x in range(max(0,x0),min(self.w,x1+1)):self.g[y][x]=ch
 def poly(self,points,ch):
  im=Image.new('1',(self.w,self.h));ImageDraw.Draw(im).polygon(points,fill=1)
  for y in range(self.h):
   for x in range(self.w):
    if im.getpixel((x,y)):self.g[y][x]=ch
 def path(self,points,width=2,ch='p',name=''):
  for x,y in B.route(points):self.rect(x-(width-1)//2,y-(width-1)//2,x+width//2,y+width//2,ch)
  if name:self.routes.append({'name':name,'waypoints':points,'width':width,'surface':ch})
 def bridge(self,x0,y0,x1,y1,axis):
  self.rect(x0,y0,x1,y1,'s')
  for y in range(y0,y1+1):
   for x in range(x0,x1+1):self.bridges[x,y]=axis
 def stamp(self,name,x,y,ground=None,occupiable=False,purpose=''):
  m=B.MODULES[name];fw,fh=m['footprint'];cells=[]
  for yy in range(y,y+fh):
   for xx in range(x,x+fw):self.under[xx,yy]=ground or self.g[yy][xx];self.g[yy][xx]='h'if occupiable else'#';cells.append([xx,yy])
  self.modules.append({'name':name,'origin':[x,y],'footprint':[fw,fh],'cells':cells,'logic':'occupiable'if occupiable else'#','runtime_prop':True,'purpose':purpose})
  self.props.append({'path':m['path'],'position':[x*16,y*16]})
 def design(self):
  if self.c=='S11':
   # A continuous rock massif is excavated into three halls, with two routes
   # around its central pillar. The floor, not scattered stones, defines rooms.
   self.poly([(2,15),(4,13),(9,13),(11,15),(11,20),(8,21),(3,21),(2,19)],'.')
   self.poly([(3,6),(7,5),(11,6),(11,9),(9,11),(4,11),(3,9)],'.')
   self.poly([(12,10),(16,9),(21,10),(23,12),(22,15),(17,15),(15,17),(12,17)],'.')
   self.poly([(14,3),(18,2),(24,2),(25,4),(25,8),(23,10),(18,10),(15,8),(14,6)],'.')
   self.path([(9,16),(14,16),(14,12),(18,12),(18,6)],3,'.')
   self.path([(5,15),(5,9)],2,'.');self.path([(9,7),(16,7)],2,'.');self.path([(23,6),(23,0)],3,'.')
   self.path([(5,21),(5,16),(10,16),(14,16),(14,12),(18,12),(18,6),(23,6),(23,0)],2,'p','救援矿厅—装卸厅—矿口主巷')
   self.path([(5,16),(5,8),(9,8),(9,7),(16,7),(18,7)],1,'p','西部检修支巷绕过中央岩柱')
   self.path([(18,12),(20,12),(20,13)],1,'p','工具作业台');self.path([(20,3),(23,3)],1,'p','工具间南门')
   self.stamp('mine_adit',19,1,'.',purpose='北端工具间依托连续岩壁')
   self.stamp('grain_wagon',20,14,'.',purpose='装卸厅边缘停放运矿车')
   self.stamp('crates',21,11,'.',purpose='装卸厅侧壁物资')
   self.stamp('camp_palisade',2,12,'^',purpose='救援厅北缘支木')
   self.d['player_positions']=[[4,18],[5,18],[6,18],[7,18],[4,17],[5,19],[6,19],[7,17],[5,20],[6,20]]
   positions={'S11_boss':[23,5],'S11_e1':[17,8],'S11_e2':[20,10],'S11_e3':[14,13],'S11_e4':[8,8],'S11_e5':[22,10],'S11_e6':[22,5]}
   for u in self.d['enemies']:u['position']=positions[u['id']]
   for u,p in zip(self.d['npc_units'],[[4,19],[7,19],[3,18]]):u['position']=p
   o=self.d['objects'][0];o['position']=[20,13]
   o=self.d['objects'][1];o.update(position=[20,2],approach=[20,3],approaches=[[20,3]],entrance_cells=[[20,2]])
   self.d['exit']=[23,1];self.d['targets']=[[20,13],[18,12]]
   self.d['building_sites']=[];self.d['nature_layout']={'biome':'rock','props':[],'excluded':[[0,0,self.w*16,self.h*16]]}
   self.d['location_theme']='连续灰岩矿体、三处矿厅、主运矿巷与绕柱检修支巷'
   self.d['tactical_notes']=['连续灰岩围出南侧救援厅、西侧检修廊与东北装卸厅；两条矿巷绕过中央岩柱，空间由整片岩体构成。','宽主巷串联两名矿工、工具台和北侧矿口；较窄的西部支巷可绕至装卸厅侧面，工具箱只提供原有物品，不作为开路机关。','部队与矿工位于南侧矿厅，弓手和首领在东北远端；矿工仍按现有安全护送规则停走，两名矿工均须存活并撤离。']
  else:
   # A transverse creek divides a southern hamlet from a northern clinic village.
   self.poly([(0,0),(11,0),(13,2),(12,4),(9,5),(7,4),(3,5),(0,4)],'f')
   self.poly([(0,15),(2,14),(4,16),(3,19),(4,23),(0,23)],'f')
   self.poly([(23,15),(27,14),(27,23),(20,23),(20,20),(22,18)],'f')
   self.poly([(26,0),(27,0),(27,3),(25,2)],'^')
   self.poly([(0,7),(2,6),(3,7),(2,9),(0,9)],'^')
   self.poly([(10,22),(13,21),(15,23),(10,23)],'^')
   banks=[(10,12),(10,12),(10,12),(10,12),(10,12),(10,12),(10,12),(11,13),(11,13),(11,13),(12,14),(12,14),(12,14),(12,14),(12,14),(12,14),(12,14),(12,14),(11,13),(11,13),(10,12),(10,12),(9,11),(9,11),(9,11),(9,11),(10,12),(10,12)]
   for x,(a,b)in enumerate(banks):
    self.rect(x,a,x,b,'~');self.channel|={(x,y)for y in range(a,b+1)}
   self.path([(7,23),(7,20),(11,20),(11,18),(16,18),(16,15),(16,10),(16,8),(20,8),(20,7),(22,7),(22,5)],2,'p','南村药车道—中央宽桥—诊所院')
   self.rect(5,19,9,21,'p');self.path([(4,19),(7,19)],1);self.path([(10,20),(11,20)],1)
   self.path([(7,20),(5,20),(5,16),(5,13),(5,9),(5,7),(14,7),(14,6),(22,6)],1,'p','西侧林边备用桥与北岸支路')
   self.bridge(16,11,17,15,'v');self.bridge(5,9,5,13,'v')
   self.rect(20,5,24,7,'p');self.path([(25,6),(24,6)],1);self.path([(22,6),(25,6),(25,2)],1)
   self.stamp('fishing_cottage',3,17,'.',purpose='南村西屋围住装车院')
   self.stamp('fishing_cottage',9,18,'.',purpose='南村东屋与药车道')
   self.stamp('well',5,18,'.',purpose='装车院边的生活水井')
   self.stamp('village_clinic',21,3,'.',purpose='北村医舍，南门与药车终点对齐')
   self.stamp('fishing_cottage',25,4,'.',purpose='诊所东侧住屋')
   self.stamp('fishing_cottage',17,3,'.',purpose='诊所西侧住屋')
   self.path([(18,5),(18,6),(20,6)],1)
   self.stamp('tactical_house',10,7,'.',True,purpose='保留原有可驻留林间小屋')
   self.stamp('camp_palisade',20,1,'.',purpose='诊所菜圃北界')
   self.d['player_positions']=[[9,16],[10,16],[11,16],[12,16],[9,17],[10,17],[11,17],[12,17],[8,16],[8,17]]
   positions={'S12_boss':[24,7],'S12_e1':[16,9],'S12_e2':[20,8],'S12_e3':[13,6],'S12_e4':[7,7],'S12_e5':[23,8],'S12_e6':[21,6]}
   for u in self.d['enemies']:u['position']=positions[u['id']]
   for u,p in zip(self.d['npc_units'],[[7,20],[6,20]]):u['position']=p
   o=self.d['objects'][0];o.update(position=[22,4],approach=[22,5],approaches=[[22,5]],entrance_cells=[[22,4]])
   self.d['targets']=[[22,6],[16,16]];self.d['exit']=[25,2]
   self.d['building_sites']=[{'position':[10,7],'label':'林间小屋','occupiable':True,'avoid':20,'phase_heal':0}]
   self.d['river_layout']={'channel':[list(p)for p in sorted(self.channel)],'bridges':[{'bounds':[16,11,17,15],'axis':'v','purpose':'药车宽桥'},{'bounds':[5,9,5,13],'axis':'v','purpose':'林边备用人行桥'}]}
   self.d['nature_layout']={'biome':'forest','props':[],'excluded':[[0,0,self.w*16,self.h*16]]}
   self.d['location_theme']='横穿溪流、南村装车院、双桥分路与北岸诊所聚落'
   self.d['tactical_notes']=['溪流横向分开南侧装车村与北岸诊所，中央两格宽桥直接承接药车道；两岸均有完整桥头落脚。','西侧一格备用桥沿林缘通向北岸小屋，再绕至诊所西侧；两条路线在医舍院前会合，林带成片而非围着道路撒树。','药车从南村装车院出发，真正交付点位于诊所南门前；两侧村舍围出生活街院，居民与守军位置配合新道路重新安排。']
 def finish(self):
  g=self.g;w=self.w;h=self.h;c=self.c
  self.anchors={tuple(p)for p in self.d['player_positions']+[self.d['exit']]+self.d['targets']+[u['position']for u in self.d['enemies']+self.d['npc_units']+self.d['reinforcements']]}
  for o in self.d['objects']:self.anchors.update(tuple(p)for p in o.get('approaches',[]))
  for x,y in self.anchors:assert g[y][x]not in'#^~',(c,'blocked anchor',x,y,g[y][x])
  ground=[[self.under.get((x,y),'.')if q=='#'else'.'if q in 'fh'else q for x,q in enumerate(row)]for y,row in enumerate(g)]
  base=[]
  for y,row in enumerate(ground):
   line=[]
   for x,q in enumerate(row):
    v=B.seed(f'{c}:redesign:{x}:{y}')%4;mat='marsh'if c=='S11'and q=='.'else MAT[q];tile=B.PACK['base'][mat][v]
    if q=='p':tile=A.edge('dirt','marsh'if c=='S11'else'grass',B.mask_at(ground,x,y,lambda t:t in'ps'),v)
    if q=='^':
     if c=='S11':tile=cave_wall([0<=x+dx<w and 0<=y+dy<h and ground[y+dy][x+dx]not in'^#'for dx,dy in[(0,-1),(1,0),(0,1),(-1,0)]],v)
     else:tile=B.PACK['base']['grass'][v]
    if q=='s':
     m=sum(bit for dx,dy,bit in[(0,-1,1),(1,0,2),(0,1,4),(-1,0,8)]if 0<=x+dx<w and 0<=y+dy<h and ground[y+dy][x+dx]=='s')
     tile=A.trans['walkway'][self.bridges.get((x,y),'v')+str(m)][v]
    if q=='~':tile=A.water([MAT[ground[y+dy][x+dx]]if 0<=x+dx<w and 0<=y+dy<h else'sea'for dx,dy in[(0,-1),(1,0),(0,1),(-1,0)]],v)
    line.append(tile)
   base.append(line)
  nature=[];rng=random.Random(B.seed(c+'ch1-redesign'))
  if c=='S12':
   for ch,large,small in [('f',['pine_tall','pine_broad','pine_pair'],['pine_small_a','pine_small_b','pine_young']),('^',['peak_low','crag_tall','ridge_bent'],['boulder'])]:
    allowed={(x,y)for y,row in enumerate(g)for x,q in enumerate(row)if q==ch};taken=set()
    places=sorted(allowed,key=lambda p:(-sum((p[0]+dx,p[1]+dy)in allowed for dx in range(-1,3)for dy in range(-1,3)),p[1],p[0]))
    for x,y in places:
     if (x,y)in taken:continue
     choices=large.copy();rng.shuffle(choices)
     for key in choices:
      sw,sh=B.NATURE[key]['size'];cells={(xx,yy)for yy in range(y,y+math.ceil(sh/16))for xx in range(x,x+math.ceil(sw/16))}
      if cells<=allowed and not cells&(taken|self.anchors):nature.append({'key':key,'position':[x*16,y*16],'flip':rng.random()<.4});taken|=cells;break
    for x,y in sorted(allowed-taken):nature.append({'key':rng.choice(small),'position':[x*16,y*16],'flip':rng.random()<.4})
    if ch=='f':
     for x,y in sorted(allowed):
      if (x+y)%2 or rng.random()<.2:continue
      key=rng.choice(large[:2]);sw,sh=B.NATURE[key]['size'];px=x*16+rng.randint(-2,2);py=y*16+rng.randint(-2,2)
      cells={(xx,yy)for yy in range(py//16,math.ceil((py+sh)/16))for xx in range(px//16,math.ceil((px+sw)/16))}
      if cells<=allowed and not cells&self.anchors:nature.append({'key':key,'position':[px,py],'flip':rng.random()<.4})
  nature.sort(key=lambda p:p['position'][1]+B.NATURE[p['key']]['size'][1])
  if c=='S11':self.props.extend(mine_rims(g,w,h))
  self.d.update(map={'width':w,'height':h,'tiles':[IDS[q]for row in g for q in row]},logic_grid=[''.join(r)for r in g],visual_ground=[''.join(r)for r in ground],art_layers=[base,[[None]*w for _ in range(h)],[[None]*w for _ in range(h)]],art_modules=self.modules,art_props=self.props,natural_props=nature,art_atlas='res://assets/chapter1-redesign-20261022/side/terrain.png',art_columns=32,tactical_routes=self.routes,tactical_review_version='0.10.5-ch1',art_style_version='chapter1-redesign-20261022',landscape_revision='M41 approved composition method; chapter1 side maps')
  self.d['production_anchors']={'revision':'0.10.5-ch1','deployment':self.d['player_positions'],'deploy':self.d['player_positions'],'targets':self.d['targets'],'exit':self.d['exit']}
  self.d['visual_notes']=self.d['tactical_notes'].copy()
  self.check()
 def check(self):
  c=self.c;d=self.d;old=self.old;seen=flood(self.g,d['player_positions'][0]);assert self.anchors<=set(seen),(c,self.anchors-set(seen))
  units=[tuple(u['position'])for u in d['enemies']+d['npc_units']]+[tuple(p)for p in d['player_positions']];assert len(units)==len(set(units)),(c,'overlap')
  for group in ['enemies','npc_units','reinforcements']:
   assert len(old[group])==len(d[group]);assert all({k:v for k,v in a.items()if k!='position'}=={k:v for k,v in b.items()if k!='position'}for a,b in zip(old[group],d[group]))
  movable=['position','approach','approaches','entrance_cells']
  for a,b in zip(old['objects'],d['objects']):assert{k:v for k,v in a.items()if k not in movable}=={k:v for k,v in b.items()if k not in movable}
  for k in ['characters','terrain','goal','before','during','after','cause','absent_branch','contract','ai_and_timing','reinforcement_turn','escort_move','equipment_revision']:assert old.get(k)==d.get(k),(c,k)
  for o in d['objects']:
   at=tuple(o['position']);fronts=o.get('approaches')or[[at[0]+dx,at[1]+dy]for dx,dy in[(0,1),(1,0),(0,-1),(-1,0)]]if o.get('adjacent')else[o['position']]
   assert any(tuple(p)in seen for p in fronts),(c,'object access',o['id'])
  escorts=[]
  for u in d['npc_units']:
   if u.get('quest_kind')not in['escort','medicine']:continue
   goal=d['targets'][0]if u['quest_kind']=='medicine'else d['exit'];dist=flood(self.g,u['position']).get(tuple(goal));assert dist is not None
   mind=min(abs(u['position'][0]-e['position'][0])+abs(u['position'][1]-e['position'][1])for e in d['enemies']);assert mind>=8,(c,u['id'],'initial enemy distance',mind)
   escorts.append({'id':u['id'],'start':u['position'],'target':goal,'path_cells':dist,'nearest_initial_enemy_manhattan':mind})
  if c=='S12':
   assert all(self.g[y][x]in '~s' for x,y in self.channel),(c,'river channel covered by land')
   for br in d['river_layout']['bridges']:
    x0,y0,x1,y1=br['bounds'];assert any((x,y)in self.channel for y in range(y0,y1+1)for x in range(x0,x1+1));assert all(self.g[y0-1][x]not in'#^~'and self.g[y1+1][x]not in'#^~'for x in range(x0,x1+1))
  moved={group:[{'id':b['id'],'before':a['position'],'after':b['position']}for a,b in zip(old[group],d[group])]for group in ['enemies','npc_units','reinforcements']}
  moved['objects']=[{'id':b['id'],'before':{k:a[k]for k in movable if k in a},'after':{k:b[k]for k in movable if k in b}}for a,b in zip(old['objects'],d['objects'])]
  moved.update(deploy_before=old['player_positions'],deploy_after=d['player_positions'],exit_before=old['exit'],exit_after=d['exit'],targets_before=old['targets'],targets_after=d['targets'])
  write(O/f'{c}-geometry.json',{'passed':True,'map':c,'size':[self.w,self.h],'connected_cells':len(seen),'reachable_anchors':len(self.anchors),'notes':d['tactical_notes'],'escorts':escorts,'units_only_positions_changed':True,'story_and_rules_unchanged':True,'coordinate_changes':moved})
  write(R/f'data/stages/{c}.json',d)
if __name__=='__main__':
 mine_rock_materials()
 for c,w,h in [('S11',26,22),('S12',28,24)]:f=Field(c,w,h);f.design();f.finish()
 A.save();write(O/'asset-review.json',{'atlas':str((ART/'terrain.png').relative_to(R.parent)),'size':[512,math.ceil(len(A.cells)/32)*16],'bytes':(ART/'terrain.png').stat().st_size,'original_ids_and_pixels_preserved':A.original,'purpose':'独立原生图集追加矿壁面、岩地与溪岸过渡，不改共享图集；保留原始16像素轮廓。'})
 print('S11/S12 authored geometry and native atlas written.')
