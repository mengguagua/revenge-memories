"""Render this review batch through the existing gallery renderer, without opening a game."""
from pathlib import Path
from types import SimpleNamespace
import json, subprocess, sys

V=Path(__file__).resolve().parents[1]; R=V.parent
sys.path.insert(0,str(R/'tools'))
from build_gallery import build
from export_gallery import export, render_frame

keys=['class-12-ally','class-12-enemy','class-6-ally','class-6-enemy']
data=build(); selected=[a for a in data['actions'] if any(a['profile'].startswith('professions-'+k+'-maps-') for k in keys)]
assert len(selected)==38, len(selected)
args=SimpleNamespace(close=False,scale=4,light=False,stills_only=False)
reports=[]
for action in selected:
    reports.append(export(data,action,args))
    print(action['id'],flush=True)
data=build(); lookup={a['id']:a for a in data['actions']};profiles={p['id']:p for p in data['profiles']}
order=[]
for key in keys:
    prefix='professions-'+key+'-maps-'
    order.append(prefix+'tactical-idle--idle-cycle')
    order.extend(prefix+'tactical-walk--walk-'+d for d in ['up','right','down','left'])
for key in ['class-12-ally','class-6-ally']:order.append('professions-'+key+'-maps-story--idle-pose')
lines=[]; segments=[]; tick=0
for aid in order:
    a=lookup[aid];assert a['video'];lines.append("file '"+str(R/a['video'])+"'")
    segments.append({'action':aid,'start_frame':tick,'frames':len(a['frames']),'start_seconds':tick/a['fps']})
    tick+=len(a['frames'])
(V/'overview-inputs.txt').write_text('\n'.join(lines)+'\n')
subprocess.run(['/opt/homebrew/bin/ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(V/'overview-inputs.txt'),'-c','copy','-movflags','+faststart',str(V/'overview.mp4')],check=True)
for key in keys:
    for context,kind,ticks in [('tactical-idle','idle-cycle',[0,22]),('tactical-walk','walk-right',[0,16])]:
        a=lookup['professions-'+key+'-maps-'+context+'--'+kind];p=profiles[a['profile']]
        for tick in ticks:
            render_frame(data,p,a,tick,4).save(V/'reviews'/f'{key}-{kind}-{tick:02}-ground.png',optimize=True)
            render_frame(data,p,a,tick,4,light=True).save(V/'reviews'/f'{key}-{kind}-{tick:02}-light.png',optimize=True)
for key in ['class-12-ally','class-6-ally']:
    a=lookup['professions-'+key+'-maps-story--idle-pose'];p=profiles[a['profile']]
    render_frame(data,p,a,0,4).save(V/'reviews'/f'{key}-story-static.png',optimize=True)
(V/'export-selection.json').write_text(json.dumps({'actions':reports,'overview_segments':segments,'overview_frames':sum(s['frames']for s in segments),'browser_inspection':'Not performed; offline renderer and exported frames reviewed.'},ensure_ascii=False,indent=2)+'\n')
print('Exported 38 actions and 22-segment overview',flush=True)
