#!/usr/bin/env python3
"""F43/S42 rescue landscapes, native modules and frozen combat contracts."""
from pathlib import Path
from collections import deque
import copy,hashlib,importlib.util,json,math,random
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter4-redesign-20261022/rescue';BASE=O.parent/'baseline';ART=R/'assets/chapter4-redesign-20261022/rescue'
spec=importlib.util.spec_from_file_location('native_builder',R/'tools/redesign_ch1_camp_fort.py');N=importlib.util.module_from_spec(spec);spec.loader.exec_module(N);N.BASE=BASE;N.O=O;N.L.ART=ART;A=N.L.Atlas();B=N.B;write=N.write
IDS={'.':48,',':48,'f':172,'^':94,'d':242,'~':96,'#':196,'=':208,'s':191,'b':48,'+':218,'m':66}
MAT={'.':'grass',',':'dirt','f':'grass','^':'rock','d':'sand','~':'sea','#':'stone','=':'stone','s':'timber','b':'cobble','+':'sacred','m':'marsh'}
class Field(N.Field):
 def __init__(self,c,w,h):super().__init__(c,w,h);self.g=[list('~'*w)for _ in range(h)];self.berths=[];self.bridges=[]
 def path(self,ps,width=2,ch=',',name=''):super().path(ps,width,ch,name)
 def bridge(self,ps,width=2,name=''):
  self.path(ps,width,'s',name)
  for a,b in zip(ps,ps[1:]):
   axis='h'if a[1]==b[1]else'v'
   for x,y in B.route([a,b]):
    for yy in range(y-(width-1)//2,y+width//2+1):
     for xx in range(x-(width-1)//2,x+width//2+1):self.axes[xx,yy]=axis
  self.bridges.append({'waypoints':ps,'width':width,'name':name})
 def boat(self,x,y):
  m=B.MODULES['rowboat'];foot=[[xx,yy]for yy in range(y,y+3)for xx in range(x,x+2)]
  assert all(self.g[yy][xx]=='~'for xx,yy in foot),'boat must float entirely on water'
  self.props.append({'path':m['path'],'position':[x*16,y*16]});self.mods.append({'name':'rowboat','origin':[x,y],'footprint':[2,3],'cells':foot,'logic':'inherits_ground','runtime_prop':True,'purpose':'接应船泊在木码头侧真实水面'});self.berths.append({'boat_origin':[x,y],'water_footprint':foot})
 def healing(self,x,y):
  self.g[y][x]='+';self.props.append({'path':B.MODULES['flowers']['path'],'position':[x*16,y*16]});self.mods.append({'name':'flowers','origin':[x,y],'footprint':[1,1],'cells':[[x,y]],'logic':'inherits_ground','runtime_prop':True,'purpose':'原有单格恢复点，保持数量与恢复地形'})
 def marsh(self):
  self.poly([(1,1),(18,1),(21,3),(21,7),(17,10),(10,12),(8,16),(3,16),(1,12)],'m');self.poly([(28,13),(33,11),(33,24),(28,25),(25,21),(24,17)],'m');self.poly([(10,22),(14,21),(16,25),(15,27),(11,27)],'m')
  self.poly([(5,18),(8,17),(11,18),(13,21),(13,24),(10,26),(4,26),(3,23),(3,20)],'.');self.poly([(14,11),(18,10),(22,12),(23,16),(20,18),(15,18),(13,16)],'.');self.poly([(23,2),(30,1),(32,3),(32,7),(30,11),(27,12),(23,10),(22,6)],'.')
  # Narrow water channels prevent automatic escorts taking a poison shortcut.
  self.rect(3,17,13,17,'~');self.rect(11,10,21,11,'~');self.rect(21,1,22,10,'~')
  self.poly([(2,3),(5,2),(7,4),(7,7),(4,9),(2,7)],'f');self.poly([(12,2),(16,2),(17,4),(15,6),(12,5)],'f');self.poly([(29,17),(32,16),(32,21),(29,22),(28,20)],'f');self.poly([(14,24),(16,24),(16,27),(14,27)],'f')
  self.path([(7,24),(7,22),(10,22),(10,20)],2,name='南船口—第一干地上栈口');self.path([(16,17),(18,17),(18,14),(21,14),(21,13)],2,name='第二干地护送道');self.path([(26,10),(28,10),(28,8),(30,8),(30,3)],2,name='第三干地—东北古道口')
  self.bridge([(10,20),(16,20),(16,17)],2,'南干地至中央避难岛的木便桥');self.bridge([(21,13),(26,13),(26,10)],2,'中央岛至东北古道的高木栈');self.bridge([(4,19),(4,16)],1,'西湿地巡行支桥');self.bridge([(19,5),(23,5)],1,'北湿地至神官台的窄侧栈')
  self.path([(4,20),(7,20)],1,name='南岸候船棚门前');self.path([(26,6),(28,6),(28,8)],2,name='神官台南面与第三干地');self.path([(26,5),(26,6)],1);self.path([(3,22),(7,22)],2,'s','南侧小码头')
  self.stamp('fishing_cottage',5,18,'.',purpose='南干地候船棚');self.stamp('ruined_watchtower',24,2,'.',purpose='东北古道残塔');self.stamp('sun_altar',28,2,'.',purpose='神官高地祭台');self.stamp('crates',17,16,'.',purpose='中央干岛转运物资');self.healing(7,23)
  self.boat(1,22)
  for o,p in zip(self.d['objects'],[[8,21],[18,15],[28,9]]):o['position']=p
  self.update_positions({'F43_boss':[28,5],'F43_e1':[27,10],'F43_e2':[22,15],'F43_e3':[27,20],'F43_e4':[10,7],'F43_e5':[29,7],'F43_e6':[19,12],'F43_e7':[25,18],'F43_e8':[11,5],'F43_e9':[30,7]},[[9,21],[10,21],[11,21],[12,21],[9,22],[10,22],[11,22],[12,22],[9,23],[10,23]],[30,3])
  for u,p in zip(self.d['npc_units'],[[6,23],[6,24],[7,24]]):u['position']=p
  self.d['surroundings']='sea';self.d['surroundings_biome']='marsh';self.d['location_theme']='南岸候船棚、中央转运岛与东北古道高地由两段水上木栈接起，西湿地侧线通往神官祭台'
  self.notes=['南船口、中央转运岛、东北古道高地各有完整干岸，三处确认点沿接应路线依次推进；居民从正式队员后方出发。','真正水沟把撤离主线收束到两段高木栈，桥端均落在干岛；毒沼集中在西侧与东南侧，不把泥沼伪装成安全道路。','西侧湿地小桥可分队压制术士并接近北祭台，离开护送线须承担沼泽与孤军风险；主队可沿中央便桥保护居民。','神官区域保留固定(26,6)召唤源及空余生成格，原第三回合最多三召唤物、击败神官只移除指定召唤物、至少两组撤离规则不变。']
 def clinic(self):
  self.poly([(4,1),(10,1),(12,3),(16,2),(21,1),(27,2),(29,5),(27,10),(24,12),(18,11),(15,13),(10,12),(6,10),(3,6)],'m')
  self.poly([(17,2),(23,2),(27,4),(26,8),(23,10),(19,10),(16,7)],'.');self.poly([(5,3),(10,3),(12,6),(11,10),(7,10),(4,7)],'.')
  self.poly([(6,15),(11,14),(15,15),(19,14),(24,14),(27,17),(26,22),(22,24),(16,24),(13,22),(8,24),(4,24),(3,21),(4,18)],'.')
  self.poly([(4,4),(6,3),(7,5),(6,8),(4,7)],'f');self.poly([(12,4),(14,3),(16,6),(15,9),(12,8)],'f');self.poly([(25,5),(28,5),(28,9),(26,10),(25,8)],'f');self.poly([(23,20),(26,19),(26,22),(23,24),(21,23)],'f');self.poly([(11,15),(13,15),(14,17),(13,19),(11,18)],'f')
  self.path([(5,22),(8,22),(8,20),(14,20),(14,18),(21,18),(21,17)],2,name='西南接应船—诊疗院南侧转运路');self.path([(10,16),(10,18),(8,18),(8,20)],2,name='主桥南端护卫集结道');self.path([(24,17),(24,18),(21,18)],1,name='东侧栈道接诊疗院')
  self.path([(9,9),(10,9),(10,11)],2,name='西北岛护卫道');self.path([(19,8),(21,8),(21,5),(24,5),(24,10)],2,name='北端驻军岗路')
  self.bridge([(10,10),(10,16)],2,'北岛至诊疗院的主木桥');self.bridge([(24,10),(24,17)],1,'沿东岸绕进北岛的窄便桥');self.bridge([(3,22),(6,22)],2,'西南靠船木台')
  self.stamp('village_clinic',20,15,'.',purpose='诊疗屋，记录与南门对齐');self.stamp('fishing_cottage',16,21,'.',purpose='地方医者照护住屋');self.stamp('well',18,17,'.',purpose='诊疗院水井');self.stamp('medicine_wagon',15,18,'.',purpose='院内搬运药车');self.stamp('ruined_watchtower',20,2,'.',purpose='北端清洗队岗楼');self.stamp('crates',6,20,',',purpose='船口接应物资');self.healing(16,20);self.boat(1,21)
  self.path([(17,23),(17,24)],1,name='照护住屋门前')
  self.d['objects'][0]['position']=[5,22];self.d['objects'][1].update(position=[21,16],approach=[21,17])
  self.update_positions({'S42_boss':[22,6],'S42_e1':[26,3],'S42_e2':[17,2],'S42_e3':[8,2],'S42_e4':[23,8],'S42_e5':[24,4],'S42_e6':[20,9],'S42_e7':[9,8],'S42_e8':[24,9]},[[8,18],[9,18],[10,18],[10,17],[8,19],[9,19],[10,19],[9,17],[7,19],[7,20]],[4,22])
  for u,p in zip(self.d['npc_units'],[[20,18],[14,19],[19,20]]):u['position']=p
  self.d['surroundings']='sea';self.d['surroundings_biome']='marsh';self.d['location_theme']='水道分开北端追兵岛与南岸诊疗院，双桥连接护卫前线，病人沿南岸干路撤到西南接应船'
  self.notes=['诊疗屋、井台、药车和照护住屋组成南岸医疗院；两组病人位于护卫队后方，南侧转运路直接通西南接应船，不穿北端敌阵。','主木桥形成可保护诊疗处的前沿，东侧窄栈可绕到北端守军侧面；两桥完整跨过真实水沟，两端都有落脚地。','北端三名飞行敌保留第3回合压近时机，玩家需要先接住病人并守住诊疗院；赛琳留在院内，航行记录就在诊疗屋南门。','必须让两组病人存活并撤离、确认船边接应点并击败队长；赛琳生死与后续邀请原样记录，保留单格恢复点。']
 def flood(self,start):
  seen={tuple(start):0};q=deque([tuple(start)])
  while q:
   x,y=q.popleft()
   for dx,dy in[(0,-1),(1,0),(0,1),(-1,0)]:
    p=x+dx,y+dy
    if 0<p[0]<self.w-1 and 0<p[1]<self.h-1 and p not in seen and self.g[p[1]][p[0]]not in '#^~':seen[p]=seen[x,y]+1;q.append(p)
  return seen
 def finish(self):
  self.marsh()if self.c=='F43'else self.clinic();self.d['targets']=[o['position']for o in self.d['objects']]
  anchors=self.d['player_positions']+[self.d['exit']]+[u['position']for u in self.d['enemies']+self.d['npc_units']+self.d['reinforcements']];protected={tuple(p)for p in anchors}
  for o in self.d['objects']:
   protected.update(tuple(p)for p in o.get('approaches',[o['approach']]if 'approach'in o else[o['position']]))
  for x,y in protected:
   assert 0<x<self.w-1 and 0<y<self.h-1,(self.c,'outer anchor',x,y)
   if self.g[y][x]=='f':self.g[y][x]='.'
  for p in anchors:assert self.g[p[1]][p[0]]not in '#^~',(self.c,'blocked anchor',p,self.g[p[1]][p[0]])
  ground=[[self.under.get((x,y),'.')if ch=='#'else'.'if ch in '^f'else ch for x,ch in enumerate(row)]for y,row in enumerate(self.g)];base=[]
  for y,row in enumerate(ground):
   line=[]
   for x,ch in enumerate(row):
    v=B.seed(f'{self.c}:ch4rescue:{x}:{y}')%4;mat=MAT[ch];tile=B.PACK['base'][mat][v]
    if ch in ',b=+':tile=A.edge(mat,'grass',B.mask_at(ground,x,y,lambda z:z==ch),v)
    if ch=='~':tile=A.water([MAT[ground[y+dy][x+dx]]if 0<=x+dx<self.w and 0<=y+dy<self.h else'sea'for dx,dy in[(0,-1),(1,0),(0,1),(-1,0)]],v)
    if ch=='s':
     mask=sum(bit for dx,dy,bit in[(0,-1,1),(1,0,2),(0,1,4),(-1,0,8)]if 0<=x+dx<self.w and 0<=y+dy<self.h and ground[y+dy][x+dx]=='s');tile=A.trans['walkway'][self.axes.get((x,y),'h')+str(mask)][v]
    line.append(tile)
   base.append(line)
  nature=[];rng=random.Random(B.seed(self.c+'deep-ch4'))
  for ch in '^f':
   allowed={(x,y)for y,row in enumerate(self.g)for x,t in enumerate(row)if t==ch};used=set();large=['peak_low','crag_tall','ridge_bent','outcrop']if ch=='^'else['pine_tall','pine_broad','pine_pair'];small=['boulder']if ch=='^'else['pine_small_a','pine_small_b','pine_young']
   for x,y in sorted(allowed,key=lambda p:(-sum((p[0]+dx,p[1]+dy)in allowed for dx in range(-1,3)for dy in range(-1,3)),p[1],p[0])):
    if(x,y)in used:continue
    choices=large.copy();rng.shuffle(choices)
    for key in choices:
     sw,sh=B.NATURE[key]['size'];foot={(xx,yy)for yy in range(y,y+math.ceil(sh/16))for xx in range(x,x+math.ceil(sw/16))}
     if foot<=allowed and not foot&(used|protected):nature.append({'key':key,'position':[x*16,y*16],'flip':rng.random()<.35});used|=foot;break
   for x,y in sorted(allowed-used-protected):nature.append({'key':rng.choice(small),'position':[x*16,y*16],'flip':rng.random()<.35})
  top=[[None]*self.w for _ in range(self.h)]
  for m in self.mods:
   if 'tiles'not in m:continue
   for dy,row in enumerate(m['tiles']):
    for dx,t in enumerate(row):top[m['origin'][1]+dy][m['origin'][0]+dx]=t
  self.d.update(map={'width':self.w,'height':self.h,'tiles':[IDS[t]for row in self.g for t in row]},logic_grid=[''.join(r)for r in self.g],visual_ground=[''.join(r)for r in ground],art_layers=[base,[[None]*self.w for _ in range(self.h)],top],art_modules=self.mods,art_props=self.props,natural_props=nature,art_atlas='res://assets/chapter4-redesign-20261022/rescue/terrain.png',tactical_review_version='0.10.8-ch4',art_style_version='chapter4-redesign-20261022',tactical_routes=self.routes,tactical_notes=self.notes,visual_notes=self.notes,nature_layout={'biome':'marsh','props':[],'excluded':[[0,0,self.w*16,self.h*16]]})
  self.d['production_anchors']={'revision':'0.10.8-ch4','deployment':self.d['player_positions'],'deploy':self.d['player_positions'],'targets':self.d['targets'],'exit':self.d['exit']}
  for group in ['enemies','npc_units','reinforcements']:
   assert len(self.old[group])==len(self.d[group])
   for a,b in zip(self.old[group],self.d[group]):assert{k:v for k,v in a.items()if k!='position'}=={k:v for k,v in b.items()if k!='position'},(self.c,'unit rules changed')
  for k in ['goal','before','during','after','optional','event_boats','clear_training_exp','reinforcement_turn','terrain','characters','summon_template']:assert self.old.get(k)==self.d.get(k),(self.c,k)
  positions=[tuple(p)for p in anchors];assert len(positions)==len(set(positions)),(self.c,'anchor overlap')
  connected=self.flood(self.d['player_positions'][0])
  for p in anchors:assert tuple(p)in connected,(self.c,'disconnected',p)
  for o in self.d['objects']:
   p=o.get('approach',o['position']);assert tuple(p)in connected,(self.c,'unreachable interaction',o['id'])
  assert sum(ch=='+'for row in self.g for ch in row)==1
  if self.c=='F43':assert self.g[6][26]not in '#^~m' and(26,6)not in protected,'fixed summon source must be dry, unoccupied and inside shrine'
  delta={}
  for k in ['player_positions','exit','targets','objects','enemies','npc_units','reinforcements']:
   a=self.old[k];b=self.d[k]
   if k in ['enemies','npc_units','reinforcements']:a={u['id']:u['position']for u in a};b={u['id']:u['position']for u in b}
   delta[k]={'before':a,'after':b}
  report={'passed':True,'code':self.c,'size':[self.w,self.h],'connected':len(connected),'coordinate_changes':delta,'bridges':self.bridges,'berths':self.berths,'notes':self.notes,'unit_stats_ai_timing_identity_unchanged':True,'healing_tiles':1,'fixed_summon_source':[26,6]if self.c=='F43'else None}
  write(R/f'data/stages/{self.c}.json',self.d);report['stage_sha256']=hashlib.sha256((R/f'data/stages/{self.c}.json').read_bytes()).hexdigest();write(O/f'{self.c}-design.json',report);return report
if __name__=='__main__':
 reports=[Field('F43',34,28).finish(),Field('S42',30,26).finish()];A.save();write(O/'design-summary.json',{'passed':True,'maps':reports});print(json.dumps([{'code':r['code'],'size':r['size'],'passed':r['passed'],'sha256':r['stage_sha256']}for r in reports],ensure_ascii=False,indent=2))
