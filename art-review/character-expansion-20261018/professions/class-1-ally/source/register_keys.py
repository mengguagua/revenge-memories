from pathlib import Path
from PIL import Image
import json,subprocess,sys
P=Path(__file__).resolve().parents[1]
M='/opt/homebrew/bin/magick'
RAW=P/'source/key-0-6-7-v1-generated.png'
FINAL='--final' in sys.argv
TAG='final'if FINAL else 'v2'
OUT=P/f'battle/candidate-keys-{TAG}';OUT.mkdir(parents=True,exist_ok=True)
def run(*args):subprocess.run([M,*map(str,args)],check=True)
def mask(im):return im.convert('RGBA').getchannel('A').point(lambda v:255 if v>=32 else 0)
raw=Image.open(RAW).convert('RGBA');records=[]
for frame,cell,head_y,source_head_y in [(0,(0,0,724,725),238,28),(6,(724,0,1447,725),256,29),(7,(1447,0,2170,725),256,29)]:
 if False:
  chosen=P/'source/battle-key-9-6-7-v3-generated.png';raw=Image.open(chosen).convert('RGBA');head_y=186
 else:
  chosen=RAW;raw=Image.open(chosen).convert('RGBA')
 art=raw.crop(cell);a=mask(art);b=a.getbbox();scale=(64-source_head_y)*4/(b[3]-head_y)
 crop=(max(0,b[0]-3),max(0,b[1]-3),min(art.width,b[2]+3),min(art.height,b[3]+3))
 cut=OUT/f'cut-{frame:03}.png';small=OUT/f'resized-{frame:03}.png'
 run(chosen,'-crop',f'{crop[2]-crop[0]}x{crop[3]-crop[1]}+{cell[0]+crop[0]}+{crop[1]}','+repage',cut)
 run(cut,'-filter','Lanczos','-resize',f'{scale*100:.10f}%',small)
 sm=Image.open(small).convert('RGBA');ma=mask(sm);sb=ma.getbbox();foot=ma.crop((0,sb[3]-4,sm.width,sb[3])).getbbox()
 src=Image.open(P/f'reference/original-{frame:03}.png').convert('RGBA');sf=mask(src).crop((0,60,80,64)).getbbox();target=[(sf[0]+sf[2])*2,256]
 dx=round(target[0]-(foot[0]+foot[2])/2);dy=256-sb[3]
 dst=OUT/f'frame-{frame:03}.png';run('-size','320x256','xc:none',small,'-geometry',f'{dx:+d}{dy:+d}','-compose','over','-composite',dst)
 lost=sum(1 for y in range(sm.height)for x in range(sm.width)if not(0<=x+dx<320 and 0<=y+dy<256)and sm.getpixel((x,y))[3]>=32)
 records.append({'frame':frame,'raw':str(chosen.relative_to(P)),'cell':cell,'content_bounds':b,'crop':crop,'head_top':head_y,'source_helmet_top':source_head_y,'uniform_scale':scale,'resampled_size':list(sm.size),'translation':[dx,dy],'target_hoof_anchor':target,'registered_hoof_anchor':[(foot[0]+foot[2])/2+dx,sb[3]+dy],'visible_clipped_pixels':lost})
 (P/f'reference/original-{frame:03}.png').exists();run(P/f'reference/original-{frame:03}.png','-filter','point','-resize','400%',OUT/f'original4-{frame:03}.png')
(OUT/'registration.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
review=P/'battle/reviews';review.mkdir(exist_ok=True)
for color,label in [('#1d2932','dark'),('#eee8d8','light')]:
 run('montage','-font','/System/Library/Fonts/STHeiti Medium.ttc',*[OUT/f'original4-{f:03}.png'for f in [0,6,7]],*[OUT/f'frame-{f:03}.png'for f in [0,6,7]],'-tile','3x2','-geometry','320x256+0+8','-background',color,review/f'keys-{TAG}-original-vs-new-{label}.png')
print(json.dumps(records))
