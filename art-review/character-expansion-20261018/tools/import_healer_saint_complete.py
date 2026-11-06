#!/usr/bin/env python3
"""Register allied healer and saint art to their unchanged native programs."""
from baseline_json import read_baseline
import argparse,copy,json,math,colorsys
from functools import lru_cache
from PIL import Image,ImageDraw
from build_gallery import ROOT,file_hash
from export_gallery import font
from prepare_healer_saint_complete import REV,OUT,SRC,write
import import_knight_redraw_v3 as helper
import import_sniper_complete as io
HEX=['172638','3976b5','e4e1c8','dda77d','78a99b'];C=[tuple(bytes.fromhex(h))for h in HEX]
REG=[];FIXED=[];io.OUT=OUT
def box(p):return[min(x for x,y in p),min(y for x,y in p),max(x for x,y in p)+1,max(y for x,y in p)+1]
def center(b):return[(b[0]+b[2])/2,(b[1]+b[3])/2]
@lru_cache(maxsize=100000)
def material(rgb):
 h,s,v=colorsys.rgb_to_hsv(*(x/255 for x in rgb))
 if v<.43 and .48<h<.76:return C[0]
 return min(C,key=lambda c:sum((a-b)**2 for a,b in zip(c,rgb)))
def quant(im):
 q=Image.new('RGBA',im.size);q.putdata([(*material(p[:3]),255)if p[3]>=240 else(0,0,0,0)for p in im.getdata()]);return q
@lru_cache(maxsize=10)
def figures(c,name,count,cols):
 path=SRC/f'class-{c}'/name;raw=Image.open(path).convert('RGBA');pix=raw.load();cs=helper.parts((x,y)for y in range(raw.height)for x in range(raw.width)if pix[x,y][3]>=240);cs=[p for p in cs if len(p)>1500];assert len(cs)==count,(c,name,len(cs));cs.sort(key=lambda p:center(box(p))[1]);order=[]
 for n in range(0,count,cols):order.extend(sorted(cs[n:n+cols],key=lambda p:box(p)[0]))
 out=[]
 for i,points in enumerate(order):
  b=box(points);im=Image.new('RGBA',(b[2]-b[0],b[3]-b[1]))
  for x,y in points:im.putpixel((x-b[0],y-b[1]),pix[x,y])
  im=quant(im);back=name=='walk-master.png'and i<2
  if back:
   whites=helper.parts((x,y)for y in range(round(im.height*.65))for x in range(round(im.width*.78))if im.getpixel((x,y))==(*C[2],255));veil=max(whites,key=len);vb=box(veil);fp=[center(vb)[0],vb[1]+im.height*.16];fb=vb
  else:
   skin=helper.parts((x,y)for y in range(round(im.height*.68))for x in range(im.width)if im.getpixel((x,y))==(*C[3],255));good=[]
   for p in skin:
    bb=box(p);w,h=bb[2]-bb[0],bb[3]-bb[1]
    if len(p)>30 and .35<w/h<2 and h<im.height*.30:good.append(p)
   assert good,(c,name,i,'face absent')
   def score(p):
    bb=box(p);eyes=[(x,y)for y in range(bb[1],bb[3])for x in range(bb[0],bb[2])if im.getpixel((x,y))==(*C[2],255)];return(len(eyes)>0,len(p)/(1+20*(center(bb)[1]/im.height-.20)**2))
   face=max(good,key=score);fb=box(face);fp=center(fb)
   if c==17 and name=='battle-1-master.png'and i==0:
    # Raised forearm encloses white sleeve pixels; it is not the face.
    face=max((p for p in good if center(box(p))[0]>im.width*.35),key=lambda p:len(p));fb=box(face);fp=center(fb)
  out.append((im,{'class_id':c,'source':name,'source_index':i,'source_bounds':b,'face':fp,'face_box':fb,'back':back,'source_sha256':file_hash(path),'opaque_alpha_threshold':240}))
 return out
def clean(im,label):
 cs=helper.parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))[3]);removed=0
 for p in cs[1:]:
  assert len(p)<=12,(label,'detached',len(p),box(p))
  for xy in p:im.putpixel(xy,(0,0,0,0));removed+=1
 return im,removed
def register(fig,size,target,floor,label):
 im,meta=fig;p=meta['face'];scale=(floor-target[1])/(im.height-p[1]);dims=[round(im.width*scale),round(im.height*scale)];small=im.resize(dims,Image.Resampling.NEAREST);at=[round(target[0]-p[0]*dims[0]/im.width),floor-dims[1]];q=Image.new('RGBA',size);q.alpha_composite(small,tuple(at));assert sum(p[3]>0 for p in q.getdata())==sum(p[3]>0 for p in small.getdata()),(label,'clipping',dims,at);q,removed=clean(q,label);REG.append({**meta,'label':label,'target_head':target,'floor':floor,'scale':scale,'dimensions':dims,'translation':at,'clipped_pixels':0,'tiny_resampling_specks_removed':removed});return q
def fixed(poses,ids,regions,label):
 for i in ids[1:]:
  for b in regions:poses[i].paste(poses[ids[0]].crop(b),b[:2])
 FIXED.append({'label':label,'frames':ids,'regions':regions,'whole_body_bob':[0,0]})
def maps(c):
 idle={i:register(f,(96,96),[49,32],88,f'{c}-idle-{i}')for i,f in enumerate(figures(c,'idle-master.png',3,3))}
 # Each complete head/neck and planted lower robe is shared, arms stay articulated.
 fixed(idle,[0,1,2],[[38,15,72,48],[0,58,96,96]],f'{c} idle head neck and planted lower robe')
 for i in idle:idle[i],_=clean(idle[i],f'{c} final idle {i}')
 if c==18:idle[1]=idle[0].copy()
 raw=figures(c,'walk-master.png',6,3);walk={}
 for i,f in enumerate(raw):
  target=[64,40]if i<2 else[66,40]if i in[2,3]else[64,40]
  im=register(f,(128,96),target,94,f'{c}-walk-{i}')
  # Generated saint profile faces left; native slots2/3 are right facing.
  if c==17 and i in[2,3]:im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
  walk[i]=im
 if c==17:
  for i,f in zip([4,5],figures(c,'front-master.png',2,2)):walk[i]=register(f,(128,96),[64,40],94,f'{c}-front-repaired-{i}')
 for ids in[[0,1],[2,3],[4,5]]:
  fixed(walk,ids,[[0,0,128,69]],f'{c} walking fixed complete upper body {ids}')
  for i in ids:walk[i],_=clean(walk[i],f'{c} walk seam {i}')
 # Alternate the complete front lower robe/shoes around the same hip axis;
 # copied upper body keeps both hands, neck and centered front face intact.
 if c==18:
  # Mirror only the complete lower robe/shoes around the hip; the staff is
  # outside this region and remains in the same hand from tip to bottom.
  lower=walk[4].crop((0,69,128,96));staff=lower.copy();robe=lower.copy()
  staff.paste((0,0,0,0),(50,0,128,27));robe.paste((0,0,0,0),(0,0,50,27));staff.alpha_composite(robe.transpose(Image.Transpose.FLIP_LEFT_RIGHT));walk[5].paste(staff,(0,69))
  walk[3].paste(walk[2].crop((82,69,92,96)),(82,69))
 # Native saint back slots are identical: keep the same complete artwork.
 if c==17:walk[1]=walk[0].copy()
 walk[6]=walk[2].transpose(Image.Transpose.FLIP_LEFT_RIGHT);walk[7]=walk[3].transpose(Image.Transpose.FLIP_LEFT_RIGHT)
 for i in walk:walk[i],_=clean(walk[i],f'{c} final walk {i}')
 return{'tactical-idle':{i:idle[j].copy()for i,j in enumerate([0,1,2,1,0,1])},'tactical-walk':walk}
def battle(c):
 raw=dict(zip([7,8],figures(c,'battle-master.png',2,2)))if c==18 else{**dict(zip([9,17,18,19,20,21],figures(c,'battle-0-master.png',6,3))),**dict(zip([22,23,24,25,26,27],figures(c,'battle-1-master.png',6,3)))}
 poses={}
 for i,f in raw.items():
  native=Image.open(SRC/f'class-{c}'/f'native-battle-{i:03}.png');floor=native.getbbox()[3]*4
  poses[i]=register(f,(320 if c==18 else 384,256),[172 if c==18 else 224,144],floor,f'{c}-battle-{i}')
 # Planted legs and lower robe remain consistent across the continuous gestures.
 fixed(poses,list(raw),[[162 if c==18 else 180,207,320 if c==18 else 384,256]],f'{c} planted battle lower body; raised staff remains whole')
 for i in poses:poses[i],_=clean(poses[i],f'{c} final battle {i}')
 return poses
def board(entries,c,kind):
 cols=4;cw,ch=(300,270)if kind=='maps'else(420,320);name='疗愈师'if c==18 else'济世术师'
 for light in[False,True]:
  q=Image.new('RGBA',(cols*cw,52+ch*math.ceil(len(entries)/cols)),(220,222,216,255)if light else(32,45,53,255));d=ImageDraw.Draw(q);fg=(23,38,56)if light else(235,243,242);d.text((q.width//2,25),'我方'+name+' · '+('待机与四向行走'if kind=='maps'else'战斗全姿势'),font=font(21),anchor='mm',fill=fg)
  for n,(label,im)in enumerate(entries):
   original_width=im.width
   if kind=='maps':im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
   x=n%cols*cw+(cw-im.width)//2;y=52+n//cols*ch
   if kind=='maps':
    sh=Image.open(ROOT/'gold-knight-walk-v3-20261020/ground-shadow.png').convert('RGBA').resize((80,12),Image.Resampling.NEAREST);sh.putalpha(sh.getchannel('A').point(lambda v:round(v*.30)));q.alpha_composite(sh,(n%cols*cw+cw//2-40,y+(88 if original_width==96 else 94)*2-6))
   q.alpha_composite(im,(x,y));assert d.textbbox((0,0),label,font=font(16))[2]<cw-32;d.text((n%cols*cw+cw//2,y+ch-17),label,font=font(16),anchor='mm',fill=fg)
  io.save(q.convert('RGB'),f'class-{c}-{kind}-'+('light'if light else'dark')+'.png','pose board; measured text/figure safe areas; continuous map shadow')
def build(publish=False):
 b=read_baseline(OUT/'baseline.json');draft={};template=json.loads((ROOT/'professions/class-16-ally/maps/frame_mapping.json').read_text());audit=json.loads((ROOT/'source-input/corrected-tactical-walk/overlay.json').read_text())
 for c in[18,17]:
  name='疗愈师'if c==18 else'济世术师';actor=f'class-{c}-ally';mp=maps(c);bp=battle(c);note=name+'：沿用女法师蓝白、深蓝与肤色，仅增加柔和玉绿，减少红灰。纯色头发、哑光衣袍。地图固定完整头颈及躯干，保留原作袍摆与交替步态、连续阴影。'+('细杖举手施法。'if c==18 else'进阶双层白肩披、长披巾和细颈圆腹白宝瓶，另一臂按原作伸手、举臂、收回。')+'原作程序、总时长与唯一结算保持；职业样板不代表所有同职业角色解锁全部法术。'
  m={k:copy.deepcopy(v)for k,v in template.items()if k in['schema_version','width_height_scale']};m.update(character_id=actor,actor_id=actor,class_id=c,source_side='ally',display_name='盟军'+name,display_class_name=name,revision=REV,status='review_candidate',runtime_integrated=False,palette=HEX,review_note=note,scenarios=[])
  for old in template['scenarios']:
   kind=old['id'];poses=mp[kind];s={k:copy.deepcopy(v)for k,v in old.items()if k in['id','source_frame_size','source_anchor','output_frame_size','output_anchor','logical_render_scale','default_facing','directions','direction_mirror_x','timing','native_actor_origin']};s.update(source_atlas=f'../../../source-input/corrected-tactical-walk/{actor}.png'if kind=='tactical-walk'else f'../../../source-input/legacy-assets/assets/original/graphics/map_units/class_{c}_ally.png',revision=REV,status='review_candidate',display_name='盟军'+name,review_note=note,frame_mapping=[],motion_review='../../../'+REV+'/README.md',source_aliases=next(r['aliases']for r in json.loads((OUT/'source-audit.json').read_text())['sources']if r['class']==c and r['kind']==('walk'if kind=='tactical-walk'else'idle')),ground_shadow={'path':'gold-knight-walk-v3-20261020/ground-shadow.png','size':[10,1.5],'offset':[0,-1]if kind=='tactical-walk'else[0,-2],'alpha':.30})
   if kind=='tactical-walk':s['source_audit']={**audit['records'][actor],'status':'verified_native_tactical','overlay':'../../../source-input/corrected-tactical-walk/overlay.json'}
   w,h=s['output_frame_size'];atlas=Image.new('RGBA',(w*len(poses),h))
   for i,im in sorted(poses.items()):
    p=io.save(im,f'class-{c}/{kind}/frame-{i:03}.png','five matte material native map pose');s['frame_mapping'].append({'source_index':i,'source_frame':i,'output_index':i,'path':p,'output_path':p,'size':[w,h],'bytes':io.ASSETS[-1]['bytes'],'sha256':io.ASSETS[-1]['sha256']});atlas.alpha_composite(im,(w*i,0))
   s['output_atlas']=io.save(atlas,f'class-{c}/{kind}-atlas.png','original slot order');m['scenarios'].append(s)
  draft[f'professions/{actor}/maps/frame_mapping.json']=m;body=b['classes'][str(c)]['body'];order=sorted(bp);w,h=body['frame_size'];paths={};atlas=Image.new('RGBA',(w*4*len(order),h*4))
  for n,i in enumerate(order):paths[str(i)]=io.save(bp[i],f'class-{c}/battle/frame-{i:03}.png','new full native gesture and complete connected held implement');atlas.alpha_composite(bp[i],(w*4*n,0))
  bm={'schema_version':1,'character_id':actor,'original_class_id':c,'source_side':'ally','display_name':'盟军'+name,'display_class_name':name,'revision':REV,'status':'review_candidate','runtime_integrated':False,'review_note':note,'palette':HEX,'source_atlas':f'../../../source-input/original-motion/class-{c}.png','source_frame_size':body['frame_size'],'source_anchor':body['anchor'],'output_anchor':[v*4 for v in body['anchor']],'output_frame_size':[w*4,h*4],'source_idle_frame':body['sequences']['idle'][0],'source_frame_count':body['frames'],'source_columns':16,'frame_mapping':paths,'required_source_frames':order,'variant_keys':list(b['classes'][str(c)]['variants']),'output_atlas':io.save(atlas,f'class-{c}/battle-atlas.png','all required native slots'),'output_atlas_order':order,'batches':[{'id':'全姿势','review':f'../../../{REV}/class-{c}-battle-light.png','status':'review_candidate'}],'qa_report':'../../../'+REV+'/verification.json'}
  previous=ROOT/f'professions/{actor}/battle/frame_mapping.json'
  if previous.exists():
   old=json.loads(previous.read_text());bm.update({k:old[k]for k in['review_timeline','heal_effect_revision','heal_qa_report','shared_spell_ids']if k in old})
  draft[f'professions/{actor}/battle/frame_mapping.json']=bm
  board([(('待机'if kind=='tactical-idle'else['上','上','右','右','下','下','左','左'][i])+f' {i}',im)for kind,poses in mp.items()for i,im in poses.items()if kind!='tactical-idle'or i<3],c,'maps');board([(f'原姿势 {i}',im)for i,im in sorted(bp.items())],c,'battle')
  if publish:write(ROOT/f'professions/{actor}/manifest.json',{'id':actor,'class_id':c,'revision':REV,'status':'review_candidate','runtime_integrated':False,'maps_mapping':'maps/frame_mapping.json','battle_mapping':'battle/frame_mapping.json','review_record':'../../'+REV+'/README.md'})
 write(OUT/'mapping-drafts.json',draft);write(OUT/'asset-manifest.json',{'revision':REV,'tool':'built-in image_gen','palette':HEX,'assets':io.ASSETS,'registrations':REG,'fixed_regions':FIXED,'runtime_integrated':False,'enemy_excluded':True})
 if publish:
  for p,m in draft.items():write(ROOT/p,m)
 print(json.dumps({'assets':len(io.ASSETS),'registrations':len(REG),'published':publish}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--inspect',action='store_true');p.add_argument('--publish',action='store_true');a=p.parse_args()
 if a.inspect:
  for c in[18,17]:
   for name,n,cols in[('idle-master.png',3,3),('walk-master.png',6,3)]+([('battle-master.png',2,2)]if c==18 else[('battle-0-master.png',6,3),('battle-1-master.png',6,3)]):print(c,name,[(list(im.size),m['face'],m['face_box'])for im,m in figures(c,name,n,cols)],flush=True)
 else:build(a.publish)
