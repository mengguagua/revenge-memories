#!/usr/bin/env python3
"""S12 winter material layer; S11 remains an unaltered underground mine."""
from pathlib import Path
from PIL import Image
import copy,hashlib,json,math,subprocess
R=Path(__file__).resolve().parents[1]
O=R/'reports/chapter1-climate-20261022/side'
BASE=O.parent/'baseline'
ART=R/'assets/chapter1-climate-20261022/side'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def mask_at(grid,x,y,predicate):
 peers=[(0,-1,1),(1,0,2),(0,1,4),(-1,0,8),(1,-1,16),(1,1,32),(-1,1,64),(-1,-1,128)]
 mask=sum(bit for dx,dy,bit in peers if 0<=y+dy<len(grid) and 0<=x+dx<len(grid[0]) and predicate(grid[y+dy][x+dx]))
 for diagonal,a,b in [(16,1,2),(32,2,4),(64,4,8),(128,8,1)]:
  if not(mask&a and mask&b):mask&=~diagonal
 return mask
def run():
 old=read(BASE/'S12.json');d=copy.deepcopy(old);w,h=old['map']['width'],old['map']['height']
 old_atlas=Image.open(R/old['art_atlas'].removeprefix('res://')).convert('RGBA')
 native=read(R/'assets/battlefield-0.3.0/terrain.json')['transitions']
 pack=read(R/'assets/battle_tiles/battle-tiles.json')
 cells=[];lookup={};source_ids=[]
 def tile(i):
  if i is None:return None
  i=int(i)
  if i not in lookup:
   lookup[i]=len(cells);cells.append(old_atlas.crop((i%32*16,i//32*16,i%32*16+16,i//32*16+16)));source_ids.append(i)
  return lookup[i]
 ground=old['visual_ground'];base=[];material_counts={}
 for y,row in enumerate(ground):
  line=[]
  for x,q in enumerate(row):
   v=int(hashlib.sha256(f'S12:winter:{x}:{y}'.encode()).hexdigest()[:8],16)%4
   if q=='p':
    mask=mask_at(ground,x,y,lambda z:z in 'ps')
    i=native['snow_path'][str(mask)][v];material='snow-edged compacted dirt'
   elif q=='~':
    key=''
    for dx,dy in [(0,-1),(1,0),(0,1),(-1,0)]:
     n=ground[y+dy][x+dx] if 0<=x+dx<w and 0<=y+dy<h else '~'
     key+='w' if n in '~s' else 'p' if n=='p' else 'n'
    i=native['winter_river'][key][v];material='flowing water with snow banks'
   elif q=='s':i=old['art_layers'][0][y][x];material='unchanged directional wooden bridge'
   else:i=pack['base']['snow'][v];material='snow outdoor ground'
   line.append(tile(i));material_counts[material]=material_counts.get(material,0)+1
  base.append(line)
 d['art_layers']=[base]+[[[tile(v) for v in row]for row in layer]for layer in old['art_layers'][1:]]
 tree_map={'pine_tall':'snow_tall','pine_broad':'snow_broad','pine_pair':'snow_pair',
  'pine_young':'snow_young','pine_small_a':'snow_small_a','pine_small_b':'snow_small_b','boulder':'snow_boulder'}
 tree_map.update({key:'climate_snow_'+key for key in ['peak_low','crag_tall','ridge_bent','outcrop']})
 nature={n['key']:n for n in read(R/'assets/nature/nature.json')['sprites']}
 changes=[]
 for item in d['natural_props']:
  key=item['key'];replacement=tree_map.get(key,key)
  assert nature[key]['size']==nature[replacement]['size'],(key,replacement)
  if key!=replacement:changes.append({'from':key,'to':replacement,'position':item['position']})
  item['key']=replacement
 prop_replacements={
  'res://assets/battlefield-0.3.0/modules/fishing_cottage.png':'res://assets/battle_tiles/modules/snow_cottage.png',
  'res://assets/battlefield-0.3.0/modules/tactical_house.png':'res://assets/battlefield-0.3.0/modules/tactical_snow_house.png',
 }
 clinic=R/'assets/chapter1-climate-20261022/grain-prison/modules/village_clinic.png'
 if clinic.exists():prop_replacements['res://assets/battlefield-0.3.0/modules/village_clinic.png']='res://'+str(clinic.relative_to(R))
 for prop in d['art_props']:
  old_path=prop['path'];new_path=prop_replacements.get(old_path,old_path)
  assert Image.open(R/old_path.removeprefix('res://')).size==Image.open(R/new_path.removeprefix('res://')).size,(old_path,new_path)
  prop['path']=new_path
 d['nature_layout']['biome']='snow'
 d['art_atlas']='res://assets/chapter1-climate-20261022/side/terrain.png'
 d['material_review_version']='0.10.11-climate'
 d['climate_notes']=[
  '日返前的雪林诊所：室外地表、林冠和屋舍积雪；南村药车道与诊所前清扫院为压实土路，保留可读的雪缘。',
  '河道仍是开放流水，两座桥保持原木板与通行宽度；雪不覆盖桥面材质，也不把河道伪装成可行走冰面。',
  '冷季外观只改变美术，地图逻辑、通行代价、敌我部署、药车轨迹、交互与剧情完全保持。']
 ART.mkdir(parents=True,exist_ok=True)
 atlas=Image.new('RGBA',(512,math.ceil(len(cells)/32)*16))
 for i,im in enumerate(cells):atlas.paste(im,(i%32*16,i//32*16))
 atlas.save(ART/'terrain.png');subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(ART/'terrain.png')],check=True)
 allowed={'art_layers','art_atlas','natural_props','art_props','nature_layout','material_review_version','climate_notes'}
 for k in sorted(set(old)|set(d)):
  if k not in allowed:assert old.get(k)==d.get(k),k
 for before,after in zip(old['natural_props'],d['natural_props']):
  assert {k:v for k,v in before.items()if k!='key'}=={k:v for k,v in after.items()if k!='key'}
 for before,after in zip(old['art_props'],d['art_props']):
  assert {k:v for k,v in before.items()if k!='path'}=={k:v for k,v in after.items()if k!='path'}
 # Compact atlas contains exact native 16px cells; no recoloring/resizing/AI edits here.
 for i,source in enumerate(source_ids):
  exact=old_atlas.crop((source%32*16,source//32*16,source%32*16+16,source//32*16+16))
  assert exact.tobytes()==cells[i].tobytes()
 write(R/'data/stages/S12.json',d)
 write(ART/'terrain.json',{'source':old['art_atlas'],'tile_size':16,'columns':32,'native_cells_reindexed':source_ids,'pixels_unchanged':True,'purpose':'Native snow ground/snow-path/winter-river plus original bridge cells; no shared asset modified.'})
 changed=[k for k in sorted(set(old)|set(d))if old.get(k)!=d.get(k)]
 report={'passed':True,'code':'S12','map_sha256':sha(R/'data/stages/S12.json'),'baseline_sha256':sha(BASE/'S12.json'),
  'size':[w,h],'changed_keys':changed,'geometry_rules_coordinates_unchanged':True,'nature_positions_and_dimensions_unchanged':True,
  'prop_positions_and_dimensions_unchanged':True,'materials':material_counts,'tree_changes':changes,'prop_replacements':prop_replacements,
  'tile_pixels_native_unchanged':True,'atlas':{'path':str((ART/'terrain.png').relative_to(R)),'size':list(atlas.size),'bytes':(ART/'terrain.png').stat().st_size},
  'clinic_winter_ready':clinic.exists(),'snow_covers_only_outdoor_ground':True,'notes':d['climate_notes']}
 write(O/'S12-review.json',report)
 assert sha(R/'data/stages/S11.json')==sha(BASE/'S11.json')
 write(O/'S11-review.json',{'passed':True,'code':'S11','unchanged':True,'map_sha256':sha(BASE/'S11.json'),
  'world_context':'S01矿口位于雪区，进入战斗后是地下矿厅。',
  'story_evidence':['docs2/完整故事剧情.md:306：贝克与矿工被堵在塌道后，工具和被押送者遗物仍在深处。','S11.before：工具还在里面；先带他们出去。'],
  'current_space':'矿厅、岩柱、装卸厅与北侧矿口内缘，当前没有可见的室外地表区域。',
  'decision':'地下岩地无需覆雪；保留上轮已纠正的碎石矿道和去草边岩体。世界地图矿口雪区由世界气候层处理，不把积雪延伸进地下。'})
 print(json.dumps({'passed':True,'code':'S12','native_tiles':len(cells),'atlas_bytes':(ART/'terrain.png').stat().st_size,'clinic_ready':clinic.exists()}))
if __name__=='__main__':run()
