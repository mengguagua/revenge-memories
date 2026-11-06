#!/usr/bin/env python3
"""Freeze heroine identity, reusable class11 poses, and native personal-map sources."""
import json,math,shutil,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
from build_gallery import ROOT,file_hash
from export_gallery import font

REV='eileen-identity-complete-v1-20261023'
OUT=ROOT/REV
SRC=OUT/'source'
def write(path,value):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def make_sheet(images,path,cols=3,cell=(400,360),labels=None):
 q=Image.new('RGBA',(cols*cell[0],math.ceil(len(images)/cols)*cell[1]));dr=ImageDraw.Draw(q)
 for n,im in enumerate(images):
  im=im.convert('RGBA');scale=min((cell[0]-40)/im.width,(cell[1]-40)/im.height)
  im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST)
  x=n%cols*cell[0]+(cell[0]-im.width)//2;y=n//cols*cell[1]+(cell[1]-im.height)//2;q.alpha_composite(im,(x,y))
  if labels:dr.text((n%cols*cell[0]+cell[0]//2,(n//cols+1)*cell[1]-12),str(labels[n]),anchor='mm',font=font(16),fill=(160,178,189))
 q.save(path,optimize=True)
def main():
 SRC.mkdir(parents=True,exist_ok=True)
 data=json.loads((ROOT/'demos/gallery-data.json').read_text())
 profile=next(p for p in data['profiles']if p['id']=='professions-class-11-ally-battle')
 actions=[a for a in data['actions']if a['profile']==profile['id']]
 maps=json.loads((ROOT/'professions/class-11-ally/maps/frame_mapping.json').read_text())
 bm=json.loads((ROOT/profile['mapping']).read_text())
 source_timeline=json.loads((ROOT/profile['mapping']).parent.joinpath(bm['review_timeline']).resolve().read_text())
 # Shared effect definitions remain owned by their existing class mappings.
 source_timeline['effects']={}
 if not(OUT/'baseline.json').exists():
  write(OUT/'baseline.json',{'digests':{a['id']:a['contentDigest']for a in data['actions']},'profile':profile,'actions':actions,'maps':maps,'battle_mapping':bm,'review_timeline':source_timeline,'effects':data['effects']})
 groups={}
 for i,path in sorted(profile['newFrames'].items(),key=lambda p:int(p[0])):
  im=Image.open(ROOT/path).convert('RGBA');groups.setdefault(hashlib.sha256(im.tobytes()).hexdigest(),[]).append(int(i))
 ids=[g[0]for g in groups.values()];batches=[ids[i:i+12]for i in range(0,len(ids),12)]
 for n,batch in enumerate(batches):
  ims=[]
  for i in batch:
   im=Image.open(ROOT/profile['newFrames'][str(i)]).convert('RGBA');ims.append(im.crop(im.getbbox()))
  make_sheet(ims,SRC/f'battle-target-{n:02}.png',3,(420,360),batch)
 for i,path in profile['newFrames'].items():shutil.copyfile(ROOT/path,SRC/f'base-battle-{int(i):03}.png')
 for s in maps['scenarios']:
  for row in s['frame_mapping']:
   path=(ROOT/'professions/class-11-ally/maps'/row['path']).resolve();shutil.copyfile(path,SRC/f"base-{s['id']}-{row['source_index']:03}.png")
 idle=[Image.open(SRC/f'base-tactical-idle-{i:03}.png')for i in range(3)]
 walk=[Image.open(SRC/f'base-tactical-walk-{i:03}.png')for i in [0,1,2,3,4,5]]
 make_sheet([im.crop(im.getbbox())for im in idle+walk],SRC/'map-target.png',3,(320,300),['idle0','idle1','idle2','up0','up1','right0','right1','down0','down1'])
 portraits=[]
 for name in ['eileen_departure','eileen_chart','eileen_present']:
  p=ROOT.parents[1]/f'actual/assets/portraits-0.7.2/{name}.png';shutil.copyfile(p,SRC/(name+'.png'));portraits.append(Image.open(p))
 make_sheet(portraits,SRC/'portrait-reference.png',3,(288,288))
 personal=ROOT/'source-input/legacy-assets/assets/original/graphics/map_units/personal_02.png'
 shutil.copyfile(personal,SRC/'original-personal-map.png')
 atlas=Image.open(personal).convert('RGBA');make_sheet([atlas.crop((i*32,0,(i+1)*32,24))for i in range(6)],SRC/'story-target.png',3,(320,240),['front0','front1','back0','back1','right0','right1'])
 write(OUT/'source-audit.json',{'revision':REV,'native_class':11,'character_id':2,'hero_profession':'light_guide','battle_groups':list(groups.values()),'battle_batches':batches,'native_program_keys':[a['key']for a in actions if a['kind']=='attack'],'portrait_sources':[{'path':str((SRC/(n+'.png')).relative_to(ROOT)),'sha256':file_hash(SRC/(n+'.png'))}for n in ['eileen_departure','eileen_chart','eileen_present']],'personal_map_sha256':file_hash(personal),'world_reuses_story':True,'runtime_integrated':False})
 print(json.dumps({'unique_battle_poses':len(ids),'batches':batches,'source_actions':len(actions)}),flush=True)
if __name__=='__main__':main()
