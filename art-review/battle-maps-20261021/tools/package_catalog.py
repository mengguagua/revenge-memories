#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate and bundle the offline map review, without touching runtime game files."""
from pathlib import Path
from PIL import Image
import hashlib,json,re,zipfile
OUT=Path(__file__).resolve().parents[1]
data=json.loads((OUT/'maps-data.js').read_text().removeprefix('window.MAP_CATALOG=').rstrip(';\n'))
manifest=json.loads((OUT/'manifest.json').read_text())
errors=[];warnings=[];checks=0
def check(ok,message):
 global checks
 checks+=1
 if not ok:errors.append(message)
check(len(data['maps'])==40,'地图数量不是40')
check([sum(m['chapter']==c for m in data['maps'])for c in range(1,6)]==[7,8,8,10,7],'章节数量不一致')
for m in data['maps']:
 code=m['code'];w,h=m['size']
 def inside(p):return len(p)==2 and 0<=p[0]<w and 0<=p[1]<h
 check(len(m['terrain_indices'])==w*h,f'{code}网格不完整')
 check(all(0<=i<len(m['terrain'])for i in m['terrain_indices']),f'{code}地形索引无效')
 check(bool(m['conditions']) and bool(m['story']) and bool(m['next']),f'{code}说明缺失')
 for key in ['image','thumbnail','source']:check((OUT/m[key]).is_file(),f'{code}缺少{key}')
 check(Image.open(OUT/m['image']).size==tuple(m['canvas']),f'{code}图像尺寸不一致')
 check(hashlib.sha256((OUT/m['source']).read_bytes()).hexdigest()==m['source_sha256'],f'{code}配置指纹不一致')
 check(all(inside(p)for p in m['deploy']),f'{code}部署越界')
 check(all(m['terrain'][m['terrain_indices'][p[1]*w+p[0]]]['foot']<255 for p in m['deploy']),f'{code}部署格步兵不可通行')
 for group in ['enemies','npcs','reinforcements','objects']:
  check(all(inside(o['position'])for o in m[group]),f'{code}{group}坐标越界')
 check(all(inside(p)for o in m['objects']for p in o['fronts']),f'{code}操作格越界')
 check(not m['exit_marker'] or inside(m['exit_marker']['position']),f'{code}出口越界')
 check(all(inside(p)for b in m['boats']for p in b['path']),f'{code}船路越界')
 image_record=next(x for x in manifest['images']if x['code']==code)
 check(hashlib.sha256((OUT/m['image']).read_bytes()).hexdigest()==image_record['sha256'],f'{code}图像指纹不一致')
for file in ['index.html','styles.css','gallery.js','maps-data.js','manifest.json','README.md','sources/flow-notes.md']:
 check((OUT/file).is_file(),f'页面缺失：{file}')
page=(OUT/'index.html').read_text();script=(OUT/'gallery.js').read_text();ids=set(re.findall(r'id="([^"]+)"',page))
check(len(ids)==len(re.findall(r'id="([^"]+)"',page)),'重复页面ID')
check(all(i in ids for i in re.findall(r"\$\('([^']+)'\)",script)),'脚本使用未定义的页面ID')
report={'passed':not errors,'checks':checks,'maps':len(data['maps']),'errors':errors,'warnings':warnings,'scope':'当前配置、原生图像完整性、离线资源、静态绑定；浏览器检查另见browser字段。'}
old=OUT/'verification.json'
if old.exists():
 previous=json.loads(old.read_text())
 for key in ['browser','script']:
  if key in previous:report[key]=previous[key]
old.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
assert not errors,errors
files=[OUT/f for f in ['index.html','styles.css','gallery.js','maps-data.js','manifest.json','README.md','verification.json']]
for folder in ['images','thumbnails','sources']:files+=sorted((OUT/folder).glob('*'))
with zipfile.ZipFile(OUT/'battle-maps-complete.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6)as archive:
 for p in files:archive.write(p,Path('全部战斗地图')/p.relative_to(OUT))
print(json.dumps({'passed':True,'checks':checks,'files':len(files),'zip_bytes':(OUT/'battle-maps-complete.zip').stat().st_size},ensure_ascii=False))
