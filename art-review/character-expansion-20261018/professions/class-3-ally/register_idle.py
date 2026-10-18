from pathlib import Path
import json,shutil
from PIL import Image,ImageDraw
import register_art as m
R=Path(__file__).resolve().parent; B=R.parents[1]; r=R/'maps'
(r/'idle-frames').mkdir(exist_ok=True)
native=R/'reference/map-idle-native.png'; ni=Image.open(native).convert('RGBA'); records=[]
configs=[(0,4,330,[450,1025,535,1078],[8,17,9,18]),(1,1,284,[415,1090,510,1150],[9,18,10,19]),(2,1,271,[415,1090,510,1150],[9,18,10,19])]
for i,v,head,roi,nroi in configs:
    source=r/f'source/idle-{i:03}-generated-v{v}.png'; si=Image.open(source); nf=ni.crop((i*24,0,(i+1)*24,24)); fb=m.foot_box(nf,nroi); target=[(fb[0]+fb[2])*2,fb[3]*4]
    rec=m.register(source,(0,0,*si.size),head,roi,[96,96],16,target,i,r/'idle-frames')
    rec.update(source_index=i,output_index=i,output_path=rec['path'],native_hoof_roi=nroi,native_hoof_bounds=fb,source_visible_bounds=list(m.box(nf)),registration_scope='Selected visible front hoof endpoint only; rounding error is not a claim that all limbs/joints match pixel-for-pixel.',native_hoof_semantics='Colored hoof-end pixel, excludes broad black base/shadow and excludes occluded diagonal spear.')
    records.append(rec)
for i,rep in [(3,1),(4,0),(5,1)]:
    out=r/f'idle-frames/frame-{i:03}.png';shutil.copyfile(r/records[rep]['path'],out);rec={**records[rep],'source_frame':i,'source_index':i,'output_index':i,'representative_frame':rep,'kind':'native_exact_pixel_alias','path':str(out.relative_to(r)),'output_path':str(out.relative_to(r))};records.append(rec)
atlas=Image.new('RGBA',(576,96));
for rec in records:atlas.alpha_composite(Image.open(r/rec['path']).convert('RGBA'),(rec['source_index']*96,0))
atlas.save(r/'frames/tactical-idle.png',optimize=True);m.compress(r/'frames/tactical-idle.png')
for theme,bg,fg in [('dark','#1d2b35','#edf0e7'),('light','#e9e4d9','#26333a')]:
    board=Image.new('RGBA',(624,486),bg);dr=ImageDraw.Draw(board);dr.text((16,10),'盟军天马待机 · 原作 / 新图 · 4倍登记',font=m.FONT,fill=fg)
    for col,i in enumerate([0,1,2]):
        x=16+col*204;nf=ni.crop((i*24,0,(i+1)*24,24)).resize((192,192),Image.Resampling.NEAREST);new=Image.open(r/f'idle-frames/frame-{i:03}.png').convert('RGBA').resize((192,192),Image.Resampling.NEAREST);board.alpha_composite(nf,(x,40));board.alpha_composite(new,(x,246));dr.text((x+90,455),str(i),font=m.FONT,fill=fg)
    board.convert('RGB').save(r/f'reviews/tactical-idle-{theme}.png',optimize=True)
scenario={'id':'tactical-idle','class_id':3,'source_side':'ally','character_id':'ally-pegasus-rider','display_name':'盟军天马骑士','source_atlas':'../../../source-input/legacy-assets/assets/original/graphics/map_units/class_3_ally.png','source_frame_size':[24,24],'source_anchor':[12,20],'output_atlas':'frames/tactical-idle.png','output_frame_size':[96,96],'output_anchor':[48,80],'logical_render_scale':0.25,'frame_mapping':records,'directions':{'static':[0,1,2,1]},'direction_mirror_x':{},'static_facing':True,'timing':{'native_fps':60.0988,'cycle_frames':[0,1,2,1],'frame_ticks':[14,8,14,8]},'output_atlas_bytes':(r/'frames/tactical-idle.png').stat().st_size,'review_status':'candidate'}
data={'schema_version':1,'class_id':3,'source_side':'ally','character_id':'ally-pegasus-rider','actor_id':'ally-pegasus-rider','display_name':'盟军天马骑士','width_height_scale':4,'runtime_integrated':False,'art_mode':'Built-in ImageGen; technical crop, uniform scale, rigid registration and lossless compression only.','scenarios':[scenario],'pending_scenarios':{'tactical-walk':'Await corrected native bank011 CHR/mover overlay. Previous fixed CHR26 world/village extraction is not accepted tactical walk source.'}}
(r/'frame_mapping.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print([(x['source_index'],x['registered_foot_anchor'],x['visible_bounds'],x['bytes'])for x in records[:3]])
