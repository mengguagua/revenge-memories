from pathlib import Path
from PIL import Image
import json,hashlib,subprocess
M=Path(__file__).resolve().parents[1];P=M.parent;ROOT=P.parents[1]
def save(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
def info(p):return {'size':list(Image.open(p).size),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
ref=json.loads((M/'native-reference/source-record.json').read_text());records=json.loads((M/'tactical-native-registration.json').read_text())
idle=Image.open(M/'idle-frames/frame-000.png').convert('RGBA');outside=[idle.getpixel((x,y))[3]for y in range(idle.height)for x in range(idle.width)if y+16>=96 or x+16>=128]
assert not any(a>=32 for a in outside)
for r in records:
 r['art_review_status']='parent_visual_review_passed'
 if r['source_index']==4:r.update({'outside_nonzero_alpha_pixels':sum(a>0 for a in outside),'outside_alpha_max':max(outside,default=0),'visible_clipped_pixels_alpha32':0})
atlas=M/'frames/tactical-native-walk.png';subprocess.run(['/opt/homebrew/bin/oxipng','-o','4','--strip','safe',str(atlas)],capture_output=True,check=True)
path=M/'frame_mapping.json';j=json.loads(path.read_text());old=M/'source/previous-map-frame_mapping.json'
if not old.exists():save(old,j)
scenario={'id':'tactical-walk','class_id':15,'source_side':'enemy','character_id':'enemy-arcanist','display_name':'敌方妖术师','source_atlas':'../../../source-input/corrected-tactical-walk/class-15-enemy.png','source_frame_size':[32,24],'source_columns':8,'source_frame_count':8,'source_anchor':[16,24],'output_frame_size':[128,96],'output_anchor':[64,96],'output_atlas':'frames/tactical-native-walk.png','output_atlas_bytes':atlas.stat().st_size,'logical_render_scale':.25,'frame_mapping':records,'directions':ref['directions'],'direction_mirror_x':{},'default_facing':'down','timing':ref['timing'],'source_audit':{'status':'verified_native_tactical','proof':'../../../source-input/corrected-tactical-walk/verification.json','unit_evidence':'native-reference/source-record.json','entry':'bank011:L0BB5B1','source_chr':27},'art_review_status':'parent_visual_review_passed','registration_note':'Native tile-base anchor[16,24], not an anatomical foot. Redraws use visible continuous robe hem; hidden joints are not inferred.','alias_note':'Slots6/7 mirror2/3 by exact full-canvas RGBA source proof. Slot4 exactly reuses approved staticidle0 translated+16,+16 output pixels.'}
j['scenarios']=[scenario if s['id']=='tactical-walk'else s for s in j['scenarios']];j['source_note']='Old village-OAM/CHR26 hybrid archived; true tactical source independently verified against native CPU and ROM tables. Static idle and battle unchanged.';save(path,j)
qa={'status':'parent_visual_review_passed','source_verified':True,'slots':8,'generated_drawings':5,'verified_static_reuse':1,'exact_source_mirrors':2,'references':['native-reference/source-record.json','../../../source-input/corrected-tactical-walk/verification.json'],'semantic_checks':['Back hood/ivory nape cloth has no front face or pendant.','Side ivory U-collar extension remains fabric, not an upright bare arm; right-phase1 raised cuff draft rejected and lowered with ImageGen.','Front arms/robe folds follow two source phases; legs remain hidden.'],'alpha_policy':'All generated in-canvas alpha preserved. Registration crops only outer transparent/low-alpha fringe, records visible alpha>=32 clipping; staticreuse outside pixels separately counted.','static_reuse_clipping':next(r for r in records if r['source_index']==4),'individual_bytes_range':[min(r['bytes']for r in records),max(r['bytes']for r in records)],'atlas':info(atlas),'review_boards':['reviews/native-walk-light.png','reviews/native-walk-dark.png'],'runtime_integrated':False};save(M/'tactical-native-qa.json',qa)
items=[]
for s in j['scenarios']:
 paths=sorted(set([s['output_atlas']]+[r.get('output_path',r.get('path'))for r in s['frame_mapping']]))
 for rel in paths:items.append({'purpose':s['id'],'path':rel,**info(M/rel)})
save(M/'delivery-inventory.json',{'scope':'current deliverables only; rejected/old-source art preserved offline','files':items})
print(json.dumps({'status':'verified_native_tactical','atlas_bytes':atlas.stat().st_size,'static_outside_alpha_max':max(outside,default=0)}))
