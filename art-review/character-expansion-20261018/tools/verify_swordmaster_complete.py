#!/usr/bin/env python3
"""Class10 native timing, anatomy connectivity, palette and playback checks."""
import ast,json,subprocess
from types import SimpleNamespace
from PIL import Image
from build_gallery import ROOT,pack_frame,relative,matched_export
from export_gallery import render_frame
from export_knight_complete import export_one
from import_knight_redraw_v3 import parts
from import_swordmaster_complete import OUT,REV,C,EC
from revise_cavalry_map import translate

def main():
    d=json.loads((ROOT/'demos/gallery-data.json').read_text());b=json.loads((OUT/'baseline.json').read_text());meta=json.loads((OUT/'asset-manifest.json').read_text());profiles={p['id']:p for p in d['profiles']}
    aa=[a for a in d['actions']if a['profile'].startswith('professions-class-10-')];assert len(aa)==40 and all(a['ready']for a in aa)
    now={a['id']:a['contentDigest']for a in d['actions']};assert set(now)-set(b['digests'])=={a['id']for a in aa};assert all(now[k]==v for k,v in b['digests'].items());assert len(b['digests'])==647
    assert not d['validation']['structuralIssues'];assert len(d['profiles'])==85
    schedules=[];checks=[]
    for a in aa:
        p=profiles[a['profile']];side=p['side'];assert p['classId']=='10'and p['className']=='剑豪'and p['revision']==REV
        assert not a.get('revisedFrames')and not a.get('reviewTailFrames')
        if a['kind']=='attack':
            v=b['variants'][side][a['key']];assert a['frames']==[pack_frame(row)for row in v['frames']];assert a['fps']==v['native_fps']and a['contactTick']==v['contact_tick']and a['origin']==v['actor_origin']
            schedules.append({'key':a['key'],'frames':len(a['frames']),'contact_tick':a['contactTick'],'contact_count':v['contact_count'],'source_program':v['source_program_address'],'source_rows_exact':True})
        elif a['key']=='idle-cycle':assert [r['frame']for r in a['frames']]==[i for _ in range(2)for i,n in zip([0,1,2,1],[14,8,14,8])for _ in range(n)]
        elif a['kind']=='map_walk':
            start={'walk-up':0,'walk-right':2,'walk-down':4,'walk-left':6}[a['key']];assert[r['frame']for r in a['frames']]==[i for _ in range(3)for i in[start,start+1]for _ in range(16)];assert all(r['offset']==[0,0]and not r['flip']for r in a['frames'])
        elif a['key'].startswith('idle-'):assert len(a['frames'])==32
    assert C[:4]==[(23,38,56),(57,118,181),(228,225,200),(221,167,125)]
    for side,palette in[('ally',C),('enemy',EC)]:
        for kind,count in[('tactical-idle',6),('tactical-walk',8),('battle',19)]:
            files=sorted((OUT/side/kind).glob('frame-*.png'));assert len(files)==count
            for path in files:
                i=int(path.stem[-3:]);im=Image.open(path).convert('RGBA');assert im.size==((320,288)if kind=='battle'else(96,96)if kind=='tactical-idle'else(128,96));assert set(im.getchannel('A').getdata())<={0,255}
                colors={p[:3]for p in im.getdata()if p[3]};assert kind=='battle'and i in[7,13]or colors<=set(palette)
                assert path.stat().st_size<50000
                cc=parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))[3]);expected=0 if kind=='battle'and i==15 else 1
                if kind=='battle'and i in[7,13]:
                    fx=Image.open(OUT/side/f'native-effect-{i:02}.png').convert('RGBA');expected+=len(parts((x,y)for y in range(fx.height)for x in range(fx.width)if fx.getpixel((x,y))[3]))
                assert len(cc)==expected,(path,list(map(len,cc)))
                checks.append({'path':relative(path),'dimensions':list(im.size),'bytes':path.stat().st_size,'colors':len(colors),'components':len(cc)})
        walk=[Image.open(OUT/side/'tactical-walk'/f'frame-{i:03}.png').convert('RGBA')for i in range(8)];assert len({im.tobytes()for im in walk})==8
        # Validate a stable core away from the intentional sword foreground.
        for ids,box in[([0,1],[55,30,74,46]),([2,3],[62,35,76,49]),([4,5],[57,33,74,50]),([6,7],[56,35,71,49])]:assert walk[ids[0]].crop(box).tobytes()==walk[ids[1]].crop(box).tobytes(),(side,ids,'head drift')
        # The remade up/down phase1 must actually plant the opposite foot.
        for ids in[[0,1],[4,5]]:
            centers=[]
            for i in ids:
                pts=[(x,y)for y in range(91,96)for x in range(128)if walk[i].getpixel((x,y))[3]];assert pts;centers.append(sum(x for x,y in pts)/len(pts))
            assert centers[0]<64 and centers[1]>64,(side,ids,'same support leg',centers)
        idle=[Image.open(OUT/side/'tactical-idle'/f'frame-{i:03}.png').convert('RGBA')for i in range(3)]
        # The native inward sword passes in front of the left collar edge in
        # phase2; validate the actual face core and both fixed body regions.
        for box in[[45,29,58,40],[37,45,59,58],[28,58,77,81]]:assert all(im.crop(box).tobytes()==idle[0].crop(box).tobytes()for im in idle),(side,box,'idle core drift')
        # Each map pose has a complete long blade, plus skin and dark eye/hair.
        for im in idle+walk:
            cs=parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))[3]and im.getpixel((x,y))[:3]==palette[2]);assert any(max(y for x,y in c)-min(y for x,y in c)>=11 for c in cs),'missing upright sword'
        for i in[0,1,2,16,31]:
            im=Image.open(OUT/side/'battle'/f'frame-{i:03}.png').convert('RGBA');assert any(p[:3]==palette[3]and p[3]for p in im.getdata())
    for i in[16,31,32]:
        a=Image.open(OUT/'ally/battle'/f'frame-{i:03}.png').convert('RGBA');e=Image.open(OUT/'enemy/battle'/f'frame-{i:03}.png').convert('RGBA');assert translate(a,[-64,0]).getchannel('A').tobytes()==e.getchannel('A').tobytes()
    for side in['ally','enemy']:
        for t,s,delta in[(7,8,[-40,-96]),(13,12,[0,0])]:
            fx=Image.open(OUT/side/f'native-effect-{t:02}.png').convert('RGBA');body=translate(Image.open(OUT/side/'battle'/f'frame-{s:03}.png').convert('RGBA'),delta);fx.alpha_composite(body);out=Image.open(OUT/side/'battle'/f'frame-{t:03}.png').convert('RGBA');assert fx.tobytes()==out.tobytes()
    for reg in meta['registration']:assert reg['clipped_pixels']==0
    for name in['import_swordmaster_complete.py','verify_swordmaster_complete.py']:ast.parse((ROOT/'tools'/name).read_text())
    write_report={'status':'structural_passed_exporting','profiles':6,'actions':40,'new_gallery_total':687,'unrelated_existing_actions_unchanged':647,'native_schedules':schedules,'assets':checks,'runtime_integrated':False,'user_visual_acceptance':'pending'}
    (OUT/'verification.json').write_text(json.dumps(write_report,ensure_ascii=False,indent=2)+'\n');print('Structure, original schedules, native effects, six colors and opposite support legs passed',flush=True)
    exports=[];captures=[]
    for a in aa:
        p=profiles[a['profile']];exports.append(export_one(d,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=False)))
        if a['kind']=='attack'and('normal'in a['key']or a['key']in['class_10_ally_levin','class_10_enemy_levin']):
            exports.append(export_one(d,a,SimpleNamespace(close=True,scale=4,light=False,stills_only=False)))
            ids=[0,2,4,6,7,8,10,11,12,13,14,15]if'normal'in a['key']else[32]
            for i in ids:
                tick=next(j for j,r in enumerate(a['frames'])if r['frame']==i);path=OUT/f'{p["side"]}-battle-pose-{i:02}-playback.png';render_frame(d,p,a,tick,4,False,True).save(path,optimize=True);captures.append(relative(path))
        if a['kind']=='map_walk'or a['key']=='idle-cycle':
            for tick in([0,16]if a['kind']=='map_walk'else[0,14,22]):
                path=OUT/f'{p["side"]}-{a["key"]}-tick-{tick:02}.png';render_frame(d,p,a,tick,8,True).save(path,optimize=True);captures.append(relative(path))
        print('Exported '+a['id'],flush=True)
    decoded=[]
    for e in exports:
        run=subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(ROOT/e['video'])],capture_output=True,text=True,check=True);row=json.loads(run.stdout)['streams'][0];assert int(row['nb_read_frames'])==e['frames'];assert abs(float(row['duration'])-e['frames']/e['fps'])<1/e['fps'];decoded.append({'path':e['video'],'stream':row})
    for a in aa:
        for field,kind,suffix,ext in[('video','videos','','mp4'),('closeVideo','videos','--close','mp4'),('still','stills','','png')]:
            p=ROOT/f'demos/{kind}/{a["id"]}{suffix}.{ext}';a[field]=relative(p)if matched_export(p,a['contentDigest'])else None
        assert a['video']and a['still']
    (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(d,ensure_ascii=False,separators=(',',':'))+';\n');(ROOT/'demos/gallery-data.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n')
    write_report.update(status='passed',fixed_map_core=True,opposite_support_legs=True,whole_pose_connections=True,original_launch_and_slash_effects_exact=True,native_blank_interval_preserved=True,map_base_palette_plus_two_colors=True,playback_captures=captures,visual_scope='Deep/light pose boards and offline original/redraw playback capture; no foreground game and no local browser access workaround.')
    (OUT/'verification.json').write_text(json.dumps(write_report,ensure_ascii=False,indent=2)+'\n');(OUT/'export-report.json').write_text(json.dumps({'status':'passed','exports':exports,'decoded_videos':decoded},ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':'passed','actions':40,'videos':len(decoded),'unrelated_existing_unchanged':647}),flush=True)

if __name__=='__main__':main()
