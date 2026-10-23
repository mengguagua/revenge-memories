#!/usr/bin/env python3
"""Freeze own class5 native references and prior review state."""
import json,math,shutil
from PIL import Image,ImageDraw
from build_gallery import ROOT,file_hash
from export_gallery import font
REV='falcon-knight-complete-v1-20261023';OUT=ROOT/REV;SRC=OUT/'source'
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def board(items,name,columns=4,scale=1):
 cw,ch=(420,600)if scale==1 else(340,300);q=Image.new('RGB',(cw*columns,56+ch*math.ceil(len(items)/columns)),(220,222,216));d=ImageDraw.Draw(q);d.text((q.width//2,24),name,anchor='mm',font=font(22),fill=(23,38,56))
 for n,(label,im)in enumerate(items):
  im=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST);x=n%columns*cw+(cw-im.width)//2;y=56+n//columns*ch;q.paste(im,(x,y),im);d.text((n%columns*cw+cw//2,y+im.height+22),label,anchor='mm',font=font(17),fill=(23,38,56))
 q.save(SRC/name,optimize=True)
def main():
 SRC.mkdir(parents=True,exist_ok=True);p=ROOT/'professions/class-5-ally';maps=json.loads((p/'maps/frame_mapping.json').read_text());battle=json.loads((p/'battle/frame_mapping.json').read_text());full=json.loads((ROOT/'source-input/original-motion/full-original-motion.json').read_text());full['variants'].update(json.loads((ROOT/'source-input/corrected-ally-motion/overlay.json').read_text())['variants']);variants={k:v for k,v in full['variants'].items()if str(v['source_class_id'])=='5'};body=full['original_bodies']['5']
 if not(OUT/'baseline.json').exists():write(OUT/'baseline.json',{'gallery':json.loads((ROOT/'demos/gallery-data.json').read_text()),'maps':maps,'battle':battle,'body':body,'variants':variants})
 assets=[]
 for kind,path,size,ids in [('idle',p/'reference/class-5-idle-source-atlas.png',(24,24),range(6)),('walk',ROOT/'source-input/corrected-tactical-walk/class-5-ally.png',(32,24),range(8)),('battle',ROOT/'source-input/original-motion/class-5.png',(96,136),sorted(map(int,battle['frame_mapping'])))]:
  im=Image.open(path).convert('RGBA');cols=im.width//size[0];items=[]
  for i in ids:
   frame=im.crop((i%cols*size[0],i//cols*size[1],i%cols*size[0]+size[0],i//cols*size[1]+size[1]));frame.save(SRC/f'native-{kind}-{i:03}.png',optimize=True);items.append((f'{kind} {i}',frame.resize((size[0]*4,size[1]*4),Image.Resampling.NEAREST)))
  board(items,'native-'+kind+'-guide.png',4,1 if kind=='battle'else 2);assets.append({'kind':kind,'path':str(path.relative_to(ROOT)),'sha256':file_hash(path),'size':list(im.size),'slots':list(ids)})
 items=[]
 for scene in maps['scenarios']:
  for f in scene['frame_mapping'][:(3 if scene['id']=='tactical-idle'else 8)]:items.append((scene['id']+str(f['source_index']),Image.open((p/'maps'/f['output_path']).resolve()).convert('RGBA')))
 board(items,'existing-map-art.png',4,2)
 board([(f'battle {i}',Image.open((p/'battle'/battle['frame_mapping'][str(i)]).resolve()).convert('RGBA'))for i in[0,1,2,3,4,5,6,7,49,50]],'existing-battle-art.png')
 timelines=[]
 for key,v in variants.items():
  runs=[]
  for tick,f in enumerate(v['frames']):
   if not runs or runs[-1]['frame']!=f['frame']:runs.append({'frame':f['frame'],'start':tick,'ticks':1})
   else:runs[-1]['ticks']+=1
  timelines.append({'key':key,'ticks':len(v['frames']),'fps':v['native_fps'],'contact':v['contact_tick'],'contact_count':v['contact_count'],'origin':v['actor_origin'],'program':v['source_program_address'],'runs':runs})
 write(OUT/'native-reference-audit.json',{'assets':assets,'timelines':timelines,'class_id':5,'ally_only':True,'no_new_class_effects':True})
 shutil.copy2('/var/folders/r8/8zr_7l9x51g8gym_ptjpzfx40000gp/T/codex-clipboard-e46f95b5-2dd6-4da0-9142-2777ad023800.png',SRC/'weapon-reference.png')
 print(json.dumps({'native_assets':len(assets),'attack_programs':len(timelines),'battle_slots':sorted(map(int,battle['frame_mapping']))}),flush=True)
if __name__=='__main__':main()
