#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Select only clean individual wins, retaining mixed/failed attempts separately."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];O=R/'reports/map-polish-20261022'
codes=['M12','M13','M14','M15','S11','S12','F21','F22','F23','F24','F25','F26','S21','S22']
selected={}
for p in sorted((O/'play').glob('*/*-play.json'),key=lambda p:p.stat().st_mtime):
 d=json.loads(p.read_text())
 for b in d['battles']:
  if b['code']in codes and b['outcome']=='victory' and not b.get('failures') and not d['stat_edits'] and not d['forced_victories']:
   selected[b['code']]=p.parent.name
missing=set(codes)-set(selected);assert not missing,sorted(missing)
focus={'M12':[26,10],'M13':[20,10],'M14':[24,18],'M15':[25,10],'S11':[17,14],'S12':[17,11],'F21':[21,11],'F22':[33,13],'F23':[24,18],'F24':[23,17],'F25':[36,20],'F26':[25,18],'S21':[17,13],'S22':[24,17]}
shots=[]
for code in codes:
 label=selected[code]
 for mode,size in [('entry',[562,320]),('field',[426,240])]:
  source=f'res://reports/map-polish-20261022/play/{label}/{label}-{code}-{mode}.json'
  p=R/source.removeprefix('res://');assert p.exists(),p
  snapshot=json.loads(p.read_text());assert snapshot['map_revision']=='0.10.2'
  shots.append({'name':code+'-'+mode,'source':source,'focus':focus[code],'width':size[0],'height':size[1]})
for code in ['M12','S11','F25']:
 label=selected[code];shots.append({'name':code+'-objective-notes','source':f'res://reports/map-polish-20261022/play/{label}/{label}-{code}-entry.json','focus':focus[code],'width':426,'height':240,'note_page':2})
(O/'selected-playthroughs.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2)+'\n')
(O/'capture-jobs.json').write_text(json.dumps({'shots':shots},ensure_ascii=False,indent=2)+'\n')
print('Selected',len(selected),'clean wins and',len(shots),'runtime viewport jobs.')
