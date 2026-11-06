#!/usr/bin/env python3
"""One contact spark burst for enemy18 review; actor and gameplay unchanged."""
import argparse,copy,hashlib,json,math,os,subprocess,tempfile
from datetime import datetime,timezone
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace
from PIL import Image,ImageDraw
import import_cleft_eye_v1 as art
import integrate_cleft_eye_v1 as scoped
import integrate_enemy_11_14_review as shared
import export_gallery as E
import validate_gallery as V

ROOT=art.ROOT;REV='cleft-eye-impact-vfx-v2-20261024';OUT=ROOT/REV
ACTION='professions-class-18-enemy-battle--original_class_18_enemy_normal'
FX_PREFIX='review-c18-impact-spark-';COUNTS=[2,3,3,4,4,3];PIVOT=[159,104]
COLORS=[tuple(bytes.fromhex(h))for h in['515d91','738cbb','9391c2','bac4df']]
def write(p,d):art.write(p,d)
def rel(p):return p.relative_to(ROOT).as_posix()
def digest(d):return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def baseline():return json.loads((OUT/'baseline.json').read_text())
def save(im,path,purpose):
    old=art.OUT;art.OUT=OUT
    try:return art.save(im,path,purpose)
    finally:art.OUT=old
@lru_cache(maxsize=None)
def color(rgb):return min(COLORS,key=lambda c:sum((a-b)**2 for a,b in zip(c,rgb)))

def prepare():
    b=baseline();raw=Image.open(OUT/'source/impact-master.png').convert('RGBA')
    pivots=[[280,310],[256,310],[248,306],[273,258],[256,258],[256,262]]
    assets=[];effects={}
    for slot,pivot in enumerate(pivots):
        x=slot%3*512;y=slot//3*512;cell=raw.crop((x,y,x+512,y+512));q=Image.new('RGBA',cell.size)
        q.putdata([(*color(p[:3]),255)if p[3]>=200 else(0,0,0,0)for p in cell.getdata()])
        small=q.resize((128,128),Image.Resampling.NEAREST);at=[round(48-n/4)for n in pivot]
        out=Image.new('RGBA',(96,96));out.alpha_composite(small,at)
        assert sum(p[3]>0 for p in small.getdata())==sum(p[3]>0 for p in out.getdata())
        path=f'effects/impact-{slot:02}.png';assets.append(save(out,path,'蓝紫撞击火花：接触、爆开、散落、消退'))
        effects[FX_PREFIX+str(slot)]={'path':'../../../'+REV+'/'+path,'frame_size':[24,24],
            'frames':1,'anchor':[12,12],'flip_origin_offset':[0,0],
            'source':'built-in image_gen authored six-phase impact sheet; fixed center and uniform quarter scale'}
    action=b['action'];rows=copy.deepcopy(action['frames']);start=action['contactTick'];tick=start
    for slot,count in enumerate(COUNTS):
        for _ in range(count):
            rows[tick]['effects'].append({'sprite':FX_PREFIX+str(slot),'position':PIVOT,'flip':False,'priority':0});tick+=1
    # Preserve the prior close-up origin; extend its right side only to keep
    # the stationary contact point visible as the actor retreats to its origin.
    camera=copy.deepcopy(action['closeCamera']);right=camera['offset'][0]+camera['size'][0]
    for row in rows:
        for e in row['effects']:
            m=effects[e['sprite']];im=Image.open((art.BP.parent/m['path']).resolve()).convert('RGBA');box=im.getbbox()
            edge=e['position'][0]-m['anchor'][0]+box[2]*m['frame_size'][0]/im.width-action['origin'][0]-row['offset'][0]
            right=max(right,edge+12)
    camera['size'][0]=math.ceil((right-camera['offset'][0])/8)*8
    camera.update(effectBoundsIncluded=True,preserves_original_camera_origin=True)
    timeline={'schema':1,'revision':REV,'runtime_integrated':False,'effects':effects,'actions':{
        action['key']:{'source_frames_sha256':digest(action['frames']),'frames':rows,'close_camera':camera,
            'events':{'spark_burst_count':1,'start_tick':start,'last_spark_tick':tick-1,
                'phase_ticks':COUNTS,'world_contact_point':PIVOT,'actor_rows_unchanged':True,
                'source_contact_tick':start,'source_damage_settlements':1,'new_hits':0},
            'note':'普通撞击：原第84帧结算时在碰撞点爆出一簇蓝紫火花，随后散开并消退，约0.32秒。火花位置固定，裂目兽按原动作退回；保留240帧、原环视、摆尾、一次撞击与一次结算。'}}}
    write(OUT/'enemy-battle-motion.json',timeline)
    mapping=json.loads(art.BP.read_text());mapping.update(review_timeline='../../../'+REV+'/enemy-battle-motion.json',effect_revision=REV);write(art.BP,mapping)
    write(OUT/'asset-manifest.json',{'revision':REV,'assets':assets,'palette':['#'+bytes(c).hex()for c in COLORS],
        'source_cells':[512,512],'source_impact_pivots':pivots,'uniform_scale':.25,
        'logical_frame_size':[24,24],'clipped_pixels':0,'actor_art_unchanged':True,'runtime_integrated':False})
    write(OUT/'action-effect-mapping.json',{'actor_id':'class-18-enemy','card':'普通单体物理攻击',
        'visual':'一次前冲撞击后的蓝紫火花','effect_contact_tick':83,'spark_active_ticks':[83,101],
        'burst_count':1,'damage_settlement_count':1,'new_damage_events':0,'runtime_rules_changed':False})

def build():
    old=scoped.OUT;scoped.OUT=OUT
    try:return scoped.build()
    finally:scoped.OUT=old

def verify(data):
    b=baseline();action=next(a for a in data['actions']if a['id']==ACTION);rows=action['revisedFrames'];errors=[];checks=0
    for field in ['frames','origin','fps','duration','contactTick']:
        assert action[field]==b['action'][field],field
    assert len(rows)==240 and action['contactTick']==83 and not action.get('reviewTailFrames')
    active=[]
    for tick,row in enumerate(rows):
        assert {k:v for k,v in row.items()if k!='effects'}=={k:v for k,v in action['frames'][tick].items()if k!='effects'}
        assert len(row['effects'])==(1 if 83<=tick<=101 else 0)
        for e in row['effects']:
            assert e['position']==PIVOT and not e['flip'];active.append(tick);m=data['effects'][e['sprite']]
            at=[e['position'][i]-m['anchor'][i]for i in(0,1)];box=V.box_at(V.image(m['path']),at,m['frame_size'],False)
            camera=action['closeCamera'];off=row['offset']
            for mode,view in [('scene',action.get('viewport',data['viewport'])),('close',[action['origin'][i]+off[i]+camera['offset'][i]for i in(0,1)]+camera['size'])]:
                checks+=1
                if V.outside(box,view):errors.append({'tick':tick,'mode':mode,'box':box})
    assert active==list(range(83,102)) and action['ready'] and not data['validation']['structuralIssues']
    assert all(a['contentDigest']==b['other_actions'][a['id']]for a in data['actions']if a['id']!=ACTION)
    for path,sha in b['body_files'].items():assert art.sha(ROOT/path)==sha
    assert next(p for p in data['profiles']if p['id']==action['profile'])==b['profile']
    for path in (OUT/'effects').glob('*.png'):
        im=Image.open(path).convert('RGBA');assert im.size==(96,96)and im.getbbox()
        assert {p[3]for p in im.getdata()}=={0,255}and {p[:3]for p in im.getdata()if p[3]}<=set(COLORS)
    write(OUT/'verification.json',{'passed':not errors,'effect_bounds_checks':checks,'actor_rows_exact':True,
        'body_and_map_assets_unchanged':True,'other_13_actions_unchanged':True,'profiles_unchanged':True,
        'total_ticks':240,'contact_tick':83,'spark_active_ticks':[83,101],'spark_bursts':1,
        'spark_position_fixed_in_world':PIVOT,'source_settlements':1,'errors':errors,'runtime_integrated':False})
    assert not errors,errors[:3]

def previews(data):
    action=next(a for a in data['actions']if a['id']==ACTION);p=next(p for p in data['profiles']if p['id']==action['profile'])
    ticks=[82,83,86,89,94,101]
    # A constant world crop shows the contact sparks remaining at the collision
    # location while the orb returns, instead of following the character camera.
    stillaction=copy.deepcopy(action);stillaction['viewport']=[40,76,152,60]
    for light in [False,True]:
        panels=[E.render_panel(data,p,stillaction,action['revisedFrames'][t],True,3,light,False).convert('RGB')for t in ticks]
        w,h=panels[0].size;bg=(220,222,216)if light else(32,45,53);fg=(23,38,56)if light else(235,243,242)
        board=Image.new('RGB',(3*w,2*(h+44)),bg);draw=ImageDraw.Draw(board)
        for n,(t,panel)in enumerate(zip(ticks,panels)):
            x=n%3*w;y=n//3*(h+44);board.paste(panel,(x,y+44))
            label='撞击'if t==82 else'接触火花'if t==83 else'火花爆开'if t==86 else'散落'if t in[89,94]else'消退'
            text=f'{t+1} / 240 · '+label;assert draw.textbbox((0,0),text,font=E.font(16))[2]<w-32
            draw.text((x+w/2,y+22),text,anchor='mm',font=E.font(16),fill=fg)
        save(board,'phases-'+('light'if light else'dark')+'.png','撞击火花深浅背景与固定碰撞点检查')

def export(data):
    action=next(a for a in data['actions']if a['id']==ACTION);records=[];videos=[]
    for close in [False,True]:
        records.append(E.export(data,action,SimpleNamespace(close=close,scale=4,light=False,stills_only=False)))
        path=ROOT/'demos/videos'/(ACTION+('--close'if close else'')+'.mp4')
        stream=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames,duration','-of','json',str(path)],text=True))['streams'][0]
        assert int(stream['nb_read_frames'])==240
        videos.append({'path':rel(path),'frames':240,'duration':float(stream['duration'])})
    write(OUT/'export-report.json',{'exports':records,'decoded_videos':videos,'scope':'only enemy18 ordinary attack, scene and close'})

def merge(data):
    files=shared.source_paths();before=shared.snapshot_shared();live=json.loads(files[1].read_text());assert shared.parse_js(files[0])==live
    combined=copy.deepcopy(live);new=next(a for a in data['actions']if a['id']==ACTION)
    combined['actions']=[new if a['id']==ACTION else a for a in live['actions']]
    assert [a for a in combined['actions']if a['id']!=ACTION]==[a for a in live['actions']if a['id']!=ACTION]
    effects={k:v for k,v in data['effects'].items()if k.startswith(FX_PREFIX)};assert len(effects)==6
    for key,value in effects.items():
        assert key not in live['effects']or live['effects'][key]==value;combined['effects'][key]=value
    assert all(combined['effects'][key]==value for key,value in live['effects'].items())
    combined['builtAt']=datetime.now(timezone.utc).isoformat();report=json.loads(files[2].read_text());report['builtAt']=combined['builtAt']
    row={k:new[k]for k in ['id','name','ready','missingFrames','missingEffects','duration']}
    report['actions']=[row if a['id']==ACTION else a for a in report['actions']]
    payload=json.dumps(combined,ensure_ascii=False,separators=(',',':'));staged=[]
    try:
        for path,text in [(files[0],'window.GALLERY_DATA = '+payload+';\n'),(files[1],payload+'\n'),(files[2],json.dumps(report,ensure_ascii=False,indent=2)+'\n')]:
            fd,name=tempfile.mkstemp(prefix='.eye-impact-',dir=path.parent);os.close(fd);Path(name).write_text(text);staged.append((Path(name),path))
        assert shared.snapshot_shared()==before,'concurrent shared writer; retry latest merge'
        for temp,path in staged:os.replace(temp,path)
    finally:
        for temp,_ in staged:temp.unlink(missing_ok=True)
    assert shared.parse_js(files[0])==json.loads(files[1].read_text())==combined
    assert combined['profiles']==live['profiles']and combined['summary']==live['summary']and shared.sha(files[3])==before['index.html']
    write(OUT/'merge-report.json',{'target_actions':1,'all_other_actions_and_profiles_unchanged':True,
        'all_previous_effects_unchanged':True,'new_effect_definitions':6,'index_default_preserved':True,'runtime_integrated':False})

def main():
    p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');p.add_argument('--export',action='store_true');p.add_argument('--merge',action='store_true');args=p.parse_args()
    if args.prepare:prepare()
    data=build();verify(data);previews(data)
    if args.export:export(data);data=build()
    if args.merge:merge(data)
    print(json.dumps({'action':ACTION,'spark_bursts':1,'spark_ticks':19,'contact_tick':83,'actor_and_other_actions_unchanged':True,'exported':args.export,'merged':args.merge}))

if __name__=='__main__':main()
