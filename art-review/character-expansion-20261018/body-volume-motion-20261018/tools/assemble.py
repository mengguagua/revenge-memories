# -*- coding: utf-8 -*-
"""Registered ImageGen body revisions with fixed-region motion composition."""
from pathlib import Path
from PIL import Image
import subprocess,json,shutil
V=Path(__file__).resolve().parents[1];R=V.parent;S=R/'body-volume-static-20261018';C=V/'candidates';L=V/'layers';G='/opt/homebrew/bin/magick';REF=json.loads((V/'source/references.json').read_text())
def run(*a):subprocess.run([G,*map(str,a)],check=True)
def quant(src,dst):
 run(src,'-alpha','extract','-threshold','50%',C/'alpha.png')
 run(src,'-background','#172638','-alpha','remove','-alpha','off','-dither','None','-remap',R/'archer-spearman-map-review-20261018/candidates/class-6-ally/palette.png',C/'rgb.png')
 run(C/'rgb.png',C/'alpha.png','-alpha','off','-compose','CopyOpacity','-composite','-background','black','-alpha','background',dst)
def move(src,size,dx,dy,dst):run('-size',f'{size[0]}x{size[1]}','xc:none',src,'-geometry',f'{dx:+d}{dy:+d}','-compose','Over','-composite','-background','black','-alpha','background',dst)
def rect(base,src,box,dst):
 x,y,r,b=box;run(base,'(',src,'-crop',f'{r-x}x{b-y}+{x}+{y}','+repage',')','-geometry',f'+{x}+{y}','-define','compose:outside-overlay=false','-compose','Src','-composite',dst)
def mask_rect(size,box,dst):
 x,y,r,b=box;run('-size',f'{size[0]}x{size[1]}','xc:black','-fill','white','-draw',f'rectangle {x},{y} {r-1},{b-1}','-alpha','off',dst)
def layer(src,mask,dst):
 run(src,'-alpha','extract',mask,'-alpha','off','-compose','Multiply','-composite',C/'mask-alpha.png')
 run(src,C/'mask-alpha.png','-alpha','off','-compose','CopyOpacity','-composite','-background','black','-alpha','background',dst)
def replace_mask(base,src,mask,dst):
 run(mask,'-negate',C/'inverse.png');layer(base,C/'inverse.png',C/'base-part.png');layer(src,mask,C/'source-part.png');run(C/'base-part.png',C/'source-part.png','-compose','Over','-composite',dst)
def scaled(src,dst,walk=False):
 run(src,'-filter','point','-resize','136x102!'if walk else'102x102!',C/'scaled.png');move(C/'scaled.png',(128,96)if walk else(96,96),-4 if walk else -3,-6 if walk else -5,dst)
def contact(files,name,tile='4x3',geometry='128x96+8+8'):
 run('montage','-font','/System/Library/Fonts/STHeiti Medium.ttc',*files,'-tile',tile,'-geometry',geometry,'-background','#d9d6c9',V/f'reviews/{name}.png');run(V/f'reviews/{name}.png','-filter','point','-resize','400%',V/f'reviews/{name}-4x.png')
qa={}
for kind,cid in [('archer',12),('spearman',6)]:
 old=REF[kind]['ally']['tactical-walk'];raw=V/f'source/{kind}-walk-generated.png'
 # A common sheet scale; extra row padding retains feet that overhang a cell.
 run(raw,'-filter','point','-resize','256x288!',C/f'{kind}-sheet.png')
 for n in range(6):
  row=n//2;col=n%2;run(C/f'{kind}-sheet.png','-crop',f'128x{min(104,288-row*96)}+{col*128}+{row*96}','+repage',C/'cell.png');quant(C/'cell.png',C/'colored.png')
  b=Image.open(C/'colored.png').convert('RGBA').getbbox();move(C/'colored.png',(128,96),0,96-b[3],C/f'{kind}-walk-{n}.png')
 # Restore the accepted head and face at the source joint coordinates, all pairs.
 heads={'archer':[(42,25,84,55),(54,25,96,55),(48,25,87,56)],'spearman':[(50,27,80,54),(48,25,80,55),(50,26,81,58)]}[kind]
 for n in range(6):rect(C/f'{kind}-walk-{n}.png',R/old['newFrames'][str((n//2)*2)],heads[n//2],C/f'{kind}-walk-{n}.png')
 if kind=='archer':
  for n,box,name in [(0,(43,78,83,96),'up'),(2,(46,79,95,96),'right'),(4,(45,78,83,96),'down')]:
   mask_rect((128,96),box,L/f'archer-legs-{name}.png')
   if name!='up':
    weapon=R/f'archer-arms-step-v3-20261018/layers/weapon-{name}.png'
    run(weapon,'-alpha','extract','-alpha','off','-morphology','Dilate','Diamond:1','-negate',C/'weapon-inverse.png')
    run(L/f'archer-legs-{name}.png',C/'weapon-inverse.png','-compose','Multiply','-composite',L/f'archer-legs-{name}.png')
   replace_mask(C/f'{kind}-walk-{n}.png',C/f'{kind}-walk-{n+1}.png',L/f'archer-legs-{name}.png',C/f'{kind}-walk-{n+1}.png')
  # Preserve the accepted downward drawing-hand over the bowstring.
  for n in [4,5]:run(C/f'{kind}-walk-{n}.png',R/'archer-arms-step-v3-20261018/layers/drawing-down.png','-compose','Over','-composite',C/f'{kind}-walk-{n}.png')
 else:
  for n,box in [(0,(57,55,73,77)),(2,(55,55,72,78)),(4,(57,59,72,78))]:rect(C/f'{kind}-walk-{n+1}.png',C/f'{kind}-walk-{n}.png',box,C/f'{kind}-walk-{n+1}.png')
 for n in range(6):scaled(C/f'{kind}-walk-{n}.png',V/f'deliverables/class-{cid}-ally/walk-{n:02}.png',True)
 # Build idle from the exact approved unscaled first pose, with local generated
 # underpaint used only beneath its moving pixels. This makes pose0 exact.
 base=S/f'candidates/{kind}-body.png';run(V/f'source/{kind}-idle-plate.png','-filter','point','-resize','96x96!',C/'plate.png');quant(C/'plate.png',L/f'{kind}-plate.png')
 if kind=='archer':
  run(R/'archer-arms-step-v3-20261018/layers/assembly-idle.png','-alpha','extract','-alpha','off','-morphology','Dilate','Diamond:2',L/f'{kind}-motion-mask.png')
  # Expanded forearm silhouette in the approved thick drawing.
  run(L/f'{kind}-motion-mask.png','-fill','white','-draw','rectangle 27,44 46,56','-draw','rectangle 47,34 67,49','-alpha','off',L/f'{kind}-motion-mask.png')
  offsets=[(0,0),(0,0),(0,4)];aliases=[0,0,2,0,0,0]
 else:
  run(R/'spearman-stance-v3-20261018/layers/held-spear.png','-alpha','extract','-alpha','off','-morphology','Dilate','Diamond:1',L/f'{kind}-motion-mask.png')
  run(L/f'{kind}-motion-mask.png','-fill','white','-draw','rectangle 53,38 68,53','-alpha','off',L/f'{kind}-motion-mask.png')
  offsets=[(0,0),(-4,0),(-4,-4)];aliases=[0,1,2,1,0,1]
 # Do not move fixed clothing pixels accidentally included by mask expansion.
 # Colors of head/torso are protected except the archer's small arm sleeve.
 a=Image.open(base).convert('RGBA');m=Image.open(L/f'{kind}-motion-mask.png').convert('L')
 # Create only a selector mask from existing generated colors (no painted art).
 # PNG writing below is analysis mask data; all sprite composition is ImageMagick.
 from PIL import ImageDraw
 protect=Image.new('L',(96,96),255);pd=ImageDraw.Draw(protect)
 if kind=='spearman':
  for y in range(96):
   for x in range(96):
    c=a.getpixel((x,y))
    if c[:3]==(57,118,181) or (c[:3]==(228,225,200) and y>=30) or (c[:3]==(221,167,125) and y<40):protect.putpixel((x,y),0)
  pd.rectangle((33,47,40,59),fill=0)
 else:
  for y in range(45):
   for x in range(96):
    c=a.getpixel((x,y))[:3]
    if c==(57,118,181) or (c==(221,167,125) and x<46):protect.putpixel((x,y),0)
 protect.save(C/'protect-mask.png')
 run(L/f'{kind}-motion-mask.png',C/'protect-mask.png','-compose','Multiply','-composite','-threshold','50%','-alpha','off',L/f'{kind}-motion-mask.png')
 layer(base,L/f'{kind}-motion-mask.png',L/f'{kind}-moving.png')
 run(base,'-alpha','extract',L/f'{kind}-motion-mask.png','-alpha','off','-compose','Multiply','-composite',L/f'{kind}-underpaint-mask.png')
 replace_mask(base,L/f'{kind}-plate.png',L/f'{kind}-underpaint-mask.png',L/f'{kind}-fixed.png')
 for n,(dx,dy) in enumerate(offsets):
  move(L/f'{kind}-moving.png',(96,96),dx,dy,L/f'{kind}-moving-{n}.png');run(L/f'{kind}-fixed.png',L/f'{kind}-moving-{n}.png','-compose','Over','-composite',C/f'{kind}-idle-{n}.png')
 # Keep the free hand and its immediate outline intact where the spear crosses.
 if kind=='spearman':
  hand=Image.new('L',(96,96),0)
  for y in range(49,60):
   for x in range(33,44):
    if a.getpixel((x,y))==(221,167,125,255):hand.putpixel((x,y),255)
  hand.save(C/'free-hand-mask.png');run(C/'free-hand-mask.png','-morphology','Dilate','Diamond:1','-alpha','off',C/'free-hand-mask.png')
  layer(base,C/'free-hand-mask.png',L/'spearman-free-hand.png')
  for n in range(3):run(C/f'{kind}-idle-{n}.png',L/'spearman-free-hand.png','-compose','Over','-composite',C/f'{kind}-idle-{n}.png')
 # Pose0 must reconstruct exactly before scaling; protect user-approved baseline.
 assert Image.open(C/f'{kind}-idle-0.png').convert('RGBA').tobytes()==a.tobytes(),kind
 for n,src in enumerate(aliases):scaled(C/f'{kind}-idle-{src}.png',V/f'deliverables/class-{cid}-ally/idle-{n:02}.png')
 expected=Image.open(S/f'deliverables/{kind}-ally.png').convert('RGBA');assert Image.open(V/f'deliverables/class-{cid}-ally/idle-00.png').convert('RGBA').tobytes()==expected.tobytes()
 for side in ['ally','enemy']:
  O=V/f'deliverables/class-{cid}-{side}'
  if side=='enemy':
   for typ,count in [('walk',6),('idle',6)]:
    for n in range(count):run(V/f'deliverables/class-{cid}-ally/{typ}-{n:02}.png','-fill','#AE5148','-opaque','#3976B5',O/f'{typ}-{n:02}.png')
  for dst,src in [(6,2),(7,3)]:run(O/f'walk-{src:02}.png','-flop',O/f'walk-{dst:02}.png')
  contact([O/f'walk-{n:02}.png'for n in range(8)]+[O/f'idle-{n:02}.png'for n in [0,1,2]],f'class-{cid}-{side}')
 qa[kind]={'idle_offsets_before_scale':offsets,'idle_aliases':aliases,'accepted_pose0_exact':True,'scale':1.0625,'foot_anchor_idle':[48,80],'foot_anchor_walk':[64,96]}
(V/'assembly.json').write_text(json.dumps(qa,indent=2)+'\n')
