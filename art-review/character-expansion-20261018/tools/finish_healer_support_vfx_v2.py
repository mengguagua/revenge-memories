#!/usr/bin/env python3
"""Publish the four spell revisions with their current preview and QA links."""
import json,re,html
from html.parser import HTMLParser
from urllib.parse import urlparse,parse_qs,unquote
from PIL import Image
from build_gallery import ROOT,file_hash
from revise_healer_support_vfx_v2 import REV,OUT,write
from finish_healer_saint_review import catalog
def main():
 report=json.loads((OUT/'verification.json').read_text());assert report['status']=='passed';d=json.loads((ROOT/'demos/gallery-data.json').read_text());exports=json.loads((OUT/'export-report.json').read_text());contracts={c['key']:c for c in json.loads((OUT/'spell-contracts.json').read_text())['actions']};parts=[]
 for c,name in[(17,'济世术师'),(18,'疗愈师')]:
  links=''.join(f'<a href="?action=professions-class-{c}-ally-battle--class_{c}_ally_item_{item}#motion-player">{name} · {label}</a>'for item,label in[(42,'红色吸血抽取'),(41,'绿色远程恢复'),(44,'全体恢复与泉水'),(43,'蓝色传送光柱')]);parts.append('<nav class="links" style="margin-top:12px" aria-label="'+name+'法术修订">'+links+'</nav>')
 capture=[]
 for item,label,field,delta,light in[(42,'吸血初始抽取','extraction_start',12,False),(41,'远程恢复雨滴','rain_start',12,True),(44,'全体恢复泉水','pool_start',25,True),(43,'传送蓝色光柱','column_start',24,False)]:
  c=contracts[f'class_17_ally_item_{item}'];path=f'class_17_ally_item_{item}-{c[field]+delta:03}-'+('light.png'if light else'dark.png');capture.append(f'<a href="{REV}/{path}">{label}检查</a>')
 section='<section id="healer-support-vfx-progress" style="margin-bottom:26px" aria-label="本轮四种辅助法术特效修订"><div class="heading"><h2>辅助法术 · 四项特效修订</h2><p>疗愈师 / 济世术师 · 48项变体</p></div>'+''.join(parts)+'<p class="action-note">吸血统一柔和红色，起始在目标处抽取能量，并持续牵引至施法者。远程恢复沿用恢复的绿色光环与雨滴，雨滴延长至54帧。全体恢复也统一绿色，雨滴落下后汇成下方的一片同色泉水，保留水花与波纹。传送在受术者位置升起蓝色光柱，结算后散为光丝。人物、法杖、宝瓶与原作施法、目标、结算保持；较长的雨滴／泉水只延长展示收尾，不追加治疗或行动。</p><nav class="links" style="margin-top:14px" aria-label="本轮特效检查">'+''.join(capture)+f'<a href="{REV}/effect-poses-light.png">全部特效素材</a><a href="{REV}/README.md">修订与检查记录</a><a href="{REV}/verification.json">针对性验证</a></nav></section>\n'
 page=ROOT/'index.html';s=page.read_text();s=re.sub(r'<section id="healer-support-vfx-progress".*?</section>\s*','',s,flags=re.S);s=s.replace('<section id="healer-saint-progress"',section+'<section id="healer-saint-progress"',1);s=re.sub(r'<section id="profession-catalog-sync".*?</section>\s*',catalog(d),s,count=1,flags=re.S);s=re.sub(r'<body data-default-action="[^"]+"','<body data-default-action="professions-class-17-ally-battle--class_17_ally_item_42"',s,count=1);s=re.sub(r'<span class="badge">[^<]+</span>','<span class="badge">疗愈师 / 济世术师 · 法术特效修订</span>',s,count=1)
 s=s.replace('href="healer-saint-complete-v1-20261023/README.md">制作与检查记录</a>','href="healer-saint-complete-v1-20261023/README.md">初版形象与动作记录</a>')
 ids={a['id']for a in d['actions']}
 def restore(m):
  href,label=m.groups();aid=parse_qs(urlparse(html.unescape(href)).query).get('action',[None])[0];return'<a href="'+href+'">'+label.removesuffix(' · 待制作')+'</a>'if aid in ids else m.group(0)
 s=re.sub(r'<span class="review-pending-link" data-pending-href="([^"]+)">(.*?)</span>',restore,s);s=re.sub(r'(gallery-data\.js\?v=)[^" ]+',r'\g<1>'+REV,s);s=re.sub(r'(tools/gallery\.js\?v=)[^" ]+',r'\g<1>'+REV,s);page.write_text(s)
 for c in[17,18]:
  p=ROOT/f'professions/class-{c}-ally/manifest.json';m=json.loads(p.read_text());m.update(revision=REV,maps_revision=m.get('maps_revision','healer-saint-complete-v1-20261023'),battle_revision=REV,effect_revision=REV,review_record='../../'+REV+'/README.md');write(p,m)
 images=[]
 paths=set(OUT.glob('**/*.png'))|{ROOT/e['still']for e in exports['exports']if e.get('still')}
 for p in sorted(paths):
  source=(OUT/'source')in p.parents
  with Image.open(p)as im:r={'path':p.relative_to(ROOT).as_posix(),'size':list(im.size),'bytes':p.stat().st_size,'mode':im.mode,'sha256':file_hash(p),'purpose':'离线生成源图'if source else'特效交付纹理'if p.parent==OUT/'effects'else'离线检查／对照图','source_only':source}
  if not source and r['bytes']>=200000:r['quality_reason']='无损检查图，保留完整特效与原像素尺寸'
  images.append(r)
 textures=[r for r in images if r['purpose']=='特效交付纹理'];assert len(textures)==33 and all(r['bytes']<50000 for r in textures);write(OUT/'image-inventory.json',{'revision':REV,'images':images,'new_effect_textures':33,'max_effect_bytes':max(r['bytes']for r in textures),'source_quality_preserved':True})
 class Page(HTMLParser):
  def __init__(self):super().__init__();self.ids=[];self.links=[];self.default=None
  def handle_starttag(self,tag,attrs):
   a=dict(attrs)
   if'id'in a:self.ids.append(a['id'])
   if'href'in a:self.links.append(a['href'])
   if tag=='body':self.default=a.get('data-default-action')
 p=Page();p.feed(s);actions={a['id']:a for a in d['actions']};assert len(p.ids)==len(set(p.ids))and actions[p.default]['video'];checked=0
 for href in p.links:
  u=urlparse(href)
  for aid in parse_qs(u.query).get('action',[]):assert aid in actions;checked+=1
  if REV+'/'in u.path:assert(ROOT/unquote(u.path)).exists(),href
 for href in re.findall(r'\]\(([^)]+)\)',(OUT/'README.md').read_text()):assert(OUT/href).resolve().exists(),href
 js=(ROOT/'gallery-data.js').read_text();assert json.loads(js[len('window.GALLERY_DATA = '):].strip().rstrip(';'))==d
 report.update(page_action_links_checked=checked,page_ids_unique=True,image_inventory_count=len(images),max_effect_texture_bytes=max(r['bytes']for r in textures),caption_safe_areas='Centered measured export headings; page labels retain padding and wrapping. Browser UI not tested.');write(OUT/'verification.json',report);print(json.dumps({'status':'passed','variants':48,'videos':report['decoded_videos'],'page_action_links':checked,'textures':33}),flush=True)
if __name__=='__main__':main()
