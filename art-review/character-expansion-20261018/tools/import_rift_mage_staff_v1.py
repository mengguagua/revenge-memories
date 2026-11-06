#!/usr/bin/env python3
"""Enemy16 staff art: authored equipment, native map legs and immutable spell programs."""
from baseline_json import read_baseline
import argparse,copy,hashlib,json,math
from functools import lru_cache
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps
from export_gallery import font
from import_knight_redraw_v3 import parts
ROOT=Path(__file__).resolve().parents[1]
REV='rift-mage-staff-v1-20261023';OUT=ROOT/REV;SRC=OUT/'source'
MP=ROOT/'professions/class-16-enemy/maps/frame_mapping.json';BP=ROOT/'professions/class-16-enemy/battle/frame_mapping.json'
HEX=['172638','4f4f7d','bbc1d6','dda77d','373e64','a394b1','77604f','77b8c7']
C=[tuple(bytes.fromhex(h))for h in HEX]
OLD=[tuple(bytes.fromhex(h))for h in ['172638','57577f','c2c5dc','dda77d','98718c']]
TABLE=dict(zip(OLD,[C[i]for i in [0,1,2,3,5]]));ASSETS=[];REG=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def save(im,relative,purpose):
 p=OUT/relative;p.parent.mkdir(parents=True,exist_ok=True)
 if im.mode=='RGBA':
  colors=sorted(set(im.getdata()));q=Image.new('P',im.size);q.putpalette([v for c in colors for v in c[:3]]+[0]*(768-len(colors)*3));lookup={c:i for i,c in enumerate(colors)};q.putdata([lookup[c]for c in im.getdata()]);q.info['transparency']=bytes(c[3]for c in colors);assert q.convert('RGBA').tobytes()==im.tobytes()
 else:q=im
 q.save(p,optimize=True);r={'path':'../../../'+p.relative_to(ROOT).as_posix(),'size':list(im.size),'bytes':p.stat().st_size,'sha256':sha(p),'purpose':purpose};ASSETS.append(r);return r
@lru_cache(maxsize=100000)
def material(rgb):return min(C,key=lambda c:sum((a-b)**2 for a,b in zip(rgb,c)))
def quant(im):
 q=Image.new('RGBA',im.size);q.putdata([(*material(p[:3]),255)if p[3]>=200 else(0,0,0,0)for p in im.getdata()]);return q
def remap(im):
 q=Image.new('RGBA',im.size);q.putdata([(*TABLE.get(p[:3],material(p[:3])),255)if p[3] else(0,0,0,0)for p in im.getdata()]);return q
def base_image(baseline,kind,i):
 scene=next(s for s in baseline['maps']['scenarios']if s['id']==kind)
 return remap(Image.open((MP.parent/scene['frame_mapping'][i]['path']).resolve()).convert('RGBA'))

def register(raw,spec,label):
 im=quant(raw.crop(spec['bounds']));scale=spec['scale'];dims=[round(im.width*scale),round(im.height*scale)];q=im.resize(dims,Image.Resampling.NEAREST);ratios=[dims[i]/im.size[i]for i in(0,1)]
 xy=[round(spec['target'][i]-spec['face'][i]*ratios[i])for i in(0,1)];out=Image.new('RGBA',tuple(spec['size']));out.alpha_composite(q,tuple(xy))
 count=lambda a:sum(p[3]>0 for p in a.getdata())
 assert count(out)==count(q),(label,'complete authored pose clipped')
 actual=[xy[i]+spec['face'][i]*ratios[i]for i in(0,1)]
 REG.append({**spec,'label':label,'source_sha256':sha(SRC/spec['source']),'translation':xy,'scaled_size':dims,'actual_face':actual,'clipped_pixels':0,'method':'uniform scale and integer registration; no joint warping'})
 return out

def staff_master():
 raw=Image.open(SRC/'staff-master.png').convert('RGBA').crop((380,20,671,1516));return quant(raw)
def equip(im,anchor,height,flip,label,angle=0):
 master=staff_master();r=height/master.height;weapon=master.resize((round(master.width*r),height),Image.Resampling.NEAREST)
 grip=[round(125*r),round(780*r)]
 if flip:weapon=ImageOps.mirror(weapon);grip[0]=weapon.width-1-grip[0]
 if angle:
  w,h=weapon.size;rotated=weapon.rotate(angle,Image.Resampling.NEAREST,expand=True);a=math.radians(angle);gx,gy=grip[0]-w/2,grip[1]-h/2
  grip=[round(math.cos(a)*gx+math.sin(a)*gy+rotated.width/2),round(-math.sin(a)*gx+math.cos(a)*gy+rotated.height/2)];weapon=rotated
 xy=[round(anchor[i]-grip[i])for i in(0,1)];layer=Image.new('RGBA',im.size);layer.alpha_composite(weapon,tuple(xy))
 assert sum(p[3]>0 for p in layer.getdata())==sum(p[3]>0 for p in weapon.getdata()),(label,'staff cropped')
 out=layer.copy();out.alpha_composite(im)
 # Upper staff is held in front; the lower shaft may naturally pass behind a robe/boot.
 upper=layer.crop((0,0,im.width,min(im.height,anchor[1]+3)));out.alpha_composite(upper,(0,0))
 # Authored source fingers occlude the grip: no invented or detached hand.
 for y in range(max(0,anchor[1]-4),min(im.height,anchor[1]+5)):
  for x in range(max(0,anchor[0]-5),min(im.width,anchor[0]+6)):
   p=im.getpixel((x,y))
   if p==(*C[3],255):out.putpixel((x,y),p)
 REG.append({'label':label,'weapon_source':'staff-master.png','height':height,'grip_anchor':anchor,'translation':xy,'mirror_x':flip,'rotation_degrees':angle,'clipped_pixels':0,'same_authored_weapon':True})
 return out
def hand_anchor(im,roi):
 pts=[(x,y)for y in range(roi[1],roi[3])for x in range(roi[0],roi[2])if im.getpixel((x,y))==(*C[3],255)]
 assert pts
 bottom=max(y for x,y in pts);pts=[p for p in pts if p[1]>=bottom-2]
 return [round(sum(x for x,y in pts)/len(pts)),round(sum(y for x,y in pts)/len(pts))]

def map_art(baseline):
 idle={i:base_image(baseline,'tactical-idle',i)for i in range(3)}
 # New staff hand gesture; keep original heads, waist/legs and robe phases.
 raw=Image.open(SRC/'maps-holding-master.png').convert('RGBA')
 spec={'source':'maps-holding-master.png','bounds':[177,75,374,464],'face':[55.62,108.41],'target':[55.31,29.75],'scale':(43.43-29.75)/(193.33-108.41),'size':[96,96]}
 holder=register(raw,spec,'map-idle-holding-arm')
 roi=[45,34,81,52]
 for i in idle:
  idle[i].paste(holder.crop(roi),roi[:2])
  idle[i]=equip(idle[i],[69,40],70,False,'idle-'+str(i))
 walk={i:base_image(baseline,'tactical-walk',i)for i in range(8)}
 # Existing native gait stays in its original slots. Each hand/staff pair is rigid.
 directions=[('up',[0,1],[44,56,55,70],True,12),('right',[2,3],[71,60,83,70],True,-12),('down',[4,5],[69,49,83,69],False,-12),('left',[6,7],[65,50,79,70],False,-12)]
 for name,ids,roi,flip,angle in directions:
  anchor=hand_anchor(walk[ids[0]],roi);height=min(64,round((96-anchor[1])/(1-780/1496)))
  for i in ids:walk[i]=equip(walk[i],anchor,height,flip,'walk-'+str(i),angle)
 return {'tactical-idle':{i:idle[j]for i,j in enumerate([0,1,2,1,0,1])},'tactical-walk':walk}

def battle_art():
 raw=Image.open(SRC/'battle-holding-master.png').convert('RGBA')
 specs=[([220,119,514,672],[82.5,125.5]),([740,89,1358,671],[184.5,147.5]),([1537,104,2012,671],[260.5,140])]
 result={}
 for i,(bounds,face)in enumerate(specs):
  height=bounds[3]-bounds[1];spec={'source':'battle-holding-master.png','bounds':bounds,'face':face,'target':[129,150],'scale':106/(height-face[1]),'size':[320,256]}
  result[i]=register(raw,spec,'battle-'+str(i))
 return result

def boards(maps,battle):
 entries=[('待机 '+str(i),maps['tactical-idle'][i])for i in range(3)]+[(d+' '+str(i),maps['tactical-walk'][i])for i,d in enumerate(['上','上','右','右','下','下','左','左'])]
 for light in[False,True]:
  bg=(220,222,216)if light else(32,45,53);fg=(23,38,56)if light else(235,243,242)
  for kind,items,cols,cw,ch in [('maps',entries,4,300,270),('battle',[(str(i)+' · '+['站立','举臂蓄力','伸臂释放'][i],battle[i])for i in range(3)],3,400,315)]:
   canvas=Image.new('RGB',(cols*cw,54+math.ceil(len(items)/cols)*ch),bg);draw=ImageDraw.Draw(canvas);draw.text((canvas.width//2,25),'隙行术师 · '+('地图姿势'if kind=='maps'else'战斗姿势'),anchor='mm',font=font(20),fill=fg)
   for n,(label,im)in enumerate(items):
    if kind=='maps':im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
    x=n%cols*cw+(cw-im.width)//2;y=54+n//cols*ch;canvas.paste(im,(x,y),im);draw.text((n%cols*cw+cw//2,y+ch-18),label,anchor='mm',font=font(16),fill=fg)
   save(canvas,kind+'-'+('light'if light else'dark')+'.png','full pose review')
  canvas=Image.new('RGB',(1152,1200),bg);draw=ImageDraw.Draw(canvas)
  groups=[('待机',[maps['tactical-idle'][i]for i in[0,1,2,1]])]+[(name,[maps['tactical-walk'][i]for i in[a,a+1,a,a+1]])for name,a in[('向上',0),('向右',2),('向下',4),('向左',6)]]
  for row,(name,ims)in enumerate(groups):
   draw.text((15,15+row*240),name,font=font(15),fill=fg)
   for col,im in enumerate(ims):
    im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST);canvas.paste(im,(col*288+(288-im.width)//2,35+row*240),im)
  save(canvas,'map-loops-'+('light'if light else'dark')+'.png','consecutive native phases, fixed centers and staff grip')

def main(publish=False):
 baseline=read_baseline(OUT/'baseline.json');maps=map_art(baseline);battle=battle_art();m=copy.deepcopy(baseline['maps']);bm=copy.deepcopy(baseline['battle'])
 note='隙行术师持弯曲木柄、龙形环首与蓝色晶石魔杖。蓝紫少色、纯色头发与哑光衣料；地图固定头颈腰胯，原步态、循环及节奏保留。前手依原作蓄力／释放，后手握杖；原法术程序与结算保持。'
 for mapping in[m,bm]:mapping.update(display_name='敌方隙行术师',display_class_name='隙行术师',revision=REV,review_note=note,palette=HEX,status='review_candidate',runtime_integrated=False)
 for scene in m['scenarios']:
  kind=scene['id'];w,h=scene['output_frame_size'];atlas=Image.new('RGBA',(len(maps[kind])*w,h));rows=[]
  for i,im in maps[kind].items():
   rec=save(im,kind+f'/frame-{i:03}.png','native map pose with authored staff');row=copy.deepcopy(scene['frame_mapping'][i]);row.update(path=rec['path'],output_path=rec['path'],size=rec['size'],bytes=rec['bytes'],sha256=rec['sha256']);rows.append(row);atlas.alpha_composite(im,(i*w,0))
  scene.update(frame_mapping=rows,output_atlas=save(atlas,kind+'-atlas.png','native slot order')['path'],revision=REV,display_name='敌方隙行术师',review_note=note,motion_review={'revision':REV,'native_gait_body_reused':True,'fixed_hand_staff_per_direction':True,'whole_body_offset_added':[0,0],'native_timing_modified':False})
 atlas=Image.new('RGBA',(960,256));paths={}
 for i,im in battle.items():paths[str(i)]=save(im,f'battle/frame-{i:03}.png','enemy16 complete native casting gesture and staff')['path'];atlas.alpha_composite(im,(i*320,0))
 bm.update(frame_mapping=paths,output_atlas=save(atlas,'battle-atlas.png','native battle pose order')['path'],batches=[{'id':'隙行术师三姿势','review':'../../../'+REV+'/battle-light.png','status':'review_candidate'}],qa_report='../../../'+REV+'/checks.json')
 boards(maps,battle)
 drafts={'maps':m,'battle':bm};write(OUT/'mapping-drafts.json',drafts);write(OUT/'asset-manifest.json',{'revision':REV,'palette':HEX,'assets':ASSETS,'registration':REG,'source_staff_sha256':sha(SRC/'staff-master.png'),'runtime_integrated':False,'user_visual_acceptance':'pending'})
 if publish:write(MP,m);write(BP,bm);write(MP.parent.parent/'manifest.json',{'id':'class-16-enemy','revision':REV,'status':'review_candidate','runtime_integrated':False,'maps_mapping':'maps/frame_mapping.json','battle_mapping':'battle/frame_mapping.json','review_record':'../../'+REV+'/README.md'})
 print(json.dumps({'staged':True,'published':publish,'assets':len(ASSETS),'maps':14,'battle':3}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');a=p.parse_args();main(a.publish)
