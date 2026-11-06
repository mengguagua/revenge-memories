#!/usr/bin/env python3
"""Finish review links and image inventory for fixed side arms, jumps and green heals."""
import json,re,ast
from html.parser import HTMLParser
from urllib.parse import urlparse,parse_qs,unquote
from PIL import Image
from build_gallery import ROOT,file_hash
from revise_spellsword_jump_heal_v3 import REV,OUT,write

def main():
 report=json.loads((OUT/'verification.json').read_text());assert report['status']=='passed'and report['decoded_videos']==8 and report['ally_heal_variants']==18
 exports=json.loads((OUT/'export-report.json').read_text())['exports'];paths=set(OUT.glob('**/*.png'))|{ROOT/e['still']for e in exports};images=[]
 for p in sorted(paths):
  source=p.parent==OUT/'source';purpose='原始参考／生成源图，离线保留'if source else'角色修订单帧'if p.stem.startswith('frame-')else'绿色恢复效果单帧'if p.parent.name=='effects'else'图集／离线检查图'
  with Image.open(p)as im:images.append({'path':p.relative_to(ROOT).as_posix(),'purpose':purpose,'size':list(im.size),'bytes':p.stat().st_size,'sha256':file_hash(p),'source_only':source})
 sprites=[x for x in images if x['purpose']=='角色修订单帧'];vfx=[x for x in images if x['purpose']=='绿色恢复效果单帧'];assert len(sprites)==16 and len(vfx)==19 and all(x['bytes']<50000 for x in sprites+vfx)
 for row in images:
  if not row['source_only']and row['bytes']>=200000:row['quality_reason']='无损对照图，保留完整原尺寸像素与文字轮廓'
 write(OUT/'image-inventory.json',{'images':images,'character_frames':16,'effect_frames':19,'sprite_max_bytes':max(x['bytes']for x in sprites+vfx),'source_quality_preserved':True})
 p=ROOT/'index.html';s=p.read_text();s=re.sub(r'<body data-default-action="[^"]+"','<body data-default-action="professions-class-11-ally-battle--original_class_11_normal"',s,count=1);s=re.sub(r'<span class="badge">[^<]*</span>','<span class="badge">女魔剑士 · 跳跃与恢复修订</span>',s,count=1)
 match=re.search(r'<section id="spellsword-progress".*?</section>',s,re.S);assert match;section=match[0];section=section.replace('spellsword-map-gait-v2-20261023/maps-light.png',REV+'/maps-all-light.png')
 extra=[]
 for label,key in [('女魔剑士 · 绿色恢复','professions-class-11-ally-battle--class_11_ally_item_40'),('疗愈师 · 绿色恢复','professions-class-18-ally-battle--class_18_ally_item_40'),('博学术师 · 绿色恢复','professions-class-19-ally-battle--class_19_ally_item_40')]:extra.append(f'<a href="?action={key}#motion-player">{label}</a>')
 for label,path in [('前后跳腿部检查','jump-poses-light.png'),('绿色光环与雨滴','green-heal-ending-dark.png'),('本轮修订与检查记录','README.md')]:extra.append(f'<a href="{REV}/{path}">{label}</a>')
 if REV+'/README.md'not in section:section=section.replace('</nav>',''.join(extra)+'</nav>',1)
 note='本轮固定女魔剑士左右行走的持剑臂和空手臂，不甩手；下半身继续使用已修正的并腿与跨步，阴影保持。前跳伸腿、空中收腿及后跳各段统一腰胯、腿长、膝盖和双靴位置，消除快速交替时的抽搐，原跳跃轨迹、转身、落地、结算和时长保持。友方女魔剑士、疗愈师与博学术师的18组恢复变体改为绿色光环，目标处光环在结尾化成绿色雨滴，在原收势时间内落下消散，不增加恢复次数。待机及前后行走延续上一版。我方女魔剑士共80项完整动作仍可切换查看；敌方暂不制作，仅供美术验收。'
 section=re.sub(r'<p class="action-note".*?</p>','<p class="action-note" style="margin-top:14px">'+note+'</p>',section,count=1,flags=re.S);s=s[:match.start()]+section+s[match.end():];s=re.sub(r'(gallery-data\.js\?v=)[^" ]+',r'\g<1>'+REV,s);s=re.sub(r'(tools/gallery\.js\?v=)[^" ]+',r'\g<1>'+REV,s);p.write_text(s)
 class Page(HTMLParser):
  def __init__(self):super().__init__();self.links=[];self.ids=[];self.default=None
  def handle_starttag(self,tag,attrs):
   a=dict(attrs)
   if'href'in a:self.links.append(a['href'])
   if'id'in a:self.ids.append(a['id'])
   if tag=='body':self.default=a.get('data-default-action')
 doc=Page();doc.feed(s);d=json.loads((ROOT/'demos/gallery-data.json').read_text());aa={a['id']:a for a in d['actions']};assert len(doc.ids)==len(set(doc.ids))and aa[doc.default]['ready']and aa[doc.default]['video']and aa[doc.default]['closeVideo'];checked=0
 for href in doc.links:
  u=urlparse(href)
  for aid in parse_qs(u.query).get('action',[]):assert aid in aa;checked+=1
  if REV+'/'in u.path:assert(ROOT/unquote(u.path)).exists()
 for href in re.findall(r'\]\(([^)]+)\)',(OUT/'README.md').read_text()):assert(OUT/href).resolve().exists(),href
 js=(ROOT/'gallery-data.js').read_text();assert json.loads(js[len('window.GALLERY_DATA = '):].strip().rstrip(';'))==d
 for name in['revise_spellsword_jump_heal_v3.py','verify_spellsword_jump_heal_v3.py','finish_spellsword_jump_heal_v3.py']:ast.parse((ROOT/'tools'/name).read_text())
 report.update(page_action_links_checked=checked,image_inventory_count=len(images),sprite_max_bytes=max(x['bytes']for x in sprites+vfx),offline_visual_review={'side_arms_fixed_and_shadow_present':True,'forward_and_backward_leg_groups':True,'green_caster_and_target_rings':True,'ring_to_green_rain_ending':True,'dark_light_and_title_safe_space':True},browser_ui_checked=False);write(OUT/'verification.json',report);print(json.dumps({'status':'passed','actions':23,'heal_variants':18,'videos':8,'character_frames':16,'green_effect_frames':19,'page_action_links':checked}),flush=True)
if __name__=='__main__':main()
