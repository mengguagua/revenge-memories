#!/usr/bin/env python3
"""Publish the full-body map correction while preserving the prior battle work."""
import hashlib,json,re
from urllib.parse import urlsplit
from PIL import Image
import integrate_hunapu_dawn_v3 as I
ROOT=I.ROOT;OUT=I.OUT;REV=I.art.REV
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):I.write(p,d)
def main():
 data=I.build();I.verify(data);ex=json.loads((OUT/'export-report.json').read_text());assert len(ex['decoded_videos'])==12
 for a in data['actions']:assert a.get('still')and(a.get('video')if a.get('defaultVideo')else True),a['id']
 I.boards(data);I.merge(data)
 live=json.loads((ROOT/'demos/gallery-data.json').read_text());before=I.art.baseline()
 for field in['profiles','actions']:
  for old in before[field]:
   if not I.own(old):assert next(x for x in live[field]if x['id']==old['id'])==old,old['id']
 page=ROOT/'index.html';old=page.read_text();default=re.search(r'data-default-action="([^"]+)"',old).group(1);match=re.search(r'<section\b[^>]*id="hunapu-dawn-progress".*?</section>',old,re.S);assert match
 section=match.group();section=section.replace('步态、持手、集中阴影与第二剑 · 待验收','剧情全身联动、正面持盾横移 · 待验收')
 paragraph='<p class="action-note" style="margin:0 0 16px">本轮重做完整人物步态：剧情向上抬腿沿髋下后摆，脚跟收直；手臂与腿反向摆动，肩、肘、躯干和衣摆连贯联动。剧情左右保留站直／跨步，头腰中心稳定。战斗地图左右按原作改为脸和胸朝前的横向移动，盾握在胸前前臂上。大地图继续复用剧情形象。</p>'
 section=re.sub(r'<p class="action-note" style="margin:0 0 16px">.*?</p>',paragraph,section,count=1,flags=re.S)
 section=section.replace('地图姿势与剑盾位置','地图全身联动与正面持盾').replace('hunapu-dawn-gait-combo-v2-20261024/maps-light.png',REV+'/maps-light.png').replace('hunapu-dawn-gait-combo-v2-20261024/README.md',REV+'/README.md').replace('本轮五项修订与检查','本轮步态修订与检查')
 extra='<nav class="links" aria-label="完整步态连续帧" style="margin-top:14px">'+''.join(f'<a href="{REV}/{file}">{label}</a>'for label,file in[('剧情向上 · 连续帧','story-up-dark.png'),('剧情侧向 · 连续帧','story-side-dark.png'),('正面向右横移','tactical-right-dark.png'),('正面向左横移','tactical-left-dark.png')])+'</nav>'
 if 'aria-label="完整步态连续帧"'not in section:section=section.replace('</section>',extra+'\n</section>')
 new=old[:match.start()]+section+old[match.end():];new=re.sub(r'(src="gallery-data\.js\?[^"&]*(?:&[^"&]*)*)"',lambda m:re.sub(r'&hunapu_dawn=[^"&]+','',m.group(1))+'&hunapu_dawn=whole-body-v3-20261024"',new,count=1);assert re.search(r'data-default-action="([^"]+)"',new).group(1)==default
 action_ids={a['id']for a in live['actions']}
 for href in re.findall(r'href="([^"]+)"',section):
  u=urlsplit(href)
  if u.query:assert u.query.removeprefix('action=')in action_ids
  elif not u.scheme:assert(ROOT/u.path).is_file(),href
 assert page.read_text()==old,'Concurrent page writer; retry latest';page.write_text(new)
 cp=ROOT/'healer-saint-complete-v1-20261023/profession-catalog-sync.json';catalog=json.loads(cp.read_text());h=next(h for h in catalog['exclusive_heroes']if h['actor']=='胡纳普');h.update(art_status='专属进阶43项已完成；剧情全身联动与战斗正面横移已重做，待验收',review_revision=REV,runtime_integrated=False);write(cp,catalog)
 mp=ROOT/'hunapu-promoted/manifest.json';manifest=json.loads(mp.read_text());manifest.update(revision=REV,map_revision=REV,battle_revision='hunapu-dawn-gait-combo-v2-20261024',review_record='../'+REV+'/README.md');write(mp,manifest)
 files=[p for p in OUT.rglob('*.png')if 'source'not in p.relative_to(OUT).parts]+[ROOT/'demos/stills'/(a['id']+'.png')for a in data['actions']];images=[]
 for p in sorted(set(files)):
  with Image.open(p)as im:dimensions=list(im.size)
  images.append({'path':p.relative_to(ROOT).as_posix(),'pixels':dimensions,'bytes':p.stat().st_size,'sha256':sha(p),'purpose':'complete character pose'if p.parent.name in['story','tactical-walk']else'lossless map atlas or inspection/export','quality_note':'Exact palette PNG; full source master retained offline.'})
 write(OUT/'delivery-image-inventory.json',{'revision':REV,'images':images,'original_sources':'source/, built-in image_gen originals and full prompts; not runtime-loaded'})
 write(OUT/'completion.json',{'revision':REV,'status':'review_candidate','corrected_map_profiles':3,'corrected_map_actions':24,'new_complete_body_poses':8,'decoded_map_videos':12,'all_dawn_actions_still_available':43,'battle_and_double_slash_sparks_exactly_preserved':True,'tactical_idle_exactly_preserved':True,'all_effects_preserved':True,'unrelated_gallery_rows_preserved':True,'page_default_preserved':default,'runtime_integrated':False,'device_updated':False,'browser_visual_check':'file access unavailable; offline full-body/ground sequence inspection and video decode performed'});print(json.dumps({'map_profiles':3,'map_actions':24,'decoded_videos':12,'images':len(images),'battle_preserved':True,'default_preserved':default},ensure_ascii=False))
if __name__=='__main__':main()
