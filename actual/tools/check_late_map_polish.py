#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check geometry changes against frozen same-session stage cards."""
from pathlib import Path
from collections import deque
from PIL import Image
import json,hashlib,sys
R=Path(__file__).resolve().parents[1];OUT=R/'reports/map-polish-late-20261022';BASE=OUT/'baseline'
codes=sys.argv[1:] or json.loads((OUT/'codes.json').read_text())
errors=[];checks=0;records=[]
def check(v,label):
 global checks
 checks+=1
 if not v:errors.append(label)
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
locked=['schema_version','id','code','name_zh','chapter','route','node','characters','player_positions','enemies','npc_units','terrain','enemy_group_ids','objects','reinforcements','reinforcement_turn','exit','boss_id','targets','goal','cause','before','during','after','absent_branch','optional','contract','ai_and_timing','event_boats','equipment_revision','clear_training_exp','escort_move','burner_departure_turn','assault_gate','camp_checkpoints','detention_bays','recovery_sites']
ids={'.':48,',':48,'n':48,'m':66,'f':172,'^':94,'d':242,'~':96,'#':196,'=':208,'c':208,'s':191,'b':48,'+':218,'a':48,'p':208}
for code in codes:
 p=R/f'data/stages/{code}.json';d=read(p);old=read(BASE/p.name);w=d['map']['width'];h=d['map']['height']
 for k in locked:
  if code=='F25' and k=='npc_units':
   check(len(d[k])==len(old[k]),'F25 witness count unchanged')
   for a,b in zip(old[k],d[k]):
    check({key:value for key,value in a.items()if key!='position'}=={key:value for key,value in b.items()if key!='position'},'F25 witness only position changed: '+b['id'])
    check(b['position']==({'sailors0':[35,19],'sailors1':[37,19]}[b['id']]),'F25 witness inside actual eastern prison: '+b['id'])
  else:check(d.get(k)==old.get(k),f'{code} gameplay field changed: {k}')
 check([w,h]==[old['map']['width'],old['map']['height']],code+' dimensions')
 check(d['map']['tiles']==[ids[q]for row in d['logic_grid']for q in row],code+' logical terrain types')
 check(d['tactical_review_version']=='0.10.3',code+' revision')
 for key in ['logic_grid']+(['visual_ground'] if 'visual_ground' in d else []):
  check(len(d[key])==h and all(len(row)==w for row in d[key]),f'{code} {key} complete')
 atlas=R/d['art_atlas'].removeprefix('res://');check(atlas.is_file(),code+' atlas exists')
 atlas_im=Image.open(atlas);count=atlas_im.width//16*(atlas_im.height//16)
 for layer in d['art_layers']:
  check(len(layer)==h and all(len(row)==w for row in layer),code+' layer dimensions')
  check(all(v is None or 0<=v<count for row in layer for v in row),code+' layer indices valid')
 for prop in d['art_props']:
  path=R/prop['path'].removeprefix('res://');check(path.is_file(),f'{code} prop {prop["path"]}')
  if path.is_file():
   image=Image.open(path);x,y=prop['position'];check(x>=-32 and y>=-32 and x+image.width<=w*16+32 and y+image.height<=h*16+32,f'{code} complete prop {path.name}')
 changes={k for k in set(d)|set(old) if d.get(k)!=old.get(k)}
 terrain_changes=sum(a!=b for a,b in zip(d['map']['tiles'],old['map']['tiles']))
 records.append({'code':code,'hash':sha(p),'fields':sorted(changes),'terrain_cells_changed':terrain_changes,'props':len(d['art_props']),'nature_props':len(d['natural_props']),'atlas':d['art_atlas']})
for code,expected in read(BASE/'hashes.json').items():
 if code not in read(OUT/'codes.json'):check(sha(R/f'data/stages/{code}.json')==expected,code+' already reviewed map unchanged')
report={'passed':not errors,'checks':checks,'errors':errors,'maps':records,'scope':'Same-session frozen map comparison, gameplay invariants, full image footprints, logic/art indices; combat and save checks separate.'}
(OUT/'geometry.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'passed':not errors,'checks':checks,'errors':errors,'maps':records},ensure_ascii=False,indent=2));sys.exit(bool(errors))
