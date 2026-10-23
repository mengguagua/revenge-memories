#!/usr/bin/env python3
"""Local ImageGen anatomy patches, leaving approved foreground pixels fixed."""
import argparse,copy,json
from pathlib import Path
from PIL import Image,ImageDraw
from build_gallery import ROOT,file_hash
from import_pegasus_knight_complete import C,map_anchor
from export_gallery import font
import import_sniper_complete as io
REV='pegasus-forelegs-wing-sync-v2-20261023'
OUT=ROOT/REV
OLD=ROOT/'pegasus-knight-complete-v1-20261023'
io.OUT=OUT

def write(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def quant(im):
 q=Image.new('RGBA',im.size)
 q.putdata([(*min(C,key=lambda c:sum((a-b)**2 for a,b in zip(c,p[:3]))),255)if p[3]>=128 else(0,0,0,0)for p in im.getdata()]);return q

def load(kind,i):return Image.open(OLD/f'ally/{kind}/frame-{i:03}.png').convert('RGBA')
def board(idle,walk):
 for light in[False,True]:
  q=Image.new('RGB',(1000,620),(220,222,216)if light else(32,45,53));d=ImageDraw.Draw(q);fg=(23,38,56)if light else(235,239,239)
  d.text((500,25),'天马骑士 · 前腿补全与双翼同步',anchor='mm',font=font(22),fill=fg)
  for n,(label,im)in enumerate([(f'待机 {i}',idle[i])for i in range(3)]+[(f'向下 {i}',walk[i])for i in[4,5]]):
   x=n%3*330;y=60+n//3*280;s=2;up=im.resize((im.width*s,im.height*s),Image.Resampling.NEAREST);q.paste(up,(x+(330-up.width)//2,y),up);d.text((x+165,y+225),label,anchor='mm',font=font(19),fill=fg)
  io.save(q,'review-'+('light'if light else'dark')+'.png','local anatomy inspection, three idle poses and two synchronized down-wing phases')

def patch(publish=False):
 gen=quant(Image.open(OUT/'source/idle-legs-master.png').convert('RGBA').resize((288,96),Image.Resampling.NEAREST))
 idle={i:load('tactical-idle',i)for i in range(6)};walk={i:load('tactical-walk',i)for i in range(8)};checks=[]
 # Masks select only the newly drawn leg from each ImageGen cell. Existing
 # foreground is composited over the patch, keeping every original pixel.
 specs=[((40,59,49,79),(0,0)),((26,54,38,72),(3,0)),((25,54,36,72),(3,0))]
 for i,(box,delta)in enumerate(specs):
  before=idle[i];part=Image.new('RGBA',before.size);crop=gen.crop((i*96+box[0],box[1],i*96+box[2],box[3]));part.alpha_composite(crop,(box[0]+delta[0],box[1]+delta[1]));part.alpha_composite(before);idle[i]=part
  added=[(x,y)for y in range(96)for x in range(96)if not before.getpixel((x,y))[3]and part.getpixel((x,y))[3]]
  assert len(added)>20 and all(before.getpixel((x,y))==part.getpixel((x,y))for y in range(96)for x in range(96)if before.getpixel((x,y))[3])
  checks.append({'kind':'tactical-idle','frame':i,'added_leg_pixels':len(added),'patch_mask':box,'registration_translation':delta,'all_original_opaque_pixels_preserved':True,'head_anchor':map_anchor(part)})
 for i,j in[(3,1),(4,0),(5,1)]:idle[i]=idle[j].copy()
 before=walk[4];wing=quant(Image.open(OUT/'source/down-wing-master.png').convert('RGBA').resize((128,96),Image.Resampling.NEAREST));q=before.copy()
 # The outer wing is behind the x49..51 spear. Remove the entire old lowered
 # wing before inserting the raised wing, so no third wing can remain.
 box=(28,16,49,49);q.paste((0,0,0,0),box);crop=wing.crop((28,16,49,42));q.alpha_composite(crop,(28,17));walk[4]=q
 for y in range(96):
  for x in range(128):
   if not(box[0]<=x<box[2]and box[1]<=y<box[3]):assert before.getpixel((x,y))==q.getpixel((x,y))
 assert map_anchor(q)==map_anchor(before)
 assert q.crop((0,88,128,96)).tobytes()==before.crop((0,88,128,96)).tobytes()
 checks.append({'kind':'tactical-walk','frame':4,'patch_mask':box,'raised_wing_translation':[0,1],'rider_horse_spear_right_wing_projection_unchanged':True,'head_anchor':map_anchor(q),'two_wings_in_same_up_phase':True})
 for kind,poses,ids in [('tactical-idle',idle,range(6)),('tactical-walk',walk,[4])]:
  for i in ids:io.save(poses[i],f'ally/{kind}/frame-{i:03}.png','ImageGen missing foreleg / raised-wing patch; original foreground and center retained')
 board(idle,walk)
 if publish:
  m=copy.deepcopy(json.loads((OUT/'baseline.json').read_text())['maps']);note='待机补全另一只前腿和独立蹄子；向下移动双翼同时抬起、同时放下。骑手、马身、长枪、投影和原作循环节奏保持。'
  m.update(revision=REV,status='review_candidate',review_note=note,art_mode='local ImageGen anatomy patches composited behind original foreground; five accepted matte colors',qa_report='../../../'+REV+'/verification.json')
  for scene in m['scenarios']:
   kind=scene['id'];poses=idle if kind=='tactical-idle'else walk;ids=range(6)if kind=='tactical-idle'else[4];atlas=Image.new('RGBA',(len(poses)*next(iter(poses.values())).width,96))
   for f in scene['frame_mapping']:
    i=f['source_index'];atlas.alpha_composite(poses[i],(i*poses[i].width,0))
    if i in ids:
     p=OUT/f'ally/{kind}/frame-{i:03}.png';path='../../../'+p.relative_to(ROOT).as_posix();f.update(path=path,output_path=path,revision=REV,bytes=p.stat().st_size,sha256=file_hash(p))
   scene.update(revision=REV,status='review_candidate',review_note=note,output_atlas=io.save(atlas,f'ally/{kind}-atlas.png','existing slot order with local anatomy repairs'),review_status='pending_user_visual_acceptance')
   scene['output_atlas_bytes']=(OUT/f'ally/{kind}-atlas.png').stat().st_size
  write(ROOT/'professions/class-3-ally/maps/frame_mapping.json',m)
  write(OUT/'mapping-draft.json',m)
 write(OUT/'patch-registration.json',{'revision':REV,'palette':[c.hex()for c in map(bytes,C)],'checks':checks,'unchanged_down_return_phase':5,'enemy_deferred':True,'runtime_integrated':False})
 write(OUT/'asset-manifest.json',{'revision':REV,'assets':io.ASSETS})
 print(json.dumps({'revision':REV,'patched_slots':7,'published':publish}),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');a=p.parse_args();patch(a.publish)
