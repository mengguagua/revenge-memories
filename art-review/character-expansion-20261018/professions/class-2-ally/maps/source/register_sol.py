"""Only crop, uniform scale, whole-frame registration and proven full-frame mirrors."""
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw
import json,hashlib
M=Path(__file__).resolve().parents[1];O=M/'sol-native-frames';O.mkdir(exist_ok=True)
def mask(i):return i.getchannel('A').point(lambda a:255 if a>=32 else 0)
records=[]
for f in range(6):
 name='sol-native-up-v2-generated.png' if f<2 else 'sol-native-side-down-v2-generated.png';raw=Image.open(M/'source'/name).convert('RGBA');n=f if f<2 else f-2;h=raw.height if f<2 else raw.height//2;w=raw.width//2;cell=(n%2*w,n//2*h,(n%2+1)*w,(n//2+1)*h);im=raw.crop(cell);a=mask(im);b=a.getbbox();head=245 if f<2 else 75 if f<4 else 34
 scale=64/(b[3]-head);sm=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS);ma=mask(sm);bb=ma.getbbox();fb=a.crop((0,b[3]-8,im.width,b[3])).getbbox();cx=(fb[0]+fb[2])/2*sm.width/im.width;target_x=[58,74,64,74,78,48][f];dx=round(target_x-cx);dy=96-bb[3];out=Image.new('RGBA',(128,96));out.alpha_composite(sm,(dx,dy));out.save(O/f'frame-{f:03}.png',optimize=True)
 outside=[sm.getpixel((x,y))[3]for y in range(sm.height)for x in range(sm.width)if not(0<=x+dx<128 and 0<=y+dy<96)]
 records.append({'revision':'sol','slot':f,'raw':'source/'+name,'cell':cell,'head_y':head,'target_head_y':32,'chosen_raw_low_boot_center':[(fb[0]+fb[2])/2,b[3]],'target_selected_boot_center':[target_x,96],'registered_selected_boot_center':[cx+dx,96],'scale':scale,'translation':[dx,dy],'visible_clipped_alpha32':sum(v>=32 for v in outside),'clipped_alpha_max':max(outside,default=0),'note':'Only selected body top/low boot registration; not an every-joint proof. Shape details differ with new armor.'})
for dest,source in [(6,2),(7,3)]:
 old=Image.open(M/f'native-reference/frame-{source:03}.png').convert('RGBA');mirror=ImageOps.mirror(old);native=Image.open(M/f'native-reference/frame-{dest:03}.png').convert('RGBA');assert mirror.size==native.size and mirror.tobytes()==native.tobytes()
 ImageOps.mirror(Image.open(O/f'frame-{source:03}.png')).save(O/f'frame-{dest:03}.png',optimize=True);records.append({'slot':dest,'exact_mirror_alias_of':source,'source_complete_rgba_mirror_proof':True,'revision':'sol'})
(M/'source/sol-native-registration.json').write_text(json.dumps(records,indent=2)+'\n')
for bg,label in [('#eee8d8','light'),('#1d2932','dark')]:
 canvas=Image.new('RGB',(128*4,96*4),bg);d=ImageDraw.Draw(canvas)
 for f in range(8):
  x=f%4*128;y=f//4*192;src=Image.open(M/f'native-reference/frame-{f:03}.png').convert('RGBA').resize((128,96),Image.Resampling.NEAREST);new=Image.open(O/f'frame-{f:03}.png').convert('RGBA');canvas.paste(src,(x,y),src);canvas.paste(new,(x,y+96),new)
 canvas.resize((1024,768),Image.Resampling.NEAREST).save(M/f'reviews/sol-native-{label}-2x.png',optimize=True)
print(json.dumps(records))
