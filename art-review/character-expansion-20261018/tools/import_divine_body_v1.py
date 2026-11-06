#!/usr/bin/env python3
"""Authored seven-feather divine body; review assets only, no game mutations."""
import copy,hashlib,json,math
from pathlib import Path
from functools import lru_cache
from PIL import Image,ImageDraw,ImageOps
from export_gallery import font
from import_knight_redraw_v3 import parts

ROOT=Path(__file__).resolve().parents[1]
REV='divine-body-complete-v1-20261024';OUT=ROOT/REV;SRC=OUT/'source'
HEX=['1c2734','2b3c53','3e566f','57808e','a04b46','733c3f','e2d8bb','c2b599','c1974f','926f43','ddb057','709690','3e2d31']
PAL=[tuple(bytes.fromhex(s))for s in HEX];ASSETS=[];REG=[]
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
@lru_cache(None)
def color(rgb):return min(PAL,key=lambda q:sum((a-b)**2 for a,b in zip(rgb,q)))
def clean(im):
 out=Image.new('RGBA',im.size);out.putdata([(*color(p[:3]),255)if p[3]>=224 else(0,0,0,0)for p in im.getdata()]);return out
def save(im,name,purpose):
 p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
 if im.mode=='RGBA':
  colors=sorted(set(im.getdata()));q=Image.new('P',im.size);q.putpalette([x for c in colors for x in c[:3]]+[0]*(768-len(colors)*3));lut={c:i for i,c in enumerate(colors)};q.putdata([lut[c]for c in im.getdata()]);q.info['transparency']=bytes(c[3]for c in colors);assert q.convert('RGBA').tobytes()==im.tobytes()
 else:q=im
 q.save(p,optimize=True);rec={'path':p.relative_to(ROOT).as_posix(),'size':list(im.size),'bytes':p.stat().st_size,'sha256':sha(p),'purpose':purpose};ASSETS.append(rec);return rec['path']
def centroid(im,box,colors):
 pts=[(x+.5,y+.5)for y in range(box[1],box[3])for x in range(box[0],box[2])if im.getpixel((x,y))[3]and im.getpixel((x,y))[:3]in colors]
 assert pts,box
 return[sum(p[i]for p in pts)/len(pts)for i in(0,1)]
def whole(cut,size,scale,at):
 q=cut.resize([round(n*scale)for n in cut.size],Image.Resampling.NEAREST);out=Image.new('RGBA',size);out.alpha_composite(q,at)
 assert sum(p[3]>0 for p in q.getdata())==sum(p[3]>0 for p in out.getdata()),('clipping',at,q.getbbox())
 return out
def battle():
 raw=Image.open(SRC/'battle-master.png').convert('RGBA');frames={};cw=raw.width/4;ch=raw.height/2
 components=[c for c in parts((x,y)for y in range(raw.height)for x in range(raw.width)if raw.getpixel((x,y))[3]>=224)if len(c)>1000]
 components.sort(key=lambda c:(min(y for x,y in c)//444,min(x for x,y in c)))
 assert len(components)==8
 for i in range(8):
  c=components[i];box=[min(x for x,y in c),min(y for x,y in c),max(x for x,y in c)+1,max(y for x,y in c)+1];piece=Image.new('RGBA',raw.size)
  for xy in c:piece.putpixel(xy,raw.getpixel(xy))
  cut=clean(piece.crop(box))
  # Talons register every authored pose to a common floor. Uniform scale is
  # shared by all poses; raised wings and crowns never shrink the torso.
  feet=centroid(cut,(max(0,cut.width-300),max(0,cut.height-80),cut.width,cut.height),{PAL[8],PAL[9],PAL[10]});scale=.90
  q=cut.resize([round(n*scale)for n in cut.size],Image.Resampling.NEAREST)
  at=(round(280-feet[0]*q.width/cut.width),448-q.getbbox()[3]);frames[i]=whole(cut,(512,512),scale,at)
  # Raster grid is deliberately two physical pixels, avoiding antialias noise.
  frames[i]=frames[i].resize((256,256),Image.Resampling.NEAREST).resize((512,512),Image.Resampling.NEAREST)
  REG.append({'kind':'battle','slot':i,'cell':box,'uniform_scale':scale,'talon_centroid':feet,'translation':at,'ground':448,'clipped_pixels':0})
 # Neutral/recovery are the same stable whole pose; a wing settle must not
 # redraw the skull, beak, torso, jewels or talons.
 frames[3]=frames[0].copy()
 return frames
def maps():
 raw=Image.open(SRC/'map-master.png').convert('RGBA');walk={};scale=.172
 for slot,col,row in[(0,0,0),(1,0,1),(2,1,0),(3,1,1),(4,2,0),(5,2,1)]:
  cut=clean(raw.crop((col*512,row*512,(col+1)*512,(row+1)*512)))
  # Fixed central skull/back or skull/breast landmarks, not outer wing bounds.
  center=(280,310)if col==0 else(336,300)if col==1 else(260,300)
  floor=94 if col!=1 else 96;q=cut.resize((88,88),Image.Resampling.NEAREST)
  at=(round(64-center[0]*88/512),floor-q.getbbox()[3]);walk[slot]=whole(cut,(128,96),88/512,at)
  REG.append({'kind':'walk','slot':slot,'uniform_scale':88/512,'translation':at,'ground':floor,'clipped_pixels':0})
 fixed=[]
 for first,second,poly in[(0,1,[(40,0),(88,0),(88,46),(78,52),(77,77),(50,77),(50,52),(40,46)]),(2,3,[(37,0),(100,0),(100,54),(85,61),(83,80),(63,80),(62,59),(44,56)]),(4,5,[(40,0),(89,0),(89,46),(79,52),(79,78),(49,78),(49,52),(40,46)])]:
  mask=Image.new('L',(128,96));ImageDraw.Draw(mask).polygon(poly,fill=255);walk[second].paste(walk[first],(0,0),mask);fixed.append({'slots':[first,second],'mask_polygon':poly,'core_drift_pixels':0})
 # Keep each artist-authored complete ankle/claw junction. The native
 # generic divine-body phase is a wing fold/spread cycle; no limb stretch,
 # sliced row shift or extra stride pose is imposed on its two-frame rhythm.
 walk[6]=ImageOps.mirror(walk[2]);walk[7]=ImageOps.mirror(walk[3])
 # Native idle 0/1 are identical. State2 opens the wings while the entire
 # crown, face, chest and feet stay fixed, including the loop boundary.
 neutral=walk[4].copy();gesture=walk[5].copy();gesture.paste(neutral.crop((0,78,128,96)),(0,78))
 idle={}
 for i,j in enumerate([0,0,1,0,0,0]):
  p=gesture if j else neutral;canvas=Image.new('RGBA',(96,96));canvas.alpha_composite(p,(-16,-14));assert canvas.getbbox();idle[i]=canvas
 write(OUT/'fixed-core-contract.json',{'walk':fixed,'idle_head_chest_feet_exact':True,'left_right_exact_mirrors':True,'no_whole_sprite_oscillation':True,'phase_ticks':16})
 return idle,walk
def profile(pid,context,source,size,count,anchor,frames):
 atlas=Image.open(ROOT/source)
 return{'id':pid,'actor':'class-21-enemy','actorName':'敌方神躯 · 乌库布·卡基','classId':'21','className':'神躯','context':context,'contextName':{'battle':'战斗场景','tactical-idle':'战斗地图 · 待机','tactical-walk':'战斗地图 · 行走'}[context],'side':'enemy','source_side':'enemy','mapping':REV+'/gallery_bundle.json','mappingStatus':'review_candidate','revision':REV,'modifiedBy':'Codex','reviewNote':'用户确认七羽日冠神鸟。原作无此神鸟；地图沿用通用神躯两相节奏，战斗按现行日冠聚光／翼喙重击制作。中心固定，羽色哑光，只有必要结构阴影。','sourceAtlas':source,'sourceFrameSize':size,'sourceAtlasSize':list(atlas.size),'sourceColumns':atlas.width//size[0],'sourceFrameCount':count,'anchor':anchor,'sourceOamCutoff':0,'flipOriginOffset':[0,0],'outputFrameSize':[n*4 for n in size],'newFrames':frames,'frameErrors':{},'sourceReviewPending':False,'links':[{'label':'制作及动作对应记录','href':REV+'/README.md'}]}
def row(f,offset=(0,0),flip=False,effects=None,**extra):return{'frame':f,'offset':list(offset),'flip':flip,'effects':effects or[],**extra}
def action(p,key,name,rows,fps,kind,contact=None,origin=(64,128),note=''):
 return{'id':p+'--'+key,'profile':p,'key':key,'name':name,'context':'battle'if p.endswith('-battle')else('tactical-idle'if p.endswith('tactical-idle')else'tactical-walk'),'kind':kind,'fps':fps,'origin':list(origin),'contactTick':contact,'frames':rows,'notes':note,'defaultVideo':True,'viewport':[-16,-32,288,176]if p.endswith('-battle')else[0,0,64,48],'referenceLabel':'现行神躯 · 旧版形象'if p.endswith('-battle')else'外传通用神躯 · 节奏参考'}
def boards(idle,walk,b):
 for light in[False,True]:
  bg=(220,222,216)if light else(32,45,53);fg=(28,39,52)if light else(235,243,242)
  for kind,items,cols,cw,ch in[('maps',[(f'待机 {i}',idle[i])for i in[0,2]]+[(s,walk[i])for i,s in enumerate(['上 0','上 1','右 0','右 1','下 0','下 1','左 0','左 1'])],5,270,245),('battle',list(zip(['待机','聚光准备','聚光释放','收势','翼喙准备','翼喙命中','受击','半血展开'],b.values())),4,410,440)]:
   out=Image.new('RGB',(cols*cw,56+math.ceil(len(items)/cols)*ch),bg);d=ImageDraw.Draw(out);d.text((out.width/2,26),'神躯 · 七羽日冠神鸟 · '+('地图'if kind=='maps'else'战斗关键姿势'),font=font(21),anchor='mm',fill=fg)
   for n,(label,im)in enumerate(items):
    im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)if kind=='maps'else im.resize((384,384),Image.Resampling.NEAREST)
    x=n%cols*cw+(cw-im.width)//2;y=56+n//cols*ch;out.paste(im,(x,y),im);d.text((n%cols*cw+cw/2,y+ch-22),label,font=font(17),anchor='mm',fill=fg)
   save(out,kind+('-light.png'if light else'-dark.png'),'深浅底完整轮廓及眼睛检查')
def main():
 idle,walk=maps();b=battle();profiles=[];actions=[]
 for context,frames in[('tactical-idle',idle),('tactical-walk',walk),('battle',b)]:
  paths={str(i):save(im,context+f'/frame-{i:03}.png','神躯像素帧')for i,im in frames.items()};atlas=Image.new('RGBA',(next(iter(frames.values())).width*len(frames),next(iter(frames.values())).height))
  for i,im in frames.items():atlas.alpha_composite(im,(im.width*i,0))
  atlaspath=save(atlas,context+'-atlas.png','完整动作图集；保留像素清晰度');pid='professions-class-21-enemy-'+('battle'if context=='battle'else'maps-'+context)
  if context=='battle':
   old=Image.open(ROOT.parents[1]/'actual/assets/innate-enemies-20261023/class-21-battle.png').convert('RGBA').resize((1024,128),Image.Resampling.NEAREST);source=save(old,'source/project-bird-reference.png','现行项目旧版神鸟参考；原图密度2转换为逻辑128方格');size=[128,128];anchor=[64,112]
  else:
   source='source-input/legacy-assets/assets/original/graphics/map_units/class_21_enemy.png'if context=='tactical-idle'else'source-input/corrected-tactical-walk/class-21-enemy.png';size=[24,24]if context=='tactical-idle'else[32,24];anchor=[12,20]if context=='tactical-idle'else[16,24]
  p=profile(pid,context,source,size,len(frames),anchor,paths);p['links']+=[{'label':'四倍重绘图集','href':atlaspath},{'label':'深浅底姿势检查','href':REV+'/'+('battle'if context=='battle'else'maps')+'-light.png'}];profiles.append(p)
  if context=='tactical-idle':
   order=[k for _ in range(2)for k,n in zip([0,1,2,1],[14,8,14,8])for _ in range(n)];actions.append(action(pid,'idle-cycle','战斗地图 · 原待机循环',[row(i)for i in order],60.0988,'map_idle',origin=(32,34),note='原作通用神躯 14/8/14/8 节奏，两遍88帧；神鸟无原作对应形象，自行设计翼动，头胸与双爪固定。'))
  elif context=='tactical-walk':
   for direction,slots in{'up':[0,1],'right':[2,3],'down':[4,5],'left':[6,7]}.items():
    label={'up':'向上','down':'向下','left':'向左','right':'向右'}[direction];rows=[row(i)for _ in range(3)for i in slots for _ in range(16)];actions.append(action(pid,'walk-'+direction,'行走 · '+label,rows,60.0988,'map_walk',origin=(32,34),note='原作两相各16帧，三遍96帧。固定头胸核心，双翼开合、双爪保持承重连接；左右精确镜像。'))
    actions.append(action(pid,'idle-'+direction,'静止 · '+label,[row(slots[0])for _ in range(32)],60.0988,'map_idle',origin=(32,34),note='保持当前方向原第一姿势，中心固定。'))
  else:
   effect='review-divine-body-sun-orb-v1'
   for key,name,melee,distance in[('sun-crown','日冠聚光 · 近距',False,144),('sun-crown-far','日冠聚光 · 远距',False,176),('wing-beak','翼喙重击 · 近身反击',True,144)]:
    rows=[]
    for t in range(54):
     e=[];dx=0
     if t<20:
      f=4 if melee else 1;dx=-3*t/20
      if not melee and t>=12:e=[{'sprite':effect,'position':[88,57],'flip':False}]
     elif t<=34:
      f=5 if melee else 2;v=(t-20)/14
      if melee:dx=(distance-42)*v
      else:e=[{'sprite':effect,'position':[88+(distance-34)*v,57+43*v],'flip':False}]
     else:
      f=3
      if melee:dx=(distance-42)*(1-(t-34)/20)
     rows.append(row(f,(dx,0),True,e))
    actions.append(action(pid,key,name,rows,50,'attack',34,note='现行固有攻击 '+('1005 翼喙重击：物理、近身反击'if melee else'1006 日冠聚光：魔法，范围2，消耗1HP')+'。准备20帧、释放至第35帧结算、20帧收势，共54帧/50fps；每次只结算一次。原作没有这只神鸟，姿态自拟，未套用Duma眼球／触手能力。'))
   actions.append(action(pid,'idle','战斗待机',[row(0,flip=True)for _ in range(60)],50,'reaction',note='固定中轴和双爪，保持厚重压迫感。'))
   actions.append(action(pid,'empowered','半血姿态 · 展翼',[row(7,flip=True)for _ in range(60)],50,'reaction',note='仅对应现行半血及以下的展开姿势，未新增攻击或增益效果。'))
   actions.append(action(pid,'hit','受击反馈',[row(6 if t<14 else 0,flip=True,tint=.65 if t<14 else 1)for t in range(28)],50,'reaction',note='收颈护身后回到待机，保持双爪落点，未赋予额外防御能力。'))
   actions.append(action(pid,'miss','未命中 · 保持警戒',[row(0,flip=True)for _ in range(23)],50,'reaction',note='短暂保持警戒，不表现额外反击。'))
   actions.append(action(pid,'exit','战败退场',[row(6,flip=True,alpha=max(0,1-(t//8+1)/4))for t in range(32)],50,'reaction',note='四级透明度退场，不新增爆炸或复活效果。'))
 # Use the real current glow bitmap at its native-density-correct logical size.
 orb=Image.open(ROOT.parents[1]/'actual/assets/reviewed-animation-20261018/effects/cde5d1cef16d92.png').convert('RGBA');orbpath=save(orb,'effects/sun-orb.png','现行金白光球原位图；密度2，仅技术复用')
 effects={'review-divine-body-sun-orb-v1':{'path':orbpath,'frame_size':[16,16],'frames':1,'anchor':[8,8],'flip_origin_offset':[0,0],'default_facing':'right'}}
 boards(idle,walk,b);write(OUT/'gallery_bundle.json',{'profiles':profiles,'actions':actions,'effects':effects,'runtime_integrated':False,'identity':'User confirmed seven-feather Vucub avian deity; no native bird counterpart'})
 write(OUT/'asset-manifest.json',{'revision':REV,'palette':HEX,'assets':ASSETS,'registration':REG,'runtime_integrated':False,'user_acceptance':'pending','generator':'built-in image_gen; prompts in source/; technical processing only in this script'})
 print(json.dumps({'profiles':len(profiles),'actions':len(actions),'assets':len(ASSETS)}))
if __name__=='__main__':main()
