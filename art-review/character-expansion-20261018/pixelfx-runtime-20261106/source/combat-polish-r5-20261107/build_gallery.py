"""Apply the R5 review assets without changing any recorded battle result."""
from bisect import bisect_right
from collections import Counter
from functools import lru_cache
import base64
import hashlib
import io
import json
import math
from pathlib import Path
from statistics import median
import struct
import subprocess
import wave

from PIL import Image, ImageChops
from prepare_cinema import HERE, BASE, R4, SNAP, FPS, capture_path, read_case, rows_at
from prepare_effects import opened, read_catalog, tile

OUT=BASE/HERE.name
GUARDS={'6b455cb494a1','6689f9fcdafc'}
MOVES={'火球':'fire','诸神黄昏':'ragnarok','吸血':'drain','雷剑':'levin'}


def load(path):
    return json.loads(path.read_text())


def js(path,name,value):
    path.write_text(name+'='+json.dumps(value,ensure_ascii=False,separators=(',',':'))+';\n')


def write_case(c):
    name=json.dumps(c['key'])
    js(OUT/'cases'/f"{c['key']}.js",f"window.PIXELFX_CASES=window.PIXELFX_CASES||{{}};window.PIXELFX_CASES[{name}]",c)


def pack(dest,stem,tiles):
    """Lossless atlases with an upper size target, without resizing the art."""
    dest.mkdir(parents=True,exist_ok=True)
    assert tiles
    w,h=tiles[0].size
    for cells in (16,12,8,4,2,1):
        cols=min(4,cells)
        results=[]
        for i in range(0,len(tiles),cells):
            group=tiles[i:i+cells]
            im=Image.new('RGBA',(w*cols,h*math.ceil(len(group)/cols)))
            for j,t in enumerate(group):
                im.paste(t,((j%cols)*w,(j//cols)*h))
            data=io.BytesIO()
            im.save(data,format='PNG',optimize=True)
            if len(data.getbuffer())>=196000 and cells>1:
                results=[]
                break
            results.append(data.getvalue())
        if results:
            break
    paths=[]
    for f in dest.glob(stem+'-*.png'):
        if f.stem.rsplit('-',1)[-1].isdigit():
            f.unlink()
    for i,blob in enumerate(results):
        f=dest/f'{stem}-{i:03}.png'
        f.write_bytes(blob); paths.append(f.relative_to(OUT).as_posix())
    return dict(paths=paths,size=[w,h],cells=cells,cols=cols,frames=len(tiles))


def raw_tile(folder,paths,j,w,h,cells=16,cols=4):
    im=opened(folder/paths[j//cells])
    i=j%cells;x=i%cols*w;y=i//cols*h
    return im.crop((x,y,x+w,y+h))


def max_channels(im):
    a,b,c=im.convert('RGB').split()
    return ImageChops.lighter(ImageChops.lighter(a,b),c)


def ordinary_timing(catalog):
    """Measure the HP tick cadence in unchanged ordinary attack captures."""
    firsts=[]; steps=[]; keys=[]
    for m in catalog['cases']:
        if m['family']=='cinema' or m['move'] not in ['诸神黄昏','火球','枪击','雷电','雷剑','吸血']:
            continue
        c=read_case(R4/'cases'/f"{m['key']}.js")
        e=c['source'].get('event',{})
        if c['source'].get('target')!='士兵' or e.get('hp_before',0)-e.get('hp_after',0)<5:
            continue
        d=load(capture_path(c['key']));prev=e['hp_before']; marks=[]
        for row in d['frames']:
            now=row.get('hp',{}).get(e['defender'],prev)
            if now<prev:
                marks.append(row['t']-d['contact_time'])
                prev=now
        if len(marks)>4:
            firsts.append(marks[0]);steps.extend(b-a for a,b in zip(marks,marks[1:]));keys.append(c['key'])
    assert len(keys)>20
    observed=median(steps)
    step=max(1,round(observed*FPS))
    return dict(sample_count=len(keys),keys=keys,observed_first=median(firsts),
                observed_step=observed,step_frames=step)


def pack_cinema(c,item,meta,step_frames):
    key=c['key'];raw=HERE/'native-cinema'/key
    x,y,w,h=item['rect']
    assert meta['rect']==item['rect'] and meta['frames']==len(item['requests'])
    index_to_n={}
    for n,j in enumerate(c['timeline']):
        index_to_n.setdefault(j,n)
    dest=OUT/'assets/r5/cinema'/key
    masks=[];copies=0;diff_pxs=0
    for j,req in enumerate(item['requests']):
        a=raw_tile(raw,meta['with'],j,w,h)
        b=raw_tile(raw,meta['without'],j,w,h)
        mask=max_channels(ImageChops.difference(a,b)).point([0]+[255]*255)
        diff_pxs+=mask.histogram()[255]
        if mask.getbbox():
            n=index_to_n[req['source_id']]
            layer='clean' if req['strip'] else 'current'
            sx,sy=c['layerSpecs'][layer]['at']
            old=tile(c,layer,n).crop((x-sx,y-sy,x-sx+w,y-sy+h))
            delta=max_channels(ImageChops.difference(old,a))
            bad=ImageChops.multiply(mask,delta).getbbox()
            assert bad is None,(key,j,req['source_id'],bad)
            copies+=1
        b.putalpha(mask)
        blank=Image.new('RGBA',b.size)
        blank.alpha_composite(b)
        masks.append(blank)
    assert copies and diff_pxs>1000
    erase=pack(dest,'label-clean',masks)
    erase.update(at=[x,y],map=item['map'])
    hud=[raw_tile(raw,meta['hud'],j,256,112) for j in range(meta['hud_count'])]
    spec=pack(dest,'battle-hud',hud)
    before=meta['target_max']; after=meta['target_min']; loss=before-after
    assert loss>0 and meta['hud_count']==(loss+1)*len(item['casterHp'])
    # The review uses the exact reaction length from the ordinary target and
    # two 60 Hz preview frames per point, as measured in the ordinary clips.
    first=math.ceil((c['contact']+meta['reaction'])*FPS)
    points=[]; track=[]
    for n,cast_idx in enumerate(item['casterIndex']):
        drop=min(loss,0 if n<first else 1+(n-first)//step_frames)
        points.append(before-drop)
        track.append(cast_idx*(loss+1)+before-drop-after)
    assert len(track)==len(c['timeline']) and points[-1]==after
    spec.update(map=track)
    c['cinemaReview']={'labelStrip':erase,'normalHud':spec,
                       'damage':loss,'hpBefore':before,'hpAfter':after,'firstDropFrame':first,
                       'pointStepFrames':step_frames}
    c['damageTime']=c['contact']+.176
    c['hpTime']=(first+(loss-1)//2*step_frames)/FPS
    return dict(label_pixels=diff_pxs,frames_checked=copies,damage=loss,hp=[before,after],
                first_step=first/FPS,finish_step=(first+(loss-1)*step_frames)/FPS)


def levin_actor(c,d,path):
    """Put only existing caster pixels in front of the electricity."""
    root=path.parent
    ckey=c['key']
    frames=len(c['timeline']); start=c['spellPhases']['charge']; stop=c['contact']+1.29
    used={};images=[];ids=[-1]*frames;bbox=None
    left,top,fw,fh=c['field']
    assert [left,top]==c['layerSpecs']['clean']['at']
    for n,srcid in enumerate(c['timeline']):
        if not start<=n/FPS<stop:
            continue
        if srcid not in used:
            alpha=raw_tile(root,d['atlases']['actor'],srcid,592,240,d['atlas_frames'],d['atlas_cols'])
            alpha=alpha.crop((left,top,left+fw,top+fh)).getchannel('A').point([0]+[255]*255)
            raw=tile(c,'clean',n)
            assert alpha.size==raw.size
            raw.putalpha(alpha)
            blank=Image.new('RGBA',raw.size);blank.alpha_composite(raw)
            rect=alpha.getbbox()
            if rect:
                x1,y1,x2,y2=rect
                bbox=[x1,y1,x2,y2] if bbox is None else [min(x1,bbox[0]),min(y1,bbox[1]),max(x2,bbox[2]),max(y2,bbox[3])]
            used[srcid]=len(images)
            images.append(blank)
        ids[n]=used[srcid]
    assert bbox is not None and bbox[2]-bbox[0]<100
    data=[a.crop(bbox) for a in images]
    # The raised pose is many recorded frames but usually only a few unique
    # sprites. Deduplicate so the overlay carries the original pixels only.
    seen={};new=[];index={}
    for i,p in enumerate(data):
        h=hashlib.sha256(p.tobytes()).digest()
        if h not in seen:seen[h]=len(new);new.append(p)
        index[i]=seen[h]
    spec=pack(OUT/'assets/r5/levin'/ckey,'front-actor',new)
    spec.update(at=[left+bbox[0],top+bbox[1]],map=[index[i] if i>=0 else -1 for i in ids])
    c['foregroundActor']=spec
    return {'actors':len(new),'box':spec['at']+spec['size'],'frames':sum(i>=0 for i in ids)}


def label(c,name,desc,modules=None):
    c['revision']=5
    c['changeLabel']='实机适配 · R5'
    c['r5Label']=name
    if modules:
        c['pixelFxModules']=list(dict.fromkeys(modules))
    c['treatment']=desc


def stage_case(c,kind,fxjobs):
    if kind=='fire':
        s=fxjobs['samples'][c['key']]
        for q in c['fxPlan']:
            name=q['effect'].replace('r4-','r5-',1)
            if s['bucket']=='enemy':
                name=name.replace('r5-fireball','r5-fireball-enemy',1)
            q['effect']=name
        c['r5Palette']=s['colors']
        desc='原蓄力照旧。飞行和撞击直接用原蓄力的砖红、珊瑚红、白三色；火尾收成余烬，去掉烟团。保留蓄力、飞行和命中的连续音轨。'
        if s['bucket']=='enemy':
            desc='原蓄力照旧。敌方火球沿用实机本来的靛蓝三色，飞行和撞击也使用同一组色。去掉烟团，保留三段连续音轨。'
        elif s['bucket']=='cinema':
            desc='保留必杀蓄力。飞行和撞击直接取必杀原火球的深红、亮红、白三色，火尾只留火星和余烬。'
        label(c,'实机取色 · 去烟',desc)
    elif kind=='ragnarok':
        for q in c['fxPlan']:
            q['effect']=q['effect'].replace('r4-','r5-',1)
        label(c,'去烟 · 保留火柱','保留熔焰蓄势、贴地火脉、聚焰和单柱喷发。删掉上浮的灰色烟团，收尾留熔缝和余烬。')
    elif kind=='drain':
        g=fxjobs['drains'][c['key']];hit=c['contact']; phase=c['spellPhases']
        start=hit-1.16
        c.pop('composition',None)
        c['fullReplacement']=True
        c['fxPlan']=[dict(effect='r5-life-steal-'+g['token'],start=start,anchor=g['caster'],flip=g['flip'])]
        c['chargeTime']=start+.54
        c['impactTime']=hit+.105
        c['actionTime']=hit+.71
        c['spellPhases']=dict(phase,charge=start,release=hit+.38,returnAt=hit+.91,contact=hit)
        # Keep the locally made cue family. The return whoosh follows the
        # red orbs; the recovery timing still comes from the sampled battle.
        for q in c.get('audioCues',[]):
            if q['id']=='drain-release':q['at']=hit+.39
            if q['id']=='drain-tail':q['at']=hit+1.04
        c['audioCues'].sort(key=lambda q:q['at'])
        c['visualRevision']='drain'
        label(c,'Life steal · 红珠回流','目标身上红珠弹出、短暂停留，再拖出细红尾迹回到施法者。沿用原动作、伤害和恢复数值。',
              ['shadow/life-steal'])
    elif kind=='levin':
        label(c,'原剑身 · 蓝紫斜雷','斜雷和蓄电沿用上版。电光从完整的原剑身后经过，保留原剑尖、剑柄和挥剑姿势。')
    elif kind=='guard':
        for q in c['fxPlan']:
            q['effect']=q['effect'].replace('r4-','r5-',1)
        label(c,'沉铁铜棕 · 重击','横扫换成沉铁和铜棕，边缘更厚，收势更快。保留长枪、盾牌和一次结算。')


def cinematic(c,fx):
    is_thunder=c['move']=='雷电'
    if is_thunder:
        count=4 if c['key'].endswith('advanced') else 3
        for q in c['fxPlan']:
            if q['effect'].startswith('r4-thunder-cinema-'):
                part=q['effect'].rsplit('-',1)[-1]
                q['effect']='r5-thunder-cinema'+('-advanced' if count==4 else '')+'-'+part
        c['r5BoltCount']=count
        c['impactTime']=c['contact']+.052
        label(c,f'{count}道雷 · 普通扣血',f'{count}道雷集中落在同一波回击，伤害只结算一次。',
              c.get('pixelFxModules'))
    elif c['revision']!=5:
        desc=c['treatment']
        label(c,'Damage number · 普通扣血',desc)
    r=c['cinemaReview'];loss=r['damage']
    assert f'r5-damage-{loss}' in fx
    d=load(capture_path(c['key']))
    row=next(row for row in rows_at(c,d)[math.ceil(c['contact']*FPS):] if row.get('cinema',{}).get('target'))
    sc=row['cinema'];tx,fy=[a+b*sc['scale'] for a,b in zip(sc['origin'],sc['target'])]
    pos=[round(tx-4),round(fy-84)]
    c['fxPlan'].append(dict(effect=f'r5-damage-{loss}',start=c['contact'],anchor=pos))
    c['pixelFxModules']=list(dict.fromkeys(c.get('pixelFxModules',[])+['ui/damage-number']))
    c['treatment']+=' 飘字显示本次实伤，扣血沿用普通战斗的分格与逐点节奏。'
    if c.get('audioCues') is None:c['audioCues']=[]
    dsec=(loss-1)*r['pointStepFrames']/FPS+.113
    c['audioCues'].append(dict(id=f'r5-hp-ticks-{loss}',at=r['firstDropFrame']/FPS,duration=dsec,gain=.53,label='普通扣血'))
    c['audioCues'].sort(key=lambda q:q['at'])
    c.setdefault('audioName','普通扣血')


def hp_sounds(values,step_frames):
    sfx=load(SNAP/'data/sound_effects.json')
    record=sfx['effects'][sfx['named_aliases']['hp_tick']]
    source=SNAP/record['path'].removeprefix('res://')
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    assert digest==record['sha256']
    rate=44100
    pcm=subprocess.check_output(['ffmpeg','-v','error','-i',str(source),'-ac','1','-ar',str(rate),'-f','s16le','-'])
    samples=list(struct.unpack('<'+'h'*(len(pcm)//2),pcm))
    target_len=math.ceil(.113*rate)
    samples=(samples+[0]*target_len)[:target_len]
    step=round(rate*step_frames/FPS)
    peak=max(abs(x) for x in samples)
    raw=[x/max(1,peak) for x in samples]
    bank={}
    for n in values:
        out=[0.0]*((n-1)*step+len(raw))
        for j in range(n):
            for i,x in enumerate(raw):
                out[j*step+i]+=x*.38
        pcm=struct.pack('<'+'h'*len(out),*(round(32767*.63*math.tanh(x/.63)) for x in out))
        buf=io.BytesIO()
        with wave.open(buf,'wb') as w:
            w.setparams((1,2,rate,len(out),'NONE','not compressed'))
            w.writeframes(pcm)
        bank[f'r5-hp-ticks-{n}']=dict(duration=len(out)/rate,wav=base64.b64encode(buf.getvalue()).decode('ascii'))
    (OUT/'r5-audio-bank.js').write_text('Object.assign(window.PIXELFX_SOUND_BANK,'+json.dumps(bank,separators=(',',':'))+');\n')
    return {'clip':record['path'],'sha256':digest,'values':values}


def build():
    catalog=read_catalog()
    a=load(OUT/'assets/r5/effects.json');fx=catalog['effects'];fx.update(a['effects'])
    jobs=load(HERE/'effect-jobs.json')
    cinema_jobs={r['key']:r for r in load(HERE/'cinema-jobs.json')}
    steps=ordinary_timing(catalog)
    updated={};counters=Counter()
    for i,m in enumerate(catalog['cases']):
        k=m['key']
        kind='guard' if k in GUARDS else MOVES.get(m['move'])
        cin=k in cinema_jobs
        if kind is None and not cin:
            continue
        c=read_case(R4/'cases'/f'{k}.js')
        e=c['source']['event']
        assert c['source']['contacts']==1 and e['hit']
        if kind:
            stage_case(c,kind,jobs)
            counters[kind]+=1
        evidence={}
        if kind=='levin':
            p=capture_path(k);evidence['sword']=levin_actor(c,load(p),p)
        if cin:
            native=load(HERE/'native-cinema'/k/'native.json')
            evidence['native_cinema_hud']=pack_cinema(c,cinema_jobs[k],native,steps['step_frames'])
            cinematic(c,fx)
            counters['cinema']+=1
        assert c['revision']==5
        for q in c['fxPlan']:assert q['effect'] in fx,(k,q['effect'])
        new=dict(m,revision=5,r5Label=c['r5Label'])
        if c.get('audioCues'):new['audioFamily']=m.get('audioFamily') or 'ordinary-hp'
        catalog['cases'][i]=new
        write_case(c)
        updated[k]=dict(kind=kind,cinema=cin,modules=c.get('pixelFxModules',[]),contact=c['contact'],event=e,**evidence)
    assert len(updated)==178 and counters==dict(fire=44,ragnarok=36,levin=72,drain=12,guard=2,cinema=14)
    ticks=hp_sounds(jobs['damage'],steps['step_frames'])
    choices=[
      ('c30ab900b09f','火球','实机取色 · 去烟'),('646005c505bb','诸神黄昏','去掉蓄势与落点烟团'),
      ('cinema-eileen-thunder','必杀雷电','三道／四道落雷'),
      ('cinema-hunapu-sword','必杀飘字','Damage number · 分格扣血'),
      ('a7e594a06797','吸血','Life steal 红珠回流'),('9624e217927f','雷剑','原剑尖完整可见'),
      ('6b455cb494a1','壁垒卫士','沉铁铜棕横扫')
    ]
    assert all(k in updated for k,_,_ in choices)
    for row in catalog['variantRows']:
        if row['label']=='雷电演出':
            for btn in row['buttons']:
                if btn['case'].endswith('thunder'):btn['name']='必杀 · 三道'
                if btn['case'].endswith('thunder-advanced'):btn['name']='进阶 · 四道'
    def pair(k,a,b):
        return dict(label=k,buttons=[dict(case=x,name=y,subtitle='') for x,y in (a,b)])
    catalog['variantRows'] += [
      pair('胡纳普弓必杀',('cinema-hunapu-bow','基础'),('cinema-hunapu-bow-advanced','进阶')),
      pair('吸血施法者',('a7e594a06797','济世术师'),('1d46d427b991','疗愈师')),
    ]
    catalog.update(revision=5,visualUpdates=len(updated),updatedCases=len(updated),defaultCase=choices[0][0],criticalCases=14,
        revisionRows=[dict(case=k,name=n,subtitle=s) for k,n,s in choices],
        references=catalog['references']+a['references'],
        audioCases=sum(1 for m in catalog['cases'] if m.get('audioFamily')),
        audioClips=catalog['audioClips']+len(jobs['damage']))
    js(OUT/'catalog.js','window.PIXELFX_CATALOG',catalog)
    (OUT/'qa/r5-provenance.json').write_text(json.dumps(dict(
      runtime_integration=False,origin_revision='a84159688af3ca37a4be05a0d422b94451b2e24e',
      fire_palette=jobs['fire'],fire_color_samples=jobs['samples'],life_steal_anchors=jobs['drains'],
      ordinary_hit_cadence=steps,hp_tick_audio=ticks,
      changed=dict(counters),effects=a['provenance'],cases=updated),ensure_ascii=False,indent=2)+'\n')
    print('R5:',len(updated),'updated of',len(catalog['cases']),dict(counters))

if __name__=='__main__':
    build()
