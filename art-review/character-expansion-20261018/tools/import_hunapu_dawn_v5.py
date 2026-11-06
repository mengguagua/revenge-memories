#!/usr/bin/env python3
"""Synchronize vertical walk and idle to the approved v4 Dawn Warrior model."""
import argparse,json,os
from functools import lru_cache
from PIL import Image
import import_hunapu_dawn_v1 as H
ROOT=H.ROOT;REV='hunapu-dawn-map-unify-v5-20261024';OUT=ROOT/REV;SRC=OUT/'source';MP=H.MP
H.OUT=OUT;H.SRC=SRC;H.REV=REV
CONTEXTS={'tactical-walk','tactical-idle'};PIDS={f'hunapu-promoted-maps-{c}'for c in CONTEXTS}
def write(p,d):H.write(p,d)
@lru_cache(maxsize=1)
def baseline():return json.loads((SRC/'before-gallery.json').read_text())
def register(raw,kind,i,back=False):
 # The raised forearm occludes the cheek in idle1. Register the complete
 # upper blue-hair component, not the nearby skin/hand or a clipped face ROI.
 im,hb=H.solid_hair(raw,back=True);point=[(hb[0]+hb[2])/2,(hb[1]+hb[3])/2]
 idle=kind=='tactical-idle';ground=80 if idle else 95
 out=H.place(im,(96,96)if idle else(128,96),64/(im.getbbox()[3]-hb[1]),point,[48 if idle else 64,38],kind+'-'+str(i),ground)
 H.REG[-1].update(hair_box_source=hb,method='complete authored figure, same 64-pixel hair-top-to-ground model height as approved v4; uniform nearest resize and integer registration only')
 return out
def prepare(publish=False):
 H.ASSETS.clear();H.REG.clear();profiles={p['context']:p for p in baseline()['profiles']};walk={int(i):Image.open(ROOT/f).convert('RGBA')for i,f in profiles['tactical-walk']['newFrames'].items()}
 for raw,i in zip(H.figures('vertical-master.png',2,2),[0,1,4,5]):walk[i]=register(raw,'tactical-walk',i,i in[0,1])
 idle3={i:register(raw,'tactical-idle',i)for i,raw in enumerate(H.figures('idle-master.png',3,1))}
 idle={i:idle3[j].copy()for i,j in enumerate([0,1,2,1,0,1])};frames={'tactical-walk':walk,'tactical-idle':idle};mm=json.loads((SRC/'before-maps-mapping.json').read_text());rel=lambda p:os.path.relpath(p,MP.parent)
 for kind,poses in frames.items():
  changed=[0,1,4,5]if kind=='tactical-walk'else list(range(6))
  for i in changed:H.save(poses[i],f'{kind}/frame-{i:03}.png','与已确认横移统一的完整地图人物：头身比例、脸型、护甲、剑盾和材质')
  s=next(s for s in mm['scenarios']if s['id']==kind);size=(128,96)if kind=='tactical-walk'else(96,96);atlas=Image.new('RGBA',(size[0]*len(poses),size[1]))
  for i,im in poses.items():atlas.alpha_composite(im,(i*size[0],0))
  ap=H.save(atlas,kind+'-atlas.png','按原槽位完整地图图集，已确认横移四帧逐字节保留')
  s.update(revision=REV,review_note='以已确认左右横移为统一人物模型：相同纯色蓝发、脸型与头身比例、厚浅蓝肩胸甲、护臂与深蓝长靴、蓝芯银剑和小盾。向上／向下保留交替换腿、前后遮挡与原持械架势，待机保留斜举→平举→过顶的举剑循环，中心稳定。左右横移原图保持。',motion_review=rel(OUT/'README.md'),output_atlas=rel(ap),output_atlas_bytes=ap.stat().st_size)
  for row in s['frame_mapping']:
   i=row['source_index']
   if i in changed:
    p=OUT/kind/f'frame-{i:03}.png';row.update(path=rel(p),output_path=rel(p),size=list(size),bytes=p.stat().st_size,sha256=H.sha(p))
 mm.update(revision=REV,status='review_candidate',runtime_integrated=False)
 write(OUT/'mapping-draft.json',mm);write(OUT/'asset-manifest.json',{'revision':REV,'palette':H.HEX,'assets':H.ASSETS,'registrations':H.REG,'new_complete_poses':7,'idle_repeated_slots':{'0':0,'1':1,'2':2,'3':1,'4':0,'5':1},'unchanged_v4_walk_slots':[2,3,6,7],'model_height_pixels':64,'runtime_integrated':False})
 def idle_for_board(im):
  out=Image.new('RGBA',(128,96));out.alpha_composite(im,(16,15));return out
 H.board([(f'向上{i}',walk[i])for i in[0,1]]+[(f'向下{i}',walk[i])for i in[4,5]]+[(f'待机{i}',idle_for_board(idle3[i]))for i in[0,1,2]]+[('已确认横移',walk[3])],'model-comparison','破晓勇士 · 战斗地图统一形象 · 同地面基准',4)
 if publish:write(MP,mm)
 print(json.dumps({'published':publish,'new_complete_poses':7,'unchanged_horizontal':[2,3,6,7]}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');a=p.parse_args();prepare(a.publish)
