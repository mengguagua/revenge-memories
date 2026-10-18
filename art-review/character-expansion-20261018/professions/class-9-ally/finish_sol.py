# -*- coding: utf-8 -*-
"""Finish maps only; all previously approved battle pixels stay unchanged."""
from pathlib import Path
from PIL import Image
import json,hashlib,shutil
P=Path(__file__).resolve().parent;M=P/'maps';F=M/'sol-frames'
read=lambda p:json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def info(p):return {'size':list(Image.open(p).size),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def strip(paths,path,size):
 out=Image.new('RGBA',(size[0]*len(paths),size[1]))
 for i,p in enumerate(paths):out.alpha_composite(Image.open(p).convert('RGBA'),(i*size[0],0))
 out.save(path,optimize=True)
m=read(M/'frame_mapping.json');walk=m['scenarios'][0];recs=[]
for f in range(8):
 out=F/f'frame-{f:03}.png';shutil.copy2(M/f'candidate-sol/frame-{f:03}.png',out);recs.append({'source_index':f,'source_frame':f,'output_index':f,'path':f'sol-frames/frame-{f:03}.png','output_path':f'sol-frames/frame-{f:03}.png','revision':'sol','art_status':'reviewed_selected','direction':['up','right','down','left'][f//2],**info(out)})
walk['frame_mapping']=recs;walk['missing_source_slots']=[];strip([M/r['path']for r in recs],M/'frames/sol-native-walk.png',(128,96));idle=[]
for f,a in enumerate([0,1,2,1,0,1]):
 out=F/f'idle-{f:03}.png';shutil.copy2(M/f'candidate-sol/idle-{a:03}.png',out);idle.append({'source_index':f,'source_frame':f,'output_index':f,'canonical_frame':a,'path':f'sol-frames/idle-{f:03}.png','output_path':f'sol-frames/idle-{f:03}.png','revision':'sol',**info(out)})
strip([M/r['path']for r in idle],M/'frames/sol-idle.png',(96,96));s={'id':'tactical-idle','static_facing':True,'source_atlas':'reference/static-source.png','source_frame_size':[24,24],'source_anchor':[12,20],'output_atlas':'frames/sol-idle.png','output_frame_size':[96,96],'output_anchor':[48,80],'frame_mapping':idle,'directions':{'all':[0,1,2,1]},'direction_mirror_x':{},'timing':{'native_fps':60.0988,'cycle_frames':[0,1,2,1],'frame_ticks':[14,8,14,8]}}
m.update(status='complete_art_review_passed',scenarios=[walk,s],review_note='sol：八个独立原生方向槽与三相静止已登记并复核；右向首相改回左低靴，静止按实测透明间隔切图，完整盾框保留。可见靴/剑尖有数输出像素的重绘轮廓差异，登记不代表全部关节逐像素一致。');write(M/'frame_mapping.json',m)
write(P/'manifest.json',{'id':'class-9-ally','revision':'sol','status':'complete_art_review_passed','battle_mapping':'battle/frame_mapping.json','maps_mapping':'maps/frame_mapping.json','battle_policy':'Retain prior approved battle without pixel edits.','qa':'qa-report.json','inventory':'image-inventory.json','runtime_integrated':False})
write(P/'qa-report.json',{'revision':'sol','status':'passed','battle':'previous complete art and source proof retained','map_walk':{'source':'verified CHR26 native CPU8slots','drawn_poses':8,'mirrors_used':False,'registration':'maps/source/sol-native-registration.json'},'idle':{'independent_poses':3,'registration':'maps/source/sol-idle-registration.json','whole_rgba_reassembly':True,'equal_thirds_rejected':True},'visual_review':'Source/new same-size light/dark sheets; individual body/weapon phases reviewed.','limitations':'Selected registration points and obvious step/equipment relations checked; no every-joint exactness claim.','runtime_integrated':False})
write(P/'image-inventory.json',{'revision':'sol','images':[{'path':str(p.relative_to(P)),**info(p)}for p in sorted(P.rglob('*.png'))]})
write(M/'sol-qa.json',{'revision':'sol','source_reference_verified':True,'native_frames_packaged':8,'idle_independent_poses':3,'whole_group_complete':True,'art_status':'complete_art_review_passed','qa':'../qa-report.json'})
print('Swordfighter complete: frozen battle + native8 + idle3.')
