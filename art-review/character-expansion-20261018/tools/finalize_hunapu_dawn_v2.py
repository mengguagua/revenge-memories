#!/usr/bin/env python3
"""Finish the five requested art corrections without altering unrelated reviews."""
import hashlib,json,re
from pathlib import Path
from urllib.parse import urlsplit
from PIL import Image
import integrate_hunapu_dawn_v2 as I
ROOT=I.ROOT;OUT=I.OUT;REV=I.art.REV
def write(p,d):I.write(p,d)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 data=I.build();v=I.verify(data);ex=json.loads((OUT/'export-report.json').read_text());assert len(ex['decoded_videos'])==25
 for a in data['actions']:
  assert a.get('still'),a['id']
  if a.get('defaultVideo'):assert a.get('video')and(a.get('closeVideo')if a['kind']=='attack'else True),a['id']
 I.boards(data);I.merge(data)
 timeline=json.loads((OUT/'review-timeline.json').read_text());write(OUT/'action-effect-mapping.json',{'actor':'hunapu','character_id':1,'class_id':21,'hero_profession':'dawn_warrior','equipment':'current compatible sword; bow and 引霆剑 remain equipment gated','visual_slash_count':2,'normal':{'first_contact_tick':95,'second_visual_cut_tick':112,'total_ticks':208},'critical':{'first_contact_tick':166,'second_visual_cut_tick':183,'spark_peak_ticks':[166,183],'total_ticks':263},'runtime_damage_changed':False,'full_review_timeline':'review-timeline.json','only_two_revised_actions':list(timeline['actions'])})
 page=ROOT/'index.html';before=page.read_text();default=re.search(r'data-default-action="([^"]+)"',before).group(1)
 def action(label,suffix):return f'<a href="?action=hunapu-promoted-{suffix}#motion-player">{label}</a>'
 nav=[action('剧情 · 向上换腿','maps-story--walk-up'),action('剧情 · 侧向站直／跨步','maps-story--walk-right'),action('大地图 · 复用剧情','maps-world--walk-up'),action('战斗地图 · 待机','maps-tactical-idle--idle-cycle')]
 nav+=[action('战斗地图 · '+label,'maps-tactical-walk--walk-'+key)for key,label in[('up','向上'),('right','向右'),('down','向下'),('left','向左')]]
 nav+=[action(label,'battle--'+key)for label,key in[('普通攻击 · 接第二剑','original_class_21_promoted'),('必杀 · 接第二剑与火花','original_class_21_critical'),('持弓','class_21_ally_bow'),('引霆剑','class_21_ally_levin'),('战斗待机','reaction-idle'),('受击','reaction-hit'),('退场','reaction-exit')]]
 docs=[('地图姿势与剑盾位置','maps-light.png'),('普通攻击连续帧','normal-followup-dark.png'),('必杀与火花连续帧','critical-followup-dark.png'),('追加剑术姿势','combo-light.png'),('本轮五项修订与检查','README.md')]
 section='<section class="panel" id="hunapu-dawn-progress" aria-label="胡纳普破晓勇士步态与连斩修订" style="margin-bottom:24px">\n<div class="heading"><h2>胡纳普 · 破晓勇士全动作</h2><p>步态、持手、集中阴影与第二剑 · 待验收</p></div>\n<p class="action-note" style="margin:0 0 16px">本轮修正向上行走的左右腿交替；左右行走改为站直与跨步交替，固定头颈和上身。战斗地图阴影集中在脚下，剑盾按左手剑、右手盾分别制作两侧遮挡；手握护手下方剑柄。剧情形象继续与大地图复用。</p>\n<nav class="links" aria-label="破晓勇士场景与修订动作">'+''.join(nav)+'</nav>\n<p class="action-note" style="margin-top:14px">普通攻击与必杀在原斩击后，经低位回收、蓄势、顺势上挑再接完整一剑，并回防退回。必杀落斩与回斩加入短促火花，从亮芯爆开到飞散、消退。保留浅蓝护甲、深蓝战衣、纯色蓝发与银色镂空蓝脊剑。共5组场景、43项动作；原第一击结算、位移与总时长保留。本轮仅更新美术对照。</p>\n<nav class="links" aria-label="破晓勇士修订检查记录" style="margin-top:14px">'+''.join(f'<a href="{REV}/{file}">{label}</a>'for label,file in docs)+'</nav>\n</section>\n'
 pattern=r'<section\b[^>]*id="hunapu-dawn-progress".*?</section>\s*';assert len(re.findall(pattern,before,re.S))==1;after=re.sub(pattern,section,before,count=1,flags=re.S)
 after=re.sub(r'(src="gallery-data\.js\?[^"&]*(?:&[^"&]*)*)"',lambda m:re.sub(r'&hunapu_dawn=[^"&]+','',m.group(1))+'&hunapu_dawn=gait-combo-v2-20261024"',after,count=1)
 assert re.search(r'data-default-action="([^"]+)"',after).group(1)==default
 for href in re.findall(r'href="([^"]+)"',section):
  u=urlsplit(href)
  if u.query:assert u.query.removeprefix('action=')in{a['id']for a in data['actions']}
  else:assert(ROOT/u.path).is_file(),href
 assert page.read_text()==before,'Page changed concurrently';page.write_text(after)
 cp=ROOT/'healer-saint-complete-v1-20261023/profession-catalog-sync.json';catalog=json.loads(cp.read_text());h=next(h for h in catalog['exclusive_heroes']if h['actor']=='胡纳普');h.update(art_status='专属进阶43项已完成；步态、持手与双剑演出已修订，待验收',review_revision=REV,runtime_integrated=False);write(cp,catalog)
 manifest=ROOT/'hunapu-promoted/manifest.json';m=json.loads(manifest.read_text());m.update(revision=REV,status='review_candidate',runtime_integrated=False,review_record='../'+REV+'/README.md');write(manifest,m)
 files=[p for p in OUT.rglob('*.png')if 'source'not in p.relative_to(OUT).parts]+[ROOT/'demos/stills'/(a['id']+'.png')for a in data['actions']]+[ROOT/'demos/stills'/(a['id']+'--close.png')for a in data['actions']if a.get('defaultVideo')and a['kind']=='attack'];inventory=[]
 for p in sorted(set(files)):
  with Image.open(p)as im:size=list(im.size)
  inventory.append({'path':p.relative_to(ROOT).as_posix(),'pixels':size,'bytes':p.stat().st_size,'sha256':sha(p),'purpose':'character frame'if p.parent.name in['battle','story','tactical-walk','tactical-idle']else'pixel effect phase'if p.parent.name=='effects'else'pose board, atlas or exported inspection','quality_note':'Lossless palette PNG; authored source preserved separately.'})
 write(OUT/'delivery-image-inventory.json',{'revision':REV,'images':inventory,'reused_shadow':next(p['mapShadow']for p in data['profiles']if p['id']=='hunapu-promoted-maps-tactical-walk'),'original_sources':'source/, retained offline'})
 write(OUT/'completion.json',{'revision':REV,'five_requested_changes_complete':True,'status':'review_candidate','profiles':5,'actions':43,'decoded_videos':25,'image_files':len(inventory),'native_rows_contacts_and_durations_preserved':True,'new_visual_slashes':{'normal':1,'critical':1},'critical_spark_groups':2,'page_default_preserved':default,'unrelated_records_preserved':True,'runtime_integrated':False,'device_installed_or_updated':False,'visual_check':'Dark/light authored-pose boards, offline map ground and shadow panels, and original-plus-revised continuous attack frames; browser file access unavailable.'});print(json.dumps({'actions':43,'videos':25,'images':len(inventory),'default_preserved':default},ensure_ascii=False))
if __name__=='__main__':main()
