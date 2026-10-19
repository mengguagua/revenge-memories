from pathlib import Path
from PIL import Image
import json,subprocess
V=Path(__file__).resolve().parents[1];R=V.parent;OLD=R/'mercenary-map-review-20261019';G='/opt/homebrew/bin/magick';C=V/'candidates'
def run(*a):subprocess.run([G,*map(str,a)],check=True)
def sha(p):
 import hashlib
 return hashlib.sha256(p.read_bytes()).hexdigest()
run(V/'source/eyes-generated.png','-filter','point','-resize','72x64!',C/'sheet.png')
run('xc:#172638','xc:#DDA77D','+append',C/'face-palette.png')
records=json.loads((V/'source/face-regions.json').read_text());checks=[]
for n,rec in enumerate(records):
 name=rec['name'];hx,hy,_,_=rec['head_crop'];x,y,r,b=rec['edit_region'];w=r-x;h=b-y
 run(C/'sheet.png','-crop',f'36x32+{n%2*36}+{n//2*32}','+repage',C/f'{name}-head.png')
 run(C/f'{name}-head.png','-crop',f'{w}x{h}+{x-hx}+{y-hy}','+repage','-alpha','remove','-alpha','off','-dither','None','-remap',C/'face-palette.png',C/f'{name}-patch.png')
 slots=range(6)if name=='idle'else {'right':[2,3],'down':[4,5],'left':[6,7]}[name];typ='idle'if name=='idle'else'walk'
 for side in ['ally','enemy','neutral']:
  for slot in slots:
   p=V/f'deliverables/class-8-{side}/{typ}-{slot:02}.png';old=OLD/f'deliverables/class-8-{side}/{typ}-{slot:02}.png'
   run(old,C/f'{name}-patch.png','-geometry',f'+{x}+{y}','-define','compose:outside-overlay=false','-compose','Src','-composite',p)
   run(old,'-alpha','extract',C/'original-alpha.png');run(p,C/'original-alpha.png','-alpha','off','-compose','CopyOpacity','-composite','-background','black','-alpha','background',p)
   a=Image.open(old).convert('RGBA');q=Image.open(p).convert('RGBA');diff=[(xx,yy)for yy in range(a.height)for xx in range(a.width)if a.getpixel((xx,yy))!=q.getpixel((xx,yy))]
   assert diff and all(x<=xx<r and y<=yy<b for xx,yy in diff),(name,side,slot,[(xx,yy)for xx,yy in diff if not(x<=xx<r and y<=yy<b)][:8]);assert a.getchannel('A').tobytes()==q.getchannel('A').tobytes(),(name,side,slot,'alpha')
   # Eyes are dark components enclosed by skin, separated from the hair mass.
   dark={(xx,yy)for yy in range(y,b)for xx in range(x,r)if q.getpixel((xx,yy))[:3]==(23,38,56)};components=[]
   while dark:
    pending=[dark.pop()];group=set(pending)
    while pending:
     xx,yy=pending.pop()
     for nb in [(xx+1,yy),(xx-1,yy),(xx,yy+1),(xx,yy-1)]:
      if nb in dark:dark.remove(nb);group.add(nb);pending.append(nb)
    if len(group)>=2 and max(yy for xx,yy in group)>min(yy for xx,yy in group) and not any(xx in[x,r-1]or yy in[y,b-1]for xx,yy in group):components.append(sorted(group))
   expected=2 if name in ['idle','down']else 1
   assert len(components)==expected,(name,side,slot,components)
   checks.append({'side':side,'kind':typ,'slot':slot,'changed_pixels':len(diff),'edit_region':rec['edit_region'],'isolated_eyes':len(components),'eye_pixels':components,'outside_face_rgba_unchanged':True,'alpha_unchanged':True})
for side in ['ally','enemy','neutral']:
 O=V/f'deliverables/class-8-{side}'
 for slot in [0,1]:assert sha(O/f'walk-{slot:02}.png')==sha(OLD/f'deliverables/class-8-{side}/walk-{slot:02}.png')
 for typ,count in [('walk',8),('idle',6)]:run(*[O/f'{typ}-{i:02}.png'for i in range(count)],'+append',O/f'{typ}-atlas.png')
 run('montage','-font','/System/Library/Fonts/STHeiti Medium.ttc',*[O/f'walk-{i:02}.png'for i in range(8)],*[O/f'idle-{i:02}.png'for i in [0,1,2]],'-tile','4x3','-geometry','128x96+8+8','-background','#d9d6c9',V/f'reviews/{side}-contact.png');run(V/f'reviews/{side}-contact.png','-filter','point','-resize','400%',V/f'reviews/{side}-contact-4x.png')
# Unaltered head silhouette and no palette expansion.
(V/'eye-verification.json').write_text(json.dumps({'passed':True,'checks':checks,'back_view_exactly_unchanged':True,'runtime_integrated':False},indent=2)+'\n')
