from pathlib import Path
from PIL import Image,ImageDraw
import json,shutil,hashlib
import register_native_walk as m
R=Path(__file__).resolve().parent;P=R.parent;B=R.parents[2]
def read(p):return json.loads(p.read_text())
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
d=read(R/'frame_mapping.json');records=read(R/'source/native-walk-registration.json');overlay=read(B/'source-input/corrected-tactical-walk/overlay.json');meta=overlay['records']['class-12-enemy']
approved=bool(next(s for s in d['scenarios'] if s['id']=='tactical-walk').get('parent_visual_review_passed',False) and next(s for s in d['scenarios'] if s['id']=='tactical-walk').get('source_audit',{}).get('status')=='verified_native_tactical')
atlas=Image.new('RGBA',(1024,96));checks=[]
for r in records:
    f=R/r['path'];im=Image.open(f).convert('RGBA');assert im.size==(128,96) and m.sha(f)==r['sha256'];fb=m.foot_box(im,r['output_foot_roi']);actual=[(fb[0]+fb[2])/2,fb[3]];assert actual==r['registered_foot_anchor'];assert abs(r['foot_delta'][0])<=.5 and abs(r['foot_delta'][1])<=1;atlas.alpha_composite(im,(r['source_index']*128,0));checks.append({'slot':r['source_index'],'target':r['target_foot_anchor'],'actual':actual,'delta':r['foot_delta']})
out=R/'frames/tactical-native-walk.png';atlas.save(out,optimize=True);m.compress(out)
src=Image.open(B/'source-input/corrected-tactical-walk/class-12-enemy.png').convert('RGBA');mirrors=[]
for i,j in [(2,6),(3,7)]:
    a=src.crop((i*32,0,(i+1)*32,24));b=src.crop((j*32,0,(j+1)*32,24)).transpose(Image.Transpose.FLIP_LEFT_RIGHT);na=Image.open(R/records[i]['path']).convert('RGBA');nb=Image.open(R/records[j]['path']).convert('RGBA').transpose(Image.Transpose.FLIP_LEFT_RIGHT);assert a.size==b.size and a.tobytes()==b.tobytes() and na.size==nb.size and na.tobytes()==nb.tobytes();mirrors.append({'slot':i,'mirror_of':j,'source_and_output_size_rgba_exact':True})
frozen=read(R/'source/pre-native-walk-frozen-sha256.json');assert all(m.sha(P/f)==h for f,h in frozen.items())
audit={'status':'verified_native_tactical','source_chr':26,'record_key':'class-12-enemy','overlay':'../../../source-input/corrected-tactical-walk/overlay.json','verification':'../../../source-input/corrected-tactical-walk/verification.json','cpu_entry':overlay['entry'],'caller':overlay['caller'],'native_render':overlay['native_render'],'old_source_status':'Historical village-table/CHR26 hybrid, retained. Native7 matches old0 under exact palette bijection, but old rendered slack-bow interpretation was incorrect and is not reused.'}
scenario={'id':'tactical-walk','class_id':12,'source_side':'enemy','character_id':'enemy-archer','display_name':'敌方弓箭手','source_atlas':'../../../source-input/corrected-tactical-walk/class-12-enemy.png','source_frame_size':[32,24],'source_anchor':[16,24],'source_columns':8,'output_atlas':'frames/tactical-native-walk.png','output_frame_size':[128,96],'output_anchor':[64,96],'logical_render_scale':.25,'output_atlas_bytes':out.stat().st_size,'frame_mapping':records,'directions':meta['directions'],'direction_mirror_x':{},'timing':meta['timing'],'static_facing':False,'source_audit':audit,'proven_mirror_pairs':[[2,6],[3,7]],'mirror_note':'CPU mirroring already baked; no additional enemy XOR or direction mirror. Phase is preserved.','parent_visual_review_passed':approved,'qa_report':'native-walk-qa-report.json'}
idle_before=next(s for s in d['scenarios'] if s['id']=='tactical-idle');d['scenarios']=[scenario if s['id']=='tactical-walk' else s for s in d['scenarios']];assert next(s for s in d['scenarios'] if s['id']=='tactical-idle')==idle_before;write(R/'frame_mapping.json',d)
semantic={'conclusion':'Native tactical walking uses a southeast drawn bow with one nocked arrow in unmirrored left6/7 and front4/5. Rear0/1 hides most bow and arrow behind torso. Static idle remains separately verified northeast drawn stance.','native7_landmarks':{'upper_NE_tip':[20,12],'lower_SW_tip':[12,21],'draw_point':[13,13],'arrow_axis':[[15,15],[16,16],[17,17],[18,18]]},'evidence':['../reference/native-walk-bow-rotation-evidence.png','../reference/corrected-native-four-directions.png'],'independent_review':'source_catalog independently confirmed two-string/outer-arc topology; old slack-bow art rejected despite native old0/new7 geometric match.','map_projectile_event_added':False,'logical_direction_is_not_forced_graphic_face':True,'scope':'Visible source topology and occlusion; no invented hidden anatomy.'}
write(R/'source/native-walk-semantic-audit.json',semantic)
inventory=[]
for f in [R/r['path'] for r in records]+[out]:inventory.append({'path':str(f.relative_to(R)),'size':list(Image.open(f).size),'bytes':f.stat().st_size,'sha256':m.sha(f),'compression':'oxipng lossless, no palette quantization'})
write(R/'native-walk-image-inventory.json',inventory)
qa={'status':'complete_art_review_passed' if approved else 'agent_visual_qa_passed_parent_review_pending','parent_visual_review_passed':approved,'class_id':12,'source_side':'enemy','character_id':'enemy-archer','unique_imagegen_poses':6,'output_slots':8,'source_frame_size':[32,24],'output_frame_size':[128,96],'source_audit':audit,'semantic_audit':semantic,'support_boot_xy_checks':checks,'registration_scope':'Only selected support sole center/baseline rounding error is quantified, not every limb/joint. Rear toe and boot contours also inspected visually. Uniform scaling and rigid translation; no body clamp.','mirror_checks':mirrors,'frozen_battle_idle_sha256':frozen,'static_idle_scenario_preserved':True,'raw_generations_preserved':True,'source_prompts':'source/native-walk-prompts.md','old_mapping_backup':'source/previous-map-frame_mapping.json','max_independent_frame_bytes':max(r['bytes'] for r in records),'atlas_bytes':out.stat().st_size,'deep_light_review_complete':True,'timing':meta['timing'],'runtime_integration':False,'godot_started':False,'this_agent_writes_actual':False}
write(R/'native-walk-qa-report.json',qa)
oldqa=P/'qa-report.json';backup=R/'source/previous-profession-qa-report.json'
if not backup.exists():shutil.copyfile(oldqa,backup)
q=read(oldqa);q.update(current_native_tactical_walk='maps/native-walk-qa-report.json',unique_map_walk_poses=6,native_walk_source_verified=True,native_walk_parent_visual_review_passed=approved,historical_tactical_walk_reference_status='Prior CHR26/village-table walk source and slack-bow art superseded; retained only as history.');write(oldqa,q)
ids=['professions-class-12-enemy-maps-tactical-walk--'+kind+'-'+direction for direction in meta['directions'] for kind in ['walk','idle']];write(R/'native-walk-gallery-action-ids.json',ids)
for theme,bg,fg in [('light','#e9e4d9','#26333a'),('dark','#1d2b35','#edf0e7')]:
    frames=[]
    for phase in [0,1]:
        board=Image.new('RGBA',(1096,470),bg);dr=ImageDraw.Draw(board);dr.text((16,8),'敌弓兵原生四向 · 原CPU / 新图 · 每相16 ticks',font=m.FONT,fill=fg)
        for col,(direction,order) in enumerate(meta['directions'].items()):
            i=order[phase];x=16+col*268;board.alpha_composite(src.crop((i*32,0,(i+1)*32,24)).resize((256,192),Image.Resampling.NEAREST),(x,38));board.alpha_composite(Image.open(R/records[i]['path']).convert('RGBA').resize((256,192),Image.Resampling.NEAREST),(x,258));dr.text((x+96,232),direction,font=m.FONT,fill=fg)
        frames.append(board.convert('RGB'))
    frames[0].save(R/f'reviews/tactical-native-four-directions-{theme}.gif',save_all=True,append_images=frames[1:],duration=[270,260],loop=0,disposal=2,optimize=True);frames[0].save(R/f'reviews/tactical-native-four-directions-{theme}.png',optimize=True)
print('8 native frames registered;',len(frozen),'battle/idle PNG unchanged; max',qa['max_independent_frame_bytes'],'bytes; atlas',out.stat().st_size)
