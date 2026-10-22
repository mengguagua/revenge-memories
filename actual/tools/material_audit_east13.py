#!/usr/bin/env python3
"""Pure bitmap-material changes only; keep all 13 maps' geometry and campaign data."""
from pathlib import Path
from PIL import Image
import copy,hashlib,json,math,shutil,subprocess
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter5-spatial-20261022/material-audit';A=R/'assets/chapter5-spatial-20261022/east-materials';B=O/'east13-baseline'
CODES='F21 F22 F23 F24 F25 F26 S21 S22 F31 F32 F33 S31 S32'.split()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
B.mkdir(parents=True,exist_ok=True)
for code in CODES:
 p=R/f'data/stages/{code}.json';target=B/(code+'.json')
 if not target.exists():shutil.copy2(p,target)
patches={'timber':Image.open(A/'outdoor-timber.png').convert('RGBA'),'stone':Image.open(R/'assets/chapter5-spatial-20261022/library/interior-stone.png').convert('RGBA')};proof=[]
for code in ['F25','F31','F33','S31','S32']:
 old=json.loads((B/(code+'.json')).read_text());d=copy.deepcopy(old);w=d['map']['width'];h=d['map']['height'];source=R/d['art_atlas'].removeprefix('res://');im=Image.open(source).convert('RGBA');columns=d.get('art_columns',32)
 cells=[im.crop((x,y,x+16,y+16))for y in range(0,im.height,16)for x in range(0,im.width,16)]
 ground=d['visual_ground'];interior=code in ['S31','S32'];patch=patches['stone'if interior else'timber']
 selected={(x,y)for y,row in enumerate(ground)for x,q in enumerate(row)if(q=='c'and d['logic_grid'][y][x]=='c')if interior}if interior else{(x,y)for y,row in enumerate(ground)for x,q in enumerate(row)if q=='s'and(code!='F31'or x>=7)}
 # Preserve existing perimeter pixels and silhouette. The only replacement is
 # the surface inside each already-authored timber cell.
 for x,y in sorted(selected):
  old_id=d['art_layers'][0][y][x];tile=cells[old_id].copy();p=patch.crop((x%4*16,y%4*16,x%4*16+16,y%4*16+16))
  left=2 if(x-1,y)not in selected else 0;right=14 if(x+1,y)not in selected else 16
  top=2 if(x,y-1)not in selected else 0;bottom=14 if(x,y+1)not in selected else 16
  tile.paste(p.crop((left,top,right,bottom)),(left,top));d['art_layers'][0][y][x]=len(cells);cells.append(tile)
 atlas=Image.new('RGBA',(columns*16,math.ceil(len(cells)/columns)*16))
 for i,tile in enumerate(cells):atlas.paste(tile,(i%columns*16,i//columns*16))
 target=A/(code+'-terrain.png');atlas.save(target);subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(target)],check=True)
 d['art_atlas']='res://'+str(target.relative_to(R));d['material_review_version']='0.10.10-material'
 changed=[k for k in d if old.get(k)!=d[k]];assert set(changed)=={'art_atlas','art_layers','material_review_version'},(code,changed)
 assert old['map']==d['map']and old['logic_grid']==d['logic_grid']
 for key in['player_positions','enemies','npc_units','objects','reinforcements','exit','targets','terrain']:assert old[key]==d[key],(code,key)
 write(R/f'data/stages/{code}.json',d)
 proof.append({'code':code,'passed':True,'changed_fields':changed,'replaced_cells':[list(p)for p in sorted(selected)],'count':len(selected),'geometry_rules_all_coordinates_identical':True,'before_sha256':sha(B/(code+'.json')),'map_sha256':sha(R/f'data/stages/{code}.json'),'source_atlas':str(source.relative_to(R)),'runtime_atlas':d['art_atlas'],'atlas_size':list(atlas.size),'atlas_bytes':target.stat().st_size})
for code in set(CODES)-{'F25','F31','F33','S31','S32'}:assert sha(B/(code+'.json'))==sha(R/f'data/stages/{code}.json')
write(O/'east13-material-proof.json',{'passed':True,'scope':'Only F25 outdoor jetty, F31 shore-side timber/gangway, F33 external maintenance bridge, and the12 walkable interior stone cells of S31/S32 each. Ship decks retain their fitted timber; outdoor approach routes and prison-door open_art_cells are unchanged. No geometry, coordinates, unit values, action rules, interactions or core code changed.','maps':proof,'unchanged':[c for c in CODES if c not in['F25','F31','F33','S31','S32']]})
print(json.dumps({'passed':True,'changed_maps':[p['code']for p in proof],'cells':sum(p['count']for p in proof),'others_unchanged':8}))
