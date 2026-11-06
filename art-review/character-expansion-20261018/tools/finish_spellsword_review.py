#!/usr/bin/env python3
"""Publish the ally spellsword review entry and inventory its local assets."""
import json,re,ast
from html.parser import HTMLParser
from urllib.parse import urlparse,parse_qs,unquote
from PIL import Image
from build_gallery import ROOT,file_hash
from prepare_spellsword_complete import REV,OUT,write

def main():
 report=json.loads((OUT/'verification.json').read_text());exports=json.loads((OUT/'export-report.json').read_text());assert report['status']=='passed'
 paths=set(OUT.glob('**/*.png'))|{ROOT/e['still']for e in exports['exports']};images=[]
 for path in sorted(paths):
  source=path.parent==OUT/'source';sprite=path.stem.startswith('frame-');purpose='原始参考／生成源图，仅离线保留'if source else'角色交付单帧'if sprite else'图集／离线检查图'
  with Image.open(path)as im:images.append({'path':path.relative_to(ROOT).as_posix(),'purpose':purpose,'dimensions':list(im.size),'mode':im.mode,'bytes':path.stat().st_size,'sha256':file_hash(path),'source_only':source})
 sprites=[x for x in images if x['purpose']=='角色交付单帧'];assert len(sprites)==58 and all(x['bytes']<50000 for x in sprites)
 for x in images:
  if not x['source_only']and x['bytes']>=200000:x['quality_reason']='无损检查图，保留完整像素和原尺寸轮廓'
 write(OUT/'image-inventory.json',{'revision':REV,'images':images,'sprite_count':58,'sprite_max_bytes':max(x['bytes']for x in sprites),'source_quality_preserved':True})
 links=[]
 for name,key in [('待机','professions-class-11-ally-maps-tactical-idle--idle-cycle'),('向上','professions-class-11-ally-maps-tactical-walk--walk-up'),('向右','professions-class-11-ally-maps-tactical-walk--walk-right'),('向下','professions-class-11-ally-maps-tactical-walk--walk-down'),('向左','professions-class-11-ally-maps-tactical-walk--walk-left'),('普通剑击','professions-class-11-ally-battle--original_class_11_normal'),('雷剑','professions-class-11-ally-battle--class_11_ally_levin'),('火球','professions-class-11-ally-battle--class_11_ally_item_23'),('风刃','professions-class-11-ally-battle--class_11_ally_item_27'),('箭雨','professions-class-11-ally-battle--class_11_ally_item_28_far_ally_vs_heavy'),('恢复','professions-class-11-ally-battle--class_11_ally_item_40')]:links.append(f'<a href="?action={key}#motion-player">我方 · {name}</a>')
 for name,path in [('地图全姿势','ally-maps-light.png'),('战斗全姿势','ally-battle-light.png'),('制作与检查记录','README.md')]:links.append(f'<a href="{REV}/{path}">{name}</a>')
 section='<section id="spellsword-progress" aria-label="我方女魔剑士全动作" style="margin:0 0 24px"><div class="heading"><h2>女魔剑士 · 我方全动作</h2><p>冰晶长剑 · 蓝白与少量冰蓝</p></div><nav class="links" aria-label="我方女魔剑士动作入口">'+''.join(links)+'</nav><p class="action-note" style="margin-top:14px">我方待机、四向行走、停止及战斗共80项已补齐。沿用女法师的深蓝、蓝色、米白、肤色和柔和玫瑰色，增加少量冰蓝；白色肩部防护、分片短战衣与高束长发加强进阶感。保留眼睛和自然肤色，头发纯色、衣料哑光。长剑依参考图保留冰晶尖刃、银白护手与完整握柄。地图固定头颈和躯干基准，双腿交替，身体随左右方向侧转；沿用原作待机14／8／14／8帧和行走每相16帧。战斗分别保留近身起跳、转身、落地斩、回位、雷剑及徒手施法的原始动作程序、结算和时长；同名法术共用已确认特效。依你的补充，本轮只制作我方，敌方暂不制作。仅更新美术对照，待视觉验收。</p></section>\n\n'
 page=ROOT/'index.html';s=page.read_text();s=re.sub(r'<body data-default-action="[^"]+"','<body data-default-action="professions-class-11-ally-maps-tactical-idle--idle-cycle"',s,count=1);s=re.sub(r'<span class="badge">[^<]+</span>','<span class="badge">我方女魔剑士 · 全动作</span>',s,count=1)
 if'id="spellsword-progress"'in s:s=re.sub(r'<section id="spellsword-progress".*?</section>\s*',section,s,count=1,flags=re.S)
 else:s=s.replace('<section id="female-mage-progress"',section+'<section id="female-mage-progress"',1)
 s=re.sub(r'(gallery-data\.js\?v=)[^" ]+',r'\g<1>'+REV,s);s=re.sub(r'(tools/gallery\.js\?v=)[^" ]+',r'\g<1>'+REV,s);page.write_text(s)
 class Page(HTMLParser):
  def __init__(self):super().__init__();self.links=[];self.ids=[];self.default=None
  def handle_starttag(self,tag,attrs):
   a=dict(attrs)
   if'id'in a:self.ids.append(a['id'])
   if'href'in a:self.links.append(a['href'])
   if tag=='body':self.default=a.get('data-default-action')
 p=Page();p.feed(s);d=json.loads((ROOT/'demos/gallery-data.json').read_text());actions={a['id']:a for a in d['actions']};assert len(p.ids)==len(set(p.ids))and actions[p.default]['ready']and actions[p.default]['video'];count=0
 for href in p.links:
  u=urlparse(href)
  for aid in parse_qs(u.query).get('action',[]):assert aid in actions;count+=1
  if REV+'/'in u.path:assert(ROOT/unquote(u.path)).exists()
 js=(ROOT/'gallery-data.js').read_text();assert json.loads(js[len('window.GALLERY_DATA = '):].strip().rstrip(';'))==d
 for href in re.findall(r'\]\(([^)]+)\)',(OUT/'README.md').read_text()):assert(OUT/href).resolve().exists(),href
 ast.parse((ROOT/'tools/finish_spellsword_review.py').read_text());report.update(page_action_links_checked=count,image_inventory_count=len(images),sprite_max_bytes=max(x['bytes']for x in sprites),browser_ui_checked=False);write(OUT/'verification.json',report);print(json.dumps({'status':'passed','new_actions':80,'videos':report['decoded_videos'],'sprites':58,'page_action_links':count}),flush=True)
if __name__=='__main__':main()
