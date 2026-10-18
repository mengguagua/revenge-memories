"""Update male gallery mappings only; world explicitly shares story artwork."""
from pathlib import Path
from PIL import Image
import json,subprocess,os,hashlib,copy
V=Path(__file__).resolve().parents[1];R=V.parent;M=R/'hunapu/maps';G='/opt/homebrew/bin/magick'
def run(*args):subprocess.run([G,*map(str,args)],check=True)
def read(p):return json.loads(p.read_text())
def info(p):return {'size':list(Image.open(p).size),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
mapping=read(M/'frame_mapping.json');prior=read(V/'reference/hunapu-mapping-before.json')
scenes={s['id']:s for s in mapping['scenarios']}
for name,slots in [('story',[4,5]),('tactical-walk',[2,3,6,7])]:
    sc=scenes[name];prefix='story'if name=='story'else'tactical'
    for slot in slots:
        path=V/f'deliverables/{prefix}-{slot:02}.png'
        subprocess.run(['/opt/homebrew/bin/oxipng','-o','4','--strip','safe',str(path)],capture_output=True,check=True)
        f=next(f for f in sc['frame_mapping']if f['source_index']==slot)
        rel=os.path.relpath(path,M)
        f.update(path=rel,output_path=rel,revision='hero-map-v3-side-arms',generated_sheet=os.path.relpath(V/'source/side-edit-v2.png',M),art_review_status='awaiting_user_review',**info(path))
        f['edit_provenance']=os.path.relpath(V/'README.md',M)
        f['generated_slot']=({4:0,5:1}if name=='story'else{2:2,3:3,6:3,7:2})[slot]
        f['generated_sources']=[os.path.relpath(V/f'source/side-edit-v{i}.png',M)for i in ([1,2]if name=='story'and slot==5 else[2])]
        f.pop('fixed_layer_contract',None)
        f['assembly_recipe']=os.path.relpath(V/'tools/assemble_sides.py',M)
    atlas=V/f'deliverables/{name}-atlas.png'
    run(*[M/f['path']for f in sc['frame_mapping']],'+append',atlas)
    subprocess.run(['/opt/homebrew/bin/oxipng','-o','4','--strip','safe',str(atlas)],capture_output=True,check=True)
    sc.update(output_atlas=os.path.relpath(atlas,M),output_atlas_bytes=atlas.stat().st_size)

# Preserve the world source/timing/direction contract, but share the actual story
# bitmap paths (not a second independently generated copy).
for key in ['frame_mapping','output_atlas','output_atlas_bytes','output_frame_size','output_anchor','logical_render_scale','palette','ground_shadow']:
    scenes['world'][key]=copy.deepcopy(scenes['story'][key])
for name in ['story','world']:
    sc=scenes[name];sc['shared_artifact']='v3-story-world-identical-frames'
    sc['explicit_left_frames']=[]
    for slot in [4,5]:
        path=V/f'deliverables/story-{slot:02}-left.png'
        run(V/f'deliverables/story-{slot:02}.png','-flop',path)
        sc['explicit_left_frames'].append({'path':os.path.relpath(path,M),'source_index':slot,'derived_from':os.path.relpath(V/f'deliverables/story-{slot:02}.png',M),'transform':'horizontal-mirror-about-frame-center',**info(path)})

notes={
 'story':'剧情地图：保留已确认的上下行走；左右行走修正完整袖子、前臂与手掌的摆动；四种主体色，头部固定。背景取本项目P00石板地面。',
 'world':'大地图：与剧情地图共用完全相同的六张人物帧和四向动作；背景取本项目正式世界地图W02附近道路。',
 'tactical-walk':'战斗地图：保留已确认的上下行走；左右补全蓝色盾面，盾与持盾手臂同步摆动，持剑手和头身固定。背景取本项目M11部署区。',
 'tactical-idle':'待机人物保留上一版约90%尺寸和原动作；仅将对照背景换为本项目M11部署区。'}
grounds={'story':'story-P00-cobble','world':'world-W02-route','tactical-walk':'tactical-M11','tactical-idle':'tactical-M11'}
inventory=[]
for name,sc in scenes.items():
    sc.update(revision='hero-map-v3-side-arms',review_note=notes[name],art_review_status='awaiting_user_review',
        preview_ground=str((V/f'reference/grounds/{grounds[name]}.png').relative_to(R)),
        motion_review=str((V/'verification.json').relative_to(R)),parent_visual_review_passed=False)
    # Retire stale legacy previews that no longer represent these bitmaps.
    sc.pop('preview_dark',None);sc.pop('preview_light',None)
    if name=='tactical-idle':
        sc['adaptation_note']='Preserved v2-size2 idle artwork and timing; ivory-rimmed blue shield; four-color palette.'
    for f in sc['frame_mapping']:
        p=(M/f['path']).resolve();inventory.append({'purpose':name,'frame':f['source_index'],'path':str(p.relative_to(R.resolve())),**info(p)})
    atlas=(M/sc['output_atlas']).resolve();inventory.append({'purpose':name+' atlas','path':str(atlas.relative_to(R.resolve())),**info(atlas)})
    sc['preview_video']=f'../../demos/videos/hunapu-maps-{name}--'+('idle-cycle.mp4'if name=='tactical-idle'else'walk-right.mp4')
    # Keep every original motion sequence, frame tick and source atlas unchanged.
    old=next(s for s in prior['scenarios']if s['id']==name)
    for key in ['source_atlas','source_frame_size','source_anchor','directions','direction_mirror_x','timing','idle']:
        assert sc.get(key)==old.get(key),(name,key)
mapping['latest_map_revision']={'id':'hero-map-v3-side-arms','status':'awaiting_user_review','scope':list(scenes),'record':'../../map-motion-review-v3/README.md','world_shares_story':True,'battle_scene_unchanged':True}
mapping['parent_visual_review_passed']=False
(M/'frame_mapping.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n')
(V/'image-inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n')
print('Published male side edits, identical story/world sprites and correct project backgrounds')
