#!/usr/bin/env python3
"""Complete authored map poses; never freeze a torso above moving leg patches."""
import argparse,copy,json,os
from pathlib import Path
from functools import lru_cache
from PIL import Image
import import_hunapu_dawn_v1 as H
ROOT=H.ROOT;REV='hunapu-dawn-map-body-v3-20261024';OUT=ROOT/REV;SRC=OUT/'source';MP=H.MP
H.OUT=OUT;H.SRC=SRC;H.REV=REV
CONTEXTS={'story','world','tactical-walk'}
def write(p,d):H.write(p,d)
def sha(p):return H.sha(p)
@lru_cache(maxsize=1)
def baseline():return json.loads((SRC/'before-gallery.json').read_text())
def oldframe(context,i):
 p=next(p for p in baseline()['profiles']if p['context']==context);return Image.open(ROOT/p['newFrames'][str(i)]).convert('RGBA')
def register(raw,kind,slot,back=False):
 fp=None if back else H.art_face(raw)[0];im,hb=H.solid_hair(raw,fp,back);point=[(hb[0]+hb[2])/2,(hb[1]+hb[3])/2];scale=64/(im.getbbox()[3]-hb[1]);out=H.place(im,(128,96),scale,point,[64,43],kind+'-'+str(slot),95)
 H.REG[-1].update(method='complete authored pose, uniform scale and integer registration only; no frozen upper-body or separate leg compositing',hair_box_source=hb,raw_face=fp)
 return out
def prepare(publish=False):
 H.ASSETS.clear();H.REG.clear();story={i:oldframe('story',i)for i in range(6)};walk={i:oldframe('tactical-walk',i)for i in range(8)};sr=H.figures('story-whole-gait-master.png',2,2);tr=H.figures('tactical-front-strafe-master.png',2,2)
 for raw,i in zip(sr,[2,3,4,5]):story[i]=register(raw,'story',i,i in[2,3])
 # Native slots2/3 are narrow/wide;6/7 wide/narrow. All face forward.
 for raw,i in zip(tr,[2,3,6,7]):walk[i]=register(raw,'tactical-walk',i)
 frames={'story':story,'tactical-walk':walk};mm=json.loads((SRC/'before-maps-mapping.json').read_text());rel=lambda p:os.path.relpath(p,MP.parent)
 note='破晓勇士地图修订：剧情背向抬膝与脚跟沿髋下收回，不外撇；手臂与腿反向摆动，肩、肘、躯干和衣摆连贯联动。整个人物完整重绘，仅校准头腰中心，不冻结上身或拼接腿部。战斗地图按原作槽位正面持械横移，脸和胸朝前，盾握在胸前前臂上；向右2/3窄步到跨步，向左6/7跨步到窄步。集中阴影及已完成的双剑、必杀火花保留。'
 for kind,poses in frames.items():
  for i,im in poses.items():
   if(kind=='story'and i in[2,3,4,5])or(kind=='tactical-walk'and i in[2,3,6,7]):H.save(im,f'{kind}/frame-{i:03}.png','完整全身联动地图姿势；无上下半身拼接')
 for s in mm['scenarios']:
  if s['id']not in CONTEXTS:continue
  kind='story'if s['id']in['story','world']else s['id'];poses=frames[kind];changed={2,3,4,5}if kind=='story'else{2,3,6,7};s.update(revision=REV,review_note=note,motion_review=rel(OUT/'README.md'))
  for row in s['frame_mapping']:
   i=row['source_index']
   if i not in changed:continue
   p=OUT/kind/f'frame-{i:03}.png';v=rel(p);row.update(path=v,output_path=v,size=[128,96],bytes=p.stat().st_size,sha256=sha(p))
  atlas=Image.new('RGBA',(128*len(poses),96))
  for i,im in poses.items():atlas.alpha_composite(im,(i*128,0))
  s['output_atlas']=rel(H.save(atlas,kind+'-atlas.png','新旧完整姿势按原槽位合并；剧情与大地图共用'))
 mm.update(revision=REV,review_note=note,status='review_candidate',runtime_integrated=False)
 H.board([('剧情 '+str(i),story[i])for i in[2,3,4,5]]+[('横移 '+str(i),walk[i])for i in[2,3,6,7]],'maps','破晓勇士 · 完整联动步态与正面横移',4)
 write(OUT/'mapping-draft.json',mm);write(OUT/'asset-manifest.json',{'revision':REV,'palette':H.HEX,'assets':H.ASSETS,'registrations':H.REG,'complete_pose_assets':8,'no_upper_body_freeze':True,'world_reuses_story':True,'native_horizontal_slots':{'2':'front-facing narrow','3':'front-facing right stride','6':'front-facing left stride','7':'front-facing narrow'},'runtime_integrated':False})
 if publish:write(MP,mm)
 print(json.dumps({'published':publish,'complete_new_poses':8,'assets':len(H.ASSETS),'battle_mapping_changed':False}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');a=p.parse_args();prepare(a.publish)
