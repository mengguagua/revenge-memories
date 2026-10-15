#!/usr/bin/env python3
"""Art-only organic geography. Never regenerate combat rules or plot definitions."""
from pathlib import Path
import json,random,math,hashlib,copy,shutil
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];REPORT=ROOT/'reports/natural-0.1.3';REPORT.mkdir(parents=True,exist_ok=True)
BACKUP=ROOT/'source/natural-0.1.3/baseline';BACKUP.mkdir(parents=True,exist_ok=True)
def read(p):return json.loads(p.read_text())
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
CAT={s['key']:s for s in read(ROOT/'assets/nature/nature.json')['sprites']}
def seed(key):return int(hashlib.sha256(str(key).encode()).hexdigest()[:12],16)
def intersects(a,b):return a[0]<b[0]+b[2] and a[0]+a[2]>b[0] and a[1]<b[1]+b[3] and a[1]+a[3]>b[1]
def contained(a,b):return a[0]>=b[0] and a[1]>=b[1] and a[0]+a[2]<=b[0]+b[2] and a[1]+a[3]<=b[1]+b[3]
def rect(p):return [*p['position'],*p.get('size',CAT[p['key']]['size'])]
def overlap(a,b):return max(0,min(a[0]+a[2],b[0]+b[2])-max(a[0],b[0]))*max(0,min(a[1]+a[3],b[1]+b[3])-max(a[1],b[1]))
def acceptable(r,placed,max_overlap=.30):
 return all(overlap(r,rect(p))<=min(r[2]*r[3],rect(p)[2]*rect(p)[3])*max_overlap for p in placed)
def prop(key,x,y,rng):return {'key':key,'position':[round(x),round(y)],'flip':rng.random()<.4}
def organic_exterior(key,cells,biome,excluded):
 rng=random.Random(seed(key));w,h=[c*16 for c in cells];area=[-256,-256,w+512,h+512];out=[]
 if biome!='rock':
  prefix='snow' if biome=='snow' else 'pine'
  kinds=[prefix+'_tall']*4+[prefix+'_broad']*3+[prefix+'_young']*4+[prefix+'_pair']
  centers=[(-25,h*.22,50,43),(-40,h*.83,58,46),(w+25,h*.18,57,43),(w+36,h*.78,55,53),
   (w*.15,-45,60,45),(w*.8,-44,60,45),(w*.18,h+38,60,43),(w*.85,h+48,65,46)]
  # Distant groups become visible on wider screens; layout stays world-fixed.
  centers += [(-145,h*.15,65,80),(-150,h*.9,72,60),(w+150,h*.25,70,72),(w+165,h*.95,65,66),
   (w*.4,-165,100,62),(w*.65,h+170,100,65)]
  for cx,cy,rx,ry in centers:
   for _ in range(35):
    sprite=rng.choice(kinds);sw,sh=CAT[sprite]['size']
    x=cx+rng.gauss(0,rx*.48)-sw/2;y=cy+rng.gauss(0,ry*.48)-sh*.65
    r=[round(x),round(y),sw,sh]
    if not contained(r,area) or any(intersects(r,e) for e in excluded) or not acceptable(r,out):continue
    out.append(prop(sprite,r[0],r[1],rng))
 else:
  # Broken, bending ridges with unequal peaks, rather than parallel rock rows.
  for side in range(4):
   for distance in [20,96,183]:
    phase=rng.random()*math.tau;t=-150.0
    limit=h+150 if side<2 else w+150
    while t<limit:
     sprite=rng.choice(['peak_low','peak_low','crag_tall','ridge_bent','outcrop']);sw,sh=CAT[sprite]['size']
     bend=math.sin(t/67+phase)*23+math.sin(t/113+phase*.4)*12+rng.uniform(-9,9)
     if side<2:x=(-distance+bend-sw if side==0 else w+distance+bend);y=t-sh*.6
     else:x=t-sw/2;y=(-distance+bend-sh if side==2 else h+distance+bend)
     r=[round(x),round(y),sw,sh];t+=rng.uniform(22,44)
     if contained(r,area) and not any(intersects(r,e) for e in excluded) and acceptable(r,out,.42):out.append(prop(sprite,r[0],r[1],rng))
 # Sparse small pieces soften edges and gaps, rather than identical big stamps.
 for _ in range(150):
  near=rng.choice(out) if out else None
  if not near:break
  sprite=rng.choice(['snow_boulder','snow_young']) if biome=='snow' else rng.choice(['brush','boulder']) if biome!='rock' else rng.choice(['boulder','stone_low'])
  sw,sh=CAT[sprite]['size'];x=near['position'][0]+rng.uniform(-24,36);y=near['position'][1]+rng.uniform(-12,35);r=[round(x),round(y),sw,sh]
  if contained(r,area) and not any(intersects(r,e) for e in excluded) and acceptable(r,out,.18):out.append(prop(sprite,r[0],r[1],rng))
 return sorted(out,key=lambda p:(p['position'][1]+CAT[p['key']]['size'][1],p['position'][0]))
def scatter_cells(key,allowed,biome,excluded):
 rng=random.Random(seed(key));placed=[];cells=sorted(allowed);rng.shuffle(cells)
 large=['snow_tall','snow_broad','snow_pair'] if biome=='snow' else ['pine_tall','pine_broad','pine_pair'] if biome=='forest' else ['peak_low','crag_tall','ridge_bent','outcrop','stone_low']
 def legal(r):
  return all((x,y) in allowed for y in range(math.floor(r[1]/16),math.ceil((r[1]+r[3])/16)) for x in range(math.floor(r[0]/16),math.ceil((r[0]+r[2])/16))) and not any(intersects(r,e) for e in excluded)
 for x,y in cells:
  for _ in range(2):
   sprite=rng.choice(large);sw,sh=CAT[sprite]['size'];r=[x*16+rng.randrange(0,9),y*16+rng.randrange(0,9),sw,sh]
   if legal(r) and acceptable(r,placed,.22):placed.append(prop(sprite,r[0],r[1],rng));break
 small=['snow_young','snow_small_a','snow_small_b'] if biome=='snow' else ['pine_young','pine_small_a','pine_small_b','brush'] if biome=='forest' else ['boulder','snow_boulder']
 for x,y in cells:
  tile=[x*16,y*16,16,16]
  if any(overlap(tile,rect(p))>70 for p in placed):continue
  sprite=rng.choice(small);r=[x*16,y*16,*CAT[sprite]['size']]
  if legal(r) and acceptable(r,placed,.2):placed.append(prop(sprite,*r[:2],rng))
 return sorted(placed,key=lambda p:p['position'][1]+CAT[p['key']]['size'][1])
def fingerprint(d,allowed):return hashlib.sha256(json.dumps({k:v for k,v in d.items() if k not in allowed},sort_keys=True).encode()).hexdigest()
def backup(path):
 p=BACKUP/path.relative_to(ROOT);p.parent.mkdir(parents=True,exist_ok=True)
 if not p.exists():shutil.copy2(path,p)
 return read(p)
def hubs():
 records=read(REPORT/'hub-geometry.json');out={};mods={m['name']:m for m in read(ROOT/'assets/battle_tiles/battle-tiles.json')['modules']}
 for room,g in records.items():
  biome='snow' if room=='H01' else 'rock' if room=='H08' else 'forest'
  excluded=[g['walk_rect'],g['exit_rect']]+[d['rect'] for d in g['scenery']]
  for obj in g['objects']:
   x,y=obj['position']
   if obj['sprite']=='actor':excluded.append([x*16-8,y*16-8,32,24])
   elif obj['sprite'] in mods:
    mw,mh=mods[obj['sprite']]['footprint'];excluded.append([x*16,y*16-(mh-1)*16,mw*16,mh*16])
  # Scenery is a real obstacle; its full footprint remains the same.
  groves=[]
  for d in g['scenery']:
   if d['name'] not in ['pine_patch','snow_pine_patch','rock_face']:continue
   x,y,w,h=d['rect'];allowed={(xx,yy) for yy in range(y//16,(y+h)//16) for xx in range(x//16,(x+w)//16)}
   groves.append({'rect':d['rect'],'source_name':d['name'],'props':scatter_cells(room+d['name'],allowed,'snow' if d['name'].startswith('snow') else 'rock' if d['name']=='rock_face' else 'forest',[])})
  out[room]={'biome':biome,'excluded':excluded,'props':organic_exterior(room,[14,9],biome,excluded),'groves':groves}
 return out
def battles():
 results=[];layouts={};pack=read(ROOT/'assets/battle_tiles/battle-tiles.json');mods={m['name']:m for m in pack['modules']}
 for path in sorted((ROOT/'data/stages').glob('*.json')):
  d=read(path);baseline=backup(path);before=fingerprint(d,['art_layers','art_modules','natural_props','art_style_version']);grid=d['logic_grid'];w=d['map']['width'];h=d['map']['height']
  d['art_layers']=copy.deepcopy(baseline['art_layers']);d['art_modules']=copy.deepcopy(baseline['art_modules'])
  for m in d['art_modules']:
   if mods[m['name']]['kind'] not in ['forest']:continue
   ox,oy=m['origin'];mw,mh=m['footprint']
   for yy in range(oy,oy+mh):
    for xx in range(ox,ox+mw):d['art_layers'][2][yy][xx]=None
  d['art_modules']=[m for m in d['art_modules'] if mods[m['name']]['kind']!='forest']
  reserved=[]
  for m in d['art_modules']:reserved.append([m['origin'][0]*16,m['origin'][1]*16,m['footprint'][0]*16,m['footprint'][1]*16])
  points=d['player_positions']+[u['position'] for u in d['enemies']+d['npc_units']+d['reinforcements']]+d['targets']+[d['exit']]+[o['position'] for o in d['objects']]
  reserved += [[x*16-4,y*16-8,24,28] for x,y in points]
  props=[]
  for char,biome in [('f','snow' if path.stem=='M11' else 'forest'),('^','rock')]:
   allowed={(x,y) for y,row in enumerate(grid) for x,c in enumerate(row) if c==char}
   props+=scatter_cells(path.stem+char,allowed,biome,reserved)
   for x,y in allowed:
    d['art_layers'][1][y][x]=None
    family='snow' if path.stem=='M11' else 'cave' if path.stem=='S11' else 'grass'
    if char=='^':family='rock'
    d['art_layers'][0][y][x]=pack['base'][family][seed(f'{path.stem}:{x}:{y}')%4]
  d['natural_props']=props;d['art_style_version']='0.1.3'
  assert before==fingerprint(d,['art_layers','art_modules','natural_props','art_style_version']),path.stem+' gameplay modified'
  write(path,d);biome='snow' if path.stem=='M11' else 'forest' if path.stem=='S12' else 'rock'
  layouts[path.stem]={'biome':biome,'excluded':[[0,0,w*16,h*16]],'props':organic_exterior(path.stem,[w,h],biome,[[0,0,w*16,h*16]])}
  results.append({'stage':path.stem,'props':len(props),'gameplay_sha256':before,'gameplay_unchanged':True})
 return layouts,results
def world():
 path=ROOT/'data/formal_world.json';d=read(path);baseline=backup(path);before=fingerprint(d,['layers','modules','natural_props','art_style_version']);pack=read(ROOT/'assets/world_tiles/world-tiles.json');mods={m['name']:m for m in pack['modules']};w=d['width'];h=d['height']
 d['layers']=copy.deepcopy(baseline['layers']);d['layers'][2]=[[None]*w for _ in range(h)];d['modules']=[];reserved=set()
 for r in d['routes']:
  for x,y in r['cells']:reserved.add((x,y))
 for n in d['nodes'].values():
  m=mods[n['symbol']];mw,mh=m['footprint'];ox=n['x']-(mw-1)//2;oy=n['y']-mh+1
  reserved.update((ox+x,oy+y) for y in range(mh) for x in range(mw))
 # Remove the old hard rectangular forest edging as well as its group stamps.
 # Geography masks remain authoritative; organic art may soften their margin on
 # adjacent plain land, always outside the complete road-cell / node footprint.
 for y,row in enumerate(d['ground']):
  for x,kind in enumerate(row):
   if kind not in ['forest','rock']:continue
   d['layers'][1][y][x]=None
   family='snow' if y>45 and x<28 else 'grass'
   d['layers'][0][y][x]=pack['base_tiles'][family][seed(f'world-ground:{x}:{y}')%4]
 props=[]
 for kind in ['forest','rock']:
  base={(x,y) for y in range(h) for x in range(w) if d['ground'][y][x]==kind}
  allowed=set(base)
  for x,y in base:
   for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)]:
    xx,yy=x+dx,y+dy
    if 0<=xx<w and 0<=yy<h and d['ground'][yy][xx] in ['grass','snow']:allowed.add((xx,yy))
  allowed-=reserved
  rng=random.Random(seed('organic-world-'+kind));cells=sorted(base);rng.shuffle(cells)
  def legal(r):
   return all((xx,yy) in allowed for yy in range(math.floor(r[1]/16),math.ceil((r[1]+r[3])/16)) for xx in range(math.floor(r[0]/16),math.ceil((r[0]+r[2])/16)))
  for x,y in cells:
   if rng.random()<.18:continue
   snow=y>45 and x<28
   names=['snow_tall','snow_broad','snow_pair'] if snow and kind=='forest' else ['pine_tall','pine_broad','pine_pair'] if kind=='forest' else ['peak_low','crag_tall','ridge_bent','outcrop']
   for attempt in range(4):
    sprite=rng.choice(names);sw,sh=[v//2 for v in CAT[sprite]['size']];r=[x*16+rng.randint(-5,5),y*16+rng.randint(-5,5),sw,sh]
    if legal(r) and acceptable(r,props,.28):
     item=prop(sprite,*r[:2],rng);item['size']=[sw,sh];props.append(item);break
  # Occasional small isolated trees / rocks, not a fill of every remaining cell.
  for x,y in cells:
   if rng.random()>(.9 if kind=='forest' else .65):continue
   sprite=rng.choice(['snow_small_a','snow_small_b','snow_young']) if y>45 and x<28 and kind=='forest' else rng.choice(['pine_small_a','pine_small_b','pine_young']) if kind=='forest' else 'boulder'
   r=[x*16+rng.randint(-5,5),y*16+rng.randint(-4,5),*CAT[sprite]['size']]
   if legal(r) and acceptable(r,props,.18):props.append(prop(sprite,*r[:2],rng))
 d['natural_props']=sorted(props,key=lambda p:p['position'][1]+p.get('size',CAT[p['key']]['size'])[1])
 d['art_style_version']='0.1.3';assert before==fingerprint(d,['layers','modules','natural_props','art_style_version']),'world gameplay changed';write(path,d)
 atlas=Image.open(ROOT/'assets/world_tiles/world-tiles.png').convert('RGBA');out=Image.new('RGBA',(w*16,h*16))
 for layer in d['layers']:
  for y,row in enumerate(layer):
   for x,tid in enumerate(row):
    if tid is not None:out.alpha_composite(atlas.crop((tid%32*16,tid//32*16,tid%32*16+16,tid//32*16+16)),(x*16,y*16))
 for p in d['natural_props']:
  texture=Image.open(ROOT/CAT[p['key']]['path'].replace('res://','')).convert('RGBA')
  if p.get('size'):texture=texture.resize(tuple(p['size']),Image.Resampling.NEAREST)
  if p['flip']:texture=texture.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
  out.alpha_composite(texture,tuple(p['position']))
 out.convert('RGB').save(ROOT/'assets/world_tiles/formal-world-overview.png',optimize=True);out.save(REPORT/'natural-world.png',optimize=True)
 return {'modules':len(d['natural_props']),'gameplay_sha256':before,'gameplay_unchanged':True,'reserved_cells':len(reserved)}
if __name__=='__main__':
 hub=hubs();battle,results=battles();world_result=world();write(ROOT/'data/nature-layouts.json',{'version':'0.1.3','seed_policy':'fixed per scene; world-space placements survive viewport resizing','hubs':hub,'battles':battle})
 report={'stages':results,'world':world_result,'hubs':{k:len(v['props']) for k,v in hub.items()},'scope':'Art layers only; full sources, unchanged rules/roads/roster/dialogue'};write(REPORT/'build-report.json',report);print(json.dumps(report))
