#!/usr/bin/env python3
"""Add one visual down-cut to enemy17; scope all writes to its attack review."""
import argparse, contextlib, copy, hashlib, io, json, os, subprocess, tempfile
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from PIL import Image, ImageDraw
import import_bone_guard_v1 as art
import integrate_enemy_11_14_review as shared
import export_gallery as E
import validate_gallery as V

ROOT = art.ROOT
REV = 'bone-guard-double-slash-v2-20261024'
OUT = ROOT / REV
ACTION = 'professions-class-17-enemy-battle--original_class_17_enemy_normal'
PROFILE = 'professions-class-17-enemy-battle'
ARM_POLYGON = [(0,0),(153,0),(153,151),(160,158),(165,164),(165,178),(0,178)]

def write(path, value):
    art.write(path, value)

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def rel(path):
    return path.relative_to(ROOT).as_posix()

def baseline():
    return json.loads((OUT / 'baseline.json').read_text())

def save(image, path, purpose):
    old = art.OUT
    art.OUT = OUT
    try:
        return art.save(image, path, purpose)
    finally:
        art.OUT = old

def prepare():
    b = baseline()
    raw = Image.open(OUT / 'source/descending-arm-master.png').convert('RGBA')
    q = art.quant(raw)
    base = Image.open(art.OUT / 'battle/frame-008.png').convert('RGBA')
    head = art.centroid(q, (649,510,789,602), {art.PALETTE[1]})
    target = art.centroid(base, (155,136,187,158), {art.PALETTE[1]})
    scale = (base.getbbox()[3]-target[1]) / (q.getbbox()[3]-head[1])
    size = [round(s*scale) for s in q.size]
    scaled = q.resize(size, Image.Resampling.NEAREST)
    at = [round(target[0]-head[0]*size[0]/q.width), base.getbbox()[3]-scaled.getbbox()[3]]
    posed = Image.new('RGBA', base.size)
    posed.alpha_composite(scaled, at)
    assert sum(p[3]>0 for p in scaled.getdata()) == sum(p[3]>0 for p in posed.getdata())
    mask = Image.new('L', base.size)
    ImageDraw.Draw(mask).polygon(ARM_POLYGON, fill=255)
    # Keep all existing skull, torso, rear arm and leg pixels outside the
    # foreground-arm silhouette. This is asset compositing, not pose drawing.
    mid = Image.composite(posed, base, mask)
    assets = [save(mid, 'battle/frame-006.png', '追加下劈过渡；仅替换前景持剑臂，身体基准固定')]
    atlas = Image.open(art.OUT / 'battle-atlas.png').convert('RGBA')
    atlas.alpha_composite(mid, (6*384,0))
    assets.append(save(atlas, 'battle-atlas.png', '骸卫对照图集；原未播放的6号新稿槽位用于追加下劈过渡'))
    # Reuse the native sword sweep's exact pixel contour and muted color.
    native = Image.open(art.SRC / 'native-battle-007.png').convert('RGBA')
    sweep = art.parts((x,y) for y in range(64) for x in range(96)
                      if native.getpixel((x,y)) == (228,229,148,255))[0]
    assert len(sweep) == 114
    effects = {}
    for name, test in [('upper',lambda y:y<30),('full',lambda y:True),('lower',lambda y:y>=30)]:
        image = Image.new('RGBA', (96,64))
        for x,y in sweep:
            if test(y): image.putpixel((x,y), (*art.PALETTE[2],255))
        path = 'effects/down-cut-' + name + '.png'
        assets.append(save(image, path, '第二刀刀弧；原作刀弧像素按上→全→下分相'))
        effects['review-c17-down-cut-'+name] = {
            'path':'../../../'+REV+'/'+path, 'frame_size':[96,64], 'frames':1,
            'anchor':[48,64], 'flip_origin_offset':[16,0],
            'source':'bone-guard-complete-v1-20261024/source/native-battle-007.png; exact 114-pixel native sweep component'}
    rows = copy.deepcopy(b['action']['frames'])
    for tick in range(108,113): rows[tick]['frame'] = 6
    for tick in range(113,122): rows[tick]['frame'] = 4
    for tick in range(122,126): rows[tick]['frame'] = 0
    for tick,name in [(112,'upper'),(113,'full'),(114,'lower')]:
        position = [b['action']['origin'][i]+rows[tick]['offset'][i] for i in (0,1)]
        rows[tick]['effects'].append({'sprite':'review-c17-down-cut-'+name,
                                     'position':position,'flip':True,'priority':0})
    timeline = {'schema':1,'revision':REV,'runtime_integrated':False,'effects':effects,
        'actions':{b['action']['key']:{'source_frames_sha256':digest(b['action']['frames']),
            'frames':rows,
            'events':{'visual_slash_count':2,'first_native_sweep_tick':97,
                'additional_down_cut_tick':113,'additional_sweep_ticks':[112,113,114],
                'overhead_hold_until_tick':107,'down_cut_transition_ticks':[108,112],
                'low_followthrough_ticks':[113,121],'guard_recovery_ticks':[122,125],
                'native_retreat_from_tick':126,'source_contact_tick':100,
                'source_damage_settlements':1,'runtime_damage_changed':False,
                'new_art_slot_6_is_review_only':True},
            'note':'普通攻击双刀：保留第一刀上挑，在举剑后的停顿接一刀顺势下劈；上半刀弧→完整刀弧→下半刀弧后低位收势，再回防退回。原作194帧与第101帧结算保留；追加刀为本次指定的动作演出，未接入运行伤害。'}}}
    write(OUT/'enemy-battle-motion.json',timeline)
    mapping = copy.deepcopy(b['mapping'])
    mapping['frame_mapping']['6'] = '../../../'+REV+'/battle/frame-006.png'
    mapping.update(review_timeline='../../../'+REV+'/enemy-battle-motion.json',
                   motion_revision=REV, output_atlas='../../../'+REV+'/battle-atlas.png')
    mapping.setdefault('review_frame_sources',{})['6'] = 8
    mapping.setdefault('review_frame_labels',{})['6'] = '追加下劈 · 新过渡姿势'
    mapping.setdefault('batches',[]).append({'id':'骸卫双刀衔接',
        'review':'../../../'+REV+'/phases-light.png','status':'review_candidate'})
    write(art.BP,mapping)
    write(OUT/'asset-manifest.json',{'revision':REV,'assets':assets,
        'palette':art.HEX,'arm_mask':ARM_POLYGON,'uniform_registration':{
            'raw_head':head,'target_head':target,'scale':scale,'translation':at,
            'clipped_pixels':0},'outside_foreground_arm_unchanged':True,
        'native_sweep_pixels':114,'runtime_integrated':False})
    write(OUT/'action-effect-mapping.json',{'actor_id':'class-17-enemy',
        'card':'普通物理攻击','weapon':'原弯刃','target':'单体',
        'visual_sequence':['原第一刀上挑','追加一刀下劈','回防退回'],
        'visual_slashes':2,'first_native_sweep_tick':97,'additional_down_cut_tick':113,
        'source_contact_tick':100,'source_settlement_count':1,
        'user_requested_extra_slash':True,'runtime_rules_changed':False})

def build():
    shared.MAPS = [art.MP,art.BP]
    module = shared.isolated_builder()
    before = shared.snapshot_shared()
    with contextlib.redirect_stdout(io.StringIO()): data = module.build()
    assert shared.snapshot_shared() == before
    assert len(data['profiles']) == 3 and len(data['actions']) == 14
    write(OUT/'gallery-data.json',data)
    return data

def verify(data):
    b = baseline()
    action = next(a for a in data['actions'] if a['id']==ACTION)
    profile = next(p for p in data['profiles'] if p['id']==PROFILE)
    rows = action['revisedFrames']
    assert action['frames'] == b['action']['frames'] and len(rows)==194
    assert action['contactTick']==100 and action['origin']==b['action']['origin']
    assert action['fps']==b['action']['fps'] and action['duration']==b['action']['duration']
    assert rows[:108] == action['frames'][:108] and rows[126:] == action['frames'][126:]
    assert [rows[t]['frame'] for t in range(108,113)] == [6]*5
    assert [rows[t]['frame'] for t in range(113,122)] == [4]*9
    assert [rows[t]['frame'] for t in range(122,126)] == [0]*4
    for old,new in zip(action['frames'],rows):
        assert {k:v for k,v in old.items() if k not in ['frame','effects']} == {k:v for k,v in new.items() if k not in ['frame','effects']}
    assert [t for t,row in enumerate(rows) if row['effects']] == [112,113,114]
    assert all(a['contentDigest']==b['non_target_action_digests'][a['id']]
               for a in data['actions'] if a['id']!=ACTION)
    for path,sha in b['body_sha256'].items(): assert art.sha(ROOT/path)==sha
    mid = Image.open(OUT/'battle/frame-006.png').convert('RGBA')
    base = Image.open(art.OUT/'battle/frame-008.png').convert('RGBA')
    mask = Image.new('L',base.size);ImageDraw.Draw(mask).polygon(ARM_POLYGON,fill=255)
    assert all(a==b for a,b,m in zip(mid.getdata(),base.getdata(),mask.getdata()) if not m)
    assert {p[3]for p in mid.getdata()} == {0,255}
    assert {p[:3]for p in mid.getdata()if p[3]} <= set(art.PALETTE)
    errors=[];checks=0
    for tick,row in enumerate(rows):
        f=row['frame'];off=row['offset'];flip=not row.get('flip',False)
        at=[action['origin'][i]+off[i]-profile['anchor'][i]for i in(0,1)]
        if flip and f<profile['sourceOamCutoff']:
            at=[at[i]+profile['flipOriginOffset'][i]for i in(0,1)]
        body=V.box_at(V.image(profile['newFrames'][str(f)]),at,profile['sourceFrameSize'],flip)
        boxes=[body]
        for effect in row['effects']:
            meta=data['effects'][effect['sprite']]
            at=[effect['position'][i]-meta['anchor'][i]+(meta['flip_origin_offset'][i]if effect['flip']else 0)for i in(0,1)]
            boxes.append(V.box_at(V.image(meta['path']),at,meta['frame_size'],effect['flip']))
        c=action['closeCamera']
        for box in boxes:
            for mode,view in [('scene',action.get('viewport',data['viewport'])),
                              ('close',[action['origin'][i]+off[i]+c['offset'][i]for i in(0,1)]+c['size'])]:
                checks+=1
                if V.outside(box,view):errors.append({'tick':tick,'mode':mode,'bounds':box})
    assert not data['validation']['structuralIssues'] and action['ready']
    write(OUT/'verification.json',{'passed':not errors,'bounds_checks':checks,
        'source_track_exact':True,'first_slash_and_retreat_unchanged':True,
        'additional_slashes':1,'visual_slash_count':2,'source_contact_tick':100,
        'total_ticks':194,'other_13_actions_unchanged':True,'old_body_files_unchanged':True,
        'skull_torso_rear_arm_legs_pixel_identical_during_new_mid_pose':True,
        'errors':errors,'runtime_integrated':False,'user_acceptance':'pending',
        'inspection':'offline player compositor; no browser access or foreground Godot launch'})
    assert not errors,errors[:3]

def previews(data):
    action=next(a for a in data['actions']if a['id']==ACTION)
    profile=next(p for p in data['profiles']if p['id']==PROFILE)
    stages=[(96,'第一刀蓄势'),(97,'第一刀上挑'),(104,'举剑停顿'),
            (110,'第二刀过渡'),(113,'追加下劈'),(119,'低位收势')]
    for light in [False,True]:
        panels=[E.render_panel(data,profile,action,action['revisedFrames'][tick],True,4,light,True).convert('RGB')for tick,_ in stages]
        w,h=panels[0].size
        board=Image.new('RGB',(3*w,2*(h+42)),(220,222,216)if light else(32,45,53))
        draw=ImageDraw.Draw(board);fg=(23,38,56)if light else(235,243,242)
        for n,((tick,label),panel)in enumerate(zip(stages,panels)):
            x=n%3*w;y=n//3*(h+42);board.paste(panel,(x,y+42))
            text=f'{tick+1} / 194 · '+label;box=draw.textbbox((0,0),text,font=E.font(16))
            assert box[2]-box[0]<w-32
            draw.text((x+w/2,y+21),text,font=E.font(16),fill=fg,anchor='mm')
        save(board,'phases-'+('light'if light else'dark')+'.png','双刀连续姿势、轮廓与深浅背景检查')

def export(data):
    action=next(a for a in data['actions']if a['id']==ACTION);records=[];videos=[]
    for close in [False,True]:
        records.append(E.export(data,action,SimpleNamespace(close=close,scale=4,light=False,stills_only=False)))
        path=ROOT/'demos/videos'/(ACTION+('--close'if close else'')+'.mp4')
        stream=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames,duration','-of','json',str(path)],text=True))['streams'][0]
        assert int(stream['nb_read_frames'])==194
        videos.append({'path':rel(path),'frames':194,'seconds':float(stream['duration'])})
    write(OUT/'export-report.json',{'exports':records,'decoded_videos':videos,
        'scope':'enemy17 ordinary attack only: scene and close, existing unrelated media untouched'})

def merge(data):
    paths=shared.source_paths();before=shared.snapshot_shared()
    live=json.loads(paths[1].read_text());assert shared.parse_js(paths[0])==live
    combined=copy.deepcopy(live)
    for field,key in [('profiles',PROFILE),('actions',ACTION)]:
        replacement=next(row for row in data[field]if row['id']==key)
        assert sum(row['id']==key for row in live[field])==1
        combined[field]=[replacement if row['id']==key else row for row in live[field]]
        assert [r for r in combined[field]if r['id']!=key]==[r for r in live[field]if r['id']!=key]
    neweffects={k:v for k,v in data['effects'].items()if k.startswith('review-c17-down-cut-')}
    assert len(neweffects)==3
    for key,value in neweffects.items():
        assert key not in live['effects']or live['effects'][key]==value
        combined['effects'][key]=value
    assert all(combined['effects'][k]==v for k,v in live['effects'].items())
    combined['builtAt']=datetime.now(timezone.utc).isoformat()
    report=json.loads(paths[2].read_text());report['builtAt']=combined['builtAt']
    target=next(a for a in data['actions']if a['id']==ACTION)
    row={k:target[k]for k in ['id','name','ready','missingFrames','missingEffects','duration']}
    report['actions']=[row if a['id']==ACTION else a for a in report['actions']]
    payload=json.dumps(combined,ensure_ascii=False,separators=(',',':'));staged=[]
    try:
        for path,text in [(paths[0],'window.GALLERY_DATA = '+payload+';\n'),(paths[1],payload+'\n'),(paths[2],json.dumps(report,ensure_ascii=False,indent=2)+'\n')]:
            fd,name=tempfile.mkstemp(prefix='.bone-double-',dir=path.parent);os.close(fd)
            Path(name).write_text(text);staged.append((Path(name),path))
        assert shared.snapshot_shared()==before,'concurrent shared writer; retry latest merge'
        for temp,path in staged:os.replace(temp,path)
    finally:
        for temp,_ in staged:temp.unlink(missing_ok=True)
    assert shared.parse_js(paths[0])==json.loads(paths[1].read_text())==combined
    assert combined['summary']==live['summary'] and shared.sha(paths[3])==before['index.html']
    write(OUT/'merge-report.json',{'target_profiles':1,'target_actions':1,
        'all_unrelated_profiles_and_actions_unchanged':True,'all_existing_effects_unchanged':True,
        'new_effect_definitions':3,'index_default_unchanged':True,'runtime_integrated':False})

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true')
    parser.add_argument('--export',action='store_true');parser.add_argument('--merge',action='store_true');args=parser.parse_args()
    if args.prepare:prepare()
    data=build();verify(data);previews(data)
    if args.export:export(data);data=build()
    if args.merge:merge(data)
    print(json.dumps({'action':ACTION,'visual_slashes':2,'total_ticks':194,
        'source_contact_tick':100,'other_actions_unchanged':True,'exported':args.export,'merged':args.merge}))

if __name__=='__main__':main()
