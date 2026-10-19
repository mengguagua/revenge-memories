from pathlib import Path
from PIL import Image
import json,subprocess
V=Path(__file__).resolve().parents[1];R=V.parent;G='/opt/homebrew/bin/magick';C=V/'candidates';L=V/'layers';PAL=R/'archer-spearman-map-review-20261018/candidates/class-6-ally/palette.png'
def run(*x):subprocess.run([G,*map(str,x)],check=True)
def quant(src,out):
 run(src,'-alpha','extract','-threshold','65%',C/'alpha.png');run(src,'-background','#172638','-alpha','remove','-alpha','off','-dither','None','-remap',PAL,C/'rgb.png');run(C/'rgb.png',C/'alpha.png','-alpha','off','-compose','CopyOpacity','-composite','-background','black','-alpha','background',out)
def place(src,size,dx,dy,out):run('-size',f'{size[0]}x{size[1]}','xc:none',src,'-geometry',f'{dx:+d}{dy:+d}','-compose','Over','-composite','-background','black','-alpha','background',out)
def rect(base,src,b,out):
 x,y,r,t=b;run(base,'(',src,'-crop',f'{r-x}x{t-y}+{x}+{y}','+repage',')','-geometry',f'+{x}+{y}','-define','compose:outside-overlay=false','-compose','Src','-composite',out)
def mask(src,selector,out):
 run(src,'-alpha','extract',selector,'-alpha','off','-compose','Multiply','-composite',C/'am.png');run(src,C/'am.png','-alpha','off','-compose','CopyOpacity','-composite','-background','black','-alpha','background',out)
def normalize(name,cols,rows,scale,specs):
 raw=V/f'source/{name}.png';im=Image.open(raw);cw=im.width//cols;ch=im.height//rows
 for slot,cell,hbox in specs:
  x=cell%cols*cw;y=cell//cols*ch;run(raw,'-crop',f'{cw}x{ch}+{x}+{y}','+repage',C/'rawcell.png');quant(C/'rawcell.png',C/'qcell.png')
  q=Image.open(C/'qcell.png').convert('RGBA');bbox=q.getbbox();bx=q.crop(hbox).getbbox();hx=hbox[0]+(bx[0]+bx[2])/2
  kind='idle'if slot.startswith('idle')else'walk';size=(96,96)if kind=='idle'else(128,96);foot=80 if kind=='idle'else 96;cx=48 if kind=='idle'else 64
  nw=round(cw*scale);nh=round(ch*scale);run(C/'qcell.png','-filter','point','-resize',f'{nw}x{nh}!',C/'sized.png');dx=round(cx-hx*scale);dy=round(foot-bbox[3]*scale);place(C/'sized.png',size,dx,dy,C/f'{slot}.png');records[slot]={'source':name,'cell':cell,'scale':scale,'head_crop':hbox,'offset':[dx,dy],'bounds':Image.open(C/f'{slot}.png').getbbox()}
records={}
normalize('walk-generated-v1',4,2,.198,[('walk-0',0,(100,190,235,275)),('walk-1',1,(100,190,235,275)),('walk-4',4,(90,78,235,160)),('walk-5',5,(90,78,235,160)),('walk-6',2,(90,195,240,280)),('walk-7',3,(90,195,240,280))])
normalize('right-generated-v2',2,1,.111,[('walk-2',0,(520,150,790,280)),('walk-3',1,(350,150,620,280))])
normalize('idle-generated-v1',3,1,.129,[('idle-0',0,(300,170,550,270)),('idle-1',1,(270,170,520,270)),('idle-2',2,(220,170,480,270))])
# Alternate the back-view support leg with the already generated leg layer.
run(C/'walk-0.png','-flop',C/'up-leg-flip.png');place(C/'up-leg-flip.png',(128,96),5,0,C/'up-leg-flip.png');rect(C/'walk-1.png',C/'up-leg-flip.png',(0,78,128,96),C/'walk-1.png')
# Native side views keep the upright blade registered; do not move it with legs.
rect(C/'walk-3.png',C/'walk-2.png',(32,0,54,68),C/'walk-3.png')
rect(C/'walk-7.png',C/'walk-6.png',(45,0,61,68),C/'walk-7.png')
# Keep only one head image in each phase pair; no mirrored derivatives.
for a,b in [(0,1),(2,3),(4,5),(6,7)]:rect(C/f'walk-{b}.png',C/f'walk-{a}.png',(49,26,81,54),C/f'walk-{b}.png')
# Hold the idle body constant. Sword and holding forearm occupy left of x34;
# source differences are local, never a whole-body displacement.
run('-size','96x96','xc:black','-fill','white','-draw','polygon 0,0 35,0 35,35 41,38 41,47 36,52 0,52','-threshold','50%','-alpha','off',L/'idle-moving-mask.png')
run(L/'idle-moving-mask.png','-negate',L/'idle-fixed-mask.png');mask(C/'idle-0.png',L/'idle-fixed-mask.png',L/'idle-fixed.png')
for i in range(3):
 mask(C/f'idle-{i}.png',L/'idle-moving-mask.png',L/f'idle-moving-{i}.png')
 if i==2:place(L/f'idle-moving-{i}.png',(96,96),2,0,L/f'idle-moving-{i}.png')
 run(L/'idle-fixed.png',L/f'idle-moving-{i}.png','-compose','Over','-composite',C/f'idle-{i}.png')
for side,color in [('ally','#3976B5'),('enemy','#AE5148'),('neutral','#8F986F')]:
 O=V/f'deliverables/class-8-{side}';O.mkdir(parents=True,exist_ok=True)
 for typ,count in [('walk',8),('idle',6)]:
  for i in range(count):
   src=i if typ=='walk'else[0,1,2,1,0,1][i];p=O/f'{typ}-{i:02}.png';run(C/f'{typ}-{src}.png','-fill',color,'-opaque','#3976B5',p)
  run(*[O/f'{typ}-{i:02}.png'for i in range(count)],'+append',O/f'{typ}-atlas.png')
 run('montage','-font','/System/Library/Fonts/STHeiti Medium.ttc',*[O/f'walk-{i:02}.png'for i in range(8)],*[O/f'idle-{i:02}.png'for i in [0,1,2]],'-tile','4x3','-geometry','128x96+8+8','-background','#d9d6c9',V/f'reviews/{side}-contact.png');run(V/f'reviews/{side}-contact.png','-filter','point','-resize','400%',V/f'reviews/{side}-contact-4x.png')
(V/'registration.json').write_text(json.dumps(records,indent=2)+'\n')
