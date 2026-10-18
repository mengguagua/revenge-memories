# -*- coding: utf-8 -*-
"""Technical registration/compositing of ImageGen artwork, not anatomy drawing."""
from pathlib import Path
from PIL import Image
import subprocess,shutil,json
V=Path(__file__).resolve().parents[1];R=V.parent;P=R/'spearman-map-v2-20261018';OLD=R/'archer-spearman-map-review-20261018';C=V/'candidates';L=V/'layers';G='/opt/homebrew/bin/magick'
def run(*a):subprocess.run([G,*map(str,a)],check=True)
def bbox(p):return Image.open(p).convert('RGBA').getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()
def quant(src,dst):
 run(src,'-alpha','extract','-threshold','50%',C/'alpha.png')
 run(src,'-background','#172638','-alpha','remove','-alpha','off','-dither','None','-remap',OLD/'candidates/class-6-ally/palette.png',C/'rgb.png')
 run(C/'rgb.png',C/'alpha.png','-alpha','off','-compose','CopyOpacity','-composite','-background','black','-alpha','background',dst)
def move(src,size,dx,dy,dst):run('-size',size,'xc:none',src,'-geometry',f'{dx:+d}{dy:+d}','-compose','Over','-composite',dst)
def patch(base,src,box,dst):
 x,y,r,b=box;run(base,'(',src,'-crop',f'{r-x}x{b-y}+{x}+{y}','+repage',')','-geometry',f'+{x}+{y}','-define','compose:outside-overlay=false','-compose','Src','-composite',dst)
def contact(files,name,tile,geometry):
 run('montage','-font','/System/Library/Fonts/STHeiti Medium.ttc',*files,'-tile',tile,'-geometry',geometry,'-background','#d9d6c9',V/f'reviews/{name}.png')
 run(V/f'reviews/{name}.png','-filter','point','-resize','400%',V/f'reviews/{name}-4x.png')
# User explicitly requested fallback: both legs vertical + the existing stride.
raw=V/'source/neutral.png';b=bbox(raw);factor=64/(b[3]-b[1]);run(raw,'-filter','point','-resize',f'{factor*100}%',C/'neutral-small.png');quant(C/'neutral-small.png',C/'neutral-color.png')
a=Image.open(C/'neutral-color.png').convert('RGBA');b=a.getbbox();skin=[(x,y)for y in range(b[1],b[1]+26)for x in range(a.width)if a.getpixel((x,y))==(221,167,125,255)];center=sum(x for x,y in skin)/len(skin)
move(C/'neutral-color.png','128x96',round(66-center),96-b[3],C/'neutral-aligned.png')
patch(P/'deliverables/class-6-ally/walk-02.png',C/'neutral-aligned.png',(34,78,83,96),C/'walk-02.png')
for key in ['class-6-ally','class-6-enemy']:
 O=V/'deliverables'/key
 for i in [0,1,3,4,5]:shutil.copy2(P/f'deliverables/{key}/walk-{i:02}.png',O/f'walk-{i:02}.png')
 if key.endswith('enemy'):run(C/'walk-02.png','-fill','#AE5148','-opaque','#3976B5',O/'walk-02.png')
 else:shutil.copy2(C/'walk-02.png',O/'walk-02.png')
 for dst,src in [(6,2),(7,3)]:run(O/f'walk-{src:02}.png','-flop',O/f'walk-{dst:02}.png')
contact([V/f'deliverables/{key}/walk-{i:02}.png'for key in ['class-6-ally','class-6-enemy']for i in [2,3,6,7]],'standing-stride','4x2','128x96+8+8')

raw=V/'source/idle-key.png'
if raw.exists():
 b=bbox(raw);factor=64/(b[3]-b[1]);run(raw,'-filter','point','-resize',f'{factor*100}%',C/'idle-key-small.png');quant(C/'idle-key-small.png',C/'idle-key-color.png')
 a=Image.open(C/'idle-key-color.png').convert('RGBA');b=a.getbbox();feet=[(x,y) for y in range(b[3]-6,b[3])for x in range(a.width)if a.getpixel((x,y))[3]];cx=(min(x for x,y in feet)+max(x for x,y in feet))/2
 move(C/'idle-key-color.png','96x96',round(48-cx),80-b[3],L/'idle-key.png')
 run(L/'idle-key.png','-background','#d9d6c9','-alpha','remove','-filter','point','-resize','800%',V/'reviews/idle-key-8x.png')
 (C/'idle-registration.json').write_text(json.dumps({'scale':factor,'translation':[round(48-cx),80-b[3]]},indent=2)+'\n')

plate=V/'source/idle-plate.png'
if plate.exists():
 reg=json.loads((C/'idle-registration.json').read_text());factor=reg['scale'];dx,dy=reg['translation']
 run(plate,'-filter','point','-resize',f'{factor*100}%',C/'plate-small.png');quant(C/'plate-small.png',C/'plate-color.png');move(C/'plate-color.png','96x96',dx,dy,L/'idle-fixed.png')
 # Existing generated pixels only. Diagonal polygon selects the single shaft;
 # remove clothing colors from that weapon-only mask, not from body or hands.
 run(L/'idle-key.png','-region','20x20+67+10','-fill','#E4E1C8','-opaque','#DDA77D','-opaque','#3976B5','+region',L/'idle-key.png')
 run('-size','96x96','xc:black','-fill','white','-draw','polygon 22,74 26,74 74,26 70,26','-draw','rectangle 68,14 85,28','-alpha','off','-threshold','50%','-alpha','off',L/'shaft-region.png')
 run(L/'idle-key.png','-alpha','extract',L/'shaft-region.png','-compose','Multiply','-composite',L/'shaft-alpha.png')
 run(L/'idle-key.png',L/'shaft-alpha.png','-alpha','off','-compose','CopyOpacity','-composite','-transparent','#3976B5','-transparent','#DDA77D','-transparent','#E4E1C8',L/'shaft.png')
 run(L/'shaft.png','(',L/'idle-key.png','-crop','18x15+68+14','+repage',')','-geometry','+68+14','-compose','Over','-composite',L/'shaft.png')
 # Bare upper-right forearm/hand and its original outline form one rigid group.
 run('-size','96x96','xc:black','-fill','white','-draw','rectangle 54,39 66,52',L/'arm-region.png')
 run(L/'idle-key.png','-alpha','extract',L/'arm-region.png','-compose','Multiply','-composite',L/'arm-alpha.png')
 run(L/'idle-key.png',L/'arm-alpha.png','-alpha','off','-compose','CopyOpacity','-composite','-transparent','#3976B5','-transparent','#E4E1C8',L/'arm.png')
 run(L/'shaft.png',L/'arm.png','-compose','Over','-composite',L/'held-spear.png')
 # Fixed relaxed hand must remain in front if the tail passes its silhouette.
 run('-size','96x96','xc:black','-fill','white','-draw','rectangle 33,47 40,59',L/'free-hand-region.png')
 run(L/'idle-fixed.png','-alpha','extract',L/'free-hand-region.png','-compose','Multiply','-composite',L/'free-hand-alpha.png')
 run(L/'idle-fixed.png',L/'free-hand-alpha.png','-alpha','off','-compose','CopyOpacity','-composite',L/'free-hand.png')
 run(L/'idle-fixed.png','-crop','96x40+0+0','+repage',L/'head.png')
 for i,(sx,sy) in enumerate([(0,0),(-4,0),(-4,-4)]):
  move(L/'held-spear.png','96x96',sx,sy,L/f'held-spear-{i}.png')
  run(L/'idle-fixed.png',L/f'held-spear-{i}.png','-compose','Over','-composite',L/'free-hand.png','-compose','Over','-composite',L/'head.png','-geometry','+0+0','-compose','Over','-composite','-background','black','-alpha','background',C/f'idle-{i}.png')
 for key in ['class-6-ally','class-6-enemy']:
  O=V/'deliverables'/key
  for i,src in enumerate([0,1,2,1,0,1]):
   if key.endswith('enemy'):run(C/f'idle-{src}.png','-fill','#AE5148','-opaque','#3976B5',O/f'idle-{i:02}.png')
   else:shutil.copy2(C/f'idle-{src}.png',O/f'idle-{i:02}.png')
 contact([V/f'deliverables/{key}/idle-{i:02}.png'for key in ['class-6-ally','class-6-enemy']for i in [0,1,2]],'idle-stance','3x2','96x96+8+8')
 contact([L/'idle-fixed.png',L/'shaft.png',L/'arm.png',L/'held-spear.png'],'layers','4x1','96x96+8+8')
