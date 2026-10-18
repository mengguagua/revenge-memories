from pathlib import Path
from PIL import Image
import json,subprocess
P=Path(__file__).resolve().parents[1];M='/opt/homebrew/bin/magick'
OUT=P/'battle/candidate-special';OUT.mkdir(parents=True,exist_ok=True)
def run(*args):subprocess.run([M,*map(str,args)],check=True)
def mask(im):return im.convert('RGBA').getchannel('A').point(lambda v:255 if v>=32 else 0)
records=[]
for frame,name,cell,head in [(17,'throw-17-19-v1-generated.png',(0,0,991,793),208),(19,'post-release19-v2-generated.png',None,378),(4,'run4-hind-hoof-v2-generated.png',None,306)]:
 rawp=P/'source'/name;raw=Image.open(rawp).convert('RGBA');cell=cell or(0,0,raw.width,raw.height);art=raw.crop(cell);a=mask(art);b=a.getbbox();scale=144/(b[3]-head)
 crop=(max(0,b[0]-3),max(0,b[1]-3),min(art.width,b[2]+3),min(art.height,b[3]+3));cut=OUT/f'cut-{frame:03}.png';small=OUT/f'resized-{frame:03}.png'
 run(rawp,'-crop',f'{crop[2]-crop[0]}x{crop[3]-crop[1]}+{cell[0]+crop[0]}+{crop[1]}','+repage',cut);run(cut,'-filter','Lanczos','-resize',f'{scale*100:.10f}%',small)
 sm=Image.open(small).convert('RGBA');ma=mask(sm);sb=ma.getbbox();band=4 if frame==4 else 6;foot=ma.crop((0,sb[3]-band,sm.width,sb[3])).getbbox();target=[178 if frame==4 else 128,256];dx=round(target[0]-(foot[0]+foot[2])/2);dy=256-sb[3]
 dst=OUT/f'frame-{frame:03}.png';run('-size','320x256','xc:none',small,'-geometry',f'{dx:+d}{dy:+d}','-compose','over','-composite',dst)
 clipped=sum(1 for y in range(sm.height)for x in range(sm.width)if not(0<=x+dx<320 and 0<=y+dy<256)and sm.getpixel((x,y))[3]>=32)
 records.append({'frame':frame,'raw':str(rawp.relative_to(P)),'cell':cell,'crop':crop,'head_top':head,'source_helmet_top':28,'uniform_scale':scale,'resampled_size':list(sm.size),'translation':[dx,dy],'target_hoof_anchor':target,'registered_hoof_anchor':[(foot[0]+foot[2])/2+dx,sb[3]+dy],'registration_basis':'lowest planted front hoof; raised hind hoof excluded'if frame==4 else'all planted hoof soles','visible_clipped_pixels':clipped})
 run(P/f'reference/original-{frame:03}.png','-filter','point','-resize','400%',OUT/f'original4-{frame:03}.png')
(OUT/'registration.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
for color,label in [('#1d2932','dark'),('#eee8d8','light')]:
 files=[]
 for f in [17,19,4]:files.extend([OUT/f'original4-{f:03}.png',OUT/f'frame-{f:03}.png'])
 run('montage','-font','/System/Library/Fonts/STHeiti Medium.ttc',*files,'-tile','2x3','-geometry','320x256+0+8','-background',color,P/f'battle/reviews/special-final-original-vs-new-{label}.png')
print(json.dumps(records))
