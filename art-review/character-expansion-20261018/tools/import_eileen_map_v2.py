#!/usr/bin/env python3
"""Narrow Eileen base-map correction from newly drawn anatomical walk poses.
No leg mirroring, fixed side upper-body patches, or combat/form changes.
"""
import argparse,copy,json,math,os,colorsys
from functools import lru_cache
from PIL import Image,ImageDraw,ImageFilter
from build_gallery import ROOT,file_hash
from export_gallery import font
from import_eileen_complete import C,HEX,NAVY,INDIGO,BLUE,IVORY,SKIN,MAGENTA,HAIR,BRASS,ICE,face,box,center
from import_knight_redraw_v3 import parts
import import_sniper_complete as io
REV='eileen-spellsword-map-v2-20261024';OUT=ROOT/REV;SRC=OUT/'source'
io.OUT=OUT;REG=[];ART=[]
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
@lru_cache(maxsize=100000)
def material(rgb):
 h,s,v=colorsys.rgb_to_hsv(*(x/255 for x in rgb))
 if s>.24 and(h<.045 or h>.965)and rgb[0]>rgb[1]*1.3:return HAIR
 return min(C,key=lambda c:sum((a-b)**2 for a,b in zip(c,rgb)))
def quant(raw):
 q=Image.new('RGBA',raw.size);q.putdata([(*material(p[:3]),255)if p[3]>=240 and not(p[2]>200 and p[0]<80 and p[1]<160)else(0,0,0,0)for p in raw.getdata()]);return q

def convex_hull(points):
 p=sorted(set(points))
 def cross(o,a,b):return(a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
 lower=[];upper=[]
 for a in p:
  while len(lower)>=2 and cross(lower[-2],lower[-1],a)<=0:lower.pop()
  lower.append(a)
 for a in reversed(p):
  while len(upper)>=2 and cross(upper[-2],upper[-1],a)<=0:upper.pop()
  upper.append(a)
 return lower[:-1]+upper[:-1]

def extract(name,row_counts,backs=()):
 raw=quant(Image.open(SRC/name).convert('RGBA'))
 groups=[g for g in parts((x,y)for y in range(raw.height)for x in range(raw.width)if raw.getpixel((x,y))[3])if len(g)>1000]
 assert len(groups)==sum(row_counts),(name,len(groups))
 groups.sort(key=lambda g:center(box(g))[1]);ordered=[];start=0
 for count in row_counts:
  ordered+=sorted(groups[start:start+count],key=lambda g:center(box(g))[0]);start+=count
 out=[]
 for n,g in enumerate(ordered):
  b=box(g);im=Image.new('RGBA',(b[2]-b[0],b[3]-b[1]))
  for x,y in g:im.putpixel((x-b[0],y-b[1]),raw.getpixel((x,y)))
  fb=None;white_pixels=0
  if n not in backs:
   fp,fb=face(im)
   skin=[xy for xy in[(x,y)for y in range(fb[1],fb[3])for x in range(fb[0],fb[2])]if im.getpixel(xy)==(*SKIN,255)]
   # Skin material palette normalization only: facial highlights are skin, not
   # the ivory cloth material. The original eye/line-art pixels are preserved.
   mask=Image.new('L',im.size);ImageDraw.Draw(mask).polygon(convex_hull(skin),fill=255)
   for y in range(fb[1],fb[3]):
    for x in range(fb[0],fb[2]):
     if mask.getpixel((x,y))and im.getpixel((x,y))[:3]in[IVORY,ICE]:im.putpixel((x,y),(*SKIN,255));white_pixels+=1
  else:
   hair=max(parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))==(*HAIR,255)),key=len)
   top=min(y for x,y in hair);hb=box([(x,y)for x,y in hair if y<top+im.height*.10]);fp=[(hb[0]+hb[2])/2,hb[1]+(hb[2]-hb[0])*.55]
  hair=max(parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))==(*HAIR,255)),key=len)
  crown_y=min(y for x,y in hair);crown_box=box([(x,y)for x,y in hair if y<crown_y+im.height*.075]);crown=[(crown_box[0]+crown_box[2])/2,crown_y]
  meta={'crown':crown,'source':name,'source_index':n,'source_bounds':b,'source_sha256':file_hash(SRC/name),'face':fp,'face_box':fb,'back_view':n in backs,'facial_highlights_normalized_to_skin':white_pixels}
  im.save(SRC/f'diagnostic-{name[:-4]}-{n:02}.png',optimize=True);out.append((im,meta))
 return out

def register_group(figures,ids,size,target,floor,label):
 scale=min(min((floor-target[1])/(im.height-m['crown'][1]),target[0]/m['crown'][0],(size[0]-target[0])/(im.width-m['crown'][0]),target[1]/max(1,m['crown'][1]))for im,m in figures)
 result={}
 for i,(im,meta)in zip(ids,figures):
  dims=[round(v*scale)for v in im.size];at=[round(target[j]-meta['crown'][j]*dims[j]/im.size[j])for j in range(2)];small=im.resize(dims,Image.Resampling.NEAREST);q=Image.new('RGBA',size)
  assert all(at[j]>=0 and at[j]+dims[j]<=size[j]for j in range(2)),(label,i,at,dims)
  q.alpha_composite(small,tuple(at));removed=0
  for g in parts((x,y)for y in range(q.height)for x in range(q.width)if q.getpixel((x,y))[3])[1:]:
   if len(g)<=5:
    for xy in g:q.putpixel(xy,(0,0,0,0));removed+=1
  transformed_face=[at[j]+meta['crown'][j]*dims[j]/im.size[j]for j in range(2)]
  REG.append({**meta,'kind':label,'index':i,'uniform_group_scale':scale,'dimensions':dims,'translation':at,'landmark':'hair crown, not a changing skin component','target_crown':target,'registered_crown':transformed_face,'clipped_pixels':0,'removed_resample_specks':removed,'whole_pose_generated':True,'leg_mirroring':False})
  result[i]=q
 return result

def asset(im,name,purpose):
 io.save(im,name,purpose);return OUT/name

def boards(poses):
 entries=[('剧情向下 · 右脚前',poses['story'][0]),('剧情向下 · 左脚前',poses['story'][1]),('剧情侧走 · 站直摆臂 / 后扫发',poses['story'][4]),('剧情侧走 · 跨步垂臂 / 垂发',poses['story'][5]),('战图待机 · 0',poses['tactical-idle'][0]),('战图待机 · 1',poses['tactical-idle'][1]),('战图待机 · 2',poses['tactical-idle'][2]),('战图上行 · 左脚前',poses['tactical-walk'][0]),('战图上行 · 右脚前',poses['tactical-walk'][1]),('战图下行 · 右脚前',poses['tactical-walk'][4]),('战图下行 · 左脚前',poses['tactical-walk'][5])]
 for light in[False,True]:
  cw,ch=350,270;q=Image.new('RGB',(cw*4,38+ch*3),(220,222,216)if light else(32,45,53));dr=ImageDraw.Draw(q);fg=NAVY if light else(235,243,242)
  dr.text((q.width//2,18),'艾琳 · 女魔剑士 · 地图姿势修正',anchor='mm',font=font(20),fill=fg)
  for n,(label,im)in enumerate(entries):
   display=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST);x=n%4*cw+(cw-display.width)//2;y=38+n//4*ch
   q.paste(display,(x,y),display);dr.text((n%4*cw+cw//2,y+230),label,anchor='mm',font=font(15),fill=fg)
  asset(q,'poses-'+('light'if light else'dark')+'.png','new map pose inspection, readable captions with measured padding')

def main(publish=False):
 baseline=json.loads((OUT/'baseline.json').read_text());m=copy.deepcopy(baseline['mapping']);story=extract('story-master-v2.png',[2,2]);tactical=extract('tactical-master-v2.png',[3,2,2],backs=[3,4])
 poses={}
 poses['story']=register_group(story[:2],[0,1],(128,96),[64,30],95,'story-down')
 poses['story'].update(register_group(story[2:],[4,5],(128,96),[59,30],95,'story-side'))
 idle=register_group(tactical[:3],[0,1,2],(96,96),[46,24],80,'tactical-idle')
 poses['tactical-idle']={i:idle[j].copy()for i,j in enumerate([0,1,2,1,0,1])}
 poses['tactical-walk']=register_group(tactical[3:5],[0,1],(128,96),[56,30],95,'tactical-up')
 poses['tactical-walk'].update(register_group(tactical[5:],[4,5],(128,96),[64,30],95,'tactical-down'))
 notes={'story':'重绘向下的前后交替步态；脸部象牙白高光按皮肤材质归色。侧走两相为站直摆臂且辫子后扫、跨步垂臂且辫子下垂。大地图精确共用剧情帧。','tactical-idle':'重绘露出眼睛的刘海和面部，持剑手臂随剑移动，保留原待机相位和双腿支撑。','tactical-walk':'上行双肩短披风与中央松辫，身前持剑手从背面被身体完全遮挡；下行前臂横过身前并握住剑柄。四方向持续阴影；上/下行是沿前后方向的左右脚交替。'}
 m.update(revision=REV,review_note='艾琳女魔剑士地图姿态与遮挡修正；引光剑使与战斗场景沿用前版。')
 for scenario in m['scenarios']:
  kind='story'if scenario['id']in['story','world']else scenario['id'];scenario.update(revision=REV,review_note=notes[kind],motion_review=os.path.relpath(OUT/'README.md',ROOT/'eileen/maps'))
  frames={}
  for f in scenario['frame_mapping']:
   i=f['source_index']
   if i in poses[kind]:
    p=asset(poses[kind][i],f'{kind}/frame-{i:03}.png','new whole-pose art, uniform registered native slot')
    f.update(path=os.path.relpath(p,ROOT/'eileen/maps'),output_path=os.path.relpath(p,ROOT/'eileen/maps'),bytes=p.stat().st_size,sha256=file_hash(p))
   frames[i]=Image.open((ROOT/'eileen/maps'/f['path']).resolve()).convert('RGBA')
  atlas=Image.new('RGBA',(frames[0].width*len(frames),frames[0].height))
  for n,i in enumerate(sorted(frames)):atlas.alpha_composite(frames[i],(n*frames[i].width,0))
  p=asset(atlas,f'{kind}-atlas.png','complete source-slot atlas including preserved unmodified directions');scenario['output_atlas']=os.path.relpath(p,ROOT/'eileen/maps')
 boards(poses)
 write(OUT/'asset-manifest.json',{'revision':REV,'assets':io.ASSETS,'registrations':REG,'palette':HEX,'native_timing_unchanged':True,'new_anatomical_leg_poses':True,'lower_body_mirrored':False,'world_reuses_story':True,'runtime_integrated':False})
 write(OUT/'mapping-draft.json',m)
 if publish:write(ROOT/'eileen/maps/frame_mapping.json',m)
 print(json.dumps({'published':publish,'unique_new_drawn_poses':11,'new_slot_images':14,'assets':len(io.ASSETS),'registrations':REG},ensure_ascii=False),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');main(p.parse_args().publish)
