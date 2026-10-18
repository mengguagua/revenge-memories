"""Technical registration; foot ROI excludes lance and trailing cloth."""
from pathlib import Path
from PIL import Image
import json,subprocess
P=Path(__file__).resolve().parents[1];M='/opt/homebrew/bin/magick';OUT=P/'battle/candidate-motion';OUT.mkdir(exist_ok=True)
def run(*a):subprocess.run([M,*map(str,a)],check=True)
def mask(im):return im.convert('RGBA').getchannel('A').point(lambda v:255 if v>=32 else 0)
records=[]
for f in range(1,9):
 if f<=3:tag='walk-1-2-3-v1';slot=f-1
 elif f<=6:tag='walk-4-5-6-blunt-tail-v2';slot=f-4
 else:tag='turn-7-8-9-v1';slot=f-7
 rawp=P/f'source/{tag}-generated.png';raw=Image.open(rawp).convert('RGBA');cell=[raw.width*slot//3,0,raw.width*(slot+1)//3,raw.height];im=raw.crop(cell);a=mask(im);b=a.getbbox();head=b[1];scale=136/(b[3]-head)
 crop=[max(0,b[0]-3),max(0,b[1]-3),min(im.width,b[2]+3),min(im.height,b[3]+3)];cut=OUT/f'cut-{f:03}.png';small=OUT/f'small-{f:03}.png';run(rawp,'-crop',f'{crop[2]-crop[0]}x{crop[3]-crop[1]}+{cell[0]+crop[0]}+{crop[1]}','+repage',cut);run(cut,'-filter','Lanczos','-resize',f'{scale*100:.10f}%',small)
 sm=Image.open(small).convert('RGBA');ma=mask(sm);sb=ma.getbbox();roi=[int(im.width*.35),b[3]-15,im.width,b[3]];fb=a.crop(roi).getbbox();fx=((fb[0]+fb[2])/2+roi[0]-crop[0])*sm.width/(crop[2]-crop[0])
 src=Image.open(P/f'reference/original-{f:03}.png');feet=mask(src).crop((40,63,80,64)).getbbox();target=[2*(feet[0]+feet[2]+80),256];dx=round(target[0]-fx);dy=256-sb[3]
 dst=OUT/f'frame-{f:03}.png';run('-size','320x256','xc:none',small,'-geometry',f'{dx:+d}{dy:+d}','-compose','over','-composite',dst)
 records.append({'frame':f,'raw':str(rawp.relative_to(P)),'cell':cell,'crop':crop,'head_top':head,'source_hair_top_without_crest':30,'uniform_scale':scale,'translation':[dx,dy],'source_boot_roi':[40,63,80,64],'generated_boot_roi':roi,'target_boot_anchor':target,'registered_boot_anchor':[fx+dx,256],'visible_clipped_pixels_alpha32':sum(1 for y in range(sm.height)for x in range(sm.width)if not(0<=x+dx<320 and 0<=y+dy<256)and sm.getpixel((x,y))[3]>=32)})
 run(P/f'reference/original-{f:03}.png','-filter','point','-resize','400%',OUT/f'original4-{f:03}.png')
(OUT/'registration.json').write_text(json.dumps(records,indent=2)+'\n')
for frames in [[1,2,3],[4,5,6],[7,8]]:
 for color,label in [('#1d2932','dark'),('#eee8d8','light')]:run('montage','-font','/System/Library/Fonts/STHeiti Medium.ttc',*[OUT/f'original4-{f:03}.png'for f in frames],*[OUT/f'frame-{f:03}.png'for f in frames],'-tile',f'{len(frames)}x2','-geometry','320x256+0+8','-background',color,P/f'battle/reviews/motion-{frames[0]}-{frames[-1]}-{label}.png')
print(json.dumps({'frames':len(records),'visible_clipped':sum(r['visible_clipped_pixels_alpha32']for r in records)}))
