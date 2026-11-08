from pathlib import Path
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
import json,math,hashlib,collections,csv,time
import build_gallery as B

start=time.time();errors=[]
def check(condition,message):
    if not condition:errors.append(message)
data=B.G.read_js(B.OUT/'catalog.js');old=B.G.read_js(B.OLD/'catalog.js')
metas={c['key']:c for c in data['cases']};changed=set(json.loads((B.ROOT/'changed-cases.json').read_text()))
check(set(metas)=={c['key'] for c in old['cases']},'The complete previous case inventory was not retained')
check(len(changed)==560,'Expected 560 revised comparisons')
cases={};sources={};paths=set();full=[];coverage=collections.Counter()
for meta in data['cases']:
    if meta.get('legacy'):continue
    c=B.load_case(B.OUT/'cases'/(meta['key']+'.js'));cases[c['key']]=c
    for layer,items in c['atlases'].items():
        paths.update(items)
        check(len(c['layerMap'][layer])>max(c['timeline']),c['key']+': truncated layer map')
    for cue in c['fxPlan']:
        check(cue['effect'] in data['effects'],c['key']+': missing effect '+cue['effect'])
        if 'track' in cue:check(len(cue['track'])==len(c['timeline']),c['key']+': cue track length mismatch')
        if 'until' in cue:check(cue['start']<cue['until']<=c['duration']+.001,c['key']+': invalid phase interval')
        if cue['effect'].startswith('r2-') and data['effects'][cue['effect']]['loop']:check('until' in cue,c['key']+': unbounded magic loop')
    if c['key'] not in changed:continue
    coverage[c['family']]+=1
    if c['family']=='map':
        original=B.load_case(B.OLD/'cases'/(c['key']+'.js'))
        check(c['source']['targets']==original['source']['targets'],c['key']+': MAP receipt changed')
        check(len(c['fxPlan'])==len(original['fxPlan']),c['key']+': MAP target cue count changed')
        sources[c['key']]=B.PRE/'map-captures'/c['key']/'capture.json'
    else:
        new=B.ROOT/'captures'/c['key']/'capture.json'
        sources[c['key']]=new if new.exists() else B.PRE/'captures'/c['key']/'capture.json'
        d=json.loads(sources[c['key']].read_text());j=d['job']
        check(d['contact_calls']==1 and c['source']['contacts']==1,c['key']+': result callback count changed')
        check(c['source']['event']==j['event'],c['key']+': gameplay receipt changed')
        check(abs(c['contact']-d['contact_time'])<1e-8,c['key']+': result timing changed')
        check(not d['layout_errors'] and not d['missing_animations'],c['key']+': source capture errors')
        if c['family'] in ['lance','javelin']:
            expected=B.LANCES[int(j['class_id'])]['id']
            check(c['fxPlan'][0]['effect'].startswith('r2-lance-'+expected),c['key']+': wrong profession spear design')
        if c['family']=='archery':
            expected=B.bow_for(j['profile'],int(j['class_id']))['id']
            check(c['projectile']['effect']=='r2-arrow-'+expected,c['key']+': wrong profession bow design')
            check(c['fxPlan'][0]['effect']=='r2-bowhit-'+expected,c['key']+': wrong arrow impact')
            check(all(p is None for i,p in enumerate(c['projectile']['anchors']) if i/60>=c['contact']+.02),c['key']+': arrow survives past contact')
        if c['family'] in ['magic','lightning-sword']:
            check(c.get('fullReplacement') and 'clean' in c['atlases'],c['key']+': old spell layer not removed')
            check(all(p['effect'].startswith('r2-') for p in c['fxPlan']),c['key']+': mixed old spell effect')
            impact=[p for p in c['fxPlan'] if p['effect'].endswith('-impact')]
            check(len(impact)==1,c['key']+': expected one main spell impact')
            if impact:
                hit=data['effects'][impact[0]['effect']]['options']['hit']
                check(abs(impact[0]['start']+hit-c['contact'])<1e-6,c['key']+': main effect impact not synchronized')
        if c['family']=='cinema' and 'eileen' in c['key'] and 'sword' not in c['key']:
            check(d.get('clean_cinema_version')==2 and c.get('fullReplacement'),c['key']+': incomplete cinema magic cleanup')
    if c.get('fullReplacement'):full.append(c['key'])

for spec in data['effects'].values():paths.add(spec['path'])
missing=[p for p in paths if not (B.OUT/p).is_file()];check(not missing,'Missing image paths: '+str(missing[:6]))

def compare(item):
    key,path=item;d=json.loads(path.read_text());c=cases[key];opened={};failures=[];checks=0
    def image(path):
        if path not in opened:opened[path]=Image.open(path).convert('RGBA')
        return opened[path]
    def rebuild(layer,idx):
        im=Image.new('RGBA',(592,240))
        for name in ['plate',layer]:
            tile=c['layerMap'][name][idx];spec=c['layerSpecs'][name];w,h=spec['size'];cell=tile%c['atlasFrames'];sheet=image(B.OUT/c['atlases'][name][tile//c['atlasFrames']]);x=cell%c['atlasCols']*w;y=cell//c['atlasCols']*h;im.alpha_composite(sheet.crop((x,y,x+w,y+h)),tuple(spec['at']))
        return im
    for sec in [0,c.get('chargeTime',c['actionTime']),c['contact'],c['duration']]:
        n=min(len(c['timeline'])-1,math.floor(sec*60+1e-6));idx=c['timeline'][n]
        for layer in ['current']+(['clean'] if key in full else []):
            sheet=image(path.parent/d['atlases'][layer][idx//16]);x=idx%16%4*592;y=idx%16//4*240;raw=sheet.crop((x,y,x+592,y+240))
            if rebuild(layer,idx).tobytes()!=raw.tobytes():failures.append(key+': '+layer+' pixels differ at '+str(sec))
            checks+=1
    return checks,failures
pixel_checks=0
with ThreadPoolExecutor(max_workers=4) as pool:
    for i,(count,failures) in enumerate(pool.map(compare,sources.items())):
        pixel_checks+=count;errors.extend(failures)
        if i%100==99:print('Verified real-frame comparisons',i+1,flush=True)

metrics={};fx_hashes={};endings=[];edge_warnings=[]
for name,s in B.NEWFX.items():
    im=Image.open(B.OUT/s['path']).convert('RGBA');w,h=s['frameSize'];masses=[];sha=hashlib.sha256()
    for i in range(s['frames']):
        x=i%s['columns']*w;y=i//s['columns']*h;tile=im.crop((x,y,x+w,y+h));alpha=tile.getchannel('A');sha.update(tile.tobytes())
        masses.append(sum(alpha.getdata())/255)
        if i==s['frames']-1 and not s['loop']:check(alpha.getextrema()[1]==0,name+': visible one-shot ending')
        box=alpha.point(lambda x:255 if x>=40 else 0).getbbox()
        if box and (box[0]==0 or box[1]==0 or box[2]==w or box[3]==h):edge_warnings.append({'effect':name,'frame':i,'bounds':box})
    metrics[name]={'peak_alpha_area':round(max(masses),2),'integrated_alpha_area':round(sum(masses)/60,2)};fx_hashes[name]=sha.hexdigest()
chains=[['r2-lance-'+B.LANCES[c]['id'] for c in chain] for chain in [[6,2,22],[1,4,7],[3,5]]]
chains+=[['r2-bowhit-archer','r2-bowhit-sniper','r2-bowhit-bowknight'],['r2-bowhit-hero-base','r2-bowhit-hero-advanced']]
for chain in chains:
    values=[metrics[n]['peak_alpha_area'] for n in chain]
    check(all(b>a*1.1 for a,b in zip(values,values[1:])),'Promotion strength not increasing: '+str(chain))
check(len({fx_hashes['r2-lance-'+x['id']] for x in B.DESIGN['lance']})==8,'Spear professions share identical effects')
check(len({fx_hashes['r2-arrow-'+x['id']] for x in B.DESIGN['bows']})==5,'Bow professions share identical arrows')
check(not edge_warnings,'Native effect sprites touch canvas bounds: '+str(edge_warnings[:8]))
check((B.OUT/'approved-data.js').read_bytes()==(B.OLD/'approved-data.js').read_bytes(),'Approved scene data modified')
check((B.OUT/'water-palette.js').read_bytes()==(B.OLD/'water-palette.js').read_bytes(),'Approved water palette modified')
baseline=json.loads((B.ROOT/'production-before.json').read_text());project=B.BASE.parents[2]
def changed_production(pair):
    path,digest=pair;p=project/path
    return path if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest else None
with ThreadPoolExecutor(max_workers=4) as pool:production_changed=[p for p in pool.map(changed_production,baseline.items()) if p]
motion_files=['data/reviewed_animations.json','data/animation_runtime/reviewed.json','data/animation_runtime/reviewed.bin','data/critical_cinema.json','data/legacy/rules_full.json','data/campaign_promotions_20261030.json','core/critical_cinema.gd','core/hero_professions.gd','core/reviewed_animations.gd','core/animation_programs.gd']
motion_audit=[]
for name in motion_files:
    a=project/'actual'/name;b=B.PRE/'runtime-snapshot'/name
    equal=hashlib.sha256(a.read_bytes()).digest()==hashlib.sha256(b.read_bytes()).digest()
    motion_audit.append({'file':name,'matches_capture_snapshot':equal});check(equal,'In-scope motion data changed: '+name)
asset_changes=[p for p in production_changed if p.startswith('actual/assets/')]
check(not asset_changes,'Existing captured artwork changed: '+str(asset_changes))
report={'passed':not errors,'total_cases':len(data['cases']),'revised_cases':len(changed),'revision_families':dict(coverage),'distinct_lance_professions':8,'distinct_bow_designs':5,'full_magic_types':13,'full_magic_cases':390,'full_magic_cinemas':8,'native_fx_atlases':len(B.NEWFX),'exact_reference_and_clean_frame_checks':pixel_checks,'profession_strength_checks':[{ 'chain':c,'metrics':[metrics[n] for n in c]} for c in chains],'native_bounds_errors':edge_warnings,'production_files_checked':len(baseline),'workspace_changes_outside_preview':production_changed,'in_scope_motion_audit':motion_audit,'existing_captured_artwork_changes':asset_changes,'sampling_base':'The same isolated Godot snapshot used by the previous comparison. Newly added story puppets are outside this weapon/magic revision.','scope_review':'Read-only diff review: battle_animation additions handle trio effects and mechanical part/revival reactions; ordinary profession hit/recovery paths are unchanged. legacy_main HP layout remains identical for non-Prometheus fixtures. No production write operations were performed by this preview task.','errors':errors,'seconds':round(time.time()-start,2)}
(B.OUT/'qa/verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
(B.OUT/'qa/production-assets.json').write_text(json.dumps({'files_checked':len(baseline),'existing_artwork_changed':asset_changes,'workspace_changes_outside_preview':production_changed,'in_scope_motion_audit':motion_audit,'baseline':'Captured at the start of this revision. Parallel story/puppet changes were observed, read for scope impact, and retained. Preview outputs stay in art-review.'},ensure_ascii=False,indent=2))
(B.OUT/'qa/referenced-images.json').write_text(json.dumps(sorted(paths),indent=2))
(B.OUT/'qa/fx-metrics.json').write_text(json.dumps(metrics,indent=2))
mapping=json.loads((B.ROOT/'action-effect-mapping.json').read_text())
with (B.OUT/'qa/action-mapping.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=mapping[0].keys());writer.writeheader();writer.writerows(mapping)
print(json.dumps({k:v for k,v in report.items() if k not in ['profession_strength_checks']},ensure_ascii=False,indent=2))
raise SystemExit(0 if report['passed'] else 1)
