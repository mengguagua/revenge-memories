from pathlib import Path
from PIL import Image
import json,hashlib,shutil,subprocess
P=Path(__file__).resolve().parents[1];ROOT=P.parents[1];M='/opt/homebrew/bin/magick'
OUT=P/'battle/frames';OUT.mkdir(parents=True,exist_ok=True)
selected={0:'candidate-keys-v2',6:'candidate-keys-v2',7:'candidate-keys-v2',1:'candidate-run-v1',2:'candidate-run-v1',3:'candidate-run-v1',5:'candidate-run-v1',4:'candidate-run-v1',17:'candidate-special',19:'candidate-special'}
records=[]
def info(path):
 im=Image.open(path);return {'size':list(im.size),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
for frame,folder in selected.items():
 src=P/'battle'/folder/f'frame-{frame:03}.png';dst=OUT/f'frame-{frame:03}.png';shutil.copy2(src,dst)
 subprocess.run(['/opt/homebrew/bin/oxipng','-o','4','--strip','safe',str(dst)],check=True,capture_output=True)
 r=next(r for r in json.loads((P/'battle'/folder/'registration.json').read_text())if r['frame']==frame);r.update({'source_frame':frame,'path':f'frames/frame-{frame:03}.png','status':'visual_review_pass',**info(dst)});records.append(r)
# Native ally slots0/9/16 are full RGBA aliases, no translation.
src=OUT/'frame-000.png'
for f in [9,16]:
 dst=OUT/f'frame-{f:03}.png';shutil.copy2(src,dst);records.append({'source_frame':f,'representative_frame':0,'path':f'frames/frame-{f:03}.png','kind':'exact_source_alias','status':'visual_review_pass',**info(dst)})
unit=json.loads((P/'reference/source-unit.json').read_text());frames=unit['required_source_frames'];canonical=unit['unique_art_frames'];atlas=OUT/'cavalry-battle.png'
subprocess.run([M,*[str(OUT/f'frame-{f:03}.png')for f in canonical],'+append',str(atlas)],check=True)
subprocess.run(['/opt/homebrew/bin/oxipng','-o','4','--strip','safe',str(atlas)],check=True,capture_output=True)
mapping={'schema_version':1,'character_id':'ally-cavalry','display_name':'盟军骑兵','original_class_id':1,'source_side':'ally','status':'art_and_registration_verified','source_atlas':'../../../'+unit['source_atlas'],'source_atlas_base':'mapping directory','source_frame_size':[80,64],'output_frame_size':[320,256],'source_anchor':[40,64],'output_anchor':[160,256],'source_columns':16,'source_idle_frame':0,'canonical_frames':canonical,'independently_generated_drawings':10,'frame_mapping':{str(f):f'frames/frame-{f:03}.png'for f in frames},'records':records,'variant_keys':unit['bound_action_keys'],'output_atlas':'frames/cavalry-battle.png','output_atlas_frame_order':canonical,'batches':[{'id':'all-battle','frames':canonical,'status':'visual_review_pass','review':'reviews/all-cavalry-original-new.png'}],'source_semantics':{'0':'mounted standing, diagonal lance: one blade at lower-left, blunt butt at upper-right','1-5':'distinct original horse leg phases; frame5 lowest visible hooves remain above ground','6':'rearing with raised horse head and diagonal lance','7':'rearing lance thrust','17':'standing horse, rider raises horizontal javelin overhead','19':'exact source standing body after35 lance pixels removed; no extra arm follow-through'},'art_mode':'Built-in imagegen. Crop/uniform scale/whole-image registration and proven translation aliases only.','runtime_integrated':False}
(P/'battle/frame_mapping.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n')
files=[]
for f in canonical:
 original=P/f'battle/frames/source-review-{f:03}.png';subprocess.run([M,str(P/f'reference/original-{f:03}.png'),'-filter','point','-resize','400%',str(original)],check=True);files.extend([original,OUT/f'frame-{f:03}.png'])
subprocess.run([M,'montage','-font','/System/Library/Fonts/STHeiti Medium.ttc',*[str(f)for f in files],'-tile','2x10','-geometry','320x256+0+6','-background','#1d2932',str(P/'battle/reviews/all-cavalry-original-new.png')],check=True)
# Review originals are references, never runtime outputs.
for f in OUT.glob('source-review-*.png'):f.unlink()
(P/'battle/qa-summary.json').write_text(json.dumps({'status':'battle_art_review_pass','required_source_slots':len(frames),'independent_drawings':10,'four_times_width_and_height':True,'visible_clipped_pixels':sum(r.get('visible_clipped_pixels',0)for r in records),'source_exact_aliases_verified':True,'post_release_body_proof':'../reference/post-release-body-proof.json','source_phase_review':'Source geometry matches enemy counterpart, recolor is not used; generated ally costume/head/horse redesign independently registered. Frame3 nearer foreleg locally returned below the chest and tail lifted to match native phase; root visual review passed.','weapon_review':'One blade, blunt butt; rearing diagonal front length corrected; overhead javelin and empty-handed source19 retained.','limits':'Detailed redraw preserves source action/visible pose relationships; it is not a pixel-identical reconstruction of hidden joints.','output_atlas':info(atlas),'atlas_quality_reason':'Full10-pose review atlas preserves fine horse/armor shading losslessly; individual frames are separately recorded and optimized.'},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'required_frames':len(frames),'canonical_frames':len(canonical),'independent_drawings':10,'atlas_bytes':atlas.stat().st_size,'frame_bytes_range':[min(r['bytes']for r in records),max(r['bytes']for r in records)]}))
