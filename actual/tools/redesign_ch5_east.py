#!/usr/bin/env python3
"""Chapter five repair works, asymmetric palace wards and archive reading wings."""
from pathlib import Path
from collections import deque
from PIL import Image
import copy,hashlib,importlib.util,json,math,random,subprocess
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter5-redesign-20261022/east';BASE=O.parent/'baseline';ART=R/'assets/chapter5-redesign-20261022/east'
spec=importlib.util.spec_from_file_location('ch5_east_helpers',R/'tools/redesign_ch3_east.py');N=importlib.util.module_from_spec(spec);spec.loader.exec_module(N)
N.O=O;N.BASE=BASE;N.ART=ART;N.L.ART=ART;N.A=N.L.Atlas();A=N.A;B=N.B;IDS={**N.IDS,'w':48};MAT={**N.MAT,'w':'timber','^':'cave'};write=N.write
for p in json.loads((R/'assets/chapter5/manifest.json').read_text()):B.MODULES['muted_'+p['name']]={'footprint':[p['size'][0]//16,p['size'][1]//16],'path':p['path']}
B.MODULES['archive_bay']={'footprint':[3,3],'path':'res://assets/chapter5-redesign-20261022/east/archive-bay.png'}
temple=json.loads((R/'assets/chapter5/terrain.json').read_text())['materials'];temple_image=Image.open(R/'assets/chapter5/temple-tiles.png').convert('RGBA')
for name in ['ivory','sandstone']:
 ids=[]
 for source in temple[name]:
  ids.append(len(A.cells));A.cells.append(temple_image.crop((source%32*16,source//32*16,source%32*16+16,source//32*16+16)))
 B.PACK['base'][name]=ids
def cave_wall(neighbors,v):
 key='ch5-cave:'+''.join('1'if n else'0'for n in neighbors)
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
class Field(N.Field):
 def object(self,id,p,front=None):
  o=next(o for o in self.d['objects']if o['id']==id);o['position']=p
  if front is not None:o['approach']=front
 def enclosure(self,x,y,w,h,gaps=(),floor=None,purpose=''):
  if floor:self.rect(x,y,x+w-1,y+h-1,floor)
  gapset=set(map(tuple,gaps));cells=[]
  if 'ch5_stone_corner'not in A.add:
   im=A.cells[459].copy();im.alpha_composite(A.cells[463]);A.add['ch5_stone_corner']=len(A.cells);A.cells.append(im)
  for yy in range(y,y+h):
   for xx in range(x,x+w):
    if xx not in[x,x+w-1]and yy not in[y,y+h-1]or(xx,yy)in gapset:continue
    self.under[xx,yy]=self.g[yy][xx];self.g[yy][xx]='#';tile=459 if yy in[y,y+h-1]else 463
    if xx in[x,x+w-1]and yy in[y,y+h-1]:tile=A.add['ch5_stone_corner']
    self.top[yy][xx]=tile;cells.append([xx,yy])
  self.modules.append({'name':'continuous_stone_enclosure','origin':[x,y],'footprint':[w,h],'cells':cells,'logic':'#','runtime_prop':False,'purpose':purpose,'openings':[list(p)for p in gaps]})
 def barrier(self,x0,y,x1,gaps=(),ground='b'):
  cells=[]
  for x in range(x0,x1+1):
   if x in gaps:continue
   self.under[x,y]=ground;self.g[y][x]='#';self.top[y][x]=459;cells.append([x,y])
  self.modules.append({'name':'continuous_stone_screen','origin':[x0,y],'footprint':[x1-x0+1,1],'cells':cells,'logic':'#','runtime_prop':False,'openings':[[x,y]for x in gaps]})
 def design(self):
  d=self.d
  if self.c=='F51':
   self.poly([(2,3),(5,2),(13,2),(14,5),(14,26),(11,28),(3,28),(2,25)],'b')
   self.poly([(20,2),(29,2),(31,5),(31,27),(22,28),(20,25)],'b')
   self.rect(16,0,18,29,'~')
   self.path([(6,27),(9,27),(9,18),(13,18),(13,13),(21,13)],2,'=','西南接应—主检修桥')
   self.path([(20,13),(20,23),(26,23),(26,21)],2,'=','东工作院南侧交接廊')
   self.path([(9,25),(23,25),(29,25),(29,23)],1,'=','渠尾窄维护桥与东增援口')
   self.path([(13,13),(13,4),(10,4)],1,'=','西侧检修上廊')
   self.path([(20,7),(25,7),(25,5),(30,5),(30,8)],2,'=','北值守阶前')
   self.path([(20,13),(20,7)],1,'=','东渠边检修侧廊')
   self.path([(9,18),(8,18),(8,15)],2,'=','第一修复院南门')
   self.bridge(14,13,20,14);self.bridge(14,25,20,25)
   self.enclosure(3,5,10,11,[(8,15),(9,15)],floor='c',purpose='第一工班实体防护院，唯一双格南门')
   self.enclosure(21,9,11,13,[(26,21),(27,21)],floor='c',purpose='第二工班实体防护院，唯一双格南门')
   self.rect(6,10,9,13,'b');self.rect(24,14,28,18,'b');self.path([(8,13),(8,15)],2,'b');self.path([(26,18),(26,21)],2,'b')
   self.stamp('muted_regulator',5,6,ground='b');self.stamp('muted_regulator',24,10,ground='b');self.stamp('muted_stair',23,1,ground='b')
   for name,x,y in [('ritual_lamp',4,11),('ritual_lamp',10,11),('ritual_lamp',22,15),('ritual_lamp',29,15),('crates',5,22),('grain_sacks',6,22),('crates',30,24),('brazier',22,6)]:self.stamp(name,x,y,ground='c')
   self.rect(8,22,8,22,'+');self.rect(23,25,23,25,'+')
   self.object('repair_1',[7,9],[7,10]);self.object('repair_2',[26,13],[26,14]);d['exit']=[6,27]
   self.units([[5,25],[6,25],[7,25],[8,25],[5,26],[6,26],[7,26],[8,26],[4,25],[4,26]],[[25,5],[11,3],[29,6],[20,18],[11,18],[10,3],[30,7],[29,23],[4,18],[13,7],[22,7]],[[6,11],[25,15]])
   for u,p in zip(d['reinforcements'],[[31,26],[30,26]]):u['position']=p
   self.notes=['地下主渠把两处错位修复院分在两岸，连续石墙与双格南门为地方工班提供真实防护；设备完整，工作面只留在南侧。','主检修桥两格宽，接西南集结与东工作院；南端一格维护桥较远但能绕过中央守军，渠边上廊连接北值守阶。','第一工班靠近西侧推进线，第二工班在东院更深处；交接前清理门外威胁，再分别保护到下一己方回合。工班身份、锁定接手、第三回合东南援军和胜败规则不变。']
  elif self.c=='F52':
   self.rect(2,2,33,25,'a')
   self.path([(8,28),(8,23),(8,13)],2,'b','南口—西门阵近路')
   self.path([(8,23),(17,23),(27,23),(27,18),(28,18),(28,16)],2,'b','南横廊—东翼门阵')
   self.path([(17,27),(17,21),(17,9)],2,'b','中央石桥与神官前庭')
   self.path([(8,13),(11,13),(11,9),(17,9),(22,9),(22,17),(28,17)],1,'b','两翼内侧巡廊')
   self.poly([(14,13),(21,13),(23,15),(23,18),(21,20),(15,20),(13,18),(13,15)],'~')
   self.rect(17,12,18,21,'b');self.bridges['stone_axis']={'cells':[[x,y]for x in[17,18]for y in range(12,22)],'purpose':'中央水庭石桥，两端接主廊'}
   self.rect(6,13,10,16,'b');self.rect(26,16,30,19,'b');self.rect(14,8,21,11,'=')
   self.enclosure(2,2,32,24,[(x,25)for x in range(7,11)]+[(17,25),(18,25)],purpose='完整下层院墙，西南门与中轴南门')
   self.barrier(4,19,12,[7,8],ground='a');self.barrier(23,22,32,[27,28],ground='a')
   self.stamp('muted_palace',14,1,ground='a');self.stamp('muted_regulator',6,9,ground='b');self.stamp('muted_regulator',26,12,ground='b')
   for x,y in[(3,8),(31,8),(11,3),(24,3)]:self.stamp('muted_column',x,y,ground='a')
   for x,y in[(12,21),(22,21),(12,11),(23,11)]:self.stamp('ritual_lamp',x,y,ground='a')
   self.rect(5,26,5,26,'+');self.rect(28,26,28,26,'+')
   self.object('lower_west',[8,12],[8,13]);self.object('lower_east',[28,15],[28,16]);d['exit']=[17,27]
   self.units([[7,26],[8,26],[9,26],[10,26],[7,27],[8,27],[9,27],[10,27],[7,28],[8,28]],[[17,9],[7,16],[28,18],[22,9],[12,9],[10,15],[25,18],[23,10],[11,10],[6,14],[30,17]],[])
   self.notes=['下层宫院以完整外墙、两组错位翼院和中央水庭形成层次；主殿占北端，四根完整石柱标出柱廊，西南门与中轴南门均是真实开口。','西门阵更近，门前可展开；东门阵藏在较深的侧院，须穿过南横廊与两格侧门。中央双格石桥跨过真实水庭，连接神官前庭，左右接敌距离不同。','两门阵均在装置南面确认，走过不会自动完成；仍须确认两处并击败中央神官，无新增钥匙、宝物或专属武器门槛。']
  else:
   self.rect(2,2,27,24,'a');self.path([(15,26),(15,8)],2,'b','北原件—南门交接中轴')
   self.path([(7,23),(22,23),(22,21)],2,'b','阅览翼南联络廊')
   self.path([(12,13),(15,13),(18,13),(18,8),(15,8)],1,'b','西阅览室侧廊与档案楼门前')
   self.path([(15,17),(19,17)],2,'b','东阅览室换线廊')
   self.path([(7,20),(7,23)],2,'b');self.rect(12,8,17,10,'b')
   self.enclosure(2,2,26,23,[(x,24)for x in range(13,17)],purpose='档案院外墙与四格南门')
   self.enclosure(3,8,10,13,[(7,20),(8,20),(12,13),(12,14)],floor='w',purpose='西阅览室：南门入、东门通中轴')
   self.enclosure(19,11,9,11,[(22,21),(23,21),(19,16),(19,17)],floor='w',purpose='东阅览室：南门入、西门通中轴')
   self.enclosure(3,2,8,5,[],floor='w',purpose='封闭北西旁室，只能看见，不添加开门或宝物规则')
   self.enclosure(21,2,7,6,[],floor='w',purpose='封闭北东旁室，保留不能进入全部房间的叙事')
   self.stamp('muted_archive',12,2,ground='b')
   for x,y in[(4,9),(8,9),(4,15),(20,12),(24,12),(24,17),(5,3),(22,3)]:self.stamp('archive_bay',x,y,ground='w',purpose='完整书架与阅览桌，3×3真实阻挡')
   for x,y in[(13,18),(17,11),(18,22)]:self.stamp('ritual_lamp',x,y,ground='a')
   self.rect(11,23,11,23,'+');self.rect(19,23,19,23,'+')
   self.object('old_record',[15,7],[15,8]);self.object('archive_exit',[15,25]);d['exit']=[15,25]
   self.units([[12,25],[13,25],[14,25],[16,25],[17,25],[18,25],[12,26],[13,26],[14,26],[16,26]],[[15,10],[10,14],[22,17],[18,18],[10,18],[13,11],[21,19]],[])
   self.notes=['北侧完整档案楼朝向中轴南门，左右阅览室采用木地板、成组书架与阅览桌，主庭和室内走廊用途清楚，不再用空石坪暗示书库。','西阅览室经南门与东侧门连接主廊，东室经南门与西侧门换线；书架全部按完整3×3占地阻挡，格间走廊可通行。','北侧两间封闭旁室只呈现保存中的藏书，不添加假门、宝物或新交互；原件在档案楼南面取回，击败守卫后沿中轴回南门交接，开放时机与支线奖励规则保持。']
  d['targets']=[o['position']for o in d['objects']]
 def flood(self,start):
  q=deque([tuple(start)]);seen={tuple(start):0}
  while q:
   x,y=q.popleft()
   for dx,dy in[(1,0),(0,1),(-1,0),(0,-1)]:
    p=x+dx,y+dy
    if 0<p[0]<self.w-1 and 0<p[1]<self.h-1 and p not in seen and self.g[p[1]][p[0]]not in'#^~':seen[p]=seen[x,y]+1;q.append(p)
  return seen
 def check(self):
  d=self.d;old=self.old;c=self.c;actors=d['enemies']+d['npc_units']+d['reinforcements'];positions=d['player_positions']+[u['position']for u in actors]
  assert len(positions)==len(set(map(tuple,positions))),(c,'actor overlap')
  seen=self.flood(d['player_positions'][0])
  for m in self.modules:
   if m['logic']=='#':assert all(self.g[y][x]=='#'for x,y in m['cells']),(c,'building was cut',m['name'],m['origin'])
  for p in positions+[d['exit']]:
   x,y=p;assert 0<x<self.w-1 and 0<y<self.h-1,(c,'outer ring',p)
   assert tuple(p)in seen,(c,'unreachable',p,self.g[y][x])
  for group in['enemies','npc_units','reinforcements']:
   assert len(old[group])==len(d[group]);assert all({k:v for k,v in a.items()if k!='position'}=={k:v for k,v in b.items()if k!='position'}for a,b in zip(old[group],d[group])),(c,'actor identity/values',group)
  fronts={}
  for a,b in zip(old['objects'],d['objects']):
   assert{k:v for k,v in a.items()if k not in['position','approach']}=={k:v for k,v in b.items()if k not in['position','approach']},(c,'object rule',b['id'])
   p=b.get('approach',b['position']);x,y=p;assert 0<x<self.w-1 and 0<y<self.h-1 and tuple(p)in seen,(c,'bad operation',b['id'],p)
   fronts[b['id']]={'object':b['position'],'operation':p,'steps_from_first_deploy':seen[tuple(p)]}
  permitted={'map','logic_grid','art_layers','art_props','art_modules','natural_props','visual_ground','art_atlas','art_columns','tactical_review_version','art_style_version','landscape_revision','tactical_routes','tactical_notes','visual_notes','nature_layout','surroundings','player_positions','enemies','npc_units','reinforcements','objects','targets','exit'}
  for k,v in old.items():
   if k not in permitted:assert v==d[k],(c,'rule/story',k)
  specials={ch:sum(row.count(ch)for row in self.g)for ch in'+ht'};assert specials=={ch:sum(row.count(ch)for row in old['logic_grid'])for ch in'+ht'}
  write(O/f'{c}-design.json',{'passed':True,'code':c,'size':[self.w,self.h],'connected_inner_cells':len(seen),'all_anchors_inside_reachable':True,'actors_identity_order_stats_equipment_AI_preserved':True,'story_rules_timing_rewards_preserved':True,'special_terrain_counts':specials,'interaction_fronts':fronts,'notes':self.notes,'routes':self.routes,'coordinate_changes':{group:[{'id':b['id'],'before':a['position'],'after':b['position']}for a,b in zip(old[group],d[group])]for group in['enemies','npc_units','reinforcements']},'deployment_before':old['player_positions'],'deployment_after':d['player_positions'],'objects':d['objects'],'exit':d['exit'],'structures':self.modules})
 def build(self):
  self.design();self.check();d=self.d;w=self.w;h=self.h;g=self.g
  ground=[[self.under.get((x,y),self.bg)if q=='#'else'.'if q=='f'else q for x,q in enumerate(row)]for y,row in enumerate(g)]
  bgmat='cave'if self.c=='F51'else'salt';base=[];mats=MAT if self.c=='F51'else{**MAT,'b':'ivory','=':'sandstone'}
  for y,row in enumerate(ground):
   line=[]
   for x,q in enumerate(row):
    v=B.seed(f'{self.c}:ch5-east:{x}:{y}')%4;tile=B.PACK['base'][mats[q]][v]
    if q in'b=,':tile=A.edge(mats[q],bgmat,B.mask_at(ground,x,y,lambda z:z in'b=,+s'),v)
    if q=='^':tile=cave_wall([0<=x+dx<w and 0<=y+dy<h and ground[y+dy][x+dx]not in'^#'for dx,dy in[(0,-1),(1,0),(0,1),(-1,0)]],v)
    if q=='~':tile=A.water([mats[ground[y+dy][x+dx]]if 0<=x+dx<w and 0<=y+dy<h else'sea'for dx,dy in[(0,-1),(1,0),(0,1),(-1,0)]],v)
    if q=='s':
     mask=sum(bit for dx,dy,bit in[(0,-1,1),(1,0,2),(0,1,4),(-1,0,8)]if 0<=x+dx<w and 0<=y+dy<h and ground[y+dy][x+dx]=='s');tile=A.trans['walkway'][self.bridges.get((x,y),'h')+str(mask)][v]
     if self.c=='F51'and(x<16 or x>18):tile=B.PACK['base']['cobble'][v]
    line.append(tile)
   base.append(line)
  d.update(map={'width':w,'height':h,'tiles':[IDS[q]for row in g for q in row]},logic_grid=[''.join(row)for row in g],visual_ground=[''.join(row)for row in ground],art_layers=[base,[[None]*w for _ in range(h)],self.top],art_modules=self.modules,art_props=self.props,natural_props=[],art_atlas='res://assets/chapter5-redesign-20261022/east/terrain.png',art_columns=32,tactical_review_version='0.10.9-ch5',art_style_version='chapter5-redesign-20261022',landscape_revision='Protected repair yards, asymmetric ward courts and furnished archive wings',tactical_routes=self.routes,tactical_notes=self.notes.copy(),visual_notes=self.notes.copy(),nature_layout={'biome':'rock'if self.c=='F51'else'salt','props':[],'excluded':[[0,0,w*16,h*16]]},surroundings='cave'if self.c=='F51'else'land')
  p=R/f'data/stages/{self.c}.json';write(p,d);j=json.loads((O/f'{self.c}-design.json').read_text());j['map_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();write(O/f'{self.c}-design.json',j)
if __name__=='__main__':
 for args in [('F51',34,30,'^'),('F52',36,30,'a'),('S51',30,28,'a')]:Field(*args).build()
 A.save();subprocess.run(['/opt/homebrew/bin/oxipng','-o','3','--quiet',str(ART/'archive-bay.png')],check=True)
 write(O/'asset-review.json',{'generated_asset':{'path':'assets/chapter5-redesign-20261022/east/archive-bay.png','runtime_size':[48,48],'runtime_bytes':(ART/'archive-bay.png').stat().st_size,'source':'reports/chapter5-redesign-20261022/east/source/archive-bay-original.png','source_isolated_by_gdignore':True,'generation':'Built-in image_gen via imagegen skill; one transparent complete bookcase/reading desk bay','crop':'Alpha-bound content cropped without clipping; uniformly fitted to48x48','review':'Actual48px light/dark background direct view; intact sides, desk and stool, no white outline or background residue. Full3x3 blocker.'},'reused_assets':'Unmodified chapter5 muted-v2 architecture and original native terrain/wall/utility modules','atlas_bytes':(ART/'terrain.png').stat().st_size,'compression':'oxipng lossless; no shared original asset changed'})
 print('F51/F52/S51 design written; strict anchor and invariant checks passed.')
