#!/usr/bin/env python3
"""Skeletal dragon sprites and exact native/source review programs. No runtime edits."""
import copy,hashlib,json,math
from functools import lru_cache
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps
from import_knight_redraw_v3 import parts
import build_gallery as G
from export_gallery import font
ROOT=G.ROOT;REV='bone-wing-beast-complete-v1-20261024';OUT=ROOT/REV;SRC=OUT/'source'
HEX=['23334a','3c4766','555879','787ba1','929bb6','bac4d8','d0d7df','ba985e','6a637f'];PAL=[tuple(bytes.fromhex(x))for x in HEX];ASSETS=[];REG=[]
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
@lru_cache(None)
def color(rgb):return min(PAL,key=lambda q:sum((a-b)**2 for a,b in zip(rgb,q)))
def clean(im):
 out=Image.new('RGBA',im.size);out.putdata([(*color(p[:3]),255)if p[3]>=224 else(0,0,0,0)for p in im.getdata()]);return out
def save(im,name,purpose):
 p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
 if im.mode=='RGBA'and len(set(im.getdata()))<=256:
  colors=sorted(set(im.getdata()));q=Image.new('P',im.size);q.putpalette([v for c in colors for v in c[:3]]+[0]*(768-len(colors)*3));lut={c:i for i,c in enumerate(colors)};q.putdata([lut[c]for c in im.getdata()]);q.info['transparency']=bytes(c[3]for c in colors);assert q.convert('RGBA').tobytes()==im.tobytes()
 else:q=im
 q.save(p,optimize=True);rec={'path':p.relative_to(ROOT).as_posix(),'size':list(im.size),'bytes':p.stat().st_size,'sha256':sha(p),'purpose':purpose};ASSETS.append(rec);return rec['path']
def sprites(file,kind):
 im=Image.open(SRC/file).convert('RGBA');groups=[c for c in parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))[3]>=224)if len(c)>1000];records=[]
 for c in groups:
  box=[min(x for x,y in c),min(y for x,y in c),max(x for x,y in c)+1,max(y for x,y in c)+1];warm=[(x+.5,y+.5)for x,y in c if(lambda p:p[0]>130 and p[1]>70 and p[2]<110 and p[0]>p[1]*1.1)(im.getpixel((x,y)))];eye=[sum(p[k]for p in warm)/len(warm)for k in(0,1)]if warm else None;cut=Image.new('RGBA',(box[2]-box[0],box[3]-box[1]))
  for x,y in c:cut.putpixel((x-box[0],y-box[1]),im.getpixel((x,y)))
  row=int(eye[1]//403)if kind=='battle'else int(box[3]>512)if kind=='walk'else 0;records.append({'raw':cut,'box':box,'eye':eye,'row':row,'file':file})
 records.sort(key=lambda r:(r['row'],r['box'][0]));return records
def register(rec,scale,target,point,size,kind,slot):
 cut=clean(rec['raw']);atpoint=[point[i]-rec['box'][i]for i in(0,1)];q=cut.resize([round(n*scale)for n in cut.size],Image.Resampling.NEAREST);ratio=[q.size[i]/cut.size[i]for i in(0,1)];at=[round(target[i]-atpoint[i]*ratio[i])for i in(0,1)];out=Image.new('RGBA',size);out.alpha_composite(q,at)
 assert sum(p[3]>0 for p in q.getdata())==sum(p[3]>0 for p in out.getdata()),(kind,slot,'authored clipping',at,q.getbbox())
 REG.append({'kind':kind,'slot':slot,'source':rec['file'],'source_component_bounds':rec['box'],'uniform_source_scale':scale,'source_landmark':point,'target_landmark':target,'translation':at,'clipped_pixels':0});return out
def core_mask(size,polys):
 mask=Image.new('L',size);d=ImageDraw.Draw(mask)
 for poly in polys:d.polygon(poly,fill=255)
 return mask
def maps():
 ims=sprites('walk-master.png','walk');assert len(ims)==6;walk={};points=[(285,370),(805,385),(1260,378),(285,870),(810,880),(1260,875)];slots=[0,2,4,1,3,5]
 for n,slot in enumerate(slots):walk[slot]=register(ims[n],.20,(64,96),points[n],(128,128),'walk',slot)
 # Register only raised wing regions above their fixed shoulder. The anatomy
 # of the original two-phase animation is a low spread and a high stroke.
 for slot,target in[(1,8),(3,20),(5,12)]:
  im=walk[slot];joint=78;piece=im.crop((0,0,128,joint));bb=piece.getbbox();factor=(joint-target)/(joint-bb[1]);tall=piece.resize((128,round(joint*factor)),Image.Resampling.NEAREST);posed=im.copy();posed.paste((0,0,0,0),(0,0,128,joint));posed.alpha_composite(tall,(0,joint-tall.height));walk[slot]=posed
 fixed=[]
 for a,b,polys in[(0,1,[[(54,56),(75,56),(76,74),(54,74)],[(59,74),(70,74),(72,103),(57,103)],[(49,101),(80,101),(79,124),(51,124)]]),(2,3,[[(76,76),(112,76),(112,105),(76,105)],[(57,89),(78,89),(80,114),(57,114)],[(14,104),(72,104),(72,117),(14,117)]]),(4,5,[[(54,73),(75,73),(77,91),(53,91)],[(55,91),(76,91),(79,111),(52,111)],[(46,109),(83,109),(83,117),(46,117)]])]:
  mask=core_mask((128,128),polys);walk[b].paste(walk[a],(0,0),mask);fixed.append({'slots':[a,b],'polygons':polys,'core_drift_pixels':0})
 walk[6]=ImageOps.mirror(walk[2]);walk[7]=ImageOps.mirror(walk[3])
 raw=sprites('idle-master.png','idle');assert len(raw)==3;idle={i:register(rec,.12,(74,56),rec['eye'],(96,96),'idle',i)for i,rec in enumerate(raw)};polys=[[(56,42),(94,42),(94,72),(56,72)],[(43,54),(68,54),(70,82),(43,82)],[(9,64),(94,64),(94,83),(9,83)]];mask=core_mask((96,96),polys)
 for i in[1,2]:idle[i].paste(idle[0],(0,0),mask)
 write(OUT/'fixed-core-contract.json',{'walk':fixed,'idle':{'slots':[0,1,2],'polygons':polys,'core_drift_pixels':0},'left_right_exact_mirrors':True,'fixed_core_not_outer_wing_bbox':True})
 return{i:idle[j]for i,j in enumerate([0,1,2,1,0,1])},walk
def battle():
 upper=sprites('battle-master.png','battle');lower=sprites('lower-wings-master.png','lower');cup=sprites('wing-20-master.png','single');assert len(upper)==9 and len(lower)==4 and len(cup)==1;frames={}
 for slot in range(16,24):
  i=slot-16;rec=cup[0]if slot==20 else upper[i]if i<4 else lower[i-4];scale=.27 if slot==20 else .70 if i<4 else .49;frames[slot]=register(rec,scale,(112,344),rec['eye'],(384,640),'battle',slot)
 # Source anatomy: wings sweep around the same skull, lower neck and near
 # foreclaw. Hold these exact pixels while allowing the near wing to pass in
 # front of the right shoulder; the farther wing remains behind the ribs.
 polys=[[(64,306),(155,300),(197,314),(201,344),(174,369),(64,369)],[(170,342),(247,342),(247,386),(170,386)],[(207,286),(240,286),(242,334),(207,334)]];mask=core_mask((384,640),polys)
 for i in range(17,24):frames[i].paste(frames[16],(0,0),mask)
 # Match actual native upper/downstroke wing reach without resizing the body.
 for slot,wanted in[(16,164),(17,8),(18,32),(19,84)]:
  im=frames[slot];joint=288;part=im.crop((0,0,384,joint));bb=part.getbbox();factor=(joint-wanted)/(joint-bb[1]);q=part.resize((384,round(joint*factor)),Image.Resampling.NEAREST);posed=im.copy();posed.paste((0,0,0,0),(0,0,384,joint));posed.alpha_composite(q,(0,joint-q.height));frames[slot]=posed
 for slot,wanted in[(20,180),(21,200),(22,200),(23,200)]:
  im=frames[slot];joint=330;part=im.crop((0,0,384,joint));bb=part.getbbox();factor=(joint-wanted)/(joint-bb[1]);q=part.resize((384,round(joint*factor)),Image.Resampling.NEAREST);posed=im.copy();posed.paste((0,0,0,0),(0,0,384,joint));posed.alpha_composite(q,(0,joint-q.height));posed.paste(frames[16],(0,0),mask);frames[slot]=posed
 # The canonical low stroke has long wing fingers below the fixed claws.
 for slot,wanted in[(20,388),(21,400),(22,460),(23,524)]:
  im=frames[slot];joint=330;part=im.crop((0,joint,384,640));bb=part.getbbox();actual=joint+bb[3];scale=(wanted-joint)/(actual-joint);q=part.resize((384,max(1,round(part.height*scale))),Image.Resampling.NEAREST);posed=im.copy();posed.paste((0,0,0,0),(0,joint,384,640));posed.alpha_composite(q,(0,joint));posed.paste(frames[16],(0,0),mask);frames[slot]=posed
 for slot in range(16,24):
  im=frames[slot];q=im.crop((0,0,384,544));assert sum(p[3]>0 for p in q.getdata())==sum(p[3]>0 for p in im.getdata())
  for group in parts((x,y)for y in range(q.height)for x in range(q.width)if q.getpixel((x,y))[3]):
   if len(group)<100:
    for xy in group:q.putpixel(xy,(0,0,0,0))
  frames[slot]=q
 # Background slots are exactly the native -16 logical-pixel registration.
 for slot in[41,48]:
  im=Image.new('RGBA',(384,544));im.alpha_composite(frames[16],(-64,0));assert sum(p[3]>0 for p in im.getdata())==sum(p[3]>0 for p in frames[16].getdata());frames[slot]=im
 authored_jaw=register(upper[8],.70,(112,344),upper[8]['eye'],(384,544),'battle-custom',50)
 # Current bite/breath use the same accepted rib cage, claws, tail and wings.
 # Only the authored skull/jaw opens; its larger raw crop must not grow the body.
 openjaw=frames[18].copy();region=(62,312,170,404);openjaw.paste(authored_jaw.crop(region),region[:2]);region=(170,312,188,386);openjaw.paste(authored_jaw.crop(region),region[:2]);region=(170,342,247,386);openjaw.paste(frames[18].crop(region),region[:2])
 groups=parts((x,y)for y in range(openjaw.height)for x in range(openjaw.width)if openjaw.getpixel((x,y))[3]);main=max(groups,key=len)
 for group in groups:
  if group is not main:
   for xy in group:openjaw.putpixel(xy,(0,0,0,0))
 im=Image.new('RGBA',(384,544));im.alpha_composite(openjaw,(-64,0));assert sum(p[3]>0 for p in im.getdata())==sum(p[3]>0 for p in openjaw.getdata());frames[50]=im
 write(OUT/'battle-anatomy-contract.json',{'fixed_core_polygons':polys,'native_alpha_bounds':{str(i):list(Image.open(SRC/f'native-battle-{i:03}.png').convert('RGBA').getbbox())for i in range(16,24)},'registration':'Body/skull density locked; retarget only wing regions around fixed joint to native reach; head and near foreclaw exact','BG_aliases':{'41':'16 shifted -64 physical px','48':'41 exact'},'50':'custom open jaw, BG registration; only revised current-innate rows'})
 return frames
def profile(pid,ctx,src,size,count,anchor,paths):
 atlas=Image.open(ROOT/src);return{'id':pid,'actor':'class-5-enemy','actorName':'敌方骸翼兽','classId':'5','className':'骸翼兽','context':ctx,'contextName':{'battle':'战斗场景','tactical-idle':'战斗地图 · 待机','tactical-walk':'战斗地图 · 行走'}[ctx],'side':'enemy','source_side':'enemy','mapping':REV+'/gallery_bundle.json','mappingStatus':'review_candidate','revision':REV,'modifiedBy':'Codex','reviewNote':'骨龙，柔和蓝紫骨骼与翼膜，固定地图头胸骨盆；原作翼关节顺序、位移和结算保留，近爪在胸前、远爪和远翼在身后。现行骸颚撕咬／蚀息单独列示，未新增能力。','sourceAtlas':src,'sourceFrameSize':size,'sourceAtlasSize':list(atlas.size),'sourceColumns':atlas.width//size[0],'sourceFrameCount':count,'anchor':anchor,'sourceOamCutoff':25 if ctx=='battle'else 0,'flipOriginOffset':[16,0]if ctx=='battle'else[0,0],'outputFrameSize':[n*4 for n in size],'newFrames':paths,'frameErrors':{},'sourceReviewPending':False,'links':[{'label':'制作及动作对应记录','href':REV+'/README.md'}]}
def row(f,off=(0,0),effects=None,**kw):return{'frame':f,'offset':list(off),'flip':False,'effects':effects or[],**kw}
def action(pid,key,name,rows,fps,kind,contact=None,origin=(56,128),note='',**kw):
 return{'id':pid+'--'+key,'profile':pid,'key':key,'name':name,'context':'battle'if pid.endswith('-battle')else'tactical-idle'if pid.endswith('tactical-idle')else'tactical-walk','kind':kind,'fps':fps,'origin':list(origin),'contactTick':contact,'frames':rows,'notes':note,'defaultVideo':True,'viewport':[-16,-32,288,224]if pid.endswith('-battle')else[0,0,64,48],**kw}
def boards(idle,walk,frames):
 for light in[False,True]:
  bg=(220,222,216)if light else(32,45,53);fg=(28,39,52)if light else(235,243,242)
  for kind,items,cols,cw,ch in[('maps',[(f'待机 {i}',idle[i])for i in range(3)]+[(f'{d} {i%2}',walk[i])for i,d in enumerate(['上','上','右','右','下','下','左','左'])],4,280,300),('battle',[(f'原作 {i}',frames[i])for i in range(16,24)]+[('待机BG41',frames[41]),('现行开颚',frames[50])],5,320,475)]:
   out=Image.new('RGB',(cols*cw,56+math.ceil(len(items)/cols)*ch),bg);d=ImageDraw.Draw(out);d.text((out.width/2,26),'骸翼兽 · '+('地图完整姿势'if kind=='maps'else'骨龙翼关节连续姿势'),font=font(21),anchor='mm',fill=fg)
   for n,(label,im)in enumerate(items):
    im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)if kind=='maps'else im.resize((288,408),Image.Resampling.NEAREST);x=n%cols*cw+(cw-im.width)//2;y=56+n//cols*ch;out.paste(im,(x,y),im);d.text((n%cols*cw+cw/2,y+ch-22),label,font=font(17),anchor='mm',fill=fg)
   save(out,kind+('-light.png'if light else'-dark.png'),'深浅底及全肢体轮廓检查')
def main():
 idle,walk=maps();frames=battle();audit=json.loads((SRC/'native-audit.json').read_text());profiles=[];actions=[];pid='professions-class-5-enemy-battle';effects={}
 for ctx,images in[('tactical-idle',idle),('tactical-walk',walk),('battle',frames)]:
  paths={str(i):save(im,ctx+f'/frame-{i:03}.png','骸翼兽 '+ctx+'姿势')for i,im in images.items()};size=[96,136]if ctx=='battle'else[32,32]if ctx=='tactical-walk'else[24,24];src=audit['inputs']['battle'if ctx=='battle'else'walk'if ctx=='tactical-walk'else'idle'];anchor=[48,96]if ctx=='battle'else[16,32]if ctx=='tactical-walk'else[12,20];pp=pid if ctx=='battle'else'professions-class-5-enemy-maps-'+ctx;p=profile(pp,ctx,src,size,51 if ctx=='battle'else len(images),anchor,paths)
  atlas=Image.new('RGBA',(size[0]*4*len(images),size[1]*4))
  for n,im in enumerate(images.values()):atlas.alpha_composite(im,(n*size[0]*4,0))
  atlaspath=save(atlas,ctx+'-atlas.png','完整动作图集；列顺序按清单，不更改原槽位');p['links'].append({'label':'完整重绘图集','href':atlaspath});profiles.append(p)
  if ctx=='tactical-idle':
   seq=[i for _ in range(2)for i,n in zip([0,1,2,1],[14,8,14,8])for _ in range(n)];actions.append(action(pp,'idle-cycle','战斗地图 · 原待机循环',[row(i)for i in seq],60.0988,'map_idle',origin=(32,36),note='14/8/14/8原待机节奏，两遍88帧，头胸爪与尾巴核心固定，只有翼指小幅舒展。'))
  elif ctx=='tactical-walk':
   for direction,slots in{'up':[0,1],'right':[2,3],'down':[4,5],'left':[6,7]}.items():
    name={'up':'向上','right':'向右','down':'向下','left':'向左'}[direction];rows=[row(i)for _ in range(3)for i in slots for _ in range(16)];actions.append(action(pp,'walk-'+direction,'行走 · '+name,rows,60.0988,'map_walk',origin=(32,36),note='原作骨龙飞移：低翼／高翼各16帧，三遍96帧；固定身体核心，翼根与爪的前后遮挡保持。'))
    actions.append(action(pp,'idle-'+direction,'静止 · '+name,[row(slots[0])for _ in range(32)],60.0988,'map_idle',origin=(32,36),note='保持当前方向第一翼姿，不整体漂移。'))
  else:
   native=audit['variant'];actions.append(action(pid,'original_class_5_enemy_normal','原作普通攻击',[G.pack_frame(r)for r in native['frames']],native['native_fps'],'attack',native['contact_tick'],native['actor_origin'],'原作507帧、原动作顺序、循环、飞移、转身和第244帧结算逐行保留。翅膀为抬翼→展开→C形下扫→深下拍，不把翼指误作手臂。'))
   for key,name,rows,note in G.reactions(41):actions.append(action(pid,'reaction-'+key,name,rows,G.FPS,'reaction',note=note))
   effectid='review-bone-wing-eroding-breath-v1';fire=Image.open(ROOT.parents[1]/'actual/assets/reviewed-animation-20261018/effects/review-ghost-fire-enemy-flight-ca271c883ab5b7.png').convert('RGBA');path=save(fire,'effects/eroding-breath.png','复用现行蚀息火焰位图，按密度4正确显示，不增加伤害次数');effects[effectid]={'path':path,'frame_size':[48,16],'anchor':[24,8],'frames':1,'default_facing':'left','flip_origin_offset':[0,0]}
   for key,name,melee in[('innate-bone-bite','骸颚撕咬 · 现行能力',True),('innate-eroding-breath','蚀息 · 现行能力',False)]:
    prep=24 if melee else 20;contact=prep+14;total=contact+20;rows=[];revised=[]
    for t in range(total):
     fx=[];dx=0
     if t<prep:f=17;dx=-3*t/prep
     elif t<=contact:
      f=19;u=(t-prep)/14
      if melee:dx=110*u
      else:fx=[{'sprite':effectid,'position':[88+110*u,84+16*u],'flip':True}]
     else:
      f=18
      if melee:dx=110*(1-(t-contact)/20)
     rr=row(f,(dx,0),fx);rows.append(rr);rr=copy.deepcopy(rr)
     if prep<=t<=contact:rr['frame']=50
     if not melee and fx:rr['effects'][0]['position']=[101+97*u,123-23*u]
     revised.append(rr)
    camera={}if melee else{'_reviewCloseCamera':{'offset':[-64,-108],'size':[248,144],'padding':12,'note':'Include both existing reference and revised mouth-to-target breath paths'}}
    actions.append(action(pid,key,name,rows,50,'attack',contact,note=('角色5→1003骸颚撕咬→24帧蓄势后开颚前冲，tick38单次结算，总58帧。'if melee else'角色5→1004蚀息→20帧蓄势后开颚吐息，tick34单次结算，总54帧；魔法范围2、消耗1HP。新稿只校准吐息起点至张颚位置，命中位置与单次结算时刻保持。')+' 现行时序独立展示，原作无开颚近景，按现有身份设计50槽开颚，不改变507帧原作攻击。',revisedFrames=revised,referenceLabel='现行动作时序 · 原作身体参考',**camera))
 boards(idle,walk,frames);write(OUT/'gallery_bundle.json',{'profiles':profiles,'actions':actions,'effects':effects,'runtime_integrated':False});write(OUT/'asset-manifest.json',{'revision':REV,'palette':HEX,'assets':ASSETS,'registration':REG,'runtime_integrated':False,'generator':'built-in image_gen; prompts and original masters kept offline in source/','user_acceptance':'pending'});print(json.dumps({'profiles':len(profiles),'actions':len(actions),'assets':len(ASSETS)}))
if __name__=='__main__':main()
