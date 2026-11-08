"""Verify delivered preview data against the immutable Godot capture sources."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
import collections, csv, hashlib, json, math, time
import build_gallery as G

START=time.time()
errors=[]
def check(ok,message):
    if not ok:errors.append(message)
def case_file(key):
    text=(G.OUT/'cases'/f'{key}.js').read_text()
    return json.loads(text.split(']=',1)[1].rstrip(';\n'))

catalog=G.read_js(G.OUT/'catalog.js')
inventories=[json.loads((G.ROOT/n).read_text()) for n in ['inventory.json','inventory-special.json']]
jobs={j['id']:j for inv in inventories for j in inv['jobs']}
maps={p.parent.name:p for p in (G.ROOT/'map-captures').glob('*/capture.json')}
captures={p.parent.name:p for p in (G.ROOT/'captures').glob('*/capture.json')}
metas={c['key']:c for c in catalog['cases']}
check(len(metas)==len(catalog['cases']),'Duplicate catalog IDs')
expected=set(jobs)|set(maps)|{'approved-'+c['key'] for c in G.read_js(G.BASE/'data.js')['cases']}
check(set(metas)==expected,'Catalog coverage differs from inventory: '+str(set(metas)^expected))
check(set(jobs)==set(captures),'Capture IDs differ from inventory')
for inv in inventories:check(not inv['errors'],'Inventory reported errors')

all_paths=set();mapping=[];pixel_checks=0;cinemas=[];cases={}
for key,path in {**captures,**maps}.items():
    d=json.loads(path.read_text());c=case_file(key);cases[key]=c;j=d['job'];n=int(d['unique_frames'])
    check(d.get('guard') is True,key+': background launch guard missing')
    check(not d.get('layout_errors'),key+': layout errors')
    check(not d.get('missing_animations'),key+': missing animations')
    check(0<=d['contact_time']<=d['duration'],key+': invalid contact time')
    times=[f['t'] for f in d['frames']]
    check(times==sorted(times) and times[0]==0,key+': non-monotonic timestamps')
    check(all(0<=int(f['image'])<n for f in d['frames']),key+': invalid capture frame')
    check(all(isinstance(i,int) and 0<=i<n for i in c['timeline']),key+': invalid gallery frame')
    check(len(c['timeline'])==math.ceil(c['duration']*60)+1,key+': incomplete timeline')
    if key in jobs:
        expected_job=jobs[key]
        for field in ['actor','target','event','exchange','program','profile','weapon','graphic','target_graphic']:
            check(j.get(field)==expected_job.get(field),key+': stale fixture '+field)
        check(d['contact_calls']==1,key+': expected exactly one result callback')
        check(sum(bool(f['contact']) and (i==0 or not d['frames'][i-1]['contact']) for i,f in enumerate(d['frames']))==1,key+': contact flag transition differs')
        event=j['event']
        if j['family']=='support':
            # _play_support deliberately passes a visual-only receipt, without
            # strike_effect.valid. Check its current production contract instead.
            check(event.get('visual_only') is True and event['damage']==0 and j['exchange']['support'],key+': invalid support receipt')
            expected_heal=0 if int(j['weapon'])==43 else min(j['target']['max_hp']-event['hp_before'],j['actor']['strength'])
            check(event['hp_after']-event['hp_before']==expected_heal,key+': support receipt healing mismatch')
            check(event['source_hp_before']-event['source_hp_after']==event['hp_cost'],key+': support cost mismatch')
        else:check(event.get('valid') is True,key+': invalid rules result')
        check(event['hp_after']>=0 and event['hp_before']>=0,key+': invalid HP')
        if not event['hit']:check(event['hp_after']==event['hp_before'],key+': miss changes target HP')
        if c['family']=='cinema':
            cinemas.append(j['program'])
            check(d.get('clean_cinema_version')==1 and c.get('cinemaReplacement'),key+': missing synchronized clean cinema')
        if j['profile'] in ['eileen_promoted','23_ally']:
            u=j['target'] if j['family']=='reaction' else j['actor']
            check(bool(u.get('hero_profession')),key+': advanced hero marker missing')
        mapping.append({'id':key,'profile':j['profile'],'actor_id':j['actor']['id'],'target_id':j['target']['id'],'weapon':j['weapon'],'move':c['move'],'program':j['program'],'contact_seconds':d['contact_time'],'callbacks':d['contact_calls'],'hp_before':event['hp_before'],'hp_after':event['hp_after'],'layout':c['subtitle']})
    elif j['kind']=='hero-map':
        receipt=d['receipt'];check(receipt.get('valid') is True,key+': invalid MAP receipt')
        check({t['id'] for t in receipt['targets']}=={t['id'] for t in j['targets']},key+': MAP target set mismatch')
        if j.get('support'):
            check(all(t['hp_after']-t['hp_before']==t['heal'] for t in receipt['targets']),key+': MAP healing mismatch')
            check(all(t.get('strong_body_after',0)>0 for t in receipt['targets']),key+': missing real strong-body status')
    elif key.startswith('map-full-'):
        receipt=d['receipt'];count=len(receipt.get('spawned') or receipt.get('changed',[]))
        check(count=={'map-full-summon':1,'map-full-invoke':2,'map-full-expel':1}[key],key+': full-flow result count differs')
        check(c.get('suppressFlash') and 'clean' in c['atlases'],key+': missing same-frame flash replacement')
    for layer,paths in c['atlases'].items():
        all_paths.update(paths);tilemap=c['layerMap'][layer]
        check(len(tilemap)==n,key+': layer map length '+layer)
        spec=c['layerSpecs'][layer];w,h=spec['size'];capacity=0
        for relative in paths:
            p=G.OUT/relative;check(p.is_file(),key+': missing '+relative)
            if not p.exists():continue
            with Image.open(p) as im:
                check(im.width==w*c['atlasCols'] and im.height%h==0,key+': invalid atlas dimensions '+relative)
                capacity+=im.width//w*(im.height//h)
        check(all(0<=v<capacity for v in tilemap),key+': invalid layer map '+layer)
    for effect in c['fxPlan']:
        check(effect['effect'] in catalog['effects'],key+': unknown effect')
        check(0<=effect['start']<=c['duration'],key+': effect starts outside clip')
        if 'track' in effect:check(len(effect['track'])==len(c['timeline']),key+': track length differs')
    if c.get('cinemaTargets'):check(len(c['cinemaTargets'])==len(c['timeline']),key+': cinema track mismatch')
    if c.get('projectile'):
        check(len(c['projectile']['anchors'])==len(c['timeline']),key+': projectile track mismatch')
        check(any(c['projectile']['anchors']),key+': empty projectile track')

def roundtrip(item):
    key,path=item;d=json.loads(path.read_text());c=cases[key];fails=[];opened={};count=0
    def image(p):
        if p not in opened:opened[p]=Image.open(p).convert('RGBA')
        return opened[p]
    sample_times=[0,d['contact_time'],d['duration']]
    for sec in sample_times:
        frame=min(len(c['timeline'])-1,math.floor(sec*60+1e-6));idx=c['timeline'][frame]
        raw=image(path.parent/d['atlases']['current'][idx//16]);x=idx%16%4*592;y=idx%16//4*240;source=raw.crop((x,y,x+592,y+240))
        rebuilt=Image.new('RGBA',(592,240))
        for layer in ['plate','current']:
            tile=c['layerMap'][layer][idx];spec=c['layerSpecs'][layer];w,h=spec['size'];cell=tile%c['atlasFrames'];atlas=image(G.OUT/c['atlases'][layer][tile//c['atlasFrames']]);x=cell%c['atlasCols']*w;y=cell//c['atlasCols']*h
            rebuilt.alpha_composite(atlas.crop((x,y,x+w,y+h)),tuple(spec['at']))
        if rebuilt.tobytes()!=source.tobytes():fails.append(key+': reference pixels changed at '+str(sec))
        count+=1
    return count,fails

with ThreadPoolExecutor(max_workers=4) as pool:
    for i,(count,fails) in enumerate(pool.map(roundtrip,{**captures,**maps}.items())):
        pixel_checks+=count;errors.extend(fails)
        if i%100==99:print('Verified pixel roundtrips',i+1,flush=True)
check(len(cinemas)==14 and len(set(cinemas))==14,'Expected 14 distinct hero critical programs')

fx_endings=[]
for name,s in catalog['effects'].items():
    p=G.OUT/s['path'];all_paths.add(s['path']);im=Image.open(p).convert('RGBA');w,h=s['frameSize'];f=s['frames']-1;x=f%s['columns']*w;y=f//s['columns']*h;alpha=im.crop((x,y,x+w,y+h)).getchannel('A');maximum=alpha.getextrema()[1]
    fx_endings.append({'effect':name,'loop':s['loop'],'last_frame_max_alpha':maximum})
    if not s['loop']:check(maximum==0,name+': one-shot ends with visible pixels')
legacy=G.read_js(G.BASE/'data.js');check((G.OUT/'approved-data.js').read_bytes()==(G.BASE/'data.js').read_bytes(),'Approved data changed')
legacy_paths=set(s['path'] for s in legacy['effects'].values())
for c in legacy['cases']:
    for k in ['atlases','cleanAtlases','actorAtlases']:legacy_paths.update(c.get(k,[]))
    legacy_paths.update(c.get('waterTint',{}).get('textures',[]))
for old in legacy_paths:
    new='assets/approved/'+old.removeprefix('assets/');all_paths.add(new)
    # Image bytes may differ after lossless PNG optimization; decoded pixels must not.
    a=Image.open(G.BASE/old).convert('RGBA');b=Image.open(G.OUT/new).convert('RGBA')
    check(a.size==b.size and a.tobytes()==b.tobytes(),'Approved pixels changed: '+old)

baseline=json.loads((G.BASE/'source/runtime-before.json').read_text());project=G.BASE.parents[2]
changed=[p for p,h in baseline.items() if not (project/p).exists() or hashlib.sha256((project/p).read_bytes()).hexdigest()!=h]
check(not changed,'Production baseline changed: '+str(changed))
report={'passed':not errors,'cases':len(metas),'closeups':len(captures),'map':len(maps),'approved':6,'profiles':catalog['coverage']['profiles'],'fx':len(catalog['effects']),'one_result_callback_cases':len(captures),'distinct_hero_critical_programs':len(set(cinemas)),'exact_reference_frame_comparisons':pixel_checks,'approved_assets_pixel_equal':len(legacy_paths),'production_baseline_files':len(baseline),'production_changed':changed,'fx_endings':fx_endings,'errors':errors,'elapsed_seconds':round(time.time()-START,2),'scope':'Controlled fixtures run the existing Godot controllers. Layout variants are not additional gameplay abilities or full campaign playthroughs.'}
(G.OUT/'qa/verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
(G.OUT/'qa/referenced-images.json').write_text(json.dumps(sorted(all_paths),indent=2))
with (G.OUT/'qa/action-mapping.csv').open('w',newline='',encoding='utf-8-sig') as f:
    writer=csv.DictWriter(f,fieldnames=mapping[0].keys());writer.writeheader();writer.writerows(mapping)
print(json.dumps({k:v for k,v in report.items() if k!='fx_endings'},ensure_ascii=False,indent=2))
raise SystemExit(0 if report['passed'] else 1)
