# coding: utf-8
"""Take registered alpha measurements and create same-scale comparison cards."""
from pathlib import Path
from PIL import Image
import json, html, re
R=Path(__file__).resolve().parent;ROOT=R.parents[2];V2=R.parent/'puppet-trio-v2-20261105'
def open_rgba(p):return Image.open(p).convert('RGBA')
def crop(im):return im.crop(im.getbbox())
def game_asset(res):return ROOT/'actual'/res.removeprefix('res://')
def game_cell(p,frame):
 w,h=p['frame_size'];x,y=(frame%p['columns'])*w,(frame//p['columns'])*h
 return open_rgba(game_asset(p['path'])).crop((x,y,x+w,y+h))
def actual_pair(name):
 a=json.loads((ROOT/'actual/data'/name).read_text());m=a['maps']['intact'];return game_cell(m,m['native_cycle'][0]),game_cell(a['battle'],a['idle_frames']['intact'])
def puppet_pair(r,u,i):
 return tuple(open_rgba(r/f'assets/{u}-intact-{scene}-{j:02}.png') for scene,j in [('maps',i),('battle',0)])
soldier=(open_rgba(R/'assets/ally-map.png'),open_rgba(R/'assets/soldier-reference.png').resize((80,64),Image.Resampling.NEAREST))
units=[('soldier','枪兵基准',soldier,None),('water','水猴傀儡',actual_pair('mechanical_puppets_art.json'),None),('titan','伪泰坦傀儡',actual_pair('pseudo_titan_art.json'),None)]
for u,cn,v2,v3 in [('cyclops','独眼傀儡',16,16),('owl','飞枭傀儡',0,0),('prometheus','普罗米修斯',0,16)]:
 units.append((u,cn,puppet_pair(R,u,v3),puppet_pair(V2,u,v2)))
data={};cards=[]
for uid,name,pair,previous in units:
 state='V3预览' if previous else '实机参考' if uid!='soldier' else '同场基准'
 out=Image.new('RGB',(96,114),(28,44,53));out.paste((33,52,58),(0,0,96,54))
 metrics={}
 for scene,im,baseline in zip(['map','battle'],pair,[49,109]):
  unit=crop(im);out.paste(unit,((96-unit.width)//2,baseline-unit.height),unit)
  metrics[scene]=list(unit.size)
 f=R/'qa'/f'scale-{uid}.png';out.save(f,optimize=True)
 data[uid]={**metrics,'name':name,'before':{s:list(crop(im).size) for s,im in zip(['map','battle'],previous)} if previous else None,'asset':f.relative_to(R).as_posix(),'size':list(out.size),'bytes':f.stat().st_size}
 m,b=metrics['map'],metrics['battle']
 cards.append(f'<figure><img src="{f.relative_to(R).as_posix()}" width="96" height="114" alt="{html.escape(name)}的地图与战斗站姿"><figcaption><strong>{html.escape(name)}</strong><small>{state}</small><small>地图 {m[0]}×{m[1]}<br>战斗 {b[0]}×{b[1]}</small></figcaption></figure>')
section='''<section class="card" id="scale-review"><div class="heading"><h2>与枪兵的占位对照</h2><span>每张上方地图、下方战斗</span></div><p class="note">同一行的角色使用同一比例与脚底基线。尺寸只量可见轮廓，地图按2倍密度，战斗按1倍，分别与枪兵比较。飞枭只有翼尖稍宽。水猴和伪泰坦取现有实机素材，伪泰坦是当前已上线的机械单位里较大的一个。</p><div class="scale-grid">'''+''.join(cards)+'''</div><nav class="resources"><a href="qa/scale-measurements.json">上一版与本版实测</a><a href="../index.html?action=puppet-trio-cyclops-intact-aura#motion-player">回到 F25 治疗场景</a></nav></section>'''
page=R/'index.html';text=page.read_text();marker='<!-- SCALE REVIEW START -->'
if marker not in text:
 text=text.replace('<section class="card" id="native-review">',marker+'\n<!-- SCALE REVIEW END -->\n<section class="card" id="native-review">',1)
text=re.sub(re.escape(marker)+r'.*?<!-- SCALE REVIEW END -->',lambda _:marker+'\n'+section+'\n<!-- SCALE REVIEW END -->',text,flags=re.S)
page.write_text(text)
(R/'qa/scale-measurements.json').write_text(json.dumps({'scene_pixels':'map2x, battle1x; alpha bounds, standing or native initial pose; compare within each scene', 'units':data},ensure_ascii=False,indent=2)+'\n')
print({u:(d['map'],d['battle']) for u,d in data.items()})
