#!/usr/bin/env python3
"""Focused gait/handedness corrections and the requested review-only second cut."""
import argparse,copy,hashlib,json,os
from functools import lru_cache
from pathlib import Path
from PIL import Image,ImageOps
import import_hunapu_dawn_v1 as H
ROOT=H.ROOT;REV='hunapu-dawn-gait-combo-v2-20261024';OUT=ROOT/REV;SRC=OUT/'source';MP=H.MP;BP=H.BP
H.OUT=OUT;H.SRC=SRC;H.REV=REV
FXHEX=['3976a8','a7d7e5','e4e5df','b9c5d1','e3bd83'];FXCOL=[tuple(bytes.fromhex(h))for h in FXHEX]
def write(p,d):H.write(p,d)
def sha(p):return H.sha(p)
@lru_cache(maxsize=1)
def olddata():return json.loads((SRC/'before-gallery.json').read_text())
def oldframe(kind,i):
 p=next(p for p in olddata()['profiles']if p['context']==kind);return Image.open(ROOT/p['newFrames'][str(i)]).convert('RGBA')
def mapreg(raw,label,back=False):
 fp=None if back else H.art_face(raw)[0];im,hb=H.solid_hair(raw,fp,back);scale=64/(im.getbbox()[3]-hb[1]);point=[(hb[0]+hb[2])/2,(hb[1]+hb[3])/2];return H.place(im,(128,96),scale,point,[64,48],label,95)
def maps():
 story={i:oldframe('story',i)for i in range(6)};walk={i:oldframe('tactical-walk',i)for i in range(8)};idle={i:oldframe('tactical-idle',i)for i in range(6)}
 sr=H.figures('story-gait-master.png',2,2);tr=H.figures('tactical-gait-master.png',2,3);rr=H.figures('tactical-right-master.png',2,1)
 # Preserve the existing story head, torso, arms, belt and scabbard. Replace
 # only the two leg phases; mirror legs alone for the opposite back step.
 reg=mapreg(sr[0],'story-back-left-low',True);base=story[2].copy();base.paste(reg.crop((51,76,79,96)),(51,76));story[2]=base;story[3]=base.copy();piece=base.crop((51,76,79,96));story[3].paste(ImageOps.mirror(piece),(51,76))
 for i,raw in[(4,sr[2]),(5,sr[3])]:
  reg=mapreg(raw,'story-side-'+str(i));base=story[4].copy();base.paste(reg.crop((39,75,91,96)),(39,75));story[i]=base
 # Native right and left phases both use standing then stride. They have
 # independently authored arm/weapon layering, never a mirrored whole body.
 pairs=[([0,1],[tr[0],tr[1]],True),([2,3],rr,False),([6,7],[tr[4],tr[5]],False)]
 for ids,raws,back in pairs:
  images=[mapreg(raw,'tactical-'+str(i),back)for i,raw in zip(ids,raws)]
  for n,i in enumerate(ids):
   walk[i]=images[n]
   if n:walk[i].paste(images[0].crop((0,0,128,73)),(0,0))
  if back:
   # One fixed upper body keeps anatomical left sword/right shield and
   # scabbard-independent opposite legs. The source supplies both phases.
   walk[ids[1]].paste(images[1].crop((0,73,128,96)),(0,73))
 return{'story':story,'tactical-walk':walk,'tactical-idle':idle}
def combo():
 result={};raws=H.figures('combo-master.png',4,2)
 for n,raw in enumerate(raws):
  slot=4+n if n<4 else 22+n-4;reference=oldframe('battle',40 if n<4 else 9);target,reference_face=H.art_face(reference);fp,fb=H.art_face(raw);im,hb=H.solid_hair(raw,fp);physical=max(fb[2]-fb[0],fb[3]-fb[1]);target_span=max(reference_face[2]-reference_face[0],reference_face[3]-reference_face[1]);scale=target_span/physical
  pose=H.place(im,(320,288),scale,fp,target,'combo-'+str(slot),reference.getbbox()[3]);result[slot]=pose;H.REG[-1].update(raw_face_box=fb,raw_hair_box=hb,physical_face_span=physical,registered_face_span=target_span)
 return result
def effects():
 raw=Image.open(SRC/'critical-spark-master.png').convert('RGBA');q=Image.new('RGBA',raw.size);q.putdata([(*min(FXCOL,key=lambda c:sum((a-b)**2 for a,b in zip(p[:3],c))),255)if p[3]>=235 and max(p[:3])>110 else(0,0,0,0)for p in raw.getdata()]);w,h=q.size;definitions={}
 # One shared grid scale keeps expansion and fading physical, instead of
 # independently enlarging the late sparse embers into a new impact.
 for n in range(6):
  c=n%3;r=n//3;cell=q.crop((round(c*w/3),round(r*h/2),round((c+1)*w/3),round((r+1)*h/2)));im=cell.resize((96,96),Image.Resampling.NEAREST);path=H.save(im,f'effects/spark-{n}.png','必杀斩击粒子阶段；白蓝为主，少量浅琥珀火星');key=f'review-hunapu-dawn-v2-spark-{n}';definitions[key]={'path':os.path.relpath(path,BP.parent),'frame_size':[24,24],'anchor':[12,12],'flip_origin_offset':[0,0]}
 return definitions
def main(publish=False):
 H.ASSETS.clear();H.REG.clear();H.CORES.clear();m=maps();b=combo();fx=effects();mm=json.loads((SRC/'before-maps-mapping.json').read_text());bm=json.loads((SRC/'before-battle-mapping.json').read_text());rel=lambda p,parent:os.path.relpath(p,parent)
 note='破晓勇士修订：向上明确左右腿交替，左右改为站直／跨步；剧情与大地图共用。战斗地图集中连续阴影，剑盾保持左手剑、右手盾，左右侧视分别制作前后遮挡，手握护手下方剑柄。普通与必杀各追加连贯一剑，必杀两次斩击加入短促白蓝火花。仅美术对照，不新增运行伤害结算。'
 for kind,poses in m.items():
  for i,im in poses.items():H.save(im,f'{kind}/frame-{i:03}.png','修订地图人物帧')
 for i,im in b.items():H.save(im,f'battle/frame-{i:03}.png','第一刀后连续回斩的新姿势')
 for s in mm['scenarios']:
  kind='story'if s['id']in['story','world']else s['id'];poses=m[kind];s.update(revision=REV,review_note=note,motion_review=rel(OUT/'README.md',MP.parent),frame_mapping=[]);size=list(next(iter(poses.values())).size);atlas=Image.new('RGBA',(len(poses)*size[0],size[1]))
  for i,im in poses.items():
   path=OUT/kind/f'frame-{i:03}.png';value=rel(path,MP.parent);s['frame_mapping'].append({'source_index':i,'source_frame':i,'output_index':i,'path':value,'output_path':value,'size':size,'bytes':path.stat().st_size,'sha256':sha(path)});atlas.alpha_composite(im,(i*size[0],0))
  s['output_atlas']=rel(H.save(atlas,kind+'-atlas.png','修订地图图集'),MP.parent)
  if kind.startswith('tactical'):s['ground_shadow']={'path':'hunapu-story-shadow-20261018/story-shadow.png','size':[8,2],'offset':[0,-.75],'alpha':.42,'kind':'continuous_compact_centered_tactical_shadow','source':'Reuse continuous compact story projection; fixed under pelvis, no scattered peripheral pixels.'}
 mm.update(revision=REV,review_note=note,status='review_candidate',runtime_integrated=False)
 for i in b:bm['frame_mapping'][str(i)]=rel(OUT/'battle'/f'frame-{i:03}.png',BP.parent)
 baseline={a['key']:a for a in olddata()['actions']};timeline={'effects':fx,'actions':{}}
 schedules={'original_class_21_promoted':[(99,105,4),(105,112,5),(112,115,6),(115,124,7),(124,128,38),(128,132,36),(132,138,31)],'original_class_21_critical':[(171,176,22),(176,183,23),(183,186,24),(186,194,25),(194,200,17)]}
 for key,segments in schedules.items():
  a=baseline[key];rows=copy.deepcopy(a['frames'])
  for start,end,slot in segments:
   for t in range(start,end):rows[t]['frame']=slot
  if 'critical'in key:
   for start in[162,181]:
    impact=[-10,-2]if start==162 else[-25,-18]
    for step,count,begin in[(0,2,0),(1,3,2),(2,2,5),(3,2,7),(4,2,9),(5,2,11)]:
     for t in range(start+begin,start+begin+count):rows[t].setdefault('effects',[]).append({'sprite':f'review-hunapu-dawn-v2-spark-{step}','position':[a['origin'][i]+rows[t]['offset'][i]+impact[i]for i in[0,1]],'flip':False})
  digest=hashlib.sha256(json.dumps(a['frames'],sort_keys=True,separators=(',',':')).encode()).hexdigest();timeline['actions'][key]={'source_frames_sha256':digest,'frames':rows,'note':note,'second_cut_window_zero_based':segments,'original_contact_tick':a['contactTick'],'second_cut_visual_only':True}
 write(OUT/'review-timeline.json',timeline);bm.update(revision=REV,review_note=note,status='review_candidate',runtime_integrated=False,review_timeline=rel(OUT/'review-timeline.json',BP.parent),qa_report=rel(OUT/'verification.json',BP.parent),batches=[{'id':'连贯第二剑与必杀火花','review':rel(OUT/'combo-light.png',BP.parent),'status':'review_candidate'}])
 bm['review_frame_sources']={str(i):40 if i<8 else 9 for i in b};bm['review_frame_labels']={str(i):'第一刀后连续回斩 · '+str(i)for i in b}
 # Atlas is audit-only; the mapping retains every unchanged V1 source file.
 order=sorted(int(i)for i in bm['frame_mapping']);atlas=Image.new('RGBA',(320*len(order),288))
 for n,i in enumerate(order):atlas.alpha_composite(Image.open((BP.parent/bm['frame_mapping'][str(i)]).resolve()).convert('RGBA'),(n*320,0))
 bm.update(output_atlas=rel(H.save(atlas,'battle-atlas.png','原战斗图加八个连续回斩姿势'),BP.parent),output_atlas_order=order)
 H.board([(k+' '+str(i),im)for k,poses in m.items()for i,im in poses.items()if k!='tactical-idle'or i<3],'maps','破晓勇士 · 腿部换相与剑盾手位',4);H.board([(str(i),im)for i,im in b.items()],'combo','第一刀之后 · 连续回斩',4)
 write(OUT/'mapping-drafts.json',{'maps':mm,'battle':bm});write(OUT/'asset-manifest.json',{'revision':REV,'palette':H.HEX,'effects_palette':FXHEX,'assets':H.ASSETS,'registrations':H.REG,'runtime_integrated':False,'world_reuses_story':True,'second_cut_windows':schedules})
 if publish:write(MP,mm);write(BP,bm)
 print(json.dumps({'published':publish,'map_slots':sum(map(len,m.values())),'new_combo_poses':len(b),'spark_phases':len(fx),'assets':len(H.ASSETS)}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');a=p.parse_args();main(a.publish)
