"""Validate the preview assets and compose representative frames without a window."""
from collections import Counter
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import sys

from PIL import Image, ImageChops, ImageDraw

from build_gallery import OUT, PREVIOUS, R3, FPS

SIZE=(592,240)
HERE=Path(__file__).resolve().parent


@lru_cache(maxsize=64)
def png(path):
    return Image.open(OUT/path).convert('RGBA')


def at(im,tile,cols,w,h):
    x=tile%cols*w;y=tile//cols*h
    return im.crop((x,y,x+w,y+h))


def layer(c,key,id):
    spec=c['layerSpecs'][key]
    j=c['layerMap'][key][id]
    tiles=c['atlasFrames']
    im=png(c['atlases'][key][j//tiles])
    return at(im,j%tiles,c['atlasCols'],*spec['size']),spec['at']


def putfx(dst, field, spec, f, point, flip, alpha=1, limit=None):
    tiles=spec.get('atlasFrames',spec['frames'])
    w,h=spec['frameSize']
    ix=f%tiles
    img=png(spec['paths'][f//tiles] if 'paths' in spec else spec['path'])
    im=at(img,ix,spec['columns'],w,h)
    px,py=spec['pivot'];x,y=map(round,point)
    if flip:
        im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        x+=px-w
    else:
        x-=px
    y-=py
    a,b,c,d=field
    xr=min(a+c,limit if limit is not None and flip else a+c,x+w)
    xl=max(a,limit if limit is not None and not flip else a,x)
    yt=max(b,y);yb=min(b+d,y+h)
    if xl>=xr or yt>=yb:
        return
    im=im.crop((xl-x,yt-y,xr-x,yb-y))
    if alpha<1:
        im.putalpha(im.getchannel('A').point(lambda a:round(a*max(0,alpha))))
    dst.alpha_composite(im,(xl,yt))


def compose(c,t,effects):
    n=max(0,min(len(c['timeline'])-1,math.floor(t*FPS+1e-6)))
    id=c['timeline'][n]
    orig=Image.new('RGBA',SIZE)
    orig.alpha_composite(*layer(c,'plate',id))
    orig.alpha_composite(*layer(c,'current',id))
    cand=orig.copy()
    if c.get('fullReplacement') or c.get('replaceEffectsFrom',math.inf)<=t<c.get('replaceEffectsUntil',math.inf):
        cand.alpha_composite(*layer(c,'clean',id))
    def cue(k):
        for q in c['fxPlan']:
            if q.get('layer','front')!=k or not q['start']<=t<q.get('until',math.inf):
                continue
            spec=effects[q['effect']]
            f=math.floor(((t-q['start'])*q.get('rate',1)+q.get('offset',0))*spec['fps']+1e-6)
            if spec['loop']:
                f%=spec['frames']
            if not 0<=f<spec['frames']:
                continue
            point=q.get('anchor') if 'track' not in q else q['track'][n]
            alpha=q.get('alpha',1)
            if q.get('fadeIn'):
                alpha*=min(1,(t-q['start'])/q['fadeIn'])
            if q.get('fadeOut'):
                alpha*=min(1,(q['until']-t)/q['fadeOut'])
            if point:
                putfx(cand,c['field'],spec,f,point,q.get('flip'),alpha,q.get('trailLimit'))
    cue('back')
    plan=c.get('actorPlan')
    if plan and 0<=n-plan['startFrame']<len(plan['frames']):
        j,x,y,flip,alpha=plan['frames'][n-plan['startFrame']]
        putfx(cand,c['field'],effects[plan['effect']],j,[x,y],flip,alpha)
    cue('front')
    return orig,cand


def board(name,samples,effects,prefix):
    stage_w,stage_h=max(c['field'][2] for c,_,_ in samples),max(c['field'][3] for c,_,_ in samples)
    zoom=1 if stage_w>300 else 2
    cw=stage_w*zoom;ch=stage_h*zoom
    sheet=Image.new('RGB',(2*cw,len(samples)*(ch+22)),(30,39,48))
    d=ImageDraw.Draw(sheet)
    for i,(c,t,caption) in enumerate(samples):
        x,y,w,h=c['field']
        a,b=compose(c,t,effects)
        top=i*(ch+22)
        for j,im in enumerate((a,b)):
            tmp=im.crop((x,y,x+w,y+h)).resize((w*zoom,h*zoom),Image.Resampling.NEAREST)
            sheet.paste(tmp,(j*cw+(cw-w*zoom)//2,top))
            d.text((j*cw+5,top+ch+4),('original' if j==0 else 'candidate')+'  '+caption+f' {t:.3f}s',fill=(213,225,224))
    sheet.save(prefix/f'{name}.png',optimize=True)


def verify(make_boards=False):
    catalog=R3.read_js(OUT/'catalog.js')
    effects=catalog['effects']; sources=json.loads((OUT/'qa/r4-provenance.json').read_text())
    audio=json.loads((OUT/'qa/r4-fire-audio.json').read_text())
    cases={m['key']:R3.read_case(OUT,m['key']) for m in catalog['cases'] if not m.get('legacy')}
    patched={k:c for k,c in cases.items() if c['revision']==4}
    expected=set(sources['cases'])
    assert set(patched)==expected
    assert len(catalog['cases'])==794 and len(expected)==202
    used=set(); actors=0; fire=0
    for key,c in cases.items():
        previous=PREVIOUS/'cases'/(key+'.js')
        if key not in expected:
            assert previous.read_bytes()==(OUT/'cases'/previous.name).read_bytes(),key
            continue
        old=R3.read_case(PREVIOUS,key)
        assert c['source']['event']==old['source']['event'] and c['source']['contacts']==old['source']['contacts']==1
        assert c['source']['program']==old['source']['program']
        assert c['duration']>=c['contact']+.7
        used.update(p for values in c['atlases'].values() for p in values)
        assert all(len(c['timeline'])==len(q['track']) for q in c['fxPlan'] if 'track' in q)
        for p in c['fxPlan']:
            s=effects[p['effect']]
            used.update(s.get('paths',[s.get('path')]))
        if c.get('actorPlan'):
            a=c['actorPlan'];actors+=1
            used.add(effects[a['effect']]['path'])
            assert c['actionEvidence']['gameContactCount']==1
            assert c['replaceEffectsFrom']==a['startFrame']/FPS
            assert c['replaceEffectsUntil']==(a['startFrame']+len(a['frames']))/FPS
            assert max(row[0] for row in a['frames'])+1==effects[a['effect']]['frames']
            assert min(row[4] for row in a['frames'])>0
        else:
            assert c['contact']==old['contact'] and c['timeline']==old['timeline']
            assert c['atlases']==old['atlases']
        if c['visualRevision']=='fire':
            fire+=1
            p=c['spellPhases']
            assert not c.get('fullReplacement') and c['replaceEffectsFrom']==p['release']
            assert c['fxPlan'][0]['start']==p['release'] and c['fxPlan'][1]['start']==p['arrival']
            assert c['fxPlan'][0]['until']==p['arrival'] and p['contact']<=p['arrival']<p['contact']+1/FPS
            cue=c['audioCues'][0];assert len(c['audioCues'])==1 and cue['id'] in audio['tracks']
            timing=audio['tracks'][cue['id']]
            assert abs(cue['at']+timing['release_seconds']-p['release'])<.00002
            assert abs(cue['at']+timing['impact_seconds']-p['arrival'])<.00002
            for t in (p['charge']+.30,p['release']-1/FPS):
                a,b=compose(c,t,effects)
                assert ImageChops.difference(a.convert('RGB'),b.convert('RGB')).getbbox() is None,(key,t)
    assert all((OUT/p).is_file() for p in used)
    assert fire==44 and actors==6
    sizes=[]
    for path in sorted((OUT/'assets/r4').glob('*.png')):
        im=png(path.relative_to(OUT).as_posix())
        size=path.stat().st_size
        if size>=200000:
            print('Oversize PNG',path.name,size,file=sys.stderr)
        sizes.append({'file':path.name,'dimensions':list(im.size),'bytes':size,
                      'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    summary={'runtime_integration':False,'catalog_cases':len(catalog['cases']),
        'updated_cases':dict(Counter(c['visualRevision'] for c in patched.values())),
        'changed_action_cases':actors,'audio_continuity_cases':fire,'single_contact_and_same_original_result':True,
        'exact_sampled_fire_charge_pairing':True,'other_cases_preserved':len(catalog['cases'])-len(expected),
        'referenced_assets_checked':len(used),'asset_sizes':sizes}
    (OUT/'qa/verification.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print({k:v for k,v in summary.items() if k!='asset_sizes'})
    print('Largest new PNG',max((a['bytes'],a['file']) for a in sizes))
    if not make_boards:
        return
    root=Path('/private/tmp/pixelfx-r4-qa')
    root.mkdir(exist_ok=True)
    f=cases['c30ab900b09f'];s=cases['cinema-eileen-fire-advanced']
    board('fire',[(f,f['chargeTime'],'charge'),(f,f['actionTime'],'flight'),(f,f['impactTime'],'impact'),(f,f['contact']+.36,'tail')],effects,root)
    board('fire-cinema',[(s,s['chargeTime'],'charge'),(s,s['actionTime'],'flight'),(s,s['impactTime'],'impact')],effects,root)
    r=cases['646005c505bb']; p=r['spellPhases']; h=r['contact']
    board('ragnarok',[(r,r['chargeTime'],'charge'),(r,r['actionTime'],'fuse'),(r,p['gather']+.15,'ring'),(r,h+.16,'pillar'),(r,h+.71,'embers')],effects,root)
    t=cases['cinema-eileen-thunder']; l=cases['eff7271f21f0']
    board('lightning-cinema',[(t,t['actionTime'],'leader'),(t,t['impactTime'],'return'),(t,t['contact']+.24,'branches')],effects,root)
    board('lightning-sword',[(l,l['chargeTime'],'charge'),(l,l['actionTime'],'leader'),(l,l['impactTime'],'return')],effects,root)
    for k,name in [('cinema-hunapu-sword','double'),('cinema-eileen-sword','spin'),('6b455cb494a1','guard'),('6689f9fcdafc','guard-enemy')]:
        c=cases[k]; t=c['contact']
        board(name,[(c,t+x,s) for x,s in [(-.36,'windup'),(-.14,'first motion'),(.035,'contact'),(.13,'follow'),(.44,'recovery')]],effects,root)
    for style, ids in [('hero',('cinema-hunapu-sword','cinema-eileen-sword','cinema-hunapu-sword-advanced','cinema-eileen-sword-advanced')),
                       ('guard',('6b455cb494a1','6689f9fcdafc'))]:
        strip=Image.new('RGB',(768,len(ids)*260),(31,42,50))
        for i,key in enumerate(ids):
            c=cases[key]
            for j,t in enumerate((-.36,-.16,.035,.20)):
                a=c['actorPlan'];n=round((c['contact']+t)*FPS)-a['startFrame']; f,x,y,flip,alpha=a['frames'][n]
                im=Image.new('RGBA',SIZE)
                putfx(im,c['field'],effects[a['effect']],f,[x,y],flip,alpha)
                alpha=im.getchannel('A');bbox=alpha.getbbox()
                assert bbox
                tile=im.crop(bbox)
                for z in range(2):
                    tile=tile.resize(tile.size,Image.Resampling.NEAREST)
                    box=Image.new('RGB',(192,130),(31,42,50) if z==0 else (218,221,216))
                    box.paste(tile,((box.width-tile.width)//2,box.height-tile.height-14),tile)
                    strip.paste(box,(j*192,i*260+z*130))
        strip.save(root/f'{style}-dark-light.png',optimize=True)


if __name__=='__main__':
    verify('--boards' in sys.argv)
