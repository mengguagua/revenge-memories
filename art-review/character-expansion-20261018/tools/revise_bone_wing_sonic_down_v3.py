#!/usr/bin/env python3
"""Aim the accepted sonic pulse at the lower target. Gallery only."""
import argparse,copy,json,math
from PIL import Image,ImageChops,ImageDraw
import revise_bone_wing_sonic_v2 as V
ROOT=V.ROOT;REV='bone-wing-sonic-down-v3-20261024';OUT=ROOT/REV;SRC=OUT/'source';BASE=V.BASE;ID=V.ID;PID=V.PID
V.REV=REV;V.OUT=OUT;V.SRC=SRC;V.FX_PREFIX='review-bone-wing-sonic-down-v3-'
MOUTH=[88,134];TARGET=[208,144]
def author():
 b=V.read(V.BUNDLE);baseline=V.read(SRC/'baseline.json');old=baseline['target_action'];a=next(a for a in b['actions']if a['id']==ID);p=next(p for p in b['profiles']if p['id']==PID);assert a['frames']==old['frames']
 raw=Image.open(SRC/'head-down-master.png').convert('RGBA');region=[(470,815),(540,850),(500,942),(445,1000),(438,1105),(350,1183),(243,1130),(244,1080),(304,1018),(386,947),(414,891)];mask=Image.new('L',raw.size);ImageDraw.Draw(mask).polygon(region,fill=255);head=V.A.clean(raw);head.putalpha(ImageChops.multiply(head.getchannel('A'),mask));head=head.crop((220,800,550,1200));head=head.resize((round(head.width*.28),round(head.height*.28)),Image.Resampling.NEAREST);piece=Image.new('RGBA',(384,544));piece.alpha_composite(head,(round(190-(490-220)*.28),round(330-(850-800)*.28)))
 # Remove the former horizontal skull only; preserve the wing/claw occlusion.
 erase=Image.new('L',(384,544));ImageDraw.Draw(erase).polygon([(62,306),(153,300),(188,312),(189,339),(173,370),(153,386),(62,386)],fill=255)
 allowed=Image.new('L',(384,544));allowed.paste(erase,(0,0));allowed=ImageChops.lighter(allowed,piece.getchannel('A'));slots=[]
 for source in range(17,24):
  body=Image.open(ROOT/p['newFrames'][str(source)]).convert('RGBA');im=body.copy();im.paste((0,0,0,0),(0,0),erase);im.alpha_composite(piece);im.paste(body.crop((174,342,247,386)),(174,342));bg=Image.new('RGBA',im.size);bg.alpha_composite(im,(-64,0));assert sum(q[3]>0 for q in bg.getdata())==sum(q[3]>0 for q in im.getdata());slot=61+source-17;p['newFrames'][str(slot)]=V.save(bg,f'battle/frame-{slot:03}.png','下压头颈、朝下方目标张嘴；沿用当前帧双翼、躯干、尾与爪');slots.append({'source':source,'revised':slot})
 allowed.save(OUT/'head-change-mask.png',optimize=True);piece.save(OUT/'registered-head.png',optimize=True)
 point=[MOUTH[0]+89,MOUTH[1]-40];delta=[TARGET[i]-point[i]for i in(0,1)];distance=math.hypot(*delta);unit=[n/distance for n in delta];angle=math.degrees(math.atan2(delta[1],delta[0]));effects={};ids=[];tip=[]
 for i in range(6):
  key=f'review-bone-wing-sonic-v2-{i}';meta=b['effects'][key];im=Image.open(ROOT/meta['path']).convert('RGBA');bb=im.getbbox();front=(bb[2]-meta['anchor'][0]*4)/4;tip.append(front);canvas=Image.new('RGBA',(512,512));canvas.alpha_composite(im,(128-round(meta['anchor'][0]*4),128-round(meta['anchor'][1]*4)));rotated=canvas.rotate(-angle,Image.Resampling.NEAREST,center=(128,128));eid=V.FX_PREFIX+str(i);path=V.save(rotated,f'effects/wave-{i}.png','复用已确认音波像素与颜色，仅按嘴部至下方目标方向旋转注册');effects[eid]={**meta,'path':path,'frame_size':[128,128],'anchor':[32,32]};ids.append(eid)
 rows=copy.deepcopy(old['revisedFrames']);lookup={r['source']:r['revised']for r in slots};travel=max(0,distance-tip[-1])
 for t,row in enumerate(rows):
  if 236<=t<=276:row['frame']=lookup[a['frames'][t]['frame']]
  if row['effects']:
   assert 243<=t<=274;k=t-243;phase=int(row['effects'][0]['sprite'].rsplit('-',1)[1]);row['effects']=[{'sprite':ids[phase],'position':[MOUTH[j]+row['offset'][j]+unit[j]*travel*k/31 for j in(0,1)],'flip':False}]
 a['revisedFrames']=rows;a['effectRevision']=REV;a['_reviewCloseCamera']={'offset':[-64,-112],'size':[224,192],'purpose':'Keep complete downward head, accepted rotated pulse and lower target inside preview'};a['notes']=old['notes'].split(' 本次修改记录：')[0]+' 朝向V3：头颈向下压，音波从嘴部斜向下方目标推进，目标参考点为[208,144]；保留已确认音波颜色、形状、扩散阶段与原507帧节奏。'
 p['links']=[x for x in p['links']if x.get('href')!=REV+'/README.md']+[{'label':'音波朝下方目标V3','href':REV+'/README.md'}];b['effects'].update(effects);V.write(V.BUNDLE,b);V.write(OUT/'effect-contract.json',{'target':TARGET,'mouth_at_release':point,'mouth_before_actor_offset':MOUTH,'direction_unit':unit,'clockwise_angle_degrees':angle,'anchor_travel':travel,'accepted_effect_geometry_and_palette_reused':True,'head_registration':{'source_neck_joint':[490,850],'fixed_neck_joint':[190,330],'uniform_scale':.28,'source_polygon':region},'head_slots':slots,'mouth_open_ticks':[236,276],'effect_ticks':[243,274],'contact_tick':243,'total_ticks':507,'runtime_integrated':False});V.write(OUT/'asset-manifest.json',{'assets':V.ASSETS,'generator':'built-in imagegen redraws head/neck only; accepted sonic images are reoriented by nearest-neighbour compositing','prompt':'source/head-down-prompt.txt','runtime_integrated':False})
def verify(d):
 base=V.read(SRC/'baseline.json');old=base['target_action'];a=next(a for a in d['actions']if a['id']==ID);p=next(p for p in d['profiles']if p['id']==PID);c=V.read(OUT/'effect-contract.json');checks=0;errors=[]
 assert a['frames']==old['frames']and a['fps']==old['fps']and a['contactTick']==old['contactTick']and len(a['revisedFrames'])==507 and a['ready'];checks+=5
 for path,h in {**base['asset_hashes'],**{base['base_bundle']['effects'][k]['path']:h for k,h in base['effect_hashes'].items()}}.items():assert V.sha(ROOT/path)==h;checks+=1
 allowed=Image.open(OUT/'head-change-mask.png').convert('L');outside=ImageChops.invert(allowed)
 for r in c['head_slots']:
  im=Image.open(ROOT/p['newFrames'][str(r['revised'])]).convert('RGBA');q=Image.new('RGBA',im.size);q.alpha_composite(im,(64,0));source=Image.open(ROOT/p['newFrames'][str(r['source'])]).convert('RGBA');diff=ImageChops.difference(q,source)
  assert not any(ImageChops.multiply(ch,outside).getbbox()for ch in diff.split());assert q.crop((174,342,247,386)).tobytes()==source.crop((174,342,247,386)).tobytes();checks+=2
 for t,(before,row)in enumerate(zip(old['revisedFrames'],a['revisedFrames'])):
  assert{k:v for k,v in before.items()if k not in['frame','effects']}=={k:v for k,v in row.items()if k not in['frame','effects']};assert len(before['effects'])==len(row['effects']);checks+=2
  if not 236<=t<=276:assert row['frame']==before['frame'];checks+=1
  for revised,r in[(False,a['frames'][t]),(True,row)]:
   f=r['frame'];off=r['offset'];flip=True!=r['flip'];at=[a['origin'][i]+off[i]-p['anchor'][i]for i in(0,1)]
   if flip and f<p['sourceOamCutoff']:at=[at[i]+p['flipOriginOffset'][i]for i in(0,1)]
   im=V.E.load(p['newFrames'][str(f)])if revised else V.E.body_image(p['sourceAtlas'],f,tuple(p['sourceFrameSize']),p['sourceColumns']);box=V.S.V.box_at(im,at,p['sourceFrameSize'],flip);cam=a['closeCamera'];close=[a['origin'][i]+off[i]+cam['offset'][i]for i in(0,1)]+cam['size']
   for mode,view in[('full',a['viewport']),('close',close)]:
    checks+=1
    if V.S.V.outside(box,view):errors.append({'tick':t,'mode':mode,'kind':'body','bounds':box})
   for fx in r['effects']:
    meta=d['effects'][fx['sprite']];im=V.E.load(meta['path']);at=[fx['position'][i]-meta['anchor'][i]for i in(0,1)];box=V.S.V.box_at(im,at,meta['frame_size'],False)
    for mode,view in[('full',a['viewport']),('close',close)]:
     checks+=1
     if V.S.V.outside(box,view):errors.append({'tick':t,'mode':mode,'kind':'effect','bounds':box})
    mouth=[MOUTH[i]+off[i]for i in(0,1)];assert fx['position'][1]>=mouth[1];v=[fx['position'][i]-mouth[i]for i in(0,1)];assert abs(v[0]*c['direction_unit'][1]-v[1]*c['direction_unit'][0])<1e-7;checks+=2
 for file,h in base['runtime_hashes'].items():assert V.sha(ROOT.parents[1]/file)==h;checks+=1
 assert not d['validation']['structuralIssues'];report={'passed':not errors,'checks':checks,'only_normal_attack_direction_changed':True,'all_previous_body_and_effect_files_unchanged':True,'accepted_sonic_phases_and_timing_preserved':True,'wings_claws_torso_tail_unchanged':True,'single_contact_display_frame':244,'frames':507,'aimed_at_lower_target':TARGET,'runtime_files_unchanged':True,'errors':errors};V.write(OUT/'verification.json',report);assert not errors,errors[:3];return report
def main():
 p=argparse.ArgumentParser();p.add_argument('--author',action='store_true');p.add_argument('--export',action='store_true');p.add_argument('--merge',action='store_true');a=p.parse_args()
 if a.author:author()
 d=V.build();print(json.dumps(verify(d),ensure_ascii=False),flush=True);V.previews(d)
 if a.export:V.export(d);d=V.build()
 if a.merge:V.merge(d)
if __name__=='__main__':main()
