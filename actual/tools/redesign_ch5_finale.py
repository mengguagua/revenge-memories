#!/usr/bin/env python3
"""Joint forecourt and final throne: original muted architecture, native collisions."""
from pathlib import Path
from collections import deque
from PIL import Image
import copy,hashlib,importlib.util,json,math,random,subprocess
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter5-redesign-20261022/finale';BASE=O.parent/'baseline';ART=R/'assets/chapter5-redesign-20261022/finale'
spec=importlib.util.spec_from_file_location('native_builder',R/'tools/redesign_ch1_camp_fort.py');N=importlib.util.module_from_spec(spec);spec.loader.exec_module(N);N.BASE=BASE;N.O=O;B=N.B;write=N.write
TEMPLE=json.loads((R/'assets/chapter5/terrain.json').read_text())['materials'];IDS={'.':48,',':48,'f':172,'^':94,'~':96,'#':196,'=':208,'s':191,'b':48,'+':218}
class Atlas:
 def __init__(self):
  im=Image.open(R/'assets/chapter5/temple-tiles.png').convert('RGBA');self.cells=[im.crop((x,y,x+16,y+16))for y in range(0,im.height,16)for x in range(0,im.width,16)];self.original=len(self.cells);self.edges={}
 def ground(self,ch,v):return TEMPLE['ivory'][1]if ch=='b'else TEMPLE['sandstone'][1]if ch=='='else B.PACK['base'][{'.':'grass',',':'dirt','~':'sea','+':'sacred'}[ch]][v]
 def edge(self,ch,mask,v):
  key=ch+':'+str(mask)
  if key not in self.edges:
   ids=[]
   for n in range(4):
    im=self.cells[self.ground('.',n)].copy();fg=self.cells[self.ground(ch,n)].copy();fg.putalpha(N.L.W.alpha_mask(mask));im.alpha_composite(fg);ids.append(len(self.cells));self.cells.append(im)
   self.edges[key]=ids
  return self.edges[key][v]
 def save(self):
  ART.mkdir(parents=True,exist_ok=True);im=Image.new('RGBA',(512,math.ceil(len(self.cells)/32)*16))
  for i,t in enumerate(self.cells):im.paste(t,(i%32*16,i//32*16))
  p=ART/'terrain.png';im.save(p);subprocess.run(['/opt/homebrew/bin/oxipng','-o','3','--quiet',str(p)],check=True);write(ART/'terrain.json',{'original_source':'res://assets/chapter5/temple-tiles.png','original_tile_count':self.original,'original_pixels_preserved':True,'tile_count':len(self.cells),'tile_size':16,'columns':32,'floor_edges':self.edges,'purpose':'Muted native palace ground; connected ivory/sandstone floors share a single edge mask, preventing grass seams between adjacent paving families. Water basins have clean physical edges.','size':list(im.size),'bytes':p.stat().st_size})
A=Atlas()
class Field(N.Field):
 def __init__(self,c,w,h):super().__init__(c,w,h);self.g=[list('.'*w)for _ in range(h)];self.stairs=[];self.landmarks=[]
 def path(self,ps,width=3,ch='=',name=''):super().path(ps,width,ch,name)
 def architecture(self,name,x,y,walk=None):
  im=Image.open(R/f'assets/chapter5/{name}.png');fw,fh=im.width//16,im.height//16;walk=walk or[];cells=[]
  for yy in range(y,y+fh):
   for xx in range(x,x+fw):
    assert 0<=xx<self.w and 0<=yy<self.h and self.g[yy][xx]!='#',(self.c,'architecture overlap',name,xx,yy)
    self.under[xx,yy]='='if name=='throne'and yy==y+fh-1 else'.'if self.g[yy][xx]in 'f^'else self.g[yy][xx];self.g[yy][xx]='='if[xx,yy]in walk else'#';cells.append([xx,yy])
  m={'name':name,'origin':[x,y],'footprint':[fw,fh],'cells':cells,'logic':'#','walk_through_cells':walk,'runtime_prop':True,'palette':'existing-muted-v2','purpose':'完整既有神宫位图，按实体栏柱/建筑碰撞'};self.mods.append(m);self.props.append({'path':f'res://assets/chapter5/{name}.png','position':[x*16,y*16]});self.landmarks.append(m)
 def stair(self,x,y):
  walk=[[xx,yy]for yy in range(y,y+4)for xx in [x+1,x+2]];self.architecture('stair',x,y,walk);self.stairs.append({'origin':[x,y],'walk_through_cells':walk,'blocked_rail_cells':[[xx,yy]for yy in range(y,y+4)for xx in[x,x+3]]})
 def healing(self,x,y):
  self.g[y][x]='+';self.props.append({'path':B.MODULES['flowers']['path'],'position':[x*16,y*16]});self.mods.append({'name':'flowers','origin':[x,y],'footprint':[1,1],'cells':[[x,y]],'logic':'inherits_ground','runtime_prop':True})
 def deployments(self,left,right):self.d['player_positions_by_route']={'alm':left,'celica':right};self.d['player_positions']=left+right
 def forecourt(self):
  self.poly([(4,8),(12,8),(14,11),(14,17),(12,20),(12,28),(3,28),(3,23),(4,20)],'b');self.poly([(25,8),(33,8),(34,11),(34,28),(25,28),(25,20),(23,17),(23,11)],'b')
  self.poly([(13,7),(24,7),(25,11),(23,13),(23,16),(22,19),(15,19),(13,16),(13,13),(11,11)],'b')
  self.path([(6,29),(6,22),(9,22),(9,15)],3,name='西军入口—左庭门阵');self.path([(31,29),(31,22),(29,22),(29,15)],3,name='东军入口—右庭门阵');self.path([(7,28),(30,28)],3,name='两军后方联络廊')
  self.path([(18,29),(18,18)],3,name='共同进军中轴');self.path([(9,18),(28,18)],3,name='两翼门阵后的横向换线平台');self.path([(12,15),(12,9),(25,9),(25,15)],2,name='上层前廊的侧面接近线');self.path([(17,12),(21,12),(21,9)],3,name='中阶上方接敌台')
  self.path([(9,14),(12,14)],2,name='西阵门前');self.path([(26,14),(29,14)],2,name='东阵门前');self.rect(17,8,20,12,'=')
  self.rect(13,21,15,26,'~');self.rect(22,21,24,26,'~');self.poly([(1,11),(3,10),(3,18),(2,20),(1,19)],'f');self.poly([(35,11),(36,11),(36,20),(34,18)],'f')
  self.poly([(5,2),(11,2),(12,5),(10,7),(5,6)],'f');self.poly([(26,2),(32,2),(33,6),(27,7),(25,5)],'f');self.poly([(10,20),(11,20),(11,24),(10,23)],'f');self.poly([(26,20),(27,20),(27,24),(26,23)],'f')
  self.rect(12,13,15,16,'~');self.rect(20,13,25,16,'~');self.rect(12,8,15,11,'.');self.rect(22,8,25,11,'.');self.rect(13,8,15,10,'f');self.rect(22,8,24,10,'f');self.rect(3,13,5,19,'f');self.rect(32,13,34,19,'f')
  self.architecture('palace',15,1);self.architecture('regulator',7,10);self.architecture('regulator',27,10);self.stair(16,14)
  for x,y in[(2,23),(10,23),(25,23),(34,23)]:self.architecture('column',x,y)
  self.healing(8,27);self.healing(29,27)
  self.d['objects'][0].update(position=[9,13],approach=[9,14]);self.d['objects'][1].update(position=[29,13],approach=[29,14]);self.d['targets']=[o['position']for o in self.d['objects']]
  self.update_positions({'J53_boss':[19,10],'J53_e1':[8,19],'J53_e2':[29,19],'J53_e3':[12,12],'J53_e4':[25,12],'J53_e5':[7,18],'J53_e6':[30,18],'J53_e7':[13,10],'J53_e8':[24,10],'J53_e9':[10,18],'J53_e10':[27,18],'J53_e11':[15,11],'J53_e12':[22,11],'J53_e13':[6,17],'J53_e14':[31,17],'J53_e15':[20,12]},[],[18,29])
  self.deployments([[5,25],[6,25],[7,25],[8,25],[5,26],[6,26],[7,26],[8,26],[5,27],[6,27]],[[29,25],[30,25],[31,25],[32,25],[29,26],[30,26],[31,26],[32,26],[31,27],[32,27]])
  self.d['location_theme']='左右门阵庭院、柱列入口与中轴阶台组成神宫前庭，两军可在后廊和中层横廊换线'
  self.notes=['两军分别从西南、东南柱列入口展开，左右庭各有本侧门阵与守军；两侧十个部署候选格均落在入口平台，不占台阶或门前格。','两翼之间有后方联络廊与中层横廊；内池和上庭小园把中央阶口与两侧门阵分开，可先解决本侧后换线支援，也能经门阵外侧短廊接近统领。','正殿位于中轴顶端，中央阶梯只有真实踏步可走，两侧栏柱阻挡；长池与花圃分出正面进军与两翼道路。','保留原合流所有权、双方最多十人、两翼确认和击败统领条件；两处后方恢复点数量不变。']
 def throne(self):
  self.poly([(3,24),(9,23),(12,24),(13,22),(21,22),(22,24),(27,23),(30,24),(31,28),(28,30),(5,30),(2,28)],'b');self.poly([(11,7),(21,7),(24,10),(24,13),(22,15),(11,15),(8,13),(8,10)],'b')
  self.path([(6,29),(28,29)],3,name='两军后撤横廊');self.path([(16,29),(16,20)],3,name='神座正面下层仪道');self.path([(7,27),(9,27),(9,22)],3,name='西侧翼上阶通路');self.path([(27,27),(24,27),(24,22)],3,name='东侧翼上阶通路')
  self.path([(9,18),(9,13),(12,13)],2,name='西侧上层回廊');self.path([(24,18),(24,13),(21,13)],2,name='东侧上层回廊');self.path([(12,12),(21,12)],3,name='神座前攻击与召唤平台');self.rect(13,7,20,11,'=');self.path([(16,15),(16,12)],3,name='中央上阶落脚区')
  self.rect(11,21,13,25,'~');self.rect(19,21,21,25,'~');self.poly([(2,5),(4,3),(7,4),(7,9),(5,11),(2,9)],'f');self.poly([(27,3),(31,3),(32,8),(29,11),(27,9)],'f');self.poly([(2,20),(5,19),(6,21),(5,24),(3,23)],'f');self.poly([(28,19),(31,19),(32,23),(29,24)],'f')
  self.architecture('throne',14,1);self.stair(14,16);self.stair(8,18);self.stair(22,18)
  for x,y in[(6,2),(25,2),(5,13),(28,13)]:self.architecture('column',x,y)
  self.healing(9,28);self.healing(24,28)
  self.update_positions({'J54_boss':[16,8],'J54_e1':[9,16],'J54_e2':[24,16],'J54_e3':[12,10],'J54_e4':[21,10],'J54_e5':[8,15],'J54_e6':[25,15],'J54_e7':[12,11],'J54_e8':[21,11],'J54_e9':[12,14]},[],[16,29]);self.d['targets']=[[16,8]]
  self.deployments([[4,26],[5,26],[6,26],[7,26],[4,27],[5,27],[6,27],[7,27],[5,28],[6,28]],[[26,26],[27,26],[28,26],[29,26],[26,27],[27,27],[28,27],[29,27],[27,28],[28,28]])
  self.d['location_theme']='神座高台与三个真实阶口构成终局战场，双侧上层回廊绕到攻击平台，长池分开后方领队退守区'
  self.notes=['实体神座位于上层中轴，中央仪道与两侧阶廊共同通向攻击平台；三座阶梯的踏步和栏柱分别对应通行与阻挡。','首领周围保留近战和法术攻击圈，固定(16,10)及邻近平台可接纳半血增援；柱脚、神座和水池不压住召唤或接敌格。','两侧先处理飞翼和术士后，可借侧廊回转；下层入口和池旁后廊给弱领队、治疗者留出后撤空间，两处恢复点仍在后方。','双方各十个候选部署格独立且全部内圈；两主角都须存活，普通武器与法术有效，半血力量+3、只召唤一次且不回血的原规则不变。']
 def flood(self,start):
  seen={tuple(start):0};q=deque([tuple(start)])
  while q:
   x,y=q.popleft()
   for dx,dy in[(0,-1),(1,0),(0,1),(-1,0)]:
    p=x+dx,y+dy
    if 0<p[0]<self.w-1 and 0<p[1]<self.h-1 and p not in seen and self.g[p[1]][p[0]]not in '#^~':seen[p]=seen[x,y]+1;q.append(p)
  return seen
 def finish(self):
  self.forecourt()if self.c=='J53'else self.throne();self.d['surroundings']='land';self.d['surroundings_biome']='grass'
  anchors=self.d['player_positions']+[self.d['exit']]+[u['position']for u in self.d['enemies']+self.d['npc_units']+self.d['reinforcements']];protected={tuple(p)for p in anchors}
  for o in self.d['objects']:protected.add(tuple(o.get('approach',o['position'])))
  for x,y in protected:
   assert 0<x<self.w-1 and 0<y<self.h-1,(self.c,'outer anchor',x,y)
   if self.g[y][x]=='f':self.g[y][x]='.'
   assert self.g[y][x]not in '#^~',(self.c,'blocked anchor',x,y,self.g[y][x])
  assert len(anchors)==len({tuple(p)for p in anchors}),(self.c,'overlap')
  ground=[[self.under.get((x,y),'b')if ch=='#'else'.'if ch in '^f'else ch for x,ch in enumerate(row)]for y,row in enumerate(self.g)];base=[]
  for y,row in enumerate(ground):
   line=[]
   for x,ch in enumerate(row):
    v=B.seed(f'{self.c}:ch5finale:{x}:{y}')%4;tile=A.ground(ch,v)
    if ch in 'b=':tile=A.edge(ch,B.mask_at(ground,x,y,lambda z:z in 'b=~'),v)
    line.append(tile)
   base.append(line)
  nature=[];rng=random.Random(B.seed(self.c+'deep-ch5'));allowed={(x,y)for y,row in enumerate(self.g)for x,t in enumerate(row)if t=='f'};used=set()
  for x,y in sorted(allowed,key=lambda p:(-sum((p[0]+dx,p[1]+dy)in allowed for dx in range(-1,3)for dy in range(-1,3)),p[1],p[0])):
   if(x,y)in used:continue
   for key in rng.sample(['pine_tall','pine_broad','pine_pair'],3):
    sw,sh=B.NATURE[key]['size'];foot={(xx,yy)for yy in range(y,y+math.ceil(sh/16))for xx in range(x,x+math.ceil(sw/16))}
    if foot<=allowed and not foot&(used|protected):nature.append({'key':key,'position':[x*16,y*16],'flip':rng.random()<.3});used|=foot;break
  for x,y in sorted(allowed-used-protected):nature.append({'key':rng.choice(['pine_small_a','pine_small_b','pine_young']),'position':[x*16,y*16],'flip':False})
  top=[[None]*self.w for _ in range(self.h)]
  self.d.update(map={'width':self.w,'height':self.h,'tiles':[IDS[t]for row in self.g for t in row]},logic_grid=[''.join(r)for r in self.g],visual_ground=[''.join(r)for r in ground],art_layers=[base,[[None]*self.w for _ in range(self.h)],top],art_modules=self.mods,art_props=self.props,natural_props=nature,art_atlas='res://assets/chapter5-redesign-20261022/finale/terrain.png',tactical_review_version='0.10.9-ch5',art_style_version='chapter5-redesign-20261022',tactical_routes=self.routes,tactical_notes=self.notes,visual_notes=self.notes,nature_layout={'biome':'grass','props':[],'excluded':[[0,0,self.w*16,self.h*16]]})
  self.d['production_anchors']={'revision':'0.10.9-ch5','deployment':self.d['player_positions'],'deploy':self.d['player_positions'],'targets':self.d['targets'],'exit':self.d['exit']}
  for group in ['enemies','npc_units','reinforcements']:
   assert len(self.old[group])==len(self.d[group])
   for a,b in zip(self.old[group],self.d[group]):assert{k:v for k,v in a.items()if k!='position'}=={k:v for k,v in b.items()if k!='position'},(self.c,'unit contract')
  for k in ['goal','before','during','after','optional','event_boats','clear_training_exp','reinforcement_turn','terrain','characters','summon_template']:assert self.old.get(k)==self.d.get(k),(self.c,k)
  side_checks=[]
  for side in ['alm','celica']:
   slots=self.d['player_positions_by_route'][side];assert len(slots)==10;connected=self.flood(slots[0]);assert all(tuple(p)in connected for p in anchors),(self.c,'disconnected from side',side)
   for o in self.d['objects']:assert tuple(o.get('approach',o['position']))in connected
   side_checks.append({'side':side,'candidate_count':10,'connected_cells':len(connected),'all_targets_and_other_side_reachable':True})
  assert self.d['player_positions']==self.d['player_positions_by_route']['alm']+self.d['player_positions_by_route']['celica'];assert sum(ch=='+'for row in self.g for ch in row)==2
  if self.c=='J54':assert self.g[10][16]not in '#^~'and(16,10)not in protected
  delta={}
  for k in ['player_positions','player_positions_by_route','exit','targets','objects','enemies','npc_units','reinforcements']:
   a=self.old[k];b=self.d[k]
   if k in ['enemies','npc_units','reinforcements']:a={u['id']:u['position']for u in a};b={u['id']:u['position']for u in b}
   delta[k]={'before':a,'after':b}
  report={'passed':True,'code':self.c,'size':[self.w,self.h],'coordinate_changes':delta,'joint_deployment_checks':side_checks,'stair_collisions':self.stairs,'landmarks':self.landmarks,'healing_tiles':2,'fixed_summon_source':[16,10]if self.c=='J54'else None,'notes':self.notes,'unit_identity_order_stats_AI_and_story_unchanged':True};write(R/f'data/stages/{self.c}.json',self.d);report['stage_sha256']=hashlib.sha256((R/f'data/stages/{self.c}.json').read_bytes()).hexdigest();write(O/f'{self.c}-design.json',report);return report
if __name__=='__main__':
 reports=[Field('J53',38,32).finish(),Field('J54',34,32).finish()];A.save();write(O/'design-summary.json',{'passed':True,'maps':reports});print(json.dumps([{'code':r['code'],'size':r['size'],'passed':r['passed'],'sha256':r['stage_sha256']}for r in reports],ensure_ascii=False,indent=2))
