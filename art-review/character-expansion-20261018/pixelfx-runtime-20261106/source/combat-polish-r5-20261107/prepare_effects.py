"""Extract exact fire colors and the real target/caster spacing from R4."""
from collections import Counter
from functools import lru_cache
import json
import math

from PIL import Image
from prepare_cinema import HERE, R4, FPS, capture_path, read_case, rows_at


@lru_cache(maxsize=28)
def opened(path):
    return Image.open(path).convert('RGBA')


def tile(c, name, n):
    raw=c['timeline'][n]
    i=c['layerMap'][name][raw]
    cap=c['atlasFrames']; cols=c['atlasCols']; j=i%cap
    w,h=c['layerSpecs'][name]['size']
    x=j%cols*w;y=j//cols*h
    return opened(R4/c['atlases'][name][i//cap]).crop((x,y,x+w,y+h))


def read_catalog():
    return json.loads((R4/'catalog.js').read_text().split('=',1)[1].rstrip(';\n'))


def fire_sample(c,d):
    colors=Counter(); release=c['spellPhases']['release']; sx,sy=c['layerSpecs']['current']['at']
    for n,row in enumerate(rows_at(c,d)):
        if not release-.4<=n/FPS<release:
            continue
        if c['family']=='cinema':
            sc=row.get('cinema',{})
            e=next((p for p in sc.get('effects',[]) if 'spell-fire-' in p['source']),None)
            if e is None:
                continue
            x,y,w,h=e['rect']; ox,oy=sc['origin']; k=sc['scale']; x,y=ox+x*k,oy+y*k;w*=k;h*=k
        else:
            e=next((p for p in row['effects'] if not p['bound']),None)
            if e is None:
                continue
            x,y,w,h=e['rect']
        rect=(math.floor(x-sx),math.floor(y-sy),math.ceil(x+w-sx),math.ceil(y+h-sy))
        original=tile(c,'current',n).crop(rect).convert('RGB')
        clean=tile(c,'clean',n).crop(rect).convert('RGB')
        colors.update(a for a,b in zip(original.getdata(),clean.getdata()) if a!=b)
    assert colors
    return colors


def resolve_colors(pixels,bucket='battle'):
    rows=pixels.most_common()
    if bucket=='enemy':
        return ['#%02x%02x%02x'%a for a,_ in rows[:3]]
    base=next(a for a,_ in rows if 90<=a[0]<204 and a[0]>a[1]*1.6 and a[1]<85)
    glint=next(a for a,_ in rows if a[0]>165 and 68<a[1]<170 and a[0]>1.28*a[1])
    white=next(a for a,_ in rows if min(a)>=245)
    return ['#%02x%02x%02x'%a for a in (base,glint,white)]


def life_anchors(c,d):
    e=c['source']['event']
    tgt=c['fxPlan'][1]['anchor']; end=c['fxPlan'][-1]['anchor']
    rows=rows_at(c,d)
    r=rows[max(0,math.floor((c['contact']-.13)*FPS))]
    cx=round(end[0]);cy=round(r['actor'][1]-1)
    tx=round(tgt[0]);ty=round(tgt[1]-3)
    hx,hy=0,round(end[1]-cy)
    return dict(caster=[cx,cy],target=[tx,ty],targetDX=abs(tx-cx),targetY=ty-cy,
                heartX=hx,heartY=hy,flip=tx<cx,recovered=int(e['heal']))


def prepare():
    samples={'battle':Counter(),'cinema':Counter(),'enemy':Counter()}
    fire_details={};drains={};damage=set()
    for m in read_catalog()['cases']:
        if m['move'] not in ['火球','吸血'] and m['family']!='cinema':
            continue
        c=read_case(R4/'cases'/f"{m['key']}.js")
        d=json.loads(capture_path(c['key']).read_text());family=m['family']
        if family=='cinema':
            e=c['source']['event'];value=int(e['hp_before']-e['hp_after'])
            assert e['critical'] and e['hit'] and value>0
            damage.add(value)
        if m['move']=='火球':
            k='cinema' if family=='cinema' else 'enemy' if c['side']=='enemy' else 'battle'
            hist=fire_sample(c,d);samples[k]+=hist
            fire_details[c['key']]={'bucket':k,'colors':resolve_colors(hist,k),'pixels':sum(hist.values())}
        if m['move']=='吸血':
            rec=life_anchors(c,d)
            token=f"{rec['targetDX']}-{abs(rec['targetY'])}-{abs(rec['heartY'])}"
            drains[c['key']]=dict(rec,token=token)
    result={'fire':{k:resolve_colors(v,k) for k,v in samples.items()},'samples':fire_details,
            'damage':sorted(damage),'drains':drains}
    assert len(fire_details)==44 and len(drains)==12
    assert len(set(tuple(i['colors']) for i in fire_details.values() if i['bucket']=='battle'))==1
    (HERE/'effect-jobs.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(result['fire'],result['damage'])
    print('Life steal spans:',sorted({r['token'] for r in drains.values()}))

if __name__=='__main__':
    prepare()
