#!/usr/bin/env python3
"""Keep the existing arrow layer present throughout nocking and drawing."""
import argparse,copy,hashlib,json,subprocess
from types import SimpleNamespace
from PIL import Image,ImageChops,ImageDraw
from build_gallery import ROOT,build,file_hash,matched_export,relative
from export_gallery import render_frame,render_panel,font
from export_knight_complete import export_one
from import_bow_knight_battle_lock import C,EC
import import_sniper_complete as io

REV='bow-knight-arrow-continuity-v3-20261023'
OUT=ROOT/REV
PREV=ROOT/'bow-knight-battle-lock-string-v2-20261023'
ALIASES={'ally':{19:16,20:18},'enemy':{7:1,8:6}}

def write(p,v):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')

def prepare():
    OUT.mkdir(parents=True,exist_ok=True)
    path=OUT/'baseline.json'
    if not path.exists():
        data=json.loads((ROOT/'demos/gallery-data.json').read_text())
        write(path,{'actions':data['actions'],'mappings':{s:json.loads((ROOT/f'professions/class-20-{s}/battle/frame_mapping.json').read_text())for s in['ally','enemy']}})
    baseline=json.loads(path.read_text());io.OUT=OUT
    arrow=Image.open(ROOT/'bow-knight-complete-v1-20261023/flying-arrow.png').convert('RGBA').crop((36,10,62,13)).resize((104,12),Image.Resampling.NEAREST)
    assets=[];timings=[]
    for side,aliases in ALIASES.items():
        mapping=copy.deepcopy(baseline['mappings'][side]);timeline={'actions':{}}
        faction_arrow=arrow.copy()
        if side=='enemy':
            table=dict(zip(C,EC));faction_arrow.putdata([(*table[p[:3]],p[3])if p[3]else(0,0,0,0)for p in arrow.getdata()])
        overlay=Image.new('RGBA',(320,256));overlay.alpha_composite(faction_arrow,(136 if side=='ally'else 104,108))
        overlay_path=io.save(overlay,f'source/{side}-nocked-arrow-layer.png','reuse the existing full-draw arrow, same palette and exact registered shooting height')
        for slot,source_slot in aliases.items():
            source=Image.open(PREV/f'{side}/battle/frame-{source_slot:03}.png').convert('RGBA');im=source.copy();im.alpha_composite(overlay)
            output=io.save(im,f'{side}/frame-{slot:03}.png','existing ready/release pose with the persistent nocked arrow layer')
            mapping['frame_mapping'][str(slot)]=output
            mapping.setdefault('review_frame_sources',{})[str(slot)]=source_slot
            mapping['records'].append({'source_frame':slot,'review_source_frame':source_slot,'path':output,'size':[320,256],'bytes':io.ASSETS[-1]['bytes'],'sha256':io.ASSETS[-1]['sha256']})
            assert im.crop((0,139,320,256)).tobytes()==source.crop((0,139,320,256)).tobytes()
            restored=source.copy();restored.alpha_composite(overlay);assert im.tobytes()==restored.tobytes()
            assets.append(io.ASSETS[-1])
        for action in baseline['actions']:
            if action['profile']!=f'professions-class-20-{side}-battle'or action['kind']!='attack':continue
            key='39768fc933fe67'if side=='ally'else'native-1487ce1e7365a7'
            rows=copy.deepcopy(action['frames']);fire=next(i for i,row in enumerate(rows)if any(e['sprite']==key for e in row['effects']))
            initial_ready=16 if side=='ally'else 1;release=18 if side=='ally'else 6
            for tick,row in enumerate(rows):
                if tick>=fire:continue
                if row['frame']==initial_ready:row['frame']=19 if side=='ally'else 7
                elif row['frame']==release:row['frame']=20 if side=='ally'else 8
            timeline['actions'][action['key']]={'source_frames_sha256':hashlib.sha256(json.dumps(action['frames'],sort_keys=True,separators=(',',':')).encode()).hexdigest(),'frames':rows,'note':'搭箭至离弦连续保留同一支箭，发射帧交接给原外置飞行箭；区分拉弓与射后收弓的同一身体姿势。原作动作姿态、时长、效果坐标和结算保持。'}
            timings.append({'key':action['key'],'first_flight_tick':fire,'ready_with_arrow_ticks':[i for i,row in enumerate(rows)if row['frame']in aliases],'source_frame_count':len(rows)})
        target=OUT/f'{side}-review-timeline.json';write(target,timeline)
        mapping['review_frame_labels']=({'16':'射后收弓 · 源姿势16','19':'拉弓搭箭 · 源姿势16','18':'箭已离弦 · 源姿势18','20':'离弦前 · 源姿势18'}if side=='ally'else{'1':'空弓／收弓 · 源姿势1','7':'搭箭待发 · 源姿势1','6':'箭已离弦 · 源姿势6','8':'离弦前 · 源姿势6'})
        mapping.update(revision=REV,review_timeline='../../../'+relative(target),review_note='搭箭／拉弓中间补箭：待发姿势保留箭，原飞行帧起才交接；射后收弓仍用空弓。已确认的马匹、弓弦、配色和箭轨均保持。',
            batches=[{'id':'搭箭连续性','review':'../../../'+REV+f'/{side}-continuity-dark.png','status':'review_candidate'},{'id':'原身体姿势（含收弓）','review':'../../../bow-knight-battle-lock-string-v2-20261023/'+side+'-battle-light.png','status':'review_candidate'}])
        write(ROOT/f'professions/class-20-{side}/battle/frame_mapping.json',mapping)
    write(OUT/'asset-manifest.json',{'revision':REV,'assets':io.ASSETS,'method':'existing generated assets and existing arrow texture composited by the editable sprite pipeline; no character repaint','runtime_integrated':False})
    write(OUT/'continuity-plan.json',{'actions':timings,'review_frame_sources':ALIASES})
    # Preserve the existing title-safe renderer for this new revision.
    path=ROOT/'tools/export_gallery.py';s=path.read_text();s=s.replace("in ['bow-knight-battle-lock-string-v2-20261023'","in ['"+REV+"','bow-knight-battle-lock-string-v2-20261023'");path.write_text(s)
    return build()

def verify_and_capture(data):
    baseline=json.loads((OUT/'baseline.json').read_text());oldactions={a['id']:a for a in baseline['actions']};pp={p['id']:p for p in data['profiles']};changed=[];checks=[]
    for a in data['actions']:
        old=oldactions[a['id']]
        if a['contentDigest']!=old['contentDigest']:changed.append(a)
        for k in['frames','fps','origin','contactTick','duration']:assert a.get(k)==old.get(k),(a['id'],k)
    assert len(changed)==18 and all(a['kind']=='attack'and a['profile'].startswith('professions-class-20-')for a in changed)
    for a in changed:
        p=pp[a['profile']];side=p['side'];rows=a['revisedFrames'];key='39768fc933fe67'if side=='ally'else'native-1487ce1e7365a7'
        fire=next(i for i,f in enumerate(rows)if any(e['sprite']==key for e in f['effects']))
        for tick,(source,row)in enumerate(zip(a['frames'],rows)):
            assert {k:v for k,v in row.items()if k!='frame'}=={k:v for k,v in source.items()if k!='frame'}
            if tick>=fire:assert row==source
        # Every pre-flight ready and release row now selects the arrow-bearing
        # image, while the post-shot reused pose selects its original image.
        ready=16 if side=='ally'else 1;release=18 if side=='ally'else 6
        for tick,source in enumerate(a['frames']):
            if tick<fire and source['frame']in[ready,release]:assert rows[tick]['frame']in ALIASES[side]
        checks.append({'key':a['key'],'first_flight_tick':fire,'ready_and_release_arrow_gaps':0,'post_shot_rows_unchanged':True,'native_timing_effects_and_contact_unchanged':True})
    # Full-size offline player frames and compact phase boards for acceptance.
    for side,key in [('ally','class_20_ally_bow'),('ally','class_20_ally_silver_bow'),('enemy','class_20_enemy_bow')]:
        a=next(a for a in changed if a['key']==key);p=pp[a['profile']];rows=a['revisedFrames'];fire=next(c['first_flight_tick']for c in checks if c['key']==key)
        ticks=([66,68,120,121,173,174,fire-1,fire]if side=='ally'else[0,41,42,92,93,fire-1,fire,fire+1])
        sheet=Image.new('RGB',(1280,680),(32,45,53));draw=ImageDraw.Draw(sheet)
        for n,tick in enumerate(ticks):
            close_action={**a,'viewport':[a['origin'][0]-40,a['origin'][1]-64,80,64]}
            frame=render_panel(data,p,close_action,rows[tick],True,4,False,False);x=n%4*320;y=n//4*340;sheet.paste(frame,(x,y),frame)
            draw.text((x+160,y+275),f'第{tick+1}帧 · 源姿势{a["frames"][tick]["frame"]}',font=font(16),anchor='mm',fill=(233,240,240))
            if n in[0,1,3,5,6,7]:render_frame(data,p,a,tick,6,False,True).save(OUT/f'{side}-{key}-tick-{tick:03}.png',optimize=True)
        sheet.save(OUT/(f'{side}-'+('silver-'if 'silver'in key else'')+'continuity-dark.png'),optimize=True)
    write(OUT/'verification.json',{'status':'passed','attack_variants':18,'unrelated_actions_unchanged':757,'continuity':checks,'runtime_integrated':False,'browser_ui_checked':False,'visual_acceptance':'pending'})
    print(json.dumps({'attack_variants':18,'unchanged_actions':757,'continuous_until_external_flight':True}),flush=True)
    return changed

def export_all(data,actions):
    exports=[]
    for a in actions:
        exports.append(export_one(data,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=False)))
        if a['key']in['class_20_ally_bow','class_20_ally_silver_bow','class_20_enemy_bow']:exports.append(export_one(data,a,SimpleNamespace(close=True,scale=4,light=False,stills_only=False)))
        print('Exported '+a['key'],flush=True)
    for e in exports:
        result=subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames,duration','-of','json',str(ROOT/e['video'])],capture_output=True,text=True,check=True)
        stream=json.loads(result.stdout)['streams'][0];assert int(stream['nb_read_frames'])==e['frames']and abs(float(stream['duration'])-e['frames']/e['fps'])<1/e['fps']
    for a in actions:
        for field,kind,suffix,ext in [('video','videos','','mp4'),('closeVideo','videos','--close','mp4'),('still','stills','','png')]:
            p=ROOT/f'demos/{kind}/{a["id"]}{suffix}.{ext}';a[field]=relative(p)if matched_export(p,a['contentDigest'])else None
    (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n')
    (ROOT/'demos/gallery-data.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
    write(OUT/'export-report.json',{'status':'passed','videos':len(exports),'decoded_frame_counts_and_durations':'passed','exports':exports})
    print(json.dumps({'videos':len(exports),'status':'passed'}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--export',action='store_true');a=p.parse_args()
    d=prepare();changed=verify_and_capture(d)
    if a.export:export_all(d,changed)
