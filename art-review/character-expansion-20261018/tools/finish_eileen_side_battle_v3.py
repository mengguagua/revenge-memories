#!/usr/bin/env python3
"""Publish Eileen's narrow side/battle corrections in the existing review page."""
import json,re,html,math
from html.parser import HTMLParser
from urllib.parse import urlparse,parse_qs,unquote
from PIL import Image,ImageDraw
from build_gallery import ROOT,file_hash
from export_gallery import font
from import_eileen_side_battle_v3 import REV,OUT,SRC,write,NAVY

def board(entries,name,title):
 for light in[False,True]:
  cw,ch=360,330;q=Image.new('RGB',(cw*4,46+ch*math.ceil(len(entries)/4)),(220,222,216)if light else(32,45,53));dr=ImageDraw.Draw(q);fg=NAVY if light else(235,243,242);dr.text((q.width//2,22),title,anchor='mm',font=font(20),fill=fg)
  for n,(label,path)in enumerate(entries):
   im=Image.open(path).convert('RGBA')
   if im.height<100:im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
   x=n%4*cw+(cw-im.width)//2;y=46+n//4*ch;q.paste(im,(x,y),im);b=font(15).getbbox(label);assert b[2]-b[0]<cw-24;dr.text((n%4*cw+cw//2,y+309),label,anchor='mm',font=font(15),fill=fg)
  q.save(OUT/(name+('-light.png'if light else'-dark.png')),optimize=True)

def main():
 report=json.loads((OUT/'verification.json').read_text());assert report['status']=='passed';d=json.loads((ROOT/'demos/gallery-data.json').read_text());ps={p['id']:p for p in d['profiles']};aa={a['id']:a for a in d['actions']}
 maps=[]
 for key,label in[('story','剧情 / 大地图'),('tactical-idle','战图待机'),('tactical-walk','战图行走')]:
  for i,path in ps['eileen-maps-'+key]['newFrames'].items():
   if key=='tactical-idle'and int(i)>2:continue
   maps.append((label+' '+i,ROOT/path))
 board(maps,'maps-current','艾琳 · 女魔剑士 · 当前地图完整姿势')
 board([(i,ROOT/path)for i,path in sorted(ps['eileen-battle']['newFrames'].items(),key=lambda kv:int(kv[0]))],'battle-current','艾琳 · 女魔剑士 · 当前战斗完整姿势')
 q=Image.new('RGB',(1440,750),(32,45,53));dr=ImageDraw.Draw(q)
 for row,(folder,job)in enumerate([('eileen','女魔剑士'),('eileen-promoted','引光剑使')]):
  dr.text((720,28+row*360),'艾琳 · '+job+' · 画像与三个场景一致性',anchor='mm',font=font(22),fill=(235,243,242));ims=[Image.open(ROOT/'eileen-identity-complete-v1-20261023/source/eileen_departure.png').convert('RGBA').resize((192,192),Image.Resampling.NEAREST)]
  for context in['maps-story','maps-tactical-idle','battle']:
   im=Image.open(ROOT/ps[folder+'-'+context]['newFrames']['0']).convert('RGBA')
   if context.startswith('maps'):im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
   ims.append(im)
  for col,(im,label)in enumerate(zip(ims,['现行画像','剧情 / 大地图复用','战斗地图','战斗场景'])):
   x=col*360+(360-im.width)//2;y=row*360+55+(288-im.height)//2;q.paste(im,(x,y),im);dr.text((col*360+180,row*360+336),label,anchor='mm',font=font(18),fill=(235,243,242))
 q.save(OUT/'identity-comparison.png',optimize=True)
 labels=[('战图向右','eileen-maps-tactical-walk--walk-right'),('战图向左','eileen-maps-tactical-walk--walk-left'),('普通攻击','eileen-battle--original_class_11_normal'),('雷剑','eileen-battle--class_11_ally_levin')]
 nav=''.join(f'<a href="?action={aid}#motion-player">{label}</a>'for label,aid in labels)
 section=f'''<section id="eileen-side-battle-v3-progress" class="panel" style="margin-bottom:26px" aria-label="艾琳侧走持剑与战斗比例修正"><div class="heading"><h2>艾琳 · 侧走持剑与战斗比例修正</h2><p>身前握剑 · 紧凑跨步 · 完整人物帧</p></div><p class="action-note">战图左右行走可见身前的前臂、握剑手与剑身；跨步保持腿长和粗细。战斗取消下半身拼接，消除重复的躯干、披风和腿；重新核对面部定位与人物比例，腾空下劈阶段表现红色松辫上扬。</p><nav class="links" aria-label="艾琳侧走与战斗动作">{nav}</nav><nav class="links" style="margin-top:14px" aria-label="艾琳侧走与战斗检查"><a href="{REV}/side-playback-light.png">侧走两相与阴影</a><a href="{REV}/battle-playback-dark.png">战斗关键帧近景</a><a href="{REV}/maps-current-light.png">当前地图全姿势</a><a href="{REV}/battle-current-light.png">当前战斗全姿势</a><a href="{REV}/README.md">制作记录与提示词</a><a href="{REV}/verification.json">针对性检查</a></nav><p class="action-note">4个侧走帧槽与25个战斗帧槽更新；11项动作和10段动画重新检查。保留原作节奏、位移和结算。剧情／大地图、战图上下行和待机沿用已确认稿，引光剑使保持独立设计。本轮仅更新隔离美术对照，待视觉验收。</p></section>\n'''
 page=ROOT/'index.html';s=page.read_text();s=re.sub(r'<section id="eileen-side-battle-v3-progress".*?</section>\s*','',s,flags=re.S);marker='<section id="eileen-map-v2-progress"';assert marker in s;s=s.replace(marker,section+marker,1)
 s=s.replace('<h2>艾琳 · 女魔剑士地图修正</h2>','<h2>艾琳 · 上一轮地图修正记录</h2>')
 s=s.replace('本轮11个独立姿势、14个帧槽更新；17项动作对照与9段动画导出。引光剑使与战斗场景沿用前版。','上一轮11个独立姿势、14个帧槽更新；17项动作对照与9段动画导出。侧走及战斗最新修正见上方。')
 s=s.replace('href="eileen-spellsword-map-v2-20261024/identity-comparison.png">画像与三个场景一致性',f'href="{REV}/identity-comparison.png">画像与三个场景一致性')
 s=s.replace('href="eileen-spellsword-map-v2-20261024/poses-light.png">女魔剑士地图修正姿势',f'href="{REV}/maps-current-light.png">女魔剑士地图全姿势')
 s=s.replace('href="eileen-identity-complete-v1-20261023/base-battle-light.png">女魔剑士战斗全姿势',f'href="{REV}/battle-current-light.png">女魔剑士战斗全姿势')
 s=re.sub(r'<body data-default-action="[^"]+"','<body data-default-action="eileen-maps-tactical-walk--walk-right"',s,count=1)
 for pattern in[r'(gallery-data\.js\?v=)[^" ]+',r'(tools/gallery\.js\?v=)[^" ]+']:s=re.sub(pattern,r'\g<1>'+REV,s)
 page.write_text(s)
 manifest=ROOT/'eileen/manifest.json';v=json.loads(manifest.read_text());v.update(revision=REV,review_record='../'+REV+'/README.md',runtime_integrated=False);write(manifest,v)
 exports=json.loads((OUT/'export-report.json').read_text())['exports'];paths=set(OUT.rglob('*.png'))|{ROOT/e['still']for e in exports if e.get('still')};images=[]
 for p in sorted(paths):
  with Image.open(p)as im:r={'path':p.relative_to(ROOT).as_posix(),'size':list(im.size),'bytes':p.stat().st_size,'sha256':file_hash(p),'source_only':SRC in p.parents,'purpose':'离线生成／参考源图'if SRC in p.parents else'无损帧纹理或离线对照'}
  if r['bytes']>=200000:r['quality_reason']='保留无损原始源图或完整离线姿势对照；播放器另用统一色板的小型无损PNG。'
  images.append(r)
 write(OUT/'image-inventory.json',{'revision':REV,'images':images,'runtime_frame_max_bytes':max(r['bytes']for r in images if '/frame-'in r['path']),'optimization':'lossless indexed nine-color frames, binary alpha'})
 class Page(HTMLParser):
  def __init__(self):super().__init__();self.ids=[];self.links=[];self.default=None
  def handle_starttag(self,t,attrs):
   a=dict(attrs)
   if'id'in a:self.ids.append(a['id'])
   if'href'in a:self.links.append(a['href'])
   if t=='body':self.default=a.get('data-default-action')
 p=Page();p.feed(s);assert len(p.ids)==len(set(p.ids));assert aa[p.default]['video'];checked=0
 for href in p.links:
  u=urlparse(html.unescape(href))
  for aid in parse_qs(u.query).get('action',[]):assert aid in aa,aid;checked+=1
  if REV+'/'in u.path:assert(ROOT/unquote(u.path)).exists(),href
 for href in re.findall(r'\]\(([^)]+)\)',(OUT/'README.md').read_text()):assert(OUT/href.split('?')[0]).resolve().exists(),href
 for _,aid in labels:assert aa[aid]['video']
 js=(ROOT/'gallery-data.js').read_text();assert json.loads(js[len('window.GALLERY_DATA = '):].strip().rstrip(';'))==d
 report.update(page_action_links_checked=checked,page_ids_unique=True,default_action=p.default,image_inventory_count=len(images),runtime_frame_max_bytes=max(r['bytes']for r in images if '/frame-'in r['path']),offline_visual_checks='Inspected current light/dark full pose sheets and actual composited side-walk two-phase and normal attack critical frames; sword hand and blade visible in front, compact legs, no duplicate actor, consistent face/body size and raised red braid. User visual acceptance pending.',text_safe_areas='Measured centered pose captions, checked playback header safe width, reused padded panel and wrapping navigation; no browser visual acceptance claimed.');write(OUT/'verification.json',report)
 print(json.dumps({'status':'passed','actions':11,'videos':10,'page_links':checked,'runtime_frame_max_bytes':report['runtime_frame_max_bytes']},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
