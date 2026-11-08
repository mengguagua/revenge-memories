"""Build R4 as a review-only layer over the unchanged Godot frames."""
from bisect import bisect_right
from collections import Counter
from copy import deepcopy
import importlib.util
import json
import math
from pathlib import Path
import subprocess
from statistics import median
import sys

import build_actions as actions

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]
OUT=BASE/HERE.name
PREVIOUS=BASE/'magic-sound-r3-20261107'
SRC=HERE.parent
SOUND_PY=Path('/Users/gcc/gaocc/project/StableAudio3SmallSFX/optimized/mlx/.venv/bin/python')
FPS=60
FAMILIES={'火球':'fire','诸神黄昏':'ragnarok','雷电':'thunder','雷剑':'levin'}
GUARDS={'6b455cb494a1','6689f9fcdafc'}


def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


R3=load_module('frozen_r3',SRC/'magic-sound-r3-20261107/build_gallery.py')
R1=load_module('frozen_r1',SRC/'full-battle-20261107/build_gallery.py')
R3.OUT=OUT
R1.OUT=OUT


def read_json(path):
    return json.loads(path.read_text())


def rounded(point):
    return list(map(round,point))


def clamp(x,a=0,b=1):
    return min(b,max(a,x))


def frame_time(t):
    return math.ceil(t*FPS-1e-7)/FPS


def point_in_scene(row, point):
    sc=row['cinema'];return actions.game_point(sc,point)


def fx_point(e):
    x,y,w,h=e['rect'];return [x+w/2,y+h/2]


def source_before(data,t):
    return data['frames'][max(0,bisect_right([row['t'] for row in data['frames']],t)-1)]


def target_anchors(case,data):
    c=case['contact']
    row=source_before(data,c-.025)
    p=case['fxPlan'][-1]
    pivot=p.get('anchor')
    if pivot is None:
        track=p['track'];n=min(len(track)-1,math.ceil(c*FPS))
        pivot=track[n] or next(t for t in track if t)
    if case['family']=='cinema':
        tx,ground=point_in_scene(row,row['cinema']['target'])
        return rounded([pivot[0],pivot[1]]),rounded([tx,ground-3])
    return rounded(pivot),rounded([pivot[0],row['target'][1]-4])


def cue(name,start,anchor=None,**kwargs):
    return dict(effect='r4-'+name,start=start,**({'anchor':anchor} if anchor is not None else {}),**kwargs)


def spaced_track(n,start,end,path):
    marks=[t for t,*_ in path]
    out=[None]*n
    for f in range(max(0,math.ceil(start*FPS)),min(n,math.ceil(end*FPS)+1)):
        u=clamp((f/FPS-start)/max(.0001,end-start))
        i=max(0,min(len(path)-2,bisect_right(marks,u)-1))
        t,x,y=path[i];q,bx,by=path[i+1]
        v=clamp((u-t)/max(.0001,q-t))
        out[f]=rounded([x+(bx-x)*v,y+(by-y)*v])
    return out


def from_fire_capture(case,d):
    c=case['contact']; cinema=case['family']=='cinema'; points=[]
    charge=None
    for row in d['frames']:
        if row['t']>=c:
            break
        if cinema:
            sc=row.get('cinema',{})
            for e in sc.get('effects',[]):
                if 'spell-fire-' in e['source'] and charge is None:
                    charge=row['t']
                if 'fire-flight-' in e['source']:
                    points.append((row['t'],point_in_scene(row,fx_point(e))))
        else:
            options=[e for e in row['effects'] if not e['bound']]
            if options:
                if charge is None:
                    charge=row['t']
                points.append((row['t'],options[0]['point']))
    assert charge is not None and len(points)>4
    if cinema:
        start,origin=points[0]
        flight=points[1:]
    else:
        opening=[p for t,p in points if charge+.1<t<charge+.45]
        origin=[median(p[i] for p in opening) for i in range(2)]
        depart=next(i for i,(t,p) in enumerate(points) if t>charge+.5 and abs(p[0]-origin[0])>=3)
        start,first=points[depart]
        # The replacement starts on the first captured moving frame, with
        # its center close to the ball in the preceding stationary frame.
        origin=[origin[0]+.56*(first[0]-origin[0]),origin[1]+.56*(first[1]-origin[1])]
        flight=points[depart+1:]
    body,ground=target_anchors(case,d)
    direct=1 if body[0]>origin[0] else -1
    delta=abs(body[0]-origin[0])
    goal=[body[0],max(case['field'][1]+20,body[1]-3)]
    # Keep native sample geometry but distribute its last few pixels all the
    # way to contact, rather than holding a motionless lit ball on the target.
    route=[(start,*origin)];max_dx=1
    for t,p in flight:
        dx=direct*(p[0]-origin[0])
        if dx>=max_dx and dx<delta-3:
            route.append((t,*p));max_dx=dx+1
    last=route[-1]
    t_end=clamp(last[0]+max(.024,min(.090,(delta-max_dx)*.002)),start+.075,c)
    route=[(clamp((t-start)/(t_end-start),0,.97),x,y) for t,x,y in route]+[(1,*goal)]
    return frame_time(charge),frame_time(start),route,direct,body,ground


def apply_fire(c,d,tasks):
    contact=c['contact'];cinema=c['family']=='cinema'
    charge,start,route,direct,body,ground=from_fire_capture(c,d)
    # Only the candidate swaps layers. Every frame before the native launch
    # still comes from the exact same Godot render on both sides.
    hit=frame_time(contact)
    c.pop('fullReplacement',None)
    c.pop('suppressFlash',None)
    name=('fireball-cinema-advanced' if 'advanced' in c['key'] else 'fireball-cinema') if cinema else 'fireball'
    track=spaced_track(len(c['timeline']),start,hit,route)
    c.update(replaceEffectsFrom=start,fxPlan=[
        cue(name,start,until=hit,track=track,flip=direct<0,trailLimit=round(route[0][1]+(-10 if direct>0 else 10)),
            offset=.21),
        cue(name+'-hit',hit,[body[0],min(ground[1],body[1]+4)]),
    ],actionTime=(start+hit)/2,impactTime=hit+.085,chargeTime=charge+min(.37,(start-charge)*.46))
    c['spellPhases']=dict(kind='fire',charge=charge,release=start,arrival=hit,contact=contact)
    nf,nc=round((hit-start)*FPS),round((start-charge)*FPS)
    key=f'r4-fire-{"cine" if cinema else "battle"}-{nc}-{nf}'
    duration=nc/FPS+nf/FPS+(.80 if cinema else .68)
    c.update(audioName='火球 · 蓄力／飞行／命中',audioCues=[dict(id=key,at=charge,duration=duration,
            gain=.91 if cinema else .86,label='蓄力 → 飞行 → 命中')],
        audioChapters=[dict(label=n,at=t) for n,t in [('蓄力',charge),('飞行',start),('命中',hit)]])
    tasks.append(dict(case=c['key'],cue=key,charge=nc/FPS,flight=nf/FPS,cinema=cinema,at=charge,release=start,contact=contact,hit_frame=hit))
    revision(c,'fire','原蓄力 · 烈焰飞行','保留原蓄力画面。原弹体离手时接上 Fireball 的滚动焰核和烟尾，接触时用同色阶 Explosion 收尾。蓄力、飞行和撞击在同一条连续音轨里。',
        ['fire/fireball','explosions/small-explosion'])


def apply_ragnarok(c,d):
    p=c['spellPhases'];hit=c['contact'];charge=p['charge'];release=p['release'];arrive=p['arrival']
    old=c['fxPlan']
    q=old[0]['track'][math.ceil((charge+.25)*FPS)]
    row=source_before(d,release-.02)
    aim,ground=target_anchors(c,d)
    direct=1 if aim[0]>row['actor'][0] else -1
    launch=[row['actor'][0]+direct*14,ground[1]-7]
    n=len(c['timeline'])
    field_y=c['field'][1]+c['field'][3]
    start_pillar=hit-.55/1.08
    effects=[cue('ragnarok-coil',charge,[q[0],q[1]+11],until=release+.08,alpha=.79,fadeIn=.26,fadeOut=.22)]
    for delay,spread,a in [(0,-5,.85),(.17,4,.66),(.28,0,.55)]:
        end=arrive+delay*.42
        start=release+delay
        route=[(0,*launch),(.26,launch[0]+(ground[0]-launch[0])*.18,field_y-14+spread),
               (.76,launch[0]+(ground[0]-launch[0])*.72,field_y-9+spread),(1,ground[0],ground[1]-3+spread)]
        effects.append(cue('ragnarok-fuse',start,until=end,track=spaced_track(n,start,end,route),
                       flip=direct<0,alpha=a,offset=delay+.13,fadeIn=.10,fadeOut=.13))
    gather=arrive-.20
    effects.append(cue('ragnarok-ring',gather,ground,alpha=.81))
    effects.append(cue('ragnarok-coil',gather+.78,[ground[0],ground[1]-1],until=hit+.06,
                       fadeIn=.37,fadeOut=.28,alpha=.81,offset=.19))
    for layer in ['back','front']:
        effects.append(cue('ragnarok-pillar-'+layer,start_pillar,ground,layer=layer,alpha=.83 if layer=='back' else 1))
    c.update(fullReplacement=True,fxPlan=effects,actionTime=(release+arrive)/2,impactTime=hit+.16,chargeTime=charge+.55)
    c['spellPhases'].update(gather=gather+.30,eruption=hit)
    c['audioCues'].append(dict(id='ragnarok-charge',at=hit-.53,duration=.48,gain=.54,label='地裂将喷'))
    c['audioCues'].sort(key=lambda x:x['at'])
    revision(c,'ragnarok','贴地火脉 · 单柱喷发',
             '炽旋蓄势，三道贴地余焰聚到落点。火环铺开后向中心聚拢，裂地熔缝在原结算时喷出一根火柱，随后熄成烟和余烬。只有一次结算。',
             ['fire/fire-tornado','fire/fireball','fire/fire-ring','fire/flame-pillar'])


def apply_thunder(c,d,kind):
    hit=c['contact'];cinema=c['family']=='cinema'
    p=c['spellPhases']; start=hit-.76/1.33;leader=start+.46/1.33
    wide='-cinema' if cinema else ''
    p0=c['fxPlan'][0]; body,ground=target_anchors(c,d)
    anchor=p0.get('anchor')
    if anchor is None:
        t=p0.get('track',[])
        anchor=t[min(len(t)-1,round((p['charge']+.17)*FPS))] or next(a for a in t if a)
    row=source_before(d,hit-.045)
    flip=not cinema and row['actor'][0]>body[0]
    if kind=='levin':
        anchor=[anchor[0]+(-11 if flip else 11),anchor[1]+8]
    begin=max(p['charge'],leader-(1.25 if cinema or kind=='levin' else .62))
    stop=leader+.057
    charge=cue(kind+'-charge',begin,anchor,until=stop,rate=1.11/max(.14,stop-begin),
            fadeIn=.15,fadeOut=.11,alpha=.87 if cinema else .78)
    c['fxPlan']=[charge]+[cue(kind+wide+'-'+layer,start,ground,layer=layer,flip=flip,
                           alpha=.87 if layer=='back' else 1) for layer in ['back','front']]
    c.update(fullReplacement=True,actionTime=leader+.115,impactTime=hit+.026,chargeTime=begin+(stop-begin)*.57)
    c['spellPhases'].update(charge=begin,release=leader,arrival=hit,chargeEnd=stop,contact=hit)
    for sound in c['audioCues']:
        if sound['id'].endswith('-charge'):
            sound['at']=begin+.04
        elif sound['id'].endswith('-release'):
            sound['at']=leader
        elif sound['id'].endswith('-resolve'):
            sound['at']=hit
    c['audioCues'].sort(key=lambda x:x['at'])
    revision(c,kind,'斜引雷 · 蓝紫剑电' if kind=='levin' else '细先导 · 冷蓝落雷',
             '剑尖聚起蓝紫电荷，再引一道斜雷到目标脚下。主干、地面分叉和衰减余电来自 Lightning strike，保留原挥剑和结算时刻。'
             if kind=='levin' else '以 Lightning strike 的细先导、冷蓝回击和地面分叉改成实机比例。必杀版用更高主干和更宽落点，原受击与结算时点不变。',
             ['lightning/charge-up','lightning/lightning-strike'])


def revision(c,kind,design,treatment,modules):
    parts=c['subtitle'].split(' · ')
    last=c.get('design',{}).get('name') if c.get('design') else None
    if c.get('revision') in (2,3) and len(parts)>2 and parts[-1] not in ['骑士目标','双路','已确认']:
        if last is not None or c.get('visualRevision') or c.get('fullReplacement'):
            parts=parts[:-1]
    c.update(revision=4,visualRevision=kind,subtitle=' · '.join(parts+[design]),treatment=treatment,
             changeLabel='原库模块 · R4',pixelFxModules=modules)


def apply_action(c):
    root='captures-clean' if c['family']=='cinema' else 'captures'
    folder=HERE/root/c['key']
    d=read_json(folder/'capture.json')
    assert d['contact_calls']==c['source']['contacts']==1 and not d['layout_errors']
    assert d['job']['event']==c['source']['event'] and d['job']['program']==c['source']['program']
    rows=R1.make_timeline(d['frames'],d['duration'])
    compact=R1.compact_layers(d,folder,['current','clean'])
    c.update(contact=d['contact_time'],duration=d['duration'],timeline=[int(r['image']) for r in rows],
             atlases=compact['paths'],layerSpecs=compact['spec'],layerMap=compact['map'],
             atlasFrames=compact['atlasFrames'],atlasCols=compact['atlasCols'])
    c['source']['clean_version']=4
    for k in ('cinemaEffect','cinemaReplacement','cinemaTargets','actorPositions','suppressFlash','fullReplacement'):
        c.pop(k,None)
    if c['key'] in GUARDS:
        assets=actions.guard(c,d,rows)
        revision(c,'guard','回身架枪 · 长枪横扫','借 Scythe reap 的收割式弧线和散雾，重排架枪、转髋横扫与回收。人物、盾牌和完整骑士长枪都用现有素材，近战仍结算一次。',
                 ['melee/scythe-reap'])
    else:
        assets=actions.hero(c,d,rows)
        female='eileen' in c['key']
        revision(c,'spin' if female else 'double','火红回旋斩' if female else '交叉双斩',
                 '艾琳贴地收剑、转身扫过背面，再转回前方。Spin slash 的前后环分层套在实机人物上，色阶改成火焰红。保留原佩剑和一次结算。'
                 if female else '胡纳普压低蓄势，先下劈，再反手向上交叉。用 Double slash 的两道交叉刀光和交点闪芒；只有交叉时触发原必杀结果。',
                 ['melee/spin-slash' if female else 'melee/double-slash'])
    return assets


def build():
    catalog=R3.read_js(PREVIOUS/'catalog.js')
    assets=read_json(OUT/'assets/r4/effects.json')
    catalog['effects'].update(assets['effects'])
    old_count=catalog['audioClips']; tasks=[]; updated={}; styles=Counter()
    for idx,meta in enumerate(catalog['cases']):
        key=meta['key'];kind=FAMILIES.get(meta['move']);action=key in actions.HEROES or key in GUARDS
        if not kind and not action:
            continue
        c=R3.read_case(PREVIOUS,key)
        if action:
            catalog['effects'].update(apply_action(c))
        else:
            d=R3.capture(key)
            assert c['source']['contacts']==d['contact_calls']==1 and c['contact']==d['contact_time']
            if kind=='fire':
                apply_fire(c,d,tasks)
            elif kind=='ragnarok':
                apply_ragnarok(c,d)
            else:
                apply_thunder(c,d,kind)
        R3.write_case(c)
        new=deepcopy(meta)
        new.update({k:c[k] for k in ('revision','visualRevision','subtitle','duration')})
        catalog['cases'][idx]=new
        updated[key]=dict(kind=c['visualRevision'],modules=c['pixelFxModules'],contact=c['contact'],
                          original_result=c['source']['event'],source_program=c['source']['program'])
        if c.get('actionEvidence'):
            updated[key]['action']=c['actionEvidence']
        styles[c['visualRevision']]+=1
    assert styles=={'fire':44,'ragnarok':36,'thunder':44,'levin':72,'double':2,'spin':2,'guard':2},styles
    assert len(tasks)==44
    task_path=HERE/'fire-audio-jobs.json'
    task_path.write_text(json.dumps(tasks,indent=2)+'\n')
    subprocess.run([str(SOUND_PY),'-B',str(HERE/'mix_fire_audio.py'),str(task_path)],check=True)
    tracks=read_json(OUT/'qa/r4-fire-audio.json')
    choices=[
       ('c30ab900b09f','火球','原蓄力 · 新飞行与音轨'),('646005c505bb','诸神黄昏','地面火脉 → 火柱'),
       ('cinema-eileen-thunder','雷电','细先导 · 冷蓝落雷'),
       (next(m['key'] for m in catalog['cases'] if m['move']=='雷剑' and m['profile']=='eileen'),'雷剑','蓝紫斜引雷'),
       ('cinema-hunapu-sword','胡纳普 · 剑必杀','Double slash 交叉双斩'),
       ('cinema-eileen-sword','艾琳 · 剑必杀','Spin slash 火红回旋'),
       ('6b455cb494a1','壁垒卫士','保留枪盾 · 收割式横扫'),
    ]
    def row(label,buttons):
        return dict(label=label,buttons=[dict(case=k,name=n,subtitle='') for k,n in buttons])
    variant_rows=[
        row('火球演出',[('c30ab900b09f','普通'),('cinema-eileen-fire','必杀'),('cinema-eileen-fire-advanced','进阶必杀')]),
        row('雷电演出',[('58d2be8829c0','普通'),('cinema-eileen-thunder','必杀'),('cinema-eileen-thunder-advanced','进阶必杀')]),
        row('胡纳普剑必杀',[('cinema-hunapu-sword','基础'),('cinema-hunapu-sword-advanced','进阶')]),
        row('艾琳剑必杀',[('cinema-eileen-sword','基础'),('cinema-eileen-sword-advanced','进阶')]),
        row('壁垒卫士',[('6b455cb494a1','己方'),('6689f9fcdafc','敌方')]),
    ]
    for entries in [choices,*[[(x['case'],'','') for x in r['buttons']] for r in variant_rows]]:
        assert all(k in updated for k,_,_ in entries),entries
    catalog.update(revision=4,defaultCase=choices[0][0],updatedCases=len(updated),visualUpdates=len(updated),
                   revisionRows=[dict(case=k,name=n,subtitle=sub) for k,n,sub in choices],
                   variantRows=variant_rows,references=assets['references'],fireAudioCases=len(tasks),
                   audioClips=old_count+tracks['unique_cues'])
    for row in catalog['progressionRows']:
        for button in row['buttons']:
            if button['case'] in GUARDS:
                button['subtitle']='长枪横扫'
    R3.write_js(OUT/'catalog.js','window.PIXELFX_CATALOG',catalog)
    (OUT/'qa/r4-provenance.json').write_text(json.dumps({
       'game_project_modified':False,
       'skill':'/Users/gcc/.codex/skills/pixelfx/SKILL.md',
       'workbench_revision':'a84159688af3ca37a4be05a0d422b94451b2e24e',
       'effects':assets['provenance'],'cases':updated,'updated':dict(styles),
       'unchanged_count':len(catalog['cases'])-len(updated),
    },ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(cases=len(catalog['cases']),updates=styles,continuous_fire=len(tasks),tracks=tracks['unique_cues']),ensure_ascii=False))


if __name__=='__main__':
    build()
