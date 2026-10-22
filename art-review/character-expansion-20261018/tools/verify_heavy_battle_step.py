#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Focused geometry, native schedule, asset integrity and playback checks."""
import json,subprocess
from types import SimpleNamespace
from PIL import Image
from build_gallery import ROOT,pack_frame,matched_export,relative
from export_gallery import render_frame
from export_knight_complete import export_one
from import_knight_redraw_v3 import parts
from import_heavy_infantry_v1 import COLORS,ECOLORS,faction
from revise_cavalry_map import translate
from revise_heavy_battle_step import OUT,SRC,REV,ALIASES,CORE_BOX

def main():
    d=json.loads((ROOT/'demos/gallery-data.json').read_text());base=json.loads((OUT/'baseline.json').read_text());profiles={p['id']:p for p in d['profiles']}
    now={a['id']:a['contentDigest']for a in d['actions']};assert set(now)==set(base['digests']);changed={k for k,v in now.items()if v!=base['digests'][k]}
    targets=[a for a in d['actions']if a['id']in changed];assert len(targets)==10 and all(a['ready']and a['profile'].startswith('professions-class-2-')and(a['kind']=='reaction'or'normal'in a['key'])for a in targets)
    assert not d['validation']['structuralIssues'];timing=[];checks=[];reports=[]
    native={side:json.loads((ROOT/f'source-input/{"original"if side=="ally"else"enemy"}-motion/full-{"original"if side=="ally"else"enemy"}-motion.json').read_text())for side in['ally','enemy']}
    accepted=Image.open(SRC/'before-000.png').convert('RGBA')
    for side in['ally','enemy']:
        old=base['mappings'][side];mapping=json.loads((ROOT/f'professions/class-2-{side}/battle/frame_mapping.json').read_text());folder=ROOT/f'professions/class-2-{side}/battle'
        assert mapping['effect_overrides']==old['effect_overrides']and mapping['variant_keys']==old['variant_keys']
        for i in[11,12,30,32]:assert mapping['frame_mapping'][str(i)]==old['frame_mapping'][str(i)]
        images={int(i):Image.open((folder/path).resolve()).convert('RGBA')for i,path in mapping['frame_mapping'].items()}
        expected=faction(accepted,side)
        for i in[0,4,5,6,7,8,9,10]:
            im=images[i];assert im.crop(CORE_BOX).tobytes()==expected.crop(CORE_BOX).tobytes()
            assert im.size==(320,256)and set(im.getchannel('A').getdata())<={0,255}
            assert {p[:3]for p in im.getdata()if p[3]}<=set(COLORS if side=='ally'else ECOLORS)
            comps=parts((x,y)for y in range(256)for x in range(320)if im.getpixel((x,y))[3]);assert len(comps)==1,(side,i,'detached limb/equipment',[len(c)for c in comps])
            assert im.getbbox()[2]<320 and im.getbbox()[3]<256
        for i,alias in ALIASES.items():
            want=translate(images[alias],[-64,0])if side=='enemy'and i in[16,29]else images[alias]
            assert images[i].tobytes()==want.tobytes(),(side,i,alias)
        for a in d['actions']:
            if a['profile']!=f'professions-class-2-{side}-battle'or a['kind']!='attack':continue
            v=native[side]['variants'][a['key']];assert a['frames']==[pack_frame(row)for row in v['frames']]and a['contactTick']==v['contact_tick']and a['fps']==v['native_fps']and v['contact_count']==1
            if'normal'in a['key']:
                assert len(a['frames'])==335 and a['contactTick']==153
                timing.append({'side':side,'frames':335,'contact_tick':153,'contact_frame_in_ui':154,'contact_count':1,'all_native_rows_identical':True})
                for i in[0,5,6,7,4,11,12]:
                    tick=next(t for t,r in enumerate(a['frames'])if r['frame']==i);render_frame(d,profiles[a['profile']],a,tick,4,False,True).save(OUT/f'{side}-normal-pose-{i:02}.png',optimize=True)
        checks.append({'side':side,'fixed_core_pixel_identical':True,'connected_body_and_equipment':True,'exact_repeated_leg_aliases':True,'binary_alpha':True,'palette_colors':len(COLORS),'unmodified_thrust_throw_and_projectile':True})
    # Native alias proof is separate from our art aliases: the lower-body CHR
    # pixels really repeat at these program slots, so they must not be invented.
    source={i:Image.open(SRC/f'native-{i:03}.png').convert('RGBA')for i in[0,4,5,6,7,8,9,10]}
    for i,j in[(5,7),(4,8),(4,9),(4,10)]:assert source[i].crop((36,49,63,64)).tobytes()==source[j].crop((36,49,63,64)).tobytes()
    manifest=json.loads((OUT/'asset-manifest.json').read_text());assert all(r['clipped_pixels']==0 for r in manifest['registration'])
    for r in manifest['leg_registration']:assert r['shear']==0 and .8<r['uniform_scale']<1.15
    for a in targets:
        reports.append(export_one(d,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=False)))
        if'normal'in a['key']:reports.append(export_one(d,a,SimpleNamespace(close=True,scale=4,light=False,stills_only=False)))
        print('Exported '+a['id'],flush=True)
    videos=[]
    for rec in reports:
        q=subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(ROOT/rec['video'])],capture_output=True,text=True,check=True);s=json.loads(q.stdout)['streams'][0]
        assert int(s['nb_read_frames'])==rec['frames']and abs(float(s['duration'])-rec['frames']/rec['fps'])<1/rec['fps'];videos.append({'path':rec['video'],'decoded':s})
    for a in targets:
        for field,kind,suffix,ext in[('video','videos','','mp4'),('closeVideo','videos','--close','mp4'),('still','stills','','png')]:
            p=ROOT/f'demos/{kind}/{a["id"]}{suffix}.{ext}';a[field]=relative(p)if matched_export(p,a['contentDigest'])else None
    (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(d,ensure_ascii=False,separators=(',',':'))+';\n');(ROOT/'demos/gallery-data.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n')
    (OUT/'verification.json').write_text(json.dumps({'status':'passed','affected_actions':10,'unrelated_action_digests_unchanged':len(now)-10,'gallery_profiles':len(d['profiles']),'gallery_actions':len(d['actions']),'both_factions':checks,'native_normal_schedule':timing,'native_repeated_lower_body_pixels_proven':True,'native_timing_modified':False,'map_idle_and_all_four_walk_directions_unchanged':True,'all_other_classes_unchanged':True,'runtime_integrated':False,'user_visual_acceptance':'pending','visual_check':'Generated master and registered dark/light full-body boards; offline actual playback captures and exported video decoding. No browser workaround or visible Godot window.'},ensure_ascii=False,indent=2)+'\n')
    (OUT/'export-report.json').write_text(json.dumps({'status':'passed','stills':len(reports),'videos':videos,'exports':reports},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':'passed','affected_actions':10,'unrelated_actions_unchanged':len(now)-10,'videos':len(videos)}),flush=True)

if __name__=='__main__':main()
