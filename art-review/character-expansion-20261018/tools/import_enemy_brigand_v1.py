#!/usr/bin/env python3
"""Import class14 enemy whole drawings; never build/export the shared gallery.

Input: brigand/pose-inputs.json. Each pose declares a source sheet and bbox,
head/hip registration landmarks, a uniform scale, target landmarks and a hair
mask rectangle. Sources are retained. Run --inspect SHEET for component boxes.
--publish writes only professions/class-14-enemy review mappings, never actual/.
"""
import argparse,copy,hashlib,json,math
from pathlib import Path
from functools import lru_cache
from PIL import Image,ImageDraw,ImageFilter
from import_knight_redraw_v3 import parts
from export_gallery import font
ROOT=Path(__file__).resolve().parents[1]
REV='enemy-revenant-brigand-v1-20261023'
OUT=ROOT/REV/'brigand'; SRC=OUT/'source'
PALETTE=['172638','4f4f7d','bbc1d6','dda77d','373e64','a394b1']
COLORS=[tuple(bytes.fromhex(h)) for h in PALETTE]
ACTOR='class-14-enemy'
ASSETS=[];REG=[]

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def pixel_count(im):return sum(p[3]>0 for p in im.getdata())
def local_path(raw):
 p=(SRC/raw).resolve()
 assert p.is_relative_to(SRC.resolve()),'source file must stay inside brigand/source'
 return p
@lru_cache(maxsize=100000)
def material(rgb):return min(range(len(COLORS)),key=lambda i:sum((x-y)**2 for x,y in zip(rgb,COLORS[i])))
def inspect(path):
 im=Image.open(path).convert('RGBA')
 cs=parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))[3]>=128)
 return [{'bounds':[min(x for x,y in c),min(y for x,y in c),max(x for x,y in c)+1,max(y for x,y in c)+1],'pixels':len(c)}for c in cs if len(c)>1000]
def save(im,relative,purpose):
 p=OUT/relative;p.parent.mkdir(parents=True,exist_ok=True)
 # Exact indexed encoding; no lossy resizing beyond the declared art scale.
 if im.mode=='RGBA':
  colors=sorted(set(im.getdata()));assert len(colors)<=256
  q=Image.new('P',im.size);q.putpalette([x for c in colors for x in c[:3]]+[0]*(768-len(colors)*3));lookup={c:i for i,c in enumerate(colors)};q.putdata([lookup[c]for c in im.getdata()]);q.info['transparency']=bytes(c[3]for c in colors);assert q.convert('RGBA').tobytes()==im.tobytes()
 else:q=im
 q.save(p,optimize=True)
 ASSETS.append({'path':p.relative_to(ROOT).as_posix(),'purpose':purpose,'size':list(im.size),'bytes':p.stat().st_size,'sha256':digest(p),'alpha_bounds':im.getbbox()if im.mode=='RGBA'else None})
 return '../../../'+p.relative_to(ROOT).as_posix()
def register(label,spec):
 src=local_path(spec['source']);sheet=Image.open(src).convert('RGBA');im=sheet.crop(spec['bounds'])
 # Full pose clipping is forbidden: bboxes are connected-component extents.
 threshold=int(spec.get('alpha_threshold',128));out=Image.new('RGBA',im.size);out.putdata([(*COLORS[material(p[:3])],255)if p[3]>=threshold else(0,0,0,0)for p in im.getdata()])
 if spec.get('hair_box'):
  b=spec['hair_box']
  for y in range(b[1],b[3]):
   for x in range(b[0],b[2]):
    p=out.getpixel((x,y))
    if p[3]and p[:3]!=COLORS[3]:out.putpixel((x,y),(*COLORS[0],255))
 size=(320,256)if label.startswith('battle-')else(96,96)if label.startswith('idle-')else(128,96)
 scale=spec['scale'];dims=[round(im.width*scale),round(im.height*scale)]
 q=out.resize(dims,Image.Resampling.NEAREST);ratios=[dims[i]/im.size[i]for i in range(2)]
 delta=[round(spec['target_head'][i]-spec['head'][i]*ratios[i])for i in range(2)]
 canvas=Image.new('RGBA',size);canvas.alpha_composite(q,tuple(delta));assert pixel_count(canvas)==pixel_count(q),(label,'clipped pose',dims,delta)
 actual={k:[delta[i]+spec[k][i]*ratios[i]for i in range(2)]for k in ['head','hip']}
 if not label.startswith('battle-'):
  assert max(abs(actual['hip'][i]-spec['target_hip'][i])for i in range(2))<=1.5,(label,'hip not at registered center',actual['hip'],spec['target_hip'])
 REG.append({'label':label,'source':spec['source'],'source_sha256':digest(src),'source_bounds':spec['bounds'],'source_head':spec['head'],'source_hip':spec['hip'],'target_head':spec['target_head'],'target_hip':spec['target_hip'],'actual_landmarks':actual,'hair_box':spec.get('hair_box'),'alpha_threshold':threshold,'scale':scale,'size':dims,'translation':delta,'clipped_pixels':0,'method':'whole-pose uniform scale and integer translation; no joint warping'})
 return canvas

def board(entries,kind,light):
 cw,ch=(300,250)if kind=='maps'else(344,300);cols=4
 out=Image.new('RGB',(cw*cols,56+ch*math.ceil(len(entries)/cols)),(220,222,216)if light else(32,45,53));d=ImageDraw.Draw(out);fg=(23,38,56)if light else(235,243,242)
 d.text((out.width//2,25),'敌方断路匪 · '+('地图姿态'if kind=='maps'else'战斗姿态'),anchor='mm',font=font(21),fill=fg)
 for n,(label,im)in enumerate(entries):
  if kind=='maps':im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
  x=n%cols*cw+(cw-im.width)//2;y=56+n//cols*ch;out.paste(im,(x,y),im);d.text((n%cols*cw+cw//2,y+ch-20),label,anchor='mm',font=font(16),fill=fg)
 save(out,f'{kind}-{"light"if light else"dark"}.png','complete poses on light/dark review background')

def loops(poses):
 groups=[('idle',['idle-0','idle-1','idle-2','idle-1'],[14,8,14,8])]+[(name,[f'walk-{a}',f'walk-{a+1}',f'walk-{a}',f'walk-{a+1}'],[16]*4)for name,a in[('up',0),('right',2),('down',4),('left',6)]]
 for light in[False,True]:
  bg=(220,222,216)if light else(32,45,53);fg=(23,38,56)if light else(235,243,242);im=Image.new('RGB',(1152,1200),bg);d=ImageDraw.Draw(im)
  d.text((576,25),'断路匪 · 连续相位 / 固定头颈与腰胯',anchor='mm',font=font(20),fill=fg)
  for row,(name,keys,ticks)in enumerate(groups):
   for col,(key,tick)in enumerate(zip(keys,ticks)):
    sprite=poses[key];sprite=sprite.resize((sprite.width*2,sprite.height*2),Image.Resampling.NEAREST);x=col*288+(288-sprite.width)//2;y=50+row*230;im.paste(sprite,(x,y),sprite)
    d.text((col*288+144,y+212),f'{name} / {key} / {tick} ticks',anchor='mm',font=font(14),fill=fg)
  save(im,'map-loop-'+('light'if light else'dark')+'.png','consecutive native phases on light/dark background, no global actor translation')

def build(publish=False):
 spec=json.loads((OUT/'pose-inputs.json').read_text());assert not spec.get('pending_redraws'),('unresolved visual fixes',spec['pending_redraws']);native=json.loads((SRC/'native-baseline.json').read_text());body=native['body'];variants=native['variants']
 poses={k:register(k,v)for k,v in spec['poses'].items()}
 for key,s in spec.get('aliases',{}).items():
  ref=poses[s['source']];out=Image.new('RGBA',ref.size);out.alpha_composite(ref,tuple(s.get('translation',[0,0])));assert pixel_count(out)==pixel_count(ref),(key,'alias cropped');poses[key]=out
 # Verified original identities: background24 = OAM8 shifted -16X;
 # 31 = 24; frame14 = frame15 plus the original 77-pixel slash effect.
 for key,source,delta in [('battle-24','battle-8',[-64,0]),('battle-31','battle-24',[0,0])]:
  ref=poses[source];im=Image.new('RGBA',ref.size);im.alpha_composite(ref,tuple(delta));assert pixel_count(im)==pixel_count(ref),(key,'cropped alias');poses[key]=im
 n14=Image.open(SRC/'native-battle-014.png').convert('RGBA');n15=Image.open(SRC/'native-battle-015.png').convert('RGBA');fx=n14.copy()
 for y in range(n14.height):
  for x in range(n14.width):
   if n15.getpixel((x,y))[3]:assert n14.getpixel((x,y))==n15.getpixel((x,y));fx.putpixel((x,y),(0,0,0,0))
 assert pixel_count(fx)==77
 fx=fx.resize((320,256),Image.Resampling.NEAREST);save(fx,'native-slash-effect-014.png','unaltered original class14 slash arc, no additional hit')
 poses['battle-14']=fx.copy();poses['battle-14'].alpha_composite(poses['battle-15'])
 # A rigid copy of the same small axe head prevents independent sheets
 # changing blade size. Skin/cloth are never copied as weapon geometry.
 for group in spec.get('shared_equipment',[]):
  original=poses[group['source']];box=group['source_box'];seed=Image.new('L',original.size)
  for y in range(box[1],box[3]):
   for x in range(box[0],box[2]):
    p=original.getpixel((x,y))
    if p[3]and p[:3]in[COLORS[2],COLORS[5]]:seed.putpixel((x,y),255)
  seed=seed.filter(ImageFilter.MaxFilter(5));layer=Image.new('RGBA',original.size)
  for y in range(box[1],box[3]):
   for x in range(box[0],box[2]):
    p=original.getpixel((x,y))
    if seed.getpixel((x,y))and p[3]and p[:3]not in[COLORS[1],COLORS[3]]:layer.putpixel((x,y),p)
  group['reference_pixels']=pixel_count(layer);group['reference_rgba_sha256']=hashlib.sha256(layer.tobytes()).hexdigest()
  group['reference_path']=save(layer,'equipment/'+group['source']+'-axe.png','same complete drawn axe head, rigid placement only; no body or limb deformation')
  for target in group['targets']:
   im=poses[target['pose']];b=target['clear_box']
   for y in range(b[1],b[3]):
    for x in range(b[0],b[2]):
     if im.getpixel((x,y))[:3]not in[COLORS[1],COLORS[3]]:im.putpixel((x,y),(0,0,0,0))
   im.alpha_composite(layer,tuple(target['translation']))
 for group in spec.get('fixed_map_cores',[]):
  ims=[poses[label]for label in group['poses']]
  # Reuse only rigid safe head/neck and waist cores, never hands or legs.
  for b in group['boxes']:
   for im in ims[1:]:im.paste(ims[0].crop(b),b[:2])
   assert all(im.crop(b).tobytes()==ims[0].crop(b).tobytes()for im in ims),('fixed head/neck or hip mismatch',group['poses'],b)
 maps={'schema_version':1,'width_height_scale':4,'scenarios':copy.deepcopy(native['map_scenarios'])}
 for scenario in maps['scenarios']:
  scenario['output_frame_size']=[n*4 for n in scenario['source_frame_size']];scenario['output_anchor']=[n*4 for n in scenario['source_anchor']];scenario['logical_render_scale']=.25
  scenario['source_aliases']={str(i):i for i in range(8)}if scenario['id']=='tactical-walk'else{str(i):j for i,j in enumerate([0,1,2,1,0,1])}
 maps.update(character_id=ACTOR,actor_id=ACTOR,display_name='敌方断路匪',display_class_name='断路匪',class_id=14,source_side='enemy',revision=REV,status='review_candidate',runtime_integrated=False,modified_by='codex')
 entries=[]
 for scenario in maps['scenarios']:
  walk=scenario['id']=='tactical-walk';kind='walk'if walk else'idle';ids=list(range(8 if walk else 6));alias={i:i for i in ids}if walk else dict(enumerate([0,1,2,1,0,1]));w,h=scenario['output_frame_size'];atlas=Image.new('RGBA',(len(ids)*w,h));rows=[]
  for i in ids:
   im=poses[f'{kind}-{alias[i]}'];path=save(im,f'{scenario["id"]}/frame-{i:03}.png','whole new native map pose');atlas.alpha_composite(im,(i*w,0));record=ASSETS[-1]
   rows.append({'source_index':i,'source_frame':i,'output_index':i,'canonical_frame':alias[i],'path':path,'output_path':path,'size':[w,h],'bytes':record['bytes'],'sha256':record['sha256'],'revision':REV,'art_status':'review_candidate'})
   if walk or i<3:entries.append((f'{kind} {i}',im))
  source=f'../../../source-input/corrected-tactical-walk/{ACTOR}.png'if walk else'../../../source-input/legacy-assets/assets/original/graphics/map_units/class_14_enemy.png'
  scenario.update(class_id=14,source_side='enemy',character_id=ACTOR,display_name='敌方断路匪',source_atlas=source,frame_mapping=rows,output_atlas=save(atlas,f'{scenario["id"]}-atlas.png','native map slot order'),revision=REV,status='review_candidate',review_note='蓝紫少色、纯色头发；头颈与腰胯固定原点，各方向手脚相位按原帧登记。',motion_review={'fixed_core_requirements':spec.get('fixed_map_cores',[]),'registration':REG,'native_timing_modified':False,'runtime_integrated':False})
  scenario.pop('action_note',None);scenario.pop('output_atlas_bytes',None)
  if walk:scenario['source_audit']={**json.loads((ROOT/'source-input/corrected-tactical-walk/overlay.json').read_text())['records'][ACTOR],'status':'verified_native_tactical','overlay':'../../../source-input/corrected-tactical-walk/overlay.json'}
 required=body['required_source_frames'];paths={};records=[];atlas=Image.new('RGBA',(320*len(required),256));battle_entries=[]
 for n,i in enumerate(required):
  im=poses[f'battle-{i}'];path=save(im,f'battle/frame-{i:03}.png','native battle pose and exact background-slot alias');paths[str(i)]=path;atlas.alpha_composite(im,(n*320,0));records.append({'source_frame':i,'path':path,'size':[320,256],'sha256':ASSETS[-1]['sha256'],'source_background_translation':[-64,0]if i in[24,31]else[0,0]})
  if i!=31:battle_entries.append((f'原姿势 {i}',im))
 battle={'schema_version':1,'character_id':ACTOR,'display_name':'敌方断路匪','display_class_name':'断路匪','original_class_id':14,'source_side':'enemy','source_atlas':'../../../source-input/enemy-motion/class-14-enemy.png','source_frame_size':body['frame_size'],'output_frame_size':[320,256],'source_anchor':body['anchor'],'output_anchor':[160,256],'source_columns':body['columns'],'source_oam_frame_count':body['source_oam_frame_count'],'source_idle_frame':body['sequences']['idle'][0],'source_frame_count':body['frames'],'frame_mapping':paths,'canonical_frames':required,'required_source_frames':required,'variant_keys':list(variants),'records':records,'output_atlas_frame_order':required,'output_atlas':save(atlas,'battle-atlas.png','all required class14 native battle slots'),'status':'review_candidate','revision':REV,'modified_by':'codex','runtime_integrated':False,'palette':PALETTE,'review_note':'原FE2断路匪完整姿势登记；原方向、步进、出手、命中、回位与节奏保持，不新增攻击。','art_provenance':'ImageGen full figure poses; uniform registration and indexed matte materials; no code-generated anatomy.'}
 drafts={f'professions/{ACTOR}/maps/frame_mapping.json':maps,f'professions/{ACTOR}/battle/frame_mapping.json':battle}
 for kind,ims in[('maps',entries),('battle',battle_entries)]:
  for light in[False,True]:board(ims,kind,light)
 loops(poses)
 write(OUT/'mapping-drafts.json',drafts);write(OUT/'asset-manifest.json',{'revision':REV,'actor':ACTOR,'palette':PALETTE,'registration':REG,'assets':ASSETS,'native_timing_modified':False,'runtime_integrated':False,'fixed_map_cores':spec.get('fixed_map_cores',[]),'shared_equipment':spec.get('shared_equipment',[]),'source_pose_inputs_sha256':digest(OUT/'pose-inputs.json'),'user_visual_acceptance':'pending'})
 if publish:
  for p,m in drafts.items():write(ROOT/p,m)
  write(ROOT/f'professions/{ACTOR}/manifest.json',{'id':ACTOR,'class_id':14,'display_name':'敌方断路匪','revision':REV,'status':'review_candidate','maps':'maps/frame_mapping.json','battle':'battle/frame_mapping.json','runtime_integrated':False})
 print(json.dumps({'assets':len(ASSETS),'mappings':len(drafts),'registered_poses':len(REG),'published':publish}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');p.add_argument('--inspect',type=Path);a=p.parse_args()
 if a.inspect:print(json.dumps(inspect(a.inspect),indent=2))
 else:build(a.publish)
