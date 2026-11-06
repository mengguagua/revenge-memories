#!/usr/bin/env python3
"""Lock side-walk arms, stabilize airborne lower bodies, and share green ally heal VFX."""
import copy,json,hashlib,math
from functools import lru_cache
from PIL import Image,ImageDraw
from build_gallery import ROOT,file_hash
from export_gallery import font
import import_knight_redraw_v3 as helper
import import_sniper_complete as io
REV='spellsword-jump-heal-v3-20261023';OUT=ROOT/REV;SRC=OUT/'source';io.OUT=OUT
G=[(53,110,78),(112,182,125),(196,233,181)]
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sha(d):return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def loadmap(m,rel):return Image.open((ROOT/m).parent.joinpath(rel).resolve()).convert('RGBA')
def clean(im,label,seam=None):
 cs=helper.parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))[3])
 for c in cs[1:]:
  hair_seam=seam is not None and len(c)<=100 and all(im.getpixel(xy)==(23,38,56,255)for xy in c)and min(x for x,y in c)>225 and max(y for x,y in c)<seam+12
  assert len(c)<=6 or hair_seam,(label,'detached',len(c))
  for xy in c:im.putpixel(xy,(0,0,0,0))
 return im

def board(entries,name,title,cols=4):
 cw,ch=320,330
 for light in[False,True]:
  q=Image.new('RGBA',(cw*cols,50+ch*math.ceil(len(entries)/cols)),(220,222,216,255)if light else(32,45,53,255));d=ImageDraw.Draw(q);fg=(23,38,56)if light else(235,243,242);d.text((q.width//2,25),title,font=font(21),anchor='mm',fill=fg)
  for n,(label,im)in enumerate(entries):
   is_map=im.height<100;original_width=im.width
   if is_map:im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
   x=n%cols*cw+(cw-im.width)//2;y=50+n//cols*ch
   if is_map:
    shadow=Image.open(ROOT/'gold-knight-walk-v3-20261020/ground-shadow.png').convert('RGBA').resize((80,12),Image.Resampling.NEAREST);shadow.putalpha(shadow.getchannel('A').point(lambda v:round(v*.30)));q.alpha_composite(shadow,(n%cols*cw+cw//2-40,y+(88 if original_width==96 else 92)*2-6))
   q.alpha_composite(im,(x,y));d.text((n%cols*cw+cw//2,y+ch-18),label,font=font(16),anchor='mm',fill=fg)
  io.save(q.convert('RGB'),f'{name}-{"light"if light else"dark"}.png','offline pose/effect board with title and label safe space')

def maps(b):
 path='professions/class-11-ally/maps/frame_mapping.json';m=copy.deepcopy(b['mappings'][path]);walk=next(s for s in m['scenarios']if s['id']=='tactical-walk');ims={r['source_index']:loadmap(path,r['path'])for r in walk['frame_mapping']}
 # Both complete arms and their old silhouettes are replaced together, through the waist.
 ims[3].paste(ims[2].crop((0,0,128,68)),(0,0));clean(ims[3],'side walk')
 ims[6]=ims[2].transpose(Image.Transpose.FLIP_LEFT_RIGHT);ims[7]=ims[3].transpose(Image.Transpose.FLIP_LEFT_RIGHT)
 note='女魔剑士侧向行走：头颈、躯干、持剑臂和空手臂固定为同一上身姿势，不甩手；仅下半身按原作并腿与跨步两相变化。保留固定地面阴影及其余方向与待机。'
 m.update(revision=REV,review_note=note);walk.update(revision=REV,review_note=note,motion_review='../../../'+REV+'/README.md')
 for row in walk['frame_mapping']:
  i=row['source_index']
  if i not in[2,3,6,7]:continue
  row['path']=row['output_path']=io.save(ims[i],f'ally/tactical-walk/frame-{i:03}.png','fixed complete upper body; original lower-body walk phase');p=OUT/f'ally/tactical-walk/frame-{i:03}.png';row.update(bytes=p.stat().st_size,sha256=file_hash(p))
 atlas=Image.new('RGBA',(128*8,96))
 for i in range(8):atlas.alpha_composite(ims[i],(i*128,0))
 walk['output_atlas']=io.save(atlas,'ally/tactical-walk-atlas.png','all original walk slots, fixed side arms')
 board([(str(i),ims[i])for i in[2,3,6,7]],'side-walk','女魔剑士 · 左右行走双臂固定')
 idle=next(s for s in m['scenarios']if s['id']=='tactical-idle');idle_ims=[loadmap(path,r['path'])for r in idle['frame_mapping'][:3]]
 board([(f'待机{i}',im)for i,im in enumerate(idle_ims)]+[(f'行走{i}',ims[i])for i in range(8)],'maps-all','女魔剑士 · 当前地图全部姿势')
 return m

def battle(b):
 path='professions/class-11-ally/battle/frame_mapping.json';m=copy.deepcopy(b['mappings'][path]);ims={int(i):loadmap(path,p)for i,p in m['frame_mapping'].items()};groups=[([2,3,4,5,6,7],112),([8,9],112),([25,26],184),([27,28],184)];contracts=[]
 for ids,y in groups:
  source=ims[ids[0]].crop((0,y,320,288))
  for i in ids:
   ims[i].paste(source,(0,y));clean(ims[i],'battle'+str(i),y);m['frame_mapping'][str(i)]=io.save(ims[i],f'ally/battle/frame-{i:03}.png','one registered pelvis/leg silhouette per native airborne phase')
  contracts.append({'frames':ids,'fixed_lower_body_region':[0,y,320,288],'base':ids[0],'trajectory_and_native_tick_sequence_unchanged':True})
 atlas=Image.new('RGBA',(320*len(m['output_atlas_order']),288))
 for n,i in enumerate(m['output_atlas_order']):atlas.alpha_composite(ims[i],(n*320,0))
 m.update(revision=REV,output_atlas=io.save(atlas,'ally/battle-atlas.png','complete battle atlas with stabilized flight lower bodies'),qa_report='../../../'+REV+'/verification.json',review_note='女魔剑士前跳与后跳：统一每段空中相邻帧的腰胯、腿长、膝盖与双靴位置，消除快速交替时的抽搐；原跳跃轨迹、转身、落地、攻击结算和总时长保持。友方恢复改为绿色，目标光环结尾化成绿色雨滴。')
 m['batches']=[{'id':'前跳后跳腿部修订','review':'../../../'+REV+'/jump-poses-light.png','status':'review_candidate'}]
 board([(str(i),ims[i])for i in[2,3,6,7,8,9,25,26,27,28]],'jump-poses','女魔剑士 · 前跳与后跳腿部衔接')
 write(OUT/'jump-registration.json',{'groups':contracts,'native_actor_schedule_unchanged':True})
 return m

@lru_cache(maxsize=100000)
def green(rgb):return min(G,key=lambda c:sum((a-b)**2 for a,b in zip(c,rgb)))
def quant(im):
 q=Image.new('RGBA',im.size);q.putdata([(*green(p[:3]),255)if p[3]>=160 else(0,0,0,0)for p in im.getdata()]);return q

def effects(b):
 raw=Image.open(SRC/'green-heal-master.png').convert('RGBA');cw,ch=raw.width//4,raw.height//2;cells=[quant(raw.crop((i%4*cw,i//4*ch,(i%4+1)*cw,(i//4+1)*ch)))for i in range(7)];ring=cells[0].crop(cells[0].getbbox());defs={};replacements={};d=b['gallery'];ids=sorted({e['sprite']for a in d['actions']if a['profile']=='professions-class-11-ally-battle'and a['key']=='class_11_ally_item_40'for f in a['frames']for e in f['effects']})
 for eid in ids:
  old=d['effects'][eid];native=Image.open(ROOT/old['path']).convert('RGBA');bb=native.getbbox();q=Image.new('RGBA',(native.width*4,native.height*4))
  if bb:q.alpha_composite(ring.resize(((bb[2]-bb[0])*4,(bb[3]-bb[1])*4),Image.Resampling.NEAREST),(bb[0]*4,bb[1]*4))
  nid='ally_heal_green_v3_'+eid;defs[nid]={**old,'path':io.save(q,'effects/'+nid+'.png','green generated healing ring in exact original visible envelope')};replacements[eid]=nid
 # Keep a common cell origin; only falling motion below the ring is registered.
 rb=cells[0].getbbox();scale=64/(rb[2]-rb[0]);center=[(rb[0]+rb[2])/2,(rb[1]+rb[3])/2];rain=[]
 for i in range(1,7):
  cell=cells[i];small=cell.resize((round(cw*scale),round(ch*scale)),Image.Resampling.NEAREST);bb=small.getbbox();at=[round(80-center[0]*scale),round(40-center[1]*scale)]
  if i>=2:at[1]=[0,0,104,120,132,140,144][i]-bb[3]
  q=Image.new('RGBA',(160,192));q.alpha_composite(small,tuple(at));assert sum(p[3]>0 for p in q.getdata())==sum(p[3]>0 for p in small.getdata()),('rain clipped',i)
  nid='ally_heal_green_rain_v3_'+str(i);defs[nid]={'path':io.save(q,f'effects/rain-{i:02}.png','generated ring-to-green-raindrop ending, fixed origin'),'frame_size':[40,48],'anchor':[20,10],'frames':1,'default_facing':'left','flip_origin_offset':[0,0]};rain.append(nid)
 board([(str(i+1),Image.open(OUT/f'effects/rain-{i+1:02}.png').convert('RGBA'))for i in range(6)],'green-heal-ending','友方恢复 · 绿色光环化成雨滴',3)
 return defs,replacements,rain

def effect_center(data,e):
 meta=data['effects'][e['sprite']];im=Image.open(ROOT/meta['path']).convert('RGBA');bb=im.getbbox();assert bb
 if e.get('flip'):bb=[meta['frame_size'][0]-bb[2],bb[1],meta['frame_size'][0]-bb[0],bb[3]]
 at=[e['position'][i]-meta['anchor'][i]+(meta.get('flip_origin_offset',[0,0])[i]if e.get('flip')else 0)for i in range(2)]
 return[at[0]+(bb[0]+bb[2])/2,at[1]+(bb[1]+bb[3])/2]

def timelines(b,bm,defs,replacements,rain):
 contracts=[];out={};data=b['gallery'];heal=[a for a in data['actions']if a['context']=='battle'and a['profile']in[f'professions-class-{c}-ally-battle'for c in[11,18,19]]and '_item_40'in a['key']]
 for c in[11,18,19]:
  path=f'professions/class-{c}-ally/battle/frame_mapping.json';m=bm if c==11 else json.loads((ROOT/path).read_text());previous=m.get('review_timeline');timeline=json.loads((ROOT/path).parent.joinpath(previous).resolve().read_text())if previous else{'effects':{},'actions':{}};timeline=copy.deepcopy(timeline);timeline.update(revision=REV,runtime_integrated=False)
  if c==11:timeline.setdefault('effects',{}).update(defs)
  for a in heal:
   if a['profile']!=f'professions-class-{c}-ally-battle':continue
   rows=copy.deepcopy(a['revisedFrames']if a.get('revisedFrames')else a['frames']);contact=a['contactTick'];start=contact+12;end=start+36;assert end<len(rows),(a['id'],'rain must fit native recovery');target=effect_center(data,a['frames'][contact]['effects'][0])
   for t,row in enumerate(rows):
    if t<start:
     for e in row['effects']:
      if e['sprite']in replacements:e['sprite']=replacements[e['sprite']]
    elif t<end:row['effects']=[{'sprite':rain[(t-start)//6],'position':target,'flip':False}]
    else:row['effects']=[]
   contract={'key':a['key'],'profile':a['profile'],'native_total_ticks':len(rows),'native_contact':contact,'rain_start':start,'rain_end_exclusive':end,'rain_target_center':target,'additional_heals':0,'actor_rows_unchanged':True}
   timeline.setdefault('actions',{})[a['key']]={'source_frames_sha256':sha(a['frames']),'frames':rows,'events':contract,'note':'友方恢复：蓄力与目标光环统一为柔和绿色，目标光环收尾化成绿色雨滴；原施法人物动作、目标、唯一结算和总时长保持，不追加恢复。'};contracts.append(contract)
  rel=f'../../../{REV}/class-{c}-ally-motion.json';write(OUT/f'class-{c}-ally-motion.json',timeline);m.update(review_timeline=rel,heal_effect_revision=REV,heal_qa_report='../../../'+REV+'/verification.json');out[path]=m
 write(OUT/'healing-contracts.json',{'actions':contracts,'affected_ally_classes':[11,18,19],'enemy_changed':False,'original_effect_source_images_unchanged':True});return out

def main(publish=False):
 b=json.loads((OUT/'baseline.json').read_text());mp=maps(b);bm=battle(b);defs,replacements,rain=effects(b);mappings=timelines(b,bm,defs,replacements,rain);mappings['professions/class-11-ally/maps/frame_mapping.json']=mp
 write(OUT/'mapping-drafts.json',mappings);write(OUT/'asset-manifest.json',{'revision':REV,'assets':io.ASSETS,'green_palette':G,'new_vfx_effect_ids':list(defs),'enemy_excluded':True,'runtime_integrated':False})
 if publish:
  for path,m in mappings.items():write(ROOT/path,m)
  p=ROOT/'professions/class-11-ally/manifest.json';m=json.loads(p.read_text());m.update(revision=REV,maps_revision=REV,battle_revision=REV,review_record='../../'+REV+'/README.md');write(p,m)
 print(json.dumps({'assets':len(io.ASSETS),'heal_variants':18,'published':publish}),flush=True)
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');main(p.parse_args().publish)
