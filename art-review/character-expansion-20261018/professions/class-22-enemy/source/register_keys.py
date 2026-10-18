from pathlib import Path
from PIL import Image
import json,subprocess
P=Path(__file__).resolve().parents[1];M='/opt/homebrew/bin/magick';OUT=P/'battle/candidate-keys-v1';OUT.mkdir(parents=True,exist_ok=True)
def run(*a):subprocess.run([M,*map(str,a)],check=True)
def mask(im):return im.convert('RGBA').getchannel('A').point(lambda v:255 if v>=32 else 0)
rawp=P/'source/key-0-10-25-v1-generated.png';raw=Image.open(rawp).convert('RGBA');records=[]
for frame,cell,head in [(0,[0,0,724,725],233),(10,[724,0,1500,725],233),(25,[1500,0,2170,725],235)]:
 
 chosen=rawp
 if frame==25:
  chosen=P/'source/key25-shorter-javelin-v2-generated.png';im=Image.open(chosen).convert('RGBA');cell=[0,0,*im.size];head=405
 else:im=raw.crop(cell)
 a=mask(im);b=a.getbbox();scale=136/(b[3]-head);crop=[max(0,b[0]-3),max(0,b[1]-3),min(im.width,b[2]+3),min(im.height,b[3]+3)];cut=OUT/f'cut-{frame:03}.png';small=OUT/f'small-{frame:03}.png'
 run(chosen,'-crop',f'{crop[2]-crop[0]}x{crop[3]-crop[1]}+{cell[0]+crop[0]}+{crop[1]}','+repage',cut);run(cut,'-filter','Lanczos','-resize',f'{scale*100:.10f}%',small)
 sm=Image.open(small).convert('RGBA');ma=mask(sm);mb=ma.getbbox();foot=ma.crop((0,mb[3]-3,sm.width,mb[3])).getbbox();fx=(foot[0]+foot[2])/2
 if frame==0:
  rr=(330,600,620,640);fb=a.crop(rr).getbbox();rawx=(fb[0]+fb[2])/2+rr[0];fx=(rawx-crop[0])*sm.width/(crop[2]-crop[0])
 src=Image.open(P/f'reference/original-{frame:03}.png');sb=mask(src).crop((0,63,80,64)).getbbox();target=[2*(sb[0]+sb[2]),256];dx=round(target[0]-fx);dy=256-mb[3]
 dst=OUT/f'frame-{frame:03}.png';run('-size','320x256','xc:none',small,'-geometry',f'{dx:+d}{dy:+d}','-compose','over','-composite',dst)
 lost=sum(1 for y in range(sm.height)for x in range(sm.width)if not(0<=x+dx<320 and 0<=y+dy<256)and sm.getpixel((x,y))[3]>=32)
 records.append({'frame':frame,'raw':str(chosen.relative_to(P)),'cell':cell,'head_top':head,'source_hair_top_without_helmet_crest':30,'crop':crop,'uniform_scale':scale,'translation':[dx,dy],'resampled_size':list(sm.size),'target_boot_anchor':target,'registered_boot_anchor':[fx+dx,256],'visible_clipped_pixels':lost})
 run(P/f'reference/original-{frame:03}.png','-filter','point','-resize','400%',OUT/f'original4-{frame:03}.png')
(OUT/'registration.json').write_text(json.dumps(records,indent=2)+'\n')
for c,l in [('#1d2932','dark'),('#eee8d8','light')]:run('montage','-font','/System/Library/Fonts/STHeiti Medium.ttc',*[OUT/f'original4-{f:03}.png'for f in [0,10,25]],*[OUT/f'frame-{f:03}.png'for f in [0,10,25]],'-tile','3x2','-geometry','320x256+0+8','-background',c,P/f'battle/reviews/keys-v1-original-new-{l}.png')
print(json.dumps(records))
