#!/usr/bin/env python3
"""Chapter-four landscape, reproducible from frozen 2026-10-22 stage cards.
All campaign anchors and rules remain exact; native bitmap modules keep scale.
"""
from pathlib import Path
from collections import deque
from PIL import Image
import copy,hashlib,importlib.util,json,math,random,subprocess
R=Path(__file__).resolve().parents[1];BASE=R/'reports/map-polish-late-20261022/baseline';OUT=R/'reports/map-polish-late-20261022/chapter4';ART=R/'assets/map-polish-late-20261022/chapter4'
spec=importlib.util.spec_from_file_location('landtools',R/'tools/redesign_battlefields.py');B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B)
spec=importlib.util.spec_from_file_location('masktools',R/'tools/build_world_tiles.py');W=importlib.util.module_from_spec(spec);spec.loader.exec_module(W)
IDS={'.':48,',':48,'f':172,'^':94,'d':242,'~':96,'#':196,'=':208,'s':191,'b':48,'+':218,'c':208,'a':48,'n':48,'m':66}
MAT={'.':'grass',',':'dirt','f':'grass','^':'rock','d':'sand','~':'sea','#':'cobble','=':'stone','s':'timber','b':'cobble','+':'sacred','c':'cave','a':'salt','n':'snow','m':'marsh'}
CODES='M41 M42 M43 M44 F41 F42 F43 F44 S41 S42'.split();SNOW={'M41','M43','S41'}
write=lambda p,v:(p.parent.mkdir(parents=True,exist_ok=True),p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n'))
class Atlas:
 def __init__(self):
  old=json.loads((R/'assets/battlefield-0.3.0/terrain.json').read_text());im=Image.open(R/'assets/battlefield-0.3.0/terrain.png').convert('RGBA')
  self.cells=[im.crop((i%32*16,i//32*16,i%32*16+16,i//32*16+16))for i in range(old['tile_count'])];self.trans=old['transitions'];self.add={};self.shores={};self.original=len(self.cells)
 def edge(self,fg,bg,mask,v):
  key=f'{fg}:{bg}:{mask}'
  if key not in self.add:
   ids=[]
   for n in range(4):
    back=self.cells[B.PACK['base'][bg][n]].copy();front=(self.cells[self.trans['mountain_ground']['grass']['255'][n]] if fg=='rock' else self.cells[B.PACK['base'][fg][n]]).copy();front.putalpha(W.alpha_mask(mask));back.alpha_composite(front);ids.append(len(self.cells));self.cells.append(back)
   self.add[key]=ids
  return self.add[key][v]
 def water(self,neighbors,v):
  key=':'.join(neighbors)
  if key not in self.shores:
   ids=[]
   for n in range(4):
    im=self.cells[B.PACK['base']['sea'][n]].copy()
    for side,mat in enumerate(neighbors):
     if mat in ['sea','timber']:continue
     land=self.cells[self.trans['mountain_ground']['grass']['255'][n]] if mat=='rock' else self.cells[B.PACK['base'][mat][n]]
     for span in range(16):
      for dep in range(2):
       x,y=[(span,dep),(15-dep,span),(span,15-dep),(dep,span)][side];r,g,b,a=land.getpixel((x,y));im.putpixel((x,y),(int(r*(.85 if dep else 1)),int(g*(.85 if dep else 1)),int(b*(.85 if dep else 1)),a))
    ids.append(len(self.cells));self.cells.append(im)
   self.shores[key]=ids
  return self.shores[key][v]
 def save(self):
  ART.mkdir(parents=True,exist_ok=True);im=Image.new('RGBA',(512,math.ceil(len(self.cells)/32)*16))
  for i,t in enumerate(self.cells):im.paste(t,(i%32*16,i//32*16))
  p=ART/'terrain.png';im.save(p);subprocess.run(['/opt/homebrew/bin/oxipng','-o','3','--quiet',str(p)],check=True)
  write(ART/'terrain.json',{'tile_count':len(self.cells),'original_ids_preserved':self.original,'native_tile_size':16,'additional_transitions':self.add,'water_banks':self.shores,'purpose':'Native landscape transitions for chapter four; original atlas pixels and module IDs exact.','size':list(im.size),'bytes':p.stat().st_size,'quality_note':'Lossless PNG; native pixel detail retained, independent atlas avoids modifying approved chapters.'})
A=Atlas()
class Field:
 def __init__(self,c):
  self.c=c;self.old=json.loads((BASE/(c+'.json')).read_text());self.d=copy.deepcopy(self.old);self.w=self.d['map']['width'];self.h=self.d['map']['height'];self.g=[list(r)for r in self.old['logic_grid']];self.base='n' if c in SNOW else 'd' if c=='F41' else 'a' if c=='F42' else 'm' if c in ['F43','S42'] else '~' if c=='F44' else '.'
  self.struct={(x,y)for y,row in enumerate(self.g)for x,ch in enumerate(row)if ch=='#'};self.anchors={tuple(p)for p in self.old['player_positions']+[self.old['exit']]+[u['position']for u in self.old['enemies']+self.old['npc_units']+self.old['reinforcements']]};self.protected=set(self.anchors);self.routes=[];self.added=[];self.bridge_axes={};self.under={};self.notes=[]
  for o in self.d['objects']:
   x,y=o['position'];self.protected.add((x,y));self.protected.update(tuple(p)for p in o.get('approaches',[o['approach']]if 'approach'in o else[]))
   if o.get('adjacent'):self.protected.update((x+dx,y+dy)for dx,dy in[(1,0),(-1,0),(0,1),(0,-1)])
  for m in self.old['art_modules']:
   if m.get('logic')=='inherits_ground':self.protected.update(tuple(p)for p in m['cells'])
  for y,row in enumerate(self.g):
   for x,ch in enumerate(row):
    if (x,y)not in self.struct and ch!='+':self.g[y][x]=self.base
 def rect(self,x0,y0,x1,y1,ch,only=None):
  for y in range(max(0,int(y0)),min(self.h,int(y1)+1)):
   for x in range(max(0,int(x0)),min(self.w,int(x1)+1)):
    if (x,y)in self.struct:self.under[(x,y)]=ch if ch not in '#^~f' else self.base;continue
    if self.g[y][x]=='+':continue
    if ch in '^#~f' and (x,y)in self.protected:continue
    if ch==',' and self.g[y][x]=='b':continue
    if only is None or self.g[y][x]in only:self.g[y][x]=ch
 def ellipse(self,cx,cy,rx,ry,ch,only=None):
  for y in range(max(0,int(cy-ry-1)),min(self.h,int(cy+ry+2))):
   for x in range(max(0,int(cx-rx-1)),min(self.w,int(cx+rx+2))):
    if ((x-cx)/rx)**2+((y-cy)/ry)**2<1+.10*math.sin(x*.8+y*.6):self.rect(x,y,x,y,ch,only)
 def path(self,points,width=2,ch=',',name=''):
  for x,y in B.route(points):self.rect(x-width//2,y-width//2,x+(width-1)//2,y+(width-1)//2,ch)
  self.routes.append({'name':name,'waypoints':points,'width':width,'surface':ch})
 def bridge(self,x0,y0,x1,y1,axis):
  self.rect(x0,y0,x1,y1,'s')
  for y in range(y0,y1+1):
   for x in range(x0,x1+1):self.bridge_axes[(x,y)]=axis
 def stamp(self,name,x,y,ground=None):
  m=B.MODULES[name];fw,fh=m['footprint'];cells={(xx,yy)for yy in range(y,y+fh)for xx in range(x,x+fw)}
  if x<0 or y<0 or x+fw>self.w or y+fh>self.h or cells&(self.struct|self.protected):raise AssertionError((self.c,name,'blocked footprint',cells&(self.struct|self.protected)))
  for xx,yy in cells:self.under[(xx,yy)]=ground or self.g[yy][xx];self.g[yy][xx]='#'
  self.struct|=cells;self.d['art_props'].append({'path':m['path'],'position':[x*16,y*16]});self.d['art_modules'].append({'name':name,'origin':[x,y],'footprint':[fw,fh],'cells':[list(p)for p in sorted(cells)],'logic':'#','runtime_prop':True});self.added.append({'name':name,'origin':[x,y]})
 def boat_berth(self,x,y,water_y0,water_y1):
  self.rect(x,water_y0,x+1,water_y1,'~')
  for m in self.d['art_modules']:
   if m['name']=='rowboat':
    m['origin']=[x,y];m['cells']=[[xx,yy]for yy in range(y,y+3)for xx in range(x,x+2)]
 def design(self):
  c=self.c
  if c=='M41':
   for p in [(0,5,2.7,9),(31,6,3.3,10),(1,24,3.4,7),(30,25,2.9,7)]:self.ellipse(*p,'^')
   for p in [(11,2,2.5,3),(5,10,3,4),(12,14,3,4),(4,22,2,2),(22,8,3,2),(22,24,3,2)]:self.ellipse(*p,'f',only='n')
   self.path([(8,0),(8,11),(9,11),(9,18),(7,18),(7,25)],2,'~','峡谷融雪溪')
   self.path([(5,4),(16,4),(16,24)],3,',','村道至南口');self.path([(4,22),(25,22),(25,6),(16,6)],2,',','东侧巡行路');self.path([(16,13),(25,13)],2,',','伤者接驳支路');self.path([(12,9),(16,9)],2,',','西屋门前');self.path([(21,3),(21,4)],2,',');self.path([(21,19),(21,22)],2,',')
   self.rect(17,12,21,14,',');self.rect(13,20,18,25,',');self.bridge(7,3,9,4,'h');self.bridge(6,21,8,22,'h')
   self.notes=['融雪溪顺峡谷贯通南北，两座横向木桥分别接北村与南口，桥面两端均落在村道上。','雪松集中成林，岩壁形成峡口轮廓；村舍南门、医舍停靠点与东侧巡逻路各有明确支路。','南口部署、三组居民、伤者停靠点与追兵入口原位保留，居民可沿连贯道路向南撤离。']
  elif c=='M42':
   for p in [(1,3,4,5),(30,12,3,6),(1,25,4,5)]:self.ellipse(*p,'^')
   for p in [(7,3,4,3),(4,17,2,4),(12,8,2,2),(22,23,4,2),(29,26,2,2),(16,1,3,2)]:self.ellipse(*p,'f',only='.')
   self.path([(4,24),(16,24),(16,5),(28,5)],3,',','纵贯军道');self.path([(7,24),(7,13),(26,13),(26,23),(29,23)],3,',','骑兵营外圈');self.path([(10,17),(10,13)],2,',','旧同袍接洽路')
   self.rect(12,12,21,18,'b');self.path([(24,4),(24,7),(27,7)],3,'b');self.rect(23,16,27,18,',');self.path([(16,24),(29,24)],2,',')
   self.path([(4,12),(7,12)],2,',');self.path([(11,22),(16,22)],2,',');self.stamp('command_pavilion',4,10);self.stamp('command_pavilion',10,20);self.stamp('crates',19,19);self.stamp('camp_palisade',11,0);self.stamp('camp_palisade',20,20)
   self.notes=['贯通南北的宽军道通向北侧关堡；西侧骑兵环道与东侧营地支路形成可迂回的关卡。','投送站位于独立铺石后勤院，仓房、营帐和货箱沿院缘布置，驻军与旧同袍各有可辨识的集结区域。','旧同袍交涉、投送站和营地登记坐标不变，原骑兵与增援入口保持连通。']
  elif c=='M43':
   for p in [(0,6,4.8,10),(27,10,3.1,12),(2,26,4,3)]:self.ellipse(*p,'^')
   for p in [(7,2,3,3),(13,1,3,2),(4,14,2,3),(14,24,3,3),(24,25,3,2)]:self.ellipse(*p,'f',only='n')
   self.rect(8,6,23,15,'b');self.rect(10,16,23,21,'b');self.path([(4,24),(10,24),(10,14),(21,14),(21,4)],3,'b','登塔主路');self.path([(10,14),(10,8),(21,8)],2,'b','外院巡行路');self.path([(7,19),(10,19)],2,',');self.path([(19,19),(23,19),(23,8)],2,'b')
   self.rect(12,8,15,11,'n');self.ellipse(13.5,9.5,1.5,1.5,'f',only='n');self.rect(17,14,19,15,'n');self.rect(9,16,10,20,',')
   self.stamp('snow_cottage',11,19,ground='n');self.stamp('ritual_lamp',8,5,ground='n');self.stamp('ritual_lamp',24,16,ground='n')
   self.notes=['日塔坐落于两侧雪崖之间，铺石主路接入外院，塔脚留出前庭与环行通道。','西侧医舍、东侧控制工房形成独立服务院，覆雪花圃和灯柱分开战斗区域，避免整片无层次的石地。','外院旗位、病人、工匠及控制室南侧读档位置不变，尚未取得观测步骤时仍能完成夺塔。']
  elif c=='M44':
   self.rect(0,0,31,7,'b');self.rect(2,10,29,25,'b');self.path([(4,24),(17,24),(17,3),(29,3)],3,'=','城门主街');self.path([(5,17),(26,17),(26,6),(17,6)],3,'=','医舍环街');self.path([(7,14),(7,17)],2,',');self.path([(10,21),(10,24)],2,',');self.path([(21,22),(21,24)],2,',')
   for p in [(1,18,1.5,6),(30,16,1.6,5),(2,2,2,2),(10,2,2,2),(28,26,2,2)]:self.ellipse(*p,'f',only='.b')
   self.rect(8,10,12,15,'.');self.rect(19,12,20,15,'.');self.rect(12,19,15,21,'.');self.rect(23,23,24,25,'.')
   self.stamp('fishing_cottage',3,19,ground='b');self.stamp('fishing_cottage',11,11,ground='.');self.stamp('village_clinic',4,1,ground='b');self.stamp('quay_warehouse',18,1,ground='b');self.stamp('crates',7,15,ground='b')
   self.notes=['城墙与四格正门作为明确前后界线，南侧民居、仓储街、伤兵医舍分别围绕主街组织。','北侧留出门内集结广场，城堡前路与门楼衔接；街角绿地、屋门前的小路与边缘林带减少大面积重复铺砖。','门楼占领、伤兵后撤门、赫兰投降判定与增援保持原位；屋顶和城墙不能通行，入口及巷道均可到达。']
  elif c=='F41':
   for p in [(1,3,3,5),(30,20,2.6,5),(2,26,3,3)]:self.ellipse(*p,'^')
   self.rect(4,4,9,8,'b');self.rect(16,17,22,22,'b');self.path([(5,21),(5,6),(25,6),(25,20),(5,20)],2,',','双井街');self.path([(5,13),(25,13)],3,',','沙城横街');self.path([(19,20),(19,13),(14,13),(14,6)],2,',','取水路');self.path([(26,3),(26,6)],2,',');self.rect(15,21,20,24,',')
   self.stamp('fishing_cottage',8,10,ground='d');self.stamp('fishing_cottage',15,8,ground='d');self.stamp('fishing_cottage',7,15,ground='d');self.stamp('quay_warehouse',25,9,ground='d');self.stamp('crates',27,14,ground='d')
   self.notes=['沙城以两处铺石井院为生活中心，取水路连接井台与民居，横街供部队穿行和调防。','外围沙丘岩脊、紧凑的住屋组和仓房围成街区；井口保持实体，南侧取水台清楚可站。','南井首回合布防和分兵夺北井的原距离保持，敌军连续占井一轮才失守的规则不变。']
  elif c=='F42':
   for p in [(1,4,3,5),(26,19,3,6),(1,24,2,4),(10,1,3,2)]:self.ellipse(*p,'^')
   self.rect(9,6,23,17,'b');self.rect(7,18,23,21,'b');self.path([(4,24),(10,24),(10,14),(23,14),(23,4)],3,'b','观测台石路');self.path([(10,14),(10,7),(22,7)],2,'b','观测环廊');self.rect(12,7,15,9,'a');self.rect(18,14,21,16,'a');self.path([(7,19),(10,19)],2,',');self.rect(20,11,24,13,'b');self.rect(13,14,17,16,'b')
   self.stamp('ritual_lamp',9,5,ground='a');self.stamp('ritual_lamp',24,5,ground='a');self.stamp('ancient_arch',1,12,ground='a');self.stamp('crates',7,21,ground='a')
   self.notes=['盐原上的观测院采用磨旧石路和裸露盐地交错，主设备、东楼档案与北侧值守堡各有明确前庭。','成组岩脊围出高台边缘，旧石拱、对称灯柱与抄录工住屋交代遗址和维护区域，保持低饱和度。','东楼记录南侧读取格与中央设备确认格原位保留，焚毁兵出发时机和保护记录任务不变。']
  elif c=='F43':
   for p in [(1,5,4,7),(28,13,5,3),(12,26,3,3),(23,18,2,2)]:self.ellipse(*p,'~')
   for p in [(5,23,4,3),(6,13,3,6),(16,16,4,3),(23,7,6,3),(27,3,4,3)]:self.ellipse(*p,',')
   self.path([(4,24),(7,24),(7,17),(16,17),(16,8),(28,8),(28,3)],2,',','三处干地古道');self.path([(7,17),(7,8),(16,8)],2,',','西侧干地旁路');self.path([(18,21),(18,17)],2,',')
   self.rect(2,22,6,26,'s');self.bridge(9,16,12,17,'h');self.bridge(15,10,16,12,'v');self.bridge(17,7,19,8,'h')
   for p in [(3,14,2,3),(11,3,2,2),(11,19,2,2),(22,23,3,2),(30,7,2,2)]:self.ellipse(*p,'f',only='m')
   self.notes=['毒沼由不规则水洼、抬高干岛和木栈连接，第一、第二、第三干地沿连续古道依次可见。','木栈只铺在湿地间的窄段，接地端各有足够落脚地；船口与北侧旧瞭望塔明确标出进入和离开方向。','毒沼材质和原伤害保留，居民与干地确认点原位；护送路线保持干燥连续，并保留西侧绕行选择。']
  elif c=='F44':
   self.rect(4,3,28,23,'b');self.rect(1,21,7,26,'s');self.rect(11,5,18,10,'~');self.rect(19,18,24,24,'~');self.rect(5,4,6,8,'~');self.rect(27,14,28,17,'~');self.path([(4,24),(10,24),(10,9),(25,9),(25,4)],3,'b','西廊至神门');self.path([(10,14),(25,14),(25,22),(10,22)],3,'b','调节庭环廊');self.path([(10,14),(16,14)],3,'=');self.path([(25,14),(25,17)],2,'=');self.path([(10,9),(10,11)],2,'=')
   self.rect(4,12,7,16,'a');self.rect(20,5,22,6,'a');self.rect(12,18,15,20,'a');self.rect(16,6,18,8,'~');self.rect(12,6,18,10,'~');self.bridge(11,7,19,8,'h');self.stamp('ritual_lamp',6,17,ground='b');self.stamp('ritual_lamp',27,10,ground='b');self.stamp('crates',6,20,ground='b')
   self.notes=['沉没祭所由中央调节庭、两座下陷水院和外圈石廊组成；西侧小码头接主入口，北侧神门构成视觉终点。','水院岸线直接落在真实水格内，局部木便桥横跨北池；残留盐渍平台与成对灯柱增强遗址层次。','三处调节点及工匠位置不变，沿外环可完成全部交接；维修等待、守兽与条件增援规则保持。']
  elif c=='S41':
   for p in [(1,3,2,4),(23,18,2,5)]:self.ellipse(*p,'^')
   for p in [(9,2,3,2),(2,8,2,2),(21,10,2,3),(10,20,3,2),(11,10,1,2)]:self.ellipse(*p,'f',only='n')
   self.path([(4,18),(12,18),(12,5),(20,5)],2,',','村口至钟楼');self.path([(6,15),(19,15),(19,10),(15,10),(12,10)],2,',','名册屋与避难院');self.path([(5,5),(9,5),(12,5)],2,',');self.path([(16,19),(16,20),(12,20),(12,18)],2,',');self.rect(6,13,9,15,',');self.rect(13,10,18,11,',')
   self.path([(2,16),(6,16),(6,15)],2,',');self.path([(21,20),(16,20)],2,',');self.stamp('snow_cottage',1,14,ground='n');self.stamp('snow_cottage',20,18,ground='n');self.stamp('crates',6,6,ground='n')
   self.notes=['黑钟村形成钟楼前街、名册屋前院与西侧避难院，覆雪住屋集中在道路两旁而非散落空地。','林带包围村缘并留出视线，所有房屋正门都有短路接入主街，南侧另设回村支路。','名册读取、同袍对话与避难院坐标不变，焚毁支线损失仍不阻断主线。']
  else:
   for p in [(0,4,5,7),(23,14,4,4),(11,21,3,3),(23,0,3,1.5),(14,0,6,1.2),(22,21,3,2)]:self.ellipse(*p,'~')
   for p in [(5,18,4,3),(8,12,3,4),(16,13,5,4),(18,5,5,4)]:self.ellipse(*p,',')
   self.path([(4,19),(6,19),(6,17),(11,17),(11,13),(18,13),(18,5),(20,5)],2,',','病人转运路');self.path([(6,17),(6,8),(19,8),(19,4)],2,',','岛缘护卫路');self.path([(18,17),(18,13)],2,',');self.rect(2,16,6,20,'s');self.rect(14,12,19,15,',');self.bridge(6,14,7,16,'v');self.bridge(10,7,12,8,'h')
   for p in [(2,11,2,2),(12,4,2,2),(21,17,2,2),(14,19,2,2)]:self.ellipse(*p,'f',only='m')
   self.stamp('fishing_cottage',13,15,ground=',');self.stamp('crates',8,19,ground=',')
   self.notes=['诊疗所位于岛中央抬高干地，病人等候处、照护住屋与西南船口由连续转运路相接。','岛缘水洼与湿地边界自然收束，两段木栈跨过低洼处，树林集中在干路外侧，便于判断安全通行区域。','赛琳、两组病人和船口接应位置均不移动；记录屋南侧可读，护送两组病人撤离的条件保持。']
 def build(self):
  self.design()
  if self.c=='F43':self.boat_berth(0,22,21,27)
  elif self.c=='F44':self.boat_berth(0,22,21,26)
  elif self.c=='S42':self.boat_berth(0,16,15,21)
  visual=copy.deepcopy(self.g)
  # Preserve healing squares and actor-cell terrain categories; the resulting appearance remains coherent.
  for x,y in self.anchors:
   oldch=self.old['logic_grid'][y][x]
   if IDS[self.g[y][x]]!=IDS[oldch]:self.g[y][x]=oldch
  # Restore authoritative static module cells and retain their baked top layer exactly.
  ground=[[self.under.get((x,y),self.base)if ch=='#' else ch for x,ch in enumerate(row)]for y,row in enumerate(visual)]
  for y,row in enumerate(ground):
   for x,ch in enumerate(row):
    if ch=='^' and self.c in SNOW|{'F41','F42'}:ground[y][x]=self.base
    if ch=='f':ground[y][x]='n' if self.c in SNOW else 'm' if self.c in ['F43','S42'] else '.'
  base=[]
  for y,row in enumerate(ground):
   result=[]
   for x,ch in enumerate(row):
    v=B.seed(f'{self.c}:{x}:{y}:20261022')%4;mat=MAT[ch];bg='snow' if self.c in SNOW else 'sand' if self.c=='F41' else 'salt' if self.c in ['F42','F44'] else 'marsh' if self.c in ['F43','S42'] else 'grass'
    tile=B.PACK['base'][mat][v]
    if ch in ',b=^':tile=A.edge(mat,bg,B.mask_at(ground,x,y,lambda q:q==ch),v)
    if ch=='s':
     axis=self.bridge_axes.get((x,y),'v');mask=sum(bit for dx,dy,bit in[(0,-1,1),(1,0,2),(0,1,4),(-1,0,8)]if 0<=y+dy<self.h and 0<=x+dx<self.w and ground[y+dy][x+dx]=='s');tile=A.trans['walkway'][axis+str(mask)][v]
    if ch=='~':
     neighbors=[MAT[ground[y+dy][x+dx]]if 0<=x+dx<self.w and 0<=y+dy<self.h else 'sea' for dx,dy in[(0,-1),(1,0),(0,1),(-1,0)]];tile=A.water(neighbors,v)
    result.append(tile)
   base.append(result)
  nature=[];rng=random.Random(B.seed(self.c+'-nature-20261022'))
  for ch in ['^','f']:
   allowed={(x,y)for y,row in enumerate(self.g)for x,t in enumerate(row)if t==ch};taken=set();places=sorted(allowed);rng.shuffle(places)
   large=['peak_low','crag_tall','ridge_bent','outcrop']if ch=='^'else ['snow_tall','snow_broad','snow_pair']if self.c in SNOW else ['pine_broad','pine_tall','pine_pair'];small=['snow_boulder']if ch=='^'and self.c in SNOW else ['boulder']if ch=='^'else ['snow_small_a','snow_small_b','snow_young']if self.c in SNOW else ['pine_small_a','pine_small_b','pine_young']
   for x,y in places:
    if (x,y)in taken or rng.random()<.16:continue
    key=rng.choice(large);sw,sh=B.NATURE[key]['size'];foot={(xx,yy)for yy in range(y,y+math.ceil(sh/16))for xx in range(x,x+math.ceil(sw/16))}
    if foot<=allowed and not foot&(taken|self.protected):nature.append({'key':key,'position':[x*16,y*16],'flip':rng.random()<.4});taken|=foot
   for x,y in sorted(allowed-taken-self.protected):
    if ch!='^' and rng.random()<.18:continue
    nature.append({'key':rng.choice(small),'position':[x*16,y*16],'flip':rng.random()<.4})
  top=[[None]*self.w for _ in range(self.h)]
  for mod in self.d['art_modules']:
   if 'tiles'not in mod:continue
   ox,oy=mod['origin']
   for dy,row in enumerate(mod['tiles']):
    for dx,t in enumerate(row):top[oy+dy][ox+dx]=t
  self.d.update(logic_grid=[''.join(row)for row in self.g],visual_ground=[''.join(row)for row in ground],art_atlas='res://assets/map-polish-late-20261022/chapter4/terrain.png',art_layers=[base,copy.deepcopy(self.old['art_layers'][1]),top],natural_props=nature,tactical_routes=self.routes,tactical_notes=self.notes,tactical_review_version='0.10.3',art_style_version='map-polish-late-20261022',landscape_revision='2026-10-22-m11-reference')
  self.d['map']['tiles']=[IDS[ch]for row in self.g for ch in row]
  changed={'map','logic_grid','visual_ground','art_atlas','art_layers','art_modules','art_props','natural_props','tactical_routes','tactical_notes','tactical_review_version','art_style_version','landscape_revision'}
  for k in set(self.old)|set(self.d):
   if k not in changed:assert self.old.get(k)==self.d.get(k),(self.c,'gameplay mutation',k)
  report=self.check();write(R/f'data/stages/{self.c}.json',self.d);write(OUT/f'{self.c}-geometry.json',report);return report
 def check(self):
  start=tuple(self.d['player_positions'][0]);seen={start};q=deque([start])
  while q:
   x,y=q.popleft()
   for dx,dy in[(0,1),(1,0),(0,-1),(-1,0)]:
    p=x+dx,y+dy
    if 0<=p[0]<self.w and 0<=p[1]<self.h and p not in seen and self.g[p[1]][p[0]]not in '#^~':seen.add(p);q.append(p)
  unreachable=[p for p in self.anchors if p not in seen];assert not unreachable,(self.c,'unreachable actor',unreachable)
  for o in self.d['objects']:
   x,y=o['position'];ps=o.get('approaches',[o['approach']]if 'approach'in o else [[x+dx,y+dy]for dx,dy in[(1,0),(-1,0),(0,1),(0,-1)]]if o.get('adjacent')else[[x,y]]);assert any(tuple(p)in seen for p in ps),(self.c,'unreachable object',o['id'],ps)
  for n in self.d['natural_props']:
   x,y=[v//16 for v in n['position']];fw,fh=B.NATURE[n['key']]['size'];assert not any((xx,yy)in self.protected for yy in range(y,y+math.ceil(fh/16))for xx in range(x,x+math.ceil(fw/16)))
  return {'code':self.c,'passed':True,'anchors':len(self.anchors),'interactions':len(self.d['objects']),'connected_cells':len(seen),'gameplay_fields_unchanged':True,'actor_cells_same_category':True,'new_structures':self.added,'changed_logic_cells':sum(a!=b for a,b in zip(''.join(self.old['logic_grid']),''.join(self.d['logic_grid']))),'natural_props':len(self.d['natural_props']),'notes':self.notes}
if __name__=='__main__':
 reports=[Field(c).build()for c in CODES];A.save();write(OUT/'geometry.json',{'passed':True,'maps':reports,'atlas':'res://assets/map-polish-late-20261022/chapter4/terrain.png'});print(json.dumps(reports,ensure_ascii=False,indent=2))
