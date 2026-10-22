#!/usr/bin/env python3
"""Fourth-chapter eastern spatial design; actors and objective rules stay frozen."""
from pathlib import Path
from collections import deque
import copy,hashlib,importlib.util,json,math,random
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter4-redesign-20261022/east';BASE=O.parent/'baseline';ART=R/'assets/chapter4-redesign-20261022/east'
spec=importlib.util.spec_from_file_location('ch4_native_helpers',R/'tools/redesign_ch3_east.py');N=importlib.util.module_from_spec(spec);spec.loader.exec_module(N)
N.O=O;N.BASE=BASE;N.ART=ART;N.L.ART=ART;N.A=N.L.Atlas();A=N.A;B=N.B;IDS=N.IDS;MAT={**N.MAT,'u':'cobble'}
write=N.write
# Bare native rock avoids the older grass-backed mountain-ground stamp.
B.PACK['base']['bare_rock']=B.PACK['base']['cave']
# Reuse native 16px cobbles with a restrained darker weathering treatment.
# The original material and all earlier chapters remain untouched.
WEATHERED=[]
for source in B.PACK['base']['cobble']:
 tile=A.cells[source].copy();tile.putdata([(int(r*.90),int(g*.90),int(b*.90),a)for r,g,b,a in tile.getdata()]);WEATHERED.append(len(A.cells));A.cells.append(tile)
ART.mkdir(parents=True,exist_ok=True)
for i,source in enumerate(B.PACK['base']['sand']):A.cells[source].save(ART/f'sand-border-{i}.png')
class Field(N.Field):
 def object(self,id,position,approach=None):
  o=next(o for o in self.d['objects']if o['id']==id);o['position']=position
  if approach is not None:o['approach']=approach
 def design(self):
  d=self.d
  if self.c=='F41':
   self.poly([(0,0),(9,0),(8,2),(5,3),(4,6),(2,8),(0,8)],'^')
   self.poly([(0,20),(2,21),(4,24),(5,27),(0,27)],'^')
   self.poly([(27,21),(29,20),(29,27),(25,27),(24,25)],'^')
   # Streets grow from two shared well courts instead of a rectangular ring.
   self.path([(13,26),(13,22),(13,18),(14,16),(13,13),(11,13),(11,10),(10,10)],2,',','南井生活街—北井主巷')
   self.path([(10,11),(15,11),(16,10),(19,10),(19,8),(24,8),(27,8),(27,3),(28,3)],2,',','北井—守军街—城关')
   self.path([(13,22),(18,22),(18,20),(22,19),(22,15),(20,15),(20,10)],1,',','东侧后巷与北井侧援线')
   self.path([(10,22),(6,22),(6,17),(4,17),(4,10),(9,10)],1,',','西住户窄巷')
   self.rect(8,8,11,11,'b');self.rect(11,20,15,23,'b')
   self.stamp('well',10,8,ground='b');self.stamp('well',13,20,ground='b')
   for name,x,y in [('fishing_cottage',6,6),('fishing_cottage',9,4),('fishing_cottage',13,5),('fishing_cottage',18,3),('quay_warehouse',17,6),('coastal_keep',23,2),('fishing_cottage',5,13),('fishing_cottage',8,15),('fishing_cottage',9,18),('fishing_cottage',7,23),('fishing_cottage',18,17),('fishing_cottage',21,21),('quay_warehouse',18,24)]:self.stamp(name,x,y,ground='d')
   for p in [[(7,8),(8,8)],[(10,6),(10,7),(9,7),(9,9)],[(14,7),(14,11)],[(19,5),(20,5),(20,8),(19,8)],[(6,15),(6,17)],[(9,17),(11,17),(11,18),(13,18)],[(10,20),(11,20)],[(8,25),(10,25),(10,22)],[(19,19),(19,20),(18,20)],[(22,23),(20,23),(20,22)],[(19,26),(15,26),(13,26)]]:self.path(p,1,',')
   self.stamp('crates',21,24,ground='d');self.stamp('grain_sacks',21,25,ground='d');self.stamp('flowers',12,20,ground='b',solid=False);self.stamp('flowers',8,8,ground='b',solid=False)
   self.rect(11,23,11,23,'+')
   self.object('well_n',[10,9]);self.object('well_s',[13,21]);d['targets']=[o['position']for o in d['objects']];d['exit']=[28,3]
   self.units([[12,22],[13,22],[14,22],[15,22],[12,23],[13,23],[14,23],[15,23],[12,24],[13,24],[14,24],[15,24]],[[24,7],[16,8],[22,18],[22,11],[19,13],[12,6],[24,19],[20,9],[18,9],[7,11],[24,17],[23,8],[17,12]],[[9,23],[16,23]])
   for u,p in zip(d['reinforcements'],[[27,7],[27,9]]):u['position']=p
   self.notes=['两处井台分别围出北住区与南取水院，屋门、小仓院和取水巷共同构成紧凑沙城；井口是实体，南侧台阶才是守井目标。','南井就在部署前方，可先留守；通北井的主巷直接但会接触守军，西住户窄巷更长，东后巷能侧援但受到高处弓手与术士威胁。','南北well_target追井身份保持，北井可暂失后夺回；第3回合援兵从东北城关进入，至少保住一井到第6己方回合并击败队长的规则不变。']
  elif self.c=='F42':
   self.poly([(0,0),(10,0),(10,2),(7,4),(6,7),(4,10),(2,11),(0,10)],'^')
   self.poly([(0,18),(3,18),(5,22),(5,27),(0,27)],'^')
   self.poly([(28,0),(31,0),(31,8),(30,10),(28,9)],'^')
   self.poly([(27,20),(30,18),(31,20),(31,27),(27,27),(25,25)],'~')
   self.path([(11,26),(11,22),(11,19),(13,18),(13,16),(17,16),(17,10),(18,8),(18,6)],2,',','南入口—观测设备—北值守台')
   self.path([(12,22),(18,22),(20,20),(23,20),(23,15)],2,',','抄录工住区—东楼抢救线')
   self.path([(17,17),(20,17),(23,17)],1,',','设备与东楼联络道')
   self.path([(11,22),(7,22),(7,16),(6,15),(6,10),(9,9),(9,6),(15,6),(17,8)],1,',','西岩脊旧维护路')
   self.path([(23,15),(25,15),(26,12),(26,6),(24,6),(24,3),(27,3)],1,',','东楼外侧防火巡查道')
   self.rect(13,12,17,16,'b');self.rect(21,14,25,16,'b');self.rect(15,7,20,10,'b')
   self.stamp('sun_altar',14,13,ground='b',purpose='完整中央观测设备')
   self.stamp('quay_warehouse',22,13,ground='b',purpose='东楼记录室，南门朝抢救线')
   self.stamp('coastal_keep',16,2,ground='a',purpose='北值守楼');self.stamp('fishing_cottage',7,19,ground='a',purpose='抄录工住屋')
   self.stamp('ruined_watchtower',10,3,ground='a');self.stamp('ritual_lamp',12,12,ground='a');self.stamp('ritual_lamp',18,14,ground='a')
   self.stamp('crates',8,18,ground='a');self.stamp('grain_sacks',9,18,ground='a');self.path([(8,21),(11,21)],1,',')
   self.rect(10,23,10,23,'+')
   self.object('observatory_record',[23,14],[23,15]);self.object('observation_device',[15,15],[15,16]);d['burn_target']=[23,15]
   self.units([[10,22],[11,22],[12,22],[13,22],[10,24],[11,24],[12,24],[13,24],[11,23],[12,23]],[[17,9],[24,6],[18,11],[26,18],[10,7],[23,10],[20,12],[27,19],[9,10],[25,9],[17,12],[25,20],[12,8],[23,7]],[[8,22],[12,18]])
   d['targets']=[o['position']for o in d['objects']];d['exit']=[27,3]
   self.notes=['盐原观测院分为南抄录住区、中央设备台、东楼记录室和北值守楼，露盐地与小块铺石台面交错，岩脊与旧塔刻出院落边界。','东侧抢救线从部署区直抵记录楼南门；中央主道较短但会接触萨弥前的守军，西岩脊维护路较窄且更长，可从侧面接近北庭。','东楼对象与唯一南门操作格、burn_target完整对应；仍须先保护记录，再在观测设备南面复制。第5回合预告、第6回合出发及连续两次点火焚毁的规则保持。']
  else:
   # Four weathered stone masses stand in connected water. Maintenance
   # bridges cross only the water gaps and have substantial landings.
   self.poly([(4,22),(6,20),(10,20),(11,22),(11,25),(9,27),(4,27),(3,25)],'a')
   self.poly([(5,5),(10,4),(12,6),(12,11),(11,13),(7,14),(5,12)],'a')
   self.poly([(14,12),(19,12),(21,14),(21,18),(19,20),(16,21),(13,21),(12,18),(13,15)],'a')
   self.poly([(21,2),(28,2),(30,4),(29,7),(28,10),(24,10),(21,8),(19,7),(19,5)],'a')
   self.poly([(26,14),(30,13),(32,15),(32,22),(30,24),(26,22),(25,19),(25,16)],'a')
   self.bridge(7,13,8,21,'v');self.bridge(10,21,14,22);self.bridge(11,12,14,12);self.bridge(20,17,26,18);self.bridge(18,8,19,13,'v');self.bridge(27,9,28,15,'v')
   self.path([(7,26),(7,22),(9,22)],2,'b','南接应台作业路')
   self.path([(7,12),(9,12),(9,10)],2,'b','西侧调节台');self.rect(7,9,10,11,'b')
   self.path([(14,21),(15,19),(16,17),(18,17),(20,17)],2,'b','中央作业台主道');self.rect(15,15,18,18,'=')
   self.path([(26,18),(27,18),(27,21),(30,21)],2,'b','东调节台与援军落点')
   self.path([(19,8),(22,8),(24,8),(27,8),(28,6),(27,3)],2,'b','北神门前庭')
   self.rect(26,17,29,19,'=');self.rect(8,10,10,11,'=')
   self.stamp('ancient_arch',6,5,ground='a',purpose='西调节点旧石拱');self.stamp('ritual_lamp',10,7,ground='a')
   self.stamp('sun_altar',16,13,ground='a',purpose='中央流量设备');self.stamp('sun_altar',27,15,ground='a',purpose='东侧调节设备')
   self.stamp('coastal_keep',22,2,ground='a',purpose='北侧神门主楼');self.stamp('ritual_lamp',21,6,ground='a');self.stamp('ritual_lamp',29,6,ground='a')
   self.stamp('fishing_cottage',4,23,ground='a',purpose='南接应台工匠棚');self.stamp('crates',9,25,ground='a');self.stamp('grain_sacks',10,25,ground='a')
   self.stamp('rowboat',1,24,solid=False,purpose='西南泊船，完整船体位于水面')
   self.rect(8,25,8,25,'+')
   self.object('regulator_1',[16,17]);self.object('regulator_2',[27,19]);self.object('regulator_3',[9,11])
   self.units([[6,25],[7,25],[6,26],[7,26],[8,26],[9,26],[6,22],[7,22],[8,22],[9,22]],[[24,7],[24,9],[19,16],[29,21],[11,11],[22,8],[20,14],[29,18],[11,8],[26,8],[18,15],[30,16]],[[6,24],[14,20]])
   for u,p in zip(d['reinforcements'],[[31,20],[31,21]]):u['position']=p
   d['targets']=[o['position']for o in d['objects']];d['exit']=[27,3]
   self.notes=['沉没祭所由西调节台、中央作业台、东调节台与北神门四处残存石台组成，水体贯穿其间；南接应台留出工匠棚和泊船位置。','南侧双格便桥可直接进入中央作业台，西侧长桥通往旧石拱，再经一格短桥侧接中央；东桥连接独立援军平台，北方另有两条接近神门的维护线。','三处设备各有可站交接点和完整岸上落脚面，工匠位于南侧与中央后方；三点交接后等待到下一己方回合、至少一名工匠存活及投送切断入场快照均保持。']
 def flood(self,g,start):
  q=deque([tuple(start)]);seen={tuple(start):0}
  while q:
   x,y=q.popleft()
   for dx,dy in[(1,0),(0,1),(-1,0),(0,-1)]:
    p=x+dx,y+dy
    if 0<p[0]<self.w-1 and 0<p[1]<self.h-1 and p not in seen and g[p[1]][p[0]]not in'#^~':seen[p]=seen[x,y]+1;q.append(p)
  return seen
 def check(self):
  d=self.d;old=self.old;c=self.c;positions=d['player_positions']+[u['position']for u in d['enemies']+d['npc_units']+d['reinforcements']]
  assert len(positions)==len({tuple(p)for p in positions}),(c,'overlap')
  seen=self.flood(self.g,d['player_positions'][0])
  for m in self.modules:
   if m['logic']=='#':assert all(self.g[y][x]=='#' for x,y in m['cells']),(c,'solid building cut by path',m['name'],m['origin'])
  for p in positions+[d['exit']]:
   x,y=p;assert 0<x<self.w-1 and 0<y<self.h-1,(c,'outer ring',p)
   assert tuple(p)in seen,(c,'not inner-ring reachable',p,self.g[y][x])
  for group in['enemies','npc_units','reinforcements']:
   assert len(old[group])==len(d[group]);assert all({k:v for k,v in a.items()if k!='position'}=={k:v for k,v in b.items()if k!='position'}for a,b in zip(old[group],d[group])),(c,'actor invariant',group)
  approaches={}
  for a,b in zip(old['objects'],d['objects']):
   allowed={'position','approach','approaches','opens','open_art_cells','open_art_props'}
   assert{k:v for k,v in a.items()if k not in allowed}=={k:v for k,v in b.items()if k not in allowed},(c,'object rules',a['id'])
   x,y=b['position'];assert 0<x<self.w-1 and 0<y<self.h-1
   fronts=b.get('approaches',[b['approach']]if 'approach'in b else[])or ([[x,y]]if not b.get('adjacent')else[[x+dx,y+dy]for dx,dy in[(0,1),(1,0),(0,-1),(-1,0)]])
   legal=[p for p in fronts if tuple(p)in seen];assert legal,(c,'operation blocked',b['id'])
   approaches[b['id']]={'object':b['position'],'fronts':legal,'shortest_steps':min(seen[tuple(p)]for p in legal)}
  for k in['characters','terrain','goal','before','during','after','reinforcement_turn','burn_start','event_boats','clear_training_exp']:assert old.get(k)==d.get(k),(c,k)
  specials={q:sum(r.count(q)for r in self.g)for q in'+ht'};assert specials=={q:sum(r.count(q)for r in old['logic_grid'])for q in'+ht'}
  if c=='F42':assert d['burn_target']==next(o['approach']for o in d['objects']if o['id']=='observatory_record') and tuple(d['burn_target'])in seen
  changes={group:[{'id':b['id'],'before':a['position'],'after':b['position']}for a,b in zip(old[group],d[group])]for group in['enemies','npc_units','reinforcements']}
  changes.update(deployment_before=old['player_positions'],deployment_after=d['player_positions'],objects_before=old['objects'],objects_after=d['objects'],targets=d['targets'],exit=d['exit'])
  report={'passed':True,'code':c,'size':[self.w,self.h],'connected_inner_cells':len(seen),'all_actors_deployments_exit_strictly_inside':True,'unit_identity_order_attributes_equipment_AI_preserved':True,'story_rules_times_counts_preserved':True,'special_terrain_counts':specials,'interaction_fronts':approaches,'coordinate_changes':changes,'routes':self.routes,'notes':self.notes}
  if c=='F42':report.update(burn_start=d['burn_start'],burn_target=d['burn_target'],burner_steps_to_door=self.flood(self.g,next(u['position']for u in d['enemies']if u.get('ch4_burner'))).get(tuple(d['burn_target'])))
  write(O/f'{c}-design.json',report)
 def build(self):
  self.design();self.check();g=self.g;w=self.w;h=self.h;d=self.d
  ground=[[self.under.get((x,y),self.bg)if q=='#'else self.bg if q=='f'else q for x,q in enumerate(row)]for y,row in enumerate(g)]
  if self.c=='F44':ground=[['u'if q=='a'else q for q in row]for row in ground]
  border_material='sand'if self.bg=='d'else'cobble'if self.c=='F44'else'salt'
  base=[]
  for y,row in enumerate(ground):
   line=[]
   for x,q in enumerate(row):
    v=B.seed(f'{self.c}:ch4-east:{x}:{y}')%4;tile=B.PACK['base'][MAT[q]][v]
    if q=='u':tile=WEATHERED[v]
    if q in',b=':tile=A.edge(MAT[q],border_material,B.mask_at(ground,x,y,lambda z:z in',b=+s'),v)
    if q=='^':tile=A.edge('bare_rock','sand'if self.bg=='d'else'salt',B.mask_at(ground,x,y,lambda z:z=='^'),v)
    if q=='~':tile=A.water([MAT[ground[y+dy][x+dx]]if 0<=x+dx<w and 0<=y+dy<h else'sea'for dx,dy in[(0,-1),(1,0),(0,1),(-1,0)]],v)
    if q=='s':
     mask=sum(bit for dx,dy,bit in[(0,-1,1),(1,0,2),(0,1,4),(-1,0,8)]if 0<=x+dx<w and 0<=y+dy<h and ground[y+dy][x+dx]=='s');tile=A.trans['walkway'][self.bridges.get((x,y),'h')+str(mask)][v]
    line.append(tile)
   base.append(line)
  if self.c=='F41':
   # Current renderer has no sand surroundings. Native background cells extend
   # beyond the field only; no actor, terrain, collider, or coordinate is changed.
   for y in range(-8,h+8):
    for x in range(-8,w+8):
     if 0<=x<w and 0<=y<h:continue
     v=B.seed(f'F41:border:{x}:{y}')%4;self.props.append({'path':f'res://assets/chapter4-redesign-20261022/east/sand-border-{v}.png','position':[x*16,y*16],'purpose':'native sand background outside playable field'})
  nature=[];rng=random.Random(B.seed(self.c+'-ridges'))
  allowed={(x,y)for y,row in enumerate(g)for x,q in enumerate(row)if q=='^'};taken=set()
  for x,y in sorted(allowed,key=lambda p:(-sum((p[0]+dx,p[1]+dy)in allowed for dx in range(-1,3)for dy in range(-1,3)),p[1],p[0])):
   if (x,y)in taken:continue
   choices=['peak_low','crag_tall','ridge_bent','outcrop'];rng.shuffle(choices)
   for key in choices:
    sw,sh=B.NATURE[key]['size'];cells={(xx,yy)for yy in range(y,y+math.ceil(sh/16))for xx in range(x,x+math.ceil(sw/16))}
    if cells<=allowed and not cells&taken:nature.append({'key':key,'position':[x*16,y*16],'flip':rng.random()<.3});taken|=cells;break
  for x,y in sorted(allowed-taken):nature.append({'key':'boulder','position':[x*16,y*16],'flip':rng.random()<.3})
  nature.sort(key=lambda p:p['position'][1]+B.NATURE[p['key']]['size'][1])
  d.update(map={'width':w,'height':h,'tiles':[IDS[q]for row in g for q in row]},logic_grid=[''.join(r)for r in g],visual_ground=[''.join(r)for r in ground],art_layers=[base,[[None]*w for _ in range(h)],self.top],art_modules=self.modules,art_props=self.props,natural_props=nature,art_atlas='res://assets/chapter4-redesign-20261022/east/terrain.png',art_columns=32,tactical_review_version='0.10.8-ch4',art_style_version='chapter4-redesign-20261022',landscape_revision='Authored well-city, observation terraces and flooded regulator network',tactical_routes=self.routes,tactical_notes=self.notes.copy(),visual_notes=self.notes.copy(),nature_layout={'biome':'sand'if self.bg=='d'else'sea'if self.bg=='~'else'salt','props':[],'excluded':[[0,0,w*16,h*16]]},surroundings='sea'if self.bg=='~'else'')
  p=R/f'data/stages/{self.c}.json';write(p,d);report=json.loads((O/f'{self.c}-design.json').read_text());report['map_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();write(O/f'{self.c}-design.json',report)
if __name__=='__main__':
 for args in [('F41',30,28,'d'),('F42',32,28,'a'),('F44',34,30,'~')]:Field(*args).build()
 A.save();meta=json.loads((ART/'terrain.json').read_text());meta['purpose']='Private fourth-chapter eastern terrain transitions; original native modules and scale retained';write(ART/'terrain.json',meta)
 write(O/'asset-review.json',{'atlas':'assets/chapter4-redesign-20261022/east/terrain.png','size':meta['size'],'bytes':meta['bytes'],'compression':'oxipng lossless','original_ids_preserved':A.original,'quality_note':'Native complete buildings and 16px terrain retained; F41 native sand background and F44 darker native cobbles preserve scale. File size follows visual-quality priority.','background_tiles':[{'path':str(p.relative_to(R)),'size':[16,16],'bytes':p.stat().st_size}for p in sorted(ART.glob('sand-border-*.png'))]})
 print('F41/F42/F44 first design written with invariant and inner-ring checks.')
