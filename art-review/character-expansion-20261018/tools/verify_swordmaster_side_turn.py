#!/usr/bin/env python3
"""Targeted registration, native timing, export and scope checks for side yaw."""
import ast, json, subprocess
from types import SimpleNamespace
from PIL import Image
from build_gallery import ROOT, matched_export, relative, file_hash
from export_gallery import render_frame
from export_knight_complete import export_one
from import_knight_redraw_v3 import parts
from revise_swordmaster_side_turn import OUT, SRC, REV
from import_swordmaster_complete import C, EC

def main():
    b=json.loads((OUT/'baseline.json').read_text())
    d=json.loads((ROOT/'demos/gallery-data.json').read_text())
    wanted={f'professions-class-10-{s}-maps-tactical-walk--{k}' for s in ['ally','enemy'] for k in ['walk-right','idle-right','walk-left','idle-left']}
    changed=[a for a in d['actions'] if a['contentDigest']!=b['actions'][a['id']]['contentDigest']]
    assert len(d['actions'])==len(b['actions'])==687
    assert {a['id'] for a in changed}==wanted
    assert not d['validation']['structuralIssues']
    checks=[]
    frames={}
    for side,palette in [('ally',C),('enemy',EC)]:
        m=json.loads((ROOT/f'professions/class-10-{side}/maps/frame_mapping.json').read_text())
        old=b['mappings'][side]
        assert m['scenarios'][1 if m['scenarios'][0]['id']=='tactical-walk' else 0]==old['scenarios'][1 if old['scenarios'][0]['id']=='tactical-walk' else 0], 'idle scenario changed'
        for i in [2,3,6,7]:
            path=OUT/side/f'walk-{i:02}.png';im=Image.open(path).convert('RGBA');frames[side,i]=im
            assert im.size==(128,96)
            assert {p[:3] for p in im.getdata() if p[3]}==set(palette)
            assert set(im.getchannel('A').getdata())=={0,255}
            components=parts((x,y) for y in range(96) for x in range(128) if im.getpixel((x,y))[3])
            assert len(components)==1,(side,i,'disconnected',list(map(len,components)))
            bound=im.getbbox();assert 0<bound[0]<bound[2]<128 and 0<bound[1]<bound[3]<96
            # Sword/eye/skin are present and not replaced with white highlights.
            assert sum(im.getpixel((x,y))[:3]==palette[3] and im.getpixel((x,y))[3]>0 for y in range(30,52) for x in range(40,83))>8
            assert path.stat().st_size<50000
            checks.append({'path':relative(path),'size':list(im.size),'bytes':path.stat().st_size,'colors':6,'alpha':'binary','opaque_components':1,'bounds':bound})
        for a,c in [(2,3),(6,7)]:
            assert frames[side,a].crop((0,0,128,65)).tobytes()==frames[side,c].crop((0,0,128,65)).tobytes(),'upper-body drift'
            assert frames[side,a].crop((0,65,128,96)).tobytes()!=frames[side,c].crop((0,65,128,96)).tobytes(),'leg phase missing'
            widths=[]
            for i in [a,c]:
                p=frames[side,i].crop((0,86,128,96));bnd=p.getbbox();widths.append(bnd[2]-bnd[0])
            assert widths[0]>widths[1],('wide vs passing stride',side,a,widths)
    # Faction substitution changes only approved materials, never geometry.
    table=dict(zip(C,EC))
    for i in [2,3,6,7]:
        ally=frames['ally',i];enemy=frames['enemy',i]
        assert ally.getchannel('A').tobytes()==enemy.getchannel('A').tobytes()
        for p,q in zip(ally.getdata(),enemy.getdata()):
            if p[3]:assert q[:3]==table[p[:3]]
    manifest=json.loads((OUT/'asset-manifest.json').read_text())
    for r in manifest['assets']:
        p=ROOT/r['path'];assert p.is_file() and p.stat().st_size==r['bytes'] and file_hash(p)==r['sha256']
    profiles={p['id']:p for p in d['profiles']};exports=[];captures=[]
    for a in changed:
        old=b['actions'][a['id']]
        for k in ['frames','fps','origin','duration','contactTick','neededFrames']:assert a[k]==old[k],(a['id'],k)
        exports.append(export_one(d,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=False)))
        if a['key'].startswith('walk-'):
            for tick in [0,16]:
                p=OUT/f'{profiles[a["profile"]]["side"]}-{a["key"]}-phase-{tick//16}.png'
                render_frame(d,profiles[a['profile']],a,tick,8,True).save(p,optimize=True)
                captures.append({'path':relative(p),'size':list(Image.open(p).size),'bytes':p.stat().st_size})
        print('Exported '+a['id'],flush=True)
    videos=[]
    for e in exports:
        probe=subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames,duration','-of','json',str(ROOT/e['video'])],capture_output=True,text=True,check=True)
        row=json.loads(probe.stdout)['streams'][0]
        assert int(row['nb_read_frames'])==e['frames']
        assert abs(float(row['duration'])-e['frames']/e['fps'])<1/e['fps']
        videos.append({'path':e['video'],'decoded':row})
    for a in changed:
        for field,kind,ext in [('video','videos','mp4'),('still','stills','png')]:
            p=ROOT/f'demos/{kind}/{a["id"]}.{ext}';assert matched_export(p,a['contentDigest']);a[field]=relative(p)
    (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(d,ensure_ascii=False,separators=(',',':'))+';\n')
    (ROOT/'demos/gallery-data.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n')
    for f in ['revise_swordmaster_side_turn.py','verify_swordmaster_side_turn.py']:ast.parse((ROOT/'tools'/f).read_text())
    report={'status':'passed','revision':REV,'changed_actions':sorted(wanted),'unchanged_actions':679,'native_frames_origins_and_timing_unchanged':True,'fixed_upper_body_region':[0,0,128,65],'asset_checks':checks,'exports':exports,'decoded_videos':videos,'phase_captures':captures,'visual_review':'Offline side-pose boards and native/redraw captures; torso/shoulder/arm perspective and both leg phases inspected. Browser page not rendered due prior file-access limitation.','runtime_integrated':False,'user_visual_acceptance':'pending'}
    (OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':'passed','changed_actions':8,'unchanged_actions':679,'videos':len(videos)}),flush=True)

if __name__=='__main__':main()
