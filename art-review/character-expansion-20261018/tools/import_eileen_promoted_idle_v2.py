#!/usr/bin/env python3
"""One intact clean promoted idle body with a shoulder-pivot arm/sword layer."""
import argparse,copy,json,math,os
from PIL import Image,ImageDraw
from build_gallery import ROOT,file_hash,relative
from export_gallery import font
from import_eileen_complete import quant,face,box,C,NAVY,SKIN,HAIR,IVORY,BRASS,INDIGO
from import_knight_redraw_v3 import parts
import import_sniper_complete as io
REV='eileen-promoted-idle-v2-20261024';OUT=ROOT/REV;SRC=OUT/'source';MAPPING=ROOT/'eileen-promoted/maps/frame_mapping.json';io.OUT=OUT

def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def extract():
 raw=quant(Image.open(SRC/'idle-layers-master.png').convert('RGBA'));groups=[g for g in parts((x,y)for y in range(raw.height)for x in range(raw.width)if raw.getpixel((x,y))[3])if len(g)>1000];assert len(groups)==2;groups.sort(key=lambda g:box(g)[0]);out=[]
 for g in groups:
  b=box(g);q=Image.new('RGBA',(b[2]-b[0],b[3]-b[1]))
  for x,y in g:q.putpixel((x-b[0],y-b[1]),raw.getpixel((x,y)))
  out.append((q,{'source_bounds':b,'source_sha256':file_hash(SRC/'idle-layers-master.png')}))
 return out

def main(publish=False):
 body_fig,arm_fig=extract();body,body_meta=body_fig;arm,arm_meta=arm_fig;fp,fb=face(body)
 # Resolve the generator's light eye material to the existing muted amber
 # palette entry. This is a semantic palette assignment, not a new eye shape.
 eye_material_pixels=0
 for y in range(fb[1],fb[3]):
  for x in range(fb[0],fb[2]):
   if body.getpixel((x,y))==(*IVORY,255):body.putpixel((x,y),(*BRASS,255));eye_material_pixels+=1
 body_meta['light_eye_material_to_amber_pixels']=eye_material_pixels
 scale=(80-34)/(body.height-fp[1]);size=[round(v*scale)for v in body.size];at=[round([43,34][j]-fp[j]*size[j]/body.size[j])for j in range(2)]
 fixed=Image.new('RGBA',(96,96));fixed.alpha_composite(body.resize(size,Image.Resampling.NEAREST),tuple(at));assert fixed.getbbox()[3]==80;io.save(fixed,'layers/body.png','one full clean head, face, torso, calves and boots, constant in every idle frame')
 # Rotate the complete generated weapon arm around the sleeve/shoulder
 # attachment; no facial/leg crops or overlapping body silhouettes.
 pivot=[149,299];target=[37,42];angles=[14,4,-8];phases=[];regs=[]
 for n,angle in enumerate(angles):
  theta=math.radians(angle);co=math.cos(theta);si=math.sin(theta);s=scale
  inverse=(co/s,-si/s,pivot[0]-co*target[0]/s+si*target[1]/s,si/s,co/s,pivot[1]-si*target[0]/s-co*target[1]/s)
  layer=arm.transform((96,96),Image.Transform.AFFINE,inverse,resample=Image.Resampling.NEAREST);q=layer.copy();q.alpha_composite(fixed);phases.append(q);io.save(layer,f'layers/arm-sword-{n}.png','complete held sword and bent arm rotating together around fixed shoulder');regs.append({'phase':n,'angle_degrees':angle,'source_shoulder':pivot,'target_shoulder':target,'scale':s,'arm_bounds':layer.getbbox()})
 slots=[0,1,2,1,0,1];poses={i:phases[j]for i,j in enumerate(slots)}
 for i,im in poses.items():io.save(im,f'tactical-idle/frame-{i:03}.png','clean promoted idle; one fixed whole body and rigid hand/sword phase')
 atlas=Image.new('RGBA',(96*6,96))
 for i,im in poses.items():atlas.alpha_composite(im,(i*96,0))
 io.save(atlas,'tactical-idle-atlas.png','all six native slots, using three canonical arm phases')
 for light in [False,True]:
  bg=(220,222,216)if light else(32,45,53);fg=NAVY if light else(235,243,242);q=Image.new('RGB',(960,460),bg);dr=ImageDraw.Draw(q);dr.text((480,28),'引光剑使 · 清晰头脸与固定身体',anchor='mm',font=font(22),fill=fg)
  for n,im in enumerate(phases):
   im=im.resize((288,288),Image.Resampling.NEAREST);q.paste(im,(n*320+16,75),im);dr.text((n*320+160,406),'待机姿势 '+str(n),anchor='mm',font=font(18),fill=fg)
  q.save(OUT/f'poses-{"light" if light else "dark"}.png',optimize=True)
 b=json.loads((OUT/'baseline.json').read_text());m=copy.deepcopy(b['mapping']);sc=next(sc for sc in m['scenarios']if sc['id']=='tactical-idle');note='引光剑使待机：统一完整头部、清楚的眼睛和纯色红发，清理脸部散乱白点；双小腿与靴子使用连续靛蓝深色块。固定身体基准，持剑臂与银白长剑绕肩部共同运动，原0／1／2／1循环、节奏和阴影保持。'
 sc.update(revision=REV,review_note=note,motion_review=os.path.relpath(OUT/'README.md',MAPPING.parent),output_atlas=os.path.relpath(OUT/'tactical-idle-atlas.png',MAPPING.parent))
 for row in sc['frame_mapping']:
  p=OUT/f'tactical-idle/frame-{row["source_index"]:03}.png';row.update(path=os.path.relpath(p,MAPPING.parent),output_path=os.path.relpath(p,MAPPING.parent),bytes=p.stat().st_size,sha256=file_hash(p))
 write(OUT/'mapping-draft.json',m);write(OUT/'asset-manifest.json',{'revision':REV,'assets':io.ASSETS,'body':{**body_meta,'source_face':fp,'source_face_box':fb,'scale':scale,'dimensions':size,'translation':at,'target_face':[43,34],'floor':80},'arm':{**arm_meta,'registrations':regs},'source_slot_phases':slots,'fixed_complete_body':True,'runtime_integrated':False})
 if publish:write(MAPPING,m)
 print(json.dumps({'published':publish,'body_scale':scale,'body_bounds':fixed.getbbox(),'arm_phases':regs}),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');main(p.parse_args().publish)
