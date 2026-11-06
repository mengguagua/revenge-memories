#!/usr/bin/env python3
"""Register generated class11 ally poses to the native map and battle schedule."""
from baseline_json import read_baseline
import argparse,copy,json,math,colorsys
from functools import lru_cache
from PIL import Image,ImageDraw,ImageFilter
from build_gallery import ROOT,file_hash
from export_gallery import font
from prepare_spellsword_complete import REV,OUT,SRC,write
import import_knight_redraw_v3 as helper
import import_sniper_complete as io
HEX=['172638','3976b5','e4e1c8','dda77d','a9687a','a7d7e5'];C=[tuple(bytes.fromhex(h))for h in HEX];io.OUT=OUT
REG=[];FIXED=[]
def box(p):return[min(x for x,y in p),min(y for x,y in p),max(x for x,y in p)+1,max(y for x,y in p)+1]
def center(b):return[(b[0]+b[2])/2,(b[1]+b[3])/2]
@lru_cache(maxsize=100000)
def material(rgb):
 h,s,v=colorsys.rgb_to_hsv(*(x/255 for x in rgb))
 if(s<.22 and v<.70)or(.64<h<.84):return C[0]
 return min(C,key=lambda c:sum((a-b)**2 for a,b in zip(c,rgb)))
def quant(im):
 q=Image.new('RGBA',im.size);q.putdata([(*material(p[:3]),255)if p[3]>=240 else(0,0,0,0)for p in im.getdata()]);return q
@lru_cache(maxsize=16)
def figures(name,count,cols):
 raw=Image.open(SRC/name).convert('RGBA');pix=raw.load();cs=helper.parts((x,y)for y in range(raw.height)for x in range(raw.width)if pix[x,y][3]>=240);cs=[p for p in cs if len(p)>1500];assert len(cs)==count,(name,'figures',len(cs));cs.sort(key=lambda p:center(box(p))[1]);order=[]
 for n in range(0,count,cols):order.extend(sorted(cs[n:n+cols],key=lambda p:box(p)[0]))
 out=[]
 for i,points in enumerate(order):
  b=box(points);im=Image.new('RGBA',(b[2]-b[0],b[3]-b[1]))
  for x,y in points:im.putpixel((x-b[0],y-b[1]),pix[x,y])
  im=quant(im);skin=helper.parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))==(*C[3],255));good=[]
  for c in skin:
   cb=box(c);w,h=cb[2]-cb[0],cb[3]-cb[1]
   if len(c)>25 and .60<w/h<1.85 and h<im.height*.23 and cb[1]<im.height*.67:good.append(c)
  assert good,(name,i,'head missing')
  def eye_score(c):
   b=box(c);pts=[(x,y)for y in range(b[1],b[3])for x in range(b[0],b[2])if im.getpixel((x,y))==(*C[2],255)];inner=[z for z in helper.parts(pts)if len(z)<len(c)*.2 and all(b[0]<x<b[2]-1 and b[1]<y<b[3]-1 for x,y in z)];return sum(len(z)for z in inner)/math.sqrt(len(c))
  c=max(good,key=lambda c:(eye_score(c),-center(box(c))[1]));fb=box(c);head=center(fb)
  overrides=SRC/'head-landmarks.json'
  if overrides.exists():
   row=json.loads(overrides.read_text()).get(name,{}).get(str(i))
   if row:head=row['point'];fb=row.get('box',fb)
  out.append((im,{'source':name,'source_index':i,'source_bounds':b,'face':head,'face_box':fb,'source_sha256':file_hash(SRC/name)}))
 return out

def register(fig,size,target,floor,label):
 im,meta=fig;p=meta['face'];assert floor>target[1];scale=min((floor-target[1])/(im.height-p[1]),floor/im.height,target[0]/max(1,p[0]),(size[0]-target[0])/max(1,im.width-p[0]));dims=[round(im.width*scale),round(im.height*scale)];small=im.resize(dims,Image.Resampling.NEAREST);at=[round(target[0]-p[0]*dims[0]/im.width),floor-dims[1]];q=Image.new('RGBA',size);q.alpha_composite(small,tuple(at))
 assert sum(p[3]>0 for p in q.getdata())==sum(p[3]>0 for p in small.getdata()),(label,'clipped',dims,at)
 cs=helper.parts((x,y)for y in range(q.height)for x in range(q.width)if q.getpixel((x,y))[3]);specks=0
 for c in cs[1:]:
  assert len(c)<=8,(label,'detached',len(c),box(c))
  for xy in c:q.putpixel(xy,(0,0,0,0));specks+=1
 REG.append({**meta,'label':label,'target_face':target,'floor':floor,'uniform_scale':scale,'scaled_size':dims,'translation':at,'clipped_pixels':0,'tiny_resampling_specks_removed':specks});return q

def fixed(poses,ids,regions,label,protect_sword=True):
 for i in ids[1:]:
  old=poses[i].copy();mask=Image.new('L',old.size)
  if protect_sword:
   cc=helper.parts((x,y)for y in range(old.height)for x in range(old.width)if old.getpixel((x,y))==(*C[5],255))
   for c in cc:
    b=box(c)
    if len(c)>=4 and max(b[2]-b[0],b[3]-b[1])>=8:
     for xy in c:mask.putpixel(xy,255)
   mask=mask.filter(ImageFilter.MaxFilter(7))
  for b in regions:
   poses[i].paste(poses[ids[0]].crop(b),b[:2])
   for y in range(b[1],b[3]):
    for x in range(b[0],b[2]):
     if mask.getpixel((x,y))and old.getpixel((x,y))[3]:poses[i].putpixel((x,y),old.getpixel((x,y)))
 FIXED.append({'label':label,'frames':ids,'regions':regions,'sword_occlusion_protected':protect_sword,'global_offset':[0,0]})

def maps():
 idle={i:register(f,(96,96),[43,33],80,'idle-'+str(i))for i,f in enumerate(figures('idle-master.png',3,3))}
 fixed(idle,[0,1,2],[[30,24,58,53],[25,70,67,81]],'idle fixed head neck torso and feet')
 walk={};raw=figures('walk-master.png',6,3);right=figures('right-master.png',2,2)
 for i,f in enumerate(raw):
  if i in [2,3]:continue
  target=[56,46]if i<2 else[64,46]
  walk[i]=register(f,(128,96),target,96,'walk-'+str(i))
 for i,f in zip([2,3],right):walk[i]=register(f,(128,96),[70,46],96,'walk-'+str(i))
 for ids,regions in [([0,1],[[42,29,77,71]]),([2,3],[[56,29,83,71]]),([4,5],[[48,29,81,71]])]:fixed(walk,ids,regions,'walk head neck torso '+str(ids))
 for i,im in walk.items():
  cs=helper.parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))[3])
  for c in cs[1:]:
   assert len(c)<=8,(i,'map detached',len(c))
   for xy in c:im.putpixel(xy,(0,0,0,0))
 walk[6]=walk[2].transpose(Image.Transpose.FLIP_LEFT_RIGHT);walk[7]=walk[3].transpose(Image.Transpose.FLIP_LEFT_RIGHT)
 return {'tactical-idle':{i:idle[j].copy()for i,j in enumerate([0,1,2,1,0,1])},'tactical-walk':walk}

def native_face(i):
 if i in [0,1,11,23,24,50,97,98,99]or i>=107:return[48,36]
 if 2<=i<=10 or i==12:return[47.5,20]
 if i==13:return[48,21]
 if i==14:return[48,37]
 if i==15:return[44,35]
 if i in[16,17,18,19,22]:return[44,49.5]
 if i in[20,21]:return[46,20]
 if i in[25,26,27,28]:return[46,36]
 if i in[29,30,31,32]:return[47,36]
 raise ValueError(i)
def battle():
 ids=json.loads((OUT/'source-audit.json').read_text())['unique_battle_slots'];raw={}
 for n in range(0,len(ids),6):raw.update(zip(ids[n:n+6],figures(f'battle-{n//6:02}-master.png',len(ids[n:n+6]),3)))
 raw.update(zip([20,21,32],figures('battle-fix-master.png',3,3)));raw[32]=raw[29];poses={}
 for i,f in raw.items():
  source=Image.open(SRC/f'native-battle-{i:03}.png').convert('RGBA');floor=source.getbbox()[3]*4;target=[v*4 for v in native_face(i)];poses[i]=register(f,(320,288),target,floor,'battle-'+str(i))
 # Preserve the original detached slash arc at its exact native coordinates.
 native=Image.open(SRC/'native-battle-019.png').convert('RGBA');arc=Image.new('RGBA',native.size)
 parts=helper.parts((x,y)for y in range(native.height)for x in range(native.width)if native.getpixel((x,y))==(254,204,197,255));arc_points=next(c for c in parts if len(c)==63 and box(c)==[21,19,41,56])
 for xy in arc_points:arc.putpixel(xy,(*C[2],255))
 io.save(arc.resize((320,288),Image.Resampling.NEAREST),'original-slash-arc.png','unchanged original slash arc, exact position; not an extra strike')
 poses[19].alpha_composite(arc.resize((320,288),Image.Resampling.NEAREST))
 # Same exact source pixels have the same new artwork, including BG idle50/97.
 aliases=json.loads((OUT/'source-audit.json').read_text())['exact_aliases']['battle']
 for i,j in aliases.items():
  if int(i)not in poses:poses[int(i)]=poses[j].copy()
 return poses

def board(entries,name,battle=False):
 cols=4;cw,ch=(360,330)if battle else(300,270)
 for light in[False,True]:
  q=Image.new('RGB',(cols*cw,52+ch*math.ceil(len(entries)/cols)),(220,222,216)if light else(32,45,53));dr=ImageDraw.Draw(q);fg=(23,38,56)if light else(235,243,242);dr.text((q.width//2,24),'我方女魔剑士 · '+('战斗姿势'if battle else'待机与四向行走'),anchor='mm',font=font(21),fill=fg)
  for n,(label,im)in enumerate(entries):
   if not battle:im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
   x=n%cols*cw+(cw-im.width)//2;y=52+n//cols*ch;q.paste(im,(x,y),im);dr.text((n%cols*cw+cw//2,y+ch-17),label,anchor='mm',font=font(16),fill=fg)
  io.save(q,f'{name}-{"light"if light else"dark"}.png','pose board with separated centered labels')

def build(publish=False):
 mp=maps();bp=battle();note='我方女魔剑士：女法师蓝白、深蓝、肤色及玫瑰腰带，少量冰蓝；分片短战衣、白色肩部防护与高束纯色长发加强进阶感。冰晶长剑依参考图统一尖刃、银白护手及完整握柄。地图固定头颈及身体基准；近身起跳转身落地斩、回位、雷剑与空手施法按原作独立程序，原结算和总时长保持。'
 for kind,poses in {**mp,'battle':bp}.items():
  for i,im in sorted(poses.items()):io.save(im,f'ally/{kind}/frame-{i:03}.png','registered ImageGen pose; six matte materials')
 board([(kind+' '+str(i),im)for kind,poses in mp.items()for i,im in sorted(poses.items())if kind!='tactical-idle'or i<3],'ally-maps')
 board([(str(i),im)for i,im in sorted(bp.items())],'ally-battle',True)
 b=read_baseline(OUT/'baseline.json');template=json.loads((ROOT/'professions/class-16-ally/maps/frame_mapping.json').read_text());m={k:copy.deepcopy(v)for k,v in template.items()if k in ['schema_version','width_height_scale']};m.update(character_id='class-11-ally',actor_id='class-11-ally',class_id=11,source_side='ally',display_name='盟军女魔剑士',display_class_name='女魔剑士',revision=REV,status='review_candidate',runtime_integrated=False,palette=HEX,review_note=note,scenarios=[])
 for old in template['scenarios']:
  kind=old['id'];poses=mp[kind];s={k:copy.deepcopy(v)for k,v in old.items()if k in ['id','source_frame_size','source_anchor','output_frame_size','output_anchor','logical_render_scale','default_facing','directions','direction_mirror_x','timing','source_aliases','native_actor_origin']};s.update(source_atlas='../../../source-input/corrected-tactical-walk/class-11-ally.png'if kind=='tactical-walk'else'../../../source-input/legacy-assets/assets/original/graphics/map_units/class_11_ally.png',revision=REV,status='review_candidate',display_name='盟军女魔剑士',review_note=note,frame_mapping=[],motion_review='../../../'+REV+'/README.md')
  if kind=='tactical-walk':s['source_audit']={'status':'verified_native_tactical','proof':'../../../source-input/corrected-tactical-walk/verification.json','overlay':'../../../source-input/corrected-tactical-walk/overlay.json','reference_key':'class-11-ally'}
  w,h=s['output_frame_size'];atlas=Image.new('RGBA',(w*len(poses),h))
  for i,im in sorted(poses.items()):
   p=f'../../../{REV}/ally/{kind}/frame-{i:03}.png';asset=OUT/f'ally/{kind}/frame-{i:03}.png';s['frame_mapping'].append({'source_index':i,'source_frame':i,'output_index':i,'path':p,'output_path':p,'size':[w,h],'bytes':asset.stat().st_size,'sha256':file_hash(asset)});atlas.alpha_composite(im,(w*i,0))
  s['output_atlas']=io.save(atlas,f'ally/{kind}-atlas.png','original map slot order');m['scenarios'].append(s)
 order=sorted(bp);atlas=Image.new('RGBA',(320*len(order),288))
 for n,i in enumerate(order):atlas.alpha_composite(bp[i],(n*320,0))
 bm={'schema_version':1,'character_id':'class-11-ally','original_class_id':11,'source_side':'ally','display_name':'盟军女魔剑士','display_class_name':'女魔剑士','revision':REV,'status':'review_candidate','runtime_integrated':False,'review_note':note,'palette':HEX,'output_frame_size':[320,288],'source_idle_frame':50,'variant_keys':list(b['variants']),'frame_mapping':{str(i):f'../../../{REV}/ally/battle/frame-{i:03}.png'for i in order},'output_atlas':io.save(atlas,'ally/battle-atlas.png','44 required native battle slots'),'output_atlas_order':order,'batches':[{'id':'完整战斗姿势','review':f'../../../{REV}/ally-battle-light.png','status':'review_candidate'}],'qa_report':'../../../'+REV+'/verification.json'}
 write(OUT/'mapping-drafts.json',{'maps':m,'battle':bm});write(OUT/'asset-manifest.json',{'revision':REV,'palette':HEX,'registrations':REG,'fixed_regions':FIXED,'assets':io.ASSETS,'enemy_excluded_by_user':True,'runtime_integrated':False})
 if publish:
  p=ROOT/'professions/class-11-ally';write(p/'maps/frame_mapping.json',m);write(p/'battle/frame_mapping.json',bm);write(p/'manifest.json',{'id':'class-11-ally','revision':REV,'status':'review_candidate','runtime_integrated':False,'maps_mapping':'maps/frame_mapping.json','battle_mapping':'battle/frame_mapping.json','review_record':'../../'+REV+'/README.md'})
 print(json.dumps({'battle_frames':len(bp),'assets':len(io.ASSETS),'published':publish}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');p.add_argument('--inspect',action='store_true');a=p.parse_args()
 if a.inspect:
  for n,count,cols in [('idle-master.png',3,3),('walk-master.png',6,3),('right-master.png',2,2),*[(f'battle-{i:02}-master.png',6,3)for i in range(7)],('battle-fix-master.png',3,3)]:print(n,[(list(im.size),m['face'],m['face_box'])for im,m in figures(n,count,cols)],flush=True)
 else:build(a.publish)
