#!/usr/bin/env python3
"""Check shared spell materials, native actor timing, and targeted previews."""
import ast,copy,json,subprocess
from types import SimpleNamespace
from PIL import Image
from build_gallery import ROOT,file_hash,relative,matched_export
from export_gallery import render_frame
from export_knight_complete import export_one
from share_sage_mage_spells import REV,OUT,COMMON,sha,item,write

def verify(export=False):
    b=json.loads((OUT/'baseline.json').read_text());data=json.loads((ROOT/'demos/gallery-data.json').read_text());now={a['id']:a for a in data['actions']};before=b['action_facts'];pp={p['id']:p for p in data['profiles']};contracts=json.loads((OUT/'spell-contracts.json').read_text())['contracts'];ledger={c['sage_action']:c for c in contracts};changed={k for k,a in now.items() if a['contentDigest']!=before[k]['digest']}
    assert len(now)==len(before)==872 and len(pp)==100 and len(ledger)==54 and changed==set(ledger)
    assert all(a['ready'] for a in now.values()) and not data['validation']['structuralIssues']
    for k,a in now.items():
        old=before[k];assert sha(a['frames'])==old['frames_sha256'] and a['fps']==old['fps'] and a['origin']==old['origin'] and a['contactTick']==old['contact'] and a['duration']==old['duration'],(k,'native schedule changed')
    assert file_hash(ROOT/b['mage_mapping_path'])==b['mage_mapping_sha256']
    assert file_hash(ROOT/b['mage_timeline_path'])==b['mage_timeline_sha256']
    assert file_hash(ROOT/'professions/class-19-ally/maps/frame_mapping.json')==b['sage_maps_sha256']
    for path,digest in b['body_assets'].items():assert file_hash(ROOT/path)==digest
    shared=json.loads((OUT/'shared-assets.json').read_text())
    for row in shared['shared_existing_assets']:
        assert data['effects'][row['effect_id']]==row['metadata'] and file_hash(ROOT/row['metadata']['path'])==row['sha256']
    checks=[]
    for key,c in ledger.items():
        a=now[key];mage=now[c['mage_action']];revised=a['revisedFrames'];assert len(revised)==len(a['frames']) and not a.get('reviewTailFrames')
        assert all({k:v for k,v in row.items() if k!='effects'}=={k:v for k,v in old.items() if k!='effects'} for row,old in zip(revised,a['frames']))
        if c['spell_id']==28:
            replace=c['replacement_effects'];native_max=0;new_max=0
            for old,row in zip(a['frames'],revised):
                expected=copy.deepcopy(old['effects']);extras=[];count=0
                for e in expected:
                    if e['sprite'] not in replace:continue
                    e['sprite']=replace[e['sprite']];count+=1
                    if c['spell_id']==28:
                        ex=copy.deepcopy(e);ex['position']=[e['position'][i]+c['additional_lane_offset'][i] for i in range(2)];extras.append(ex)
                expected.extend(extras);assert row['effects']==expected
                native_max=max(native_max,count);new_max=max(new_max,sum(e['sprite'] in replace.values() for e in row['effects']))
            if c['spell_id']==28:assert native_max==3 and new_max==6
        else:
            template=mage.get('revisedFrames',mage['frames'])+mage.get('reviewTailFrames',[])
            for row,n in zip(revised,c['source_tick_by_sage_frame']):
                expected=[] if n is None else copy.deepcopy(template[n]['effects'] if n<len(template) else template[-1]['effects'] if c['spell_id']==32 else [])
                for e in expected:e['position']=[e['position'][i]+c['origin_delta'][i] for i in range(2)]
                assert row['effects']==expected
            assert c['source_tick_by_sage_frame'][a['contactTick']]==mage['contactTick']
            assert all(c['source_tick_by_sage_frame'][v['sage_tick']]==v['mage_tick'] for v in c['anchors'])
        assert {e['sprite'] for row in revised for e in row['effects']}<=set(mage['effectIds'])
        checks.append({'spell':c['spell_id'],'action':key,'source_mage_action':c['mage_action'],'contact':a['contactTick'],'native_body_rows_exact':True,'same_existing_effect_assets':True,'mode':c['mode']})
    for n in ['share_sage_mage_spells.py','verify_sage_shared_spells.py']:ast.parse((ROOT/'tools'/n).read_text())
    report={'status':'assets_passed','revision':REV,'common_spell_ids':COMMON,'updated_variants':54,'unrelated_actions_unchanged':818,'all_native_frames_fps_origins_contacts_duration_unchanged':True,'mage_mapping_timeline_and_shared_images_unchanged':True,'all_22_sage_body_and_ruby_staff_assets_unchanged':True,'map_art_and_mapping_unchanged':True,'native_sage_actor_rows_exact':True,'arrow_rain_max_visible_arrows':6,'shared_existing_effect_assets':len(shared['shared_existing_assets']),'new_art_assets':0,'checks':checks,'browser_ui_checked':False,'runtime_integrated':False,'user_visual_acceptance':'pending'}
    write(OUT/'verification.json',report);print(json.dumps({'status':'assets_passed','shared_spells':9,'variants':54,'unchanged':818,'arrow_rain_arrows':6}),flush=True)
    if not export:return
    exports=[];captures=[]
    selected=[now[k] for k in ledger if not any(w in now[k]['key'] for w in ['far_','vs_heavy'])]
    selected.append(next(now[k] for k in ledger if now[k]['key']=='class_19_ally_item_28_far_ally_vs_heavy'))
    for a in selected:
        p=pp[a['profile']];exports.append(export_one(data,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=False)))
        if a['key'] in ['class_19_ally_item_27','class_19_ally_item_28','class_19_ally_item_32']:exports.append(export_one(data,a,SimpleNamespace(close=True,scale=4,light=False,stills_only=False)))
        ticks={a['contactTick']}
        if item(a['key'])==28:
            rows=a['revisedFrames'];ticks.add(next(i for i,f in enumerate(rows) if sum('review-arrow-rain' in e['sprite'] for e in f['effects'])==6));ticks.add(min(a['contactTick']-20,len(rows)-1))
        else:
            c=ledger[a['id']]
            if c.get('anchors'):ticks.update(v['sage_tick'] for v in c['anchors'])
            else:ticks.add(next(i for i,f in enumerate(a['revisedFrames']) if f['effects']))
            if item(a['key']) in [29,31,32]:ticks.add(min(len(a['frames'])-1,a['contactTick']+35))
        for tick in sorted(ticks):
            for light in [False,True]:
                path=OUT/f'{a["key"]}-{tick:03}-{"light" if light else "dark"}.png';render_frame(data,p,a,tick,4,light,False).save(path,optimize=True);captures.append(relative(path))
        print('Exported '+a['key'],flush=True)
    decoded=[]
    for e in exports:
        info=json.loads(subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(ROOT/e['video'])],capture_output=True,text=True,check=True).stdout)['streams'][0]
        assert int(info['nb_read_frames'])==e['frames'] and abs(float(info['duration'])-e['expected_duration'])<1/e['fps'];decoded.append({'path':e['video'],**info})
    for a in [now[k] for k in ledger]:
        for field,kind,suffix,ext in [('video','videos','','mp4'),('closeVideo','videos','--close','mp4'),('still','stills','','png')]:
            path=ROOT/f'demos/{kind}/{a["id"]}{suffix}.{ext}';a[field]=relative(path) if matched_export(path,a['contentDigest']) else None
    (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n');(ROOT/'demos/gallery-data.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
    report.update(status='passed',decoded_videos=len(decoded),offline_captures=captures);write(OUT/'verification.json',report);write(OUT/'export-report.json',{'status':'passed','exports':exports,'decoded_video_checks':decoded});print(json.dumps({'status':'passed','variants':54,'unchanged':818,'videos':len(decoded)}),flush=True)
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--export',action='store_true');verify(p.parse_args().export)
