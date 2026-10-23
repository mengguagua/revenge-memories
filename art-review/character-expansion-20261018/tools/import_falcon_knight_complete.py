#!/usr/bin/env python3
"""Class5 native flight poses, six matte materials and ImageGen cavalry lance."""
import argparse,copy,json,colorsys,math
from functools import lru_cache
from PIL import Image,ImageDraw
from build_gallery import ROOT,file_hash
from export_gallery import font
from prepare_falcon_knight_complete import OUT,SRC,REV,write
import import_sniper_complete as io
io.OUT=OUT
HEX=['172638','3976b5','e4e1c8','dda77d','b96369','c98953'];C=[tuple(bytes.fromhex(h))for h in HEX]
REG=[];CENTERS=[];WEAPONS=[]
# Own pose coordinates. Helmet, braid, exposed face are separate materials.
B={0:([200,214,227,239],[216,222,254,243],[206,225,219,240]),1:([182,218,212,246],[195,233,248,259],[187,236,201,251]),2:([170,214,201,243],[182,230,242,257],[174,234,190,250]),3:([187,240,214,264],[199,250,247,272],[192,253,205,267]),4:([204,240,234,269],[216,253,262,280],[208,258,223,275]),5:([206,200,241,232],[220,213,273,245],[211,221,230,240]),6:([202,211,232,241],[216,224,260,247],[208,225,223,242]),7:([200,211,231,241],[216,224,260,247],[206,225,222,242]),49:([202,213,234,244],[218,228,267,253],[207,229,225,249]),50:([202,211,232,241],[218,224,260,246],[208,226,223,243])}
M={0:([63,8,80,20],[61,19,81,43],None),1:([61,7,78,20],[59,19,77,42],None),2:([52,1,69,13],[43,9,57,23],[59,9,69,21]),3:([51,0,68,13],[35,9,57,24],[58,9,69,22]),4:([51,8,74,23],[43,17,86,29],[58,18,72,30]),5:([53,7,76,22],[47,15,86,27],[60,16,74,28])}
I={0:([50,20,68,33],[39,25,55,38],[57,29,69,43]),1:([43,20,62,33],[23,25,47,40],[50,29,63,42]),2:([41,19,60,33],[19,24,46,41],[48,28,61,42])}
AXIS={0:((181,240),(128,234,175,247)),1:((161,252),(115,245,156,259)),2:((156,249),(103,242,151,256)),3:((164,265),(128,259,159,272)),4:((176,267),(105,260,170,274)),5:((185,232),(136,224,180,240)),6:((185,241),(108,234,179,249)),7:((181,254),(108,247,175,262))}

def inside(x,y,b):return b is not None and b[0]<=x<b[2]and b[1]<=y<b[3]
@lru_cache(maxsize=80000)
def material(rgb,hair,face):
 r,g,b=rgb;h,s,v=colorsys.rgb_to_hsv(r/255,g/255,b/255)
 if v<.26 or .18*r+.72*g+.10*b<54:return C[0]
 if hair and(h<.10 or h>.96)and s>.35 and r>1.25*g:return C[4]
 if face and h<.16 and s>.20 and r>1.04*g and r>1.25*b and r>125:return C[3]
 if .075<h<.19 and s>.42:return C[5]if v>.43 else C[0]
 if s<.30:return C[2]if v>.62 else C[1]if v>.41 else C[0]
 if .48<h<.83:return C[2]if v>.8 and s<.41 else C[1]if v>.43 else C[0]
 return C[1]if v>.44 else C[0]

def recolor(im,spec,label):
 helm,hair,face=spec;im=im.convert('RGBA');q=Image.new('RGBA',im.size)
 for y in range(im.height):
  for x in range(im.width):
   p=im.getpixel((x,y))
   if p[3]<128:continue
   # The open helmet's gray/white crown is armor, never red hair.
   q.putpixel((x,y),(*material(p[:3],inside(x,y,hair)and not inside(x,y,helm),inside(x,y,face)),255))
 REG.append({'label':label,'helmet':helm,'hair':hair,'face':face,'source_alpha_threshold':128});return q

def helmet_anchor(im,box):
 pts=[(x,y)for y in range(box[1],box[3])for x in range(box[0],box[2])if im.getpixel((x,y))==(*C[2],255)]
 if not pts:raise ValueError(('Missing ivory helmet',box))
 top=min(y for x,y in pts);cap=[x for x,y in pts if top<=y<top+3];return [(min(cap)+max(cap))//2,top]

def fixed(poses,ids,spec,label,target_x):
 anchors={i:helmet_anchor(poses[i],spec[i][0])for i in ids};target=[target_x,max(a[1]for a in anchors.values())]
 for i in ids:
  im=poses[i];a=anchors[i];delta=[target[k]-a[k]for k in[0,1]];cut=84 if im.width==128 else 96;body=im.crop((0,0,im.width,cut));q=Image.new('RGBA',im.size);q.alpha_composite(body,tuple(delta))
  assert sum(p[3]>0 for p in body.getdata())==sum(p[3]>0 for p in q.getdata()),(label,i,'clipping',delta)
  if cut<96:q.paste(im.crop((0,cut,im.width,96)),(0,cut))
  box=[spec[i][0][k]+delta[k%2]for k in range(4)];assert helmet_anchor(q,box)==target
  poses[i]=q;CENTERS.append({'group':label,'slot':i,'original_anchor':a,'fixed_helmet_anchor':target,'translation':delta,'registered_helmet_region':box,'native_projection_rows_unmoved':cut<96,'clipped_opaque_pixels':0})

def quant(im):
 q=Image.new('RGBA',im.size);q.putdata([(*min(C,key=lambda c:sum((a-b)**2 for a,b in zip(c,p[:3]))),255)if p[3]>=128 else(0,0,0,0)for p in im.getdata()]);return q

def lance():
 im=Image.open(SRC/'lance-master.png').convert('RGBA');pts=[(x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))[3]>=128];comp=io.helper.parts(pts)[0];box=io.box(comp);q=Image.new('RGBA',(box[2]-box[0],box[3]-box[1]))
 for x,y in comp:q.putpixel((x-box[0],y-box[1]),im.getpixel((x,y)))
 q=quant(q);io.save(q,'source/lance-clean.png','ImageGen rigid weapon master isolated by true alpha, exact six matte colors');return q

def weapon_layer(size,asset,length,grip,angle=0):
 small=asset.resize((length,max(3,round(asset.height*length/asset.width))),Image.Resampling.NEAREST);gx=round(length*.845);gy=small.height//2
 if angle==90:small=small.transpose(Image.Transpose.ROTATE_90);gx,gy=gy,length-1-gx
 q=Image.new('RGBA',size);at=[grip[0]-gx,grip[1]-gy];q.alpha_composite(small,tuple(at));return q,at,small

def battle_weapon(im,original,i,asset):
 grip,erase=AXIS[i];q=im.copy();q.paste((0,0,0,0),erase);layer,at,small=weapon_layer(q.size,asset,150,grip);q.alpha_composite(layer)
 # Original glove sits on the short rear grip; it is not erased by the weapon.
 hand=(grip[0]-4,grip[1]-5,grip[0]+7,grip[1]+6);patch=im.crop(hand);q.alpha_composite(patch,hand[:2]);WEAPONS.append({'kind':'battle','slot':i,'grip':grip,'weapon_length':150,'new_weapon_bounds':[*at,at[0]+small.width,at[1]+small.height],'old_weapon_removal':erase,'original_glove_retained':True});return q

def ready_pose():
 raw=Image.open(SRC/'throw-ready-master.png').convert('RGBA').resize((384,544),Image.Resampling.NEAREST);a=raw.getchannel('A').point(lambda x:255 if x>=128 else 0);box=a.getbbox();footbox=(220,370,270,425);pts=[(x,y)for y in range(footbox[1],footbox[3])for x in range(footbox[0],footbox[2])if raw.getpixel((x,y))[3]>=128];bottom=max(y for x,y in pts)+1;feet=[x for x,y in pts if y>=bottom-6];fx=(min(feet)+max(feet))/2
 scale=(384-108)/(bottom-box[1]);dims=[round(raw.width*scale),round(raw.height*scale)];small=raw.resize(dims,Image.Resampling.NEAREST);at=[round(212-fx*scale),round(384-bottom*scale)];q=Image.new('RGBA',(384,544));q.alpha_composite(small,tuple(at));spec=B[49];q=recolor(q,spec,'battle-49-new-weapon')
 REG.append({'label':'new-ready-49-registration','native_primary_hoof':[212,384],'native_top':108,'generated_foot': [fx,bottom],'uniform_scale':scale,'translation':at,'complete_generation_source':'source/throw-ready-master.png'});return q

def board(items,name,battle=False):
 cw,ch=(420,600)if battle else(340,300);cols=4
 for light in[False,True]:
  q=Image.new('RGB',(cw*cols,56+ch*math.ceil(len(items)/cols)),(220,222,216)if light else(32,45,53));d=ImageDraw.Draw(q);fg=(23,38,56)if light else(235,239,239);d.text((q.width//2,25),'盟军隼骑士 · '+('战斗姿势'if battle else'待机／四向移动'),anchor='mm',font=font(22),fill=fg)
  for n,(label,im)in enumerate(items):
   if not battle:im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
   x=n%cols*cw+(cw-im.width)//2;y=56+n//cols*ch;q.paste(im,(x,y),im);d.text((n%cols*cw+cw//2,y+im.height+22),label,anchor='mm',font=font(18),fill=fg)
  io.save(q,name+'-'+('light'if light else'dark')+'.png','all poses on light/dark backgrounds, labels inside measured safe margins')

def build(publish=False):
 b=json.loads((OUT/'baseline.json').read_text());p=ROOT/'professions/class-5-ally';asset=lance();maps={};battle={}
 for s in b['maps']['scenarios']:
  kind=s['id'];spec=I if kind=='tactical-idle'else M;maps[kind]={}
  for f in s['frame_mapping']:
   i=f['source_index']
   if kind=='tactical-idle'and i>2:continue
   if kind=='tactical-walk'and i in[6,7]:continue
   source=Image.open((p/'maps'/f['output_path']).resolve()).convert('RGBA');q=recolor(source,spec[i],f'{kind}-{i}')
   if kind=='tactical-walk'and i in[0,1,4,5]:
    grips={0:(90,29),1:(85,28),4:(44,32),5:(46,30)};erase={0:(86,0,95,65),1:(81,0,90,64),4:(40,0,49,70),5:(42,0,51,69)}
    for yy in range(erase[i][1],erase[i][3]):
     for xx in range(erase[i][0],erase[i][2]):
      pp=source.getpixel((xx,yy));hh,ss,vv=colorsys.rgb_to_hsv(*(z/255 for z in pp[:3]));warm=(hh<.17 or hh>.97)and ss>.28 and pp[0]>1.15*pp[1];center=grips[i][0]
      if warm or yy<8 or(q.getpixel((xx,yy))[:3]in[C[0],C[1]])or(yy>52 and abs(xx-center)<=3):q.putpixel((xx,yy),(0,0,0,0))
    layer,at,small=weapon_layer(q.size,asset,56,grips[i],90);q.alpha_composite(layer)
    # Keep the native gauntlet above the rear grip.
    gx,gy=grips[i];hand=(gx-2,gy-3,gx+3,gy+3);handim=recolor(source,spec[i],f'{kind}-{i}-glove').crop(hand);q.alpha_composite(handim,hand[:2]);WEAPONS.append({'kind':kind,'slot':i,'grip':grips[i],'weapon_length':56,'point_down':True,'old_weapon_removal':erase[i]})
   maps[kind][i]=q
 fixed(maps['tactical-idle'],[0,1,2],I,'idle',48)
 for i,j in[(3,1),(4,0),(5,1)]:maps['tactical-idle'][i]=maps['tactical-idle'][j].copy()
 fixed(maps['tactical-walk'],[0,1],M,'up',64);fixed(maps['tactical-walk'],[2,3],M,'right',63);fixed(maps['tactical-walk'],[4,5],M,'down',64)
 for i,j in[(6,2),(7,3)]:maps['tactical-walk'][i]=maps['tactical-walk'][j].transpose(Image.Transpose.FLIP_LEFT_RIGHT)
 for i in[0,1,2,3,4,5,6,7,49,50]:
  if i==49:q=ready_pose()
  else:
   source=Image.open((p/'battle'/b['battle']['frame_mapping'][str(i)]).resolve()).convert('RGBA');q=recolor(source,B[i],f'battle-{i}')
   if i in AXIS:q=battle_weapon(q,source,i,asset)
  battle[i]=q
 for i in[25,48]:battle[i]=battle[0].copy()
 for kind,poses in {**maps,'battle':battle}.items():
  for i,im in sorted(poses.items()):io.save(im,f'ally/{kind}/frame-{i:03}.png','own native class5 registered pose; six matte materials and ImageGen cavalry lance')
 # One native thrown-weapon event. Only visual asset is replaced.
 native=Image.open(ROOT/'source-input/effects/1ecba259419456.png').convert('RGBA');projectile=Image.new('RGBA',native.size);small=asset.resize((38,max(3,round(asset.height*38/asset.width))),Image.Resampling.NEAREST);projectile.alpha_composite(small,(24,10));effect=io.save(projectile,'ally/flying-lance.png','same native 64x16 canvas, anchor and flight program; lance matches held weapon')
 board([(f'{kind} {i}',poses[i])for kind,poses in maps.items()for i in(range(3)if kind=='tactical-idle'else range(8))],'ally-maps');board([(f'源姿势 {i}',battle[i])for i in[0,1,2,3,4,5,6,7,49,50]],'ally-battle',True)
 if publish:
  note='我方隼骑士：开放米白头盔、完整臂胫甲与坐骑额甲，沿用天马蓝白／纯色红发并增加柔和橙色饰边；更换锥形骑枪。保留本类原作扑翼／收腿／前刺／投枪的顺序、循环、节奏和结算；地图固定头盔定位，原生投影独立保留。'
  m=copy.deepcopy(b['maps']);m.update(revision=REV,display_name='盟军隼骑士',status='review_candidate',modified_by='codex',review_note=note,palette=HEX,runtime_integrated=False,qa_report='../../../'+REV+'/verification.json')
  for s in m['scenarios']:
   poses=maps[s['id']];w,h=next(iter(poses.values())).size;atlas=Image.new('RGBA',(len(poses)*w,h));records=[]
   for i,im in sorted(poses.items()):
    path=OUT/f'ally/{s["id"]}/frame-{i:03}.png';f='../../../'+path.relative_to(ROOT).as_posix();atlas.alpha_composite(im,(i*w,0));records.append({'source_index':i,'source_frame':i,'output_index':i,'path':f,'output_path':f,'revision':REV,'size':[w,h],'bytes':path.stat().st_size,'sha256':file_hash(path)})
   s.update(revision=REV,status='review_candidate',frame_mapping=records,output_atlas=io.save(atlas,f'ally/{s["id"]}-atlas.png','exact native slot order'),review_note=note,review_status='pending_user_visual_acceptance',motion_review={'fixed_helmet_centers':CENTERS,'native_timing_unchanged':True,'projection_rows': [21,24]})
   s['output_atlas_bytes']=(OUT/f'ally/{s["id"]}-atlas.png').stat().st_size
  write(p/'maps/frame_mapping.json',m)
  bm=copy.deepcopy(b['battle']);order=sorted(battle);atlas=Image.new('RGBA',(len(order)*384,544));records=[]
  for n,i in enumerate(order):
   path=OUT/f'ally/battle/frame-{i:03}.png';f='../../../'+path.relative_to(ROOT).as_posix();atlas.alpha_composite(battle[i],(n*384,0));records.append({'source_frame':i,'path':f,'size':[384,544],'bytes':path.stat().st_size,'sha256':file_hash(path)})
  bm.update(revision=REV,display_name='盟军隼骑士',display_class_name='隼骑士',status='review_candidate',modified_by='codex',review_note=note,palette=HEX,runtime_integrated=False,frame_mapping={str(f['source_frame']):f['path']for f in records},records=records,output_atlas=io.save(atlas,'ally/battle-atlas.png','required native class5 battle slots and aliases'),output_atlas_order=order,effect_overrides={'1ecba259419456':effect},qa_report='../../../'+REV+'/verification.json',batches=[{'id':'隼骑士蓝白橙与锥形骑枪','review':'../../../'+REV+'/ally-battle-light.png','status':'review_candidate'}]);bm['output_atlas_bytes']=(OUT/'ally/battle-atlas.png').stat().st_size;write(p/'battle/frame_mapping.json',bm);write(OUT/'mapping-drafts.json',{'maps':m,'battle':bm})
 write(OUT/'registration.json',{'palette':HEX,'materials':REG,'fixed_map_centers':CENTERS,'weapon_registrations':WEAPONS,'native_aliases':{'battle_25_48':0,'map_idle':[0,1,2,1,0,1]},'side_weapon_visibility':'source side/idle poses keep weapon stowed/occluded; no new arm gestures introduced','runtime_integrated':False});write(OUT/'asset-manifest.json',{'revision':REV,'assets':io.ASSETS});print(json.dumps({'revision':REV,'map_slots':14,'battle_slots':12,'publish':publish}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');a=p.parse_args();build(a.publish)
