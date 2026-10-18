from pathlib import Path
from PIL import Image
import json,subprocess
P=Path(__file__).resolve().parents[1];M='/opt/homebrew/bin/magick'
OUT=P/'battle/candidate-run-v1';OUT.mkdir(parents=True,exist_ok=True)
def run(*args):subprocess.run([M,*map(str,args)],check=True)
def mask(im):return im.convert('RGBA').getchannel('A').point(lambda v:255 if v>=32 else 0)
records=[]
for frame,tag,n,slot,head_top in [(1,'run-1-2-3',3,0,239),(2,'run-1-2-3',3,1,242),(3,'run-1-2-3',3,2,244),(4,'run-4-5',2,0,206),(5,'run-4-5',2,1,217)]:
 rawp=P/f'source/{tag}-v1-generated.png'
 if frame==3:rawp=P/'source/run3-foreleg-tail-v2-generated.png';n=1;slot=0;head_top=423
 raw=Image.open(rawp).convert('RGBA');cell=(raw.width*slot//n,0,raw.width*(slot+1)//n,raw.height);im=raw.crop(cell);a=mask(im);b=a.getbbox()
 src=Image.open(P/f'reference/original-{frame:03}.png').convert('RGBA');sa=mask(src);sb=sa.getbbox()
 source_hoof_extents={1:[34,59],2:[31,64],3:[32,65],4:[43,58],5:[40,52]}[frame]
 target=[sum(source_hoof_extents)*2,sb[3]*4]
 scale=4*(sb[3]-28)/(b[3]-head_top);crop=(max(0,b[0]-3),max(0,b[1]-3),min(im.width,b[2]+3),min(im.height,b[3]+3));cut=OUT/f'cut-{frame:03}.png';small=OUT/f'resized-{frame:03}.png'
 run(rawp,'-crop',f'{crop[2]-crop[0]}x{crop[3]-crop[1]}+{cell[0]+crop[0]}+{crop[1]}','+repage',cut);run(cut,'-filter','Lanczos','-resize',f'{scale*100:.10f}%',small)
 sm=Image.open(small).convert('RGBA');ma=mask(sm);mb=ma.getbbox()
 feet_roi={1:[220,520,600,725],2:[150,550,635,700],3:[250,970,1150,1100],4:[480,690,580,750],5:[480,560,740,760]}[frame]
 fb=a.crop(feet_roi).getbbox();foot_raw=[fb[0]+feet_roi[0],fb[1]+feet_roi[1],fb[2]+feet_roi[0],fb[3]+feet_roi[1]]
 foot_center=(foot_raw[0]+foot_raw[2])/2;sx=sm.width/(crop[2]-crop[0]);registered_center=(foot_center-crop[0])*sx
 
 if frame==4:
  band=ma.crop((0,mb[3]-3,sm.width,mb[3])).getbbox();registered_center=(band[0]+band[2])/2;target=[178,256]
 dx=round(target[0]-registered_center);dy=target[1]-mb[3]
 dst=OUT/f'frame-{frame:03}.png';run('-size','320x256','xc:none',small,'-geometry',f'{dx:+d}{dy:+d}','-compose','over','-composite',dst)
 clipped=sum(1 for y in range(sm.height)for x in range(sm.width)if not(0<=x+dx<320 and 0<=y+dy<256)and sm.getpixel((x,y))[3]>=32)
 records.append({'frame':frame,'raw':str(rawp.relative_to(P)),'cell':cell,'crop':crop,'head_top':head_top,'source_helmet_top':28,'uniform_scale':scale,'resampled_size':list(sm.size),'translation':[dx,dy],'target_hoof_anchor':target,'registered_hoof_anchor':[registered_center+dx,mb[3]+dy],'source_hoof_extents_x':source_hoof_extents,'generated_hooves_roi':feet_roi,'generated_hooves_bounds':foot_raw,'visible_clipped_pixels':clipped})
 run(P/f'reference/original-{frame:03}.png','-filter','point','-resize','400%',OUT/f'original4-{frame:03}.png')
(OUT/'registration.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
files=[]
for f in range(1,6):files.extend([OUT/f'original4-{f:03}.png',OUT/f'frame-{f:03}.png'])
for c,label in [('#1d2932','dark'),('#eee8d8','light')]:run('montage','-font','/System/Library/Fonts/STHeiti Medium.ttc',*files,'-tile','2x5','-geometry','320x256+0+8','-background',c,P/f'battle/reviews/run-v1-original-vs-new-{label}.png')
print(json.dumps(records))
