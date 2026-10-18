"""Targeted regression checks for the male map art correction."""
from pathlib import Path
from PIL import Image
import json,hashlib,subprocess,shutil
V=Path(__file__).resolve().parents[1];R=V.parent;M=R/'hunapu/maps'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def im(p):return Image.open(p).convert('RGBA')
def same(a,b,box):return a.crop(box).tobytes()==b.crop(box).tobytes()
def delta(a,b,box):return sum(p!=q for p,q in zip(a.crop(box).getdata(),b.crop(box).getdata()))
def probe(p):return json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,nb_frames,duration','-of','json',str(p)]))['streams'][0]
report={'status':'technical_checks_passed_pending_user_visual_acceptance','scope':'male maps only','browser_playback_tested':False,'godot_runtime_tested':False}
baseline=read(V/'reference/protected-sha256.json');changed=[p for p,h in baseline.items()if sha(R/p)!=h]
assert not changed,changed
report['protected_prior_art_and_other_maps']={'checked':len(baseline),'changed':changed}
before={s['id']:s for s in read(V/'reference/hunapu-mapping-before.json')['scenarios']}
sc={s['id']:s for s in read(M/'frame_mapping.json')['scenarios']}
for name,slots in [('story',[0,1,2,3]),('tactical-walk',[0,1,4,5]),('tactical-idle',list(range(6)))]:
    for slot in slots:
        old=next(f for f in before[name]['frame_mapping']if f['source_index']==slot)
        new=next(f for f in sc[name]['frame_mapping']if f['source_index']==slot)
        assert old['path']==new['path'] and sha(M/old['path'])==new['sha256'],(name,slot)
report['accepted_vertical_and_idle_unchanged']=True
assert sc['world']['frame_mapping']==sc['story']['frame_mapping']
assert sc['world']['output_atlas']==sc['story']['output_atlas']
report['world_reuses_story_exact_paths']=True
for name in sc:
    for key in ['source_atlas','source_frame_size','source_anchor','directions','direction_mirror_x','timing','idle']:
        assert sc[name].get(key)==before[name].get(key),(name,key)
report['source_directions_anchors_and_timing_unchanged']=True
palette={(23,38,56),(57,118,181),(228,225,200),(221,167,125)};paths=set()
inventory=[]
for name,s in sc.items():
    for f in s['frame_mapping']:
        p=(M/f['path']).resolve();image=im(p);assert set(image.getchannel('A').getdata())=={0,255}
        assert {c[:3]for c in image.getdata()if c[3]}==palette
        assert list(image.size)==[n*4 for n in s['source_frame_size']]
        assert sha(p)==f['sha256'];paths.add(str(p.relative_to(R)))
    atlas=im(M/s['output_atlas'])
    assert atlas.size==(len(s['frame_mapping'])*s['output_frame_size'][0],s['output_frame_size'][1])
report['unique_sprite_files']=len(paths);report['palette_opaque_colors']=4;report['binary_alpha']=True
story_a=im(V/'deliverables/story-04.png');story_b=im(V/'deliverables/story-05.png')
assert same(story_a,story_b,(0,0,128,58))
assert same(story_a,story_b,(69,59,76,65))and same(story_a,story_b,(66,74,80,81))
arm_changes={name:delta(story_a,story_b,box)for name,box in [('rear_forearm_hand',(48,65,66,78)),('front_forearm_hand',(76,63,92,78))]}
assert all(n>10 for n in arm_changes.values()),arm_changes
skin=(221,167,125,255)
hand_shapes=[]
for image in [story_a,story_b]:
    sets=[]
    for x0,y0,x1,y1 in [(48,65,66,78),(76,63,92,78)]:
        pts=[(x,y)for y in range(y0,y1)for x in range(x0,x1)if image.getpixel((x,y))==skin]
        assert len(pts)>=10
        sets.append({'pixels':len(pts),'centroid':[round(sum(p[k]for p in pts)/len(pts),2)for k in [0,1]]})
    hand_shapes.append(sets)
assert hand_shapes[0][0]['centroid']!=hand_shapes[1][0]['centroid']
assert hand_shapes[0][1]['centroid']!=hand_shapes[1][1]['centroid']
report['story_side']={'head_equal':True,'exposed_torso_equal':True,'forearm_hand_changed_pixels':arm_changes,'hand_positions':hand_shapes}
a=im(V/'deliverables/tactical-02.png');b=im(V/'deliverables/tactical-03.png')
assert same(a,b,(0,0,128,54)) and same(a,b,(0,0,70,78))
shield_counts=[sum(p==(57,118,181,255)for p in image.crop((70,56,92,78)).getdata())for image in [a,b]]
assert min(shield_counts)>=40 and delta(a,b,(70,56,92,78))>20,shield_counts
for dst,src in [(6,3),(7,2)]:
    assert im(V/f'deliverables/tactical-{dst:02}.png').tobytes()==im(V/f'deliverables/tactical-{src:02}.png').transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes()
report['tactical_side']={'head_sword_and_sword_arm_equal':True,'shield_blue_area_each_phase':shield_counts,'shield_region_changed_pixels':delta(a,b,(70,56,92,78)),'left_cross_phase_mirror_exact':True}
report['backgrounds']=[]
for item in read(V/'background-provenance.json'):
    assert sha(R.parents[1]/item['source_atlas'])==item['source_sha256']
    p=V/item['output'];image=im(p);assert image.size==(64,48)and image.getchannel('A').getextrema()==(255,255)
    report['backgrounds'].append({'name':item['name'],'native_size':list(image.size),'source_atlas':item['source_atlas'],'bytes':p.stat().st_size})
D=read(R/'demos/gallery-data.json');actions={a['id']:a for a in D['actions']};profiles={p['id']:p for p in D['profiles']}
videos=[]
for ident in read(V/'export-selection.json'):
    a=actions[ident];p=R/'demos/videos'/f'{ident}.mp4';meta=read(p.with_suffix('.json'))
    assert a['ready']and a['video']and a['still']and meta['contentDigest']==a['contentDigest'],ident
    info=probe(p);assert int(info['nb_frames'])==len(a['frames'])and abs(float(info['duration'])-a['duration'])<.03
    profile=profiles[a['profile']]
    for path in [profile['sourceAtlas'],profile['mapGround'],profile['mapShadow']['path'],*profile['newFrames'].values()]:assert (R/path).is_file(),path
    videos.append({'action':ident,**info})
report['videos']=videos;report['overview']=probe(V/'overview.mp4');assert int(report['overview']['nb_frames'])==1240
subprocess.run([shutil.which('node')or'/opt/homebrew/bin/node','--check',str(R/'tools/gallery.js')],check=True,capture_output=True)
report['gallery_javascript_syntax']='passed'
report['visual_inspection']='Both side phases, both directions, dark/light/project grounds; complete sleeves/hands, shield faces, transparency and comparison text padding checked offline. User acceptance pending.'
inventory=read(V/'image-inventory.json')
for p in [*V.glob('reference/grounds/*[!0-9].png'),*V.glob('reviews/*.png')]:
    if '-tile-'in p.name:continue
    inventory.append({'purpose':'comparison background or review','path':str(p.relative_to(R)),'size':list(im(p).size),'bytes':p.stat().st_size,'sha256':sha(p)})
(V/'image-inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n')
(V/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'protected_files':len(baseline),'accepted_vertical_idle_unchanged':True,'world_shared_story':True,'story_hand_changes':arm_changes,'shield_blue_pixels':shield_counts,'videos':len(videos),'overview_frames':report['overview']['nb_frames'],'pass':True},ensure_ascii=False))
