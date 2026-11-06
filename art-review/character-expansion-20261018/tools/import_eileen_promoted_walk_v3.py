#!/usr/bin/env python3
"""Three continuous coat bodies, true depth-step leg pairs, and mirrored side art."""
import argparse,copy,json,math,os
from PIL import Image,ImageDraw
from build_gallery import ROOT,file_hash
from export_gallery import font
from import_eileen_complete import quant,box,face,C,NAVY,INDIGO,HAIR,IVORY,BRASS,SKIN
from import_knight_redraw_v3 import parts
import import_sniper_complete as io
REV='eileen-promoted-walk-v3-20261024';OUT=ROOT/REV;SRC=OUT/'source';MAPPING=ROOT/'eileen-promoted/maps/frame_mapping.json';io.OUT=OUT

def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')

def extract(name):
 raw=quant(Image.open(SRC/f'{name}-master.png').convert('RGBA'));groups=[g for g in parts((x,y)for y in range(raw.height)for x in range(raw.width)if raw.getpixel((x,y))[3])if len(g)>1000];assert len(groups)==3,(name,len(groups));groups.sort(key=lambda g:box(g)[0]);out=[]
 for g in groups:
  b=box(g);q=Image.new('RGBA',(b[2]-b[0],b[3]-b[1]))
  for x,y in g:q.putpixel((x-b[0],y-b[1]),raw.getpixel((x,y)))
  out.append((q,{'source_bounds':b,'source_sha256':file_hash(SRC/f'{name}-master.png')}))
 return out

def place(im,scale,source_anchor,target):
 size=[round(v*scale)for v in im.size];at=[round(target[j]-source_anchor[j]*size[j]/im.size[j])for j in range(2)];small=im.resize(size,Image.Resampling.NEAREST);q=Image.new('RGBA',(128,96));assert all(at[j]>=0 and at[j]+size[j]<=q.size[j]for j in range(2)),(at,size);q.alpha_composite(small,tuple(at));return q,{'scale':scale,'dimensions':size,'translation':at,'source_anchor':source_anchor,'target_anchor':target,'clipped_pixels':0}

def make(publish=False):
 configs={'up':{'waist_global':[527,426],'slots':[0,1]},'down':{'waist_global':[501,440],'slots':[4,5]},'side':{'waist_global':[498,463],'slots':[2,3]}};poses={};registrations={};occlusion={}
 for name,conf in configs.items():
  figs=extract(name);body,bmeta=figs[0];b=bmeta['source_bounds'];waist=[conf['waist_global'][j]-b[j]for j in range(2)];hair=[(x,y)for y in range(body.height)for x in range(body.width)if body.getpixel((x,y))==(*HAIR,255)];crown=min(y for x,y in hair)
  # Classify light eye pixels as muted amber during palette registration.
  if name!='up':
   fp,fb=face(body)
   for y in range(fb[1],fb[3]):
    for x in range(fb[0],fb[2]):
     if body.getpixel((x,y))==(*IVORY,255):body.putpixel((x,y),(*BRASS,255))
   bmeta['source_face_box']=fb;bmeta['source_face']=fp
  leg_length=max(im.height for im,meta in figs[1:]);scale=62/(waist[1]-crown+leg_length);target=[64,33+(waist[1]-crown)*scale];fixed,reg=place(body,scale,waist,target);io.save(fixed,f'layers/{name}-body.png','one uninterrupted coat/head/weapon body, fully in front of the leg roots')
  legs=[];lregs=[]
  for phase,(im,lmeta)in enumerate(figs[1:]):
   band=[(x,y)for y in range(min(20,im.height))for x in range(im.width)if im.getpixel((x,y))[3]];bb=box(band);anchor=[(bb[0]+bb[2])/2,0];layer,lr=place(im,scale,anchor,target);legs.append(layer);lregs.append({**lmeta,**lr});io.save(layer,f'layers/{name}-legs-{phase}.png','true forward/back or passing/stride leg pair beneath the whole coat');q=layer.copy();q.alpha_composite(fixed);poses[conf['slots'][phase]]=q
  registrations[name]={'body':{**bmeta,**reg,'source_crown_y':crown,'source_waist':waist},'legs':lregs,'source_common_scale':scale,'target_crown_y':33,'target_waist':target,'feet_max_y':max(q.getbbox()[3]for q in legs),'coat_layers':1,'body_splits':0}
  if name=='up':
   # The only visible skin near the upper head is the tiny ear; weapon hand
   # and forearm are genuinely hidden in the generated rear body artwork.
   occlusion={'source_holding_arm':'behind head and torso, not drawn on rear silhouette','only_exposed_sword_blade_above_shoulder':True}
 poses[6]=poses[2].transpose(Image.Transpose.FLIP_LEFT_RIGHT);poses[7]=poses[3].transpose(Image.Transpose.FLIP_LEFT_RIGHT)
 for i,q in sorted(poses.items()):io.save(q,f'tactical-walk/frame-{i:03}.png','whole continuous coat over articulated walking legs; hidden back holding arm or readable lower front carry')
 atlas=Image.new('RGBA',(128*8,96))
 for i,q in poses.items():atlas.alpha_composite(q,(i*128,0))
 io.save(atlas,'tactical-walk-atlas.png','all four directions and two native phases')
 for light in [False,True]:
  bg=(220,222,216)if light else(32,45,53);fg=NAVY if light else(235,243,242);q=Image.new('RGB',(1200,560),bg);dr=ImageDraw.Draw(q)
  for n,i in enumerate([0,1,4,5,2,3,6,7]):
   im=poses[i].resize((256,192),Image.Resampling.NEAREST);x=n%4*300+22;y=n//4*280+15;q.paste(im,(x,y),im);dr.text((n%4*300+150,n//4*280+245),{0:'上行 A',1:'上行 B',4:'下行 A',5:'下行 B',2:'右行 · 并腿',3:'右行 · 跨步',6:'左行 · 并腿',7:'左行 · 跨步'}[i],anchor='mm',font=font(18),fill=fg)
  q.save(OUT/f'poses-{"light"if light else"dark"}.png',optimize=True)
 b=json.loads((OUT/'baseline.json').read_text());m=copy.deepcopy(b['mapping']);sc=next(s for s in m['scenarios']if s['id']=='tactical-walk');note='引光剑使四向行走：上行持剑臂在身前，被头和身体遮住，仅露肩后剑刃；下行两腿在各自窄通道前后交替，不横移、不翻转衣摆；左右行走持剑前臂、肘和握剑手露在胸前，握柄降低到下胸。完整连续长衣覆盖独立关节腿层，保持同一中心、原节奏及持续阴影。'
 sc.update(revision=REV,review_note=note,motion_review=os.path.relpath(OUT/'README.md',MAPPING.parent),output_atlas=os.path.relpath(OUT/'tactical-walk-atlas.png',MAPPING.parent))
 for row in sc['frame_mapping']:
  p=OUT/f'tactical-walk/frame-{row["source_index"]:03}.png';row.update(path=os.path.relpath(p,MAPPING.parent),output_path=os.path.relpath(p,MAPPING.parent),bytes=p.stat().st_size,sha256=file_hash(p))
 write(OUT/'asset-manifest.json',{'revision':REV,'assets':io.ASSETS,'registrations':registrations,'rear_occlusion':occlusion,'all_leg_pairs_behind_one_whole_coat':True,'base_eileen_and_promoted_idle_not_modified':True,'runtime_integrated':False});write(OUT/'mapping-draft.json',m)
 if publish:write(MAPPING,m)
 print(json.dumps({'published':publish,'directions':list(registrations),'registrations':registrations}),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');make(p.parse_args().publish)
