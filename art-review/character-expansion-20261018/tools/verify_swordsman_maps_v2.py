#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Targeted map redraw validation and original/new playback, class9 only."""
import json,subprocess
from types import SimpleNamespace
from PIL import Image
from build_gallery import ROOT,matched_export,relative
from export_gallery import render_frame
from export_knight_complete import export_one
from import_knight_redraw_v3 import parts
from rebuild_swordsman_maps import OUT,REV,COLORS,ENEMY

def main():
    d=json.loads((ROOT/'demos/gallery-data.json').read_text());b=json.loads((OUT/'baseline.json').read_text());meta=json.loads((OUT/'asset-manifest.json').read_text());profiles={p['id']:p for p in d['profiles']};aa=[a for a in d['actions']if a['profile'].startswith('professions-class-9-')and a['context']!='battle'];assert len(aa)==18 and all(a['ready']for a in aa)
    ids={a['id']for a in aa};now={a['id']:a['contentDigest']for a in d['actions']};assert set(now)==set(b['digests']);other=[k for k in now if k not in ids];assert len(other)==629;assert all(now[k]==b['digests'][k]for k in other);assert all(now[k]!=b['digests'][k]for k in ids);assert not d['validation']['structuralIssues']
    for a in aa:
        old=b['actions'][a['id']]
        for field in['frames','fps','origin','duration','contactTick']:assert a[field]==old[field],(a['id'],field)
        assert not a.get('revisedFrames')and not a.get('reviewTailFrames');p=profiles[a['profile']];assert p['revision']==REV
    checks=[];stable=[]
    for side,palette in[('ally',COLORS),('enemy',ENEMY)]:
        for kind,count in[('tactical-idle',6),('tactical-walk',8)]:
            files=sorted((OUT/side/kind).glob('frame-*.png'));assert len(files)==count
            for f in files:
                im=Image.open(f).convert('RGBA');colors={p[:3]for p in im.getdata()if p[3]};assert colors<=set(palette);assert set(im.getchannel('A').getdata())<={0,255};assert f.stat().st_size<50000
                cs=parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))[3]);assert len(cs)==1,(f,'body/shield/sword disconnected',list(map(len,cs)))
                checks.append({'path':relative(f),'size':list(im.size),'bytes':f.stat().st_size,'colors':len(colors),'opaque_components':1})
        idle=[Image.open(OUT/side/'tactical-idle'/f'frame-{i:03}.png').convert('RGBA')for i in range(3)]
        for box in[[44,24,51,35],[39,45,50,55],[25,65,68,81]]:
            assert all(im.crop(box).tobytes()==idle[0].crop(box).tobytes()for im in idle)
            stable.append({'side':side,'fixed_idle_region':box,'rgba_identical':True})
        walk=[Image.open(OUT/side/'tactical-walk'/f'frame-{i:03}.png').convert('RGBA')for i in range(8)]
        assert len({im.tobytes()for im in walk})==8
        for i,box in[(0,[58,32,78,69]),(2,[64,44,69,49]),(4,[59,39,66,48]),(6,[55,43,61,49])]:
            assert walk[i].crop(box).tobytes()==walk[i+1].crop(box).tobytes(),(side,i,'fixed head drift')
            stable.append({'side':side,'direction_start':i,'fixed_region':box,'rgba_identical':True})
        # Back-view support legs are on opposite sides; upper-body colors do
        # not get mirrored with the below-hem leg exchange.
        for i in[0,1]:
            pts=[(x,y)for y in range(73,96)for x in range(128)if walk[i].getpixel((x,y))[:3]==palette[3]and walk[i].getpixel((x,y))[3]];assert pts;mean=sum(x for x,y in pts)/len(pts)
            assert mean<66 if i==0 else mean>66,(i,'same leg repeated',mean)
    # Compare palette with the exact approved in-project mercenary requested
    # by the user, not the frozen original sprite or an imagined reference.
    merc=Image.open(ROOT/'mercenary-eyes-v2-20261019/deliverables/class-8-ally/idle-00.png').convert('RGBA');assert{p[:3]for p in merc.getdata()if p[3]}==set(COLORS)
    exports=[];captures=[]
    for a in aa:
        exports.append(export_one(d,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=False)));p=profiles[a['profile']]
        if a['kind']=='map_walk'or a['key']=='idle-cycle':
            ticks=[0,16]if a['kind']=='map_walk'else[0,14,22]
            for tick in ticks:
                path=OUT/f'{p["side"]}-{a["key"]}-tick-{tick:03}.png';render_frame(d,p,a,tick,4,True).save(path,optimize=True);captures.append(relative(path))
        print('Exported '+a['id'],flush=True)
    videos=[]
    for r in exports:
        p=subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(ROOT/r['video'])],capture_output=True,text=True,check=True);v=json.loads(p.stdout)['streams'][0];assert int(v['nb_read_frames'])==r['frames'];assert abs(float(v['duration'])-r['frames']/r['fps'])<1/r['fps'];videos.append({'path':r['video'],'decoded':v})
    for a in aa:
        for field,kind,ext in[('video','videos','mp4'),('still','stills','png')]:
            p=ROOT/f'demos/{kind}/{a["id"]}.{ext}';a[field]=relative(p)if matched_export(p,a['contentDigest'])else None
    (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(d,ensure_ascii=False,separators=(',',':'))+';\n');(ROOT/'demos/gallery-data.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n')
    result={'status':'passed','affected_actions':18,'map_profiles':4,'original_timing_rows_unchanged':True,'unrelated_existing_actions_unchanged':629,'battle_actions_unchanged':22,'approved_mercenary_ally_palette_exact':True,'both_factions':True,'idle_holds':[14,8,14,8],'walk_hold_per_phase':16,'fixed_regions':stable,'assets':checks,'playback_captures':captures,'runtime_integrated':False,'user_visual_acceptance':'pending','browser_visual_inspection':'Not attempted; native file URL access unavailable. Verified via offline gallery compositor and decoded local videos.'}
    (OUT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');(OUT/'export-report.json').write_text(json.dumps({'status':'passed','exports':exports,'decoded_videos':videos},ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':'passed','map_actions':18,'videos':len(videos),'unrelated_existing_unchanged':629}),flush=True)

if __name__=='__main__':main()
