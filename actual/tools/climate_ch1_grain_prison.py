#!/usr/bin/env python3
"""M12/M13 winter art only, from the current frozen climate baseline."""
from pathlib import Path
from PIL import Image
import copy,hashlib,importlib.util,json,math,subprocess
R=Path(__file__).resolve().parents[1]
O=R/'reports/chapter1-climate-20261022/grain-prison'
BASE=O.parent/'baseline';ART=R/'assets/chapter1-climate-20261022/grain-prison'
spec=importlib.util.spec_from_file_location('climate_native',R/'tools/polish_chapter4_20261022.py')
L=importlib.util.module_from_spec(spec);spec.loader.exec_module(L);B=L.B
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
WINTER_NATURE={'pine_tall':'snow_tall','pine_broad':'snow_broad','pine_young':'snow_young','pine_pair':'snow_pair','pine_small_a':'snow_small_a','pine_small_b':'snow_small_b','boulder':'snow_boulder',**{k:'climate_snow_'+k for k in ['peak_low','crag_tall','ridge_bent','outcrop']}}
NATURE={a['key']:a for a in read(R/'assets/nature/nature.json')['sprites']}
NATURE.update({a['key']:a for a in read(R/'source/chapter1-climate-20261022/nature/export.json')})
GENERATED={'hill_granary','village_clinic','command_pavilion','quay_warehouse','barracks'}
def run(code):
 old=read(BASE/(code+'.json'));d=copy.deepcopy(old);w,h=old['map']['width'],old['map']['height']
 original_atlas=R/old['art_atlas'].removeprefix('res://');im=Image.open(original_atlas).convert('RGBA')
 L.ART=ART/code;A=L.Atlas()
 A.cells=[im.crop((x,y,x+16,y+16))for y in range(0,im.height,16)for x in range(0,im.width,16)]
 A.original=len(A.cells)
 vg=old['visual_ground'];g=old['logic_grid'];base=copy.deepcopy(old['art_layers'][0]);protected=set()
 if code=='M13':
  for obj in old['objects']:
   if obj['kind']=='door':
    x,y=obj['position'];protected.add((x,y))
    protected.update((xx,yy)for xx in range(x-1,x+2)for yy in range(y-2,y))
 mats=[]
 for y in range(h):
  row=[]
  for x in range(w):
   q=vg[y][x]
   material={'p':'dirt','c':'cobble','s':'timber','~':'sea'}.get(q,'snow')
   if code=='M13' and q=='.':
    # Coherent exposed earth on busy lower yards, not random summer-grass cells.
    bare=((x-21)/5.5)**2+((y-20)/3.7)**2<1 or ((x-9)/3.8)**2+((y-14)/2.6)**2<1
    if bare:material='dirt'
   if(x,y)in protected:material='indoor_stone'
   row.append(material)
  mats.append(row)
 for y in range(h):
  for x in range(w):
   q=vg[y][x];mat=mats[y][x];v=B.seed(f'{code}:winter:{x}:{y}')%4
   if(x,y)in protected:continue
   if q=='s':continue # Keep exact native plank direction and complete bridge edges.
   if q=='~':
    ns=[mats[y+dy][x+dx]if 0<=x+dx<w and 0<=y+dy<h else'sea'for dx,dy in[(0,-1),(1,0),(0,1),(-1,0)]]
    base[y][x]=A.water([('stone'if a=='indoor_stone'else a)for a in ns],v);continue
   if q in'pc':
    mask=B.mask_at(vg,x,y,lambda t:t in'pcs')
    base[y][x]=A.edge(mat,'snow',mask,v);continue
   if mat=='dirt':
    grid=[['d'if z=='dirt'else'n'for z in rr]for rr in mats]
    mask=B.mask_at(grid,x,y,lambda z:z=='d')
    base[y][x]=A.edge('dirt','snow',mask,v)
   else:base[y][x]=B.PACK['base'][mat][v]
 d['art_layers'][0]=base;A.save();d['art_atlas']='res://'+str((ART/code/'terrain.png').relative_to(R))
 prop_changes=[]
 for p in d['art_props']:
  name=Path(p['path']).stem
  if name in GENERATED:
   previous=p['path'];p['path']='res://'+str((ART/'modules'/f'{name}.png').relative_to(R));prop_changes.append({'from':previous,'to':p['path'],'position':p['position']})
  elif name=='tactical_store':
   previous=p['path'];p['path']='res://assets/battlefield-0.3.0/modules/tactical_snow_house.png';prop_changes.append({'from':previous,'to':p['path'],'position':p['position'],'reason':'Same16px storage/outpost footprint, complete existing snowy house bitmap.'})
 nature_changes=[]
 for p in d['natural_props']:
  old_key=p['key'];new_key=WINTER_NATURE.get(old_key)
  if new_key:
   assert NATURE[old_key]['size']==NATURE[new_key]['size']
   p['key']=new_key;nature_changes.append({'from':old_key,'to':new_key,'position':p['position']})
 d['nature_layout']['biome']='snow';d['material_review_version']='0.10.11-climate'
 d['climate_review']={'chapter':1,'phase':'before_day_return','environment':'snowy grain depot'if code=='M12'else'patchy snow at a cold prison valley','snow_outside_only':True,'geometry_and_rules_unchanged':True}
 d['location_theme']=('寒地丘堡粮站：雪林粮车坡路、清扫仓坪与冬屋'if code=='M12'else'残雪溪谷押送所：两岸冬营、双木桥、无雪牢室石地')
 notes=copy.deepcopy(old.get('tactical_notes',[]))
 notes=[n.replace('仓院之外保留草地展开面','仓院之外保留积雪展开面')for n in notes]
 notes.append('日返前寒地外景：积雪、雪松与冬季屋顶一致；清扫土路、门前踏实地和室内石地按用途露出，河水与木桥保持原通行规则。'if code=='M12'else'雪缘过渡由较多积雪与连贯裸土车场组成，不使用夏季绿草；室内牢房及开门后石门槛不覆雪，全部道路、桥宽和护送判定保持。')
 d['tactical_notes']=notes;d['visual_notes']=notes.copy()
 allow={'art_atlas','art_layers','art_props','natural_props','nature_layout','material_review_version','climate_review','location_theme','tactical_notes','visual_notes'}
 assert all(old.get(k)==d.get(k) for k in set(old)|set(d) if k not in allow)
 assert d['map']==old['map'] and d['logic_grid']==old['logic_grid']
 assert d['objects']==old['objects']
 assert all(d['art_layers'][0][y][x]==old['art_layers'][0][y][x]for x,y in protected)
 for p,q in zip(old['art_props'],d['art_props']):
  assert {k:v for k,v in p.items()if k!='path'}=={k:v for k,v in q.items()if k!='path'}
  assert Image.open(R/p['path'].removeprefix('res://')).size==Image.open(R/q['path'].removeprefix('res://')).size
 for p,q in zip(old['natural_props'],d['natural_props']):assert{k:v for k,v in p.items()if k!='key'}=={k:v for k,v in q.items()if k!='key'}
 path=R/f'data/stages/{code}.json';write(path,d)
 report={'passed':True,'code':code,'size':[w,h],'map_sha256':sha(path),'baseline_sha256':sha(BASE/(code+'.json')),
  'map_tiles_logic_all_coordinates_stats_objects_story_unchanged':True,'door_open_art_exactly_preserved':True,'protected_indoor_and_threshold_cells':[list(p)for p in sorted(protected)],
  'material_counts':{m:sum(rr.count(m)for rr in mats)for m in sorted(set(sum(mats,[])))},'material_grid':mats,
  'winter_props':prop_changes,'winter_nature':nature_changes,'ground_source':'Existing native snow4..7/dirt8..11 and same original bitmap-edge masks; all bridge art retained; no added gameplay terrain effects.',
  'notes':notes,'generated_modules_export':'source/chapter1-climate-20261022/grain-prison/export.json'}
 write(O/f'{code}-climate.json',report);return report
if __name__=='__main__':
 reports=[run(c)for c in ['M12','M13']]
 write(O/'climate-summary.json',{'passed':True,'maps':reports})
 print(json.dumps([{'code':m['code'],'passed':m['passed'],'materials':m['material_counts']}for m in reports]))
