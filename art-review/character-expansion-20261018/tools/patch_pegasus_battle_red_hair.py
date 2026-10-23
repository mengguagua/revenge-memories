#!/usr/bin/env python3
"""Repair material labels of all native-registered Pegasus battle heads."""
import argparse,colorsys,copy,json
from PIL import Image,ImageDraw
from build_gallery import ROOT,file_hash
from export_gallery import font
from import_pegasus_knight_complete import C,matte
import import_sniper_complete as io
REV='pegasus-battle-red-hair-v3-20261023';OUT=ROOT/REV;OLD=ROOT/'pegasus-knight-complete-v1-20261023';io.OUT=OUT
# Hand-reviewed head and face regions in the existing 320x384 registration.
# These identify materials on the original raster; no silhouettes are redrawn.
SPEC={
0:([173,127,213,156],[178,138,188,150]),
1:([155,129,205,159],[163,141,175,153]),
2:([155,127,223,163],[163,141,176,154]),
3:([158,142,197,169],[165,154,176,165]),
4:([149,147,214,180],[158,160,171,174]),
5:([156,126,206,155],[163,138,176,152]),
6:([173,127,213,156],[178,138,188,150]),
7:([174,127,215,157],[179,139,190,151]),
16:([173,127,213,156],[178,138,188,150]),
33:([173,127,213,156],[178,138,188,150]),
34:([173,126,214,156],[179,137,189,149]),
35:([174,126,216,156],[180,137,191,150])}

def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def inside(x,y,b):return b[0]<=x<b[2]and b[1]<=y<b[3]
def make(publish=False):
 base=json.loads((OUT/'baseline.json').read_text());mapping=copy.deepcopy(base['battle']);native=json.loads((OLD/'baseline.json').read_text())['ally_battle'];poses={};records=[]
 for i,(head,face)in SPEC.items():
  current=Image.open((ROOT/'professions/class-3-ally/battle'/mapping['frame_mapping'][str(i)]).resolve()).convert('RGBA');source=Image.open((ROOT/'professions/class-3-ally/battle'/native['frame_mapping'][str(i)]).resolve()).convert('RGBA');q=current.copy();hair_pixels=[];changed=[];skin=[];false_hair=[]
  candidate=[]
  for yy in range(head[1],head[3]):
   for xx in range(head[0],head[2]):
    rr,gg,bb,aa=source.getpixel((xx,yy));hh,ss,vv=colorsys.rgb_to_hsv(rr/255,gg/255,bb/255)
    if aa>=128 and (hh<.10 or hh>.97)and ss>.30 and vv>.21 and rr>1.35*gg and rr>1.45*bb:candidate.append((xx,yy))
  hair_mask=set(p for comp in io.helper.parts(candidate)if min(y for x,y in comp)<=face[1]+7 for p in comp)
  for y in range(q.height):
   for x in range(q.width):
    old=current.getpixel((x,y));p=source.getpixel((x,y));r,g,b=p[:3];h,s,v=colorsys.rgb_to_hsv(r/255,g/255,b/255)
    if not old[3]:continue
    value=old[:3]
    # The previous generic red-cluster detector selected the belt for slot3.
    if old[:3]==C[4]:value=matte(p[:3],False,False)
    if old[:3]==C[4]and not inside(x,y,head):false_hair.append((x,y))
    if inside(x,y,head):
     warm=(h<.12 or h>.97)and s>.30 and v>.22 and r>1.18*g and r>1.38*b
     face_skin=inside(x,y,face)and warm and r>130 and g>65 and b>30
     if face_skin:value=C[3];skin.append((x,y))
     elif (x,y)in hair_mask:value=C[4];hair_pixels.append((x,y))
    if value!=old[:3]:q.putpixel((x,y),(*value,old[3]));changed.append((x,y))
  assert hair_pixels and changed
  assert q.getchannel('A').tobytes()==current.getchannel('A').tobytes()
  assert all(inside(x,y,head)or(x,y)in false_hair for x,y in changed)
  poses[i]=q;path=io.save(q,f'ally/battle/frame-{i:03}.png','existing pixel geometry; complete matte red hair, preserved face and navy contours')
  records.append({'source_frame':i,'head_region':head,'protected_face_region':face,'hair_pixels':len(hair_pixels),'skin_pixels':len(skin),'incorrect_nonhair_red_pixels_removed':len(false_hair),'changed_pixels':len(changed),'alpha_geometry_unchanged':True,'path':path,'size':list(q.size),'bytes':(OUT/f'ally/battle/frame-{i:03}.png').stat().st_size,'sha256':file_hash(OUT/f'ally/battle/frame-{i:03}.png')})
 order=sorted(poses);atlas=Image.new('RGBA',(len(order)*320,384))
 for n,i in enumerate(order):atlas.alpha_composite(poses[i],(n*320,0))
 atlaspath=io.save(atlas,'ally/battle-atlas.png','all required native battle slots, corrected red hair')
 for light in[False,True]:
  board=Image.new('RGB',(1520,1376),(220,222,216)if light else(32,45,53));d=ImageDraw.Draw(board);fg=(23,38,56)if light else(235,239,239);d.text((760,25),'天马骑士 · 战斗红发修正',anchor='mm',font=font(22),fill=fg)
  for n,i in enumerate(order):
   x=n%4*380+30;y=56+n//4*440;board.paste(poses[i],(x,y),poses[i]);d.text((x+160,y+405),f'源姿势 {i}',anchor='mm',font=font(19),fill=fg)
  io.save(board,'review-'+('light'if light else'dark')+'.png','all battle hair phases, dark/light edge and face inspection')
 write(OUT/'material-registration.json',{'revision':REV,'palette':[bytes(c).hex()for c in C],'frames':records,'hair_material':'single matte muted coral b96369','motion_or_alpha_changes':False})
 if publish:
  note='天马骑士战斗全部源姿势统一纯色柔和红发，修正漏染的头顶、鬓发和马尾；保留肤色／眼睛、原轮廓与动作，纠正源姿势3误染红色的腰带。'
  mapping.update(revision=REV,status='review_candidate',review_note=note,art_mode='existing ImageGen geometry, explicit head/face material regions replace generic warm-cluster detection',frame_mapping={str(a['source_frame']):a['path']for a in records},records=[{k:a[k]for k in['source_frame','path','size','bytes','sha256']}for a in records],output_atlas=atlaspath,output_atlas_bytes=(OUT/'ally/battle-atlas.png').stat().st_size,qa_report='../../../'+REV+'/verification.json',batches=[{'id':'战斗全帧红发修正','review':'../../../'+REV+'/review-light.png','status':'review_candidate'}])
  write(ROOT/'professions/class-3-ally/battle/frame_mapping.json',mapping);write(OUT/'mapping-draft.json',mapping)
 write(OUT/'asset-manifest.json',{'revision':REV,'assets':io.ASSETS});print(json.dumps({'slots':len(poses),'publish':publish}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');a=p.parse_args();make(a.publish)
