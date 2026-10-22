#!/usr/bin/env python3
"""Prepare generated winter rock cutouts at their existing native canvas size.

Only transparent padding, alpha cleanup and proportional export are performed;
the winter stone/snow painting is from the recorded imagegen edits.
"""
from pathlib import Path
from PIL import Image, ImageDraw
import json, shutil, hashlib
R=Path(__file__).resolve().parents[1]
S=R/'source/chapter1-climate-20261022/nature'
D=R/'assets/chapter1-climate-20261022/nature'
O=R/'reports/chapter1-climate-20261022/grain-prison'
S.mkdir(parents=True,exist_ok=True);D.mkdir(parents=True,exist_ok=True);O.mkdir(parents=True,exist_ok=True)
meta={a['key']:a for a in json.loads((R/'assets/nature/nature.json').read_text())['sprites']}
prompts=json.loads((S.parent/'rock-prompts.json').read_text())
report=[]
sheet=Image.new('RGB',(896,376),(29,42,48));draw=ImageDraw.Draw(sheet)
for i,p in enumerate(prompts):
 name=p['name'];original=Image.open(R/meta[name]['path'].removeprefix('res://')).convert('RGBA')
 src=Path(p['source']);saved=S/(name+'-source.png');shutil.copy2(src,saved)
 im=Image.open(src).convert('RGBA');alpha=im.getchannel('A').point(lambda v:255 if v>=64 else 0)
 box=alpha.getbbox();im.putalpha(alpha);im=im.crop(box)
 ob=original.getbbox();limit=(ob[2]-ob[0],ob[3]-ob[1]);scale=min(limit[0]/im.width,limit[1]/im.height)
 target=(round(im.width*scale),round(im.height*scale));im=im.resize(target,Image.Resampling.BOX)
 im.putalpha(im.getchannel('A').point(lambda v:255 if v>=128 else 0))
 out=Image.new('RGBA',original.size);out.alpha_composite(im,((original.width-im.width)//2,ob[3]-im.height))
 path=D/(name+'.png');out.save(path,optimize=True)
 item={'key':'climate_snow_'+name,'original_key':name,'path':'res://'+str(path.relative_to(R)),
       'size':list(out.size),'anchor':meta[name]['anchor'],'kind':meta[name]['kind'],
       'source_bbox':list(box),'opaque_bbox':list(out.getbbox()),'bytes':path.stat().st_size,
       'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source':str(saved.relative_to(R)),
       'export':'Alpha below64 removed; proportional BOX export into original opaque bounds; native alpha128 cutoff; full original canvas/anchor/footprint preserved.'}
 report.append(item)
 x=i*224;draw.text((x+8,8),name,fill=(235,240,246))
 for row,bg in enumerate([(29,42,48),(225,226,235)]):
  y=36+row*168;draw.rectangle((x,y,x+223,y+159),fill=bg)
  sheet.paste(original.resize((original.width*2,original.height*2),Image.Resampling.NEAREST),(x+9,y+20),original.resize((original.width*2,original.height*2),Image.Resampling.NEAREST))
  sheet.paste(out.resize((out.width*2,out.height*2),Image.Resampling.NEAREST),(x+118,y+20),out.resize((out.width*2,out.height*2),Image.Resampling.NEAREST))
(S/'export.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
sheet.save(O/'winter-rock-contours.png',optimize=True)
print(json.dumps(report,ensure_ascii=False))
