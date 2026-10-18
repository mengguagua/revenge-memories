"""Register stationary map breathing poses; legs are not walking phases."""
from pathlib import Path
from PIL import Image
import json,subprocess
M=Path(__file__).resolve().parents[1];P=M.parent;G='/opt/homebrew/bin/magick';O=M/'idle-frames';O.mkdir(exist_ok=True);(M/'reviews').mkdir(exist_ok=True);(M/'frames').mkdir(exist_ok=True)
def run(*a):subprocess.run([G,*map(str,a)],check=True)
def mask(i):return i.convert('RGBA').getchannel('A').point(lambda a:255 if a>=32 else 0)
p=M/'source/idle-v2-generated.png';raw=Image.open(p).convert('RGBA');records=[]
for f in range(3):
 cell=[raw.width*f//3,0,raw.width*(f+1)//3,raw.height];im=raw.crop(cell);a=mask(im);b=a.getbbox();scale=64/(b[3]-b[1]);crop=[max(0,b[0]-3),max(0,b[1]-3),min(im.width,b[2]+3),min(im.height,b[3]+3)];cut=M/f'source/idle-cut-{f}.png';small=M/f'source/idle-small-{f}.png'
 run(p,'-crop',f'{crop[2]-crop[0]}x{crop[3]-crop[1]}+{cell[0]+crop[0]}+{crop[1]}','+repage',cut);run(cut,'-filter','Lanczos','-resize',f'{scale*100:.10f}%',small)
 sm=Image.open(small).convert('RGBA');ma=mask(sm);sb=ma.getbbox();fb=ma.crop((0,sb[3]-2,sm.width,sb[3])).getbbox();fx=(fb[0]+fb[2])/2;target=[62,80];dx=round(62-fx);dy=80-sb[3];dst=O/f'frame-{f:03}.png';run('-size','96x96','xc:none',small,'-geometry',f'{dx:+d}{dy:+d}','-compose','over','-composite',dst)
 outside=[sm.getpixel((x,y))[3]for y in range(sm.height)for x in range(sm.width)if not(0<=x+dx<96 and 0<=y+dy<96)]
 records.append({'source_index':f,'source_frame':f,'path':f'idle-frames/frame-{f:03}.png','output_path':f'idle-frames/frame-{f:03}.png','raw':str(p.relative_to(M)),'cell':cell,'crop':crop,'uniform_scale':scale,'translation':[dx,dy],'target_near_boot_anchor':target,'registered_near_boot_anchor':[fx+dx,80],'anchor_basis':'Image-right lowest boot; original lower-leg pixels identical across phases. Image-left boot slightly higher by perspective. Whole registration does not claim exact every-foot placement.','visible_clipped_pixels_alpha32':sum(a>=32 for a in outside),'outside_nonzero_alpha_pixels':sum(a>0 for a in outside)})
 run(M/f'reference/static-{f:03}.png','-filter','point','-resize','400%',M/f'source/idle-original4-{f}.png')
(M/'idle-registration.json').write_text(json.dumps(records,indent=2)+'\n')
for c,l in [('#1d2932','dark'),('#eee8d8','light')]:
 run('montage','-font','/System/Library/Fonts/STHeiti Medium.ttc',*[M/f'source/idle-original4-{f}.png'for f in range(3)],*[O/f'frame-{f:03}.png'for f in range(3)],'-tile','3x2','-geometry','96x96+8+8','-background',c,M/f'reviews/idle-{l}.png')
 run(M/f'reviews/idle-{l}.png','-filter','point','-resize','300%',M/f'reviews/idle-{l}-3x.png')
print(json.dumps(records))
