#!/usr/bin/env python3
"""Stage only class14's three idle drawings and six original slots.

No shared build/export. No edits to walk, battle or any v1 image.
The final source is registered from OUT/pose-inputs.json. Never copy a neck.
--publish is an explicit final operation and only patches tactical-idle.
"""
import argparse,copy,hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw
from export_gallery import font
from import_knight_redraw_v3 import parts
ROOT=Path(__file__).resolve().parents[1]
REV='brigand-idle-shoulders-v2-20261023';OUT=ROOT/REV;SRC=OUT/'source'
MAP=ROOT/'professions/class-14-enemy/maps/frame_mapping.json'
BATTLE=ROOT/'professions/class-14-enemy/battle/frame_mapping.json'
HEX=['172638','4f4f7d','bbc1d6','dda77d','373e64','a394b1']
COLORS=[tuple(bytes.fromhex(h))for h in HEX];ORDER=[0,1,2,1,0,1]

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def source_path(p):
 p=(SRC/p).resolve();assert p.is_relative_to(SRC.resolve());return p

def save(im,p):
 p.parent.mkdir(parents=True,exist_ok=True)
 if im.mode=='RGBA':
  colors=sorted(set(im.getdata()));assert len(colors)<=256
  q=Image.new('P',im.size);q.putpalette([v for c in colors for v in c[:3]]+[0]*(768-len(colors)*3));lookup={c:i for i,c in enumerate(colors)};q.putdata([lookup[c]for c in im.getdata()]);q.info['transparency']=bytes(c[3]for c in colors);assert q.convert('RGBA').tobytes()==im.tobytes()
 else:q=im
 q.save(p,optimize=True)
 return {'path':'../../../'+p.relative_to(ROOT).as_posix(),'size':list(im.size),'bytes':p.stat().st_size,'sha256':digest(p)}

def prepare():
 SRC.mkdir(parents=True,exist_ok=True)
 if not(OUT/'baseline.json').exists():
  m=json.loads(MAP.read_text());idle=next(s for s in m['scenarios']if s['id']=='tactical-idle')
  write(OUT/'baseline.json',{'maps':m,'maps_sha256':digest(MAP),'battle_sha256':digest(BATTLE),'idle_asset_hashes':{r['path']:digest((MAP.parent/r['path']).resolve())for r in idle['frame_mapping']}})
 if not(OUT/'pose-inputs.json').exists():write(OUT/'pose-inputs.json',{'status':'awaiting_final_generated_source','poses':[],'fixed_lower_body':None,'head_region':[34,18,62,40],'neck_region':[40,31,59,49],'neck_bridge_rows':[40,41,42,43],'target_head':[48,34],'target_hip':[48,55.3]})

def register(spec):
 raw=Image.open(source_path(spec['source'])).convert('RGBA').crop(spec['bounds']);palette={}
 def material(rgb):
  if rgb not in palette:palette[rgb]=min(COLORS,key=lambda c:sum((a-b)**2 for a,b in zip(rgb,c)))
  return palette[rgb]
 raw.putdata([(*material(p[:3]),255)if p[3]>=spec.get('alpha_threshold',200)else(0,0,0,0)for p in raw.getdata()])
 if spec.get('hair_box'):
  b=spec['hair_box']
  for y in range(b[1],b[3]):
   for x in range(b[0],b[2]):
    p=raw.getpixel((x,y))
    if p[3]and p[:3]!=COLORS[3]:raw.putpixel((x,y),(*COLORS[0],255))
 size=[round(raw.width*spec['scale']),round(raw.height*spec['scale'])];im=raw.resize(size,Image.Resampling.NEAREST);ratio=[size[i]/raw.size[i]for i in range(2)];delta=[round(spec['target_head'][i]-spec['head'][i]*ratio[i])for i in range(2)];out=Image.new('RGBA',(96,96));out.alpha_composite(im,tuple(delta))
 count=lambda q:sum(p[3]>0 for p in q.getdata())
 assert count(out)==count(im),'complete pose must fit; never crop feet to register'
 actual={key:[delta[i]+spec[key][i]*ratio[i]for i in range(2)]for key in['head','hip']}
 return out,{**spec,'source_sha256':digest(source_path(spec['source'])),'registered_size':size,'translation':delta,'actual_landmarks':actual,'clipped_pixels':0,'method':'uniform whole-pose scale and integer translation; no neck or shoulder patch'}

def preview(poses,light):
 bg=(220,222,216)if light else(32,45,53);fg=(23,38,56)if light else(235,243,242);records=[]
 for scale in[1,4]:
  cell=128 if scale==1 else 384;height=170 if scale==1 else 460;top=35 if scale==1 else 50;im=Image.new('RGB',(cell*4,height),bg);d=ImageDraw.Draw(im)
  d.text((cell*2,18 if scale==1 else 26),'断路匪待机 · 0 / 1 / 2 / 1',anchor='mm',font=font(14 if scale==1 else 20),fill=fg)
  for col,(idx,ticks)in enumerate(zip([0,1,2,1],[14,8,14,8])):
   actor=poses[idx].resize((96*scale,96*scale),Image.Resampling.NEAREST);im.paste(actor,(col*cell+(cell-96*scale)//2,top),actor);d.text((col*cell+cell//2,height-18),f'原槽{idx} · {ticks} ticks',anchor='mm',font=font(12 if scale==1 else 16),fill=fg)
  records.append(save(im,OUT/('loop-'+('native-'if scale==1 else'')+('light.png'if light else'dark.png'))))
 return records

def stage():
 prepare();recipe=json.loads((OUT/'pose-inputs.json').read_text());assert len(recipe['poses'])==3,'final three source poses are still pending'
 poses=[];registrations=[]
 for spec in recipe['poses']:
  im,reg=register(spec);poses.append(im);registrations.append(reg)
 # A single lower body is permitted only below the moving shoulder/hand area.
 # It is a rigid copied source region; preserve the entire authored legs/feet.
 lower=recipe.get('fixed_lower_body')
 if lower:
  if 'reference_pose' in lower:
   reference=poses[int(lower['reference_pose'])].copy();reference_hash=hashlib.sha256(reference.tobytes()).hexdigest()
  else:
   p=(ROOT/lower['path']).resolve();assert p.is_relative_to(ROOT);reference=Image.open(p).convert('RGBA');reference_hash=digest(p)
  assert reference.size==(96,96)
  box=lower['box'];assert box[1]>=57 and box==[0,box[1],96,96]
  for im in poses:im.paste(reference.crop(box),box[:2])
  lower={**lower,'sha256':reference_hash,'method':'same intact lower-body crop, no limb rearrangement'}
 atlas=Image.new('RGBA',(576,96));records=[]
 for slot,idx in enumerate(ORDER):
  record=save(poses[idx],OUT/'frames'/f'frame-{slot:03}.png');record.update(source_index=slot,source_frame=slot,output_index=slot,canonical_frame=idx,output_path=record['path'],revision=REV,art_status='review_candidate');records.append(record);atlas.alpha_composite(poses[idx],(slot*96,0))
 atlas_record=save(atlas,OUT/'idle-atlas.png');previews=preview(poses,False)+preview(poses,True)
 current=json.loads(MAP.read_text());prior=next(s for s in current['scenarios']if s['id']=='tactical-idle');candidate=copy.deepcopy(prior)
 for row,new in zip(candidate['frame_mapping'],records):row.update(new)
 candidate.update(output_atlas=atlas_record['path'],revision=REV,review_note='待机小幅左右扭肩；连续颈部与V领色面、稍收窄肩幅。头腰与脚底保持原点，原相位顺序和节奏保留。',motion_review={'revision':REV,'registration':registrations,'fixed_lower_body':lower,'neck_region':recipe['neck_region'],'old_neck_frame_reused':False,'native_timing_modified':False,'runtime_integrated':False})
 write(OUT/'idle-scenario-draft.json',candidate);write(OUT/'asset-manifest.json',{'revision':REV,'palette':HEX,'registrations':registrations,'fixed_lower_body':lower,'records':records,'atlas':atlas_record,'previews':previews,'old_neck_frame_reused':False,'runtime_integrated':False,'user_visual_acceptance':'pending'})
 print('Staged exactly 3 idle poses / 6 native slots; no mapping published.',flush=True)

def check():
 recipe=json.loads((OUT/'pose-inputs.json').read_text());meta=json.loads((OUT/'asset-manifest.json').read_text());candidate=json.loads((OUT/'idle-scenario-draft.json').read_text());baseline=json.loads((OUT/'baseline.json').read_text());old=next(s for s in baseline['maps']['scenarios']if s['id']=='tactical-idle');checks=[];neck=[]
 def require(value,label):assert value,label;checks.append(label)
 require(candidate['timing']==old['timing'],'original 0/1/2/1 and14/8/14/8 timing')
 require(candidate['directions']==old['directions']and candidate['source_aliases']==old['source_aliases'],'original idle directions and slot aliases')
 require(digest(BATTLE)==baseline['battle_sha256'],'battle mapping unchanged')
 current=json.loads(MAP.read_text());require([s for s in current['scenarios']if s['id']!='tactical-idle']==[s for s in baseline['maps']['scenarios']if s['id']!='tactical-idle'],'walk and other map scenarios unchanged')
 for path,sha in baseline['idle_asset_hashes'].items():require(digest((MAP.parent/path).resolve())==sha,'previous v1 idle asset preserved '+path)
 poses=[]
 for idx in range(3):
  im=Image.open(OUT/'frames'/f'frame-{idx:03}.png').convert('RGBA');poses.append(im);require(set(im.getchannel('A').getdata())<={0,255},'clean alpha '+str(idx));require({p[:3]for p in im.getdata()if p[3]}<=set(COLORS),'six matte colors '+str(idx));require(len(parts((x,y)for y in range(96)for x in range(96)if im.getpixel((x,y))[3]))==1,'complete connected figure '+str(idx))
  b=recipe['neck_region'];skin=parts((x,y)for y in range(b[1],b[3])for x in range(b[0],b[2])if im.getpixel((x,y))==(*COLORS[3],255));bridges=[c for c in skin if min(y for x,y in c)<=38 and max(y for x,y in c)>=44]
  require(bool(bridges),'face and neck enter V-collar as one skin component '+str(idx));bridge=max(bridges,key=len);widths={str(y):len([p for p in bridge if p[1]==y])for y in recipe['neck_bridge_rows']};require(min(widths.values())>=2,'neck has visible width through shadow/collar band '+str(idx));neck.append({'frame':idx,'connected_skin_pixels':len(bridge),'neck_row_widths':widths})
 for key in['head','hip']:
  actual=[r['actual_landmarks'][key]for r in meta['registrations']]
  require(all(max(p[a]for p in actual)-min(p[a]for p in actual)<=1.5 for a in[0,1]),key+' registration remains fixed')
 if meta.get('fixed_lower_body'):
  box=meta['fixed_lower_body']['box'];require(all(im.crop(box).tobytes()==poses[0].crop(box).tobytes()for im in poses),'intact fixed legs and feet')
 require(all(im.getbbox()[3]==poses[0].getbbox()[3]for im in poses),'same foot baseline')
 for alias,source in[(3,1),(4,0),(5,1)]:require(Image.open(OUT/'frames'/f'frame-{alias:03}.png').convert('RGBA').tobytes()==poses[source].tobytes(),'exact slot alias '+str(alias))
 write(OUT/'checks.json',{'status':'structural_passed','checks':len(checks),'neck':neck,'registration':meta['registrations'],'fixed_lower_body':meta['fixed_lower_body'],'visual_review_required':['shoulder twist direction and amount','neck/collar seams','unbroken hands and axe'],'runtime_integrated':False});print('Focused idle checks:',len(checks),flush=True)

def publish():
 check();candidate=json.loads((OUT/'idle-scenario-draft.json').read_text());current=json.loads(MAP.read_text());before=copy.deepcopy(current);idx=next(i for i,s in enumerate(current['scenarios'])if s['id']=='tactical-idle');current['scenarios'][idx]=candidate
 require=lambda v:None if v else(_ for _ in()).throw(AssertionError('non-idle mapping changed'))
 require({k:v for k,v in before.items()if k!='scenarios'}=={k:v for k,v in current.items()if k!='scenarios'});require([s for s in before['scenarios']if s['id']!='tactical-idle']==[s for s in current['scenarios']if s['id']!='tactical-idle'])
 write(OUT/'maps-before-publish.json',before);write(MAP,current);write(OUT/'publish-proof.json',{'only_scenario_changed':'tactical-idle','top_level_fields_unchanged':True,'other_scenarios_unchanged':True,'runtime_integrated':False});print('Published tactical-idle only.',flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');p.add_argument('--check',action='store_true');p.add_argument('--publish',action='store_true');a=p.parse_args()
 if a.prepare:prepare()
 elif a.publish:publish()
 elif a.check:check()
 else:stage()
