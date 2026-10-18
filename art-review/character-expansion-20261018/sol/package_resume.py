# -*- coding: utf-8 -*-
"""Package reviewed selections and explicitly labelled pending candidates only."""
import sys
if "--historical-partial-stage" not in sys.argv:
    raise SystemExit("Historical partial checkpoint only. Current results are the per-unit finish_sol.py packages; no files changed.")
from pathlib import Path
from PIL import Image
import json,hashlib,shutil
R=Path(__file__).resolve().parent.parent
read=lambda p:json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def info(p):return {'size':list(Image.open(p).size),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def strip(paths,path,size):
 im=Image.new('RGBA',(size[0]*len(paths),size[1]))
 for i,p in enumerate(paths):im.alpha_composite(Image.open(p).convert('RGBA'),(i*size[0],0))
 im.save(path,optimize=True)
overlay=read(R/'source-input/corrected-tactical-walk/overlay.json')
verification=read(R/'source-input/corrected-tactical-walk/verification.json');assert verification['passed']
for cid,slots,note,candidate in [(9,[0,1,3,4,5,6,7],'sol：右向首相2的高低脚顺序待修，未采用。静止三相尚缺；本组未完成。其余7相已登记。',False),(7,list(range(8)),'sol：地图为登记后的对照候选，待进一步复核远侧马蹄和枪端。战斗21/22仍待修，本组未完成。静止稿整体等比登记时保留完整枪尖，头顶约比源低3输出像素，作为候选保留。',True)]:
 P=R/f'professions/class-{cid}-ally';M=P/'maps';O=M/'sol-frames';O.mkdir(exist_ok=True);(M/'frames').mkdir(exist_ok=True)
 recs=[]
 for i,f in enumerate(slots):
  a=M/f'candidate-sol/frame-{f:03}.png';out=O/f'frame-{f:03}.png';shutil.copy2(a,out);recs.append({'source_index':f,'source_frame':f,'output_index':i,'path':f'sol-frames/frame-{f:03}.png','output_path':f'sol-frames/frame-{f:03}.png','revision':'sol','art_status':'candidate_pending_review'if candidate else'reviewed_selected','direction':['up','right','down','left'][f//2],**info(out)})
 strip([M/r['path']for r in recs],M/'frames/sol-native-walk.png',(128,96))
 source=overlay['records'][f'class-{cid}-ally']
 walk={'id':'tactical-walk','source_atlas':f'../../../source-input/corrected-tactical-walk/class-{cid}-ally.png','source_frame_size':[32,24],'source_anchor':[16,24],'output_atlas':'frames/sol-native-walk.png','output_frame_size':[128,96],'output_anchor':[64,96],'logical_render_scale':.25,'frame_mapping':recs,'directions':source['directions'],'direction_mirror_x':{},'timing':source['timing'],'source_audit':{'status':'verified_native_tactical','record_key':f'class-{cid}-ally','source_chr':source['source_chr'],'overlay':'../../../source-input/corrected-tactical-walk/overlay.json','verification':'../../../source-input/corrected-tactical-walk/verification.json','note':'Source verified separately from candidate art acceptance.'},'missing_source_slots':sorted(set(range(8))-set(slots))}
 scenarios=[walk]
 if cid==7:
  recs=[]
  for i,a in enumerate([8,9,10,9,8,9]):
   out=O/f'idle-{i:03}.png';shutil.copy2(M/f'candidate-sol/frame-{a:03}.png',out);recs.append({'source_index':i,'source_frame':i,'canonical_frame':a-8,'path':f'sol-frames/idle-{i:03}.png','output_path':f'sol-frames/idle-{i:03}.png','art_status':'candidate_pending_review',**info(out)})
  strip([M/r['path']for r in recs],M/'frames/sol-idle.png',(96,96));scenarios.append({'id':'tactical-idle','static_facing':True,'source_atlas':'reference/static-idle-atlas.png','source_frame_size':[24,24],'source_anchor':[12,20],'output_atlas':'frames/sol-idle.png','output_frame_size':[96,96],'output_anchor':[48,80],'frame_mapping':recs,'directions':{'all':[0,1,2,1]},'direction_mirror_x':{},'timing':{'native_fps':60.0988,'cycle_frames':[0,1,2,1],'frame_ticks':[14,8,14,8]}})
 title={7:'黄金骑士（地图候选） · sol',9:'剑士（地图补充） · sol'}[cid]
 write(M/'frame_mapping.json',{'schema_version':1,'revision':'sol','character_id':f'class-{cid}-ally','actor_id':f'class-{cid}-ally','display_name':title,'class_id':cid,'source_side':'ally','status':'candidate_pending_art_review'if candidate else'partial_selected_missing_right0_and_idle','review_note':note,'runtime_integrated':False,'scenarios':scenarios})
 write(M/'sol-qa.json',{'revision':'sol','source_reference_verified':True,'native_frames_packaged':len(slots),'whole_group_complete':False,'art_status':'candidate_pending_review'if candidate else'partial_selected','note':note,'registration':'source/sol-registration.json'if cid==7 else'source/sol-native-registration.json'})
# Battle7: previously approved frames only. Rejected21/22 are deliberately unmapped.
P=R/'professions/class-7-ally';B=P/'battle';units=read(R/'catalog/production-units.json')['units'];u=next(x for x in units if x['id']=='class-7-ally');selected=list(range(21))+[50,52];mapping={str(f):f'frames/frame-{f:03}.png'for f in selected}
for f in [26,49]:
 a=Image.open(B/f'reference/native-{f:03}.png').convert('RGBA');b=Image.open(B/'reference/native-000.png').convert('RGBA');assert a.size==b.size and a.tobytes()==b.tobytes();mapping[str(f)]='frames/frame-000.png'
write(B/'frame_mapping.json',{'schema_version':1,'revision':'sol','character_id':'class-7-ally','display_name':'黄金骑士（职业样板） · sol','original_class_id':7,'source_side':'ally','status':'partial_approved_missing_21_22','review_note':'sol：既有通过稿0–20、50、52保留；21/22尚待修，未采用暂停时未审v5。普通攻击明确缺帧，投枪与反应可查看。','runtime_integrated':False,'source_frame_size':[112,80],'output_frame_size':[448,320],'source_anchor':[56,80],'source_oam_frame_count':26,'source_idle_frame':26,'source_columns':16,'frame_mapping':mapping,'variant_keys':u['bound_action_keys'],'required_source_frames':u['required_source_frames'],'missing_source_frames':[21,22],'canonical_frames':selected})
# Inventory current actual file dimensions/bytes, distinct from acceptance.
for cid in [7,9]:
 P=R/f'professions/class-{cid}-ally';write(P/'sol-image-inventory.json',{'revision':'sol','acceptance':'See mapping statuses; presence/bytes do not imply approval.','images':[{'path':str(p.relative_to(P)),**info(p)}for p in sorted(P.rglob('*.png'))]})
print('Packaged partial swordsman maps and labelled gold-knight candidates; no group completion claims.')
