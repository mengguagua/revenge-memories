#!/usr/bin/env python3
"""Add the reviewed stone-wing entry, retaining other artists' live content."""
import hashlib,json,re
from urllib.parse import urlsplit
from PIL import Image
import integrate_stone_wing_v1 as I
ROOT=I.ROOT;OUT=I.OUT;REV=I.A.REV
def main():
 d=I.build();v=I.verify(d);ex=json.loads((OUT/'export-report.json').read_text());assert len(ex['decoded_videos'])==22
 for a in d['actions']:
  assert a['video']and a['still']
  if a['kind']=='attack':assert a['closeVideo']
 I.merge(d);live=json.loads((ROOT/'demos/gallery-data.json').read_text());ids={a['id']for a in live['actions']};page=ROOT/'index.html';old=page.read_text();default=re.search(r'data-default-action="([^"]+)"',old).group(1)
 nav=lambda items:''.join('<a href="'+href+'">'+name+'</a>'for name,href in items)
 actions=[('地图待机','maps-tactical-idle--idle-cycle'),('向上行走','maps-tactical-walk--walk-up'),('向右行走','maps-tactical-walk--walk-right'),('向下行走','maps-tactical-walk--walk-down'),('向左行走','maps-tactical-walk--walk-left'),('裂石爪','battle--stone-claw'),('碎岩喷吐','battle--stone-spit'),('远距喷吐','battle--stone-spit-far'),('外传节奏对照','battle--original_class_3_enemy_normal'),('战斗待机','battle--idle'),('受击','battle--hit'),('未命中','battle--miss'),('退场','battle--exit'),('厚石甲变体','battle--thick-stone')]
 links=[(name,'?action=professions-class-3-enemy-'+key+'#motion-player')for name,key in actions];files=[('地图全姿势',REV+'/maps-light.png'),('战斗全姿势',REV+'/battle-light.png'),('连续帧检查',REV+'/decoded-actions.png'),('制作与触发对应记录',REV+'/README.md')]
 section='<section class="panel" id="stone-wing-progress" aria-label="敌方石翼兽全动作" style="margin-bottom:24px">\n<div class="heading"><h2>石翼兽 · 全动作</h2><p>柔和蓝紫石甲 · 待验收</p></div>\n<p class="action-note" style="margin:0 0 16px">沿用本篇四足石翼兽：角状石首、四爪、蝠翼和长石尾。待机与行走固定头胸基准，保留外传展翼／收翼的顺序与节奏；战斗补全振翼、收身、伸爪、回收。裂石爪与碎岩喷吐各只有一次命中，碎岩只作接触反馈；原作208帧节奏另设对照入口。</p>\n<nav class="links" aria-label="石翼兽动作入口">'+nav(links)+'</nav>\n<nav class="links" aria-label="石翼兽姿势检查" style="margin-top:14px">'+nav(files)+'</nav>\n</section>'
 for name,href in links+files:
  u=urlsplit(href)
  if u.query:assert u.query.removeprefix('action=')in ids
  else:assert(ROOT/u.path).is_file(),href
 m=re.search(r'<section\b[^>]*id="stone-wing-progress".*?</section>',old,re.S)
 if m:new=old[:m.start()]+section+old[m.end():]
 else:
  m=re.search(r'<section\b[^>]*id="divine-body-progress"',old);assert m;new=old[:m.start()]+section+'\n\n'+old[m.start():]
 new=re.sub(r'&stone_wing=[^"&]+','',new);new=re.sub(r'(src="gallery-data\.js\?[^"]*)"',lambda m:m.group(1)+'&stone_wing=full-v1-20261024"',new,count=1);assert re.search(r'data-default-action="([^"]+)"',new).group(1)==default
 assert page.read_text()==old,'Concurrent page writer; retry latest';page.write_text(new)
 cp=ROOT/'healer-saint-complete-v1-20261023/profession-catalog-sync.json';catalog=json.loads(cp.read_text());entry=next(c for c in catalog['classes']if c['class_id']==3);entry['gallery_coverage']['enemy']={'tactical-idle':'professions-class-3-enemy-maps-tactical-idle--idle-cycle','tactical-walk':'professions-class-3-enemy-maps-tactical-walk--walk-up','battle':'professions-class-3-enemy-battle--stone-claw'};entry.update(enemy_art_revision=REV,enemy_identity='四足石翼兽；裂石爪与明确配置变体的碎岩喷吐，蓝紫哑光石甲',enemy_review_actions=18);I.A.write(cp,catalog)
 allpng=list(OUT.rglob('*.png'))+[ROOT/'demos/stills'/(a['id']+suffix+'.png')for a in d['actions']for suffix in(['','--close']if a['kind']=='attack'else[''])];inventory=[]
 for p in sorted(set(allpng)):
  size=list(Image.open(p).size);source='source'in p.relative_to(OUT).parts if p.is_relative_to(OUT)else False;purpose='offline generated source/native reference'if source else'character frame'if p.parent.name in['battle','tactical-idle','tactical-walk']else'effect bitmap'if p.parent.name=='effects'else'lossless comparison/export/atlas';row={'path':p.relative_to(ROOT).as_posix(),'size':size,'bytes':p.stat().st_size,'sha256':I.S.sha(p),'purpose':purpose,'source_only':source}
  if source:row['quality_reason']='Original generation or native source retained offline; not loaded as a character.'
  elif p.stat().st_size>=50000:row['quality_reason']='Combined atlas or offline comparison retains complete poses and readable labels; player loads small independent character frames.'
  inventory.append(row)
 I.A.write(OUT/'delivery-image-inventory.json',{'revision':REV,'images':inventory})
 I.A.write(OUT/'completion.json',{'revision':REV,'status':'review_candidate','profiles':3,'actions':18,'decoded_videos':22,'native_flight_attack_frames':208,'native_contact_tick':103,'innate_claw_frames':46,'innate_claw_contact_tick':26,'innate_spit_frames':54,'innate_spit_contact_tick':34,'no_extra_hits':True,'latest_live_unrelated_rows_preserved':True,'page_default_preserved':default,'runtime_integrated':False,'device_updated':False,'browser_visual_check':'file access unavailable; offline compositing and encoded-video decoding only'})
 print(json.dumps({'profiles':3,'actions':18,'videos':22,'images':len(inventory),'page_default_preserved':default}),flush=True)
if __name__=='__main__':main()
