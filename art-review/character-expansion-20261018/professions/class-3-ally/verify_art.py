"""Validate assigned offline art only. No game launch or runtime writes."""
from pathlib import Path
import json,hashlib
from PIL import Image
import register_art as m
R=Path(__file__).resolve().parent;B=R.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def same(a,b):return a.size==b.size and a.tobytes()==b.tobytes()
def main():
    battle=json.loads((R/'battle/frame_mapping.json').read_text());maps=json.loads((R/'maps/frame_mapping.json').read_text())
    assert battle['original_class_id']==maps['class_id']==3
    assert battle['source_side']==maps['source_side']=='ally'
    assert battle['character_id']==maps['character_id']=='ally-pegasus-rider'
    unit=next(u for u in json.loads((B/'catalog/production-units.json').read_text())['units']if u['id']=='class-3-ally');assert battle['variant_keys']==unit['bound_action_keys'];assert all(str(i)in battle['frame_mapping']for i in unit['required_source_frames'])
    checks=[];paths=set()
    for group,rec in [('battle',x)for x in battle['records']]+[('maps',x)for s in maps['scenarios']for x in s['frame_mapping']]:
        p=R/group/rec['path'];im=Image.open(p).convert('RGBA');assert list(im.size)==rec['size'];assert p.stat().st_size==rec['bytes'];assert sha(p)==rec['sha256'];assert(R/group/rec['generated_source']).is_file();b=m.foot_box(im,rec['output_foot_roi'],rec.get('anchor_is_anatomical_foot',True));at=[(b[0]+b[2])/2,b[3]];target=rec['target_foot_anchor'];delta=[at[i]-target[i]for i in range(2)];assert at==rec['registered_foot_anchor'];assert abs(delta[0])<=.5 and abs(delta[1])<=1
        bounds=m.box(im);assert bounds[0]>=0 and bounds[1]>=0 and bounds[2]<=im.width and bounds[3]<=im.height
        checks.append({'path':str(p.relative_to(R)),'anchor_kind':rec.get('anchor_kind','selected visible hoof'),'selected_hoof_target':target,'selected_hoof_actual':at,'rounding_delta':delta,'visible_bounds':bounds});paths.add(p)
    ni=Image.open(B/'source-input/original-motion/class-3.png').convert('RGBA');aliases=[]
    for i in [16,33]:
        assert same(ni.crop((0,0,80,96)),ni.crop((i%16*80,i//16*96,(i%16+1)*80,(i//16+1)*96)))
        assert same(Image.open(R/'battle'/battle['frame_mapping']['0']).convert('RGBA'),Image.open(R/'battle'/battle['frame_mapping'][str(i)]).convert('RGBA'));aliases.append({'battle_source':i,'representative':0,'dimensions_and_rgba_equal':True})
    for sc in maps['scenarios']:
        src=Image.open((R/'maps'/sc['source_atlas']).resolve()).convert('RGBA');w,h=sc['source_frame_size']
        for group in sc.get('native_alias_groups',[[0,4],[1,3,5],[2]]):
            assert len({src.crop((i*w,0,(i+1)*w,h)).tobytes()for i in group})==1
            new=[Image.open(R/'maps'/sc['frame_mapping'][i]['path']).convert('RGBA')for i in group];assert all(same(new[0],x)for x in new[1:]);aliases.append({'scenario':sc['id'],'slots':group,'dimensions_and_rgba_equal':True})
        paths.add(R/'maps'/sc['output_atlas'])
    paths.add(R/'battle'/battle['output_atlas'])
    frozen=json.loads((R/'battle/source/approved-keyposes-sha256.json').read_text());assert all(sha(R/p)==h for p,h in frozen.items())
    assets=[]
    for p in sorted(paths):
        im=Image.open(p);size=p.stat().st_size;is_atlas=p.name in ['ally-pegasus-battle-ten.png','tactical-idle.png','tactical-walk.png','tactical-native-walk.png'];a={'path':str(p.relative_to(R)),'size':list(im.size),'bytes':size,'purpose':'atlas'if is_atlas else'independent-frame','sha256':sha(p),'compression':'oxipng lossless; no palette quantization'}
        if size>=20000:a['quality_reason']='Preserve face, layered wing feathers, tack, spear and transparent contour at the accepted fourfold dimensions. Lossless PNG retained; root explicitly accepted quality-priority exceptions. Atlas combines complete independent frames.'
        assets.append(a)
    qa={'status':'complete_art_review_passed','character_id':'ally-pegasus-rider','unique_battle_poses':10,'required_battle_variants':7,'unique_map_idle_poses':3,'unique_map_walk_poses':6,'map_walk_slots':8,'map_walk_status':'verified bank011 CPU/CHR19 source; all body/wing phases and corrected weapon endpoints passed','selected_hoof_checks':checks,'alias_checks':aliases,'assets':assets,'max_independent_frame_bytes':max(a['bytes']for a in assets if a['purpose']=='independent-frame'),'max_atlas_bytes':max(a['bytes']for a in assets if a['purpose']=='atlas'),'registration_policy':'Errors above concern only selected semantic hoof ROI anchors after uniform resizing and rigid translation. They do not assert exact positions of all hooves, joints, wing tips or hands. Those silhouettes and occlusion layers were separately visually reviewed. No whole-body clamp or nonuniform anatomy stretch.','visual_review':['All ten battle source/new poses on dark and light backgrounds; root passed keyposes0/3/7, flight1/2, flight4/5 and attack6/34/35.','Pose3 isolated lower-left piece is far wing, not hoof; original CHR48/49/4A tile evidence retained.','Pose4 nose-left small piece is far wing.','Javelin35 empty hand, native external projectile copied and original per-tick positions retained.','All three idle wing/leg phases; root passed. Diagonal shaft ends are not hoof anchors.'],'no_runtime_integration':True,'godot_started':False,'this_agent_writes_actual':False,'source_art_mode':'Built-in ImageGen, full prompts and unselected original sources preserved. Endpoint-only correction uses ImageGen components and technical mask compositing, no drawn/recolored substitute.'}
    (R/'qa-report.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
    battle['status']='complete_battle_art_review_passed';battle['qa_report']='../qa-report.json'
    for b in battle['batches']:b['root_review']='passed'
    maps['status']='complete_art_review_passed';maps['qa_report']='../qa-report.json'
    for s in maps['scenarios']:s['review_status']='parent_visual_review_passed'
    (R/'battle/frame_mapping.json').write_text(json.dumps(battle,ensure_ascii=False,indent=2)+'\n');(R/'maps/frame_mapping.json').write_text(json.dumps(maps,ensure_ascii=False,indent=2)+'\n')
    inventory=[]
    for p in sorted(R.rglob('*.png')):
        im=Image.open(p);inventory.append({'path':str(p.relative_to(R)),'size':list(im.size),'bytes':p.stat().st_size,'mode':im.mode,'sha256':sha(p),'scope':'source/reference/review only'if not '/frames/'in str(p)and not'/idle-frames/'in str(p)else'delivery'})
    (R/'image-inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n');print(qa['status'],len(assets),qa['max_independent_frame_bytes'],qa['max_atlas_bytes'])
if __name__=='__main__':main()
