#!/usr/bin/env python3
"""Publish reviewed media and narrowly add Dawn Warrior's review navigation."""
import hashlib,json,re
from pathlib import Path
from urllib.parse import urlsplit,unquote
from PIL import Image
import integrate_hunapu_dawn_v1 as I
ROOT=I.ROOT;OUT=I.OUT;REV=I.art.REV
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):I.write(p,d)
def main():
 data=I.build();verification=I.verify(data);exports=json.loads((OUT/'export-report.json').read_text());assert len(exports['decoded_videos'])==25
 for a in data['actions']:
  p=ROOT/'demos/stills'/(a['id']+'.png');assert p.exists()and json.loads(p.with_suffix('.json').read_text())['contentDigest']==a['contentDigest']
 for v in exports['decoded_videos']:
  p=ROOT/v['path'];aid=p.stem.removesuffix('--close');a=next(a for a in data['actions']if a['id']==aid);assert json.loads(p.with_suffix('.json').read_text())['contentDigest']==a['contentDigest']
 I.boards(data);I.merge(data)
 actions=[]
 for a in data['actions']:
  if a['kind']!='attack':continue
  poses={str(i):next(t+1 for t,r in enumerate(a['frames'])if r['frame']==i)for i in dict.fromkeys(r['frame']for r in a['frames'])};actions.append({'character_id':1,'actor':'hunapu','hero_profession':'dawn_warrior','underlying_class_id':21,'action_id':a['id'],'current_behavior':a['name'],'required_equipment':'compatible bow actually carried'if'bow'in a['key']else'item15 引霆剑 actually carried'if'levin'in a['key']else'current compatible sword; critical conditional on actual result'if'critical'in a['key']else'current compatible sword','ticks':len(a['frames']),'fps':a['fps'],'contact_tick_zero_based':a['contactTick'],'contact_frame_one_based':a['contactTick']+1,'pose_first_frame_one_based':poses,'native_timeline_exact':True,'new_extra_hit_or_ability':False})
 write(OUT/'action-effect-mapping.json',{'revision':REV,'character_id':1,'cards_note':'Current project defines equipment and native attack variants; no independent new card or item is introduced by these visuals.','story_armaments':{'15':'引霆剑','18':'守约剑, personal character1 and actual inventory required'},'actions':actions})
 path=ROOT/'index.html';before=path.read_text();default=re.search(r'data-default-action="([^"]+)"',before).group(1)
 def link(label,action):return f'<a href="?action=hunapu-promoted-{action}#motion-player">{label}</a>'
 links=[link('剧情地图','maps-story--walk-down'),link('大地图 · 复用剧情形象','maps-world--walk-down'),link('战斗地图 · 待机','maps-tactical-idle--idle-cycle')]
 links+=[link('战斗地图 · '+label,'maps-tactical-walk--walk-'+key)for key,label in[('up','向上'),('right','向右'),('down','向下'),('left','向左')]]
 links+=[link(label,'battle--'+key)for label,key in[('普通攻击','original_class_21_promoted'),('必杀 · 跃起重斩','original_class_21_critical'),('持弓攻击','class_21_ally_bow'),('引霆剑 · 装备攻击','class_21_ally_levin'),('战斗待机','reaction-idle'),('受击','reaction-hit'),('退场','reaction-exit')]]
 records=[('地图全姿势','maps-light.png'),('剑术全姿势','sword-light.png'),('必杀全姿势','critical-light.png'),('剑与弓装备姿势','equipment-light.png'),('连续动作检查','normal-sequence-dark.png'),('制作与验证记录','README.md')]
 section='<section class="panel" id="hunapu-dawn-progress" aria-label="胡纳普破晓勇士全动作" style="margin-bottom:24px">\n<div class="heading"><h2>胡纳普 · 破晓勇士全动作</h2><p>浅蓝护甲、深蓝战衣、新剑型 · 待验收</p></div>\n<p class="action-note" style="margin:0 0 16px">延续战士的短蓝发与年轻面孔，以浅蓝胸肩甲、护膝、深蓝分片战衣和短肩披强化进阶感，减少咖啡色。长剑依参考图重做银色镂空剑身、蓝色中脊、圆形深蓝护手与短蓝羽带；头发纯色，衣料哑光，保留必要的阴影和轮廓。</p>\n<nav class="links" aria-label="破晓勇士场景与动作">'+''.join(links)+'</nav>\n<p class="action-note" style="margin-top:14px">剧情与大地图复用同套人物；战斗地图另做持剑盾待机、四向行走与停止，固定头颈和躯干，保留换步及阴影。普通攻击加强前冲、蓄力与单次挥斩，必杀加强跃起、蜷腿和重斩；持弓动作单独制作并统一脚底。共5组场景、43项动作，包含原有距离／目标变体与通用反馈；原结算时刻和攻击次数保留，能力取实际装备。原战士形象保留。本轮仅更新美术对照。</p>\n<nav class="links" aria-label="破晓勇士姿势与制作记录" style="margin-top:14px">'+''.join(f'<a href="{REV}/{file}">{label}</a>'for label,file in records)+'</nav>\n</section>\n'
 if 'id="hunapu-dawn-progress"'in before:after=re.sub(r'<section\b[^>]*id="hunapu-dawn-progress".*?</section>\s*',section,before,count=1,flags=re.S)
 else:
  mark='<section class="panel" id="journey-home"';assert before.count(mark)==1;after=before.replace(mark,section+mark,1)
 after=after.replace('胡纳普的专属进阶新形象待单独制作。','胡纳普的破晓勇士全场景43项动作已完成，见本页专属入口，待视觉验收。')
 rowmatch=re.search(r'<tr><td>21</td>.*?</tr>',after,re.S);assert rowmatch
 row=rowmatch.group();cells=re.findall(r'<td>(.*?)</td>',row,re.S);assert len(cells)==5
 if 'hunapu-promoted-'not in cells[3]:cells[3]+='<br>'+link('破晓勇士 · 待机','maps-tactical-idle--idle-cycle')+link('破晓勇士 · 战斗','battle--original_class_21_promoted')
 after=after[:rowmatch.start()]+'<tr>'+''.join('<td>'+c+'</td>'for c in cells)+'</tr>'+after[rowmatch.end():]
 t=re.search(r'<section\b[^>]*id="thunder-impact-progress".*?</section>',after,re.S)
 if t:after=after[:t.start()]+t.group().replace('先冲击地面，再电弧分裂 · 待验收','先冲击地面，再电弧分裂 · 已确认')+after[t.end():]
 after=re.sub(r'(src="gallery-data\.js\?[^"&]*(?:&[^"&]*)*)"',lambda m:m.group(1)+'"'if'&hunapu_dawn='in m.group(1)else m.group(1)+'&hunapu_dawn=20261024"',after,count=1)
 assert re.search(r'data-default-action="([^"]+)"',after).group(1)==default
 for href in re.findall(r'href="([^"]+)"',section):
  u=urlsplit(href)
  if u.query:
   aid=unquote(u.query.removeprefix('action='));assert any(a['id']==aid for a in data['actions']),aid
  else:assert(ROOT/u.path).is_file(),href
 assert path.read_text()==before,'Page changed concurrently; re-read latest before retrying';path.write_text(after)
 cp=ROOT/'healer-saint-complete-v1-20261023/profession-catalog-sync.json';catalog=json.loads(cp.read_text());row=next(h for h in catalog['exclusive_heroes']if h['actor']=='胡纳普');row.update(art_status='专属进阶全场景43项动作已完成，待验收',review_revision=REV,review_profiles=[p['id']for p in data['profiles']],runtime_integrated=False);write(cp,catalog)
 images=[]
 files=list(OUT.rglob('*.png'))+[ROOT/'demos/stills'/(a['id']+'.png')for a in data['actions']]+[ROOT/'demos/stills'/(a['id']+'--close.png')for a in data['actions']if a.get('defaultVideo')and a['kind']=='attack']
 for p in sorted(set(files)):
  if p.is_relative_to(OUT)and 'source'in p.relative_to(OUT).parts:continue
  with Image.open(p)as im:size=list(im.size)
  images.append({'path':p.relative_to(ROOT).as_posix(),'pixels':size,'bytes':p.stat().st_size,'sha256':sha(p),'purpose':'individual character frame'if p.parent.name in['battle','story','tactical-walk','tactical-idle']else'pose atlas or offline inspection/export','quality_note':'Exact palette PNG; no lossy resizing for size target. Large inspection boards retained at readable pixel scale.'})
 write(OUT/'delivery-image-inventory.json',{'revision':REV,'images':images,'individual_character_frames_max_bytes':max(r['bytes']for r in images if r['purpose']=='individual character frame'),'original_generated_masters':'source/, retained offline; never runtime-loaded'})
 scope=json.loads((OUT/'runtime-scope-baseline.json').read_text());changed=[p for p,h in scope.items()if sha(Path(p))!=h]
 write(OUT/'completion.json',{'revision':REV,'status':'review_candidate','profiles':5,'actions':43,'decoded_videos':25,'image_files':len(images),'page_action_links_valid':True,'page_default_preserved':default,'all_unrelated_gallery_rows_preserved':True,'runtime_files_changed_since_scope_snapshot':changed,'runtime_integrated':False,'device_updated':False,'browser_visual_check':'Unavailable for file://; offline dark/light and animation compositing inspected.'})
 assert not changed,changed;print(json.dumps({'profiles':5,'actions':43,'videos':25,'images':len(images),'default_preserved':default,'runtime_changed':changed},ensure_ascii=False))
if __name__=='__main__':main()
