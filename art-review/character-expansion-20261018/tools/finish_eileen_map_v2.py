#!/usr/bin/env python3
"""Refresh only Eileen map-fix gallery links and lossless asset inventory."""
import html,json,re
from html.parser import HTMLParser
from urllib.parse import urlparse,parse_qs,unquote
from PIL import Image,ImageDraw
from build_gallery import ROOT,file_hash
from export_gallery import font
from import_eileen_map_v2 import REV,OUT,SRC,write

def main():
 report=json.loads((OUT/'verification.json').read_text());assert report['status']=='passed'
 d=json.loads((ROOT/'demos/gallery-data.json').read_text());profiles={p['id']:p for p in d['profiles']};actions={a['id']:a for a in d['actions']}
 # Update the old identity cross-context link so it shows the current base maps.
 q=Image.new('RGB',(1440,750),(32,45,53));dr=ImageDraw.Draw(q)
 for row,(folder,job)in enumerate([('eileen','女魔剑士'),('eileen-promoted','引光剑使')]):
  dr.text((720,28+row*360),'艾琳 · '+job+' · 画像与三个场景一致性',anchor='mm',font=font(22),fill=(235,243,242))
  ims=[Image.open(ROOT/'eileen-identity-complete-v1-20261023/source/eileen_departure.png').convert('RGBA').resize((192,192),Image.Resampling.NEAREST)]
  for context,i in[('maps-story','0'),('maps-tactical-idle','0'),('battle','0')]:
   im=Image.open(ROOT/profiles[folder+'-'+context]['newFrames'][i]).convert('RGBA')
   if context.startswith('maps'):im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
   ims.append(im)
  for col,(im,label)in enumerate(zip(ims,['现行画像','剧情 / 大地图复用','战斗地图','战斗场景'])):
   x=col*360+(360-im.width)//2;y=row*360+55+(288-im.height)//2;q.paste(im,(x,y),im);dr.text((col*360+180,row*360+336),label,anchor='mm',font=font(18),fill=(235,243,242))
 q.save(OUT/'identity-comparison.png',optimize=True)
 labels=[('剧情向下','eileen-maps-story--walk-down'),('剧情向左','eileen-maps-story--walk-left'),('剧情向右','eileen-maps-story--walk-right'),('大地图同步','eileen-maps-world--walk-down'),('战图待机','eileen-maps-tactical-idle--idle-cycle'),('战图向上','eileen-maps-tactical-walk--walk-up'),('战图向下','eileen-maps-tactical-walk--walk-down')]
 nav=''.join(f'<a href="?action={aid}#motion-player">{label}</a>'for label,aid in labels)
 section=f'''<section id="eileen-map-v2-progress" class="panel" style="margin-bottom:26px" aria-label="艾琳女魔剑士地图姿势修正"><div class="heading"><h2>艾琳 · 女魔剑士地图修正</h2><p>剧情步态 · 眼睛 · 披风与握剑遮挡</p></div><p class="action-note">剧情向下改为左右脚前后交替，清理脸部白条；侧走采用站直摆臂与头发后扫、跨步垂臂与头发下垂两相。战图待机露出眼睛，上行披风从双肩垂下、持剑手藏在身前，下行可见前臂握住剑柄。大地图同步复用，所有地图动作保留地面阴影与原作节奏。</p><nav class="links" aria-label="艾琳地图修正动作">{nav}</nav><nav class="links" style="margin-top:14px" aria-label="艾琳地图修正检查图"><a href="{REV}/poses-light.png">浅色全姿势</a><a href="{REV}/poses-dark.png">深色全姿势</a><a href="{REV}/playback-phases-light.png">播放器相位与阴影</a><a href="{REV}/README.md">制作记录与提示词</a><a href="{REV}/verification.json">针对性检查</a></nav><p class="action-note">本轮11个独立姿势、14个帧槽更新；17项动作对照与9段动画导出。引光剑使与战斗场景沿用前版。仅隔离美术验收，尚未接入游戏运行场景。</p></section>\n'''
 page=ROOT/'index.html';s=page.read_text();s=re.sub(r'<section id="eileen-map-v2-progress".*?</section>\s*','',s,flags=re.S);marker='<section id="eileen-complete-progress"';assert marker in s;s=s.replace(marker,section+marker,1)
 old='eileen-identity-complete-v1-20261023'
 s=s.replace(f'href="{old}/base-maps-light.png">女魔剑士地图全姿势',f'href="{REV}/poses-light.png">女魔剑士地图修正姿势')
 s=s.replace(f'href="{old}/identity-comparison.png">画像与三个场景一致性',f'href="{REV}/identity-comparison.png">画像与三个场景一致性')
 s=re.sub(r'<body data-default-action="[^"]+"','<body data-default-action="eileen-maps-story--walk-down"',s,count=1)
 for pattern in[r'(gallery-data\.js\?v=)[^" ]+',r'(tools/gallery\.js\?v=)[^" ]+']:s=re.sub(pattern,r'\g<1>'+REV,s)
 page.write_text(s)
 # Source masters stay offline. Runtime textures are exact indexed PNGs.
 exports=json.loads((OUT/'export-report.json').read_text())['exports'];paths=set(OUT.rglob('*.png'))|{ROOT/e['still']for e in exports if e.get('still')};images=[]
 for p in sorted(paths):
  with Image.open(p)as im:r={'path':p.relative_to(ROOT).as_posix(),'size':list(im.size),'bytes':p.stat().st_size,'sha256':file_hash(p),'source_only':SRC in p.parents,'purpose':'离线参考或生成源图'if SRC in p.parents else'地图纹理／离线姿势及播放器对照'}
  if r['bytes']>=200000:r['quality_reason']='保留无损生成源图或完整离线相位对照；实际播放器纹理另存无损索引小图。'
  images.append(r)
 write(OUT/'image-inventory.json',{'revision':REV,'images':images,'runtime_frame_max_bytes':max(r['bytes']for r in images if '/frame-'in r['path']),'runtime_png_optimization':'lossless indexed 9-color palette with binary alpha'})
 class Page(HTMLParser):
  def __init__(self):super().__init__();self.ids=[];self.links=[];self.default=None
  def handle_starttag(self,tag,attrs):
   a=dict(attrs)
   if'id'in a:self.ids.append(a['id'])
   if'href'in a:self.links.append(a['href'])
   if tag=='body':self.default=a.get('data-default-action')
 p=Page();p.feed(s);assert len(p.ids)==len(set(p.ids));assert actions[p.default]['video'];checked=0
 for href in p.links:
  u=urlparse(html.unescape(href))
  for aid in parse_qs(u.query).get('action',[]):assert aid in actions,aid;checked+=1
  if REV+'/'in u.path:assert(ROOT/unquote(u.path)).exists(),href
 for href in re.findall(r'\]\(([^)]+)\)',(OUT/'README.md').read_text()):assert(OUT/href.split('?')[0]).resolve().exists(),href
 for label,aid in labels:assert actions[aid]['ready']and actions[aid]['video']
 js=(ROOT/'gallery-data.js').read_text();assert json.loads(js[len('window.GALLERY_DATA = '):].strip().rstrip(';'))==d
 # Measured labels stay within each pose-board cell and playback header.
 for text in['剧情侧走 · 站直摆臂 / 后扫发','剧情侧走 · 跨步垂臂 / 垂发']:
  b=font(15).getbbox(text);assert b[2]-b[0]<350-32
 report.update(page_action_links_checked=checked,page_ids_unique=True,default_action=p.default,image_inventory_count=len(images),runtime_frame_max_bytes=max(r['bytes']for r in images if '/frame-'in r['path']),text_safe_areas='Pose captions measured inside cells; playback title measured inside safe width; gallery uses existing padded panel and wrapping navigation. Offline verification, no browser rendering claim.');write(OUT/'verification.json',report)
 print(json.dumps({'status':'passed','actions':17,'videos':9,'page_action_links':checked,'runtime_frame_max_bytes':report['runtime_frame_max_bytes']},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
