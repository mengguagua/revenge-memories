from pathlib import Path
from types import SimpleNamespace
import json,sys,subprocess,hashlib
V=Path(__file__).resolve().parents[1];R=V.parent;sys.path.insert(0,str(R/'tools'))
from build_gallery import build
from export_gallery import export,render_frame
old=json.loads((V/'source/action-digests-before.json').read_text());data=build();targets=[a for a in data['actions']if a['id']in [f'professions-class-8-{s}-maps-tactical-walk--walk-left'for s in ['ally','enemy']]];ids={a['id']for a in targets};assert len(targets)==2;assert all(a['contentDigest']==old[a['id']]for a in data['actions']if a['id']not in ids)
args=SimpleNamespace(close=False,scale=4,light=False,stills_only=False)
for a in targets:
 export(data,a,args);p=next(p for p in data['profiles']if p['id']==a['profile'])
 for tick in [0,16]:
  for light,label in [(False,'ground'),(True,'light')]:render_frame(data,p,a,tick,4,light).save(V/f'reviews/{p["side"]}-left-{tick}-{label}.png',optimize=True)
data=build();actions={a['id']:a for a in data['actions']};(V/'overview-inputs.txt').write_text('\n'.join("file '"+str(R/actions[a['id']]['video'])+"'"for a in targets)+'\n');subprocess.run(['/opt/homebrew/bin/ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(V/'overview-inputs.txt'),'-c','copy','-movflags','+faststart',str(V/'overview.mp4')],check=True)
q=json.loads((V/'verification.json').read_text());q['updated_actions']=2;q['unrelated_actions_unchanged']=len(data['actions'])-2;old_runtime=json.loads((V/'source/runtime-hashes-before.json').read_text());assert all(hashlib.sha256((R.parent.parent/p).read_bytes()).hexdigest()==h for p,h in old_runtime.items());q['runtime_files_unchanged']=len(old_runtime);(V/'verification.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');print(q)
