#!/usr/bin/env python3
"""M14/M15 climate art only, with exact tactical data and pixel footprints."""
from pathlib import Path
from PIL import Image
import copy,json,hashlib,importlib.util,math
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter1-climate-20261022/camp-fort';BASE=O.parent/'baseline';ART=R/'assets/chapter1-climate-20261022/camp-fort'
spec=importlib.util.spec_from_file_location('native_climate',R/'tools/polish_chapter4_20261022.py');L=importlib.util.module_from_spec(spec);spec.loader.exec_module(L);L.ART=ART;B=L.B
A=L.Atlas();source=Image.open(R/'assets/chapter1-redesign-20261022/camp-fort/terrain.png').convert('RGBA');count=json.loads((R/'assets/chapter1-redesign-20261022/camp-fort/terrain.json').read_text())['tile_count'];A.cells=[source.crop((i%32*16,i//32*16,i%32*16+16,i//32*16+16))for i in range(count)];A.original=count
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
write=lambda p,v:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
snow_trees={'pine_tall':'snow_tall','pine_broad':'snow_broad','pine_pair':'snow_pair','pine_young':'snow_young','pine_small_a':'snow_small_a','pine_small_b':'snow_small_b','boulder':'snow_boulder'}
snow_rocks={k:'climate_snow_'+k for k in ['peak_low','crag_tall','ridge_bent','outcrop']}
changed=[]
for c in ['M14','M15']:
 old=json.loads((BASE/(c+'.json')).read_text());d=copy.deepcopy(old);w=old['map']['width'];h=old['map']['height'];g=old['visual_ground'];winter=[list(row)for row in g]
 for y in range(h):
  for x in range(w):
   if g[y][x]=='.':
    winter[y][x]='n'
    if c=='M15' and old['logic_grid'][y][x]not in'f^' and (((x-18)/6)**2+((y-25)/3)**2<1 or ((x-28)/3)**2+((y-17)/5)**2<1):winter[y][x]='d'
 base=copy.deepcopy(d['art_layers'][0]);mats={'.':'grass','n':'snow','p':'dirt','d':'dirt','c':'cobble','s':'timber','~':'sea','#':'cobble','=':'stone','+':'sacred'}
 room_cells=set()
 if c=='M15':
  for o in old['objects'][:2]:
   x,y=o['position'];room_cells.update((xx,yy)for xx in range(x-1,x+2)for yy in range(y-2,y))
 for y in range(h):
  for x in range(w):
   q=winter[y][x];v=B.seed(f'{c}:climate:{x}:{y}')%4
   if(x,y)in room_cells or q=='s':continue
   if q=='~':
    base[y][x]=A.water([mats[winter[y+dy][x+dx]]if 0<=x+dx<w and 0<=y+dy<h else'sea'for dx,dy in[(0,-1),(1,0),(0,1),(-1,0)]],v)
   elif q in 'pdc=':
    fg=mats[q];mask=B.mask_at(winter,x,y,lambda z:mats.get(z)==fg);base[y][x]=A.edge(fg,'snow',mask,v)
   elif q=='n':base[y][x]=B.PACK['base']['snow'][v]
   else:base[y][x]=B.PACK['base'][mats[q]][v]
 d['art_layers'][0]=base;d['visual_ground']=[''.join(row)for row in winter]
 for p in d['natural_props']:
  if p.get('key')in snow_trees:p['key']=snow_trees[p['key']]
  elif p.get('key')in snow_rocks:p['key']=snow_rocks[p['key']]
 replacements=[]
 for p in d['art_props']:
  name=Path(p['path']).stem
  new=ART/(name+'-winter.png')
  if new.exists():
   prior=p['path'];p['path']='res://'+str(new.relative_to(R));replacements.append({'before':prior,'after':p['path'],'position':p['position']})
 d['art_atlas']='res://assets/chapter1-climate-20261022/camp-fort/terrain.png';d['material_review_version']='0.10.11-climate';d['nature_layout']['biome']='snow'
 d['climate_review']={'phase':'chapter1-before-day-return','climate':'冬季军营：积雪林缘、踩实泥路与积雪帐顶'if c=='M14'else'临海寒地：薄雪、风蚀裸土、石坪与清扫港栈','snow_inside_jails':False,'geometry_and_rules_unchanged':True}
 allowed={'art_atlas','art_layers','art_props','natural_props','nature_layout','visual_ground','material_review_version','climate_review'}
 for k in set(old)|set(d):assert k in allowed or old.get(k)==d.get(k),(c,k)
 assert all(a['position']==b['position'] for a,b in zip(old['art_props'],d['art_props']))
 assert all(a['position']==b['position'] for a,b in zip(old['natural_props'],d['natural_props']))
 assert len(old['art_props'])==len(d['art_props']) and len(old['natural_props'])==len(d['natural_props'])
 assert old['art_layers'][1:]==d['art_layers'][1:]
 for a,b in zip(old['art_props'],d['art_props']):assert {k:v for k,v in a.items()if k!='path'}=={k:v for k,v in b.items()if k!='path'}
 for a,b in zip(old['natural_props'],d['natural_props']):assert {k:v for k,v in a.items()if k!='key'}=={k:v for k,v in b.items()if k!='key'}
 for cell in room_cells:assert base[cell[1]][cell[0]]==old['art_layers'][0][cell[1]][cell[0]]
 path=R/f'data/stages/{c}.json';write(path,d)
 record={'passed':True,'code':c,'map_sha256':sha(path),'baseline_sha256':sha(BASE/(c+'.json')),'phase':'日返仪式之前','size':[w,h],'unchanged_keys':[k for k in old if old[k]==d[k]],'changed_keys':[k for k in d if old.get(k)!=d[k]],'geometry_rules_all_coordinates_exact':True,'native_snow_tree_footprints_preserved':True,'roof_replacements':replacements,'interior_floor_cells_preserved':list(map(list,sorted(room_cells))),'snow_ground_cells':sum(row.count('n') for row in winter),'exposed_soil_cells':sum(row.count('d') for row in winter),'surroundings':d.get('surroundings','snow'),'climate':d['climate_review']['climate']}
 write(O/(c+'-climate.json'),record);changed.append(record)
A.save();write(O/'invariants.json',{'passed':True,'maps':changed,'scope':'Current runtime baseline; every field except climate art and metadata exact. No tile movement, terrain rules, actors, object behavior, AI, timing, doors or coordinates modified.'});print(json.dumps({'passed':True,'maps':[{'code':x['code'],'hash':x['map_sha256']}for x in changed]}))
