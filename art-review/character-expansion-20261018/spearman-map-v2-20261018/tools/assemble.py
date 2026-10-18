"""Register generated layers; compose native translations without drawing anatomy."""
from pathlib import Path
import subprocess,json,shutil
from PIL import Image
V=Path(__file__).resolve().parents[1];R=V.parent;OLD=R/'archer-spearman-map-review-20261018';C=V/'candidates';L=V/'layers';G='/opt/homebrew/bin/magick'
def run(*a):subprocess.run([G,*map(str,a)],check=True)
def quant(src,dst):
 run(src,'-alpha','extract','-threshold','50%',C/'alpha.png')
 run(src,'-background','#172638','-alpha','remove','-alpha','off','-dither','None','-remap',OLD/'candidates/class-6-ally/palette.png',C/'rgb.png')
 run(C/'rgb.png',C/'alpha.png','-alpha','off','-compose','CopyOpacity','-composite','-background','black','-alpha','background',dst)
def move(src,size,dx,dy,dst):run('-size',size,'xc:none',src,'-geometry',f'{dx:+d}{dy:+d}','-compose','Over','-composite',dst)
raw=V/'source/idle-layers.png';w,h=Image.open(raw).size
# Discard only the extraneous center divider; each cell has identical geometry.
for n,name in enumerate(['idle-fixed','idle-moving']):
 run(raw,'-crop',f'{w//2-10}x{h}+{n*(w//2)+5}+0','+repage','-filter','point','-resize','9.36%',C/f'{name}-small.png')
 quant(C/f'{name}-small.png',C/f'{name}-colored.png')
 move(C/f'{name}-colored.png','96x96',4,0,L/f'{name}.png')
run(L/'idle-moving.png','-region','35x32+59+0','-fill','#E4E1C8','-opaque','#DDA77D','+region',L/'idle-moving.png')
# Isolate the generated skin arm plus its existing outline. The entire spear is
# behind the body; the arm is in front. This keeps one shaft and a fixed face.
run(L/'idle-moving.png','-alpha','off','-fill','black','+opaque','#DDA77D','-fill','white','-opaque','#DDA77D','-colorspace','gray','-morphology','Dilate','Diamond:1',L/'arm-mask.png')
run(L/'idle-moving.png','-alpha','extract',L/'arm-mask.png','-compose','Multiply','-composite',L/'arm-alpha.png')
run(L/'idle-moving.png',L/'arm-alpha.png','-alpha','off','-compose','CopyOpacity','-composite',L/'arm.png')
for i,(dx,dy) in enumerate([(0,0),(-4,0),(-4,-4)]):
 move(L/'idle-moving.png','96x96',dx,dy,L/f'idle-moving-{i}.png')
 move(L/'arm.png','96x96',dx,dy,L/f'arm-{i}.png')
 run(L/f'idle-moving-{i}.png',L/'idle-fixed.png','-compose','Over','-composite',L/f'arm-{i}.png','-compose','Over','-composite',C/f'idle-{i}.png')
 # The fixed head and shoulder pivot occlude the translating upper-arm root.
 run(C/f'idle-{i}.png','(',L/'idle-fixed.png','-crop','45x46+23+0','+repage',')','-geometry','+23+0','-compose','Over','-composite',C/f'idle-{i}.png')
for key in ['class-6-ally','class-6-enemy']:
 O=V/'deliverables'/key
 for i,src in enumerate([0,1,2,1,0,1]):
  if key.endswith('enemy'):run(C/f'idle-{src}.png','-fill','#AE5148','-opaque','#3976B5',O/f'idle-{i:02}.png')
  else:shutil.copy2(C/f'idle-{src}.png',O/f'idle-{i:02}.png')
run('montage','-font','/System/Library/Fonts/STHeiti Medium.ttc',*[V/f'deliverables/{k}/idle-{i:02}.png' for k in ['class-6-ally','class-6-enemy'] for i in range(3)],'-tile','3x2','-geometry','96x96+8+8','-background','#d9d6c9',V/'reviews/idle-contact.png')
run(V/'reviews/idle-contact.png','-filter','point','-resize','400%',V/'reviews/idle-contact-4x.png')

if (V/'source/side-walk.png').exists():
 raw=V/'source/side-walk.png';w,h=Image.open(raw).size
 for i in range(2):
  run(raw,'-crop',f'{w//2}x{h}+{i*(w//2)}+0','+repage',C/f'right-{i}-raw.png')
  # Register by the character height, then preserve the accepted fixed head and torso.
  a=Image.open(C/f'right-{i}-raw.png').convert('RGBA');b=a.getchannel('A').point(lambda v:255 if v>=128 else 0).getbbox()
  scale=64/(b[3]-b[1])
  run(C/f'right-{i}-raw.png','-filter','point','-resize',f'{scale*100}%',C/f'right-{i}-small.png')
  quant(C/f'right-{i}-small.png',C/f'right-{i}-color.png')
  a=Image.open(C/f'right-{i}-color.png').convert('RGBA');b=a.getbbox()
  # Helmet/face extends to the front, registered to the previous face center x66.
  skin=[(x,y)for y in range(b[1],b[1]+26)for x in range(a.width)if a.getpixel((x,y))==(221,167,125,255)]
  center=sum(x for x,y in skin)/len(skin)
  move(C/f'right-{i}-color.png','128x96',round(66-center),96-b[3],C/f'right-{i}-aligned.png')
  base=OLD/f'deliverables/class-6-ally/walk-{i+2:02}.png'
  # Complete leg area comes from ImageGen. Retain original weapon and arm phases.
  run(base,'(',C/f'right-{i}-aligned.png','-crop','49x18+34+78','+repage',')','-geometry','+34+78','-define','compose:outside-overlay=false','-compose','Src','-composite',C/f'walk-{i+2:02}.png')
 for key in ['class-6-ally','class-6-enemy']:
  O=V/'deliverables'/key
  for i in [0,1,4,5]:shutil.copy2(OLD/f'deliverables/{key}/walk-{i:02}.png',O/f'walk-{i:02}.png')
  for i in [2,3]:
   if key.endswith('enemy'):run(C/f'walk-{i:02}.png','-fill','#AE5148','-opaque','#3976B5',O/f'walk-{i:02}.png')
   else:shutil.copy2(C/f'walk-{i:02}.png',O/f'walk-{i:02}.png')
  for dst,src in [(6,2),(7,3)]:run(O/f'walk-{src:02}.png','-flop',O/f'walk-{dst:02}.png')
 run('montage','-font','/System/Library/Fonts/STHeiti Medium.ttc',*[V/f'deliverables/{k}/walk-{i:02}.png'for k in ['class-6-ally','class-6-enemy']for i in [2,3,6,7]],'-tile','4x2','-geometry','128x96+8+8','-background','#d9d6c9',V/'reviews/side-contact.png')
 run(V/'reviews/side-contact.png','-filter','point','-resize','400%',V/'reviews/side-contact-4x.png')
