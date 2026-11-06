#!/usr/bin/env python3
"""Authored quadruped stone-wing art, native timing and current innate review."""
import hashlib,json,math,copy
from functools import lru_cache
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps
from import_knight_redraw_v3 import parts
from export_gallery import font
ROOT=Path(__file__).resolve().parents[1];REV='stone-wing-complete-v1-20261024';OUT=ROOT/REV;SRC=OUT/'source'
HEX=['1b2739','333b58','465172','5a6083','7a82a2','a5b0c6','c9ccd7','8d96b3','c5a16e','8c735f','697491'];PAL=[tuple(bytes.fromhex(x))for x in HEX]
ASSETS=[];REG=[]
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def clean(im):
 pal=Image.new('P',(1,1));pal.putpalette([v for c in PAL for v in c]+list(PAL[0])*(256-len(PAL)))
 out=im.convert('RGB').quantize(palette=pal,dither=Image.Dither.NONE).convert('RGBA');out.putalpha(im.getchannel('A').point(lambda v:255 if v>=224 else 0));return out
def save(im,name,purpose):
 p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
 if im.mode=='RGBA':
  cs=sorted(set(im.getdata()));assert len(cs)<=256;q=Image.new('P',im.size);q.putpalette([v for c in cs for v in c[:3]]+[0]*(768-3*len(cs)));lut={c:i for i,c in enumerate(cs)};q.putdata([lut[c]for c in im.getdata()]);q.info['transparency']=bytes(c[3]for c in cs);assert q.convert('RGBA').tobytes()==im.tobytes()
 else:q=im
 q.save(p,optimize=True);ASSETS.append({'path':p.relative_to(ROOT).as_posix(),'size':list(im.size),'bytes':p.stat().st_size,'sha256':sha(p),'purpose':purpose});return p.relative_to(ROOT).as_posix()
@lru_cache(None)
def figures(name,cols,rows):
 raw=Image.open(SRC/name).convert('RGBA');gs=parts((x,y)for y in range(raw.height)for x in range(raw.width)if raw.getpixel((x,y))[3]>=224);gs=[g for g in gs if len(g)>10000];assert len(gs)==cols*rows,(name,len(gs));gs.sort(key=lambda g:sum(y for x,y in g)/len(g));ordered=[]
 for n in range(0,len(gs),cols):ordered+=sorted(gs[n:n+cols],key=lambda g:sum(x for x,y in g)/len(g))
 out=[]
 for i,g in enumerate(ordered):
  b=[min(x for x,y in g),min(y for x,y in g),max(x for x,y in g)+1,max(y for x,y in g)+1];im=Image.new('RGBA',(b[2]-b[0],b[3]-b[1]))
  for x,y in g:im.putpixel((x-b[0],y-b[1]),raw.getpixel((x,y)))
  im.save(SRC/(name.removesuffix('.png')+f'-figure-{i:02}.png'));out.append((im,b))
 return out
def eye(im):
 pts=[(x+.5,y+.5)for y in range(im.height)for x in range(im.width)if (p:=im.getpixel((x,y)))[3]>=224 and p[0]>130 and p[1]>80 and p[0]>p[1]*1.1 and p[1]>p[2]*1.25]
 assert pts,'amber eye missing';return[sum(p[i]for p in pts)/len(pts)for i in[0,1]]
def place(raw,size,scale,pivot,target,label,ground=None,mirror=False):
 im=clean(raw)
 if mirror:im=ImageOps.mirror(im);pivot=[im.width-pivot[0],pivot[1]]
 q=im.resize([round(v*scale)for v in im.size],Image.Resampling.NEAREST);ratio=[q.size[i]/im.size[i]for i in[0,1]];at=[round(target[i]-pivot[i]*ratio[i])for i in[0,1]]
 if ground is not None:at[1]=ground-q.getbbox()[3]
 out=Image.new('RGBA',size);out.alpha_composite(q,at);count=lambda v:sum(p[3]>0 for p in v.getdata());assert count(out)==count(q),('clipped pose',label,at,q.getbbox())
 REG.append({'label':label,'scale':scale,'source_pivot':pivot,'target':target,'registered_pivot':[at[i]+pivot[i]*ratio[i]for i in[0,1]],'translation':at,'source_size':list(raw.size),'ground':ground,'clipped_pixels':0,'method':'complete authored figure, uniform scale and landmark translation only'})
 return out
def maps():
 f=figures('walk-master.png',3,2);walk={}
 for cell,slot in[(0,0),(3,1),(1,2),(4,3),(2,4),(5,5)]:
  raw,bb=f[cell]
  if slot in[0,1]:
   absolute=[256,233]if slot==0 else[257,699];pivot=[absolute[i]-bb[i]for i in[0,1]];target=[64,46]
  else:pivot=eye(raw);target=[87,52]if slot in[2,3]else[64,49]
  walk[slot]=place(raw,(128,96),.17,pivot,target,'walk-'+str(slot))
 walk[6]=ImageOps.mirror(walk[2]);walk[7]=ImageOps.mirror(walk[3])
 idle={}
 for i,(raw,bb)in enumerate(figures('idle-master.png',3,1)):
  idle[i]=place(raw,(96,96),.103,eye(raw),[48,51],'idle-'+str(i),ground=80)
 return {i:idle[j]for i,j in enumerate([0,1,2,1,0,1])},walk
def battle():
 f=figures('battle-master.png',3,2);b={};raws={}
 for cell,slot in enumerate([9,10,11,12,14,13]):
  raw,bb=f[cell];raws[slot]=raw;ep=eye(raw)
  b[slot]=place(raw,(320,384),.40,ep,[100,228],'battle-'+str(slot),mirror=True)
 b[25]=Image.new('RGBA',(320,384));b[25].alpha_composite(b[9],(-64,0));assert sum(p[3]>0 for p in b[25].getdata())==sum(p[3]>0 for p in b[9].getdata());b[33]=b[25].copy()
 # Reuse the original two-frame slash sweep as motion feedback, not damage.
 src=Image.open(SRC/'native-battle-015.png').convert('RGBA');gs=parts((x,y)for y in range(src.height)for x in range(src.width)if (p:=src.getpixel((x,y)))[3]and p[0]>220 and p[1]>180 and p[2]>150)
 g=max(gs,key=len);arc=Image.new('RGBA',src.size)
 for xy in g:arc.putpixel(xy,(*PAL[5],255))
 b[15]=b[13].copy();b[15].alpha_composite(arc.resize((320,384),Image.Resampling.NEAREST))
 # New innate profile poses use BG coordinates (no OAM +16 correction).
 for slot,native in[(36,9),(37,14),(38,13),(39,9)]:
  raw=raws[native];b[slot]=place(raw,(320,384),.40,eye(raw),[36,228],'innate-'+str(slot),ground=288,mirror=True)
 for cell,slot in enumerate([40,41,42,43]):
  raw,bb=figures('extra-master.png',2,2)[cell];b[slot]=place(raw,(320,384),.26,eye(raw),[36,228],'innate-'+str(slot),ground=288,mirror=True)
 return b
def effects():
 raw=Image.open(SRC/'effects-master.png').convert('RGBA');result={}
 for i in range(4):
  l=round(i*raw.width/4);r=round((i+1)*raw.width/4);im=clean(raw.crop((l,0,r,raw.height)));bb=im.getbbox();assert bb;im=im.crop(bb);size=32 if i==0 else 96;scale=(size-6)/max(im.size);im=im.resize([round(v*scale)for v in im.size],Image.Resampling.NEAREST);out=Image.new('RGBA',(size,size));out.alpha_composite(im,((size-im.width)//2,(size-im.height)//2));path=save(out,f'effects/stone-{i}.png','岩芯或单次冲击碎石图');result['review-stone-wing-fx-'+str(i)]={'path':path,'frame_size':[size/4,size/4],'frames':1,'anchor':[size/8,size/8],'default_facing':'right','flip_origin_offset':[0,0]}
 return result
def row(f,offset=(0,0),effects=None,**extra):return{'frame':f,'offset':list(offset),'flip':False,'effects':effects or[],**extra}
def action(pid,key,name,rows,fps,kind,contact=None,note='',origin=(64,128),reference=None):
 return{'id':pid+'--'+key,'profile':pid,'key':key,'name':name,'context':'battle'if pid.endswith('-battle')else pid.split('maps-')[-1],'kind':kind,'fps':fps,'origin':list(origin),'contactTick':contact,'frames':rows,'notes':note,'defaultVideo':True,'viewport':[-16,-32,288,192]if pid.endswith('-battle')else[0,0,64,48],'referenceLabel':reference or('外传 · 原节奏／四足形态改编'if pid.endswith('-battle')else'外传 · 石像鬼动作参考')}
def profile(pid,ctx,source,size,anchor,paths,count):
 return{'id':pid,'actor':'class-3-enemy','actorName':'敌方石翼兽','classId':'3','className':'石翼兽','context':ctx,'contextName':{'battle':'战斗场景','tactical-idle':'战斗地图 · 待机','tactical-walk':'战斗地图 · 行走'}[ctx],'side':'enemy','source_side':'enemy','mapping':REV+'/gallery_bundle.json','mappingStatus':'review_candidate','revision':REV,'reviewNote':'四足石翼兽，柔和蓝紫哑光石甲；沿用原作振翼和扑击程序，现行裂石爪与碎岩喷吐各一次命中。','sourceAtlas':source,'sourceFrameSize':size,'sourceAtlasSize':list(Image.open(ROOT/source).size),'sourceColumns':Image.open(ROOT/source).width//size[0],'sourceFrameCount':count,'anchor':anchor,'sourceOamCutoff':16 if ctx=='battle'else 0,'flipOriginOffset':[16,0]if ctx=='battle'else[0,0],'outputFrameSize':[v*4 for v in size],'newFrames':paths,'frameErrors':{},'sourceReviewPending':False,'links':[{'label':'制作与动作对应记录','href':REV+'/README.md'}]}
def boards(idle,walk,b):
 for light in[False,True]:
  bg=(220,222,216)if light else(32,45,53);fg=PAL[0]if light else(235,243,242)
  for name,items,cols,cw,ch in[('maps',[(f'待机 {i}',idle[i])for i in[0,1,2]]+[(f'行走 {i}',walk[i])for i in range(8)],4,300,280),('battle',[(str(i),b[i])for i in[9,10,11,12,14,15,13,40,41,42,43]],4,350,420)]:
   q=Image.new('RGB',(cols*cw,56+math.ceil(len(items)/cols)*ch),bg);dr=ImageDraw.Draw(q);dr.text((q.width/2,26),'石翼兽 · '+('待机与四向振翼'if name=='maps'else'原作姿势与固有攻击'),font=font(21),anchor='mm',fill=fg)
   for n,(label,im)in enumerate(items):
    if name=='maps':im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
    x=n%cols*cw+(cw-im.width)//2;y=56+n//cols*ch;q.paste(im,(x,y),im);dr.text((n%cols*cw+cw/2,y+ch-20),label,font=font(17),anchor='mm',fill=fg)
   save(q,name+('-light.png'if light else'-dark.png'),'完整轮廓、前后肢体与深浅背景检查')
def main():
 idle,walk=maps();b=battle();fx=effects();audit=json.loads((SRC/'native-audit.json').read_text());profiles=[];actions=[]
 # Append current old quadruped poses to unused cells; frozen native pixels stay exact.
 old=Image.open(ROOT/audit['body']['path']).convert('RGBA');old=old.copy();project=Image.open(ROOT.parents[1]/'actual/assets/innate-enemies-20261023/class-3-battle.png').convert('RGBA')
 for i in range(8):
  im=project.crop((i*256,0,(i+1)*256,256));im=ImageOps.mirror(im);bb=im.getbbox();im=im.crop(bb);scale=min(58/im.width,50/im.height);im=im.resize([round(v*scale)for v in im.size],Image.Resampling.NEAREST);at=(40-im.width//2,72-im.height);old.alpha_composite(im,((36+i)%16*80+at[0],(36+i)//16*96+at[1]))
 source=save(old,'source/battle-reference-atlas.png','原作36槽原像素不动，36至43附本篇旧八姿势供新增攻击对照')
 for ctx,frames in[('tactical-idle',idle),('tactical-walk',walk),('battle',b)]:
  paths={str(i):save(im,ctx+f'/frame-{i:03}.png','石翼兽完整人物姿势')for i,im in frames.items()};pw,ph=next(iter(frames.values())).size;atlas=Image.new('RGBA',(pw*(max(frames)+1),ph))
  for i,im in frames.items():atlas.alpha_composite(im,(i*pw,0))
  ap=save(atlas,ctx+'-atlas.png','完整原槽位图集');pid='professions-class-3-enemy-'+('battle'if ctx=='battle'else'maps-'+ctx)
  if ctx=='battle':src=source;sz=[80,96];anchor=[40,72];count=44
  else:src=audit['idle_source']if ctx=='tactical-idle'else audit['walk_source'];sz=[24,24]if ctx=='tactical-idle'else[32,24];anchor=[12,20]if ctx=='tactical-idle'else[16,24];count=len(frames)
  p=profile(pid,ctx,src,sz,anchor,paths,count);p['links']+=[{'label':'全姿势图集','href':ap},{'label':'深浅底检查','href':REV+'/'+('battle'if ctx=='battle'else'maps')+'-light.png'}];profiles.append(p)
  if ctx=='tactical-idle':
   order=[k for _ in range(2)for k,n in zip([0,1,2,1],[14,8,14,8])for _ in range(n)];actions.append(action(pid,'idle-cycle','战斗地图 · 原待机循环',[row(i)for i in order],60.0988,'map_idle',origin=(32,36),note='保留原作14/8/14/8展翼与收翼顺序；四足、头胸保持稳定。'))
  elif ctx=='tactical-walk':
   for direction,ids in{'up':[0,1],'right':[2,3],'down':[4,5],'left':[6,7]}.items():
    name={'up':'向上','right':'向右','down':'向下','left':'向左'}[direction];actions.append(action(pid,'walk-'+direction,'行走 · '+name,[row(i)for _ in range(3)for i in ids for _ in range(16)],60.0988,'map_walk',origin=(32,36),note='原作CHR28方向及两相16帧节奏；翼根连接、近远腿区分，整体位置数据固定。'));actions.append(action(pid,'idle-'+direction,'静止 · '+name,[row(ids[0])for _ in range(32)],60.0988,'map_idle',origin=(32,36)))
  else:
   native=audit['variant'];rows=[{k:r[k]for k in['frame','offset','flip','effects']if k in r}for r in native['frames']];actions.append(action(pid,'original_class_3_enemy_normal','裂石爪 · 外传振翼扑击节奏',rows,native['native_fps'],'attack',native['contact_tick'],note='原作208帧、单次第104帧结算与全部位移逐行保留；四足石翼兽按原作中振翼、收身、伸爪、回位意图重绘。此对照程序不替换现行本篇46帧固有攻击。'))
   for key,name,melee,distance in[('stone-claw','裂石爪 · 本篇固有攻击',True,112),('stone-spit','碎岩喷吐 · 近距变体',False,112),('stone-spit-far','碎岩喷吐 · 远距变体',False,176)]:
    prep=12 if melee else 20;contact=prep+14;rows=[]
    for t in range(contact+20):
     eff=[];dx=dy=0
     if t<prep:f=37 if melee else 40;dx=-3*t/prep;dy=-2 if melee else 0
     elif t<=contact:
      f=38 if melee else 41;v=(t-prep)/14
      if melee:dx=(distance-42)*v;dy=-math.sin(v*math.pi)*12
      else:eff=[{'sprite':'review-stone-wing-fx-0','position':[98+(distance-44)*v,112-12*v],'flip':False}]
     else:f=39;dx=(distance-42)*(1-(t-contact)/20)if melee else 0
     if t>=contact:
      phase=t-contact
      if phase<12:eff=[{'sprite':'review-stone-wing-fx-'+str(1 if phase<3 else 2 if phase<7 else 3),'position':[64+distance-10,126 if melee else 100],'flip':False}]
     rows.append(row(f,(dx,dy),eff))
    a=action(pid,key,name,rows,50,'attack',contact,note=('1001，物理1格，准备12帧，命中一次。'if melee else'1002，仅明确配置的变体，物理1至2格，一枚岩芯命中一次。')+'现行源码的准备／释放／收势时长及接触时刻保持；嘴部发射点和爪端碎石位置按新身体登记。碎石是视觉反馈，不新增伤害。',reference='本篇旧版关键姿势 · 固有攻击')
    a['_reviewCloseCamera']={'offset':[-64,-80]if melee else[-56,-80],'size':[176,128]if melee else[256 if key.endswith('far')else 192,128]}
    actions.append(a)
   for key,name,rows in[('idle','战斗待机',[row(36)for _ in range(60)]),('hit','受击反馈',[row(42 if t<14 else 36,tint=.65 if t<14 else 1)for t in range(28)]),('miss','未命中 · 保持警戒',[row(36)for _ in range(23)]),('exit','战败退场',[row(42,alpha=max(0,1-(t//8+1)/4))for t in range(32)]),('thick-stone','厚石甲 · S22变体形象',[row(43)for _ in range(60)])]:actions.append(action(pid,key,name,rows,50,'reaction',note='身体反应或既有S22天然石甲形象，不新增出牌、格挡、伤害或护盾。',reference='本篇旧版关键姿势'))
 boards(idle,walk,b);write(OUT/'gallery_bundle.json',{'profiles':profiles,'actions':actions,'effects':fx,'runtime_integrated':False});write(OUT/'asset-manifest.json',{'revision':REV,'palette':HEX,'assets':ASSETS,'registration':REG,'generator':'built-in image_gen; original sources and full prompts retained','runtime_integrated':False})
 write(OUT/'action-effect-mapping.json',{'actor':'class-3-enemy','class_name':'石翼兽','native_reference':{'action':'original_class_3_enemy_normal','frames':208,'contact_tick':103,'pose_order':'9 → 10/11/12振翼 → 14收身 → 15伸爪过渡 → 13接触 → 振翼回位 → 33','limitation':'Established quadruped model is retargeted from the original biped; no human weapons.'},'innate_attacks':[{'id':1001,'name':'裂石爪','action':'stone-claw','frames':46,'fps':50,'contact_tick':26,'resolution_count':1},{'id':1002,'name':'碎岩喷吐','actions':['stone-spit','stone-spit-far'],'frames':54,'fps':50,'contact_tick':34,'projectiles':1,'resolution_count':1}],'thick_armour':'Existing S22 passive identity only; no added shield/card','runtime_integrated':False});print(json.dumps({'profiles':len(profiles),'actions':len(actions),'assets':len(ASSETS)}),flush=True)
if __name__=='__main__':main()
