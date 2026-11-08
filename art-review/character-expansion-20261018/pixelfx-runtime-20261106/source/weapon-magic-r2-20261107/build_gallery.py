from pathlib import Path
from PIL import Image
import sys,json,math,hashlib,collections,statistics

ROOT=Path(__file__).resolve().parent;PRE=ROOT.parent/'full-battle-20261107';BASE=ROOT.parent.parent
OUT=BASE/'weapon-magic-r2-20261107';OLD=BASE/'full-battle-20261107'
sys.path.insert(0,str(PRE));import build_gallery as G
# This module has the same filename; load the previous builder explicitly.
import importlib.util
spec=importlib.util.spec_from_file_location('previous_gallery',PRE/'build_gallery.py');G=importlib.util.module_from_spec(spec);spec.loader.exec_module(G)
G.OUT=OUT
DESIGN=json.loads((ROOT/'design.json').read_text())
LANCES={x['class']:x for x in DESIGN['lance']}
BOWS={str(x.get('class',x.get('profile'))):x for x in DESIGN['bows']}
MAGIC={x['weapon']:x for x in DESIGN['magic']}
NEWFX=json.loads((OUT/'assets/fx/manifest.json').read_text())['effects']
ANGLES={a['key']:a['angle'] for a in json.loads((ROOT/'weapon-angles.json').read_text())}
OLDPREFIX='assets/base/'
def load_case(path):return json.loads(path.read_text().split(']=',1)[1].rstrip(';\n'))
def save_case(c):
    (OUT/'cases'/(c['key']+'.js')).write_text('window.PIXELFX_CASES=window.PIXELFX_CASES||{};window.PIXELFX_CASES['+json.dumps(c['key'])+']='+json.dumps(c,ensure_ascii=False,separators=(',',':'))+';\n')
def old_case(key):
    c=load_case(OLD/'cases'/(key+'.js'))
    for layer,paths in c['atlases'].items():c['atlases'][layer]=[OLDPREFIX+p for p in paths]
    c['revision']=1;return c
def clean_layer(d,folder,c):
    dest=OUT/'assets/runtime'/d['id'];dest.mkdir(parents=True,exist_ok=True)
    cache=dest/'clean-map.json';digest=hashlib.sha256((folder/'capture.json').read_bytes()).hexdigest()
    if cache.exists():
        saved=json.loads(cache.read_text())
        if saved['source_hash']==digest:
            c['atlases']['clean']=saved['paths'];c['layerSpecs']['clean']=saved['spec'];c['layerMap']['clean']=saved['mapping'];return
    frames=[];mapping=[];seen={};opened={}
    for idx in range(d['unique_frames']):
        name=d['atlases']['clean'][idx//16]
        if name not in opened:opened[name]=Image.open(folder/name).convert('RGBA')
        x=idx%16%4*592+191;y=idx%16//4*240;im=opened[name].crop((x,y,x+256,y+128));sha=hashlib.sha256(im.tobytes()).digest()
        if sha not in seen:seen[sha]=len(frames);frames.append(im)
        mapping.append(seen[sha])
        if idx%16==15:opened.clear()
    paths=[]
    for start in range(0,len(frames),16):
        group=frames[start:start+16];sheet=Image.new('RGBA',(1024,128*math.ceil(len(group)/4)))
        for n,im in enumerate(group):sheet.paste(im,((n%4)*256,(n//4)*128))
        path=dest/('clean-r2-%03d.png'%(start//16));sheet.save(path,compress_level=6);paths.append(str(path.relative_to(OUT)))
    entry={'source_hash':digest,'paths':paths,'mapping':mapping,'spec':{'size':[256,128],'at':[191,0]}}
    cache.write_text(json.dumps(entry,separators=(',',':')))
    c['atlases']['clean']=paths;c['layerMap']['clean']=mapping;c['layerSpecs']['clean']=entry['spec']
def bow_for(profile,cid):
    if profile in ['21_ally','23_ally']:return BOWS[profile]
    return BOWS[str(cid)]
def mark(c,design):
    c['revision']=2;c['design']={'name':design['direction'],'profession':design['name'],'tier':design.get('rank',design.get('tier'))}
    c['subtitle']+=' · '+design['direction']
def positions(d,folder):
    contact=d['contact_time'];sample=G.frame_at(d['frames'],contact);off=G.target_offset(d,folder);actor=sample['actor'];target=sample['target']
    direction=1 if target[0]>actor[0] else -1
    point=[round(target[0]+off[0]-direction*2),round(max(66,min(108,target[1]+off[1])))]
    return point,direction
def weapon_case(c,d,folder):
    j=d['job'];family=j['family'];point,direction=positions(d,folder)
    if family in ['lance','javelin']:
        design=LANCES[int(j['class_id'])];effect='r2-lance-'+design['id']
        if family=='lance' and ANGLES.get(c['key']):effect+='-angle'+str(ANGLES[c['key']])
        c['fxPlan']=[{'effect':effect,'start':c['contact']-.07,'anchor':point,'flip':direction<0,'alpha':1}]
        if family=='javelin':
            c['projectile']['effect']='r2-wake-'+design['id']
            c['treatment']='原投枪保持完整，枪尾换为该职业的专属气流。'+design['description']
        else:c['treatment']=design['description']+'保留真实枪击动作与一次命中。'
    else:
        design=bow_for(j['profile'],int(j['class_id']))
        flight_points=[p for p in c['projectile']['anchors'] if p]
        if flight_points:
            point[1]=round(max(64,min(112,flight_points[-1][1])))
            # The legacy projectile travels a few pixels beyond offset body roots.
            # Let the new arrow enter the actual silhouette, then hold until its
            # unchanged result callback instead of visibly passing through.
            c['projectile']['anchors']=[[max(p[0],point[0]) if direction<0 else min(p[0],point[0]),p[1]] if p else None for p in c['projectile']['anchors']]
            c['projectile']['contact_clamp']='Captured target silhouette; original release and contact times unchanged.'
        c['projectile']['effect']='r2-arrow-'+design['id']
        c['fxPlan']=[{'effect':'r2-bowhit-'+design['id'],'start':c['contact']-.07,'anchor':point,'flip':direction<0,'alpha':1}]
        c['treatment']=design['description']+'保留原飞行时序，箭尖在实际人物轮廓处收住；始终只有一支实体箭、一次结算。'
    c['impactTime']=c['contact']+.055;mark(c,design)
def spell_case(c,d,folder):
    j=d['job'];design=MAGIC[int(j['weapon'])];point,direction=positions(d,folder);rows=G.make_timeline(d['frames'],d['duration']);contact=c['contact'];kind=design['id']
    fxrows=[r for r in d['frames'] if r['effects']];first=fxrows[0]['t'] if fxrows else contact-.7
    start=max(.42,min(first,contact-.65));flight=min(.46,max(.18,(contact-start)*.2));release=contact-flight;arrival=contact
    # Medians keep orbiting outer motes from being mistaken for a release.
    origin_dx=None;departure=None;bound_arrival=None;near_arrival=None
    for row in fxrows:
        if row['t']>=contact:break
        points=[fx['point'] for fx in row['effects'] if fx['role']!='defender']
        if not points:continue
        mx=statistics.median(p[0] for p in points);ax=row['actor'][0];tx=row['target'][0]
        if origin_dx is None and abs(mx-ax)<55:origin_dx=mx-ax
        if origin_dx is not None and departure is None and row['t']>start+.1 and direction*(mx-(ax+origin_dx))>14:departure=row['t']
        if departure is not None and row['t']>=departure:
            if bound_arrival is None and any(e['bound'] for e in row['effects']):bound_arrival=row['t']
            if near_arrival is None and abs(mx-tx)<17:near_arrival=row['t']
    if departure is not None:release=max(start+.12,min(contact-.10,departure))
    detected_arrival=bound_arrival if bound_arrival is not None else near_arrival
    if detected_arrival is not None and contact-detected_arrival>.5:arrival=max(release+.1,min(contact,detected_arrival))
    elif kind in ['death','medusa'] and departure is not None:arrival=min(contact,release+.55)
    flight=arrival-release
    offset=[direction*10,-33]
    for row in fxrows:
        found=False
        for fx in row['effects']:
            x,y,w,h=fx['rect'];center=[x+w/2,y+h/2]
            if fx['role']!='defender' and not fx['bound'] and abs(center[0]-row['actor'][0])<40 and center[1]<116:
                offset=[center[0]-row['actor'][0],max(-62,min(-21,center[1]-row['actor'][1]))];found=True;break
        if found:break
    caster=[[round(r['actor'][0]+offset[0]),round(max(32,r['actor'][1]+offset[1]))] for r in rows]
    clean_layer(d,folder,c);c['fullReplacement']=True;c['fxPlan']=[];c.pop('projectile',None)
    has_flight=kind in ['fire','ragnarok','holy','wind','wisp','slime','death','medusa']
    charge_until=release if has_flight else contact-design['hit']
    if kind in ['rain','halo'] and departure is not None:charge_until=min(charge_until,release)
    if kind=='levin':
        charged=[r['t'] for r in fxrows if any(e['role']=='attacker_charge' for e in r['effects']) and r['t']<contact]
        if charged:charge_until=min(charge_until,max(charged)+1/30)
    charge_cue={'effect':'r2-'+kind+'-charge','start':start,'until':charge_until,'alpha':.88,'fadeIn':.16,'fadeOut':.1}
    if kind=='drain':charge_cue['anchor']=point
    else:charge_cue['track']=caster
    c['fxPlan'].append(charge_cue)
    c['chargeTime']=start+min(.32,max(.01,(charge_until-start)/2))
    if has_flight:
        launch=caster[min(len(caster)-1,math.floor(release*60))];destination=point
        if kind=='ragnarok':launch=[launch[0],116];destination=[point[0],116]
        track=[]
        for n in range(len(rows)):
            t=n/60;u=(t-release)/flight
            if not 0<=u<1:track.append(None);continue
            arc={'slime':18,'fire':9,'ragnarok':0,'holy':8,'wind':3,'wisp':4,'death':5,'medusa':2}[kind]
            track.append([round(launch[0]+(destination[0]-launch[0])*u),round(launch[1]+(destination[1]-launch[1])*u-math.sin(u*math.pi)*arc)])
        c['fxPlan'].append({'effect':'r2-'+kind+'-travel','start':release,'until':arrival,'track':track,'flip':direction<0,'alpha':1})
    hold_start=None
    if arrival<contact-.4:hold_start=arrival
    elif kind=='levin' and charge_until<contact-design['hit']-.2:hold_start=max(charge_until+.04,contact-.65)
    elif contact-start>2 and kind in ['halo','rain']:hold_start=contact-min(1.4,(contact-start)*.27)
    if hold_start is not None:
        c['fxPlan'].append({'effect':'r2-'+kind+'-charge','start':hold_start,'until':contact-design['hit'],'anchor':[point[0],point[1]-8],'alpha':.72,'fadeIn':.15,'fadeOut':.12})
    c['fxPlan'].append({'effect':'r2-'+kind+'-impact','start':contact-design['hit'],'anchor':point,'flip':False,'alpha':1})
    if kind=='drain' and j['event'].get('heal',0)>0:
        track=[];return_start=contact-.45;return_end=contact
        for n in range(len(rows)):
            u=(n/60-return_start)/(return_end-return_start)
            if not 0<=u<1:track.append(None);continue
            dest=caster[n];track.append([round(point[0]+(dest[0]-point[0])*u),round(point[1]+(dest[1]-point[1])*u-math.sin(u*math.pi)*8)])
        c['fxPlan'].append({'effect':'r2-drain-travel','start':return_start,'until':return_end,'track':track,'flip':direction>0,'alpha':.85,'fadeOut':.12})
    c['treatment']='完整替换旧魔法层：'+design['direction']+'。人物、受击和生命结算保持原样。'
    if kind=='medusa':c['treatment']+='不添加石化状态。'
    if kind=='slime':c['treatment']+='不添加持续伤害或中毒。'
    c['actionTime']=release+flight*.5 if has_flight else max(start,contact-design['hit']-.18);c['impactTime']=contact+.08
    c['spellPhases']={'charge':start,'chargeEnd':charge_until,'release':release if has_flight else charge_until,'arrival':max(charge_until,arrival),'contact':contact,'kind':kind,'release_from_source_effect_motion':departure is not None}
    mark(c,design)
def cinema_spell(c,d):
    design=MAGIC[int(d['job']['weapon'])];kind=design['id'];rows=G.make_timeline(d['frames'],d['duration']);contact=c['contact']
    charge_offset=[30,-151]
    for row in d['frames']:
        v=row.get('cinema',{})
        if not v.get('actor'):continue
        found=False
        for effect in v.get('effects',[]):
            x,y,w,h=effect['rect'];center=[x+w/2,y+h/2]
            if abs(center[0]-v['actor'][0])<90:
                charge_offset=[center[0]-v['actor'][0],center[1]-v['actor'][1]];found=True;break
        if found:break
    targets=[];actors=[]
    for row in rows:
        v=row.get('cinema');target=None;actor=None
        if v and v['show']>.95:
            if v['target']:target=[round(v['origin'][0]+v['target'][0]*v['scale']),round(v['origin'][1]+v['target'][1]*v['scale']-34)]
            if v.get('actor'):actor=[round(v['origin'][0]+(v['actor'][0]+charge_offset[0])*v['scale']),round(v['origin'][1]+(v['actor'][1]+charge_offset[1])*v['scale'])]
        targets.append(target);actors.append(actor)
    first=next((r['t'] for r in d['frames'] if r.get('cinema',{}).get('effects')),contact-1.35)
    start=max(.6,min(first,contact-.9));flight=.62;release=contact-flight;flight_enabled=kind in ['fire','holy','wind'];plan=[]
    plan.append({'effect':'r2-cinema-'+kind+'-charge','start':start,'until':release if flight_enabled else contact-design['hit'],'track':actors,'alpha':.9,'fadeIn':.2,'fadeOut':.12})
    c['chargeTime']=start+.32
    if flight_enabled:
        source=next((actors[i] for i in range(min(len(rows)-1,math.floor(release*60)),len(rows)) if actors[i]),[220,120]);track=[]
        for n in range(len(rows)):
            u=(n/60-release)/flight;p=targets[n]
            track.append([round(source[0]+(p[0]-source[0])*u),round(source[1]+(p[1]-source[1])*u-math.sin(u*math.pi)*10)] if 0<=u<1 and p else None)
        plan.append({'effect':'r2-cinema-'+kind+'-travel','start':release,'until':contact,'track':track,'alpha':1})
    plan.append({'effect':'r2-cinema-'+kind+'-impact','start':contact-design['hit'],'track':targets,'alpha':1})
    c['fxPlan']=plan;c['fullReplacement']=True;c.pop('cinemaEffect',None);c['treatment']='必杀的蓄势、飞行与命中魔法层全部改为 PixelFX：'+design['direction']+'。保留原镜头、人物动作和一次结算。'
    c['actionTime']=(release+contact)/2 if flight_enabled else contact-.33;c['impactTime']=contact+.08;c['spellPhases']={'charge':start,'release':release,'contact':contact,'kind':kind}
    c['source']['clean_version']=2;mark(c,design)
def main():
    data=G.read_js(OLD/'catalog.js');catalog=[];changed=[];mapping=[];errors=[]
    for n,meta in enumerate(data['cases']):
        m=dict(meta);key=m['key']
        if m.get('legacy'):
            if m['legacy']=='archery':m['revision']=2;m['subtitle']+=' · 基础弓手新版';changed.append(key)
            catalog.append(m);continue
        try:
            recapture=ROOT/'captures'/key/'capture.json'
            source=recapture if recapture.exists() else PRE/'captures'/key/'capture.json'
            if recapture.exists():G.build_case(recapture);c=load_case(OUT/'cases'/(key+'.js'))
            else:c=old_case(key)
            if c['family'] in ['lance','javelin','archery','magic','lightning-sword'] or recapture.exists():
                d=json.loads(source.read_text())
                if recapture.exists():cinema_spell(c,d)
                elif c['family'] in ['lance','javelin','archery']:weapon_case(c,d,source.parent)
                else:spell_case(c,d,source.parent)
                mapping.append({'id':key,'profile':d['job']['profile'],'actor_id':d['job']['actor']['id'],'weapon':d['job']['weapon'],'program':d['job']['program'],'contact':d['contact_time'],'callbacks':d['contact_calls'],'effect_direction':c['design']['name'],'full_replacement':c.get('fullReplacement',False)})
            elif c['family']=='cinema' and 'hunapu-bow' in key:
                design=BOWS['23_ally' if 'advanced' in key else '21_ally']
                c.pop('cinemaEffect',None);c['fullReplacement']=True
                c['fxPlan']=[{'effect':'r2-cinema-bowhit-'+design['id'],'start':c['contact']-.07,'track':[[p[0],p[1]-32] if p else None for p in c['cinemaTargets']],'alpha':1}]
                c['treatment']='保留男主原有单箭追镜，命中改为独立的'+design['direction']+'锐角冲击。基础与进阶使用各自的强度。';c['impactTime']=c['contact']+.05;mark(c,design)
            elif key=='map-hunapu-bow':
                for cue in c['fxPlan']:
                    cue['effect']='r2-map-hero-bow';cue['start']-=.07;cue['track']=[[p[0],p[1]-12] if p else None for p in cue['track']];cue['alpha']=1
                c['treatment']='男主持弓 MAP 使用独立的铜金羽状命中芒；原范围、真实目标和各目标结算时刻保持一致。';mark(c,BOWS['23_ally'])
            if c.get('revision')==2:changed.append(key)
            save_case(c)
            for field in ['title','subtitle','family','group','profile','side','move','far','heavy','reaction','duration']:m[field]=c[field]
            m['revision']=c.get('revision',1);m['design']=c.get('design');catalog.append(m)
        except Exception as e:errors.append({'id':key,'error':str(e)})
        if n%100==99:print('Built',n+1,flush=True)
    effects={k:{**v,'path':OLDPREFIX+v['path']} for k,v in data['effects'].items()};effects.update(NEWFX)
    rows=[]
    for label,chain in [('步兵枪系',[6,2,22]),('骑兵枪系',[1,4,7]),('飞行枪系',[3,5]),('弓箭晋阶',[12,13,20]),('男主专属',['21_ally','23_ally'])]:
        buttons=[]
        for value in chain:
            bow=label in ['弓箭晋阶','男主专属'];profile=value if isinstance(value,str) else str(value)+'_ally';family='archery' if bow else 'lance'
            match=next(c for c in catalog if c['profile']==profile and c['family']==family and not c['far'] and not c['heavy'] and (not bow or c['move']=='弓箭'))
            design=BOWS[str(value)] if bow else LANCES[value]
            buttons.append({'case':match['key'],'name':design['name'],'subtitle':design['direction'],'stage':design.get('rank',design['tier'])})
        rows.append({'label':label,'buttons':buttons})
    featured=[]
    for weapon in [15,24,23,25,26,27,28,29,31,32,33,34,42]:
        options=[c for c in catalog if c['family'] in ['magic','lightning-sword'] and not c['far'] and not c['heavy'] and c.get('design',{}).get('name')==MAGIC[weapon]['direction']]
        if options:featured.append(sorted(options,key=lambda c:c['profile']!='eileen')[0]['key'])
    featured+=['cinema-eileen-thunder-advanced','cinema-eileen-fire-advanced','cinema-hunapu-bow-advanced','map-hunapu-bow','approved-water']
    data.update({'cases':catalog,'effects':effects,'featured':featured,'progressionRows':rows,'revision':2,'updatedCases':len(changed),'defaultCase':rows[0]['buttons'][0]['case']})
    (OUT/'catalog.js').write_text('window.PIXELFX_CATALOG='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n')
    (ROOT/'changed-cases.json').write_text(json.dumps(changed,indent=2));(ROOT/'action-effect-mapping.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2))
    (OUT/'qa/build-report.json').write_text(json.dumps({'cases':len(catalog),'updated':len(changed),'full_spell_replacements':sum(c.get('family') in ['magic','lightning-sword'] for c in catalog),'cinema_full_replacements':8,'errors':errors},ensure_ascii=False,indent=2))
    print('Finished',len(catalog),'updated',len(changed),'errors',errors)
    if errors:raise SystemExit(1)
if __name__=='__main__':main()
