#!/usr/bin/env python3
"""Register authored bone-guard poses without replacing native motion programs."""
import argparse,copy,hashlib,json,math
from functools import lru_cache
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps
from export_gallery import font
from import_knight_redraw_v3 import parts

ROOT=Path(__file__).resolve().parents[1];REV='bone-guard-complete-v1-20261024';OUT=ROOT/REV;SRC=OUT/'source'
MP=ROOT/'professions/class-17-enemy/maps/frame_mapping.json';BP=ROOT/'professions/class-17-enemy/battle/frame_mapping.json'
HEX=['172638','d9d8c5','9b9eb4','57577f','343c5d','bac4d2','8f7b8d'];PALETTE=[tuple(bytes.fromhex(x))for x in HEX]
ASSETS=[];REG=[]
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
@lru_cache(maxsize=None)
def material(rgb):return min(PALETTE,key=lambda q:sum((a-b)**2 for a,b in zip(rgb,q)))
def quant(im):
 out=Image.new('RGBA',im.size);out.putdata([(*material(p[:3]),255)if p[3]>=200 else(0,0,0,0)for p in im.getdata()]);return out
def save(im,path,purpose):
 p=OUT/path;p.parent.mkdir(parents=True,exist_ok=True)
 if im.mode=='RGBA':
  colors=sorted(set(im.getdata()));q=Image.new('P',im.size);q.putpalette([v for c in colors for v in c[:3]]+[0]*(768-len(colors)*3));lookup={c:i for i,c in enumerate(colors)};q.putdata([lookup[c]for c in im.getdata()]);q.info['transparency']=bytes(c[3]for c in colors);assert q.convert('RGBA').tobytes()==im.tobytes()
 else:q=im
 q.save(p,optimize=True);record={'path':'../../../'+p.relative_to(ROOT).as_posix(),'size':list(im.size),'bytes':p.stat().st_size,'sha256':sha(p),'purpose':purpose};ASSETS.append(record);return record
def centroid(im,roi,colors):
 pts=[(x+.5,y+.5)for y in range(roi[1],roi[3])for x in range(roi[0],roi[2])if im.getpixel((x,y))[:3]in colors and im.getpixel((x,y))[3]]
 assert pts,roi
 return[sum(p[i]for p in pts)/len(pts)for i in(0,1)]
def native_head(kind,slot):
 im=Image.open(SRC/f'native-{kind}-{slot:03}.png').convert('RGBA')
 if kind=='idle':roi=[9,4,15,9];colors={(254,204,197)}
 elif kind=='walk':roi={0:[12,8,19,13],1:[12,8,19,13],2:[11,8,18,13],3:[11,8,18,13],4:[12,8,20,13],5:[12,8,20,13]}[slot];colors={(254,204,197)}
 else:roi={0:[47,33,54,38],1:[47,33,54,38],2:[47,35,54,40],3:[47,33,54,39],4:[38,34,47,40],5:[38,32,47,39],7:[38,32,48,40],8:[38,32,48,40]}[slot];colors={(228,229,148)}
 return[c*4 for c in centroid(im,roi,colors)]

def register(file,cell,head_roi,kind,slot,target=None):
 raw=Image.open(SRC/file).convert('RGBA');cut=quant(raw.crop(cell));head=centroid(cut,head_roi,{PALETTE[1]});target=target or native_head(kind,slot);bb=cut.getbbox();assert bb
 native=Image.open(SRC/f'native-{kind}-{slot:03}.png').convert('RGBA');ground=native.getbbox()[3]*4
 scale=(ground-target[1])/(bb[3]-head[1]);size=[round(cut.width*scale),round(cut.height*scale)];q=cut.resize(size,Image.Resampling.NEAREST);ratios=[size[i]/cut.size[i]for i in(0,1)];at=[round(target[i]-head[i]*ratios[i])for i in(0,1)];out=Image.new('RGBA',tuple(x*4 for x in native.size));out.alpha_composite(q,tuple(at))
 # Use the uncomposited alpha extent so a one-pixel edge cannot be silently
 # hidden by the output canvas before the ground-baseline registration.
 at[1]=ground-q.getbbox()[3];out=Image.new('RGBA',out.size);out.alpha_composite(q,tuple(at))
 count=lambda im:sum(p[3]>0 for p in im.getdata())
 if count(q)!=count(out):raise ValueError((kind,slot,'clipped authored pixels',count(q)-count(out),at,q.getbbox()))
 REG.append({'kind':kind,'slot':slot,'source':file,'cell':cell,'raw_head_roi':head_roi,'raw_head_centroid':head,'target_head':target,'scale':scale,'translation':at,'registered_head':[at[i]+head[i]*ratios[i]for i in(0,1)],'ground_y':ground,'clipped_pixels':0,'method':'whole authored pose, uniform scale and integer registration'})
 return out

def maps():
 idle={};walk={};file='idle-master.png'
 for i in range(3):idle[i]=register(file,[i*724,0,(i+1)*724,724],[347,135,530,220],'idle',i)
 # These native idle parts are stationary. Preserve the three independently
 # authored hand/shield gestures around the common skull, rib cage and legs.
 for i in[1,2]:
  for box in[(34,16,62,40),(39,39,60,55),(36,55,65,80)]:idle[i].paste(idle[0].crop(box),box[:2])
 # Native idle0/1 differ only in the shield; the foreground sword moves in2.
 idle[1].paste(idle[0].crop((0,0,63,96)),(0,0))
 # Split in the actual transparent gutter: upper-row feet extend beyond the
 # nominal half-height. No adjacent feet may enter the lower sprites.
 cells=[(0,0,0),(2,1,0),(4,2,0),(1,0,1),(3,1,1),(5,2,1)];xs=[0,591,1183,1774];ys=[0,474,887]
 rois={0:[245,142,346,205],1:[245,62,346,130],2:[276,141,379,204],3:[277,57,381,125],4:[251,138,356,205],5:[253,58,357,126]}
 for slot,col,row in cells:walk[slot]=register('walk-master.png',[xs[col],ys[row],xs[col+1],ys[row+1]],rois[slot],'walk',slot,target=native_head('walk',slot-slot%2))
 # Small fixed head/spine/pelvis regions retain the artist's forearm occlusion.
 for first,second,boxes in[(0,1,[(48,28,76,49),(58,50,70,74)]),(2,3,[(46,28,75,49),(57,59,65,73)]),(4,5,[(49,28,77,49),(59,54,66,73)])]:
  for box in boxes:walk[second].paste(walk[first].crop(box),box[:2])
 walk[6]=ImageOps.mirror(walk[2]);walk[7]=ImageOps.mirror(walk[3])
 return {'tactical-idle':{i:idle[j]for i,j in enumerate([0,1,2,1,0,1])},'tactical-walk':walk}

def battle():
 specs={0:('battle-a-master.png',[0,0,768,512],[348,110,440,166]),1:('battle-a-master.png',[768,0,1536,512],[342,110,435,170]),2:('battle-a-master.png',[0,512,768,1024],[347,94,440,155]),3:('battle-a-master.png',[768,512,1536,1024],[342,95,437,157]),4:('battle-b-master.png',[0,0,768,482],[365,152,447,205]),5:('battle-b-master.png',[768,0,1536,482],[331,145,417,201]),7:('battle-b-master.png',[0,482,768,1024],[400,208,481,264]),8:('battle-b-master.png',[768,482,1536,1024],[371,208,461,266])}
 specs.update({7:('raised-arm-final.png',[0,0,1085,725],[632,302,755,366]),8:('raised-arm-final.png',[1085,0,2170,725],[588,302,720,366])})
 frames={i:register(file,cell,roi,'battle',i)for i,(file,cell,roi)in specs.items()if i!=7}
 # The native overhead attack intentionally extends the wrapped forearm.
 # Retarget this authored upper-arm/sword region above the fixed shoulder;
 # keep the skull, rear arm, rib cage, pelvis and feet unchanged.
 base=frames[8];region=(0,0,153,145);piece=base.crop(region);wanted=20;factor=(145-wanted)/(145-piece.getbbox()[1]);height=round(piece.height*factor);reached=piece.resize((piece.width,height),Image.Resampling.NEAREST)
 posed=base.copy();posed.paste((0,0,0,0),region);posed.alpha_composite(reached,(0,145-height))
 assert posed.getbbox()[1]==wanted
 frames[8]=posed
 REG.append({'kind':'battle','slot':8,'method':'native overhead reach registration above fixed shoulder; nearest-neighbor vertical retarget of authored forearm/sword only','region':region,'fixed_shoulder_y':145,'vertical_scale':factor,'native_tip_y':20,'skull_torso_rear_arm_legs_unchanged':True})
 # Torso/legs below native row34 are exact between source7/8. Keep the same
 # body and reuse the actual source's single-frame C sweep for the transition.
 native7=Image.open(SRC/'native-battle-007.png').convert('RGBA');native8=Image.open(SRC/'native-battle-008.png').convert('RGBA');assert native7.crop((32,34,96,64)).tobytes()==native8.crop((32,34,96,64)).tobytes()
 sweep=parts((x,y)for y in range(64)for x in range(96)if native7.getpixel((x,y))==(228,229,148,255))[0];arc=Image.new('RGBA',(96,64))
 for xy in sweep:arc.putpixel(xy,(*PALETTE[2],255))
 frames[7]=frames[8].copy();frames[7].alpha_composite(arc.resize((384,256),Image.Resampling.NEAREST))
 REG.append({'kind':'battle','slot':7,'method':'authored final body plus native one-frame sweep','native_sweep_pixels':len(sweep),'source':'native-battle-007.png','sweep_color':HEX[2],'source_body_equality_below_y':34})
 bg=Image.new('RGBA',frames[0].size);bg.alpha_composite(frames[0],(-64,0));assert sum(p[3]>0 for p in bg.getdata())==sum(p[3]>0 for p in frames[0].getdata());frames[9]=bg;frames[17]=bg.copy();return frames

def boards(m,b):
 sets=[('maps',[('待机 '+str(i),m['tactical-idle'][i])for i in range(3)]+[(name+' '+str(i),m['tactical-walk'][i])for i,name in enumerate(['上','上','右','右','下','下','左','左'])],4,280,260),('battle',[(str(i),b[i])for i in[0,1,2,3,4,5,7,8,9]],3,400,310)]
 for light in[False,True]:
  bg=(220,222,216)if light else(32,45,53);fg=(23,38,56)if light else(235,243,242)
  for kind,items,cols,cw,ch in sets:
   out=Image.new('RGB',(cw*cols,54+ch*math.ceil(len(items)/cols)),bg);d=ImageDraw.Draw(out);d.text((out.width/2,26),'骸卫 · '+('地图全姿势'if kind=='maps'else'原作战斗姿势'),anchor='mm',font=font(20),fill=fg)
   for n,(label,im)in enumerate(items):
    if kind=='maps':im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
    x=n%cols*cw+(cw-im.width)//2;y=54+n//cols*ch;out.paste(im,(x,y),im);d.text((n%cols*cw+cw/2,y+ch-20),label,anchor='mm',font=font(16),fill=fg)
   save(out,kind+('-light.png'if light else'-dark.png'),'完整姿势及前后肢体检查')

def main(publish=False):
 m=maps();b=battle();audit=json.loads((SRC/'native-audit.json').read_text());note='骸卫：温和骨白与蓝紫色，骨骼、下颌、肋骨和骨盆清楚，包腕包腿哑光；地图持剑圆盾，战斗沿原作弯刃与后屈空手臂。固定地图头部和身体基准，保留原步态、遮挡、动作顺序及结算。'
 scenes=[]
 for kind in['tactical-idle','tactical-walk']:
  idle=kind=='tactical-idle';size=[24,24]if idle else[32,24];outsize=[x*4 for x in size];anchor=[12,20]if idle else[16,24];nativepath=audit['inputs']['idle'if idle else'walk']['path'];frames=m[kind];rows=[];atlas=Image.new('RGBA',(outsize[0]*len(frames),outsize[1]))
  for i,im in frames.items():
   rec=save(im,kind+f'/frame-{i:03}.png','骸卫地图原槽位');rows.append({'source_index':i,'source_frame':i,'output_index':i,'canonical_frame':([0,1,2,1,0,1][i]if idle else i),'path':rec['path'],'size':rec['size'],'bytes':rec['bytes'],'sha256':rec['sha256'],'revision':REV,'art_status':'review_candidate'});atlas.alpha_composite(im,(i*outsize[0],0))
  scene={'id':kind,'source_atlas':'../../../'+nativepath,'source_frame_size':size,'source_anchor':anchor,'source_frame_count':len(frames),'output_frame_size':outsize,'output_anchor':[n*4 for n in anchor],'logical_render_scale':.25,'class_id':17,'source_side':'enemy','character_id':'class-17-enemy','display_name':'敌方骸卫','frame_mapping':rows,'output_atlas':save(atlas,kind+'-atlas.png','原槽位图集')['path'],'revision':REV,'review_note':note,'required_drawn_frames':list(range(3 if idle else 8))}
  if idle:scene.update(static_facing=True,directions={'all':[0,1,2,1]},source_aliases={str(i):j for i,j in enumerate([0,1,2,1,0,1])},timing={'native_fps':60.0988,'cycle_frames':[0,1,2,1],'frame_ticks':[14,8,14,8],'cycle_ticks':44})
  else:
   evidence=[]
   for record in audit['walk']['frame_mapping']:
    source=Image.open(SRC/f'native-walk-{record["source_slot"]:03}.png').convert('RGBA');actual=hashlib.sha256(source.tobytes()).hexdigest();assert actual==record['rgba_sha256'];evidence.append({'source_slot':record['source_slot'],'native_cpu_rgba_sha256_matches':True,'rgba_sha256':actual})
   checked=copy.deepcopy(audit['walk']);checked.update(native_record_status=checked['status'],status='verified_native_tactical',scope='native CPU frame/phase source verified for art review; no runtime integration',review_evidence='../../../'+REV+'/source-walk-verification.json')
   write(OUT/'source-walk-verification.json',{'passed':True,'source_chr':27,'native_cpu_records':evidence,'old_hybrid_reference_not_used':True})
   scene.update(directions={'up':[0,1],'right':[2,3],'down':[4,5],'left':[6,7]},direction_mirror_x={},timing={'native_fps':60.0988,'frame_ticks':16,'cycle_ticks':32},source_audit=checked)
  scenes.append(scene)
 maps_mapping={'schema_version':1,'width_height_scale':4,'scenarios':scenes,'character_id':'class-17-enemy','display_name':'敌方骸卫','display_class_name':'骸卫','class_id':17,'original_class_id':17,'source_side':'enemy','revision':REV,'status':'review_candidate','runtime_integrated':False,'review_note':note,'palette':HEX}
 atlas=Image.new('RGBA',(384*19,256));paths={}
 for i,im in b.items():paths[str(i)]=save(im,f'battle/frame-{i:03}.png','骸卫完整战斗姿势或原生背景别名')['path'];atlas.alpha_composite(im,(i*384,0))
 battle_mapping={'schema_version':1,'character_id':'class-17-enemy','display_name':'敌方骸卫','display_class_name':'骸卫','original_class_id':17,'source_side':'enemy','source_atlas':'../../../'+audit['inputs']['battle']['path'],'source_frame_size':[96,64],'source_anchor':[48,64],'output_frame_size':[384,256],'source_idle_frame':9,'source_frame_count':19,'source_columns':16,'frame_mapping':paths,'required_source_frames':audit['body']['required_source_frames'],'variant_keys':['original_class_17_enemy_normal'],'output_atlas':save(atlas,'battle-atlas.png','原槽位战斗图集')['path'],'revision':REV,'status':'review_candidate','runtime_integrated':False,'review_note':note,'palette':HEX,'batches':[{'id':'骸卫完整姿势','review':'../../../'+REV+'/battle-light.png','status':'review_candidate'}]}
 boards(m,b);write(OUT/'mapping-drafts.json',{'maps':maps_mapping,'battle':battle_mapping});write(OUT/'asset-manifest.json',{'revision':REV,'palette':HEX,'assets':ASSETS,'registration':REG,'runtime_integrated':False,'user_acceptance':'pending'})
 if publish:
  write(MP,maps_mapping);write(BP,battle_mapping);write(MP.parent.parent/'manifest.json',{'id':'class-17-enemy','revision':REV,'status':'review_candidate','runtime_integrated':False,'maps_mapping':'maps/frame_mapping.json','battle_mapping':'battle/frame_mapping.json','review_record':'../../'+REV+'/README.md'})
 print(json.dumps({'published':publish,'assets':len(ASSETS),'map_slots':14,'battle_slots':len(b)}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');args=p.parse_args();main(args.publish)
