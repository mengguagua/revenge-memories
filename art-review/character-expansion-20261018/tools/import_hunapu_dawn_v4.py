#!/usr/bin/env python3
"""Register two authored cross-body guards and their exact native mirrors."""
import argparse,copy,json,os
from functools import lru_cache
from PIL import Image,ImageOps
import import_hunapu_dawn_v1 as H
ROOT=H.ROOT; REV='hunapu-dawn-strafe-v4-20261024';OUT=ROOT/REV;SRC=OUT/'source';MP=H.MP
H.OUT=OUT;H.SRC=SRC;H.REV=REV
PID='hunapu-promoted-maps-tactical-walk'
def write(p,d):H.write(p,d)
@lru_cache(maxsize=1)
def baseline():return json.loads((SRC/'before-gallery.json').read_text())
def prepare(publish=False):
 H.ASSETS.clear();H.REG.clear();p=baseline()['profiles'][0]
 poses={int(i):Image.open(ROOT/f).convert('RGBA')for i,f in p['newFrames'].items()}
 for raw,i in zip(H.figures('cross-body-master.png',2,1),[2,3]):
  fp=H.art_face(raw)[0];im,hb=H.solid_hair(raw,fp);point=[(hb[0]+hb[2])/2,(hb[1]+hb[3])/2]
  poses[i]=H.place(im,(128,96),64/(im.getbbox()[3]-hb[1]),point,[64,43],'tactical-walk-'+str(i),95)
  H.REG[-1].update(method='complete authored pose; palette/alpha normalization, uniform nearest resize and integer registration only',hair_box_source=hb)
 # Native left6 is mirror(right3), left7 is mirror(right2).
 poses[6]=ImageOps.mirror(poses[3]);poses[7]=ImageOps.mirror(poses[2])
 for i in[2,3,6,7]:H.save(poses[i],f'tactical-walk/frame-{i:03}.png','斜跨胸前持剑、低位持盾的完整横移人物')
 atlas=Image.new('RGBA',(128*8,96))
 for i,im in poses.items():atlas.alpha_composite(im,(128*i,0))
 ap=H.save(atlas,'tactical-walk-atlas.png','保留四个纵向旧姿势，只替换左右横移四个槽')
 mm=json.loads((SRC/'before-maps-mapping.json').read_text());s=next(s for s in mm['scenarios']if s['id']=='tactical-walk');rel=lambda p:os.path.relpath(p,MP.parent)
 note='按用户确认的原作姿势重做横移：脸朝前且略向移动侧转，胸面可见，肩胯稍错位；剑柄握于腹前，剑从身前斜向反侧上方举起，另一手持小盾贴在腹部前侧低位。右2/3收腿重叠→屈膝跨开，左6/7按原作反相镜像；中心稳定、完整全身姿势。'
 s.update(revision=REV,review_note=note,motion_review=rel(OUT/'README.md'),output_atlas=rel(ap))
 for row in s['frame_mapping']:
  i=row['source_index']
  if i in[2,3,6,7]:
   path=OUT/f'tactical-walk/frame-{i:03}.png';row.update(path=rel(path),output_path=rel(path),size=[128,96],bytes=path.stat().st_size,sha256=H.sha(path))
 mm.update(revision=REV,status='review_candidate',runtime_integrated=False)
 write(OUT/'mapping-draft.json',mm);write(OUT/'asset-manifest.json',{'revision':REV,'palette':H.HEX,'assets':H.ASSETS,'registrations':H.REG,'authored_right_poses':2,'mirror_slots':{'6':3,'7':2},'changed_slots':[2,3,6,7],'runtime_integrated':False})
 H.board([(f'向右 · 槽{i}',poses[i])for i in[2,3]]+[(f'向左 · 槽{i}',poses[i])for i in[6,7]],'poses','破晓勇士 · 斜跨持剑与低位持盾横移',4)
 if publish:write(MP,mm)
 print(json.dumps({'published':publish,'changed_slots':[2,3,6,7],'individual_bytes':[p['bytes']for p in H.ASSETS if '/tactical-walk/'in p['path']]}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');a=p.parse_args();prepare(a.publish)
