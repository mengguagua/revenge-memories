# -*- coding: utf-8 -*-
"""Focused source/layout/art checks for this isolated sol batch. No game launch."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,sys,subprocess
R=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(R/'tools'))
from export_gallery import font
read=lambda p:json.loads(p.read_text())
data=read(R/'demos/gallery-data.json');profiles={p['id']:p for p in data['profiles']};sources=[];images={};titles=[]
for cid in[2,5,7,9]:
 P=R/f'professions/class-{cid}-ally';bm=read(P/'battle/frame_mapping.json')
 for f,rel in bm['frame_mapping'].items():
  p=(P/'battle'/rel).resolve();im=Image.open(p).convert('RGBA');assert list(im.size)==bm['output_frame_size'];assert im.getbbox();images[str(p.relative_to(R))]={'purpose':'battle','size':list(im.size),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 mm=read(P/'maps/frame_mapping.json')
 for s in mm['scenarios']:
  p=(P/'maps'/s['source_atlas']).resolve();im=Image.open(p).convert('RGBA');native=(R/f'source-input/corrected-tactical-walk/class-{cid}-ally.png')if s['id']=='tactical-walk'else(R/f'source-input/legacy-assets/assets/original/graphics/map_units/class_{cid}_ally.png');ref=Image.open(native).convert('RGBA');same=im.size==ref.size and im.tobytes()==ref.tobytes();expected=[v*(8 if s['id']=='tactical-walk'else 6)if i==0 else v for i,v in enumerate(s['source_frame_size'])];assert list(im.size)==expected and same,(cid,s['id'],'wrong native source');sources.append({'unit':cid,'context':s['id'],'path':str(p.relative_to(R)),'pixels':list(im.size),'matches_own_frozen_source_rgba':same})
  assert set(r['source_index']for r in s['frame_mapping'])==set(range(8 if s['id']=='tactical-walk'else 6))
  for r in s['frame_mapping']:
   p=(P/'maps'/r['path']).resolve();im=Image.open(p).convert('RGBA');assert list(im.size)==s['output_frame_size'];assert im.getbbox();images[str(p.relative_to(R))]={'purpose':s['id'],'size':list(im.size),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
for a in data['actions']:
 if a.get('revision')!='sol':continue
 assert a['ready'];p=profiles[a['profile']];view=a.get('viewport',data['viewport']);panelw=round(view[2]*4);w=panelw*2+72;w+=w%2;draw=ImageDraw.Draw(Image.new('RGB',(w,96)));text=p['actorName']+' · '+a['name'];chosen=next(n for n in range(22,13,-1)if draw.textbbox((0,0),text,font=font(n))[2]<=w-48);b=draw.textbbox((0,0),text,font=font(chosen));left=(w-(b[2]-b[0]))/2;assert left>=24 and 14+b[3]<48;assert all(draw.textbbox((0,0),v,font=font(15))[2]<panelw-24 for v in['原作','四倍像素重绘']);titles.append({'action':a['id'],'canvas_width':w,'font_size':chosen,'title_glyph_width':b[2]-b[0],'minimum_horizontal_padding':left,'title_glyph_bottom':14+b[3],'next_label_row':48,'pass':True})
previous=read(R/'sol/baseline-sha256.json');changed=[s for s,h in previous.items()if hashlib.sha256((R/s).read_bytes()).hexdigest()!=h];assert not changed
actual=subprocess.run(['git','diff','--name-only','--','actual','core','data','assets','scenes','tests','project.godot'],capture_output=True,text=True,check=True).stdout.splitlines();assert not actual,actual
for v in images.values():
 if v['bytes']>50000:v['quality_reason']='Keep required4x feather/metal/outline detail; PNG optimize lossless, soft50KB reference exceeded with visible-quality priority.'
report={'revision':'sol','pass':True,'complete_units':['class-2-ally','class-5-ally','class-7-ally','class-9-ally'],'whole_requested_scope_complete':False,'source_atlases_checked':sources,'delivered_individual_images_checked':len(images),'image_inventory':images,'titles_checked':len(titles),'title_checks':titles,'previous_packaged_pngs_checked':len(previous),'previous_packaged_pngs_changed':changed,'game_files_modified':actual,'browser_playback':'not performed; original environment access limitation honored','visual_review':'Source/new light/dark individual sheets and rendered representative stills inspected separately; structure does not imply user acceptance.'}
(R/'sol/verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('sol batch:',len(sources),'native atlases,',len(images),'individual PNGs,',len(titles),'text layouts; previous',len(previous),'PNGs unchanged')
