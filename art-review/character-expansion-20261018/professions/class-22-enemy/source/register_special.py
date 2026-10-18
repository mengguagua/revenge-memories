from pathlib import Path
from PIL import Image
import json,subprocess
P=Path(__file__).resolve().parents[1];M='/opt/homebrew/bin/magick';OUT=P/'battle/candidate-special';OUT.mkdir(exist_ok=True)
def run(*a):subprocess.run([M,*map(str,a)],check=True)
def mask(im):return im.convert('RGBA').getchannel('A').point(lambda v:255 if v>=32 else 0)
rawp=P/'source/thrust-release-11-27-v1-generated.png';raw=Image.open(rawp).convert('RGBA');recs=[]
for f,cell in [(11,[0,0,1150,793]),(27,[1150,0,1984,793])]:
 im=raw.crop(cell);a=mask(im);b=a.getbbox();head=b[1];scale=136/(b[3]-head);crop=[max(0,b[0]-3),max(0,b[1]-3),min(im.width,b[2]+3),min(im.height,b[3]+3)];cut=OUT/f'cut-{f:03}.png';small=OUT/f'small-{f:03}.png'
 run(rawp,'-crop',f'{crop[2]-crop[0]}x{crop[3]-crop[1]}+{cell[0]+crop[0]}+{crop[1]}','+repage',cut);run(cut,'-filter','Lanczos','-resize',f'{scale*100:.10f}%',small)
 sm=Image.open(small).convert('RGBA');ma=mask(sm);mb=ma.getbbox();fb=ma.crop((0,mb[3]-3,sm.width,mb[3])).getbbox();fx=(fb[0]+fb[2])/2
 sa=mask(Image.open(P/f'reference/original-{f:03}.png'));sf=sa.crop((0,63,80,64)).getbbox();target=[2*(sf[0]+sf[2]),256];dx=round(target[0]-fx);dy=256-mb[3]
 dst=OUT/f'frame-{f:03}.png';run('-size','320x256','xc:none',small,'-geometry',f'{dx:+d}{dy:+d}','-compose','over','-composite',dst)
 clipped=sum(1 for y in range(sm.height)for x in range(sm.width)if not(0<=x+dx<320 and 0<=y+dy<256)and sm.getpixel((x,y))[3]>=32)
 recs.append({'frame':f,'raw':str(rawp.relative_to(P)),'cell':cell,'crop':crop,'head_top':head,'uniform_scale':scale,'translation':[dx,dy],'target_boot_anchor':target,'registered_boot_anchor':[fx+dx,256],'visible_clipped_pixels_alpha32':clipped})
 run(P/f'reference/original-{f:03}.png','-filter','point','-resize','400%',OUT/f'original4-{f:03}.png')
(OUT/'registration.json').write_text(json.dumps(recs,indent=2)+'\n')
for c,l in [('#1d2932','dark'),('#eee8d8','light')]:run('montage','-font','/System/Library/Fonts/STHeiti Medium.ttc',*[OUT/f'original4-{f:03}.png'for f in [11,27]],*[OUT/f'frame-{f:03}.png'for f in [11,27]],'-tile','2x2','-geometry','320x256+0+8','-background',c,P/f'battle/reviews/special-v1-{l}.png')
print(recs)
