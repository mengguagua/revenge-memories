#!/usr/bin/env python3
"""Register four edited recovery poses with the sword continuously in front."""
from baseline_json import read_baseline
import argparse,copy,json,math,os
from PIL import Image,ImageDraw
from build_gallery import ROOT,file_hash
from export_gallery import font
from import_eileen_complete import C,NAVY,SKIN,INDIGO,HAIR,IVORY,BRASS,box,center
from import_eileen_promoted_battle_v4 import landmarks
from import_knight_redraw_v3 import parts
import import_sniper_complete as io
REV='eileen-front-sword-v5-20261024';OUT=ROOT/REV;SRC=OUT/'source';MAPPING=ROOT/'eileen-promoted/battle/frame_mapping.json'
POINTS={30:[149,54],31:[147.5,51.5],11:[148.5,53],23:[152,53.5]}
GRIPS={30:[120.5,131],31:[120,128],11:[125,132.5],23:[131.5,151.5]}

def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')

def main(publish=False):
 io.OUT=OUT;b=read_baseline(OUT/'baseline.json');m=copy.deepcopy(b['mapping']);poses={int(i):Image.open((MAPPING.parent/path).resolve()).convert('RGBA')for i,path in m['frame_mapping'].items()};reg=[]
 # Reuse the accepted, already drawn forward hand/guard/blade as a layer.
 # This keeps blade length, width, navy contour and grip identical across
 # the landing edits; no new vector blade is drawn in the delivered art.
 source=Image.open(SRC/'before-029.png').convert('RGBA');selection=Image.new('L',source.size);ImageDraw.Draw(selection).polygon([(159,166),(173,165),(181,174),(180,185),(171,190),(116,226),(114,221),(158,178)],fill=255);weapon=Image.new('RGBA',source.size)
 for y in range(source.height):
  for x in range(source.width):
   if selection.getpixel((x,y)):weapon.putpixel((x,y),source.getpixel((x,y)))
 io.save(weapon,'layers/front-hand-sword.png','accepted pose29 silver blade, contour, guard and gripping hand reused as one registered layer')
 for i,point in POINTS.items():
  im=Image.open(SRC/f'edited-{i:03}.png').convert('RGBA');fb,hh,skull=landmarks(im,point)
  # Quantized peach reflections below the knee belong to the dark boots,
  # not skin; leave both carrying and relaxed hands untouched.
  for y in range(im.height):
   for x in range(im.width):
    c=im.getpixel((x,y))
    if y>point[1]+125 and c in [(*SKIN,255),(*HAIR,255)]:im.putpixel((x,y),(*INDIGO,255))
    elif fb[0]<=x<fb[2]and fb[1]<=y<fb[3]and c==(*IVORY,255):im.putpixel((x,y),(*BRASS,255))
  scale=30/hh;dims=[round(v*scale)for v in im.size];target=[188 if i in [30,31]else 192,144];floor=poses[i].getbbox()[3];at=[round(target[0]-point[0]*dims[0]/im.width),floor-dims[1]]
  small=im.resize(dims,Image.Resampling.NEAREST);q=Image.new('RGBA',(320,288));q.alpha_composite(small,tuple(at));assert sum(c[3]>0 for c in q.getdata())==sum(c[3]>0 for c in small.getdata());assert q.getbbox()[3]==floor
  grip=[at[j]+GRIPS[i][j]*dims[j]/im.size[j]for j in range(2)];clear=Image.new('L',q.size);polygon=[(-140,110),(-140,80),(-27,-13),(8,-11),(21,32),(-6,45)];polygon=[(round(grip[0]+x*dims[0]/im.width),round(grip[1]+y*dims[1]/im.height))for x,y in polygon];ImageDraw.Draw(clear).polygon(polygon,fill=255);q.paste((0,0,0,0),(0,0),clear)
  shift=[round(grip[j]-[174,177][j])for j in range(2)];layer=Image.new('RGBA',q.size);layer.alpha_composite(weapon,tuple(shift));q.alpha_composite(layer);io.save(layer,f'layers/front-hand-sword-{i:03}.png','identical existing forward sword and grip registered to edited leading wrist')
  debris=[g for g in parts((x,y)for y in range(q.height)for x in range(q.width)if q.getpixel((x,y))[3])if len(g)<3]
  for g in debris:
   for xy in g:q.putpixel(xy,(0,0,0,0))
  poses[i]=q;io.save(q,f'battle/frame-{i:03}.png','complete edited landing/recovery pose; single low front sword pointing down-left')
  reg.append({'slot':i,'source':f'edited-{i:03}.png','source_sha256':file_hash(SRC/f'edited-{i:03}.png'),'source_size':list(im.size),'source_face':point,'source_head_height':hh,'target_head_height':30,'scale':scale,'dimensions':dims,'translation':at,'registered_face':[at[j]+point[j]*dims[j]/im.size[j]for j in range(2)],'preserved_floor':floor,'clipped_pixels':0,'whole_body':True,'front_grip':grip,'weapon_layer_shift':shift,'weapon_source_grip':[174,177],'weapon_source_slot':29})
 atlas=Image.new('RGBA',(320*len(poses),288));order=sorted(poses)
 for n,i in enumerate(order):atlas.alpha_composite(poses[i],(n*320,0))
 io.save(atlas,'battle-atlas.png','complete current promoted battle atlas')
 for light in [False,True]:
  bg=(220,222,216)if light else(32,45,53);fg=NAVY if light else(235,243,242);q=Image.new('RGB',(1440,330*math.ceil(len(order)/4)),bg);dr=ImageDraw.Draw(q)
  for n,i in enumerate(order):
   x=n%4*360+20;y=n//4*330;q.paste(poses[i],(x,y),poses[i]);dr.text((n%4*360+180,y+306),str(i),anchor='mm',font=font(18),fill=fg)
  q.save(OUT/f'battle-current-{"light"if light else"dark"}.png',optimize=True)
  seq=[29,30,31,11,23,1,0];q=Image.new('RGB',(360*len(seq),330),bg);dr=ImageDraw.Draw(q)
  for n,i in enumerate(seq):q.paste(poses[i],(n*360+20,0),poses[i]);dr.text((n*360+180,306),str(i),anchor='mm',font=font(18),fill=fg)
  q.save(OUT/f'front-carry-sequence-{"light"if light else"dark"}.png',optimize=True)
 m.update(revision=REV,review_note='保留已校准空中体型与完整蹲地姿势；修正后跳落地30／31及回位11／23的持剑方向，剑与握剑手连续保持在身前低位、剑尖指向左下，再平顺接回待机。原312帧、位移、唯一第129帧结算及全部法术特效保持。',qa_report=os.path.relpath(OUT/'verification.json',MAPPING.parent),output_atlas=os.path.relpath(OUT/'battle-atlas.png',MAPPING.parent),output_atlas_order=order,batches=[{'id':'落地到待机连续身前持剑','review':os.path.relpath(OUT/'front-carry-sequence-light.png',MAPPING.parent),'status':'review_candidate'}])
 for i in POINTS:m['frame_mapping'][str(i)]=os.path.relpath(OUT/f'battle/frame-{i:03}.png',MAPPING.parent)
 write(OUT/'mapping-draft.json',m);write(OUT/'asset-manifest.json',{'revision':REV,'changed_slots':list(POINTS),'registrations':reg,'assets':io.ASSETS,'source_master_sha256':file_hash(SRC/'edit-master.png'),'native_timeline_unchanged':True,'runtime_integrated':False})
 if publish:write(MAPPING,m)
 print(json.dumps({'published':publish,'registrations':reg}),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');main(p.parse_args().publish)
