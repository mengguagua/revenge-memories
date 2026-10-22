#!/usr/bin/env python3
"""M41 sample: village, diagonal river valley, two crossings and a southern pass.
Rebuild only M41 from this turn's frozen baseline; no rule or animation edits.
"""
from pathlib import Path
from collections import deque
from PIL import Image,ImageDraw
import copy,hashlib,importlib.util,json,math,random
R=Path(__file__).resolve().parents[1];O=R/'reports/m41-redesign-20261022';ART=R/'assets/m41-valley-20261022'
spec=importlib.util.spec_from_file_location('native_land',R/'tools/polish_chapter4_20261022.py');L=importlib.util.module_from_spec(spec);spec.loader.exec_module(L)
L.ART=ART;A=L.Atlas();B=L.B;IDS=L.IDS;MAT=L.MAT
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
old=json.loads((O/'baseline/M41.json').read_text());d=copy.deepcopy(old);w,h=32,26
g=[list('n'*w)for _ in range(h)];under={};bridges={};routes=[];modules=[];props=[]
def rect(x0,y0,x1,y1,ch):
 for y in range(max(0,y0),min(h,y1+1)):
  for x in range(max(0,x0),min(w,x1+1)):g[y][x]=ch
def poly(points,ch):
 mask=Image.new('1',(w,h));ImageDraw.Draw(mask).polygon(points,fill=1)
 for y in range(h):
  for x in range(w):
   if mask.getpixel((x,y)):g[y][x]=ch
def path(points,width=2,name='',ch=','):
 for x,y in B.route(points):rect(x-(width-1)//2,y-(width-1)//2,x+width//2,y+width//2,ch)
 if name:routes.append({'name':name,'waypoints':points,'width':width,'surface':ch})
def bridge(x0,y0,x1,y1,axis):
 rect(x0,y0,x1,y1,'s')
 for y in range(y0,y1+1):
  for x in range(x0,x1+1):bridges[x,y]=axis
def stamp(name,x,y,ground='n',purpose=''):
 m=B.MODULES[name];fw,fh=m['footprint'];cells=[]
 for yy in range(y,y+fh):
  for xx in range(x,x+fw):under[xx,yy]=ground;g[yy][xx]='#';cells.append([xx,yy])
 modules.append({'name':name,'origin':[x,y],'footprint':[fw,fh],'cells':cells,'logic':'#','runtime_prop':True,'purpose':purpose})
 props.append({'path':m['path'],'position':[x*16,y*16]})

# Three coherent land masses. Mountain shoulders continue beyond the cropped map.
poly([(0,0),(5,0),(5,2),(4,2),(4,4),(2,5),(2,10),(0,12)],'^')
poly([(29,0),(31,0),(31,7),(30,6),(29,4)],'^')
poly([(31,16),(30,17),(30,20),(28,21),(28,23),(25,24),(25,25),(31,25)],'^')
poly([(13,24),(15,22),(17,23),(19,23),(20,25),(13,25)],'^')
# Forests make sheltered edges and readable empty snow clearings, not a ring of icons.
poly([(12,0),(21,0),(22,2),(21,4),(19,5),(18,7),(15,7),(14,5),(12,4)],'f')
poly([(0,13),(3,12),(6,13),(7,15),(6,17),(7,19),(5,22),(2,23),(0,21)],'f')
poly([(29,6),(31,7),(31,16),(29,17),(27,15),(26,12),(27,10),(27,8)],'f')
poly([(13,19),(15,18),(17,19),(17,21),(15,23),(12,22)],'f')
# Variable-width river descends NE -> SW. Both crossings span genuine water.
banks=[(25,28),(25,27),(24,27),(24,26),(23,26),(23,25),(22,25),(21,24),(20,23),(19,22),(18,21),(16,18),(16,18),(16,18),(16,18),(13,16),(12,15),(11,14),(10,13),(9,12),(8,11),(8,10),(7,10),(7,9),(6,9),(6,8)]
for y,(a,b)in enumerate(banks):rect(a,y,b,y,'~')
# Village street, then a short wider bridge approach, then an open medical court.
path([(8,0),(8,8),(10,8),(10,10)],1,'北口与村街')
path([(10,10),(13,10),(13,12),(20,12),(20,14),(22,14),(22,18),(21,18),(21,21),(22,21),(22,25)],2,'谷桥—医舍—南口主线')
path([(6,5),(11,5)],1,'屋门前街');path([(5,9),(8,9)],1);path([(13,9),(13,10)],1)
rect(7,6,10,7,',');rect(13,11,15,13,',');rect(19,12,21,14,',')
rect(23,16,27,17,',');path([(22,16),(25,16)],2);path([(27,20),(23,20),(23,21)],1)
path([(19,21),(21,21)],1);rect(20,21,23,23,',')
# Longer narrow northern approach reconnects behind the bridge guard line.
path([(11,5),(11,6),(12,6),(17,6),(17,5),(21,5),(21,6),(27,6),(27,9),(26,9),(26,12),(25,12),(25,16)],1,'东北林缘小桥绕行线')
bridge(15,12,19,13,'h');bridge(21,6,26,6,'h')
# Homes enclose a small shared street. Doors are on their southern faces.
stamp('snow_cottage',5,3,purpose='北村西屋');stamp('snow_cottage',10,3,purpose='北村东屋')
stamp('snow_cottage',4,7,purpose='村街西侧住屋');stamp('snow_cottage',12,7,purpose='岔路口住屋')
stamp('well',6,6,purpose='村院生活中心');stamp('camp_palisade',4,10,purpose='菜圃南缘')
stamp('village_clinic',24,14,purpose='停靠点北侧医舍');stamp('snow_cottage',26,18,purpose='南村住屋')
stamp('snow_cottage',18,19,purpose='南口村舍');stamp('crates',27,16,purpose='医舍院角物资')
stamp('camp_palisade',17,22,purpose='南口西侧路障');stamp('camp_palisade',24,22,purpose='南口东侧路障')
# The original one recovery square now belongs to the medical stop.
g[17][25]='+'
d['player_positions']=[[8,9],[9,9],[10,9],[11,9],[8,10],[9,10],[10,10],[11,10],[7,10],[7,11],[8,11],[9,11]]
enemy_positions={'M41_boss':[22,23],'M41_e1':[20,12],'M41_e2':[19,15],'M41_e3':[26,10],'M41_e4':[24,18],'M41_e5':[23,22],'M41_e6':[21,13],'M41_e7':[27,12],'M41_e8':[23,12],'M41_e9':[25,21],'M41_e10':[29,11],'M41_e11':[24,20],'M41_e12':[28,17]}
for u in d['enemies']:u['position']=enemy_positions[u['id']]
for u,p in zip(d['npc_units'],[[7,7],[12,11],[28,20]]):u['position']=p
for u,p in zip(d['reinforcements'],[[8,1],[9,1]]):u['position']=p
for o in d['objects']:o['position']={'south_gate':[21,22],'rest_station':[25,17]}[o['id']]
d['exit']=[22,24];d['targets']=[o['position']for o in d['objects']]
anchors={tuple(p)for p in d['player_positions']+[d['exit']]+d['targets']+[u['position']for u in d['enemies']+d['npc_units']+d['reinforcements']]}
for x,y in anchors:
 assert g[y][x]not in '#^~',(x,y,g[y][x])
 if g[y][x]=='f':g[y][x]='n'

def snow_shore(neighbors,v):
 key='m41:'+':'.join(neighbors)
 if key not in A.shores:
  ids=[]
  for n in range(4):
   im=A.cells[B.PACK['base']['sea'][n]].copy()
   for side,mat in enumerate(neighbors[:4]):
    if mat in ['sea','timber']:continue
    bank=A.cells[B.PACK['base'][mat][n]]
    for span in range(16):
     depth=3+(1 if (span+n*3)%11 in [3,4,5]else 0)
     for step in range(depth):
      px,py=[(span,step),(15-step,span),(span,15-step),(step,span)][side]
      r,g_,b,a_=bank.getpixel((px,py));shade=.90 if step==depth-1 else 1.0
      im.putpixel((px,py),(int(r*shade),int(g_*shade),int(b*shade),a_))
   for mat,(cx,cy,sx,sy)in zip(neighbors[4:],[(15,0,-1,1),(15,15,-1,-1),(0,15,1,-1),(0,0,1,1)]):
    if mat in ['sea','timber']:continue
    bank=A.cells[B.PACK['base'][mat][n]]
    for dy in range(5):
     for dx in range(5):
      if dx+dy<=4:
       px,py=cx+sx*dx,cy+sy*dy;im.putpixel((px,py),bank.getpixel((px,py)))
   ids.append(len(A.cells));A.cells.append(im)
  A.shores[key]=ids
 return A.shores[key][v]

# Native terrain transitions; preserve whole bitmap architecture and clean road silhouettes.
ground=[[under.get((x,y),'n')if ch=='#'else'n'if ch in '^f'else ch for x,ch in enumerate(row)]for y,row in enumerate(g)]
base=[]
for y,row in enumerate(ground):
 line=[]
 for x,ch in enumerate(row):
  v=B.seed(f'M41-valley:{x}:{y}')%4;mat=MAT[ch];tile=B.PACK['base'][mat][v]
  if ch in ',b=':tile=A.edge(mat,'snow',B.mask_at(ground,x,y,lambda q:q==ch),v)
  if ch=='~':tile=snow_shore([MAT[ground[y+dy][x+dx]]if 0<=x+dx<w and 0<=y+dy<h else'sea'for dx,dy in[(0,-1),(1,0),(0,1),(-1,0),(1,-1),(1,1),(-1,1),(-1,-1)]],v)
  if ch=='s':
   mask=sum(bit for dx,dy,bit in[(0,-1,1),(1,0,2),(0,1,4),(-1,0,8)]if 0<=x+dx<w and 0<=y+dy<h and ground[y+dy][x+dx]=='s')
   tile=A.trans['walkway'][bridges.get((x,y),'h')+str(mask)][v]
  line.append(tile)
 base.append(line)
nature=[];rng=random.Random(41022026)
for ch in ['^','f']:
 allowed={(x,y)for y,row in enumerate(g)for x,c in enumerate(row)if c==ch};taken=set()
 large=['peak_low','crag_tall','ridge_bent','outcrop']if ch=='^'else['snow_tall','snow_broad','snow_pair']
 small=['snow_boulder']if ch=='^'else['snow_small_a','snow_small_b','snow_young']
 # Pack the interior with whole large silhouettes; smaller edge pieces describe the shape.
 places=sorted(allowed,key=lambda p:(-sum((p[0]+dx,p[1]+dy)in allowed for dx in range(-1,3)for dy in range(-1,3)),p[1],p[0]))
 for x,y in places:
  if (x,y)in taken:continue
  choices=large.copy();rng.shuffle(choices)
  for key in choices:
   sw,sh=B.NATURE[key]['size'];cells={(xx,yy)for yy in range(y,y+math.ceil(sh/16))for xx in range(x,x+math.ceil(sw/16))}
   if cells<=allowed and not cells&(taken|anchors):
    nature.append({'key':key,'position':[x*16,y*16],'flip':rng.random()<.35});taken|=cells;break
 for x,y in sorted(allowed-taken):nature.append({'key':rng.choice(small),'position':[x*16,y*16],'flip':rng.random()<.35})
# Extra interior crowns join forests into masses rather than an evenly spaced icon field.
interior={(x,y)for y,row in enumerate(g)for x,c in enumerate(row)if c=='f'}
for x,y in sorted(interior):
 if (x+y)%2 or rng.random()<.2:continue
 key=rng.choice(['snow_tall','snow_broad']);sw,sh=B.NATURE[key]['size']
 px=x*16+rng.randint(-3,3);py=y*16+rng.randint(-2,2)
 cells={(xx,yy)for yy in range(py//16,math.ceil((py+sh)/16))for xx in range(px//16,math.ceil((px+sw)/16))}
 if cells<=interior and not cells&anchors:nature.append({'key':key,'position':[px,py],'flip':rng.random()<.35})
nature.sort(key=lambda p:p['position'][1]+B.NATURE[p['key']]['size'][1])
d.update(logic_grid=[''.join(r)for r in g],visual_ground=[''.join(r)for r in ground],art_layers=[base,[[None]*w for _ in range(h)],[[None]*w for _ in range(h)]],art_modules=modules,art_props=props,natural_props=nature,art_atlas='res://assets/m41-valley-20261022/terrain.png',tactical_routes=routes,tactical_review_version='0.10.4-m41',art_style_version='m41-valley-20261022',landscape_revision='M41 single-map composition sample')
d['map']['tiles']=[IDS[c]for row in g for c in row]
d['visual_notes']=['西北村落经中央谷桥通往东南南口；东北林缘小桥提供较长绕行线。部署、三组居民、守军及交互坐标随整体空间重新安排，原剧情和胜利条件保持。']
d['tactical_notes']=['西北四座村舍围出紧凑村街，融雪河从东北斜向西南切开雪峡；中央主桥连接村街和东岸医舍，南口在两侧山肩与木障之间收窄。','主桥可集中兵力正面破阵；东北林缘的一格小桥较长、较窄，能绕至桥头守军侧后。两线在医舍前重新汇合，沿途保留雪地展开空间与林缘地形。','北口第4敌方回合仍有两名骑兵追来。保护北村居民与山道伤者过桥，同时接应南村居民；疏通南口、确认医舍停靠点、撤离至少两组并击败指挥官的规则不变。']
# A sample may change coordinates, never identity, strength, timing or narrative contracts.
for group in ['enemies','npc_units','reinforcements']:
 for a,b in zip(old[group],d[group]):assert {k:v for k,v in a.items()if k!='position'}=={k:v for k,v in b.items()if k!='position'}
for a,b in zip(old['objects'],d['objects']):assert {k:v for k,v in a.items()if k!='position'}=={k:v for k,v in b.items()if k!='position'}
for k in ['before','during','after','goal','reinforcement_turn','clear_training_exp','terrain','characters']:assert d[k]==old[k],k
def flood(start):
 seen={start:0};q=deque([start])
 while q:
  x,y=q.popleft()
  for dx,dy in[(0,-1),(1,0),(0,1),(-1,0)]:
   p=x+dx,y+dy
   if 0<p[0]<w-1 and 0<p[1]<h-1 and p not in seen and g[p[1]][p[0]]not in '#^~':seen[p]=seen[x,y]+1;q.append(p)
 return seen
seen=flood(tuple(d['player_positions'][0]));assert anchors<=set(seen),anchors-set(seen)
occupied=[tuple(u['position'])for u in d['enemies']+d['npc_units']]+[tuple(p)for p in d['player_positions']]
assert len(occupied)==len(set(occupied))
write(R/'data/stages/M41.json',d);A.save()
write(O/'design.json',{'passed':True,'theme':'斜穿雪峡的撤离线','map_size':[w,h],'deploy':d['player_positions'],'enemy_groups':{'bridge':['M41_e1','M41_e2','M41_e6','M41_e8'],'forest_side':['M41_e3','M41_e7','M41_e10'],'south_pass':['M41_boss','M41_e4','M41_e5','M41_e9','M41_e11','M41_e12']},'anchors':len(anchors),'connected_cells':len(seen),'resident_distances_to_exit':{u['id']:flood(tuple(u['position'])).get(tuple(d['exit']))for u in d['npc_units']},'notes':d['tactical_notes'],'old_units_only_positions_changed':True,'story_rules_unchanged':True,'other_maps_changed':False})
print(json.dumps({'passed':True,'connected':len(seen),'natural_props':len(nature),'modules':len(modules)},ensure_ascii=False))
