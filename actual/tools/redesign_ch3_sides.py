#!/usr/bin/env python3
"""S31/S32: compact village detention courts and salt-road barracks.
Frozen narrative/unit rules; native 16 px props, independent terrain atlas.
"""
from pathlib import Path
from collections import deque
import copy,hashlib,importlib.util,json,math,random
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter3-redesign-20261022/sides';BASE=O.parent/'baseline';ART=R/'assets/chapter3-redesign-20261022/sides'
spec=importlib.util.spec_from_file_location('native_builder',R/'tools/redesign_ch1_camp_fort.py');N=importlib.util.module_from_spec(spec);spec.loader.exec_module(N)
N.BASE=BASE;N.O=O;N.ART=ART;N.L.ART=ART;A=N.L.Atlas();B=N.B;write=N.write
IDS={'.':48,',':48,'f':172,'^':94,'d':242,'~':96,'#':196,'=':208,'s':191,'b':48,'+':218,'c':208,'a':48}
MAT={'.':'grass',',':'dirt','f':'grass','^':'rock','d':'sand','~':'sea','#':'stone','=':'stone','s':'timber','b':'cobble','+':'sacred','c':'cobble','a':'salt'}
class Field(N.Field):
 def __init__(self,c,w,h):
  super().__init__(c,w,h);self.biome='.'if c=='S31'else'a';self.g=[list(self.biome*w)for _ in range(h)];self.cages=[]
 def path(self,ps,width=2,ch=',',name=''):super().path(ps,width,ch,name)
 def cage(self,index,x,y,npcs,back_barrack=False):
  self.rect(x,y,x+4,y+3,'c');self.tiles('jail_bars_h',x,y,[[481,482,482,482,483]]);self.tiles('jail_bars_v',x,y+1);self.tiles('jail_bars_v',x+4,y+1);self.tiles('jail_bars_h',x,y+3,[[481,482,None,482,483]])
  gx,gy=x+2,y+3;self.g[gy][gx]='#';self.under[gx,gy]='c';o=self.d['objects'][index];o.update(position=[gx,gy],opens=[[gx,gy]],open_art_cells=[{'position':[gx,gy],'base_tile':B.PACK['base']['cobble'][0],'clear_layers':[1,2]}])
  for uid,p in npcs.items():next(u for u in self.d['npc_units']if u['id']==uid)['position']=p
  self.cages.append({'object':o['id'],'bounds':[x,y,x+4,y+3],'door':[gx,gy],'front':[gx,gy+1],'npc_positions':npcs,'unique_passage':True})
  if back_barrack:self.stamp('barracks',x+1,y-2,self.biome,purpose='拘押营房后屋，南侧围院是唯一出入口')
 def village(self):
  self.poly([(0,0),(12,0),(13,2),(11,4),(6,3),(3,6),(0,7)],'^');self.poly([(13,0),(20,0),(20,2),(17,4),(17,8),(14,8),(12,5)],'^');self.poly([(26,0),(29,0),(29,13),(28,13),(28,4),(22,4),(21,2)],'^')
  self.poly([(0,15),(2,12),(4,13),(5,17),(3,20),(3,25),(0,25)],'f');self.poly([(13,17),(16,15),(18,17),(17,22),(14,25),(12,25),(13,21)],'f');self.poly([(23,20),(26,19),(29,20),(29,25),(21,25)],'f');self.poly([(24,11),(29,10),(29,18),(27,18),(25,15),(23,14)],'f')
  self.rect(16,7,21,11,'b')
  self.path([(8,25),(8,22),(9,22),(9,17),(11,17),(11,12),(18,12),(18,9),(25,9)],2,name='山村主街—山肩勤务道—东拘押院')
  self.path([(8,19),(4,19),(4,10),(8,10),(8,9)],1,name='西侧住户巷—西拘押院门前')
  self.path([(8,10),(11,10),(11,12)],1,name='两院间山肩横路')
  self.path([(10,21),(21,21),(21,16),(22,16),(22,12),(21,12),(21,9)],1,name='粮仓后巷—东山肩侧路')
  self.path([(18,9),(18,5),(21,5),(21,2)],2,name='狱卒值守台与山后出口')
  self.path([(4,14),(6,14)],1,name='西巷家屋门前');self.path([(18,15),(21,15),(21,16)],1,name='医舍门前');self.path([(19,19),(21,19)],1,name='粮仓门前');self.path([(20,6),(18,6)],1,name='哨楼门前')
  self.stamp('snow_cottage',5,17,'.',purpose='村口住屋');self.stamp('snow_cottage',10,19,'.',purpose='沿街住屋');self.stamp('fishing_cottage',5,12,'.',purpose='西巷家屋');self.stamp('hill_granary',18,17,'.',purpose='村民粮仓');self.stamp('village_clinic',17,13,'.',purpose='山村医舍');self.stamp('well',7,20,',',purpose='村井');self.stamp('ruined_watchtower',19,3,'.',purpose='山肩狱卒哨楼')
  self.cage(0,6,5,{'family0':[7,6]});self.cage(1,23,5,{'family1':[24,6]})
  self.stamp('camp_palisade',15,11,'.',purpose='狱卒院下侧短木障');self.stamp('crates',20,10,'b',purpose='值守院器材')
  self.update_positions({'S31_boss':[20,8],'S31_e1':[18,10],'S31_e2':[22,10],'S31_e3':[11,14],'S31_e4':[4,11],'S31_e5':[25,10],'S31_e6':[8,11],'S31_e7':[22,14],'S31_e8':[11,9]},[[8,22],[9,22],[10,22],[11,22],[8,23],[9,23],[10,23],[11,23],[7,23],[7,24]],[21,2])
  self.d['surroundings']='land';self.d['surroundings_biome']='grass';self.d['location_theme']='山村家屋沿井街聚居，山肩木障与两处拘押院围绕狱卒哨楼；西住户巷和东粮仓后路分开救援'
  self.notes=['村口住屋、井台、医舍和粮仓形成真实聚落；拘押院位于北侧山肩，狱卒哨楼朝向两院之间的勤务道。','可从西住户巷先救西院，或沿主街转入东山肩；粮仓后巷提供通向东院守军侧面的支路，两院都能由完整道路抵达。','两组家属各在独立封闭围院内，只有南侧牢门可进出；门的位置、开启地形和解锁名单同步，开门前可先清除门前守军。','两扇门均须开启且至少一组家属存活，再击败狱卒首领；蕾娜劝降旧部仍为可选手段，不依赖她出阵。']
 def salt(self):
  self.poly([(0,0),(9,0),(9,3),(6,4),(4,7),(0,8)],'^');self.poly([(27,0),(31,0),(31,10),(29,11),(28,8),(29,5),(26,3)],'^');self.poly([(0,17),(2,16),(3,20),(2,25),(0,25)],'^');self.poly([(28,20),(31,19),(31,25),(25,25),(25,23)],'^')
  self.poly([(11,0),(16,0),(17,3),(15,5),(11,4)],'d');self.poly([(13,17),(17,18),(18,22),(16,25),(12,25),(12,22)],'d');self.poly([(27,13),(31,12),(31,16),(28,18),(26,17)],'d')
  self.rect(17,6,26,10,'b');self.rect(9,13,15,17,',')
  self.path([(7,25),(7,21),(11,21),(11,16),(15,16),(15,10),(19,10),(19,8),(25,8),(25,5)],2,name='南营口—勤务井台—营长前庭')
  self.path([(7,21),(4,21),(4,12),(7,12),(7,11)],1,name='西营房外侧巡查路')
  self.path([(11,21),(23,21),(26,21),(26,17),(22,17)],2,name='东侧后勤路—居民营房南门')
  self.path([(26,18),(26,11),(25,11),(25,8)],1,name='后勤路北支—营长院东侧')
  self.path([(7,12),(11,12),(11,16)],1,name='术士营房接井台短路')
  self.path([(15,16),(18,16),(18,18),(22,18),(22,17)],1,name='两营房间横向勤务道')
  self.path([(25,5),(25,2)],2,name='北营出口')
  self.path([(23,5),(25,5)],1,name='指挥帐门前');self.path([(14,7),(14,10)],1,name='术士值守帐门前');self.path([(17,13),(15,13)],1,name='驻军帐门前')
  self.cage(0,5,7,{'noya':[6,8]},True);self.cage(1,20,13,{'noya_brother':[21,14],'salt_residents':[23,14]},True)
  self.stamp('command_pavilion',22,3,'a',purpose='北营指挥帐');self.stamp('command_pavilion',13,5,'a',purpose='术士值守帐');self.stamp('grain_store',19,20,'a',purpose='后勤粮仓');self.stamp('command_pavilion',16,11,'a',purpose='中央驻军帐');self.stamp('well',13,14,',',purpose='营地井台');self.stamp('crates',17,8,'b',purpose='北营箱垛')
  for x,y in[(9,18),(15,18),(2,14),(16,7),(27,11)]:self.stamp('camp_palisade',x,y,'a',purpose='分隔营区的短木障')
  self.update_positions({'S32_boss':[25,6],'S32_e1':[22,9],'S32_e2':[15,12],'S32_e3':[26,19],'S32_e4':[10,14],'S32_e5':[24,10],'S32_e6':[16,15],'S32_e7':[18,18],'S32_e8':[11,11]},[[6,22],[7,22],[8,22],[9,22],[6,23],[7,23],[8,23],[9,23],[5,23],[5,24]],[25,2])
  self.d['surroundings']='land';self.d['surroundings_biome']='salt';self.d['location_theme']='盐原井台旁的分区营盘：西侧术士拘押营房、东侧居民营房、中央驻军与北部指挥帐，后勤路绕营相接'
  self.notes=['西侧术士营房、东侧居民营房与北侧指挥帐分区明确，后屋与封闭前院相连；井台、粮仓和短木障形成营地生活与勤务关系。','正面经井台与中央驻军推进，也能由东西外侧巡查路分兵抵达两扇牢门；东后勤路继续通向指挥院侧面，不是只能原路折返的支路。','诺娅和居民均在独立围院中，唯一南门、打开地形和解锁名单完整对应；固定弓手与术士不覆盖被囚者初始位置，可先清门前威胁再开门。','两间营房都须打开、营长必须败北；诺娅、弟弟与居民分别保留真实生死记录，原问责、接纳与后续剧情不变。']
 def flood(self,start,opened=False):
  opens={tuple(p)for o in self.d['objects']for p in o.get('opens',[])};seen={tuple(start):0};q=deque([tuple(start)])
  while q:
   x,y=q.popleft()
   for dx,dy in[(0,-1),(1,0),(0,1),(-1,0)]:
    p=x+dx,y+dy
    if 0<p[0]<self.w-1 and 0<p[1]<self.h-1 and p not in seen and(self.g[p[1]][p[0]]not in '#^~'or(opened and p in opens)):seen[p]=seen[x,y]+1;q.append(p)
  return seen
 def check(self):
  r=super().check();r['cages']=self.cages;r['npc_fixed_enemy_safety']=[]
  for cage in self.cages:
   x0,y0,x1,y1=cage['bounds'];door=tuple(cage['door']);border={(x,y)for y in range(y0,y1+1)for x in range(x0,x1+1)if x in[x0,x1]or y in[y0,y1]}
   assert all(self.g[y][x]=='#'for x,y in border),'cage has accidental second opening'
   assert tuple(cage['front'])in self.flood(self.d['player_positions'][0]),'inaccessible door front'
   for uid,p in cage['npc_positions'].items():
    assert tuple(p)not in self.flood(self.d['player_positions'][0]),'locked captive has walk-in bypass'
    threats=[];distances=[]
    for e in self.d['enemies']:
     if e.get('behavior')!='guard':continue
     dist=abs(e['position'][0]-p[0])+abs(e['position'][1]-p[1]);safe=dist>3 # conservative for all fixed bows/spells, irrespective of walls
     distances.append({'enemy':e['id'],'distance':dist,'outside_three_tile_radius':safe})
     if not safe:threats.append(e['id'])
    assert not threats,(self.c,uid,'fixed enemy attack overlap',threats)
    r['npc_fixed_enemy_safety'].append({'npc':uid,'position':p,'passed':True,'guards':distances})
  r['source_rule_changes']='None: unit order/identity/attributes/AI/equipment and narrative/goal/timing preserved; only geometry and visual fields change.'
  return r
 def finish(self):
  self.village()if self.c=='S31'else self.salt();self.d['targets']=[o['position']for o in self.d['objects']if not o.get('optional',False)]
  anchors=self.d['player_positions']+[self.d['exit']]+[u['position']for u in self.d['enemies']+self.d['npc_units']+self.d['reinforcements']];protected={tuple(p)for p in anchors}
  for o in self.d['objects']:
   x,y=o['position'];protected.update((x+dx,y+dy)for dx,dy in[(0,1),(1,0),(-1,0),(0,-1)])
  for x,y in protected:
   if self.g[y][x]=='f':self.g[y][x]=self.biome
  for p in anchors:assert self.g[p[1]][p[0]]not in '#^~',(self.c,'blocked anchor',p,self.g[p[1]][p[0]])
  ground=[[self.under.get((x,y),self.biome)if ch=='#'else self.biome if ch in '^f'else ch for x,ch in enumerate(row)]for y,row in enumerate(self.g)];base=[]
  for y,row in enumerate(ground):
   line=[]
   for x,ch in enumerate(row):
    v=B.seed(f'{self.c}:ch3side:{x}:{y}')%4;mat=MAT[ch];tile=B.PACK['base'][mat][v]
    if ch!=self.biome:tile=A.edge(mat,MAT[self.biome],B.mask_at(ground,x,y,lambda z:z==ch),v)
    line.append(tile)
   base.append(line)
  nature=[];rng=random.Random(B.seed(self.c+'deep-ch3'))
  for ch in '^f':
   allowed={(x,y)for y,row in enumerate(self.g)for x,t in enumerate(row)if t==ch};used=set();large=['peak_low','crag_tall','ridge_bent','outcrop']if ch=='^'else['pine_tall','pine_broad','pine_pair'];small=['boulder']if ch=='^'else['pine_small_a','pine_small_b','pine_young']
   places=sorted(allowed,key=lambda p:(-sum((p[0]+dx,p[1]+dy)in allowed for dx in range(-1,3)for dy in range(-1,3)),p[1],p[0]))
   for x,y in places:
    if(x,y)in used:continue
    choices=large.copy();rng.shuffle(choices)
    for key in choices:
     sw,sh=B.NATURE[key]['size'];foot={(xx,yy)for yy in range(y,y+math.ceil(sh/16))for xx in range(x,x+math.ceil(sw/16))}
     if foot<=allowed and not foot&(used|protected):nature.append({'key':key,'position':[x*16,y*16],'flip':rng.random()<.35});used|=foot;break
   for x,y in sorted(allowed-used-protected):nature.append({'key':rng.choice(small),'position':[x*16,y*16],'flip':rng.random()<.35})
  top=[[None]*self.w for _ in range(self.h)]
  for mod in self.mods:
   if 'tiles'not in mod:continue
   x,y=mod['origin']
   for dy,row in enumerate(mod['tiles']):
    for dx,t in enumerate(row):top[y+dy][x+dx]=t
  self.d.update(map={'width':self.w,'height':self.h,'tiles':[IDS[t]for row in self.g for t in row]},logic_grid=[''.join(r)for r in self.g],visual_ground=[''.join(r)for r in ground],art_layers=[base,[[None]*self.w for _ in range(self.h)],top],art_modules=self.mods,art_props=self.props,natural_props=nature,art_atlas='res://assets/chapter3-redesign-20261022/sides/terrain.png',tactical_review_version='0.10.7-ch3',art_style_version='chapter3-redesign-20261022',tactical_routes=self.routes,tactical_notes=self.notes,visual_notes=self.notes,nature_layout={'biome':'grass'if self.c=='S31'else'salt','props':[],'excluded':[[0,0,self.w*16,self.h*16]]})
  self.d['production_anchors']={'revision':'0.10.7-ch3','deployment':self.d['player_positions'],'deploy':self.d['player_positions'],'targets':self.d['targets'],'exit':self.d['exit']}
  for group in ['enemies','npc_units','reinforcements']:
   assert len(self.old[group])==len(self.d[group])
   for a,b in zip(self.old[group],self.d[group]):assert{k:v for k,v in a.items()if k!='position'}=={k:v for k,v in b.items()if k!='position'},(self.c,'unit rules changed')
  for key in ['goal','before','during','after','optional','event_boats','clear_training_exp','reinforcement_turn','terrain','characters']:assert self.old.get(key)==self.d.get(key),(self.c,key)
  positions=[tuple(p)for p in anchors];assert len(positions)==len(set(positions)),(self.c,'anchor overlap')
  for old,new in zip(self.old['objects'],self.d['objects']):assert{k:v for k,v in old.items()if k not in ['position','opens','open_art_cells']}=={k:v for k,v in new.items()if k not in ['position','opens','open_art_cells']},'object semantics changed'
  report=self.check();write(R/f'data/stages/{self.c}.json',self.d);report['stage_sha256']=hashlib.sha256((R/f'data/stages/{self.c}.json').read_bytes()).hexdigest();write(O/f'{self.c}-design.json',report);return report
if __name__=='__main__':
 reports=[Field('S31',30,26).finish(),Field('S32',32,26).finish()];A.save();write(O/'design-summary.json',{'passed':True,'maps':reports});print(json.dumps([{'code':r['code'],'size':r['size'],'passed':r['passed'],'sha256':r['stage_sha256']}for r in reports],ensure_ascii=False,indent=2))
