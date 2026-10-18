"""Register local ImageGen revisions without drawing or warping any anatomy."""
from pathlib import Path
from PIL import Image
import json,subprocess
P=Path(__file__).resolve().parents[1];M='/opt/homebrew/bin/magick';O=P/'battle/candidate-revisions';O.mkdir(exist_ok=True)
def run(*a):subprocess.run([M,*map(str,a)],check=True)
def mask(i):return i.convert('RGBA').getchannel('A').point(lambda a:255 if a>=32 else 0)
spec=[(7,'pose7-cloth-only-v2',387),(9,'turn9-rear-leg-v2',310),(11,'thrust11-arm-v2',278)]
records=[]
for f,tag,head in spec:
 p=P/f'source/{tag}-generated.png';im=Image.open(p).convert('RGBA');a=mask(im);b=a.getbbox();scale=136/(b[3]-head)
 crop=[max(0,b[0]-3),max(0,b[1]-3),min(im.width,b[2]+3),min(im.height,b[3]+3)]
 cut=O/f'cut-{f:03}.png';small=O/f'small-{f:03}.png';run(p,'-crop',f'{crop[2]-crop[0]}x{crop[3]-crop[1]}+{crop[0]}+{crop[1]}','+repage',cut);run(cut,'-filter','Lanczos','-resize',f'{scale*100:.10f}%',small)
 sm=Image.open(small).convert('RGBA');ma=mask(sm);mb=ma.getbbox()
 # Both boots, excluding lance at image left. The farther boot may stand slightly higher.
 roi=[int(im.width*.4),b[3]-50,im.width,b[3]];fb=a.crop(roi).getbbox();fx=((fb[0]+fb[2])/2+roi[0]-crop[0])*sm.width/(crop[2]-crop[0])
 src=Image.open(P/f'reference/original-{f:03}.png');source_roi=[0 if f==11 else 40,63,80,64];sf=mask(src).crop(source_roi).getbbox();target=[2*(sf[0]+sf[2]+2*source_roi[0]),256];dx=round(target[0]-fx);dy=256-mb[3]
 run('-size','320x256','xc:none',small,'-geometry',f'{dx:+d}{dy:+d}','-compose','over','-composite',O/f'frame-{f:03}.png')
 outside=[sm.getpixel((x,y))[3]for y in range(sm.height)for x in range(sm.width)if not(0<=x+dx<320 and 0<=y+dy<256)]
 records.append({'frame':f,'raw':str(p.relative_to(P)),'crop':crop,'head_top':head,'source_hair_top_without_crest':30,'uniform_scale':scale,'translation':[dx,dy],'target_boot_anchor':target,'registered_boot_anchor':[fx+dx,256],'source_boot_roi':source_roi,'generated_boot_roi':roi,'visible_clipped_pixels_alpha32':sum(a>=32 for a in outside),'outside_nonzero_alpha_pixels':sum(a>0 for a in outside),'anchor_note':'Whole-body two-boot span, not a per-joint exact fit. All in-canvas generated alpha retained.'})
 run(P/f'reference/original-{f:03}.png','-filter','point','-resize','400%',O/f'original4-{f:03}.png')
(O/'registration.json').write_text(json.dumps(records,indent=2)+'\n')
for c,l in [('#1d2932','dark'),('#eee8d8','light')]:run('montage','-font','/System/Library/Fonts/STHeiti Medium.ttc',*[O/f'original4-{f:03}.png'for f,_,_ in spec],*[O/f'frame-{f:03}.png'for f,_,_ in spec],'-tile','3x2','-geometry','320x256+0+8','-background',c,P/f'battle/reviews/revisions-7-9-11-{l}.png')
print(json.dumps(records))
