from pathlib import Path
from types import SimpleNamespace
import sys,json
V=Path(__file__).resolve().parents[1];R=V.parent;sys.path.insert(0,str(R/'tools'))
from build_gallery import build
from export_gallery import export
pids={f'professions-class-{c}-{s}-battle' for c,s in [('8','ally'),('8','enemy'),('14','ally')]}
d=build();targets=[a for a in d['actions'] if a['profile'] in pids];report=[]
for a in targets:
 args=SimpleNamespace(close=False,scale=2,light=False,stills_only=False);r=export(d,a,args);report.append(r);print(json.dumps(r,ensure_ascii=False),flush=True)
 if a['key'] in ['original_class_8_normal','original_class_8_enemy_normal','original_class_14_normal','reaction-idle']:
  args.close=True;args.scale=4;r=export(d,a,args);report.append(r);print(json.dumps(r,ensure_ascii=False),flush=True)
(V/'export-report.json').write_text(json.dumps({'exports':report,'actions':len(targets)},ensure_ascii=False,indent=2)+'\n');build()
