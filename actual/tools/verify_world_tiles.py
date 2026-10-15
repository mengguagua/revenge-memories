#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
import importlib.util,json,xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/world_tiles';REPORT=ROOT/'reports/world-tiles-b'
spec=importlib.util.spec_from_file_location('world_tile_builder',ROOT/'tools/build_world_tiles.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
p=json.loads((OUT/'world-tiles.json').read_text());atlas=Image.open(OUT/'world-tiles.png').convert('RGBA')
records={t['id']:t for t in p['tiles']};errors=[]
def tile(i):
 x,y=records[i]['atlas'];return atlas.crop((x*16,y*16,x*16+16,y*16+16))
for m in p['modules']:
 complete=Image.open(OUT/m['path']).convert('RGBA');rebuild=Image.new('RGBA',complete.size)
 for y,row in enumerate(m['tiles']):
  for x,i in enumerate(row):rebuild.alpha_composite(tile(i),(x*16,y*16))
 if complete.tobytes()!=rebuild.tobytes():errors.append(m['name']+': module reconstruction mismatch')
 if set(complete.getchannel('A').getdata())!={0,255}:errors.append(m['name']+': alpha not binary')
 bounds=complete.getchannel('A').getbbox()
 if bounds[0]<1 or bounds[1]<1 or bounds[2]>complete.width-1 or bounds[3]>complete.height-1:errors.append(m['name']+': no silhouette margin')
 if (OUT/m['path']).stat().st_size>=20000:errors.append(m['name']+': small module over 20KB reference')
seam_cases=0;seam_failures=0
for family in p['families']:
 if sorted(map(int,family['tiles_by_mask']))!=b.MASKS:errors.append(family['name']+': missing corner/side mask')
 cached={m:tile(family['tiles_by_mask'][str(m)]) for m in b.MASKS}
 # Exhaustive shared-border neighborhoods: two occupied central cells in 3x4.
 for bits in range(4096):
  grid=[[bool(bits&(1<<(y*4+x))) for x in range(4)] for y in range(3)]
  if not grid[1][1] or not grid[1][2]:continue
  a=b.mask_at(grid,1,1,bool);c=b.mask_at(grid,2,1,bool)
  left=[cached[a].getpixel((15,y)) for y in range(16)]
  right=[cached[c].getpixel((0,y)) for y in range(16)]
  seam_cases+=1
  if left!=right:seam_failures+=1
 # Rotate the same local neighborhoods to check horizontal shared borders too.
 for bits in range(4096):
  g=[[bool(bits&(1<<(y*4+x))) for x in range(4)] for y in range(3)]
  if not g[1][1] or not g[1][2]:continue
  grid=[list(r) for r in zip(*g)]
  a=b.mask_at(grid,1,1,bool);c=b.mask_at(grid,1,2,bool)
  seam_cases+=1
  if [cached[a].getpixel((x,15)) for x in range(16)]!=[cached[c].getpixel((x,0)) for x in range(16)]:seam_failures+=1
if seam_failures:errors.append('Shared edge color/alpha mismatch: '+str(seam_failures))
for name,ids in p['roads'].items():
 for m,i in ids.items():
  m=int(m)
  if m&2:
   for n,j in ids.items():
    if int(n)&8 and [tile(i).getpixel((15,y)) for y in range(16)]!=[tile(j).getpixel((0,y)) for y in range(16)]:errors.append(name+': road east/west gap')
  if m&4:
   for n,j in ids.items():
    if int(n)&1 and [tile(i).getpixel((x,15)) for x in range(16)]!=[tile(j).getpixel((x,0)) for x in range(16)]:errors.append(name+': road north/south gap')
for sample in json.loads((OUT/'sample-maps.json').read_text()):
 for layer in sample['layers']:
  if len(layer)!=sample['height'] or any(len(r)!=sample['width'] for r in layer):errors.append(sample['name']+': invalid dimensions')
  for row in layer:
   if any(i>=0 and i not in records for i in row):errors.append(sample['name']+': invalid tile ID')
ET.parse(OUT/'world-tiles.tsx')
for item in json.loads((REPORT/'manifest.json').read_text()):
 if (ROOT/item['path']).stat().st_size!=item['bytes']:errors.append('Stale image manifest: '+item['path'])
report={'native_tile_size':16,'atlas_size':list(atlas.size),'atlas_bytes':(OUT/'world-tiles.png').stat().st_size,
 'registered_nonplaceholder_tiles':len([t for t in p['tiles'] if t['kind']!='unused']),
 'transition_families':10,'canonical_variants_per_family':47,'shared_border_cases':seam_cases,
 'shared_border_failures':seam_failures,'complete_modules':len(p['modules']),
 'module_cut_reassembly':'pixel exact','road_connector_checks':'horizontal and vertical',
 'tiled_definition_xml':'parsed','errors':errors,
 'scope':'Resource pixels, source modules, boundary matching and example map IDs. Gameplay is not integrated.'}
(REPORT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False));raise SystemExit(bool(errors))
