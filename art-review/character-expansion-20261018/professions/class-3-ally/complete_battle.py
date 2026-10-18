"""Package already generated art and compose original effects; no art drawing."""
from pathlib import Path
import sys,json,shutil,hashlib,itertools
from PIL import Image
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parent;B=R.parents[1];sys.path.insert(0,str(B/'tools'))
from build_gallery import pack_frame,close_camera
from export_gallery import render_frame
import register_art as m
r=R/'battle';mapping=json.loads((r/'frame_mapping.json').read_text());native=Image.open(B/'source-input/original-motion/class-3.png').convert('RGBA')
canonical=[0,1,2,3,4,5,6,7,34,35]
for i in canonical:assert str(i)in mapping['frame_mapping']
for i in [16,33]:
    assert native.crop((i%16*80,i//16*96,(i%16+1)*80,(i//16+1)*96)).tobytes()==native.crop((0,0,80,96)).tobytes()
    p=r/f'frames/frame-{i:03}.png';shutil.copyfile(r/mapping['frame_mapping']['0'],p);mapping['frame_mapping'][str(i)]=str(p.relative_to(r));rec={**next(x for x in mapping['records']if x['source_frame']==0),'source_frame':i,'representative_frame':0,'kind':'native_exact_pixel_alias','path':str(p.relative_to(r))};mapping['records']=[x for x in mapping['records']if x['source_frame']!=i]+[rec]
atlas=Image.new('RGBA',(320*len(canonical),384))
for col,i in enumerate(canonical):atlas.alpha_composite(Image.open(r/mapping['frame_mapping'][str(i)]).convert('RGBA'),(col*320,0))
out=r/'frames/ally-pegasus-battle-ten.png';atlas.save(out,optimize=True);m.compress(out)
mapping.update(output_atlas=str(out.relative_to(r)),output_atlas_order=canonical,output_atlas_bytes=out.stat().st_size,status='all_battle_frames_candidate',registration_scope='Foot XY error measures only each explicitly selected native hoof anchor after uniform scaling and rigid translation, not every limb or joint. Other limbs, feathers and spear poses are separately inspected visually.')
mapping['records']=sorted(mapping['records'],key=lambda x:x['source_frame']);mapping['batches']=[{'id':'keyposes','frames':[0,3,7],'root_review':'passed'},{'id':'flight-a','frames':[1,2],'root_review':'passed'},{'id':'flight-b','frames':[4,5],'root_review':'pending'},{'id':'attack-throw','frames':[6,34,35],'root_review':'pending'}]
(r/'frame_mapping.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n')
vdata=json.loads((r/'native-action-variants.json').read_text());effects=json.loads((B/'source-input/effects.json').read_text());eid='3d558f7aa86343';effect=effects[eid];shutil.copyfile(B/effect['path'],r/f'source/native-javelin-{eid}.png')
P={'sourceAtlas':'source-input/original-motion/class-3.png','sourceFrameSize':[80,96],'sourceColumns':16,'anchor':[40,72],'sourceOamCutoff':16,'flipOriginOffset':[16,0],'newFrames':{k:str((r/v).relative_to(B))for k,v in mapping['frame_mapping'].items()},'side':'ally','context':'battle','actorName':'盟军天马骑士'}
D={'effects':effects,'viewport':[-16,-32,288,176]};checks={}
for key,v in vdata['variants'].items():
    fs=v['frames'];assert all(str(f['frame'])in mapping['frame_mapping']for f in fs);assert v['contact_count']==1
    checks[key]={'native_ticks':len(fs),'contact_tick':v['contact_tick'],'contact_count':v['contact_count'],'body_rle':[[f,len(list(g))]for f,g in itertools.groupby(x['frame']for x in fs)],'effect_ticks':[i for i,f in enumerate(fs)if f.get('effects')],'native_trace_sha256':hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()}
    if key=='class_3_ally_javelin':
        A={'origin':v['actor_origin'],'frames':[pack_frame(f)for f in fs],'context':'battle','name':'投枪释放与原外置枪','fps':60.0988};A['closeCamera']=close_camera(P,A)
        for tick in [17,18,21,22]:
            for theme,light in [('dark',False),('light',True)]:render_frame(D,P,A,tick,scale=4,light=light,close=True).save(r/f'reviews/native-javelin-tick-{tick:03}-{theme}.png',optimize=True)
checks['external_effect']={'id':eid,'metadata':effect,'preserved_path':f'source/native-javelin-{eid}.png','sha256':m.sha(r/f'source/native-javelin-{eid}.png'),'policy':'Original external projectile, positions and tick list preserved. Body35 contains no held spear. No additional attack/contact.'}
(r/'timing-qa.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
ids={'battle':['professions-class-3-ally-battle--'+k for k in mapping['variant_keys']]+['professions-class-3-ally-battle--reaction-'+k for k in ['idle','miss','hit','exit']],'maps':['professions-class-3-ally-maps-tactical-idle--idle-cycle'],'pending':['corrected tactical-walk source and art']}
(R/'gallery-action-ids.json').write_text(json.dumps(ids,ensure_ascii=False,indent=2)+'\n')
print('battle complete; atlas bytes',out.stat().st_size,'variants',len(vdata['variants']))
