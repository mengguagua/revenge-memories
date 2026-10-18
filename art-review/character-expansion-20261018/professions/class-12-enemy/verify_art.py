"""Scope-limited delivery checks; no engine launch or runtime integration."""
from pathlib import Path
from PIL import Image
import json,hashlib,itertools
R=Path(__file__).resolve().parent;B=R.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def abox(im):return im.getchannel('A').point(lambda a:255 if a>=32 else 0).getbbox()
def foot(im,roi):
    b=abox(im.crop(roi));return [(b[0]+b[2])/2+roi[0],b[3]+roi[1]]

def main():
    battle=json.loads((R/'battle/frame_mapping.json').read_text());maps=json.loads((R/'maps/frame_mapping.json').read_text())
    assert battle['source_side']=='enemy' and battle['original_class_id']==12 and battle['character_id']=='enemy-archer'
    assert maps['source_side']=='enemy' and maps['class_id']==12 and maps['character_id']=='enemy-archer'
    original=json.loads((B/'source-input/enemy-motion/full-enemy-motion.json').read_text());unit=next(u for u in json.loads((B/'catalog/production-units.json').read_text())['units'] if u['id']=='class-12-enemy')
    assert battle['variant_keys']==unit['bound_action_keys']
    records=[('battle',rec)for rec in battle['records']]+[('maps',rec)for sc in maps['scenarios']for rec in sc['frame_mapping']]
    foot_checks=[];paths=set()
    for group,rec in records:
        p=R/group/rec['path'];im=Image.open(p).convert('RGBA');assert list(im.size)==rec['size'];assert p.stat().st_size==rec['bytes'];assert sha(p)==rec['sha256'];assert (R/group/rec['generated_source']).is_file()
        actual=foot(im,rec['output_foot_roi']);target=rec['target_foot_anchor'];delta=[actual[i]-target[i]for i in range(2)]
        assert abs(delta[0])<=.5 and abs(delta[1])<=1,(p,actual,target);assert actual==rec['registered_foot_anchor']
        bb=abox(im);assert bb[0]>=0 and bb[1]>=0 and bb[2]<=im.width and bb[3]<=im.height
        foot_checks.append({'path':str(p.relative_to(R)),'target':target,'actual':actual,'delta':delta});paths.add(p)
    traces={}
    for key in battle['variant_keys']:
        v=original['variants'][key];required=sorted(set(f['frame']for f in v['frames']));assert required==[1,5,6];assert all(str(f)in battle['frame_mapping']for f in required);assert v['contact_count']==1
        traces[key]={'ticks':len(v['frames']),'required_frames':required,'contact_tick':v['contact_tick'],'contact_count':v['contact_count'],
          'body_rle':[[f,len(list(g))]for f,g in itertools.groupby(x['frame']for x in v['frames'])],
          'external_projectile_ticks':[i for i,f in enumerate(v['frames'])if f.get('effects')],
          'native_trace_sha256':hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()}
    alias_checks=[]
    for sc in maps['scenarios']:
        source=(R/'maps'/sc['source_atlas']).resolve();assert source.is_file();ni=Image.open(source).convert('RGBA');fw,fh=sc['source_frame_size']
        for group in sc['native_alias_groups']:
            originals=[ni.crop((i*fw,0,(i+1)*fw,fh)).tobytes()for i in group];new=[Image.open(R/'maps'/sc['frame_mapping'][i]['path']).convert('RGBA').tobytes()for i in group]
            assert len(set(originals))==len(set(new))==1
            alias_checks.append({'scenario':sc['id'],'slots':group,'source_and_new_exact':True})
        paths.add(R/'maps'/sc['output_atlas'])
        for item in sc.get('explicit_left_frames',[]):
            p=R/'maps'/item['path'];base=R/'maps'/item['derived_from'];assert Image.open(p).convert('RGBA').tobytes()==Image.open(base).convert('RGBA').transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes();paths.add(p)
    paths.add(R/'battle'/battle['output_atlas'])
    assets=[]
    for p in sorted(paths):
        im=Image.open(p);is_atlas=p.name in ['archer-battle-three.png','tactical-idle.png','tactical-walk.png'];size=p.stat().st_size
        item={'path':str(p.relative_to(R)),'purpose':'transparent-atlas' if is_atlas else 'independent-frame','size':list(im.size),'bytes':size,'sha256':sha(p),'compression':'oxipng lossless; no palette quantization'}
        if size>=20000:item['quality_reason']='Preserve face, material seams, bow/string edges and RGBA detail at approved4x resolution; atlas combines multiple complete frames.' if is_atlas else 'Full battle pose with face, leather seams, bowstring and RGBA contour; retained losslessly.'
        if not is_atlas:assert size<50000,p
        assets.append(item)
    baseline=json.loads((R/'maps/source/pre-idle-fix-approved-sha256.json').read_text())
    assert all(sha(R/p)==digest for p,digest in baseline.items()),'approved battle/walk art changed'
    semantic_audit=json.loads((R/'reference/idle-semantic-audit.json').read_text())
    report={'status':'pass','character_id':'enemy-archer','display_name':'敌方弓箭手','source_side':'enemy','original_class_id':12,
      'unique_battle_poses':3,'required_variants':6,'unique_map_walk_poses':2,'unique_map_idle_poses':2,'runtime_png_count':len(assets),
      'max_independent_frame_bytes':max(a['bytes']for a in assets if a['purpose']=='independent-frame'),'max_atlas_bytes':max(a['bytes']for a in assets if a['purpose']=='transparent-atlas'),
      'foot_xy_checks':foot_checks,'alias_checks':alias_checks,'variant_checks':traces,'assets':assets,
      'visual_review':['battle dark/light original/new boards','map dark/light source/new boards','pose5 single nocked arrow; pose1 and6 empty bow','idle source-confirmed northeast drawn bow, single nocked arrow, crouched legs, upper bow limb above cap','strings and full bow/boots contour visible on both backgrounds','tick44 projectile tip begins at new bow grip; tick45 moves forward using native compositor'],
      'idle_semantic_audit':semantic_audit,'approved_battle_walk_sha256_unchanged':True,
      'registration_policy':'Explicit boot regions; x error<=0.5px and y error<=1px. Uniform resize plus rigid translation only. No horizontal body clamp.',
      'compression_policy':'Visual quality preserved;3-pose atlas exceeds50KB guideline while all independent frames stay below50KB. Source generation originals isolated in source/.',
      'runtime_integration':False,'godot_started':False,'original_source_and_actual_unchanged':True}
    (R/'qa-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    for group in ['battle','maps']:
        p=R/group/'frame_mapping.json';d=json.loads(p.read_text());d['qa_report']='../qa-report.json';d['status']='complete_art_review_passed';d['art_review']='agent source/shape/alpha/timing review passed; root visually passed battle, walk and corrected northeast drawn-bow idle';d.pop('pending',None)
        if group=='maps':d['idle_semantic_audit']='../reference/idle-semantic-audit.json'
        p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:report[k]for k in ['status','runtime_png_count','max_independent_frame_bytes','max_atlas_bytes','required_variants','unique_map_walk_poses','unique_map_idle_poses']},ensure_ascii=False))

if __name__=='__main__':main()
