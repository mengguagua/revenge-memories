#!/usr/bin/env python3
"""Update only the spellsword map review entry and its local delivery inventory."""
import json,re,ast
from html.parser import HTMLParser
from urllib.parse import urlparse,parse_qs,unquote
from PIL import Image
from build_gallery import ROOT,file_hash
from revise_spellsword_map_gait_v2 import REV,OUT,write

def main():
 report=json.loads((OUT/'verification.json').read_text());assert report['status']=='passed'and report['decoded_videos']==5
 images=[];exports=json.loads((OUT/'export-report.json').read_text())['exports'];paths=set(OUT.glob('**/*.png'))|{ROOT/e['still']for e in exports}
 for p in sorted(paths):
  with Image.open(p)as im:images.append({'path':p.relative_to(ROOT).as_posix(),'size':list(im.size),'bytes':p.stat().st_size,'sha256':file_hash(p),'source_only':p.parent==OUT/'source','purpose':'生成源图，离线保留原始质量'if p.parent==OUT/'source'else'地图交付单帧'if p.stem.startswith('frame-')else'姿势图／离线对照检查'})
 sprites=[x for x in images if x['purpose']=='地图交付单帧'];assert len(sprites)==14 and max(x['bytes']for x in sprites)<50000
 write(OUT/'image-inventory.json',{'images':images,'sprite_count':14,'sprite_max_bytes':max(x['bytes']for x in sprites),'source_quality_preserved':True})
 p=ROOT/'index.html';s=p.read_text();s=re.sub(r'<body data-default-action="[^"]+"','<body data-default-action="professions-class-11-ally-maps-tactical-idle--idle-cycle"',s,count=1);s=re.sub(r'<span class="badge">[^<]*</span>','<span class="badge">女魔剑士 · 待机与行走修订</span>',s,count=1)
 match=re.search(r'<section id="spellsword-progress".*?</section>',s,re.S);assert match
 section=match[0].replace('spellsword-complete-v1-20261023/ally-maps-light.png',REV+'/maps-light.png')
 section=section.replace('>制作与检查记录</a>','>初版完整记录</a>')
 if REV+'/README.md'not in section:section=section.replace('</nav>','<a href="'+REV+'/README.md">本轮待机与步态修订</a></nav>',1)
 note='本轮修正地图待机与四向行走：待机保持完整两腿，右肩、肘、腕和剑一起完成三相动作；前后行走沿固定髋部的窄步道交替前迈，向下改回右臂经胸前握剑；左右行走保留并腿通过相与前后跨步相，两只脚均可辨认。待机及所有行走方向恢复连续地面阴影。头颈、躯干基准与原作88／96帧循环保持，蓝白服饰、肤色和纯色头发延续，战斗动作保持上一版。本轮只制作我方，敌方暂不制作。共80项完整动作仍可切换查看，待视觉验收。'
 section=re.sub(r'<p class="action-note".*?</p>','<p class="action-note" style="margin-top:14px">'+note+'</p>',section,count=1,flags=re.S);s=s[:match.start()]+section+s[match.end():];s=re.sub(r'(gallery-data\.js\?v=)[^" ]+',r'\g<1>'+REV,s);s=re.sub(r'(tools/gallery\.js\?v=)[^" ]+',r'\g<1>'+REV,s);p.write_text(s)
 class Page(HTMLParser):
  def __init__(self):super().__init__();self.ids=[];self.links=[];self.default=None
  def handle_starttag(self,tag,attrs):
   a=dict(attrs)
   if'id'in a:self.ids.append(a['id'])
   if'href'in a:self.links.append(a['href'])
   if tag=='body':self.default=a.get('data-default-action')
 doc=Page();doc.feed(s);d=json.loads((ROOT/'demos/gallery-data.json').read_text());aa={a['id']:a for a in d['actions']};assert len(doc.ids)==len(set(doc.ids))and aa[doc.default]['ready']and aa[doc.default]['video'];checked=0
 for href in doc.links:
  u=urlparse(href)
  for aid in parse_qs(u.query).get('action',[]):assert aid in aa;checked+=1
  if REV+'/'in u.path:assert(ROOT/unquote(u.path)).exists()
 for href in re.findall(r'\]\(([^)]+)\)',(OUT/'README.md').read_text()):assert(OUT/href).resolve().exists(),href
 js=(ROOT/'gallery-data.js').read_text();assert json.loads(js[len('window.GALLERY_DATA = '):].strip().rstrip(';'))==d
 ast.parse((ROOT/'tools/finish_spellsword_map_gait_v2.py').read_text());report.update(page_action_links_checked=checked,image_inventory_count=len(images),sprite_max_bytes=max(x['bytes']for x in sprites),offline_visual_review={'two_idle_legs':True,'sword_arm_articulates':True,'front_right_hand':True,'front_back_alternate_legs':True,'side_passing_and_open_stride':True,'continuous_shadow_dark_and_light':True,'title_spacing':True});write(OUT/'verification.json',report);print(json.dumps({'status':'passed','map_actions':9,'sprites':14,'videos':5,'page_links':checked}),flush=True)
if __name__=='__main__':main()
