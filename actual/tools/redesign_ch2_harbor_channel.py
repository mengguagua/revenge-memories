#!/usr/bin/env python3
"""F25/F26 only: a working bay port and two independent ship-safe channels."""
from pathlib import Path
from collections import deque
from PIL import Image
import copy,hashlib,importlib.util,json,math
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter2-redesign-20261022/harbor-channel';BASE=O.parent/'baseline';ART=R/'assets/chapter2-redesign-20261022/harbor-channel'
spec=importlib.util.spec_from_file_location('native_builder',R/'tools/redesign_ch1_camp_fort.py');N=importlib.util.module_from_spec(spec);spec.loader.exec_module(N)
N.O=O;N.BASE=BASE;N.ART=ART;N.L.ART=ART;N.A=N.L.Atlas();B=N.B
write=N.write
class Field(N.Field):
 def fort(self):
  if self.c=='F25':self.harbor()
  else:self.channel()
 def cage(self,x,y):
  self.rect(x+1,y+1,x+3,y+2,'c');self.tiles('jail_bars_h',x,y,[[481,482,482,482,483]]);self.tiles('jail_bars_v',x,y+1);self.tiles('jail_bars_v',x+4,y+1);self.tiles('jail_bars_h',x,y+3,[[481,482,None,482,483]])
  gx,gy=x+2,y+3;self.g[gy][gx]='#';self.under[gx,gy]='p';o=next(o for o in self.d['objects']if o['id']=='pilot_prison');o.update(position=[gx,gy],opens=[[gx,gy]],open_art_cells=[{'position':[gx,gy],'base_tile':B.PACK['base']['dirt'][0],'clear_layers':[1,2]}])
  self.d['npc_units'][0]['position']=[x+1,y+1];self.d['npc_units'][1]['position']=[x+3,y+1]
 def harbor(self):
  self.poly([(2,0),(30,0),(30,7),(25,8),(22,11),(20,15),(21,18),(24,19),(29,18),(30,24),(26,27),(5,27),(3,24),(2,18)],'.')
  self.poly([(2,0),(6,0),(6,3),(4,6),(2,7)],'^');self.poly([(3,8),(5,7),(6,10),(5,14),(2,16)],'f');self.poly([(3,22),(6,21),(8,24),(7,27),(4,27)],'f');self.poly([(24,0),(28,0),(28,2),(25,4),(23,2)],'f')
  self.rect(16,5,23,10,'c');self.rect(12,13,18,18,'p')
  self.path([(10,26),(10,20),(12,20),(12,13),(16,13),(16,8),(22,8),(22,5)],2,name='仓街—驻军院—主楼前庭')
  self.path([(6,22),(6,9),(10,9),(10,5),(17,5)],1,name='西侧仓房勤务道');self.path([(14,4),(16,4),(16,8)],1,name='账房南门短路')
  self.path([(14,23),(30,23),(30,6),(23,6)],2,'s','岸侧码头绕进东牢与主楼');self.path([(12,22),(14,22),(14,23)],2);self.path([(26,22),(30,22)],2,name='东牢南门接岸路')
  for y in range(6,25):
   for x in [30,31]:self.axes[x,y]='v'
  for y in [23,24]:
   for x in range(14,32):self.axes[x,y]='h'
  self.stamp('coastal_keep',18,1,'c',purpose='军港主楼');self.stamp('quay_warehouse',13,2,'.',purpose='港仓账房');self.stamp('quay_warehouse',7,10,'.',purpose='仓街西侧仓库');self.stamp('grain_store',11,7,'.',purpose='仓街北侧粮库');self.stamp('quay_warehouse',5,18,'.',purpose='临湾南仓')
  self.stamp('barracks',13,14,'p',purpose='驻军院营房');self.stamp('command_pavilion',17,16,'p',purpose='值守帐');self.stamp('crates',9,12,'p');self.stamp('crates',17,11,'c');self.stamp('camp_palisade',14,12,'p');self.stamp('camp_palisade',17,19,'.')
  self.cage(24,18)
  self.stamp('tactical_store',10,15,'p',occupiable='h',purpose='可驻守粮仓');self.stamp('tactical_store',28,17,'.',occupiable='h',purpose='可驻守港仓');self.stamp('tactical_tent',25,5,'.',occupiable='h',purpose='北哨军帐')
  self.sites=[{'position':[10,15],'label':'粮仓','occupiable':True,'avoid':20,'phase_heal':0},{'position':[28,17],'label':'港仓','occupiable':True,'avoid':20,'phase_heal':0},{'position':[25,5],'label':'军帐','occupiable':True,'avoid':20,'phase_heal':0}]
  self.d['objects'][0]['position']=[21,7]
  self.d['objects'][2].update(position=[14,3],approach=[14,4],approaches=[[14,4]],entrance_cells=[[14,3]])
  self.update_positions({'F25_boss':[22,6],'F25_e1':[24,8],'F25_e2':[17,14],'F25_e3':[23,22],'F25_e4':[10,6],'F25_e5':[23,8],'F25_e6':[20,15],'F25_e7':[28,22],'F25_e8':[12,5],'F25_e9':[27,7],'F25_e10':[17,13],'F25_e11':[30,16],'F25_e12':[8,8],'F25_e13':[30,11],'F25_e14':[21,17]},[[10,23],[11,23],[12,23],[13,23],[10,24],[11,24],[12,24],[13,24],[9,24],[9,25]],[27,3])
  self.d['surroundings']='sea';self.d['surroundings_biome']='sea';self.d['location_theme']='仓街与驻军院围住海湾，东侧引航者牢房接岸侧码头，北部主楼和证物前庭形成终点'
  self.notes=['军港按南仓入口、仓街、驻军院和北侧主楼逐层展开，主楼前神教箱与仓房账房都有明确的道路与门前空间。','陆路可以沿仓街推进；东侧连续木码头绕过湾内驻军院，连接引航者牢门外侧与北哨，形成独立的侧进路线。','两名引航者完整关在东牢围栏后，唯一南门、开门格与解锁名单同步；取箱、开门与击败裴萨的原胜利条件不变。']
 def channel(self):
  # A northern old road, a western landing and an eastern peninsula enclose the water.
  self.poly([(0,0),(37,0),(37,29),(34,29),(34,20),(31,20),(29,18),(25,18),(24,16),(21,17),(19,19),(15,19),(14,17),(11,18),(11,6),(9,5),(2,5),(2,12),(0,13)],'.')
  self.poly([(13,0),(21,0),(20,3),(17,4),(13,3)],'^');self.poly([(31,0),(37,0),(37,4),(34,5),(32,3)],'^');self.poly([(23,0),(28,0),(29,3),(28,6),(25,6),(23,3)],'f');self.poly([(14,6),(17,5),(20,7),(20,10),(18,12),(15,10)],'f');self.poly([(29,10),(32,8),(35,10),(35,15),(33,17),(30,15)],'f')
  self.path([(31,19),(28,19),(28,17),(22,17),(22,15),(16,15),(16,17),(12,17),(12,8),(10,8),(10,4),(4,4)],2,'c','沿岸古道—西岸石门')
  self.path([(30,18),(35,18),(35,26)],2,'p','东端泊口护卫路');self.path([(27,17),(27,12),(25,12),(25,8),(21,8),(21,5),(12,5),(10,5)],1,'p','遗迹内侧侧路')
  self.path([(2,4),(1,4),(1,11)],1,'c','西岸靠泊接应道');self.rect(10,5,13,8,'c');self.rect(34,22,36,27,'c')
  self.stamp('ancient_arch',3,0,'.',walk=[[4,1],[5,1],[4,2],[5,2],[4,3],[5,3]],purpose='西岸古石门')
  self.stamp('ruined_watchtower',18,11,'.',purpose='古道断壁岗楼');self.stamp('breached_wall',23,3,'.',purpose='航灯废台外墙');self.stamp('ritual_lamp',27,9,'.',purpose='古灯座');self.stamp('sea_cliff',8,0,'.',purpose='西岸石门旁断崖')
  self.d['objects'][0]['position']=[7,4];self.d['objects'][1]['position']=[26,11]
  self.update_positions({'F26_boss':[11,8],'F26_e1':[13,7],'F26_e2':[22,14],'F26_e3':[35,21],'F26_e4':[14,16],'F26_e5':[13,5],'F26_e6':[24,16],'F26_e7':[35,24],'F26_e8':[12,18],'F26_e9':[1,11],'F26_e10':[11,14],'F26_e11':[1,8]},[[29,18],[30,18],[31,18],[32,18],[29,19],[30,19],[31,19],[32,19],[28,19],[28,18]],[7,4])
  first=B.route([[32,23],[8,23],[8,8]]);second=B.route([[31,27],[4,27],[4,8]])
  for boat,path in zip(self.d['event_boats'],[first,second]):boat['path']=[list(p)for p in path];boat['position']=list(path[0])
  # There are no bridge pillars in either lane, including the full 32x48 sprite footprint.
  # Reef silhouette is moved into the island between channels, so it never clips a hull.
  self.d['surroundings']='sea';self.d['surroundings_biome']='sea';self.d['location_theme']='北岸断航古道护送西行居民船：外内两道宽水路、东泊口与西岸石门接应区'
  self.notes=['断航古道沿北岸通往左侧西岸石门，遗迹内侧小路提供绕过沿岸守军的选择；东泊口与西岸接应台均在陆上通路中。','两艘居民船使用分离的内、外水道，由东向西再沿西岸入泊。逐步航线都为真实水面，按完整船体留出宽度，停航或抵达后也不与另一船重叠。','岸边弓手、术士与封航首领仍会迫使船只停航并损伤射程内船体；玩家需要沿岸清路，不能用陆上桥梁代替航道。','船只仍延迟4/8回合、速度3、耐久30；至少一艘存活抵达且首领败北才胜利，原船队事件规则与人物动画保留。']
 def check(self):
  # Chapter-two doors have explicit opens rather than the chapter-one rescue-only convention.
  opens={tuple(p)for o in self.d['objects']for p in o.get('opens',[o['position']]if o['kind']in ['door','rescue']else[])}
  def flood(start,opened=False):
   seen={tuple(start):0};q=deque([tuple(start)])
   while q:
    x,y=q.popleft()
    for dx,dy in[(0,-1),(1,0),(0,1),(-1,0)]:
     p=x+dx,y+dy
     if 0<p[0]<self.w-1 and 0<p[1]<self.h-1 and p not in seen and(self.g[p[1]][p[0]]not in '#^~'or(opened and p in opens)):seen[p]=seen[x,y]+1;q.append(p)
   return seen
  closed=flood(self.d['player_positions'][0]);opened=flood(self.d['player_positions'][0],True)
  for p in self.d['player_positions']+[self.d['exit']]+[u['position']for u in self.d['enemies']+self.d['reinforcements']]:assert tuple(p)in closed,(self.c,'unreachable',p)
  for u in self.d['npc_units']:assert tuple(u['position'])in opened,(self.c,'unreachable NPC',u['id'])
  for o in self.d['objects']:
   x,y=o['position'];ps=o.get('approaches',[[x+dx,y+dy]for dx,dy in[(0,1),(1,0),(-1,0),(0,-1)]]if o.get('adjacent')else[[x,y]]);assert any(tuple(p)in closed for p in ps),(self.c,'inaccessible',o['id'])
  result={'code':self.c,'passed':True,'size':[self.w,self.h],'closed_connected':len(closed),'opened_connected':len(opened),'notes':self.notes,'coordinate_changes':{}}
  for key in ['player_positions','exit','targets','objects','event_boats','building_sites']:
   result['coordinate_changes'][key]={'before':self.old.get(key),'after':self.d.get(key)}
  for key in ['enemies','npc_units','reinforcements']:result['coordinate_changes'][key]={'before':{u['id']:u['position']for u in self.old[key]},'after':{u['id']:u['position']for u in self.d[key]}}
  if self.c=='F26':
   all_hulls=[];route_records=[]
   for old,new in zip(self.old['event_boats'],self.d['event_boats']):
    assert {k:v for k,v in old.items()if k not in ['path','position']}=={k:v for k,v in new.items()if k not in ['path','position']},'boat rules mutated'
    used=set()
    for i,(x,y)in enumerate(new['path']):
     if i:assert abs(x-new['path'][i-1][0])+abs(y-new['path'][i-1][1])==1
     hull={(xx,yy)for yy in range(y-2,y+1)for xx in range(x-1,x+2)}
     assert all(0<=xx<self.w and 0<=yy<self.h and self.g[yy][xx]=='~'for xx,yy in hull),(new['id'],'hull touches land',i,[x,y],[(xx,yy,self.g[yy][xx])for xx,yy in hull if self.g[yy][xx]!='~'])
     used|=hull
    all_hulls.append(used);route_records.append({'id':new['id'],'steps':len(new['path'])-1,'delay':new['delay'],'speed':new['speed'],'hp':new['hp'],'swept_water_cells':len(used),'sprite_bounds':'32x48; anchor offset(-8,-32), conservative hull x-1..x+1,y-2..y'})
   assert not all_hulls[0]&all_hulls[1],('boat paths may overlap even when stopped',all_hulls[0]&all_hulls[1]);result['boat_channels']={'disjoint_entire_swept_hulls':True,'routes':route_records}
  return result
 def finish(self):
  result=super().finish();self.d.update(art_atlas='res://assets/chapter2-redesign-20261022/harbor-channel/terrain.png',tactical_review_version='0.10.6-ch2',art_style_version='chapter2-redesign-20261022');self.d['production_anchors']['revision']='0.10.6-ch2';self.d['visual_notes']=self.notes
  write(R/f'data/stages/{self.c}.json',self.d);write(O/f'{self.c}-design.json',result);return result
if __name__=='__main__':
 reports=[Field('F25',34,28).finish(),Field('F26',38,30).finish()];N.A.save();write(O/'design-summary.json',{'passed':True,'maps':reports});print(json.dumps([{'code':r['code'],'size':r['size'],'connected':r['closed_connected'],'boat_channels':r.get('boat_channels')}for r in reports],ensure_ascii=False,indent=2))
