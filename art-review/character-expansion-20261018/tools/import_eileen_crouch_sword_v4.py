#!/usr/bin/env python3
"""One intact squat body, three separately drawn hair layers, restored retreat sword."""
import argparse,copy,json,math,os
from PIL import Image,ImageDraw
from build_gallery import ROOT,file_hash
from export_gallery import font
from import_eileen_complete import quant,face,box,center,HAIR,SKIN,NAVY,C
from import_knight_redraw_v3 import parts
import import_sniper_complete as io
REV='eileen-crouch-sword-v4-20261024';OUT=ROOT/REV;SRC=OUT/'source';io.OUT=OUT

def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def save(im,name,purpose):io.save(im,name,purpose);return OUT/name

def extract(name,expected):
 raw=quant(Image.open(SRC/name).convert('RGBA'));gs=[g for g in parts((x,y)for y in range(raw.height)for x in range(raw.width)if raw.getpixel((x,y))[3])if len(g)>1000];assert len(gs)==expected,(name,len(gs));gs.sort(key=lambda g:center(box(g))[1])
 if expected==4:gs=sorted(gs[:2],key=lambda g:center(box(g))[0])+sorted(gs[2:],key=lambda g:center(box(g))[0])
 out=[]
 for n,g in enumerate(gs):
  b=box(g);q=Image.new('RGBA',(b[2]-b[0],b[3]-b[1]))
  for x,y in g:q.putpixel((x-b[0],y-b[1]),raw.getpixel((x,y)))
  out.append((q,{'source':name,'part':n,'source_box':b,'sha256':file_hash(SRC/name)}))
 return out

def make():
 b=json.loads((OUT/'baseline.json').read_text());raw=extract('crouch-layers-master.png',4);im,meta=raw[0];fp,fb=face(im);scale=57/(im.height-fp[1]);dims=[round(v*scale)for v in im.size];at=[round(176-fp[0]*dims[0]/im.width),round(200-fp[1]*dims[1]/im.height)];body=Image.new('RGBA',(320,288));small=im.resize(dims,Image.Resampling.NEAREST);assert at[0]>=0 and at[1]>=0 and at[0]+dims[0]<=320 and at[1]+dims[1]<=288;body.alpha_composite(small,tuple(at))
 hair=max(parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))==(*HAIR,255)),key=len);right=max(x for x,y in hair);rootband=[(x,y)for x,y in hair if x>right-10];root=[right-20,sum(y for x,y in rootband)/len(rootband)];target=[at[j]+round(root[j]*dims[j]/im.size[j])for j in range(2)]
 save(body,'layers/canonical-body.png','one whole intact squat body, fixed hip knee ankle and support hands')
 hairscale=60/max(q.width for q,m in raw[1:]);layers=[];records=[]
 for n,(q,m)in enumerate(raw[1:]):
  pts=[(x,y)for y in range(q.height)for x in range(min(36,q.width))if q.getpixel((x,y))[3]];hp=[12,sum(y for x,y in pts)/len(pts)];sz=[round(v*hairscale)for v in q.size];small=q.resize(sz,Image.Resampling.NEAREST);loc=[round(target[j]-hp[j]*sz[j]/q.size[j])for j in range(2)];layer=Image.new('RGBA',(320,288));assert all(loc[j]>=0 and loc[j]+sz[j]<=layer.size[j]for j in range(2));layer.alpha_composite(small,tuple(loc));layers.append(layer);save(layer,f'layers/hair-{n}.png','generated braid-only layer behind intact squat body');records.append({**m,'root':hp,'target_root':target,'scale':hairscale,'dimensions':sz,'translation':loc})
 poses={};order={16:0,22:0,17:1,18:2,19:0}
 for i,phase in order.items():
  q=layers[phase].copy();q.alpha_composite(body)
  if i==19:q.alpha_composite(Image.open(ROOT/'spellsword-complete-v1-20261023/original-slash-arc.png').convert('RGBA'))
  poses[i]=q
 # Only add the missing weapon and closed hand. Every pre-existing retreat
 # body pixel outside the overlay remains byte-identical to the accepted frame.
 weapon,wmeta=extract('sword-hand-master.png',1)[0];weapon=weapon.rotate(14,resample=Image.Resampling.NEAREST,expand=True);wb=weapon.getbbox();weapon=weapon.crop(wb).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
 skin=max(parts((x,y)for y in range(weapon.height)for x in range(weapon.width)if weapon.getpixel((x,y))==(*SKIN,255)),key=len);grip=center(box(skin));pts=[(x,y)for y in range(weapon.height)for x in range(weapon.width)if weapon.getpixel((x,y))[3]];tip=max(pts,key=lambda p:p[0]+p[1]);length=math.dist(grip,tip);ss=76/length;sz=[round(v*ss)for v in weapon.size];small=weapon.resize(sz,Image.Resampling.NEAREST);loc=[round([236.5,190.0][j]-grip[j]*sz[j]/weapon.size[j])for j in range(2)];overlay=Image.new('RGBA',(320,288));assert all(loc[j]>=0 and loc[j]+sz[j]<=320 if j==0 else loc[j]>=0 and loc[j]+sz[j]<=288 for j in range(2));overlay.alpha_composite(small,tuple(loc));q=Image.open(SRC/'before-011.png').convert('RGBA');q.alpha_composite(overlay);poses[11]=q;save(overlay,'layers/retreat-sword-hand.png','single ice sword plus closed gripping hand; original retreat body preserved')
 for i,q in sorted(poses.items()):save(q,f'battle/frame-{i:03}.png','stable crouch body with braid motion'if i!=11 else'restored held sword, original body unchanged')
 m=copy.deepcopy(b['battle']);m.update(revision=REV,review_note='下蹲16／22／17／18／19使用同一个完整支撑姿势，仅松辫在身体后方摆动，避免大腿和膝盖跳变；后退11补齐冰蓝长剑与握剑手。原作节奏、位移和结算不变。',qa_report=os.path.relpath(OUT/'verification.json',ROOT/'eileen/battle'))
 for i in poses:m['frame_mapping'][str(i)]=os.path.relpath(OUT/f'battle/frame-{i:03}.png',ROOT/'eileen/battle')
 allposes={int(i):Image.open((ROOT/'eileen/battle'/path).resolve()).convert('RGBA')for i,path in m['frame_mapping'].items()};atlas=Image.new('RGBA',(320*len(allposes),288));order=sorted(allposes)
 for n,i in enumerate(order):atlas.alpha_composite(allposes[i],(n*320,0))
 p=save(atlas,'battle-atlas.png','complete current battle source slots');m.update(output_atlas=os.path.relpath(p,ROOT/'eileen/battle'),output_atlas_order=order,batches=[{'id':'下蹲支撑稳定与后退持剑','review':os.path.relpath(OUT/'poses-light.png',ROOT/'eileen/battle'),'status':'review_candidate'}])
 for light in[False,True]:
  q=Image.new('RGB',(1280,650),(220,222,216)if light else(32,45,53));dr=ImageDraw.Draw(q);fg=NAVY if light else(235,243,242)
  for n,i in enumerate([16,22,17,18,19,11]):
   x=n%4*320;y=n//4*325;q.paste(poses[i],(x,y),poses[i]);dr.text((x+160,y+304),'姿势 '+str(i),anchor='mm',font=font(17),fill=fg)
  save(q,'poses-'+('light'if light else'dark')+'.png','centered pose QA on light/dark background')
 write(OUT/'asset-manifest.json',{'revision':REV,'assets':io.ASSETS,'body_registration':{**meta,'face':fp,'face_box':fb,'scale':scale,'size':dims,'translation':at,'hair_join_root':target,'whole_body_layers':1},'hair_registrations':records,'weapon_registration':{**wmeta,'grip':grip,'tip':tip,'scale':ss,'rotation_degrees':14,'mirrored_for_rear_hand':True,'size':sz,'translation':loc,'target_grip':[236.5,190.0],'hand_to_tip_length':76},'crouch_body_shared_exact':True,'changed_slots':[11,16,17,18,19,22],'runtime_integrated':False});write(OUT/'mapping-draft.json',m);return m
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');a=p.parse_args();m=make()
 if a.publish:write(ROOT/'eileen/battle/frame_mapping.json',m)
 print(json.dumps({'published':a.publish,'slots':[11,16,17,18,19,22]}),flush=True)
