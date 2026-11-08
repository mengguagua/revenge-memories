"""Frame-level and asset checks for the R5 comparison."""
from collections import Counter
from functools import lru_cache
import json
import math
import hashlib
from pathlib import Path
import sys

from PIL import Image, ImageChops, ImageDraw
from prepare_cinema import HERE, R4, FPS, capture_path, read_case, rows_at
from prepare_effects import opened, tile
from build_gallery import OUT, load, max_channels

SIZE=(592,240)


def over(im,dest,at):
    im.alpha_composite(dest,tuple(at))


def tile_by_path(path,j,cols,w,h):
    im=opened(path); x=j%cols*w;y=j//cols*h
    return im.crop((x,y,x+w,y+h))


def review_img(spec,n):
    id=spec['map'][n]
    if id<0:return None
    s=spec['cells']; w,h=spec['size']
    return tile_by_path(OUT/spec['paths'][id//s],id%s,spec['cols'],w,h)


def draw_review(img,spec,n):
    frame=review_img(spec,n)
    if frame:over(img,frame,spec.get('at',(0,0)))


def sprite_effect(q,t,n,sp):
    if not q['start']<=t<q.get('until',math.inf):
        return None
    f=math.floor(((t-q['start'])*q.get('rate',1)+q.get('offset',0))*sp['fps']+1e-6)
    if sp['loop']:f%=sp['frames']
    if not 0<=f<sp['frames']:return None
    p=q['track'][n] if 'track' in q else q.get('anchor')
    if not p:return None
    alpha=q.get('alpha',1)
    if q.get('fadeIn'):alpha*=min(1,(t-q['start'])/q['fadeIn'])
    if q.get('fadeOut'):alpha*=min(1,(q['until']-t)/q['fadeOut'])
    return f,p,q.get('flip',False),alpha


def draw_fx(img,field,sp,f,p,flip=False,alpha=1,limit=None):
    w,h=sp['frameSize'];cols=sp['columns'];cells=sp.get('atlasFrames',sp['frames'])
    path=sp['paths'][f//cells] if 'paths' in sp else sp['path']
    im=tile_by_path(OUT/path,f%cells,cols,w,h)
    x,y=map(round,p);px,py=sp['pivot'];y-=py
    if flip:
        im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT);x+=px-w
    else:x-=px
    l,b,sw,sh=field
    xr=min(l+sw,x+w,limit if flip and limit is not None else l+sw)
    xl=max(l,x,limit if not flip and limit is not None else l)
    yt=max(b,y);yb=min(b+sh,y+h)
    if xr<=xl or yb<=yt:return
    im=im.crop((xl-x,yt-y,xr-x,yb-y))
    if alpha<1:im.putalpha(im.getchannel('A').point(lambda x:round(x*alpha)))
    over(img,im,(xl,yt))


def frames(c,t,effects):
    n=max(0,min(len(c['timeline'])-1,math.floor(t*FPS+1e-6)))
    a=Image.new('RGBA',SIZE)
    for k in ('plate','current'):
        over(a,tile(c,k,n),c['layerSpecs'][k]['at'])
    b=a.copy()
    if c.get('fullReplacement') or c.get('suppressFlash') or c.get('replaceEffectsFrom',math.inf)<=t<c.get('replaceEffectsUntil',math.inf):
        over(b,tile(c,'clean',n),c['layerSpecs']['clean']['at'])
    r=c.get('cinemaReview')
    if r:draw_review(b,r['labelStrip'],n)
    for layer in ['back','actor','front']:
        if layer=='actor':
            p=c.get('actorPlan')
            if p and 0<=n-p['startFrame']<len(p['frames']):
                f,x,y,flip,a1=p['frames'][n-p['startFrame']]
                draw_fx(b,c['field'],effects[p['effect']],f,[x,y],flip,a1)
            continue
        for q in c['fxPlan']:
            if (q.get('layer') or 'front')!=layer:continue
            s=effects[q['effect']];p=sprite_effect(q,t,n,s)
            if p:draw_fx(b,c['field'],s,*p,q.get('trailLimit'))
    if c.get('foregroundActor'):draw_review(b,c['foregroundActor'],n)
    return a,b,review_img(r['normalHud'],n) if r else None


def validate(make_boards=False):
    d=json.loads((OUT/'catalog.js').read_text().split('=',1)[1].rstrip(';\n'))
    old=json.loads((R4/'catalog.js').read_text().split('=',1)[1].rstrip(';\n'))
    p=load(OUT/'qa/r5-provenance.json')
    fx=d['effects'];cases={};stats=Counter();new=set(p['cases']); paths=set()
    for meta,bmeta in zip(d['cases'],old['cases']):
        key=meta['key'];assert key==bmeta['key']
        if key not in new:
            assert meta==bmeta
            if not meta.get('legacy'):assert (OUT/'cases'/f'{key}.js').read_bytes()==(R4/'cases'/f'{key}.js').read_bytes()
            continue
        c=read_case(OUT/'cases'/f'{key}.js');b=read_case(R4/'cases'/f'{key}.js');cases[key]=c
        assert c['revision']==5 and c['source']==b['source'] and c['source']['contacts']==1
        assert c['contact']==b['contact'] and c['timeline']==b['timeline'] and c['atlases']==b['atlases']
        specs=[]
        if c['move']=='火球':
            stats['fire']+=1
            assert c['audioCues'][:len(b['audioCues'])]==b['audioCues']
            assert c['spellPhases']==b['spellPhases']
            a1,b1,_=frames(c,c['chargeTime'],fx)
            row=rows_at(c,load(capture_path(key)))[math.floor(c['chargeTime']*FPS)]
            if c['family']=='cinema':
                sc=row['cinema']
                e=next(f for f in sc['effects'] if 'spell-fire-' in f['source'])
                x,y,w,h=e['rect'];ox,oy=sc['origin'];s=sc['scale'];x,y=ox+x*s,oy+y*s;w*=s;h*=s
                box=tuple(map(round,[x,y,x+w,y+h]))
                a1=a1.crop(box);b1=b1.crop(box)
            assert not max_channels(ImageChops.difference(a1,b1)).getbbox(),key
        if c.get('foregroundActor'):
            stats['weapon']+=1
            s=c['foregroundActor'];specs.append(s)
            t=c['chargeTime'];n=math.floor(t*FPS)
            patch=review_img(s,n)
            assert patch is not None and patch.getchannel('A').getbbox()
            _,right,_=frames(c,t,fx);x,y=s['at'];w,h=s['size'];o=right.crop((x,y,x+w,y+h))
            diff=max_channels(ImageChops.difference(o,patch))
            assert ImageChops.multiply(diff,patch.getchannel('A')).getbbox() is None,key
        if c.get('cinemaReview'):
            stats['cinema']+=1
            v=c['cinemaReview'];a=v['hpBefore'];b1=v['hpAfter']
            assert v['damage']==a-b1 and c['source']['event']['hp_after']==b1
            assert len(v['labelStrip']['map'])==len(c['timeline'])==len(v['normalHud']['map'])
            specs.extend([v['labelStrip'],v['normalHud']])
            assert len([q for q in c['fxPlan'] if q['effect']==f"r5-damage-{v['damage']}"])==1
            assert c['contact']<c['damageTime']<v['firstDropFrame']/FPS<c['duration']
        if c.get('r5BoltCount'):
            stats['multi_bolt']+=1
            q=next(q for q in c['fxPlan'] if q['effect'].startswith('r5-thunder'))
            assert len(p['effects'][q['effect']]['options']['secondary'])+1==c['r5BoltCount']
        for sp in specs:paths.update(sp['paths'])
        for q in c['fxPlan']:
            sp=fx[q['effect']]
            paths.update(sp.get('paths',[sp.get('path')]))
    assert stats=={'fire':44,'weapon':72,'cinema':14,'multi_bolt':2} and len(cases)==178
    assert all((OUT/path).is_file() for path in paths)
    for k,spec in p['effects'].items():
        if 'ink' not in spec['render']:continue
        swatches={tuple(bytes.fromhex(x[1:])) for x in spec['render']['ink']['colors']}
        for path in fx[k]['paths']:
            pix=opened(OUT/path)
            actual={x[:3] for x in pix.getdata() if x[3]}
            assert actual<=swatches and actual,(k,actual)
    images=[]
    for path in sorted((OUT/'assets/r5').rglob('*.png')):
        s=path.stat().st_size
        assert s<200000,(path,s)
        images.append(dict(path=path.relative_to(OUT).as_posix(),size=list(opened(path).size),bytes=s))
    results=dict(runtime_integration=False,catalog_cases=len(d['cases']),updated=len(new),
        unchanged=len(d['cases'])-len(new),counts=stats,
        baseline_frames_contact_and_event_unchanged=True,source_palette_verified=True,
        asset_paths_checked=len(paths),images=images)
    (OUT/'qa/verification.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    print({k:v for k,v in results.items() if k!='images'})
    print('PNG files:',len(images),'largest:',max((x['bytes'],x['path']) for x in images))
    if not make_boards:return
    qa=Path('/private/tmp/pixelfx-r5-qa')
    qa.mkdir(exist_ok=True)
    def board(name,key,moments,scale=1,show_hud=False):
        c=cases[key];x,y,w,h=c['field'];ww=w*scale;hh=h*scale
        pad=119 if show_hud else 0
        out=Image.new('RGB',(2*ww,len(moments)*(hh+pad+22)),(32,42,50))
        label=ImageDraw.Draw(out)
        for i,(t,tag) in enumerate(moments):
            a,b,u=frames(c,t,fx);yy=i*(hh+pad+22)
            for j,im in enumerate([a,b]):
                crop=im.crop((x,y,x+w,y+h)).resize((ww,hh),Image.Resampling.NEAREST)
                out.paste(crop,(ww*j,yy))
                if show_hud and j==1 and u:out.paste(u,(ww*j+(ww-u.width)//2,yy+hh+5))
                label.text((ww*j+6,yy+hh+pad+4),('actual' if j==0 else 'candidate')+f' · {tag} {t:.3f}s',fill='white')
        out.save(qa/f'{name}.png',optimize=True)
    key='c30ab900b09f';c=cases[key]
    board('fire',key,[(1.75,'charge'),(1.967,'flight'),(c['contact']+.09,'impact'),(c['contact']+.4,'embers')],2)
    key='cinema-eileen-fire-advanced';c=cases[key]
    board('fire-cinema',key,[(c['chargeTime'],'charge'),(c['actionTime'],'flight'),(c['contact']+.175,'damage')])
    key='646005c505bb';c=cases[key]
    board('ragnarok',key,[(1.38,'charge'),(3.88,'gather'),(c['contact']+.16,'pillar'),(c['contact']+.86,'embers')],2)
    for suffix in ('','-advanced'):
        key='cinema-eileen-thunder'+suffix;c=cases[key]
        board('critical-thunder'+suffix,key,[(c['contact']-.083,'leaders'),(c['impactTime'],'return'),(c['damageTime'],'number'),(c['hpTime'],'deduct')],show_hud=True)
    key='9624e217927f';c=cases[key]
    board('levin',key,[(c['chargeTime'],'sword'),(2.252,'sword'),(c['impactTime'],'hit')],2)
    key='a7e594a06797';c=cases[key]
    board('drain',key,[(c['contact']+.13,'strike'),(c['contact']+.67,'return'),(c['contact']+.88,'arrive'),(c['contact']+1.16,'recovery')],2)
    key='6b455cb494a1';c=cases[key]
    board('guard',key,[(c['contact']+.10,'contact'),(c['contact']+.24,'sweep'),(c['contact']+.42,'end')],2)
    key='cinema-hunapu-sword';c=cases[key]
    board('damage-hunapu',key,[(c['damageTime'],'number'),(c['hpTime'],'deduct')],show_hud=True)

if __name__=='__main__':
    validate('--boards' in sys.argv)
