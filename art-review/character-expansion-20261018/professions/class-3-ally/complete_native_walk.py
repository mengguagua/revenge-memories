from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,shutil
import register_art as m
R=Path(__file__).resolve().parent;B=R.parents[1];r=R/'maps';p=r/'frame_mapping.json'
backup=r/'source/previous-map-frame_mapping.json'
if not backup.exists():shutil.copyfile(p,backup)
d=json.loads(p.read_text());records=json.loads((r/'source/native-walk-registration.json').read_text());overlay=json.loads((B/'source-input/corrected-tactical-walk/overlay.json').read_text());src=overlay['records']['class-3-ally'];ni=Image.open(B/'source-input/corrected-tactical-walk/class-3-ally.png').convert('RGBA')
for i,j in [(2,6),(3,7)]:
    base=next(x for x in records if x['source_index']==j);rec=next(x for x in records if x['source_index']==i);out=r/rec['path'];im=Image.open(out).convert('RGBA');roi=base['output_foot_roi'];nroi=base['native_hoof_roi'];nf=ni.crop((i*32,0,(i+1)*32,24));shadow=nf.crop((0,22,32,24));shadow_file=r/f'source/native-shadow-{i:03}.png';shadow.save(shadow_file,optimize=True)
    rec.update({k:v for k,v in base.items()if k not in rec})
    rec.update(output_foot_roi=[128-roi[2],roi[1],128-roi[0],roi[3]],native_hoof_roi=[32-nroi[2],nroi[1],32-nroi[0],nroi[3]],target_foot_anchor=[128-base['target_foot_anchor'][0],base['target_foot_anchor'][1]],registered_foot_anchor=[128-base['registered_foot_anchor'][0],base['registered_foot_anchor'][1]],foot_delta=[-base['foot_delta'][0],base['foot_delta'][1]],visible_bounds=list(m.box(im)),body_visible_bounds=[128-base['body_visible_bounds'][2],base['body_visible_bounds'][1],128-base['body_visible_bounds'][0],base['body_visible_bounds'][3]],registration_transform='Full128x96 canvas horizontal mirror after representative registration; inherited crop/scale/offset describe representative before mirror.',native_projection={'source_roi':[0,22,32,24],'source_rgba_sha256':hashlib.sha256(shadow.tobytes()).hexdigest(),'source_file':str(shadow_file.relative_to(r)),'composite_at':[0,88],'scale':4,'filter':'nearest','separate_from_body_registration':True})
for rec in records:
    rec['native_cpu_frame']=src['frame_mapping'][rec['source_index']]
atlas=Image.new('RGBA',(1024,96))
for rec in records:atlas.alpha_composite(Image.open(r/rec['path']).convert('RGBA'),(rec['source_index']*128,0))
out=r/'frames/tactical-native-walk.png';atlas.save(out,optimize=True);m.compress(out)
scenario={'id':'tactical-walk','class_id':3,'source_side':'ally','character_id':'ally-pegasus-rider','display_name':'盟军天马骑士','source_atlas':'../../../source-input/corrected-tactical-walk/class-3-ally.png','source_frame_size':[32,24],'source_anchor':[16,24],'source_columns':8,'output_atlas':'frames/tactical-native-walk.png','output_frame_size':[128,96],'output_anchor':[64,96],'logical_render_scale':0.25,'output_atlas_bytes':out.stat().st_size,'frame_mapping':records,'directions':src['directions'],'direction_mirror_x':{},'timing':src['timing'],'native_alias_groups':[[i]for i in range(8)],'proven_mirror_pairs':[[2,6],[3,7]],'source_audit':{'status':'verified_native_tactical','source_chr':19,'overlay':'../../../source-input/corrected-tactical-walk/overlay.json','verification':'../../../source-input/corrected-tactical-walk/verification.json','record_key':'class-3-ally','cpu_entry':overlay['entry'],'caller':overlay['caller'],'native_render':overlay['native_render'],'mirror_policy':'All CPU direction and OAM flips are in source frames. Right output frames are proven full-canvas mirrors of left frames. No additional runtime direction mirror.'},'review_status':'candidate','projection_policy':'Exact original black projection ROI y22:24 composed nearest4 at[0,88]; its pixel SHA is per record. It is excluded from all anatomical registration.'}
d['scenarios']=[scenario]+[s for s in d['scenarios']if s['id']!='tactical-walk'];d.pop('pending_scenarios',None);d['status']='battle_idle_passed_native_walk_review_candidate';p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
frames=[]
for theme,bg,fg in [('light','#e9e4d9','#26333a'),('dark','#1d2b35','#edf0e7')]:
    frames=[]
    for phase in [0,1]:
        board=Image.new('RGBA',(1096,470),bg);dr=ImageDraw.Draw(board);dr.text((16,8),'天马真实战术四向 · 原CPU / 新图 · 每相16 ticks',font=m.FONT,fill=fg)
        for col,(direction,order)in enumerate(src['directions'].items()):
            i=order[phase];x=16+col*268;board.alpha_composite(ni.crop((i*32,0,(i+1)*32,24)).resize((256,192),Image.Resampling.NEAREST),(x,38));board.alpha_composite(Image.open(r/records[i]['path']).convert('RGBA').resize((256,192),Image.Resampling.NEAREST),(x,258));dr.text((x+96,232),direction,font=m.FONT,fill=fg)
        frames.append(board.convert('RGB'))
    frames[0].save(r/f'reviews/tactical-native-four-directions-{theme}.gif',save_all=True,append_images=[frames[1]],duration=[270,260],loop=0,disposal=2,optimize=True)
    frames[0].save(r/f'reviews/tactical-native-four-directions-{theme}.png',optimize=True)
ids=json.loads((R/'gallery-action-ids.json').read_text());ids['maps']=['professions-class-3-ally-maps-tactical-walk--'+kind+'-'+direction for direction in src['directions']for kind in ['walk','idle']]+['professions-class-3-ally-maps-tactical-idle--idle-cycle'];ids.pop('pending',None);(R/'gallery-action-ids.json').write_text(json.dumps(ids,ensure_ascii=False,indent=2)+'\n')
print('8-slot native walk packaged',out.stat().st_size,'bytes',len(ids['battle'])+len(ids['maps']),'gallery actions')
