#!/usr/bin/env python3
"""Correct intact battle sprites: anatomical head registration, never lower-body splices."""
import argparse,copy,json,math,os
from PIL import Image,ImageDraw
from build_gallery import ROOT,file_hash
from export_gallery import font
import import_eileen_complete as old
from import_eileen_complete import C,HEX,NAVY,INDIGO,IVORY,SKIN,HAIR,ICE,box,center
from import_knight_redraw_v3 import parts
import import_sniper_complete as io
REV='eileen-side-battle-v3-20261024';OUT=ROOT/REV;SRC=OUT/'source';io.OUT=OUT;REG=[]
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def sheet(name,rows):
 q=old.quant(Image.open(SRC/name).convert('RGBA'));gs=[g for g in parts((x,y)for y in range(q.height)for x in range(q.width)if q.getpixel((x,y))[3])if len(g)>1000];assert len(gs)==sum(rows),(name,len(gs))
 gs.sort(key=lambda g:center(box(g))[1]);order=[];s=0
 for n in rows:order+=sorted(gs[s:s+n],key=lambda g:center(box(g))[0]);s+=n
 result=[]
 for n,g in enumerate(order):
  b=box(g);im=Image.new('RGBA',(b[2]-b[0],b[3]-b[1]))
  for x,y in g:im.putpixel((x-b[0],y-b[1]),q.getpixel((x,y)))
  result.append((im,{'source':name,'cell':n,'source_visible_bounds':b,'source_sha256':file_hash(SRC/name)}))
 return result

def save(im,name,purpose):io.save(im,name,purpose);return OUT/name

def head_registration(fig,point,head_height,target,label):
 im,meta=fig;scale=31/head_height;dims=[round(x*scale)for x in im.size];small=im.resize(dims,Image.Resampling.NEAREST);at=[round(target[j]-point[j]*dims[j]/im.size[j])for j in range(2)]
 assert at[0]>=0 and at[1]>=0 and at[0]+dims[0]<=320 and at[1]+dims[1]<=288,(label,dims,at)
 out=Image.new('RGBA',(320,288));out.alpha_composite(small,tuple(at))
 # Both Eileen costumes use trousers. Palette correction excludes the face,
 # hands, and forearms by classifying only isolated skin below the pelvis.
 for g in parts((x,y)for y in range(out.height)for x in range(out.width)if out.getpixel((x,y))==(*SKIN,255)):
  b=box(g)
  if len(g)>=45 and center(b)[1]>target[1]+35 and b[3]-b[1]>6:
   for xy in g:out.putpixel(xy,(*INDIGO,255))
 for g in parts((x,y)for y in range(out.height)for x in range(out.width)if out.getpixel((x,y))[3])[1:]:
  if len(g)<=8:
   for xy in g:out.putpixel(xy,(0,0,0,0))
 REG.append({**meta,'label':label,'face_landmark':point,'anatomical_head_height':head_height,'target_head_height':31,'uniform_scale':scale,'dimensions':dims,'translation':at,'target_face':target,'clipped_pixels':0,'whole_unspliced_pose':True,'body_patch_count':0})
 return out

def selected_face(im,point):
 cs=[g for g in parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))==(*SKIN,255))if len(g)>12]
 g=min(cs,key=lambda g:sum((center(box(g))[j]-point[j])**2 for j in range(2)));return center(box(g)),box(g)

def body_landmark(im,i):
 rough={2:[68,132],3:[67,130],4:[66,134],5:[63,133],6:[70,129],7:[70,127],8:[87,147],9:[78,136],10:[72,137]}
 point,fb=selected_face(im,rough[i])if i in rough else old.face(im)
 # A local skull window excludes the braid, sword, and lifted arm. Record
 # the physical face and chin; the external hair envelope never sets scale.
 radius=(fb[2]-fb[0])*1.8
 main_hair=set(max(parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))==(*HAIR,255)),key=len))
 ys=[y for y in range(max(0,int(fb[1]-radius*1.5)),fb[1])for x in range(max(0,int(point[0]-radius)),min(im.width,int(point[0]+radius)))if(x,y)in main_hair]
 top=min(ys)if ys else fb[1]-20
 return point,fb[3]-top,{'face_box':fb,'skull_crown_y':top,'method':'local skull crown to chin; separate from raised hand and braid'}

def map_art():
 raw=sheet('side-master.png',[2]);result={};meta=[]
 # Register a shared crown/waist baseline and common scale for both drawn
 # gait phases; stride is joint rotation, never limb stretching.
 for im,m in raw:
  hair=max(parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))==(*HAIR,255)),key=len);top=min(y for x,y in hair);b=box([(x,y)for x,y in hair if y<top+im.height*.06]);m['crown']=[(b[0]+b[2])/2,top]
 scale=min(65/(im.height-m['crown'][1])for im,m in raw)
 for n,(im,m)in enumerate(raw):
  dims=[round(v*scale)for v in im.size];at=[round(66-m['crown'][0]*dims[0]/im.width),round(30-m['crown'][1]*dims[1]/im.height)];q=Image.new('RGBA',(128,96));small=im.resize(dims,Image.Resampling.NEAREST)
  assert at[0]>=0 and at[1]>=0 and at[0]+dims[0]<=128 and at[1]+dims[1]<=96;q.alpha_composite(small,tuple(at));result[2+n]=q
  meta.append({**m,'label':'map right '+str(n),'uniform_group_scale':scale,'translation':at,'size':dims,'clipped_pixels':0})
 result[6]=result[2].transpose(Image.Transpose.FLIP_LEFT_RIGHT);result[7]=result[3].transpose(Image.Transpose.FLIP_LEFT_RIGHT)
 return result,meta

def battle_art():
 audit=json.loads((ROOT/'eileen-identity-complete-v1-20261023/source-audit.json').read_text());raw={};out={};measurements={}
 for n,ids in enumerate(audit['battle_batches'][:3]):raw.update(zip(ids,old.figures(f'base-battle-{n:02}-master.png',3,4)))
 # Preserve accepted casting and standing frames exactly; only the physical
 # jump/slash/landing/recovery sequence and raised sword frame are repaired.
 b=json.loads((OUT/'baseline.json').read_text())['battle']
 for key,path in b['frame_mapping'].items():out[int(key)]=Image.open((ROOT/'eileen/battle'/path).resolve()).convert('RGBA')
 changed=list(range(2,11))+list(range(12,23))+[25,26,27,28,98]
 for i in changed:
  if i in[12,13,14,15]:continue
  im,m=raw[i];pt,height,detail=body_landmark(im,i);measurements[i]={**detail,'source_face':pt,'head_height':height}
  out[i]=head_registration((im,m),pt,height,[v*4 for v in old.native_face(i)],'battle '+str(i))
 # Four genuinely redrawn upward-braid poses. Landmark measurements refer to
 # the compact skull near the face, not the raised red braid behind it.
 hairs=sheet('hair-rise-master.png',[2,2]);global_head=[([273,292],96),([894,292],96),([263,917],96),([874,906],96)]
 for i,fig,(gpt,height)in zip([12,13,14,15],hairs,global_head):
  im,m=fig;b=m['source_visible_bounds'];pt=[gpt[0]-b[0],gpt[1]-b[1]];target_native={12:[47.5,20],13:[45,28],14:[45,44],15:[45.5,45]}[i];measurements[i]={'manual_anatomical_face':pt,'head_height':height,'braid_excluded_from_scale':True,'native_face_component_center':target_native,'native_face_source':'warm skin component: 12 [44,17,51,23], 13 [43,25,47,31], 14 [43,41,47,47], 15 [42,42,49,48]'};out[i]=head_registration(fig,pt,height,[v*4 for v in target_native],'battle '+str(i))
 # Keep the original single slash arc exactly; it is not another actor/hit.
 out[19].alpha_composite(Image.open(ROOT/'spellsword-complete-v1-20261023/original-slash-arc.png').convert('RGBA'))
 write(OUT/'head-measurements.json',measurements)
 return out,changed

def boards(walk,battle,changed):
 for light in[False,True]:
  entries=[('侧走 '+str(i),q)for i,q in walk.items()]+[('战斗 '+str(i),battle[i])for i in sorted(set(changed)|{0,1,11,23,24,29})]
  cw,ch=360,330;q=Image.new('RGB',(cw*4,42+ch*math.ceil(len(entries)/4)),(220,222,216)if light else(32,45,53));dr=ImageDraw.Draw(q);fg=NAVY if light else(235,243,242)
  dr.text((q.width//2,20),'艾琳 · 持剑侧走与完整战斗帧校准',anchor='mm',font=font(20),fill=fg)
  for n,(label,im)in enumerate(entries):
   if im.height<100:im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
   x=n%4*cw+(cw-im.width)//2;y=42+n//4*ch;q.paste(im,(x,y),im);dr.text((n%4*cw+cw//2,y+309),label,anchor='mm',font=font(16),fill=fg)
  save(q,'poses-'+('light'if light else'dark')+'.png','offline pose QA, centered captions inside padded cells')

def main(publish=False):
 base=json.loads((OUT/'baseline.json').read_text());walk,mapreg=map_art();battle,changed=battle_art();m=copy.deepcopy(base['maps']);bm=copy.deepcopy(base['battle'])
 for s in m['scenarios']:
  if s['id']!='tactical-walk':continue
  s.update(revision=REV,review_note='侧走握剑前臂和剑身置于身前且可见，腿长、粗细按同一骨架保持；保留上／下行已验收修正、原步态节奏和持续阴影。',motion_review=os.path.relpath(OUT/'README.md',ROOT/'eileen/maps'))
  ims={}
  for f in s['frame_mapping']:
   i=f['source_index']
   if i in walk:
    p=save(walk[i],f'map/frame-{i:03}.png','whole drawn side walk, no leg-length stretch');f.update(path=os.path.relpath(p,ROOT/'eileen/maps'),output_path=os.path.relpath(p,ROOT/'eileen/maps'),bytes=p.stat().st_size,sha256=file_hash(p))
   ims[i]=Image.open((ROOT/'eileen/maps'/f['path']).resolve()).convert('RGBA')
  atlas=Image.new('RGBA',(128*8,96))
  for i,im in ims.items():atlas.alpha_composite(im,(i*128,0))
  p=save(atlas,'map-atlas.png','all native tactical slots; accepted up/down unchanged');s['output_atlas']=os.path.relpath(p,ROOT/'eileen/maps')
 bm.update(revision=REV,palette=HEX,review_note='完整战斗画帧重新登记，取消固定高度下半身拼接以消除重影；以真实面部与头颅尺寸为缩放依据，排除持剑手与上扬辫子。保留原帧序、位移、结算、单次剑弧及法术特效。',qa_report=os.path.relpath(OUT/'verification.json',ROOT/'eileen/battle'))
 for i in changed:
  p=save(battle[i],f'battle/frame-{i:03}.png','complete pose normalized by anatomical skull, no body splice');bm['frame_mapping'][str(i)]=os.path.relpath(p,ROOT/'eileen/battle')
 order=sorted(battle);atlas=Image.new('RGBA',(320*len(order),288))
 for n,i in enumerate(order):atlas.alpha_composite(battle[i],(320*n,0))
 p=save(atlas,'battle-atlas.png','complete battle atlas with intact sprites');bm.update(output_atlas=os.path.relpath(p,ROOT/'eileen/battle'),output_atlas_order=order,batches=[{'id':'完整身体与头发上飘修正','review':os.path.relpath(OUT/'poses-light.png',ROOT/'eileen/battle'),'status':'review_candidate'}])
 boards(walk,battle,changed);write(OUT/'asset-manifest.json',{'revision':REV,'assets':io.ASSETS,'battle_registrations':REG,'map_registrations':mapreg,'changed_battle_slots':changed,'new_source_drawings':{'side':2,'hair_rise':4},'body_splice_count':0,'runtime_integrated':False});write(OUT/'map-draft.json',m);write(OUT/'battle-draft.json',bm)
 if publish:write(ROOT/'eileen/maps/frame_mapping.json',m);write(ROOT/'eileen/battle/frame_mapping.json',bm)
 print(json.dumps({'published':publish,'map_frames':len(walk),'battle_frames':len(changed),'head_measurements':json.loads((OUT/'head-measurements.json').read_text())}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');main(p.parse_args().publish)
