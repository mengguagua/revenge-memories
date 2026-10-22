#!/usr/bin/env python3
"""Targeted pose continuity, preserved native schedules and preview checks."""
import json, subprocess
from types import SimpleNamespace
from PIL import Image
from build_gallery import ROOT, matched_export, relative, file_hash
from export_gallery import render_frame
from export_knight_complete import export_one
from import_sniper_complete import C, EC, helper
from revise_sniper_down_left import OUT, REV

def main():
    baseline=json.loads((OUT/'baseline.json').read_text());data=json.loads((ROOT/'demos/gallery-data.json').read_text())
    wanted={f'professions-class-13-{side}-maps-tactical-walk--{key}'for side in ['ally','enemy']for key in ['walk-down','idle-down','walk-left','idle-left']}
    changed=[a for a in data['actions']if a['contentDigest']!=baseline['actions'][a['id']]['contentDigest']]
    assert {a['id']for a in changed}==wanted
    assert len(data['actions'])==len(baseline['actions'])==731
    assert not data['validation']['structuralIssues']
    frames={};checks=[]
    for side,palette in [('ally',C),('enemy',EC)]:
        m=json.loads((ROOT/f'professions/class-13-{side}/maps/frame_mapping.json').read_text());old=baseline['mappings'][side]
        assert next(s for s in m['scenarios']if s['id']=='tactical-idle')==next(s for s in old['scenarios']if s['id']=='tactical-idle')
        scene=next(s for s in m['scenarios']if s['id']=='tactical-walk');os=next(s for s in old['scenarios']if s['id']=='tactical-walk')
        for i in range(4):assert scene['frame_mapping'][i]==os['frame_mapping'][i]
        for i in [4,5,6,7]:
            path=OUT/f'{side}/tactical-walk/frame-{i:03}.png';im=Image.open(path).convert('RGBA');frames[side,i]=im
            assert im.size==(128,96)and set(im.getchannel('A').getdata())=={0,255}
            assert {p[:3]for p in im.getdata()if p[3]}==set(palette)
            cc=helper.parts((x,y)for y in range(96)for x in range(128)if im.getpixel((x,y))[3]);assert len(cc)==1
            box=im.getbbox();assert 0<box[0]<box[2]<128 and 0<box[1]<box[3]<96
            assert path.stat().st_size<50000
            checks.append({'path':relative(path),'size':[128,96],'bytes':path.stat().st_size,'colors':5,'connected_components':1,'bounds':box})
        a,b=frames[side,4],frames[side,5]
        assert a.crop((0,0,128,69)).tobytes()==b.crop((0,0,128,69)).tobytes()
        for i,sign in [(4,1),(5,-1)]:
            pts=[x for y in range(91,94)for x in range(128)if frames[side,i].getpixel((x,y))[3]]
            assert pts and (sum(pts)/len(pts)-64)*sign>0,('wrong down support foot',side,i)
        a,b=frames[side,6],frames[side,7]
        for box in [(52,37,73,60),(64,60,68,66),(62,66,70,69)]:
            assert a.crop(box).tobytes()==b.crop(box).tobytes(),('head/neck/chest/waist drift',side,box)
        # Both legs remain visible, and the passing versus extended stride differs.
        widths=[]
        for im in [a,b]:
            feet=im.crop((45,88,76,94));bb=feet.getbbox();widths.append(bb[2]-bb[0])
            assert any(im.getpixel((x,y))[3]for x in range(45,64)for y in range(88,94))
            assert any(im.getpixel((x,y))[3]for x in range(64,76)for y in range(88,94))
        assert widths[0]<widths[1]
        assert a.crop((47,60,61,76)).tobytes()!=b.crop((47,60,61,76)).tobytes(),'empty arm did not swing'
    table=dict(zip(C,EC))
    for i in [4,5,6,7]:
        a,b=frames['ally',i],frames['enemy',i];assert a.getchannel('A').tobytes()==b.getchannel('A').tobytes()
        assert all(not p[3]or table[p[:3]]==q[:3]for p,q in zip(a.getdata(),b.getdata()))
    manifest=json.loads((OUT/'asset-manifest.json').read_text())
    for row in manifest['assets']:
        p=ROOT/row['path'];assert p.stat().st_size==row['bytes']and file_hash(p)==row['sha256']
    profiles={p['id']:p for p in data['profiles']};exports=[];captures=[]
    for a in changed:
        old=baseline['actions'][a['id']]
        for key in ['frames','fps','duration','origin','neededFrames','contactTick']:assert a[key]==old[key],(a['id'],key)
        assert not a.get('revisedFrames')and not a.get('reviewTailFrames')
        exports.append(export_one(data,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=False)))
        if a['kind']=='map_walk':
            for tick in [0,16]:
                p=OUT/f'{profiles[a["profile"]]["side"]}-{a["key"]}-phase-{tick//16}.png'
                render_frame(data,profiles[a['profile']],a,tick,8,True).save(p,optimize=True);captures.append(relative(p))
        print('Exported '+a['id'],flush=True)
    decoded=[]
    for e in exports:
        probe=subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames,duration','-of','json',str(ROOT/e['video'])],capture_output=True,text=True,check=True)
        stream=json.loads(probe.stdout)['streams'][0];assert int(stream['nb_read_frames'])==e['frames']and abs(float(stream['duration'])-e['frames']/e['fps'])<1/e['fps']
        decoded.append({'path':e['video'],'stream':stream})
    for a in changed:
        for field,kind,ext in [('video','videos','mp4'),('still','stills','png')]:
            p=ROOT/f'demos/{kind}/{a["id"]}.{ext}';assert matched_export(p,a['contentDigest']);a[field]=relative(p)
    (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n')
    (ROOT/'demos/gallery-data.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
    report={'status':'passed','revision':REV,'changed_actions':sorted(wanted),'unaffected_actions':723,'native_frame_vectors_and_timing_unchanged':True,'fixed_left_regions':[[52,37,73,60],[64,60,68,66],[62,66,70,69]],'down_support_legs_alternate':True,'arm_swing_and_bow_motion':'shoulder rotation -15/+30 degrees; bow and forearm together 0/+1 output pixel','assets':checks,'exports':exports,'decoded_videos':decoded,'phase_captures':captures,'runtime_integrated':False,'user_visual_acceptance':'pending','visual_review_scope':'Offline actual-size/light/dark pose boards and synchronized native/redraw playback captures; browser rendering unavailable under previous file-access restriction.'}
    (OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':'passed','changed_actions':8,'unaffected_actions':723,'videos':len(decoded)}),flush=True)

if __name__=='__main__':main()
