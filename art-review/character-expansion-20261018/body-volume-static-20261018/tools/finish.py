# -*- coding: utf-8 -*-
from pathlib import Path
from PIL import Image,ImageChops
import json,subprocess,hashlib
V=Path(__file__).resolve().parents[1];R=V.parent;G='/opt/homebrew/bin/magick';Q=V/'reviews';C=V/'candidates';FONT='/System/Library/Fonts/STHeiti Medium.ttc'
def run(*a):subprocess.run([G,*map(str,a)],check=True)
def banner(text,name,width=1280,fill='#e9f0f0'):
 run('-size',f'{width}x48','xc:#18232b','-font',FONT,'-pointsize','22','-fill',fill,'-gravity','center','-annotate','+0+0',text,C/name)
for version in ['current','sample']:
 run(Q/f'lineup-{version}.png','-crop','640x128+564+288','+repage','-filter','point','-resize','200%',Q/f'lineup-{version}-detail.png')
banner('当前版 · 男主作为尺度参照','current-title.png');banner('静态样板 · 增厚身体＋整体放大约 6% · 男主不变','sample-title.png',fill='#a8d6c8')
labels=['友军弓箭手','友军枪兵','男主（保持原样）','敌军弓箭手','敌军枪兵']
for i,label in enumerate(labels):banner(label,f'label-{i}.png',256)
run(*[C/f'label-{i}.png'for i in range(5)],'+append',C/'labels.png')
run(C/'current-title.png',C/'labels.png',Q/'lineup-current-detail.png',C/'sample-title.png',C/'labels.png',Q/'lineup-sample-detail.png','-append',Q/'comparison.png')
for p in [*Q.glob('*.png'),*C.glob('*title.png'),C/'labels.png']:
 subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(p)],check=True)
# Verify real-scene captures differ only inside the four temporary sprite slots.
a=Image.open(Q/'lineup-current.png').convert('RGB');b=Image.open(Q/'lineup-sample.png').convert('RGB')
assert a.crop((836,304,932,400)).tobytes()==b.crop((836,304,932,400)).tobytes()
diff=ImageChops.difference(a,b);allowed=[(x-48,304,x+48,400)for x in [628,756,1012,1140]]
changes=0;outside=0
for i,c in enumerate(diff.getdata()):
 if c!=(0,0,0):
  changes+=1;x=i%a.width;y=i//a.width
  if not any(l<=x<r and t<=y<bt for l,t,r,bt in allowed):outside+=1
assert changes>0 and outside==0,(changes,outside)
baseline=json.loads((V/'source/unchanged-baseline.json').read_text());assert all(hashlib.sha256((R.parent.parent/p).read_bytes()).hexdigest()==sha for p,sha in baseline.items())
assets=[]
for p in [*V.joinpath('deliverables').glob('*.png'),*Q.glob('*.png')]:
 im=Image.open(p);assets.append({'path':str(p.relative_to(V)),'size':list(im.size),'bytes':p.stat().st_size,'use':'static sprite'if p.parent.name=='deliverables' else 'comparison / actual-map screenshot','size_note':'Lossless compression; preserve actual screenshot resolution and map texture.'if p.stat().st_size>=200000 else ''})
(V/'verification.json').write_text(json.dumps({'passed':True,'capture':json.loads((V/'capture.json').read_text()),'hero_pixels_identical':True,'changed_scene_pixels':changes,'pixels_changed_outside_four_samples':outside,'runtime_and_existing_gallery_files_unchanged':len(baseline),'scope':'Four static candidate sprites only; no animation expansion or game integration.','assets':assets},ensure_ascii=False,indent=2)+'\n')
print('Verified unchanged hero, actual-map background, runtime and existing review assets:',len(baseline))
