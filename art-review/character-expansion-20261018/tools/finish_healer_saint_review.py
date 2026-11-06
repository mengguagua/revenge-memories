#!/usr/bin/env python3
"""Sync approved job terminology and publish the allied healer/saint review."""
import json,re,html
from html.parser import HTMLParser
from urllib.parse import urlparse,parse_qs,unquote
from PIL import Image
from build_gallery import ROOT,file_hash
from prepare_healer_saint_complete import REV,OUT,write
def a(label,aid):return f'<a href="?action={aid}#motion-player">{label}</a>'
def catalog(data):
 source=json.loads((ROOT/'catalog/class-catalog.json').read_text());names=json.loads((ROOT.parents[1]/'actual/data/class_names.json').read_text());records=[];rows=[]
 for c in source['classes']:
  cid=c['class_id'];n=names.get(str(cid),{});ally=n.get('name_zh',c['name']);enemy=n.get('enemy_name_zh',c['enemy_source_name']);cells=[];art={}
  for side in['ally','enemy']:
   ps=[p for p in data['profiles']if str(p['classId'])==str(cid)and p['side']==side];parts=[];art[side]={}
   for ctx,label in[('tactical-idle','待机'),('tactical-walk','行走'),('battle','战斗')]:
    matches=[x for p in ps if p['context']==ctx for x in data['actions']if x['profile']==p['id']and x['ready']];matches.sort(key=lambda x:('professions-class-'not in x['id'],x['kind']=='reaction',len(x['id'])))
    if matches and cid not in[23,24]:parts.append(a(label,matches[0]['id']));art[side][ctx]=matches[0]['id']
   cells.append(''.join(parts)or('<span class="muted">原作留档</span>'if cid in[23,24]else'<span class="muted">待制作</span>'))
  records.append({'class_id':cid,'ally':ally,'enemy':enemy,'source_ally':c['name'],'source_enemy':c['enemy_source_name'],'gallery_coverage':art,'source_archive_only':cid in[23,24]});rows.append(f'<tr><td>{cid}</td><td>{html.escape(ally)}</td><td>{html.escape(enemy)}</td><td>{cells[0]}</td><td>{cells[1]}</td></tr>')
 heroes=[{'actor':'胡纳普','base':'战士','advanced':'破晓勇士','underlying_class_id':21,'marker':'hero_profession','art_status':'专属进阶新形象待单独制作'},{'actor':'艾琳','base':'女魔剑士','advanced':'引光剑使','underlying_class_id':11,'marker':'hero_profession','art_status':'专属进阶新形象待单独制作'}]
 eileen_ready=any(p.get('actor')=='eileen'and p.get('heroProfession')=='light_guide'for p in data['profiles'])
 if eileen_ready:heroes[1]['art_status']='双阶段专属全动作已完成，待验收'
 write(OUT/'profession-catalog-sync.json',{'reference_thread':'codex://threads/01a1676d-d26b-7992-acd6-1335649650d5','name_source':'actual/data/class_names.json','name_source_sha256':file_hash(ROOT.parents[1]/'actual/data/class_names.json'),'classes':records,'exclusive_heroes':heroes,'same_source_number_does_not_merge_enemy_identity':True,'runtime_changed':False})
 hero_note='艾琳双阶段专属形象已完成，见本页艾琳全动作入口；胡纳普的专属进阶新形象待单独制作。'if eileen_ready else'专属进阶新形象待单独制作。'
 return '<section id="profession-catalog-sync" style="margin-bottom:24px"><details class="profession-overview"><summary>职业总览 · 我方、敌方与主角专属进阶</summary><p class="action-note">已同步“优化问题1”的现行名称。同编号的敌方特殊职业独立列出；“待制作”指本对照页的新重绘素材，不表示游戏中未实装。原作编号23勇者、24公主作为留档，不能代替主角专属职业。</p><div class="profession-table-wrap"><table class="profession-table"><thead><tr><th>原作编号</th><th>我方职业</th><th>敌方职业</th><th>我方重绘入口</th><th>敌方重绘入口</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table></div><p class="action-note">主角专属：胡纳普 · 战士 → 破晓勇士；艾琳 · 女魔剑士 → 引光剑使。两者分别沿用原作编号21、11并用专属标记区分，本页普通职业不会一并改名。'+hero_note+'</p><nav class="links" style="margin-top:14px" aria-label="职业梳理依据"><a href="codex://threads/01a1676d-d26b-7992-acd6-1335649650d5">职业梳理对话</a><a href="'+REV+'/profession-catalog-sync.json">名称与重绘覆盖记录</a></nav></details></section>\n'
def main():
 d=json.loads((ROOT/'demos/gallery-data.json').read_text());sections=[]
 for c in[18,17]:
  name='疗愈师'if c==18 else'济世术师';prefix=f'professions-class-{c}-ally-';links=[]
  for label,key in[('待机','maps-tactical-idle--idle-cycle'),('向上','maps-tactical-walk--walk-up'),('向右','maps-tactical-walk--walk-right'),('向下','maps-tactical-walk--walk-down'),('向左','maps-tactical-walk--walk-left'),('战斗待机','battle--reaction-idle'),('恢复',f'battle--class_{c}_ally_item_40'),('远程恢复',f'battle--class_{c}_ally_item_41'),('吸血',f'battle--class_{c}_ally_item_42'),('传送',f'battle--class_{c}_ally_item_43'),('全体恢复',f'battle--class_{c}_ally_item_44')]:links.append(a(label,prefix+key))
  if c==17:
   for label,i in[('火球',23),('雷电',24),('诸神黄昏',25),('圣光',26),('风刃',27),('箭雨',28),('光环',29),('鬼火',31),('史莱姆',32)]:links.append(a(label,prefix+f'battle--class_{c}_ally_item_{i}'))
  for label,p in[('地图全姿势',f'class-{c}-maps-light.png'),('战斗全姿势',f'class-{c}-battle-light.png')]:links.append(f'<a href="{REV}/{p}">{label}</a>')
  count=sum(x['profile'].startswith(prefix)for x in d['actions']);sections.append(f'<div style="margin-top:20px"><div class="heading"><h3>我方{name}</h3><p>{count}项 · '+('细杖、白色兜帽与长袍'if c==18 else'双层白肩披、细颈圆腹宝瓶')+'</p></div><nav class="links" aria-label="'+name+'全动作">'+''.join(links)+'</nav></div>')
 section='<section id="healer-saint-progress" style="margin-bottom:26px" aria-label="本轮疗愈师与济世术师全动作"><div class="heading"><h2>疗愈师 → 济世术师 · 我方全动作</h2><p>蓝白与少量玉绿 · 纯色头发、哑光衣袍</p></div>'+''.join(sections)+'<p class="action-note">本轮两职业共140项，包含地图待机、四向行走、四向停止，及战斗原作全部动作变体。头颈与躯干固定，长袍下按原作换步，保留连续阴影。济世术师以分层白肩披、长披巾和宝瓶加强进阶感；宝瓶细颈、圆腹及底座保持完整。战斗保留原作持杖举手、伸臂、举臂、收势的顺序与节奏，同名攻击法术复用已确认特效；恢复保留绿色光环和雨滴收尾。法术列表是职业动作样板，角色实际使用仍按各自已学会的法术，未新增能力。仅更新美术对照，待视觉验收。</p><nav class="links" style="margin-top:14px" aria-label="本轮制作记录"><a href="'+REV+'/README.md">制作与检查记录</a><a href="'+REV+'/verification.json">针对性验证</a></nav></section>\n'
 page=ROOT/'index.html';s=page.read_text();s=re.sub(r'<body data-default-action="[^"]+"','<body data-default-action="professions-class-17-ally-maps-tactical-idle--idle-cycle"',s,count=1);s=re.sub(r'<span class="badge">[^<]+</span>','<span class="badge">疗愈师 / 济世术师 · 全动作</span>',s,count=1)
 s=re.sub(r'(<p class="action-note" id="profession-name-note"[^>]*>).*?</p>',r'\g<1>职业已同步现行设定：乡勇；士兵→重装兵→壁垒卫士；骑兵→骑士→大骑士；佣兵→剑士→剑豪；弓箭手→狙击手→弓骑士；天马骑士→隼骑士；术法师→博学术师；女法师→女魔剑士；疗愈师→济世术师。敌方特殊职业分别为石翼兽、骸翼兽、蚀躯、断路匪、执令术师、隙行术师、骸卫、裂目兽、驭魔师、神躯。</p>',s,count=1,flags=re.S)
 for sid in['healer-saint-progress','profession-catalog-sync']:s=re.sub(r'<section id="'+sid+r'".*?</section>\s*','',s,flags=re.S)
 s=s.replace('<section id="infantry-progression"',catalog(d)+section+'<section id="infantry-progression"',1)
 css='.profession-overview{padding:18px 20px;background:var(--panel2);border-radius:12px}.profession-overview summary{cursor:pointer;color:var(--mint);font-weight:600;padding:8px 4px}.profession-overview .action-note{margin:14px 0;max-width:1050px}.profession-table-wrap{overflow:auto;margin-top:18px}.profession-table{width:100%;border-collapse:separate;border-spacing:0 6px;min-width:680px;text-align:center;font-size:13px}.profession-table th,.profession-table td{padding:12px 16px;background:var(--panel);vertical-align:middle}.profession-table th{font-weight:500;color:var(--muted)}.profession-table td:first-child{color:var(--muted);border-radius:7px 0 0 7px}.profession-table td:last-child{border-radius:0 7px 7px 0}.profession-table a{display:inline-block;padding:5px 8px;margin:2px;color:var(--mint);text-decoration:none;border-radius:6px;background:var(--panel2)}'
 if'.profession-overview{'not in s:s=s.replace('</style>',css+'\n</style>',1)
 s=re.sub(r'(gallery-data\.js\?v=)[^" ]+',r'\g<1>'+REV,s);s=re.sub(r'(tools/gallery\.js\?v=)[^" ]+',r'\g<1>'+REV,s)
 available={a['id']for a in d['actions']};pending=[]
 def pending_link(m):
  href,label=m.groups();aid=parse_qs(urlparse(html.unescape(href)).query).get('action',[None])[0]
  if aid is None or aid in available:return m.group(0)
  pending.append(aid);return '<span class="review-pending-link" data-pending-href="'+html.escape(html.unescape(href),quote=True)+'">'+label+' · 待制作</span>'
 def restore_link(m):
  href,label=m.groups();aid=parse_qs(urlparse(html.unescape(href)).query).get('action',[None])[0]
  return '<a href="'+href+'">'+label.removesuffix(' · 待制作')+'</a>'if aid in available else m.group(0)
 s=re.sub(r'<span class="review-pending-link" data-pending-href="([^"]+)">(.*?)</span>',restore_link,s)
 s=re.sub(r'<a href="([^"]+)">(.*?)</a>',pending_link,s)
 if'.links .review-pending-link{'not in s:s=s.replace('</style>','.links .review-pending-link{display:inline-block;color:var(--muted);padding:8px 14px;background:var(--panel2);border-radius:8px;font-size:12px;opacity:.75}\n</style>',1)
 page.write_text(s)
 if(OUT/'export-report.json').exists():
  report=json.loads((OUT/'verification.json').read_text());assert report['status']=='passed';ex=json.loads((OUT/'export-report.json').read_text());paths=set(OUT.glob('**/*.png'))|{ROOT/e['still']for e in ex['exports']if e.get('still')};images=[]
  for path in sorted(paths):
   source=OUT/'source'in path.parents;sprite=path.stem.startswith('frame-');purpose='离线原作／生成源图'if source else'角色交付单帧'if sprite else'图集／检查图'
   with Image.open(path)as im:r={'path':path.relative_to(ROOT).as_posix(),'purpose':purpose,'dimensions':list(im.size),'mode':im.mode,'bytes':path.stat().st_size,'sha256':file_hash(path),'source_only':source}
   if not source and r['bytes']>=200000:r['quality_reason']='无损检查图，保留完整画面与原尺寸像素，未为体积降低质量'
   images.append(r)
  sprites=[r for r in images if r['purpose']=='角色交付单帧'];assert len(sprites)==42 and all(r['bytes']<50000 for r in sprites);write(OUT/'image-inventory.json',{'revision':REV,'images':images,'sprites':len(sprites),'sprite_max_bytes':max(r['bytes']for r in sprites),'source_quality_preserved':True})
  class Page(HTMLParser):
   def __init__(self):super().__init__();self.ids=[];self.links=[];self.default=None
   def handle_starttag(self,tag,attrs):
    attrs=dict(attrs)
    if'id'in attrs:self.ids.append(attrs['id'])
    if'href'in attrs:self.links.append(attrs['href'])
    if tag=='body':self.default=attrs.get('data-default-action')
  p=Page();p.feed(s);actions={a['id']:a for a in d['actions']};assert len(p.ids)==len(set(p.ids))and actions[p.default]['ready']and actions[p.default]['video'];checked=0
  for href in p.links:
   u=urlparse(href)
   for aid in parse_qs(u.query).get('action',[]):assert aid in actions;checked+=1
   if REV+'/'in u.path:assert(ROOT/unquote(u.path)).exists(),href
  for href in re.findall(r'\]\(([^)]+)\)',(OUT/'README.md').read_text()):assert(OUT/href).resolve().exists(),href
  js=(ROOT/'gallery-data.js').read_text();assert json.loads(js[len('window.GALLERY_DATA = '):].strip().rstrip(';'))==d
  report.update(page_action_links_checked=checked,page_unique_ids=True,profession_catalog_rows=24,exclusive_hero_jobs_separate=True,image_inventory_count=len(images),other_pending_action_links=pending,page_text_safe_area_checked='Static table padding and wrapping; measured centered offline export captions. Browser rendering not tested.');write(OUT/'verification.json',report)
 print(json.dumps({'profession_rows':24,'current_profession_actions':140,'default':'saint-idle'}),flush=True)
if __name__=='__main__':main()
