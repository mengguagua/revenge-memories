"""Register ImageGen sprites using native helmet-top position and visible height."""
from pathlib import Path
from PIL import Image
import json,subprocess
M=Path(__file__).resolve().parents[1];G='/opt/homebrew/bin/magick';O=M/'tactical-native-frames';O.mkdir(exist_ok=True)
def run(*a):subprocess.run([G,*map(str,a)],check=True)
def mask(i):return i.convert('RGBA').getchannel('A').point(lambda a:255 if a>=32 else 0)
def largest_top_component(a,b):
 # Detection only: retain all original generated alpha in the actual sprite.
 pts={(x,y)for y in range(b[1],b[1]+35)for x in range(a.width)if a.getpixel((x,y))};groups=[]
 while pts:
  seed=pts.pop();todo=[seed];group=[seed]
  while todo:
   x,y=todo.pop()
   for n in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
    if n in pts:pts.remove(n);todo.append(n);group.append(n)
  groups.append(group)
 group=max(groups,key=len);return (min(x for x,y in group)+max(x for x,y in group)+1)/2
records=[]
for f in range(6):
 d=['up','up','right','right','down','down'][f];tag=next((name for name in [f'native-{d}-phase-v2-generated.png','native-right-neck-v2-generated.png'if d=='right'else '',f'native-{d}-v1-generated.png']if name and(M/'source'/name).exists()),None);p=M/'source'/tag;raw=Image.open(p).convert('RGBA');i=f%2;cell=[raw.width*i//2,0,raw.width*(i+1)//2,raw.height];im=raw.crop(cell);a=mask(im);b=a.getbbox();hx=largest_top_component(a,b);native=Image.open(M/f'native-reference/frame-{f:03}.png').convert('RGBA');nb=mask(native).getbbox();target_head_x=[64,64,58,62,64,64][f];other=raw.crop((raw.width*(1-i)//2,0,raw.width*(2-i)//2,raw.height));ob=mask(other).getbbox();other_native=mask(Image.open(M/f'native-reference/frame-{f//2*2+1-i:03}.png')).getbbox();scale=4*max(nb[3]-nb[1],other_native[3]-other_native[1])/max(b[3]-b[1],ob[3]-ob[1]);crop=[max(0,b[0]-3),max(0,b[1]-3),min(im.width,b[2]+3),min(im.height,b[3]+3)];cut=M/f'source/native-cut-{f:03}.png';small=M/f'source/native-small-{f:03}.png'
 run(p,'-crop',f'{crop[2]-crop[0]}x{crop[3]-crop[1]}+{cell[0]+crop[0]}+{crop[1]}','+repage',cut);run(cut,'-filter','Lanczos','-resize',f'{scale*100:.10f}%',small)
 sm=Image.open(small).convert('RGBA');sb=mask(sm).getbbox();headx=(hx-crop[0])*sm.width/(crop[2]-crop[0]);dx=round(target_head_x-headx);dy=round(nb[1]*4-(b[1]-crop[1])*sm.height/(crop[3]-crop[1]));rounding_adjustment=-1 if dy+sb[3]>nb[3]*4 and dy+sb[3]-nb[3]*4<=1 else 0;dy+=rounding_adjustment;dst=O/f'frame-{f:03}.png';run('-size','128x96','xc:none',small,'-geometry',f'{dx:+d}{dy:+d}','-compose','over','-composite',dst)
 outside=[sm.getpixel((x,y))[3]for y in range(sm.height)for x in range(sm.width)if not(0<=x+dx<128 and 0<=y+dy<96)]
 records.append({'source_index':f,'source_frame':f,'path':f'tactical-native-frames/frame-{f:03}.png','output_path':f'tactical-native-frames/frame-{f:03}.png','raw':f'source/{tag}','cell':cell,'crop':crop,'uniform_scale':scale,'translation':[dx,dy],'native_visible_bounds':nb,'registered_visible_bottom':dy+sb[3],'source_visible_bottom':nb[3]*4,'pair_uniform_scale':True,'vertical_resampling_rounding_adjustment':rounding_adjustment,'generated_helmet_top_component_center':hx,'target_helmet_x':target_head_x,'registered_helmet_x':headx+dx,'visible_clipped_pixels_alpha32':sum(a>=32 for a in outside),'outside_nonzero_alpha_pixels':sum(a>0 for a in outside),'registration_basis':'Helmet top/X and visible height with whole-image uniform scaling. Not an inferred anatomical hoof/pelvis anchor; all in-canvas generated alpha retained.'})
for f,s in [(6,2),(7,3)]:run(O/f'frame-{s:03}.png','-flop',O/f'frame-{f:03}.png')
(M/'tactical-native-registration.json').write_text(json.dumps(records,indent=2)+'\n')
run(*[O/f'frame-{f:03}.png'for f in range(8)],'+append',M/'frames/tactical-native-walk.png')
for f in range(8):run(M/f'native-reference/frame-{f:03}.png','-filter','point','-resize','400%',O/f'source4-{f:03}.png')
for c,l in [('#1d2932','dark'),('#eee8d8','light')]:
 run('montage','-font','/System/Library/Fonts/STHeiti Medium.ttc',*[O/f'source4-{f:03}.png'for f in range(8)],*[O/f'frame-{f:03}.png'for f in range(8)],'-tile','8x2','-geometry','128x96+8+8','-background',c,M/f'reviews/native-walk-{l}.png')
print(json.dumps({'registered':6,'mirror':2,'visible_clipped':sum(r['visible_clipped_pixels_alpha32']for r in records)}))
