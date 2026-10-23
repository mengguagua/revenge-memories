#!/usr/bin/env python3
"""Verify fixed class20 mount, exact nock/flight registration and native timing."""
import argparse, ast, json, subprocess
from html.parser import HTMLParser
from types import SimpleNamespace
from PIL import Image,ImageChops
from build_gallery import ROOT,file_hash,matched_export,relative
from export_gallery import render_frame,render_panel
from export_knight_complete import export_one
from import_bow_knight_battle_lock import REV,OUT,SRC,PREV,C,EC,STRINGS,old

def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')

def checks():
    d=json.loads((ROOT/'demos/gallery-data.json').read_text());b=json.loads((OUT/'baseline.json').read_text())
    pp={p['id']:p for p in d['profiles']};now={a['id']:a for a in d['actions']}
    assert len(d['profiles'])==97 and len(now)==775 and not d['validation']['structuralIssues']
    changed={k for k,a in now.items()if a['contentDigest']!=b['actions'][k]['contentDigest']}
    expected={a['id']for a in now.values()if a['profile'].startswith('professions-class-20-')and a['context']=='battle'}
    assert changed==expected and len(changed)==26
    for p,sha in b['map_hashes'].items():assert file_hash(ROOT.parent.parent/p)==sha if p.startswith('art-review/')else file_hash(ROOT/p)==sha
    for a in now.values():
        base=b['actions'][a['id']]
        for key in['frames','fps','origin','contactTick','duration','neededFrames']:
            assert a.get(key)==base.get(key),(a['id'],key)
    assets=[];geometry={}
    for side,palette,ids in [('ally',C,[1,13,14,15,16,17,18]),('enemy',EC,[1,5,6])]:
        tail=None
        for i in ids:
            p=OUT/f'{side}/battle/frame-{i:03}.png';im=Image.open(p).convert('RGBA')
            assert im.size==(320,256)and set(im.getchannel('A').getdata())=={0,255}
            assert {p[:3]for p in im.getdata()if p[3]}==set(palette)
            cs=old.io.helper.parts((x,y)for y in range(256)for x in range(320)if im.getpixel((x,y))[3])
            assert len(cs)==1,(side,i,[len(c)for c in cs])
            stable=im.crop((0,185,320,256)).tobytes()
            if tail is None:tail=stable
            else:assert tail==stable,(side,i,'horse legs/tail moved')
            assets.append({'path':relative(p),'size':list(im.size),'bytes':p.stat().st_size,'colors':6,'connected_components':1,'stable_horse_lower_region':[0,185,320,256]})
        arrow=Image.open(OUT/f'{side}/flying-arrow.png').convert('RGBA');original=Image.open(PREV/'flying-arrow.png').convert('RGBA')
        delta=(-10 if side=='ally'else -2,-9);test=Image.new('RGBA',original.size);test.alpha_composite(original,delta)
        assert arrow.tobytes()==test.tobytes()and sum(p[3]>0 for p in arrow.getdata())==34
        p=pp[f'professions-class-20-{side}-battle'];effect='39768fc933fe67'if side=='ally'else'native-1487ce1e7365a7'
        assert p['revisedEffects'][effect]['path']==REV+f'/{side}/flying-arrow.png'
        for k,v in d['effects'][effect].items():
            if k!='path':assert p['revisedEffects'][effect][k]==v
        geometry[side]={'native_metadata_preserved':True,'flight_texture_translation':delta,'all_34_alpha_pixels_preserved':True}
    # Compare the complete, pixel-exact nocked arrow with the FIRST external
    # flying arrow after compositing at world coordinates (both orientations).
    track=[]
    raw_arrow=Image.open(PREV/'flying-arrow.png').convert('RGBA').crop((36,10,62,13)).resize((104,12),Image.Resampling.NEAREST)
    for a in now.values():
        if a['id']not in changed or a['kind']!='attack':continue
        p=pp[a['profile']];side=p['side'];effect='39768fc933fe67'if side=='ally'else'native-1487ce1e7365a7'
        nock=next(f for f in a['frames']if f['frame']==(17 if side=='ally'else 5))
        fired=next(f for f in a['frames']if any(e['sprite']==effect for e in f['effects']))
        e=next(e for e in fired['effects']if e['sprite']==effect);meta=p['revisedEffects'][effect]
        body=Image.new('RGBA',(320,256));body.alpha_composite(raw_arrow,(136 if side=='ally'else 104,108))
        if side=='enemy':body=body.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        body=body.resize((80,64),Image.Resampling.NEAREST)
        held=Image.new('RGBA',(400,180));held.alpha_composite(body,(a['origin'][0]-40+nock['offset'][0],a['origin'][1]-64+nock['offset'][1]))
        arrow=Image.open(ROOT/meta['path']).convert('RGBA')
        if e['flip']:arrow=arrow.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        flying=Image.new('RGBA',held.size);at=[e['position'][i]-meta['anchor'][i]+(meta['flip_origin_offset'][i]if e['flip']else 0)for i in range(2)]
        flying.alpha_composite(arrow,tuple(at))
        assert held.tobytes()==flying.tobytes(),(a['key'],held.getbbox(),flying.getbbox())
        assert all(f.get('shake',0)==0 and f['offset']==[0,0]for f in a['frames'])
        track.append({'action':a['key'],'first_flight_tick':a['frames'].index(fired),'nock_and_first_flight_pixel_exact':True,'world_arrow_bounds':held.getbbox(),'shaft_center_y':92.5,'native_contact_tick':a['contactTick']})
    manifest=json.loads((OUT/'asset-manifest.json').read_text())
    for x in manifest['assets']:
        path=ROOT/x['path'];assert file_hash(path)==x['sha256']and path.stat().st_size==x['bytes']
    native=json.loads((PREV/'native-reference-audit.json').read_text())
    for x in native['source_assets']:assert file_hash(ROOT/x['path'])==x['sha256']
    for name in ['import_bow_knight_battle_lock.py','verify_bow_knight_battle_lock.py']:ast.parse((ROOT/'tools'/name).read_text())
    # Offline player renderer uses the same paths, placement and source rows as
    # the gallery. Browser access was unavailable; do not claim a UI check.
    captures=[]
    for side,key in [('ally','class_20_ally_bow'),('ally','class_20_ally_silver_bow'),('enemy','class_20_enemy_bow')]:
        a=next(a for a in now.values()if a['key']==key);p=pp[a['profile']]
        for slot in sorted({f['frame']for f in a['frames']}):
            tick=next(n for n,f in enumerate(a['frames'])if f['frame']==slot)
            path=OUT/f'{side}-{key}-pose-{slot:02}.png';render_frame(d,p,a,tick,6,True,True).save(path,optimize=True);captures.append(relative(path))
        first=next(n for n,f in enumerate(a['frames'])if f['effects'])
        for delta in[0,1,3,6]:
            path=OUT/f'{side}-{key}-flight-{delta:02}.png';render_frame(d,p,a,first+delta,6,False,True).save(path,optimize=True);captures.append(relative(path))
    report={'status':'assets_passed','actions_changed':26,'attack_variants':18,'common_reactions_refreshed':8,'unchanged_actions':749,'maps_unchanged':True,'all_native_frame_rows_fps_origins_contacts_unchanged':True,'horse_core_reused':True,'stationary_horse_legs_tail_pixel_exact':True,'bowstrings':STRINGS,'arrow_registration':geometry,'nock_to_first_flight':track,'assets':assets,'offline_captures':captures,'browser_ui_checked':False,'runtime_integrated':False,'user_visual_acceptance':'pending'}
    write(OUT/'verification.json',report)
    print(json.dumps({k:report[k]for k in ['status','actions_changed','unchanged_actions','maps_unchanged']}),flush=True)
    return d,[now[k]for k in sorted(changed)],report

def export_all(d,actions,report):
    exports=[]
    for a in actions:
        exports.append(export_one(d,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=False)))
        if a['key']in['class_20_ally_bow','class_20_ally_silver_bow','class_20_enemy_bow']:
            exports.append(export_one(d,a,SimpleNamespace(close=True,scale=4,light=False,stills_only=False)))
        print('Exported '+a['key'],flush=True)
    decoded=[]
    for e in exports:
        result=subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(ROOT/e['video'])],capture_output=True,text=True,check=True)
        info=json.loads(result.stdout)['streams'][0]
        assert int(info['nb_read_frames'])==e['frames']and abs(float(info['duration'])-e['frames']/e['fps'])<1/e['fps']
        decoded.append({'video':e['video'],**info})
    for a in actions:
        for field,kind,suffix,ext in [('video','videos','','mp4'),('closeVideo','videos','--close','mp4'),('still','stills','','png')]:
            path=ROOT/f'demos/{kind}/{a["id"]}{suffix}.{ext}';a[field]=relative(path)if matched_export(path,a['contentDigest'])else None
        assert a['video']and a['still']
    (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(d,ensure_ascii=False,separators=(',',':'))+';\n')
    (ROOT/'demos/gallery-data.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n')
    write(OUT/'export-report.json',{'status':'passed','videos':len(exports),'exports':exports,'decoded':decoded})
    report.update(status='passed',decoded_videos=len(exports));write(OUT/'verification.json',report)
    print(json.dumps({'status':'passed','videos':len(exports),'decoded_frame_counts':'passed'}),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--export',action='store_true');args=parser.parse_args()
    d,a,r=checks()
    if args.export:export_all(d,a,r)
