#!/usr/bin/env python3
"""Chapter-five royal medical court and three-span ascension bridge."""
from pathlib import Path
from collections import deque
from PIL import Image,ImageDraw
import copy,hashlib,importlib.util,json,math,random
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter5-redesign-20261022/west';BASE=O.parent/'baseline';ART=R/'assets/chapter5-redesign-20261022/west'
spec=importlib.util.spec_from_file_location('native_atlas',R/'tools/polish_chapter4_20261022.py');L=importlib.util.module_from_spec(spec);spec.loader.exec_module(L)
L.ART=ART;A=L.Atlas();B=L.B;IDS=dict(B.IDS,b=48);MAT=dict(B.MATERIAL,b='cobble')
temple=json.loads((R/'assets/chapter5/terrain.json').read_text())['materials'];temple_image=Image.open(R/'assets/chapter5/temple-tiles.png').convert('RGBA')
for name in ['ivory','sandstone']:
 ids=[]
 for source_id in temple[name]:
  ids.append(len(A.cells));A.cells.append(temple_image.crop((source_id%32*16,source_id//32*16,source_id%32*16+16,source_id//32*16+16)))
 B.PACK['base'][name]=ids
MAT['b']='ivory';MAT['=']='sandstone'
write=lambda p,d:(p.parent.mkdir(parents=True,exist_ok=True),p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n'))
def jail_corner():
 key='complete-jail-corner'
 if key not in A.add:
  tile=A.cells[482].copy();tile.alpha_composite(A.cells[485]);A.add[key]=[len(A.cells)];A.cells.append(tile)
 return A.add[key][0]
class Field:
 def __init__(self,c,w,h):
  self.c=c;self.old=json.loads((BASE/f'{c}.json').read_text());self.d=copy.deepcopy(self.old);self.w=w;self.h=h;self.base='~'if c=='M52'else'.';self.g=[list(self.base*w)for _ in range(h)];self.under={};self.routes=[];self.modules=[];self.props=[];self.layers=[[[None]*w for _ in range(h)]for _ in range(3)];self.solid=set()
 def rect(self,x0,y0,x1,y1,ch):
  for y in range(max(0,y0),min(self.h,y1+1)):
   for x in range(max(0,x0),min(self.w,x1+1)):self.g[y][x]=ch
 def poly(self,points,ch):
  im=Image.new('1',(self.w,self.h));ImageDraw.Draw(im).polygon(points,fill=1)
  for y in range(self.h):
   for x in range(self.w):
    if im.getpixel((x,y)):self.g[y][x]=ch
 def path(self,points,width=1,name='',ch='p'):
  for x,y in B.route(points):self.rect(x-(width-1)//2,y-(width-1)//2,x+width//2,y+width//2,ch)
  if name:self.routes.append({'name':name,'waypoints':points,'width':width,'surface':ch})
 def stamp(self,name,x,y,ground='.',purpose=''):
  m=B.MODULES[name];fw,fh=m['footprint'];cells=[]
  assert 0<=x and 0<=y and x+fw<=self.w and y+fh<=self.h
  for yy in range(y,y+fh):
   for xx in range(x,x+fw):
    assert(xx,yy)not in self.solid,(self.c,name,xx,yy)
    self.under[xx,yy]=ground;self.g[yy][xx]='#';cells.append([xx,yy]);self.solid.add((xx,yy))
  self.modules.append({'name':name,'origin':[x,y],'footprint':[fw,fh],'cells':cells,'logic':'#','runtime_prop':True,'purpose':purpose});self.props.append({'path':m['path'],'position':[x*16,y*16]})
 def tiled(self,name,x,y,tiles):
  cells=[]
  for dy,row in enumerate(tiles):
   for dx,t in enumerate(row):
    if t is None:continue
    xx,yy=x+dx,y+dy;self.g[yy][xx]='#';self.under[xx,yy]='b';self.layers[2][yy][xx]=t;cells.append([xx,yy]);self.solid.add((xx,yy))
  self.modules.append({'name':name,'origin':[x,y],'footprint':[len(tiles[0]),len(tiles)],'cells':cells,'logic':'#','tiles':tiles})
 def jail(self,x,y):
  self.rect(x,y,x+4,y+3,'#');self.rect(x+1,y+1,x+3,y+2,'c')
  mh=next(m for m in B.PACK['modules']if m['name']=='jail_bars_h');mv=next(m for m in B.PACK['modules']if m['name']=='jail_bars_v')
  self.tiled('jail_bars_h',x+1,y,[[mh['tiles'][0][1]]*3]);self.tiled('jail_bars_h',x+1,y+3,[[mh['tiles'][0][1],None,mh['tiles'][0][1]]])
  for xx in[x,x+4]:self.tiled('jail_bars_v',xx,y,[[jail_corner()],mv['tiles'][1],mv['tiles'][1],[jail_corner()]])
  self.under[x+2,y+3]='c';return[x+2,y+3]
 def relocate(self,group,positions):
  for u in self.d[group]:u['position']=positions[u['id']]
 def wall_h(self,x0,x1,y,gaps=(),wood=False):
  tile=475 if wood else 459;self.tiled('palisade_h'if wood else'fort_wall_h',x0,y,[[None if x in gaps else tile for x in range(x0,x1+1)]])
  for x in range(x0,x1+1):
   if x not in gaps:self.under[x,y]=self.base
 def wall_v(self,x,y0,y1,gaps=(),wood=False):
  tile=479 if wood else 463;self.tiled('palisade_v'if wood else'fort_wall_v',x,y0,[[None if y in gaps else tile]for y in range(y0,y1+1)])
  for y in range(y0,y1+1):
   if y not in gaps:self.under[x,y]=self.base
 def corner(self,x,y,wood=False):
  h,v=(475,479)if wood else(459,463);key=f'corner-{h}-{v}'
  if key not in A.add:
   im=A.cells[h].copy();im.alpha_composite(A.cells[v]);A.add[key]=[len(A.cells)];A.cells.append(im)
  self.tiled('complete_wall_corner',x,y,[[A.add[key][0]]]);self.under[x,y]=self.base
 def art(self,name,x,y,ground='b',purpose=''):
  p=R/f'assets/chapter5/{name}.png';im=Image.open(p);fw,fh=im.width//16,im.height//16;cells=[]
  assert 0<=x and 0<=y and x+fw<=self.w and y+fh<=self.h
  for yy in range(y,y+fh):
   for xx in range(x,x+fw):
    assert(xx,yy)not in self.solid,(self.c,name,xx,yy)
    self.g[yy][xx]='#';self.under[xx,yy]=ground;self.solid.add((xx,yy));cells.append([xx,yy])
  self.props.append({'path':f'res://assets/chapter5/{name}.png','position':[x*16,y*16]});self.modules.append({'name':name,'origin':[x,y],'footprint':[fw,fh],'cells':cells,'logic':'#','runtime_prop':True,'purpose':purpose})
 def design(self):
  d=self.d;c=self.c
  if c=='M51':
   # An enclosed medical inner court, behind a true southern evacuation court.
   self.rect(3,3,28,25,'.')
   self.rect(12,9,20,12,'b')
   self.path([(16,10),(16,28)],3,'宫前中轴与南侧后撤门',ch='=')
   self.path([(8,18),(25,18)],3,'两病房南门救护横廊',ch='=')
   self.path([(8,17),(8,18)],1,'西病房南门接应',ch='=');self.path([(25,17),(25,18)],1,'东病房南门接应',ch='=')
   self.path([(4,9),(12,9),(12,13),(16,13),(21,13),(21,9),(28,9),(30,9),(30,10)],2,'宫前守备与东侧来援通路',ch='b')
   self.path([(28,9),(28,19),(25,19)],1,'东医舍旁守备通道',ch='b');self.path([(4,9),(4,19),(8,19)],1,'西医舍旁接应廊',ch='b')
   self.path([(11,24),(16,24),(21,24)],2,'南院照护集结路',ch='b')
   self.wall_h(2,29,2,list(range(13,20)));self.wall_v(2,2,26);self.wall_v(29,2,26,[9,10]);self.wall_h(2,29,26,list(range(15,18)))
   for p in[(2,2),(29,2),(2,26),(29,26)]:self.corner(*p)
   self.wall_h(2,29,20,list(range(15,18)))
   self.art('palace',13,2,'.','北端王都内廷主殿');self.art('infirmary',5,11,'.','西病房与南向接应门');self.art('infirmary',22,11,'.','东病房与南向接应门')
   self.stamp('medicine_wagon',10,23,'b','南撤院照护药车')
   self.rect(4,4,8,7,'~');self.poly([(9,3),(11,3),(11,6),(9,8)],'f');self.poly([(23,3),(27,3),(28,6),(26,8),(23,7)],'f');self.poly([(4,22),(7,22),(8,25),(4,25)],'f');self.poly([(23,22),(27,22),(28,25),(24,25)],'f')
   d['player_positions']=[[14,23],[15,23],[16,23],[17,23],[14,24],[15,24],[16,24],[17,24],[13,23],[18,23]]
   self.relocate('npc_units',{'royal_wounded0':[8,17],'royal_wounded1':[25,17]})
   self.relocate('enemies',{'M51_boss':[16,10],'M51_e1':[13,13],'M51_e2':[20,12],'M51_e3':[27,20],'M51_e4':[4,9],'M51_e5':[14,10],'M51_e6':[20,15],'M51_e7':[28,19],'M51_e8':[11,10],'M51_e9':[18,10],'M51_e10':[21,13]})
   # The southern transverse wall must remain a wall; the east patrol stands north of it.
   next(u for u in d['enemies']if u['id']=='M51_e3')['position']=[27,18]
   self.relocate('reinforcements',{'M51_r0':[30,9],'M51_r1':[30,10]})
   d['objects'][0].update(position=[8,16],approach=[8,18]);d['objects'][1].update(position=[25,16],approach=[25,18]);d['exit']=[16,28]
   d['tactical_notes']=['北殿与东西两间完整医舍共同围成王都内廷，两处病房门朝南；南侧照护院与后撤门由中轴相连，形成内廷而非散落村舍。','伤兵在已打开的病房门槛等待接应，确认后沿南门横廊汇入中轴；横向院墙限制向南抄近路，接应队可守中央缺口与东侧来援巷。','队伍部署在南院，药车和庭园在道路两旁；先压住东医舍附近守军再放行，更容易保护两组伤兵。两病房都要确认、至少一组撤离及第4回合来援不变。']
  else:
   # Three separate real spans, connected by two generous support piers.
   self.rect(0,0,self.w-1,self.h-1,'~')
   self.poly([(1,4),(6,4),(6,7),(8,8),(8,16),(6,19),(2,19),(1,16)],'b')
   self.poly([(12,8),(13,5),(16,5),(17,8),(17,16),(15,19),(12,18)],'b')
   self.poly([(22,7),(23,4),(26,4),(27,7),(27,17),(25,20),(22,18)],'b')
   self.poly([(32,5),(36,4),(36,21),(32,21),(31,18),(31,9)],'b')
   self.rect(7,11,12,15,'=');self.rect(16,9,22,13,'=');self.rect(26,12,32,16,'=')
   self.path([(4,13),(14,13),(14,11),(24,11),(24,14),(35,14)],3,'西岸—三段石桥—东岸神宫入口',ch='=')
   self.path([(5,7),(5,13)],2,'西岸援军与部署回廊',ch='b');self.path([(34,10),(34,18)],2,'东岸守备回廊',ch='b')
   self.path([(14,13),(14,17)],2,'第一承台南侧待机支台',ch='b');self.path([(24,14),(24,18)],2,'第二承台南侧待机支台',ch='b')
   # Railing cells are truly blocked and sit outside the three clear walking rows.
   self.wall_h(8,11,11);self.wall_h(8,11,15);self.wall_h(17,21,9);self.wall_h(17,21,13);self.wall_h(27,30,12);self.wall_h(27,30,16)
   self.art('column',2,3,'b','西岸桥头石柱');self.art('column',14,5,'b','第一承台柱');self.art('column',24,4,'b','第二承台柱');self.art('column',33,3,'b','东岸桥头石柱')
   d['player_positions']=[[3,13],[4,13],[3,14],[4,14],[2,13],[5,13],[2,14],[5,14],[3,15],[4,15]]
   self.relocate('enemies',{'M52_boss':[34,14],'M52_e1':[11,13],'M52_e2':[18,11],'M52_e3':[28,14],'M52_e4':[34,10],'M52_e5':[13,12],'M52_e6':[23,10],'M52_e7':[31,14],'M52_e8':[34,11],'M52_e9':[14,10],'M52_e10':[24,9],'M52_e11':[24,12],'M52_e12':[33,12],'M52_e13':[14,14]})
   self.relocate('reinforcements',{'M52_r0':[5,7],'M52_r1':[6,7]})
   for o,p in zip(d['objects'],[[12,13],[22,11],[32,14]]):o['position']=p
   d['exit']=[35,14]
   d['tactical_notes']=['登天桥由三段真正跨水的石桥、两处承台与东西岸桥头组成；每段保持三格净通行宽度，护栏在通行带外，桥两端都落在完整石台上。','三个桥锁从西到东依次位于落脚承台，使用可通行的控制标记，不用封闭门图阻断已连通的桥面；原先后确认规则保持。','承台南侧留出待机与整队支台，可避免全队挤入桥口；飞行者可越水绕侧，但仍需正式确认三段桥锁，东岸和西岸来援通道均有实际落脚地。']
  d['targets']=[o['position']for o in d['objects']]
 def flood(self,start,opened=False):
  opens={tuple(p)for o in self.d['objects']for p in o.get('opens',[o['position']]if o['kind']in['door','rescue']else[])};q=deque([tuple(start)]);seen={tuple(start):0}
  while q:
   x,y=q.popleft()
   for dx,dy in[(0,-1),(1,0),(0,1),(-1,0)]:
    p=x+dx,y+dy
    if 0<p[0]<self.w-1 and 0<p[1]<self.h-1 and p not in seen and(self.g[p[1]][p[0]]not in'#^~'or opened and p in opens):seen[p]=seen[x,y]+1;q.append(p)
  return seen
 def bake(self):
  self.design();c=self.c;d=self.d;w=self.w;h=self.h;g=self.g
  anchors={tuple(p)for p in d['player_positions']+[d['exit']]+[u['position']for k in['enemies','npc_units','reinforcements']for u in d[k]]}
  for x,y in anchors:
   assert g[y][x]not in'#^~',(c,'blocked actor',x,y,g[y][x])
   if g[y][x]=='f':g[y][x]=self.base
  for o in d['objects']:
   for x,y in o.get('approaches',[o['approach']]if'approach'in o else[]):assert g[y][x]not in'#^~',(c,'blocked front',o['id'])
  occupied=[tuple(p)for p in d['player_positions']]+[tuple(u['position'])for u in d['enemies']+d['npc_units']];assert len(occupied)==len(set(occupied)),(c,'overlap')
  ground=[[self.under.get((x,y),self.base)if ch=='#'else self.base if ch in'^f'else ch for x,ch in enumerate(row)]for y,row in enumerate(g)]
  for y,row in enumerate(ground):
   for x,ch in enumerate(row):
    v=B.seed(f'{c}:composition:{x}:{y}')%4;mat=MAT[ch];tile=B.PACK['base'][mat][v]
    if ch in'pb=':tile=A.edge(mat,'sea'if self.base=='~'else'snow'if self.base=='n'else'grass',B.mask_at(ground,x,y,lambda q:q in'pb='),v)
    elif ch=='s':
     m=sum(bit for dx,dy,bit in[(0,-1,1),(1,0,2),(0,1,4),(-1,0,8)]if 0<=x+dx<w and 0<=y+dy<h and ground[y+dy][x+dx]=='s');tile=A.trans['walkway']['h'+str(m)][v]
    self.layers[0][y][x]=tile
  nature=[];rng=random.Random(B.seed(c+'-landmass'))
  for ch,large,small in[('f',['pine_tall','pine_broad','pine_pair'],['pine_small_a','pine_small_b','pine_young']),('^',['peak_low','crag_tall','ridge_bent'],['boulder'])]:
   if self.base=='n' and ch=='f':large=['snow_tall','snow_broad','snow_pair'];small=['snow_small_a','snow_small_b','snow_young']
   if self.base=='n' and ch=='^':small=['snow_boulder']
   allowed={(x,y)for y,row in enumerate(g)for x,t in enumerate(row)if t==ch};used=set();places=sorted(allowed,key=lambda p:(-sum((p[0]+dx,p[1]+dy)in allowed for dx in range(-1,3)for dy in range(-1,3)),p[1],p[0]))
   for x,y in places:
    if(x,y)in used:continue
    choices=large.copy();rng.shuffle(choices)
    for key in choices:
     sw,sh=B.NATURE[key]['size'];cells={(xx,yy)for yy in range(y,y+math.ceil(sh/16))for xx in range(x,x+math.ceil(sw/16))}
     if cells<=allowed and not cells&(used|anchors):nature.append({'key':key,'position':[x*16,y*16],'flip':rng.random()<.35});used|=cells;break
   for x,y in sorted(allowed-used):nature.append({'key':rng.choice(small),'position':[x*16,y*16],'flip':rng.random()<.35})
   if ch=='f':
    for x,y in sorted(allowed):
     if(x+y)%2 or rng.random()<.2:continue
     key=rng.choice(large[:2]);sw,sh=B.NATURE[key]['size'];px=x*16+rng.randint(-2,2);py=y*16+rng.randint(-2,2);cells={(xx,yy)for yy in range(py//16,math.ceil((py+sh)/16))for xx in range(px//16,math.ceil((px+sw)/16))}
     if cells<=allowed and not cells&anchors:nature.append({'key':key,'position':[px,py],'flip':rng.random()<.35})
  nature.sort(key=lambda p:p['position'][1]+B.NATURE[p['key']]['size'][1])
  d.update(map={'width':w,'height':h,'tiles':[IDS[ch]for row in g for ch in row]},logic_grid=[''.join(row)for row in g],visual_ground=[''.join(row)for row in ground],art_layers=self.layers,art_modules=self.modules,art_props=self.props,natural_props=nature,art_atlas='res://assets/chapter5-redesign-20261022/west/terrain.png',art_columns=32,tactical_routes=self.routes,tactical_review_version='0.10.9-ch5',art_style_version='chapter5-redesign-20261022',landscape_revision='M41 approved composition method; chapter5 west',nature_layout={'biome':'snow'if self.base=='n'else'forest','props':[],'excluded':[[0,0,w*16,h*16]]})
  d['visual_notes']=d['tactical_notes'].copy();seen=self.flood(d['player_positions'][0]);opened=self.flood(d['player_positions'][0],True)
  standard={tuple(p)for p in d['player_positions']+[d['exit']]+[u['position']for k in['enemies','reinforcements']for u in d[k]]};assert standard<=set(seen),(c,'unreachable actors',standard-set(seen));assert anchors<=set(opened),(c,'unreachable NPC',anchors-set(opened))
  distances={}
  for o in d['objects']:
   x,y=o['position'];fronts=o.get('approaches',[o['approach']]if'approach'in o else[[x,y]]+([[x+dx,y+dy]for dx,dy in[(0,-1),(1,0),(0,1),(-1,0)]]if o.get('adjacent')else[]));valid=[seen[tuple(p)]for p in fronts if tuple(p)in seen];assert valid,(c,'object unreachable',o['id']);distances[o['id']]=min(valid)
  for group in['enemies','npc_units','reinforcements']:
   assert len(d[group])==len(self.old[group]);assert all({k:v for k,v in a.items()if k!='position'}=={k:v for k,v in b.items()if k!='position'}for a,b in zip(self.old[group],d[group])),(c,group)
  for k in['characters','terrain','goal','before','during','after','optional','clear_training_exp','reinforcement_turn','event_boats']:assert d.get(k)==self.old.get(k),(c,k)
  movable={'position','approach','approaches','opens','open_art_cells','sprite_offset'}
  for a,b in zip(self.old['objects'],d['objects']):assert{k:v for k,v in a.items()if k not in movable}=={k:v for k,v in b.items()if k not in movable},(c,a['id'])
  report={'passed':True,'code':c,'size':[w,h],'closed_connected':len(seen),'opened_connected':len(opened),'notes':d['tactical_notes'],'units_only_positions_changed':True,'story_timing_rules_preserved':True,'coordinate_changes':{group:[{'id':b['id'],'before':a['position'],'after':b['position']}for a,b in zip(self.old[group],d[group])]for group in['enemies','npc_units','reinforcements','objects']},'deployment_before':self.old['player_positions'],'deployment_after':d['player_positions'],'exit':d['exit'],'targets':d['targets'],'interaction_front_distances':distances}
  assert all(0<x<w-1 and 0<y<h-1 for x,y in anchors),(c,'outer-border anchor')
  if c=='M51':
   report['escort_to_exit_steps']={u['id']:self.flood(u['position'])[tuple(d['exit'])]for u in d['npc_units']}
   assert all(o['position'][0]==o['approach'][0]and o['position'][1]+2==o['approach'][1]for o in d['objects'])
   report['medical_crosswall_gaps']=[[x,20]for x in range(15,18)]
  if c=='M52':
   assert[d['objects'][i]['position'][0]for i in range(3)]==sorted(o['position'][0]for o in d['objects']);report['bridge_walk_rows']=[{'x':[7,12],'y':[12,14]},{'x':[16,22],'y':[10,12]},{'x':[26,32],'y':[13,15]}]
   for span in report['bridge_walk_rows']:
    assert all(g[y][x]!='~'and g[y][x]!='#'for x in range(span['x'][0],span['x'][1]+1)for y in range(span['y'][0],span['y'][1]+1)),(c,'bridge walking strip')
  report.update(routes=d['tactical_routes'],structures=[{'name':m['name'],'origin':m['origin'],'footprint':m['footprint']}for m in d['art_modules']],interactions=[{k:v for k,v in z.items()if k in ['id','position','approach','approaches','sprite_offset']}for z in d['objects']])
  write(R/f'data/stages/{c}.json',d);report['map_sha256']=hashlib.sha256((R/f'data/stages/{c}.json').read_bytes()).hexdigest();write(O/f'{c}-design.json',report);return report
if __name__=='__main__':
 reports=[Field('M51',32,30).bake(),Field('M52',38,26).bake()];A.save();write(O/'geometry.json',{'passed':True,'maps':reports});print(json.dumps([{'code':r['code'],'size':r['size'],'passed':True}for r in reports]))
