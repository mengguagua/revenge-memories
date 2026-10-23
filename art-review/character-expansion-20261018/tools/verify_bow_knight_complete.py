#!/usr/bin/env python3
"""Class20 native schedule, stable-center, asset and offline playback checks."""
import ast,json,subprocess
from types import SimpleNamespace
from PIL import Image
from build_gallery import ROOT,pack_frame,file_hash,matched_export,relative
from export_gallery import render_frame
from export_knight_complete import export_one
from import_bow_knight_complete import REV,OUT,SRC,C,EC,io

def main():
    d=json.loads((ROOT/'demos/gallery-data.json').read_text());b=json.loads((OUT/'baseline.json').read_text());manifest=json.loads((OUT/'asset-manifest.json').read_text());pp={p['id']:p for p in d['profiles']}
    aa=[a for a in d['actions']if a['profile'].startswith('professions-class-20-')]
    assert len(aa)==44 and all(a['ready']for a in aa)
    assert len(d['profiles'])==97 and len(d['actions'])==775 and not d['validation']['structuralIssues']
    now={a['id']:a for a in d['actions']};assert set(now)-set(b['actions'])=={a['id']for a in aa}
    for k,a in b['actions'].items():assert now[k]['contentDigest']==a['contentDigest'],('unrelated action changed',k)
    schedules=[]
    for a in aa:
        p=pp[a['profile']];side=p['side'];assert p['classId']=='20'and p['className']=='弓骑士'and p['revision']==REV
        assert not a.get('revisedFrames')and not a.get('reviewTailFrames')
        if a['kind']=='attack':
            v=b['variants'][side][a['key']]
            assert a['frames']==[pack_frame(f)for f in v['frames']]
            assert a['fps']==v['native_fps']and a['origin']==v['actor_origin']and a['contactTick']==v['contact_tick']and v['contact_count']==1
            schedules.append({'action':a['key'],'frames':len(a['frames']),'fps':a['fps'],'contact_tick':a['contactTick'],'program':v['source_program_address'],'single_contact':True,'source_rows_exact':True})
        elif a['key']=='idle-cycle':assert[f['frame']for f in a['frames']]==[f for _ in range(2)for f,n in zip([0,1,2,1],[14,8,14,8])for _ in range(n)]
        elif a['kind']=='map_walk':
            start={'walk-up':0,'walk-right':2,'walk-down':4,'walk-left':6}[a['key']]
            assert[f['frame']for f in a['frames']]==[f for _ in range(3)for f in[start,start+1]for _ in range(16)]
            assert all(f['offset']==[0,0]and not f['flip']for f in a['frames'])
        elif a['key'].startswith('idle-'):assert len(a['frames'])==32
    checks=[];frames={}
    for side,palette in [('ally',C),('enemy',EC)]:
        for kind,count,size in [('tactical-idle',6,(96,96)),('tactical-walk',8,(128,96)),('battle',7 if side=='ally'else 3,(320,256))]:
            paths=sorted((OUT/side/kind).glob('frame-*.png'));assert len(paths)==count
            for path in paths:
                im=Image.open(path).convert('RGBA');assert im.size==size and set(im.getchannel('A').getdata())=={0,255}
                assert{p[:3]for p in im.getdata()if p[3]}==set(palette)
                cc=io.helper.parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))[3]);assert len(cc)==1,(path,list(map(len,cc)))
                assert path.stat().st_size<50000
                bb=im.getbbox();assert 0<bb[0]<bb[2]<im.width and 0<bb[1]<bb[3]<=im.height
                frames[side,kind,int(path.stem.split('-')[1])]=im
                checks.append({'path':relative(path),'size':list(im.size),'bytes':path.stat().st_size,'colors':6,'connected_components':1,'bounds':bb})
        idle=[frames[side,'tactical-idle',i]for i in range(6)];walk=[frames[side,'tactical-walk',i]for i in range(8)]
        for i,j in enumerate([0,1,2,1,0,1]):assert idle[i].tobytes()==idle[j].tobytes()
        assert all(im.crop((0,0,96,56)).tobytes()==idle[0].crop((0,0,96,56)).tobytes()for im in idle)
        assert len({idle[i].crop((0,56,96,96)).tobytes()for i in range(3)})==3
        for ids in [[0,1],[4,5]]:
            assert walk[ids[0]].crop((0,0,128,68)).tobytes()==walk[ids[1]].crop((0,0,128,68)).tobytes()
            assert walk[ids[0]].crop((0,68,128,96)).tobytes()!=walk[ids[1]].crop((0,68,128,96)).tobytes()
        for dst,src in [(6,0),(7,2)]:
            im=Image.new('RGBA',(128,96));im.alpha_composite(idle[src],(16,16));assert im.tobytes()==walk[dst].tobytes()
        for dst,src in [(2,6),(3,7)]:assert walk[dst].tobytes()==walk[src].transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes()
        # The reuse is proven against the CPU-extracted source, not assumed.
        for slot,static in [(6,0),(7,2)]:
            im=Image.new('RGBA',(32,24));im.alpha_composite(Image.open(SRC/f'native-{side}-idle-{static:03}.png').convert('RGBA'),(4,4))
            assert im.tobytes()==Image.open(SRC/f'native-{side}-walk-{slot:03}.png').convert('RGBA').tobytes()
    for kind,count in [('tactical-idle',6),('tactical-walk',8)]:
        table=dict(zip(C,EC))
        for i in range(count):
            a,c=frames['ally',kind,i],frames['enemy',kind,i];assert a.getchannel('A').tobytes()==c.getchannel('A').tobytes();assert all(not p[3]or table[p[:3]]==q[:3]for p,q in zip(a.getdata(),c.getdata()))
    arrow=Image.open(OUT/'flying-arrow.png').convert('RGBA');assert arrow.size==(64,16)
    assert{p[:3]for p in arrow.getdata()if p[3]}=={C[2],C[4]}
    for side,key in [('ally','39768fc933fe67'),('enemy','native-1487ce1e7365a7')]:
        p=pp[f'professions-class-20-{side}-battle'];assert p['revisedEffects'][key]['path']==REV+'/flying-arrow.png'
        source=Image.open(ROOT/d['effects'][key]['path']).convert('RGBA');assert source.getchannel('A').tobytes()==arrow.getchannel('A').tobytes()
        for k,v in d['effects'][key].items():
            if k!='path':assert p['revisedEffects'][key][k]==v
    audit=json.loads((OUT/'native-reference-audit.json').read_text())
    for record in audit['source_assets']:assert file_hash(ROOT/record['path'])==record['sha256']
    for record in manifest['assets']:
        p=ROOT/record['path'];assert p.stat().st_size==record['bytes']and file_hash(p)==record['sha256']
    assert all(r['clipped_pixels']==0 for r in manifest['whole_pose_registrations'])
    for script in ['prepare_bow_knight_complete.py','import_bow_knight_complete.py','verify_bow_knight_complete.py']:ast.parse((ROOT/'tools'/script).read_text())
    report={'status':'assets_passed_exporting','class_id':20,'profiles':6,'actions':44,'existing_actions_unchanged':731,'native_attack_schedules':schedules,'asset_checks':checks,'fixed_map_rider_horse_centers':True,'native_cpu_side_aliases_proven':True,'native_arrow_alpha_anchors_positions_unchanged':True,'runtime_integrated':False,'user_visual_acceptance':'pending'}
    (OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    exports=[];captures=[]
    for a in aa:
        p=pp[a['profile']];exports.append(export_one(d,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=False)))
        if a['key']in ['class_20_ally_bow','class_20_ally_silver_bow','class_20_enemy_bow']:
            exports.append(export_one(d,a,SimpleNamespace(close=True,scale=4,light=False,stills_only=False)))
            for frame in sorted({f['frame']for f in a['frames']}):
                tick=next(n for n,f in enumerate(a['frames'])if f['frame']==frame);path=OUT/f'{p["side"]}-{a["key"]}-pose-{frame:02}.png'
                render_frame(d,p,a,tick,6,True,True).save(path,optimize=True);captures.append(relative(path))
            ticks=[i for i,f in enumerate(a['frames'])if f['effects']];tick=ticks[len(ticks)//2]
            path=OUT/f'{p["side"]}-{a["key"]}-flight.png';render_frame(d,p,a,tick,4,False).save(path,optimize=True);captures.append(relative(path))
        if a['kind']=='map_walk'or a['key']=='idle-cycle':
            for tick in ([0,16]if a['kind']=='map_walk'else[0,14,22]):
                path=OUT/f'{p["side"]}-{a["key"]}-phase-{tick:02}.png';render_frame(d,p,a,tick,8,True).save(path,optimize=True);captures.append(relative(path))
        print('Exported '+a['id'],flush=True)
    decoded=[]
    for e in exports:
        probe=subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(ROOT/e['video'])],capture_output=True,text=True,check=True)
        s=json.loads(probe.stdout)['streams'][0];assert int(s['nb_read_frames'])==e['frames']and abs(float(s['duration'])-e['frames']/e['fps'])<1/e['fps'];decoded.append({'video':e['video'],'stream':s})
    for a in aa:
        for field,kind,suffix,ext in [('video','videos','','mp4'),('closeVideo','videos','--close','mp4'),('still','stills','','png')]:
            path=ROOT/f'demos/{kind}/{a["id"]}{suffix}.{ext}';a[field]=relative(path)if matched_export(path,a['contentDigest'])else None
        assert a['video']and a['still']
    (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(d,ensure_ascii=False,separators=(',',':'))+';\n');(ROOT/'demos/gallery-data.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n')
    report.update(status='passed',phase_captures=captures,visual_scope='Light/dark pose boards and offline synchronized native/redraw captures; browser rendering unavailable under prior file-access restriction.')
    (OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');(OUT/'export-report.json').write_text(json.dumps({'status':'passed','exports':exports,'decoded_videos':decoded},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':'passed','actions':44,'existing_unchanged':731,'videos':len(decoded)}),flush=True)

if __name__=='__main__':main()
