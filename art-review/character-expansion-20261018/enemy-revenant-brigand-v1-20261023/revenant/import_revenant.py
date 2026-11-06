#!/usr/bin/env python3
"""Import inspected whole-pose art using explicit head/hip registration only.
Reads source/import-plan.json written after reviewing the generated sheets.
Writes this candidate directory only; does not publish gallery or game changes.
"""
from pathlib import Path
from PIL import Image,ImageDraw
import hashlib,json,math
OUT=Path(__file__).resolve().parent
BASE=OUT.parent
ROOT=BASE.parent
REV=BASE.name
PALETTE=['172638','4f4f7d','bbc1d6','aaa6bc','373e64','a394b1']
COLORS=[tuple(bytes.fromhex(h))for h in PALETTE]
ASSETS=[];REG=[]
def read(p):return json.loads(p.read_text())
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def shift(im,dx,dy=0):
 result=Image.new('RGBA',im.size);result.alpha_composite(im,(dx,dy));return result

def save(im,rel,purpose):
 p=OUT/rel;p.parent.mkdir(parents=True,exist_ok=True)
 colors=sorted(set(im.getdata()))
 if im.mode=='RGBA' and len(colors)<=256:
  q=Image.new('P',im.size);q.putpalette([v for c in colors for v in c[:3]]+[0]*(768-len(colors)*3));lookup={c:i for i,c in enumerate(colors)};q.putdata([lookup[c]for c in im.getdata()]);q.info['transparency']=bytes(c[3]for c in colors)
  assert q.convert('RGBA').tobytes()==im.tobytes();q.save(p,optimize=True)
 else:im.save(p,optimize=True)
 record={'path':str(p.relative_to(ROOT)),'size':list(im.size),'bytes':p.stat().st_size,'sha256':digest(p),'purpose':purpose};ASSETS.append(record)
 return '../../../'+record['path']

def quantize(im):
 cache={}
 def mapped(p):
  if p[3]<128:return (0,0,0,0)
  rgb=p[:3]
  if rgb not in cache:cache[rgb]=min(COLORS,key=lambda c:sum((a-b)**2 for a,b in zip(c,rgb)))
  return (*cache[rgb],255)
 result=Image.new('RGBA',im.size);result.putdata([mapped(p)for p in im.getdata()]);return result

def registered(record):
 path=(OUT/record['path']).resolve();image=Image.open(path).convert('RGBA')
 if record.get('crop'):image=image.crop(tuple(record['crop']))
 # A native anatomical head/neck or hip landmark is mandatory. Bounds-centroid
 # registration is forbidden because reaching arms change the silhouette bounds.
 assert record.get('landmark_kind') in ['head_neck','hip','native_ground_residue']
 image=quantize(image)
 if record.get('flat_hair_box'):
  box=record['flat_hair_box'];pixels=image.load()
  for y in range(box[1],box[3]):
   for x in range(box[0],box[2]):
    if pixels[x,y][3] and pixels[x,y][:3] in [COLORS[0],COLORS[1],COLORS[4]]:pixels[x,y]=(*COLORS[0],255)
 scale=float(record['scale']);dims=[max(1,round(s*scale))for s in image.size];small=image.resize(dims,Image.Resampling.NEAREST)
 point=record['source_landmark'];target=[v*4 for v in record['target_native_landmark']]
 ratio=[dims[i]/image.size[i]for i in range(2)];delta=[round(target[i]-point[i]*ratio[i])for i in range(2)]
 size=[96,96]if record['kind']=='idle'else[128,96]if record['kind']=='walk'else[320,288]
 result=Image.new('RGBA',size);result.alpha_composite(small,tuple(delta))
 before=sum(p[3]>0 for p in small.getdata());after=sum(p[3]>0 for p in result.getdata())
 assert before==after,(record['kind'],record['frame'],'clipped',delta,dims)
 actual=[delta[i]+point[i]*ratio[i]for i in range(2)];error=max(abs(actual[i]-target[i])for i in range(2));assert error<=.51
 REG.append({**record,'source_sha256':digest(path),'uniform_scale':scale,'resampled_size':dims,'translation':delta,'actual_landmark':actual,'target_landmark':target,'landmark_error_pixels':error,'clipped_pixels':0,'method':'whole pose uniform scaling and integer translation, no joint warp or bounding-box-centroid alignment'})
 return result

def board(entries,name,light=False):
 cw,ch=(344,330)if name=='battle'else(280,250);cols=4
 out=Image.new('RGB',(cw*cols,ch*math.ceil(len(entries)/cols)),(227,227,222)if light else(31,39,53));d=ImageDraw.Draw(out)
 for i,(label,im)in enumerate(entries):
  if name=='maps':im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
  x=i%cols*cw+(cw-im.width)//2;y=i//cols*ch+8;out.paste(im,(x,y),im);d.text((i%cols*cw+12,i//cols*ch+ch-20),label,fill=(25,31,47)if light else(235,236,231))
 save(out,f'{name}-{"light"if light else"dark"}.png','registered full-pose visual audit on '+('light'if light else'dark')+' background')

def build():
 baseline=read(OUT/'source/native-baseline.json');plan=read(OUT/'source/import-plan.json');poses={k:{}for k in ['idle','walk','battle']}
 for row in plan['poses']:
  assert row['frame']not in poses[row['kind']];poses[row['kind']][int(row['frame'])]=registered(row)
 assert set(poses['idle'])=={0,1,2};assert set(poses['walk'])==set(range(8));assert set(poses['battle'])==set(baseline['newly_drawn_battle_frames'])
 poses['battle'][49]=Image.new('RGBA',(320,288))
 arc=Image.open(OUT/'source/native-claw-arc-047.png').convert('RGBA').resize((320,288),Image.Resampling.NEAREST)
 poses['battle'][47]=poses['battle'][48].copy();poses['battle'][47].alpha_composite(arc)
 poses['battle'][83]=shift(poses['battle'][33],-64);poses['battle'][98]=poses['battle'][83].copy()
 assert sum(p[3]>0 for p in poses['battle'][83].getdata())==sum(p[3]>0 for p in poses['battle'][33].getdata())
 maps={'schema_version':1,'revision':REV,'character_id':'class-11-enemy','actor_id':'class-11-enemy','display_name':'敌方蚀躯','display_class_name':'蚀躯','class_id':11,'source_side':'enemy','status':'review_candidate','runtime_integrated':False,'review_note':'蚀躯完整姿态重绘；蓝紫六色、冷灰紫皮肤与纯色发块。原动作与时序保持，注册按头颈/腰胯点，无额外整体抖动。','scenarios':[]}
 map_entries=[]
 for kind,context,order in [('idle','tactical-idle',[0,1,2,1,0,1]),('walk','tactical-walk',list(range(8)))]:
  source=next(s for s in baseline['map_scenarios']if s['id']==context);scenario={k:v for k,v in source.items()if k not in ['required_drawn_frames']}
  scenario['source_atlas']='../../../'+source['source_atlas'];scenario.update(output_frame_size=[96,96]if kind=='idle'else[128,96],output_anchor=[48,80]if kind=='idle'else[64,96],logical_render_scale=.25,status='review_candidate',revision=REV,frame_mapping=[])
  w,h=scenario['output_frame_size'];atlas=Image.new('RGBA',(w*len(order),h))
  for index,frame in enumerate(order):
   im=poses[kind][frame];path=save(im,f'{context}/frame-{index:03}.png','whole registered native '+context+' pose');atlas.alpha_composite(im,(index*w,0))
   scenario['frame_mapping'].append({'source_index':index,'source_frame':index,'output_index':index,'path':path,'output_path':path,'size':[w,h],'bytes':ASSETS[-1]['bytes'],'sha256':ASSETS[-1]['sha256'],'revision':REV,'art_status':'review_candidate'})
   if kind=='walk'or index<3:map_entries.append((kind+' '+str(index),im))
  scenario['output_atlas']=save(atlas,f'{context}-atlas.png','original source slot order');maps['scenarios'].append(scenario)
 body=baseline['body'];order=sorted(poses['battle']);atlas=Image.new('RGBA',(320*len(order),288));paths={};records=[];battle_entries=[]
 for n,frame in enumerate(order):
  im=poses['battle'][frame];paths[str(frame)]=save(im,f'battle/frame-{frame:03}.png','native body slot; blank49/BG aliases/exact claw arc retained');atlas.alpha_composite(im,(n*320,0));records.append({'source_frame':frame,'path':paths[str(frame)],'bytes':ASSETS[-1]['bytes'],'sha256':ASSETS[-1]['sha256'],'size':[320,288]})
  if frame not in [83,98]:battle_entries.append(('source '+str(frame),im))
 battle={'schema_version':1,'character_id':'class-11-enemy','display_name':'敌方蚀躯','display_class_name':'蚀躯','original_class_id':11,'source_side':'enemy','source_atlas':'../../../'+body['path'],'source_frame_size':body['frame_size'],'output_frame_size':[320,288],'source_anchor':body['anchor'],'output_anchor':[160,256],'source_columns':body['columns'],'source_oam_frame_count':body['source_oam_frame_count'],'source_idle_frame':83,'source_frame_count':body['frames'],'frame_mapping':paths,'canonical_frames':body['unique_art_frames'],'required_source_frames':body['required_source_frames'],'variant_keys':list(baseline['variants']),'records':records,'output_atlas_frame_order':order,'output_atlas':save(atlas,'battle-atlas.png','required source battle slots'),'status':'review_candidate','revision':REV,'runtime_integrated':False,'palette':PALETTE,'review_note':'原下沉/消失/重现/抬臂/挥击/回位的472tick逐帧保留；接触tick274，不新增打击。47叠55像素原生弧，49透明，83/98按BG位置复用33。','batches':[{'id':'full-pose-review','review':'../../../'+str((OUT/'battle-dark.png').relative_to(ROOT)),'status':'review_candidate'}]}
 for name,entries in [('maps',map_entries),('battle',battle_entries)]:
  for light in [False,True]:board(entries,name,light)
 maps['review_note']+=' 原生脚位终核：上行0左支撑/1右支撑，下行4右支撑/5左支撑；完整新图已对应归位，原16tick不变。'
 for scene in maps['scenarios']:
  if scene['id']=='tactical-walk':scene['motion_review']={'native_foot_phase':'../../../'+str((OUT/'native-foot-phase-checks.json').relative_to(ROOT)),'head_hip_registration':'../../../'+str((OUT/'map-registration-checks.json').relative_to(ROOT)),'source_timing_modified':False,'complete_pose_assignment':{'0':'generated-up-phase1','1':'generated-up-phase0','4':'generated-down-phase1','5':'generated-down-phase0'}}
 write(OUT/'mapping-drafts.json',{'professions/class-11-enemy/maps/frame_mapping.json':maps,'professions/class-11-enemy/battle/frame_mapping.json':battle})
 write(OUT/'asset-manifest.json',{'runtime_integrated':False,'revision':REV,'palette':PALETTE,'assets':ASSETS,'registration':REG,'user_visual_acceptance':'pending'})
 print('Prepared',len(ASSETS),'candidate assets; shared files untouched')
if __name__=='__main__':build()
