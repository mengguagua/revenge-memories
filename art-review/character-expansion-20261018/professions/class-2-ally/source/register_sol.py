"""Technical crop/uniform resize/translation only. No drawn or repainted pixels."""
from pathlib import Path
from PIL import Image, ImageDraw
import json, subprocess
P=Path(__file__).resolve().parents[1]
O=P/'battle/candidate-sol';O.mkdir(exist_ok=True)
def mask(im): return im.getchannel('A').point(lambda a:255 if a>=32 else 0)
records=[]
raw=Image.open(P/'source/motion-7-10-v1-generated.png').convert('RGBA')
items=[(6,P/'source/frame6-v3-generated.png',None)]
for n in range(4):items.append((7+n,P/'source/motion-7-10-v1-generated.png',(raw.width*(n%2)//2,raw.height*(n//2)//2,raw.width*((n%2)+1)//2,raw.height*((n//2)+1)//2)))
for f,path,cell in items:
 raw=Image.open(path).convert('RGBA');cell=cell or (0,0,*raw.size);im=raw.crop(cell);a=mask(im);b=a.getbbox()
 src=Image.open(P/f'reference/original-{f:03}.png').convert('RGBA');top=src.getbbox()[1]*4
 scale=(256-top)/(b[3]-b[1]);sm=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS);ma=mask(sm);bb=ma.getbbox()
 # The lower legs occupy the right half of each cut. Exclude shaft and skirt at foot registration height.
 roi=(int(im.width*.45),b[3]-40,im.width,b[3]);fb=a.crop(roi).getbbox();cx=(roi[0]+(fb[0]+fb[2])/2)*sm.width/im.width
 sr=mask(src).crop((30,61,65,64)).getbbox();target_x=2*(sr[0]+sr[2]+60)
 dx=round(target_x-cx);dy=256-sm.getchannel('A').point(lambda v:255 if v>4 else 0).getbbox()[3];out=Image.new('RGBA',(320,256));out.alpha_composite(sm,(dx,dy));dest=O/f'frame-{f:03}.png';out.save(dest,optimize=True)
 clipped=[sm.getpixel((x,y))[3]for y in range(sm.height)for x in range(sm.width)if not(0<=x+dx<320 and 0<=y+dy<256)]
 records.append({'revision':'sol','frame':f,'raw':str(path.relative_to(P)),'cell':cell,'scale':scale,'translation':[dx,dy],'source_top_y':top,'registered_top_y':dy+bb[1],'chosen_boot_span_center':[cx+dx,bb[3]+dy],'target_boot_span_center':[target_x,256],'visible_clipped_alpha32':sum(a>=32 for a in clipped),'visible_clipped_alpha_gt4':sum(a>4 for a in clipped),'maximum_cropped_alpha':max(clipped,default=0),'clipped_alpha_nonzero':sum(a>0 for a in clipped),'status':'sol_selected_registration'})
(O/'registration.json').write_text(json.dumps(records,indent=2)+'\n')
for bg,label in [('#eee8d8','light'),('#1d2932','dark')]:
 canvas=Image.new('RGB',(960,3*290),bg);d=ImageDraw.Draw(canvas)
 for j,f in enumerate([6,7,8,9,10]):
  x=(j%3)*320;y=(j//3)*290
  # Separate row source/new inside each 320px wide mini pair, each logical rendering width160.
  s=Image.open(P/f'reference/original4-{f:03}.png').convert('RGBA');n=Image.open(O/f'frame-{f:03}.png').convert('RGBA')
  s=s.resize((160,128),Image.Resampling.NEAREST);n=n.resize((160,128),Image.Resampling.NEAREST)
  canvas.paste(s,(x,y+18),s);canvas.paste(n,(x+160,y+18),n);d.text((x+16,y+4),f'pose {f} original | sol',fill='white' if label=='dark' else 'black')
 canvas=canvas.crop((0,0,960,2*290));canvas.save(P/f'battle/reviews/sol-motion-{label}.png',optimize=True)
print(json.dumps(records))
