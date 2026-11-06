#!/usr/bin/env python3
"""Publish heroine review entry points and resource/HTML delivery checks."""
import html,json,re,shutil
from html.parser import HTMLParser
from urllib.parse import urlparse,parse_qs,unquote
from PIL import Image
from build_gallery import ROOT,file_hash
from prepare_eileen_complete import REV,OUT,SRC,write
from finish_healer_saint_review import catalog

def link(label,action):return f'<a href="?action={action}#motion-player">{label}</a>'
def main():
 report=json.loads((OUT/'verification.json').read_text());assert report['status']=='passed'
 d=json.loads((ROOT/'demos/gallery-data.json').read_text());sections=[]
 for folder,job in[('eileen','女魔剑士'),('eileen-promoted','引光剑使')]:
  nav=[]
  for label,key in [('剧情地图','maps-story--walk-down'),('大地图 · 复用剧情','maps-world--walk-right'),('战斗地图待机','maps-tactical-idle--idle-cycle'),('战图向上','maps-tactical-walk--walk-up'),('战图向右','maps-tactical-walk--walk-right'),('战图向下','maps-tactical-walk--walk-down'),('战图向左','maps-tactical-walk--walk-left'),('普通攻击','battle--original_class_11_normal'),('雷剑','battle--class_11_ally_levin'),('火球','battle--class_11_ally_item_23'),('雷电','battle--class_11_ally_item_24'),('诸神黄昏','battle--class_11_ally_item_25'),('圣光','battle--class_11_ally_item_26'),('风刃','battle--class_11_ally_item_27'),('恢复','battle--class_11_ally_item_40')]:nav.append(link(label,folder+'-'+key))
  sections.append('<article class="panel" style="margin:16px 0"><h3 style="margin-bottom:14px">艾琳 · '+job+'</h3><nav class="links" aria-label="艾琳'+job+'全动作">'+''.join(nav)+'</nav></article>')
 section='<section id="eileen-complete-progress" style="margin-bottom:26px" aria-label="艾琳专属双阶段全动作"><div class="heading"><h2>艾琳 · 女魔剑士与引光剑使</h2><p>10个场景配置 · 144项动作对照</p></div><p class="action-note">依据现行画像统一深红波浪刘海、低位松辫、年轻面容、象牙白海披肩与小罗盘扣。女魔剑士沿用已完成职业的动作骨架；引光剑使独立设计白色分片长衣、护肩、靛蓝内层、黄铜细节与银白长剑。每阶段的剧情与大地图共用同一套图片，地图保持身体基准和持续阴影，战斗保留原姿态顺序、位移、节奏和结算。</p>'+''.join(sections)+'<nav class="links" style="margin-top:14px" aria-label="艾琳画像与全姿势检查">'+f'<a href="{REV}/identity-comparison.png">画像与三个场景一致性</a><a href="{REV}/base-maps-light.png">女魔剑士地图全姿势</a><a href="{REV}/base-battle-light.png">女魔剑士战斗全姿势</a><a href="{REV}/promoted-maps-light.png">引光剑使地图全姿势</a><a href="{REV}/promoted-battle-light.png">引光剑使战斗全姿势</a><a href="{REV}/README.md">素材、提示词与制作记录</a><a href="{REV}/verification.json">针对性检查</a></nav><p class="action-note">法术入口按艾琳原学习表展示，雷剑及故事专武仍按实际装备与剧情条件使用。专属进阶继续采用职业11与 light_guide 标记，不替换普通女魔剑士或原作留档职业24。使用内置 imagegen 制作，两阶段素材与完整提示词保存在本轮记录中。本轮仅更新隔离美术对照，待视觉验收。</p></section>\n'
 page=ROOT/'index.html';s=page.read_text();s=re.sub(r'<section id="eileen-complete-progress".*?</section>\s*','',s,flags=re.S)
 marker='<section id="healer-all-heal-flow-progress"';assert marker in s;s=s.replace(marker,section+marker,1)
 s=re.sub(r'<section id="profession-catalog-sync".*?</section>\s*',catalog(d),s,count=1,flags=re.S)
 s=re.sub(r'<body data-default-action="[^"]+"','<body data-default-action="eileen-maps-story--walk-down"',s,count=1)
 s=re.sub(r'<span class="badge">[^<]+</span>','<span class="badge">艾琳 · 专属双阶段全动作</span>',s,count=1)
 for pattern in[r'(gallery-data\.js\?v=)[^" ]+',r'(tools/gallery\.js\?v=)[^" ]+']:s=re.sub(pattern,r'\g<1>'+REV,s)
 page.write_text(s)
 diagnostics=list(OUT.glob('diagnostic-*.png'))
 if diagnostics:
  (SRC/'diagnostics').mkdir(exist_ok=True)
  for p in diagnostics:shutil.move(p,SRC/'diagnostics'/p.name)
 exports=json.loads((OUT/'export-report.json').read_text())['exports'];paths=set(OUT.rglob('*.png'))|{ROOT/e['still']for e in exports if e.get('still')};images=[]
 for p in sorted(paths):
  source=SRC in p.parents
  with Image.open(p)as im:record={'path':p.relative_to(ROOT).as_posix(),'purpose':'离线生成／参考源图，不供播放器加载'if source else'艾琳运行规格纹理与离线对照检查','size':list(im.size),'bytes':p.stat().st_size,'mode':im.mode,'sha256':file_hash(p),'source_only':source}
  limit=200000 if source or'battle-atlas'not in p.name and len(record['size'])==2 and max(record['size'])>1000 else 50000
  if record['bytes']>=limit:record['quality_reason']='保留完整无损源图或完整姿势对照；运行纹理另行使用统一色板无损索引版本。'
  images.append(record)
 write(OUT/'image-inventory.json',{'revision':REV,'images':images,'runtime_texture_max_bytes':max(a['bytes']for a in json.loads((OUT/'asset-manifest.json').read_text())['assets']if '/frame-'in a['path']),'lossless_indexed_runtime_png':True})
 class Page(HTMLParser):
  def __init__(self):super().__init__();self.ids=[];self.links=[];self.default=None
  def handle_starttag(self,tag,attrs):
   a=dict(attrs)
   if'id'in a:self.ids.append(a['id'])
   if'href'in a:self.links.append(a['href'])
   if tag=='body':self.default=a.get('data-default-action')
 p=Page();p.feed(s);assert len(p.ids)==len(set(p.ids));actions={a['id']:a for a in d['actions']};assert actions[p.default]['video'];checked=0
 for href in p.links:
  u=urlparse(html.unescape(href))
  for aid in parse_qs(u.query).get('action',[]):assert aid in actions,aid;checked+=1
  if REV+'/'in u.path:assert(ROOT/unquote(u.path)).exists(),href
 for href in re.findall(r'\]\(([^)]+)\)',(OUT/'README.md').read_text()):assert(OUT/href).resolve().exists(),href
 for name in['eileen_departure','eileen_chart','eileen_present']:assert file_hash(SRC/(name+'.png'))==file_hash(ROOT.parents[1]/f'actual/assets/portraits-0.7.2/{name}.png')
 js=(ROOT/'gallery-data.js').read_text();assert json.loads(js[len('window.GALLERY_DATA = '):].strip().rstrip(';'))==d
 report.update(page_action_links_checked=checked,page_ids_unique=True,default_action=p.default,image_inventory_count=len(images),current_portrait_files_unchanged=True,text_safe_areas='Measured centered export captions; page uses existing padded panel and wrapping link layout. No browser rendering claimed.',offline_visual_acceptance='Inspected both full pose boards and portrait-context comparison; contact and airborne captures inspected offline. User acceptance pending.');write(OUT/'verification.json',report)
 print(json.dumps({'status':'passed','new_actions':144,'decoded_videos':report['decoded_videos'],'page_links':checked,'images':len(images),'default':p.default}),flush=True)
if __name__=='__main__':main()
