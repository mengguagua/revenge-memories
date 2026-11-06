#!/usr/bin/env python3
"""Register generated female-mage art to separate immutable faction programs."""
import argparse,copy,json,math
from functools import lru_cache
from PIL import Image,ImageDraw
from build_gallery import ROOT,file_hash
from export_gallery import font
from prepare_female_mage_complete import REV,OUT,SRC,write
import import_knight_redraw_v3 as helper
import import_sniper_complete as io
HEX=['172638','3976b5','e4e1c8','dda77d','a9687a'];EHEX=['172638','57577f','c2c5dc','dda77d','98718c']
C=[tuple(bytes.fromhex(h))for h in HEX];EC=[tuple(bytes.fromhex(h))for h in EHEX]
REG=[];FIXED=[];io.OUT=OUT

def box(p):return[min(x for x,y in p),min(y for x,y in p),max(x for x,y in p)+1,max(y for x,y in p)+1]
def center(b):return[(b[0]+b[2])/2,(b[1]+b[3])/2]
@lru_cache(maxsize=100000)
def material(rgb):return min(C,key=lambda c:sum((a-b)**2 for a,b in zip(c,rgb)))
def quant(im):
 q=Image.new('RGBA',im.size);q.putdata([(*material(p[:3]),255)if p[3]>=128 else(0,0,0,0)for p in im.getdata()]);return q
@lru_cache(maxsize=6)
def figures(name,count,cols):
 raw=Image.open(SRC/name).convert('RGBA');parts=helper.parts((x,y)for y in range(raw.height)for x in range(raw.width)if raw.getpixel((x,y))[3]>=128);parts=[p for p in parts if len(p)>1500];assert len(parts)==count,(name,len(parts))
 parts.sort(key=lambda p:center(box(p))[1]);ordered=[]
 for n in range(0,count,cols):ordered.extend(sorted(parts[n:n+cols],key=lambda p:box(p)[0]))
 out=[]
 for i,points in enumerate(ordered):
  b=box(points);im=Image.new('RGBA',(b[2]-b[0],b[3]-b[1]));pix=raw.load()
  for x,y in points:im.putpixel((x-b[0],y-b[1]),pix[x,y])
  im=quant(im);back=(name=='walk-master.png'and i<2)or name=='up-step-master.png'
  if back:
   band=[(x,y)for y in range(round(im.height*.2))for x in range(im.width)if im.getpixel((x,y))==(*C[2],255)];assert band;p=[center(box(band))[0],im.height*.24];fb=[0,0,0,0]
  else:
   skin=helper.parts((x,y)for y in range(round(im.height*.5))for x in range(im.width)if im.getpixel((x,y))==(*C[3],255))
   good=[c for c in skin if len(c)>30 and .45<(box(c)[2]-box(c)[0])/(box(c)[3]-box(c)[1])<2.2 and .06<center(box(c))[1]/im.height<.37]
   assert good,(name,i,'face missing')
   c=max(good,key=lambda c:len(c)/(1+30*(center(box(c))[1]/im.height-(.27 if name=='battle-master.png'and i==1 else .20))**2));fb=box(c);p=center(fb)
  if name=='battle-master.png':
   # Reviewed skin-face boxes: avoid selecting a bare arm as the face.
   fb=[[58,49,99,95],[167,120,209,166],[207,48,251,95]][i];p=center(fb)
  out.append((im,{'source':name,'source_bounds':b,'face':p,'face_box':fb,'back':back,'source_sha256':file_hash(SRC/name)}))
 return out

def register(fig,size,target,floor,label):
 im,meta=fig;p=meta['face'];scale=(floor-target[1])/(im.height-p[1]);dims=[round(im.width*scale),round(im.height*scale)];small=im.resize(dims,Image.Resampling.NEAREST);at=[round(target[0]-p[0]*dims[0]/im.width),floor-dims[1]];q=Image.new('RGBA',size);q.alpha_composite(small,tuple(at))
 assert sum(p[3]>0 for p in q.getdata())==sum(p[3]>0 for p in small.getdata()),(label,'clipped',dims,at)
 cs=helper.parts((x,y)for y in range(q.height)for x in range(q.width)if q.getpixel((x,y))[3]);removed=0
 for c in cs[1:]:
  assert len(c)<=8,(label,'detached part',len(c),box(c))
  for xy in c:q.putpixel(xy,(0,0,0,0));removed+=1
 REG.append({**meta,'label':label,'target_face':target,'floor':floor,'uniform_scale':scale,'scaled_size':dims,'translation':at,'clipped_pixels':0,'removed_tiny_resampling_specks':removed})
 return q

def freeze(poses,ids,boxes,label):
 for i in ids[1:]:
  for b in boxes:poses[i].paste(poses[ids[0]].crop(b),b[:2])
 FIXED.append({'label':label,'frames':ids,'fixed_regions':boxes,'extra_whole_body_offset':[0,0]})
def maps():
 idle={i:register(f,(96,96),[56,29],80,'idle-'+str(i))for i,f in enumerate(figures('idle-master.png',3,3))}
 freeze(idle,[0,1,2],[[41,14,69,53],[40,70,70,81]],'idle head neck torso and planted feet')
 walk={}
 targets=[[64,45],[64,45],[68,43],[68,43],[64,44],[64,44],[59,43],[59,43]]
 for i,f in enumerate(figures('walk-master.png',8,4)):walk[i]=register(f,(128,96),targets[i],96,'walk-'+str(i))
 walk[1]=register(figures('up-step-master.png',1,1)[0],(128,96),[64,45],96,'walk-1-repaired')
 for ids,b in [([0,1],[36,25,92,72]),([2,3],[55,25,83,64]),([4,5],[47,25,82,63]),([6,7],[45,25,73,64])]:freeze(walk,ids,[b],'walk fixed head neck torso '+str(ids))
 return {'tactical-idle':{i:idle[j].copy()for i,j in enumerate([0,1,2,1,0,1])},'tactical-walk':walk}

def battle():
 poses={i:register(f,(320,256),[193,150],256,'battle-'+str(i))for i,f in enumerate(figures('battle-master.png',3,3))}
 # Register complete original gestures on a common face and foot baseline;
 # keep each full raised/folded arm and flaring garment visible.
 FIXED.append({'label':'battle rigid whole-pose registration','frames':[0,1,2],'target_head':[193,150],'foot_baseline':256,'own_hands_and_garment_poses_retained':True})
 return poses

def faction(im,side):
 if side=='ally':return im.copy()
 table=dict(zip(C,EC));q=Image.new('RGBA',im.size);q.putdata([(*table[p[:3]],p[3])if p[3]else(0,0,0,0)for p in im.getdata()]);return q

def board(entries,side,kind,light):
 cols=4 if kind=='maps' else 3;cw,ch=(300,270)if kind=='maps'else(400,315);q=Image.new('RGB',(cw*cols,52+ch*math.ceil(len(entries)/cols)),(220,222,216)if light else(32,45,53));dr=ImageDraw.Draw(q);fg=(23,38,56)if light else(235,243,242)
 dr.text((q.width//2,25),('盟军'if side=='ally'else'敌方')+'女法师 · '+('地图姿势'if kind=='maps'else'战斗姿势'),anchor='mm',font=font(21),fill=fg)
 for n,(label,im)in enumerate(entries):
  if kind=='maps':im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
  x=n%cols*cw+(cw-im.width)//2;y=52+n//cols*ch;q.paste(im,(x,y),im);assert dr.textbbox((0,0),label,font=font(16))[2]<cw-24;dr.text((n%cols*cw+cw//2,y+ch-17),label,anchor='mm',font=font(16),fill=fg)
 io.save(q,f'{side}-{kind}-{"light"if light else"dark"}.png','complete pose review; clear labels and figure spacing')

def build(publish=False):
 b=json.loads((OUT/'baseline.json').read_text());mapart=maps();ba=battle();drafts={};template=json.loads((ROOT/'professions/class-19-ally/maps/frame_mapping.json').read_text());audit=json.loads((ROOT/'source-input/corrected-tactical-walk/overlay.json').read_text())
 note='女法师采用原作长发、无袖分片长裙与徒手施法。盟军沿用弓箭手蓝白、深蓝与肤色，仅加柔和玫瑰色腰带；敌方蓝紫。地图固定头颈与身体基准，保留袍摆、摆臂及交替脚步。战斗站立、举臂蓄力、伸臂释放依各自原作程序，结算与时长保持。'
 for side in ['ally','enemy']:
  actor='class-16-'+side;name='盟军女法师'if side=='ally'else'敌方女法师（移形术师）';entries={'maps':[],'battle':[]};m={k:copy.deepcopy(v)for k,v in template.items()if k in ['schema_version','width_height_scale']};m.update(character_id=actor,actor_id=actor,class_id=16,source_side=side,display_name=name,display_class_name='女法师',revision=REV,status='review_candidate',runtime_integrated=False,review_note=note,palette=HEX if side=='ally'else EHEX,scenarios=[])
  for old in template['scenarios']:
   kind=old['id'];poses=mapart[kind];s={k:copy.deepcopy(v)for k,v in old.items()if k in ['id','source_frame_size','source_anchor','output_frame_size','output_anchor','logical_render_scale','default_facing','directions','direction_mirror_x','timing','source_aliases','native_actor_origin']};s.update(source_atlas=f'../../../source-input/corrected-tactical-walk/{actor}.png'if kind=='tactical-walk'else f'../../../source-input/legacy-assets/assets/original/graphics/map_units/class_16_{side}.png',revision=REV,status='review_candidate',review_note=note,display_name=name,frame_mapping=[],motion_review='../../../'+REV+'/README.md')
   if kind=='tactical-walk':s['source_audit']={**audit['records'][actor],'status':'verified_native_tactical','overlay':'../../../source-input/corrected-tactical-walk/overlay.json'}
   w,h=s['output_frame_size'];atlas=Image.new('RGBA',(w*len(poses),h))
   for i,im in poses.items():
    im=faction(im,side);path=io.save(im,f'{side}/{kind}/frame-{i:03}.png','native map pose, five matte materials');s['frame_mapping'].append({'source_index':i,'source_frame':i,'output_index':i,'path':path,'output_path':path,'size':[w,h],'bytes':io.ASSETS[-1]['bytes'],'sha256':io.ASSETS[-1]['sha256']});atlas.alpha_composite(im,(w*i,0))
    if kind=='tactical-walk'or i<3:entries['maps'].append((('待机'if kind=='tactical-idle'else['上','上','右','右','下','下','左','左'][i])+' '+str(i),im))
   s['output_atlas']=io.save(atlas,f'{side}/{kind}-atlas.png','original slot order');m['scenarios'].append(s)
  drafts[f'professions/{actor}/maps/frame_mapping.json']=m
  body=b['source_bodies'][side];poses={};paths={};atlas=Image.new('RGBA',(320*3,256))
  for i,im in ba.items():
   im=faction(im,side)
   if side=='enemy':
    q=Image.new('RGBA',im.size);q.alpha_composite(im,(-64,0));assert sum(p[3]>0 for p in q.getdata())==sum(p[3]>0 for p in im.getdata());im=q
   poses[i]=im;paths[str(i)]=io.save(im,f'{side}/battle/frame-{i:03}.png','faction-native pose; enemy original BG registration is 16 native pixels left');atlas.alpha_composite(im,(320*i,0));entries['battle'].append((['0 · 站立','1 · 举臂蓄力','2 · 伸臂释放'][i],im))
  bm={'schema_version':1,'character_id':actor,'display_name':name,'display_class_name':'女法师','original_class_id':16,'source_side':side,'source_frame_size':body['frame_size'],'source_anchor':body['anchor'],'output_frame_size':[320,256],'source_idle_frame':0,'source_frame_count':3,'source_columns':16,'frame_mapping':paths,'required_source_frames':[0,1,2],'variant_keys':list(b['variants'][side]),'output_atlas':io.save(atlas,f'{side}/battle-atlas.png','three native battle poses'),'output_atlas_order':[0,1,2],'revision':REV,'status':'review_candidate','runtime_integrated':False,'review_note':note,'palette':HEX if side=='ally'else EHEX,'batches':[{'id':'三姿势全对照','review':f'../../../{REV}/{side}-battle-light.png','status':'review_candidate'}],'qa_report':'../../../'+REV+'/verification.json'}
  drafts[f'professions/{actor}/battle/frame_mapping.json']=bm
  for kind,ent in entries.items():
   for light in [False,True]:board(ent,side,kind,light)
  if publish:write(ROOT/f'professions/{actor}/manifest.json',{'id':actor,'revision':REV,'status':'review_candidate','runtime_integrated':False,'maps_mapping':'maps/frame_mapping.json','battle_mapping':'battle/frame_mapping.json','review_record':'../../'+REV+'/README.md'})
 if publish:
  for path,m in drafts.items():write(ROOT/path,m)
 write(OUT/'mapping-drafts.json',drafts);write(OUT/'asset-manifest.json',{'revision':REV,'palettes':{'ally':HEX,'enemy':EHEX},'assets':io.ASSETS,'registrations':REG,'fixed_regions':FIXED,'enemy_battle_native_offset':[-16,0],'runtime_integrated':False})
 print(json.dumps({'assets':len(io.ASSETS),'registrations':len(REG),'published':publish}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');p.add_argument('--inspect',action='store_true');a=p.parse_args()
 if a.inspect:
  for n,c,cols in [('idle-master.png',3,3),('walk-master.png',8,4),('battle-master.png',3,3)]:print(n,[(list(im.size),m['face'],m['face_box'])for im,m in figures(n,c,cols)],flush=True)
 else:build(a.publish)
