#!/usr/bin/env python3
"""Select current-map genuine wins, retaining every failed/retried attempt."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];O=R/'reports/map-polish-late-20261022'
read=lambda p:json.loads(p.read_text())
codes=sorted(read(O/'codes.json'),key=lambda c:read(R/f'data/stages/{c}.json')['id'])
selected={}
for p in sorted((O/'play').glob('*/*-play.json'),key=lambda p:p.stat().st_mtime):
 d=read(p)
 if d.get('entry_only'):continue
 for b in d['battles']:
  c=b['code'];sha=hashlib.sha256((R/f'data/stages/{c}.json').read_bytes()).hexdigest()
  if c in codes and b['outcome']=='victory' and not b.get('failures') and b.get('entry_map_sha256')==b.get('map_sha256')==sha and not d['stat_edits'] and not d['forced_victories']:
   selected[c]=p.parent.name
missing=set(codes)-set(selected);assert not missing,sorted(missing)
shots=[]
for c in codes:
 d=read(R/f'data/stages/{c}.json');label=selected[c];folder=f'res://reports/map-polish-late-20261022/play/{label}/'
 focus=[d['map']['width']//2,d['map']['height']//2]
 for mode,size in [('entry',[562,320]),('field',[426,240])]:
  source=folder+f'{label}-{c}-{mode}.json';p=R/source.removeprefix('res://')
  if not p.exists():source=folder+f'{label}-{c}-entry.json';p=R/source.removeprefix('res://')
  state=read(p);assert state['map_revision']=='0.10.3'
  shots.append({'name':c+'-'+mode,'source':source,'focus':focus,'width':size[0],'height':size[1]})
for c in ['M31','M41','F43','M52','J54']:
 label=selected[c];d=read(R/f'data/stages/{c}.json')
 shots.append({'name':c+'-objective','source':f'res://reports/map-polish-late-20261022/play/{label}/{label}-{c}-entry.json','focus':[d['map']['width']//2,d['map']['height']//2],'width':426,'height':240,'note_page':1})
(O/'selected-playthroughs.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2)+'\n')
(O/'capture-jobs.json').write_text(json.dumps({'shots':shots},ensure_ascii=False,indent=2)+'\n')
print('Selected',len(selected),'current-map clean wins;',len(shots),'viewport jobs.')
