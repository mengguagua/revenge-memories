"""Replay only the cinema pixels touched by legacy labels, on the R4 clock."""
from bisect import bisect_right
import gzip
import json
import math
from pathlib import Path

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]
R4=BASE/'pixel-reference-r4-20261107'
S4=HERE.parent/'pixel-reference-r4-20261107'
SNAP=HERE.parent/'full-battle-20261107/runtime-snapshot'
ROOTS=[S4/'captures-clean',HERE.parent/'weapon-magic-r2-20261107/captures',HERE.parent/'full-battle-20261107/captures']
FPS=60

def read_case(path):
    return json.loads(path.read_text().split(']=',1)[1].rstrip(';\n'))

def capture_path(key):
    return next(r/key/'capture.json' for r in ROOTS if (r/key/'capture.json').is_file())

def rows_at(c,d):
    times=[r['t'] for r in d['frames']]
    return [d['frames'][max(0,bisect_right(times,n/FPS+1e-8)-1)] for n in range(len(c['timeline']))]

def prepare():
    data=json.loads((SNAP/'data/critical_cinema.json').read_text())
    items=[]
    for path in sorted((R4/'cases').glob('cinema-*.js')):
        c=read_case(path);d=json.loads(capture_path(c['key']).read_text())
        assert d['contact_time']==c['contact'] and d['job']['event']==c['source']['event']
        spec=data['cases'][c['source']['program']]
        native_program=json.loads(gzip.decompress((SNAP/spec['program'].removeprefix('res://')).read_bytes()))
        label_ops=[[op for op in f if op[0] in (3,4)] for f in native_program['frames']]
        e=c['source']['event'];jobs=[];lookup={};mapping=[];x1=592;y1=240;x2=0;y2=0;hp_keys=[];hp_lookup={}
        for n,row in enumerate(rows_at(c,d)):
            sc=row.get('cinema');t=n/FPS
            cast_hp=int(row.get('hp',{}).get(e['attacker'],e['source_hp_before']))
            # Actual first HP decrement is measured from an ordinary hit on
            # this fixture. The capture records its native reaction length.
            hp_lookup.setdefault(cast_hp, len(hp_lookup))
            hp_keys.append(hp_lookup[cast_hp])
            if not sc or sc['show']<.01:
                mapping.append(-1);continue
            ops=label_ops[min(len(label_ops)-1,math.floor(sc['elapsed']*native_program['fps']))]
            if not ops:
                mapping.append(-1);continue
            strip=(c.get('fullReplacement',False) or c.get('suppressFlash',False) or
                   c.get('replaceEffectsFrom',math.inf)<=t<c.get('replaceEffectsUntil',math.inf))
            key=(int(row['image']),strip)
            if key not in lookup:
                lookup[key]=len(jobs)
                jobs.append(dict(elapsed=sc['elapsed'],strip=strip,source_id=key[0],hp=row.get('hp',{})))
                ox,oy=sc['origin'];s=sc['scale']
                for op in ops:
                    if op[0]==3:
                        _,kind,x,y,h,_=op
                        half=2.15*h if kind=='hp' else 1.70*h if kind=='name' else 1.64*h
                        x1=min(x1,math.floor(ox+(x-half)*s-2));x2=max(x2,math.ceil(ox+(x+half)*s+2))
                        y1=min(y1,math.floor(oy+(y-h)*s-2));y2=max(y2,math.ceil(oy+(y+h)*s+2))
                    else:
                        _,x,y,w,h=op
                        x1=min(x1,math.floor(ox+x*s-2));x2=max(x2,math.ceil(ox+(x+w)*s+2))
                        y1=min(y1,math.floor(oy+y*s-2));y2=max(y2,math.ceil(oy+(y+h)*s+2))
            mapping.append(lookup[key])
        assert jobs and x1<x2 and y1<y2
        caster_values=list(hp_lookup.keys())
        assert len(caster_values)<=3
        items.append(dict(key=c['key'],job=d['job'],sword=c.get('actorPlan') is not None,
                          requests=jobs,map=mapping,rect=[x1,y1,x2-x1,y2-y1],
                          casterHp=caster_values,casterIndex=hp_keys,baselinePath=str(capture_path(c['key']))))
    assert len(items)==14
    (HERE/'cinema-jobs.json').write_text(json.dumps(items,ensure_ascii=False,separators=(',',':'))+'\n')
    print('Prepared',len(items),'cinematics;',sum(len(i['requests']) for i in items),'label frames')
    for i in items:print(i['key'],i['rect'],len(i['requests']),i['casterHp'])

if __name__=='__main__':
    prepare()
