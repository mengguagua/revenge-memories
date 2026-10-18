# -*- coding: utf-8 -*-
"""Prepare static ImageGen edits; retain original heads and register at fixed feet."""
from pathlib import Path
from PIL import Image
import json,subprocess,shutil,hashlib
V=Path(__file__).resolve().parents[1];R=V.parent;C=V/'candidates';O=V/'deliverables';G='/opt/homebrew/bin/magick';refs=json.loads((V/'source/references.json').read_text())
def run(*a):subprocess.run([G,*map(str,a)],check=True)
def quant(src,dst):
 run(src,'-alpha','extract','-threshold','50%',C/'alpha.png')
 run(src,'-background','#172638','-alpha','remove','-alpha','off','-dither','None','-remap',R/'archer-spearman-map-review-20261018/candidates/class-6-ally/palette.png',C/'rgb.png')
 run(C/'rgb.png',C/'alpha.png','-alpha','off','-compose','CopyOpacity','-composite','-background','black','-alpha','background',dst)
report=[]
for kind,head in [('archer',(19,23,45,47)),('spearman',(35,17,61,40))]:
 raw=V/f'source/{kind}-generated.png';run(raw,'-filter','point','-resize','96x96!',C/f'{kind}-small.png');quant(C/f'{kind}-small.png',C/f'{kind}-body.png')
 old=R/refs[kind+'-ally']['frame'];x,y,r,b=head
 # Head identity remains the accepted original; body comes from the generated edit.
 run(C/f'{kind}-body.png','(',old,'-crop',f'{r-x}x{b-y}+{x}+{y}','+repage',')','-geometry',f'+{x}+{y}','-define','compose:outside-overlay=false','-compose','Src','-composite',C/f'{kind}-body.png')
 # 102/96 = 1.0625. Register the unchanged native foot anchor (48,80).
 run(C/f'{kind}-body.png','-filter','point','-resize','102x102',C/f'{kind}-scaled.png')
 run('-size','96x96','xc:none',C/f'{kind}-scaled.png','-geometry','-3-5','-compose','Over','-composite','-background','black','-alpha','background',O/f'{kind}-ally.png')
 run(O/f'{kind}-ally.png','-fill','#AE5148','-opaque','#3976B5',O/f'{kind}-enemy.png')
 for side in ['ally','enemy']:
  name=kind+'-'+side;p=O/f'{name}.png';original=R/refs[name]['frame'];shutil.copy2(original,O/f'{name}-before.png')
  subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(p)],check=True)
  a=Image.open(p).convert('RGBA');before=Image.open(original).convert('RGBA');assert a.size==(96,96);assert set(a.getchannel('A').getdata())=={0,255};assert len({c for c in a.getdata()if c[3]})==4
  assert a.getbbox()[0]>0 and a.getbbox()[1]>0 and a.getbbox()[2]<96 and a.getbbox()[3]<96
  color=(57,118,181)if side=='ally'else(174,81,72)
  count=lambda im:sum(c[3]>0 and c[:3] in [color,(221,167,125)]for c in im.getdata())
  report.append({'name':name,'size':[96,96],'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'scale':1.0625,'foot_anchor':[48,80],'before_bounds':list(before.getbbox()),'after_bounds':list(a.getbbox()),'before_blue_or_red_and_skin_pixels':count(before),'after_blue_or_red_and_skin_pixels':count(a),'note':'Color-area metric excludes weapon ivory/navy; diagnostic only, not a visual acceptance result.'})
shutil.copy2(R/refs['hero']['frame'],O/'hero.png')
for theme,bg in [('light','#d9d6c9'),('dark','#26343b')]:
 files=[]
 for suffix in ['-before','']:
  files.extend([O/('hero.png' if name=='hero'else name+suffix+'.png')for name in ['archer-ally','spearman-ally','hero','archer-enemy','spearman-enemy']])
 run('montage','-font','/System/Library/Fonts/STHeiti Medium.ttc',*files,'-tile','5x2','-geometry','96x96+8+8','-background',bg,V/f'reviews/lineup-{theme}.png')
 run(V/f'reviews/lineup-{theme}.png','-filter','point','-resize','300%',V/f'reviews/lineup-{theme}-3x.png')
(V/'image-inventory.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
