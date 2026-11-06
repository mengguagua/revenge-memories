#!/usr/bin/env python3
"""Register authored enemy19 art; native motion remains the source of timing."""
import argparse,copy,hashlib,json,math
from functools import lru_cache
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps
from export_gallery import font
import build_gallery as G

ROOT=Path(__file__).resolve().parents[1];REV='summoner-complete-v1-20261024';OUT=ROOT/REV;SRC=OUT/'source'
MP=ROOT/'professions/class-19-enemy/maps/frame_mapping.json';BP=ROOT/'professions/class-19-enemy/battle/frame_mapping.json'
HEX=['172638','353e60','55567d','aaa4bf','d7a481','a77d73','26344d'];PALETTE=[tuple(bytes.fromhex(x))for x in HEX]
ASSETS=[];REG=[]
CORES={'idle':[(36,15,63,42),(43,52,56,60)],'up':[(49,32,78,59),(59,66,71,72)],'right':[(50,32,77,59),(58,66,70,71)],'down':[(50,32,78,59),(58,66,71,71)]}
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
@lru_cache(maxsize=None)
def material(rgb):return min(PALETTE,key=lambda q:sum((a-b)**2 for a,b in zip(rgb,q)))
def quant(im):
 out=Image.new('RGBA',im.size);out.putdata([(*material(p[:3]),255)if p[3]>=200 else(0,0,0,0)for p in im.getdata()]);return out
def save(im,path,purpose):
 p=OUT/path;p.parent.mkdir(parents=True,exist_ok=True)
 if im.mode=='RGBA':
  colors=sorted(set(im.getdata()));assert len(colors)<=256
  q=Image.new('P',im.size);q.putpalette([v for c in colors for v in c[:3]]+[0]*(768-len(colors)*3));lookup={c:i for i,c in enumerate(colors)};q.putdata([lookup[c]for c in im.getdata()]);q.info['transparency']=bytes(c[3]for c in colors);assert q.convert('RGBA').tobytes()==im.tobytes()
 else:q=im
 q.save(p,optimize=True);record={'path':'../../../'+p.relative_to(ROOT).as_posix(),'size':list(im.size),'bytes':p.stat().st_size,'sha256':sha(p),'purpose':purpose};ASSETS.append(record);return record
def center(im,roi,colors=None):
 pts=[(x+.5,y+.5)for y in range(roi[1],roi[3])for x in range(roi[0],roi[2])if im.getpixel((x,y))[3]and(colors is None or im.getpixel((x,y))[:3]in colors)]
 assert pts,roi
 return[sum(p[i]for p in pts)/len(pts)for i in(0,1)]
def place(cut,scale,point,target,size,ground,kind,slot):
 q=cut.resize(tuple(round(v*scale)for v in cut.size),Image.Resampling.NEAREST);rat=[q.size[i]/cut.size[i]for i in(0,1)];at=[round(target[i]-point[i]*rat[i])for i in(0,1)];at[1]=ground-q.getbbox()[3]
 out=Image.new('RGBA',size);out.alpha_composite(q,tuple(at));count=lambda im:sum(p[3]>0 for p in im.getdata());assert count(out)==count(q),(kind,slot,'clipping',at,q.getbbox())
 REG.append({'kind':kind,'slot':slot,'scale':scale,'translation':at,'registered_landmark':[at[i]+point[i]*rat[i]for i in(0,1)],'ground_y':ground,'clipped_pixels':0,'method':'uniform scale and integer translation of authored pose'})
 return out
def maps():
 master=Image.open(SRC/'maps-master.png').convert('RGBA');xs=[0,483,965,1448];ys=[0,362,724,1086];raw={i:quant(master.crop((xs[i%3],ys[i//3],xs[i%3+1],ys[i//3+1])))for i in range(9)};raw[4]=ImageOps.mirror(raw[4]);idle={};walk={}
 for slot,cell in enumerate([0,1,2,3,6,4,7,5,8]):
  cut=raw[cell];bb=cut.getbbox();point=center(cut,(bb[0],bb[1],bb[2],bb[1]+int((bb[3]-bb[1])*.30)));scale=64/(bb[3]-bb[1]);isidle=slot<3;index=slot if isidle else slot-3;target=[48 if isidle else 64,25 if isidle else 41];im=place(cut,scale,point,target,(96,96)if isidle else(128,96),80 if isidle else 96,'idle'if isidle else'walk',index)
  (idle if isidle else walk)[index]=im
 for i in[1,2]:
  for box in CORES['idle']:idle[i].paste(idle[0].crop(box),box[:2])
 for first,second,name in[(0,1,'up'),(2,3,'right'),(4,5,'down')]:
  for box in CORES[name]:walk[second].paste(walk[first].crop(box),box[:2])
 walk[6]=ImageOps.mirror(walk[2]);walk[7]=ImageOps.mirror(walk[3]);return {'tactical-idle':{i:idle[j]for i,j in enumerate([0,1,2,1,0,1])},'tactical-walk':walk}
def battle():
 master=Image.open(SRC/'battle-master.png').convert('RGBA');native=Image.open(SRC/'native-battle-000.png').convert('RGBA');target=[4*v for v in center(native,(25,28,34,40),{(247,216,165)})];b={};rois={0:(273,192,316,242),4:(304,193,344,242),5:(356,192,395,242)}
 for slot,col in[(0,0),(4,1),(5,2)]:
  cut=quant(master.crop((716*col,0,716*(col+1),732)));head=center(cut,rois[slot],{PALETTE[4],PALETTE[5]});bb=cut.getbbox();scale=(256-target[1])/(bb[3]-head[1]);b[slot]=place(cut,scale,head,target,(320,256),256,'battle',slot)
 # The corrected raised-hand study puts the palm above the face as in the
 # native pose. Its lower rear arm is replaced by the matching master torso.
 cut=quant(Image.open(SRC/'raised-cross-study.png').convert('RGBA'));head=center(cut,(588,370,647,442),{PALETTE[4],PALETTE[5]});scale=(256-target[1])/(cut.getbbox()[3]-head[1]);raised=place(cut,scale,head,target,(320,256),256,'battle-raised-upper',4)
 raised.paste(b[4].crop((0,160,320,256)),(0,160));b[4]=raised
 # The native three cast poses keep the lower robe/feet stationary.
 for i in[4,5]:b[i].paste(b[0].crop((0,208,320,256)),(0,208))
 return b
def effects_and_demo(audit):
 effects={};mist=Image.open(SRC/'summon-mist-master.png').convert('RGBA');xs=[0,591,1183,1774];ys=[0,444,887];colors=[tuple(bytes.fromhex(h))for h in['4f587d','7485ac','9693bb','bdc4d8']]
 for i in range(6):
  cut=mist.crop((xs[i%3],ys[i//3],xs[i%3+1],ys[i//3+1]));q=Image.new('RGBA',cut.size);q.putdata([(*min(colors,key=lambda c:sum((a-b)**2 for a,b in zip(p[:3],c))),160)if p[3]>=200 else(0,0,0,0)for p in cut.getdata()]);small=q.resize((296,222),Image.Resampling.NEAREST);out=Image.new('RGBA',(352,240));out.alpha_composite(small,(28,7 if i<3 else 29));rec=save(out,f'effects/mist-{i}.png','一处召唤场、两团雾光，透明蓝紫色');effects[f'review-c19-summon-mist-{i}']={'path':rec['path'],'frame_size':[88,60],'frames':1,'anchor':[44,52],'flip_origin_offset':[0,0]}
 child=Image.open(ROOT/'bone-guard-complete-v1-20261024/battle/frame-000.png').convert('RGBA');bb=child.getbbox();child=child.crop(bb);anchor=[child.width/8,child.height/4]
 for i,alpha in enumerate([64,128,192,255]):
  q=child.copy();q.putalpha(child.getchannel('A').point(lambda n:round(n*alpha/255)));rec=save(q,f'effects/guard-{i}.png','复用已确认骸卫；召唤显形透明阶段');effects[f'review-c19-summon-guard-{i}']={'path':rec['path'],'frame_size':[child.width/4,child.height/4],'frames':1,'anchor':anchor,'flip_origin_offset':[0,0]}
 rows=[];new=[]
 for t in range(160):
  row={'frame':0 if t<24 or t>=136 else 4 if t<56 else 5,'offset':[0,0],'flip':False,'effects':[]};rows.append(row);revised=copy.deepcopy(row)
  if 40<=t<116:
   phase=min(5,(t-40)//13);revised['effects'].append({'sprite':f'review-c19-summon-mist-{phase}','position':[160,128],'flip':False})
  if t>=80:
   phase=min(3,(t-80)//5)
   for x in[140,180]:revised['effects'].append({'sprite':f'review-c19-summon-guard-{phase}','position':[x,128],'flip':True})
  new.append(revised)
 action={'id':'professions-class-19-enemy-battle--review-summon-skeletons','profile':'professions-class-19-enemy-battle','key':'review-summon-skeletons','name':'召唤 · 两名骸卫（能力演示）','context':'battle','kind':'skill','fps':60.0988,'origin':[64,128],'contactTick':80,'frames':rows,'revisedFrames':new,'notes':'自定召唤演示：原作共用托掌→举掌→伸掌→回位姿势，原作侧仅作姿势参考；蓝紫雾光中显形两名骸卫。遵循F43每波最多两名的现行上限，无伤害、无额外攻击。未接入运行场景。','referenceLabel':'原作共用施法姿势','_reviewCloseCamera':{'offset':[-44,-68],'size':[196,84]},'defaultVideo':True}
 write(OUT/'gallery_bundle.json',{'actions':[action]})
 revisions={};shared=json.loads((SRC/'shared-spell-effects.json').read_text())['sources']
 for key,v in audit['variants'].items():
  if key not in shared:continue
  rows=[G.pack_frame(r)for r in v['frames']];fx=shared[key]['effects'];assert len(rows)==len(fx)
  revised=[{**r,'effects':copy.deepcopy(fx[i])}for i,r in enumerate(rows)]
  revisions[key]={'source_frames_sha256':hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'frames':revised,'note':'保留驭魔师原作身体姿势、位移、节奏与结算；仅复用已逐帧核对相同原生效果轨道的蓝紫法术素材。完整法术目录仅为原作美术参考，不代表F43解锁这些法术。'}
 write(OUT/'enemy-motion.json',{'revision':REV,'runtime_integrated':False,'effects':effects,'actions':revisions})
def boards(m,b):
 groups=[('maps',[(f'待机 {i}',m['tactical-idle'][i])for i in range(3)]+[(f'{d} {i%2}',m['tactical-walk'][i])for i,d in enumerate(['上','上','右','右','下','下','左','左'])],4,280,260),('battle',[(str(i),b[i])for i in[0,4,5]],3,340,310)]
 for light in[False,True]:
  for kind,items,cols,cw,ch in groups:
   bg=(220,222,216)if light else(32,45,53);fg=(23,38,56)if light else(235,243,242);out=Image.new('RGB',(cols*cw,54+ch*math.ceil(len(items)/cols)),bg);d=ImageDraw.Draw(out);d.text((out.width/2,26),'驭魔师 · '+('地图全姿势'if kind=='maps'else'原作施法姿势'),anchor='mm',font=font(20),fill=fg)
   for n,(label,im)in enumerate(items):
    if kind=='maps':im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
    x=n%cols*cw+(cw-im.width)//2;y=54+n//cols*ch;out.paste(im,(x,y),im);d.text((n%cols*cw+cw/2,y+ch-20),label,anchor='mm',font=font(16),fill=fg)
   save(out,kind+('-light.png'if light else'-dark.png'),'深浅底全部姿势和遮挡检查')
def main(publish=False):
 m=maps();b=battle();audit=json.loads((SRC/'native-audit.json').read_text());note='驭魔师：蓝紫哑光兜帽长袍，淡紫内衬，暖肤色露前臂；头发被兜帽覆盖，无高光。地图固定头部和腰部基准，保留手臂、衣摆、脚步相位与前后遮挡。战斗沿原作三姿势及全部原时序；法术目录仅作美术参考。';scenes=[]
 for kind in['tactical-idle','tactical-walk']:
  idle=kind=='tactical-idle';size=[24,24]if idle else[32,24];outsize=[x*4 for x in size];anchor=[12,20]if idle else[16,24];nativepath=audit['inputs']['idle'if idle else'walk']['path'];frames=m[kind];rows=[];atlas=Image.new('RGBA',(outsize[0]*len(frames),outsize[1]))
  for i,im in frames.items():
   rec=save(im,kind+f'/frame-{i:03}.png','驭魔师地图原槽位');rows.append({'source_index':i,'source_frame':i,'output_index':i,'canonical_frame':([0,1,2,1,0,1][i]if idle else i),'path':rec['path'],'size':rec['size'],'bytes':rec['bytes'],'sha256':rec['sha256'],'revision':REV,'art_status':'review_candidate'});atlas.alpha_composite(im,(i*outsize[0],0))
  scene={'id':kind,'source_atlas':'../../../'+nativepath,'source_frame_size':size,'source_anchor':anchor,'source_frame_count':len(frames),'output_frame_size':outsize,'output_anchor':[n*4 for n in anchor],'logical_render_scale':.25,'class_id':19,'source_side':'enemy','character_id':'class-19-enemy','display_name':'敌方驭魔师','frame_mapping':rows,'output_atlas':save(atlas,kind+'-atlas.png','原槽位图集')['path'],'revision':REV,'review_note':note,'required_drawn_frames':list(range(3 if idle else 8))}
  if idle:scene.update(static_facing=True,directions={'all':[0,1,2,1]},source_aliases={str(i):j for i,j in enumerate([0,1,2,1,0,1])},timing={'native_fps':60.0988,'cycle_frames':[0,1,2,1],'frame_ticks':[14,8,14,8],'cycle_ticks':44})
  else:
   checked=copy.deepcopy(audit['walk']);checked.update(native_record_status=checked['status'],status='verified_native_tactical',scope='native CPU phase verified, art review only',review_evidence='../../../'+REV+'/source/source-walk-verification.json');scene.update(directions={'up':[0,1],'right':[2,3],'down':[4,5],'left':[6,7]},direction_mirror_x={},timing={'native_fps':60.0988,'frame_ticks':16,'cycle_ticks':32},source_audit=checked)
  scenes.append(scene)
 maps_mapping={'schema_version':1,'width_height_scale':4,'scenarios':scenes,'character_id':'class-19-enemy','display_name':'敌方驭魔师','display_class_name':'驭魔师','class_id':19,'original_class_id':19,'source_side':'enemy','revision':REV,'status':'review_candidate','runtime_integrated':False,'review_note':note,'palette':HEX}
 atlas=Image.new('RGBA',(320*6,256));paths={}
 for i,im in b.items():paths[str(i)]=save(im,f'battle/frame-{i:03}.png','驭魔师完整施法姿势')['path'];atlas.alpha_composite(im,(i*320,0))
 battle_mapping={'schema_version':1,'character_id':'class-19-enemy','display_name':'敌方驭魔师','display_class_name':'驭魔师','original_class_id':19,'source_side':'enemy','source_atlas':'../../../'+audit['inputs']['battle']['path'],'source_frame_size':[80,64],'source_anchor':[40,64],'output_frame_size':[320,256],'source_idle_frame':0,'source_frame_count':6,'source_columns':16,'frame_mapping':paths,'required_source_frames':[0,4,5],'variant_keys':list(audit['variants']),'output_atlas':save(atlas,'battle-atlas.png','原槽位战斗图集')['path'],'revision':REV,'review_timeline':'../../../'+REV+'/enemy-motion.json','status':'review_candidate','runtime_integrated':False,'review_note':note,'palette':HEX,'batches':[{'id':'驭魔师完整姿势','review':'../../../'+REV+'/battle-light.png','status':'review_candidate'}]}
 effects_and_demo(audit);boards(m,b);write(OUT/'mapping-drafts.json',{'maps':maps_mapping,'battle':battle_mapping});write(OUT/'asset-manifest.json',{'revision':REV,'palette':HEX,'assets':ASSETS,'registration':REG,'fixed_map_cores':CORES,'runtime_integrated':False,'user_acceptance':'pending'})
 if publish:
  write(MP,maps_mapping);write(BP,battle_mapping);write(MP.parent.parent/'manifest.json',{'id':'class-19-enemy','revision':REV,'status':'review_candidate','runtime_integrated':False,'maps_mapping':'maps/frame_mapping.json','battle_mapping':'battle/frame_mapping.json','review_record':'../../'+REV+'/README.md'})
 print(json.dumps({'published':publish,'assets':len(ASSETS),'map_slots':14,'battle_slots':len(b),'spell_variants':66,'custom_summon_demo':1}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');args=p.parse_args();main(args.publish)
