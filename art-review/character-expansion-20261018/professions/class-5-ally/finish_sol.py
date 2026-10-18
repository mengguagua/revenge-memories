# -*- coding: utf-8 -*-
"""Freeze native5 explicit reviewed art selections; preserve previously approved0/3/7."""
from pathlib import Path
from PIL import Image
import json,hashlib,shutil
P=Path(__file__).resolve().parent;R=P.parents[1];B=P/'battle';M=P/'maps';O=B/'sol-frames';O.mkdir(exist_ok=True)
read=lambda p:json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def info(p):
 d={'size':list(Image.open(p).size),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 if d['bytes']>50000:d['quality_reason']='Preserve full feather/metal/outline detail at required4x dimensions; file-size reference is soft. PNG optimize lossless.'
 return d
def strip(paths,path,size):
 out=Image.new('RGBA',(size[0]*len(paths),size[1]))
 for i,p in enumerate(paths):out.alpha_composite(Image.open(p).convert('RGBA'),(i*size[0],0))
 out.save(path,optimize=True)
u=read(P/'reference/production-unit.json');canonical=u['unique_art_frames'];mapping={};records=[]
for f in canonical:
 if f in[0,3,7]:out=B/f'frames/frame-{f:03}.png';path=f'frames/frame-{f:03}.png';revision='previous_approved_retained'
 else:out=O/f'frame-{f:03}.png';shutil.copy2(B/f'candidate-sol/frame-{f:03}.png',out);path=f'sol-frames/frame-{f:03}.png';revision='sol'
 mapping[str(f)]=path;records.append({'source_frame':f,'path':path,'revision':revision,**info(out)})
atlas=Image.open(P/'reference/battle-native-atlas.png').convert('RGBA')
def source(f):return atlas.crop((f%16*96,f//16*136,f%16*96+96,f//16*136+136))
for f in[25,48]:
 a=source(f);b=source(0);assert a.size==b.size and a.tobytes()==b.tobytes();mapping[str(f)]=mapping['0']
strip([B/mapping[str(f)]for f in canonical],O/'sol-battle-atlas.png',(384,544))
write(B/'frame_mapping.json',{'schema_version':1,'revision':'sol','character_id':'class-5-ally','display_name':'隼骑士（职业样板） · sol','original_class_id':5,'source_side':'ally','status':'complete_art_review_passed','runtime_integrated':False,'source_frame_size':[96,136],'output_frame_size':[384,544],'source_anchor':[48,96],'output_anchor':[192,384],'source_columns':16,'source_oam_frame_count':25,'source_idle_frame':25,'frame_mapping':mapping,'required_source_frames':u['required_source_frames'],'canonical_frames':canonical,'variant_keys':u['bound_action_keys'],'records':records,'batches':[{'id':'sol','review':'reviews/sol-all-light.png','frames':canonical}],'review_note':'sol：0/3/7保持既有通过稿；补齐1/2/4/5/6/49/50。原翼相和各自蹄部位置逐姿势登记，49举枪握点改为头右上方，50空手。源3下左孤立片保留为远翼；非额外马蹄。轮廓/次要蹄位保留数至十余输出像素重绘差异，不声称所有关节逐像素一致。'})
walk=[]
for f in range(8):
 fn=f'sol-frames/frame-{f:03}.png';walk.append({'source_index':f,'source_frame':f,'output_index':f,'path':fn,'output_path':fn,'revision':'sol','direction':['up','right','down','left'][f//2],**info(M/fn)})
strip([M/r['path']for r in walk],M/'frames/sol-native-walk.png',(128,96))
idle=[]
for f,a in enumerate([0,1,2,1,0,1]):
 fn=f'sol-frames/idle-{a:03}.png';idle.append({'source_index':f,'source_frame':f,'canonical_frame':a,'output_index':f,'path':fn,'output_path':fn,'revision':'sol',**info(M/fn)})
strip([M/r['path']for r in idle],M/'frames/sol-idle.png',(96,96))
walk_s={'id':'tactical-walk','source_atlas':'../../../source-input/corrected-tactical-walk/class-5-ally.png','source_frame_size':[32,24],'source_anchor':[16,24],'output_atlas':'frames/sol-native-walk.png','output_frame_size':[128,96],'output_anchor':[64,96],'frame_mapping':walk,'directions':{'up':[0,1],'right':[2,3],'down':[4,5],'left':[6,7]},'direction_mirror_x':{},'timing':{'native_fps':60.0988,'frame_ticks':16},'source_audit':{'status':'verified_native_tactical','source_chr':19,'record_key':'class-5-ally','evidence':'../reference/corrected-tactical-walk-record.json','overlay':'../../../source-input/corrected-tactical-walk/overlay.json','verification':'../../../source-input/corrected-tactical-walk/verification.json','projection':'Native rows21..23; row20 body pixel preserved; not anatomical anchor.'}}
idle_s={'id':'tactical-idle','static_facing':True,'source_atlas':'../reference/class-5-idle-source-atlas.png','source_frame_size':[24,24],'source_anchor':[12,20],'output_atlas':'frames/sol-idle.png','output_frame_size':[96,96],'output_anchor':[48,80],'frame_mapping':idle,'directions':{'all':[0,1,2,1]},'direction_mirror_x':{},'timing':{'native_fps':60.0988,'cycle_frames':[0,1,2,1],'frame_ticks':[14,8,14,8]}}
write(M/'frame_mapping.json',{'schema_version':1,'revision':'sol','character_id':'class-5-ally','actor_id':'class-5-ally','display_name':'隼骑士（职业样板） · sol','class_id':5,'source_side':'ally','status':'complete_art_review_passed','runtime_integrated':False,'scenarios':[walk_s,idle_s],'review_note':'sol：本类原生8槽，6绘加2严格全RGBA镜像。原投影与主体独立处理；正背面竖枪为上端短帽/下端刃部，侧向收在体内，不新增前伸长枪；正面左相收腿、右相伸腿。静止3相保留固定右朝向。仅选定落点与明显相位关系核对，次要轮廓有数输出像素差异。'})
write(P/'manifest.json',{'id':'class-5-ally','revision':'sol','status':'complete_art_review_passed','battle_mapping':'battle/frame_mapping.json','maps_mapping':'maps/frame_mapping.json','qa':'qa-report.json','inventory':'image-inventory.json','runtime_integrated':False})
write(P/'qa-report.json',{'revision':'sol','status':'passed','battle_source_slots':12,'canonical_battle_frames':10,'previous_approved_retained':[0,3,7],'native_tactical_frames':8,'tactical_drawn_poses':6,'static_idle_poses':3,'registration':['battle/source/sol-registration.json','battle/source/keypose-registration.json','maps/source/sol-registration.json'],'checks':['Own class5 source and per-pose primary hoof target','No nonuniform scaling or procedural anatomy','No visiblealpha>4 clipping','Full exactRGBA battle aliases25/48to0 and map6/7mirrors','Original native flight shadow rows21..23 preserved separately','Measured transparent static extraction boundaries preserve wing and muzzle','Light/dark source/new sheets inspected'],'limits':['Selected registration points do not prove every joint/hoof.','Wings and secondary hoof/weapon contours retain several to low-teens output-pixel differences.','Browser playback not performed; no visible Godot launched.'],'runtime_integrated':False})
write(P/'image-inventory.json',{'revision':'sol','images':[{'path':str(p.relative_to(P)),'purpose':'raw_reference'if'source'in p.parts or'reference'in p.parts else'review_delivery',**info(p)}for p in sorted(P.rglob('*.png'))]})
print('Falcon Knight package ready: battle12 slots, maps8+3,0/3/7 retained.')
