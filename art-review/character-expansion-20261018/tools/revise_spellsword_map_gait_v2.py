#!/usr/bin/env python3
"""Replace class11 ally map keyframes; retain native timing and battle assets."""
import copy,json,math
from PIL import Image,ImageDraw
from build_gallery import ROOT,file_hash
from prepare_spellsword_complete import write
from export_gallery import font
import import_spellsword_complete as art
import import_sniper_complete as io
REV='spellsword-map-gait-v2-20261023';OUT=ROOT/REV;SRC=OUT/'source';art.SRC=SRC;art.OUT=OUT;io.OUT=OUT

def freeze(poses,base,ids,regions):
 for i in ids:
  if i==base:continue
  for b in regions:poses[i].paste(poses[base].crop(b),b[:2])

def clean(im,label):
 cs=art.helper.parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))[3])
 for c in cs[1:]:
  assert len(c)<=5,(label,'detached',len(c),art.box(c))
  for xy in c:im.putpixel(xy,(0,0,0,0))
 return im

def board(mp):
 labels=['待机0 · 右臂屈肘','待机1 · 前臂展开','待机2 · 抬肘举剑','向上0 · 左脚前迈','向上1 · 右脚前迈','向右2 · 并腿通过','向右3 · 跨步','向下4 · 右手持剑','向下5 · 右手持剑','向左6 · 并腿通过','向左7 · 跨步']
 entries=[*list(mp['tactical-idle'].items())[:3],*mp['tactical-walk'].items()]
 sh=Image.open(ROOT/'gold-knight-walk-v3-20261020/ground-shadow.png').convert('RGBA').resize((80,12),Image.Resampling.NEAREST);sh.putalpha(sh.getchannel('A').point(lambda v:round(v*.30)))
 for light in[False,True]:
  q=Image.new('RGBA',(1200,3*270+52),(220,222,216,255)if light else(32,45,53,255));dr=ImageDraw.Draw(q);fg=(23,38,56)if light else(235,243,242);dr.text((600,24),'我方女魔剑士 · 待机与步态修订',anchor='mm',font=font(21),fill=fg)
  for n,((i,im),label)in enumerate(zip(entries,labels)):
   x=n%4*300+(300-im.width*2)//2;y=52+n//4*270
   # A single existing project shadow behind the feet, matching gallery metadata.
   sy=y+(88 if n<3 else 92)*2-6;sx=n%4*300+150-40;q.alpha_composite(sh,(sx,sy));q.alpha_composite(im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST),(x,y));dr.text((n%4*300+150,y+249),label,anchor='mm',font=font(16),fill=fg)
  io.save(q.convert('RGB'),f'maps-{"light"if light else"dark"}.png','map keyframes, existing ground shadow, centered separated labels')

def main(publish=False):
 idle={i:art.register(f,(96,96),[43,37],88,'idle-'+str(i))for i,f in enumerate(art.figures('idle-master.png',3,3))}
 # Replace the entire lower body together. No ankle-only pastes and no frozen sword arm.
 freeze(idle,0,[1,2],[[0,55,96,96],[38,35,49,46]])
 raw=art.figures('front-back-master.png',4,2);side=art.figures('right-master.png',2,2);walk={}
 for i,j,target in[(0,0,[60,42]),(1,1,[60,42]),(4,2,[64,42]),(5,3,[64,42])]:walk[i]=art.register(raw[j],(128,96),target,92,'walk-'+str(i))
 for i,f in zip([2,3],side):walk[i]=art.register(f,(128,96),[70,42],92,'walk-'+str(i))
 # Freeze only central head/neck/chest. Hands and both full leg chains remain their own phase.
 for ids,b in[([0,1],[53,27,72,60]),([4,5],[55,31,74,60]),([2,3],[64,31,80,59])]:freeze(walk,ids[0],ids[1:],[b])
 # Matte hair: small blue/ice marks in the side-view crown become the existing navy material.
 for i in[2,3]:
  for y in range(28,42):
   for x in range(54,74):
    if walk[i].getpixel((x,y))[:3]==art.C[5]and walk[i].getpixel((x,y))[3]:walk[i].putpixel((x,y),(*art.C[0],255))
 for i,im in idle.items():clean(im,'idle'+str(i))
 for i,im in walk.items():clean(im,'walk'+str(i))
 walk[6]=walk[2].transpose(Image.Transpose.FLIP_LEFT_RIGHT);walk[7]=walk[3].transpose(Image.Transpose.FLIP_LEFT_RIGHT)
 mp={'tactical-idle':{i:idle[j].copy()for i,j in enumerate([0,1,2,1,0,1])},'tactical-walk':{i:walk[i]for i in range(8)}}
 for kind,poses in mp.items():
  for i,im in poses.items():io.save(im,f'ally/{kind}/frame-{i:03}.png','two-leg complete map pose; original phase schedule')
 board(mp)
 baseline=json.loads((OUT/'baseline.json').read_text());m=copy.deepcopy(baseline['maps_mapping']);note='女魔剑士地图修订：待机仅两腿，右臂随剑完成屈肘、展臂、抬肘；前后行走双腿沿固定髋部窄步道交替前迈，向下右臂从胸前持剑；左右行走并腿通过相与跨步相，保留双足。头颈及躯干基准固定，所有行走使用已有落地阴影。'
 m.update(revision=REV,review_note=note)
 for s in m['scenarios']:
  kind=s['id'];s.update(revision=REV,review_note=note,motion_review='../../../'+REV+'/README.md',ground_shadow={'path':'gold-knight-walk-v3-20261020/ground-shadow.png','size':[10,1.5],'offset':[0,-2]if kind=='tactical-idle'else[0,-1],'alpha':.30})
  w,h=s['output_frame_size'];atlas=Image.new('RGBA',(w*len(mp[kind]),h))
  for row in s['frame_mapping']:
   i=row['source_index'];p=OUT/f'ally/{kind}/frame-{i:03}.png';rel=f'../../../{REV}/ally/{kind}/frame-{i:03}.png';row.update(path=rel,output_path=rel,sha256=file_hash(p),bytes=p.stat().st_size);atlas.alpha_composite(mp[kind][i],(i*w,0))
  s['output_atlas']=io.save(atlas,f'ally/{kind}-atlas.png','original slot order')
 write(OUT/'mapping-draft.json',m);write(OUT/'asset-manifest.json',{'revision':REV,'palette':art.HEX,'assets':io.ASSETS,'registrations':art.REG,'battle_unchanged':True,'ground_shadow':m['scenarios'][0]['ground_shadow'],'whole_lower_body_replacement':True,'sword_arm_not_frozen':True})
 if publish:
  write(ROOT/'professions/class-11-ally/maps/frame_mapping.json',m)
  manifest=ROOT/'professions/class-11-ally/manifest.json';meta=json.loads(manifest.read_text());meta.update(revision=REV,maps_revision=REV,battle_revision='spellsword-complete-v1-20261023',review_record='../../'+REV+'/README.md');write(manifest,meta)
 print(json.dumps({'maps':14,'published':publish,'registrations':len(art.REG)}),flush=True)
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');main(p.parse_args().publish)
