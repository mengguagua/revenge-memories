#!/usr/bin/env python3
"""Check all new sniper assets and both original programs, then export reviews."""
import ast,json,subprocess
from types import SimpleNamespace
from PIL import Image
from build_gallery import ROOT,pack_frame,matched_export,relative,file_hash
from export_gallery import render_frame
from export_knight_complete import export_one
from import_sniper_complete import REV,OUT,C,EC,helper

def main():
    d=json.loads((ROOT/'demos/gallery-data.json').read_text());b=json.loads((OUT/'baseline.json').read_text());manifest=json.loads((OUT/'asset-manifest.json').read_text())
    pp={p['id']:p for p in d['profiles']};aa=[a for a in d['actions']if a['profile'].startswith('professions-class-13-')]
    assert len(aa)==44 and all(a['ready']for a in aa)
    assert len(d['profiles'])==91 and len(d['actions'])==731
    assert not d['validation']['structuralIssues']
    now={a['id']:a['contentDigest']for a in d['actions']}
    assert set(now)-set(b['actions'])=={a['id']for a in aa}
    for k,a in b['actions'].items():assert now[k]==a['contentDigest'],('unrelated change',k)
    schedules=[];checks=[]
    for a in aa:
        p=pp[a['profile']];side=p['side'];assert p['classId']=='13'and p['className']=='狙击手'and p['revision']==REV
        assert not a.get('revisedFrames')and not a.get('reviewTailFrames')
        if a['kind']=='attack':
            v=b['variants'][side][a['key']]
            assert a['frames']==[pack_frame(x)for x in v['frames']]
            assert a['fps']==v['native_fps']and a['contactTick']==v['contact_tick']and a['origin']==v['actor_origin']and v['contact_count']==1
            schedules.append({'key':a['key'],'frames':len(a['frames']),'contact_tick':a['contactTick'],'program':v['source_program_address'],'single_contact':True,'source_rows_exact':True})
        elif a['key']=='idle-cycle':
            expected=[f for _ in range(2)for f,n in zip([0,1,2,1],[14,8,14,8])for _ in range(n)]
            assert [r['frame']for r in a['frames']]==expected
        elif a['kind']=='map_walk':
            start={'walk-up':0,'walk-right':2,'walk-down':4,'walk-left':6}[a['key']]
            assert [r['frame']for r in a['frames']]==[f for _ in range(3)for f in [start,start+1]for _ in range(16)]
            assert all(r['offset']==[0,0]and not r['flip']for r in a['frames'])
        elif a['key'].startswith('idle-'):assert len(a['frames'])==32
    assert C[:4]==[(23,38,56),(57,118,181),(228,225,200),(221,167,125)]
    assert len(C)==len(EC)==5
    for side,palette in [('ally',C),('enemy',EC)]:
        for kind,count,size in [('tactical-walk',8,(128,96)),('tactical-idle',6,(96,96)),('battle',9 if side=='ally'else 13,(320,256))]:
            paths=sorted((OUT/side/kind).glob('frame-*.png'));assert len(paths)==count
            for path in paths:
                im=Image.open(path).convert('RGBA');assert im.size==size
                assert set(im.getchannel('A').getdata())=={0,255}
                colors={p[:3]for p in im.getdata()if p[3]};assert colors==set(palette),(path,colors)
                cc=helper.parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))[3]);assert len(cc)==1,(path,list(map(len,cc)))
                assert path.stat().st_size<50000
                checks.append({'path':relative(path),'dimensions':list(im.size),'bytes':path.stat().st_size,'colors':5,'connected_components':1})
        walk=[Image.open(OUT/side/'tactical-walk'/f'frame-{i:03}.png').convert('RGBA')for i in range(8)]
        assert len({im.tobytes()for im in walk})==8
        for ids in [[0,1],[2,3],[4,5],[6,7]]:
            for box in [[51,30,79,54],[57,60,71,69]]:assert walk[ids[0]].crop(box).tobytes()==walk[ids[1]].crop(box).tobytes(),(side,ids,'fixed core')
        for i,sign in [(0,-1),(1,1),(4,1),(5,-1)]:
            pts=[(x,y)for y in range(91,96)for x in range(128)if walk[i].getpixel((x,y))[3]]
            center=sum(x for x,y in pts)/len(pts);assert (center-64)*sign>0,(side,i,center)
        idle=[Image.open(OUT/side/'tactical-idle'/f'frame-{i:03}.png').convert('RGBA')for i in range(6)]
        for i,j in enumerate([0,1,2,1,0,1]):assert idle[i].tobytes()==idle[j].tobytes()
        for box in [[37,18,60,41],[40,42,57,55],[26,57,72,81]]:assert all(idle[i].crop(box).tobytes()==idle[0].crop(box).tobytes()for i in [1,2])
    for r in manifest['assets']:
        p=ROOT/r['path'];assert p.stat().st_size==r['bytes']and file_hash(p)==r['sha256']
    for r in manifest['registration']:assert r['clipped_pixels']==0
    for name in ['prepare_sniper_sources.py','import_sniper_complete.py','verify_sniper_complete.py']:ast.parse((ROOT/'tools'/name).read_text())
    report={'status':'structure_passed_exporting','profiles':6,'actions':44,'existing_actions_unchanged':687,'palette':'approved archer four materials plus warm brown','native_schedules':schedules,'assets':checks,'runtime_integrated':False,'user_visual_acceptance':'pending'}
    (OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    exports=[];captures=[]
    for a in aa:
        p=pp[a['profile']];exports.append(export_one(d,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=False)))
        if a['key']in ['class_13_ally_bow','class_13_ally_silver_bow','class_13_enemy_bow']:
            exports.append(export_one(d,a,SimpleNamespace(close=True,scale=4,light=False,stills_only=False)))
            ids=sorted(set(r['frame']for r in a['frames']))
            for i in ids:
                tick=next(n for n,r in enumerate(a['frames'])if r['frame']==i);path=OUT/f'{p["side"]}-{a["key"]}-pose-{i:02}.png'
                render_frame(d,p,a,tick,6,True,True).save(path,optimize=True);captures.append(relative(path))
            path=OUT/f'{p["side"]}-{a["key"]}-contact.png';render_frame(d,p,a,a['contactTick'],4,False).save(path,optimize=True);captures.append(relative(path))
        if a['kind']=='map_walk'or a['key']=='idle-cycle':
            for tick in ([0,16]if a['kind']=='map_walk'else [0,14,22]):
                path=OUT/f'{p["side"]}-{a["key"]}-tick-{tick:02}.png';render_frame(d,p,a,tick,8,True).save(path,optimize=True);captures.append(relative(path))
        print('Exported '+a['id'],flush=True)
    decoded=[]
    for e in exports:
        r=subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(ROOT/e['video'])],capture_output=True,text=True,check=True)
        s=json.loads(r.stdout)['streams'][0];assert int(s['nb_read_frames'])==e['frames'];assert abs(float(s['duration'])-e['frames']/e['fps'])<1/e['fps'];decoded.append({'path':e['video'],'stream':s})
    for a in aa:
        for field,kind,suffix,ext in [('video','videos','','mp4'),('closeVideo','videos','--close','mp4'),('still','stills','','png')]:
            p=ROOT/f'demos/{kind}/{a["id"]}{suffix}.{ext}';a[field]=relative(p)if matched_export(p,a['contentDigest'])else None
        assert a['video']and a['still']
    (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(d,ensure_ascii=False,separators=(',',':'))+';\n')
    (ROOT/'demos/gallery-data.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n')
    report.update(status='passed',fixed_map_center=True,native_opposite_support_legs=True,source_projectile_and_contact_rows_exact=True,playback_captures=captures,visual_scope='Deep/light pose boards and offline synchronized original/redraw captures; no foreground game or browser workaround.')
    (OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    (OUT/'export-report.json').write_text(json.dumps({'status':'passed','exports':exports,'decoded_videos':decoded},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':'passed','actions':44,'videos':len(decoded),'existing_unchanged':687}),flush=True)

if __name__=='__main__':main()
