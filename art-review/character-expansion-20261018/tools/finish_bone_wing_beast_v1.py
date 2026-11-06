#!/usr/bin/env python3
"""Offline media inspection, review entry, and scoped delivery audit."""
import argparse,copy,hashlib,json,re,subprocess
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs,urlsplit,unquote
from PIL import Image,ImageDraw,ImageChops
import import_bone_wing_beast_v1 as A
import integrate_bone_wing_beast_v1 as I
from export_gallery import font
ROOT=A.ROOT;OUT=A.OUT;REV=A.REV
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def board(images,path,columns=3):
 w,h=560,430;out=Image.new('RGB',(w*columns,46+h*((len(images)+columns-1)//columns)),(220,222,216));d=ImageDraw.Draw(out)
 d.text((out.width/2,23),'骸翼兽 · 已编码视频连续帧检查',font=font(21),anchor='mm',fill=(35,51,74))
 for i,(label,im)in enumerate(images):
  im=im.copy();im.thumbnail((w-24,h-48),Image.Resampling.NEAREST);x=i%columns*w+(w-im.width)//2;y=46+i//columns*h
  out.paste(im,(x,y));d.text((i%columns*w+w/2,y+h-25),label,font=font(16),anchor='mm',fill=(35,51,74))
 out.save(path,optimize=True)
def qa():
 data=read(OUT/'gallery-data.json');actions={a['key']:a for a in data['actions']};dest=OUT/'decoded';dest.mkdir(exist_ok=True);records=[]
 requests=[('idle-cycle',[0,14,22,36,44,87]),('walk-up',[0,15,16,31,32,95]),('walk-right',[0,15,16,31]),('walk-down',[0,15,16,31]),('walk-left',[0,15,16,31]),('original_class_5_enemy_normal',[0,20,42,48,54,57,60,62,243,279,394,505]),('innate-bone-bite',[0,23,24,38,39,57]),('innate-eroding-breath',[0,19,20,34,35,53])]
 maps=[];native=[];innate=[]
 for key,ticks in requests:
  a=actions[key];p=dest/key;p.mkdir(exist_ok=True);video=ROOT/a['video'];assert video.exists()
  pattern=p/'frame-%03d.png';select='+'.join(f'eq(n\\,{t})'for t in ticks)
  subprocess.run(['/opt/homebrew/bin/ffmpeg','-v','error','-y','-i',str(video),'-vf','select='+select,'-vsync','0',str(pattern)],check=True)
  files=sorted(p.glob('frame-*.png'));assert len(files)==len(ticks)
  for tick,file in zip(ticks,files):
   im=Image.open(file).convert('RGB');crop=im.crop((im.width//2+12,76,im.width-24,im.height-60))
   label=f'{a["name"]} · 第{tick+1}帧';item=(label,crop)
   (maps if a['context']!='battle'else native if key=='original_class_5_enemy_normal'else innate).append(item)
   records.append({'action':a['id'],'tick':tick,'file':file.relative_to(ROOT).as_posix(),'dimensions':list(im.size),'bytes':file.stat().st_size})
 board(maps,OUT/'decoded-maps.png',4);board(native,OUT/'decoded-native-attack.png',4);board(innate,OUT/'decoded-current-innates.png',3)
 a=actions['innate-eroding-breath'];p=dest/'breath-close';p.mkdir(exist_ok=True);ticks=[20,27,34];select='+'.join(f'eq(n\\,{t})'for t in ticks)
 subprocess.run(['/opt/homebrew/bin/ffmpeg','-v','error','-y','-i',str(ROOT/a['closeVideo']),'-vf','select='+select,'-vsync','0',str(p/'frame-%03d.png')],check=True);close=[]
 for tick,file in zip(ticks,sorted(p.glob('frame-*.png'))):
  im=Image.open(file).convert('RGB');close.append((f'蚀息近景 · 第{tick+1}帧',im.crop((im.width//2+12,76,im.width-24,im.height-60))));records.append({'action':a['id'],'mode':'close','tick':tick,'file':file.relative_to(ROOT).as_posix(),'dimensions':list(im.size),'bytes':file.stat().st_size})
 board(close,OUT/'decoded-breath-close.png',3)
 A.write(OUT/'decoded-frame-audit.json',{'method':'ffmpeg decode of final MP4; no browser or live game capture','frames':records,'browser_visual_inspection':False})
def docs():
 text='''# 骸翼兽 · 全动作重绘 V1

本轮为「角色重绘 · 全动作对照」的美术候选，待用户视觉验收。仅制作并发布对照素材；未修改游戏运行场景、技能定义、数据或设备安装。

## 形象与部位

原作职业5敌方为骨龙，并非骑乘单位。长颅骨和颈椎位于身前，弓起的胸廓／脊骨位于身后高处；近侧前爪叠在胸前，远爪与远翼置于胸廓后，卷尾在身后。翼指从肩关节抬起、展开、向前下方形成弧形、继续下拍；不把翼骨解释成手臂或武器。

采用柔和蓝紫翼膜、浅薰衣草骨骼、深蓝轮廓及小面积低饱和琥珀眼睛，参考敌方剑豪的蓝紫关系。保留结构阴影，没有发光、光泽高光或散乱亮点；骨龙没有头发和衣服。九色为23334a、3c4766、555879、787ba1、929bb6、bac4d8、d0d7df、ba985e、6a637f。

## 动作与时序

| 内容 | 原作／现行依据 | 本轮处理 |
| --- | --- | --- |
| 地图待机 | 0→1→2→1，每相14／8／14／8 ticks | 两遍88帧；固定头、胸廓、爪和尾部，只活动翼指 |
| 四向飞移 | 每方向低翼／高翼各16 ticks，32帧循环 | 三遍96帧；固定头、胸廓、骨盆，左右为严格镜像；停止保留该方向第一姿势 |
| 原作普通攻击 | 507 ticks，60.0988 fps，第244显示帧结算 | 动作槽、顺序、位移、转身、循环及节奏逐行保留；保持高举→展开→弧形下扫→深下拍 |
| 战斗反应 | 已有通用待机／未命中／受击／退场 | 使用同一中立身体，通用反应不增加防御能力 |

原作41／48槽为16槽向左偏移16逻辑像素，已严格保留，避免OAM／背景切换时整体跳动。地图八帧与冻结CPU来源逐槽RGBA哈希一致；本轮固定的是身体核心，不以展开翅膀的包围盒重新缩放全身。PNG为4倍像素尺寸、二值透明度。

## 角色5 → 卡牌／固有能力 → 动作 → 结算

| 定义 | 当前效果 | 对照动作与触发 |
| --- | --- | --- |
| 1003 骸颚撕咬 | 物理，威力3、重量3、命中85、暴击0，范围1，不消耗HP | 50fps，共58帧；准备24 ticks，开颚前冲，tick38（显示第39帧）单次结算，然后收势回位 |
| 1004 蚀息 | 魔法，威力3、重量3、命中75、暴击0，范围2，消耗1HP | 50fps，共54帧；准备20 ticks，开颚释放现行蚀息位图，tick34（显示第35帧）单次结算 |

以上现行短动作独立列出，不冒充原作507帧程序。原作没有对应开颚近景，本轮按身份自行设计50槽；只有颅骨／下颚改变，胸廓、双翼、爪与尾部沿用18槽。蚀息复用现行火焰、原密度与方向，新稿将吐息起点校准至张颚处，命中位置和时刻保持；近景扩宽以保留完整弹道。不增加爆炸、连击次数或其他能力。定义依据为actual/core/innate_attacks.gd及actual/core/innate_attack_animation.gd，文件保持不变。

## 制作与文件

通过内置imagegen绘制身体、低翼／深下拍、地图飞移、地图待机及弧形过渡翼姿。完整源图与最终提示词保存在source/：battle-master.png／battle-prompt.txt，lower-wings-master.png／lower-wings-prompt.txt，walk-master.png／walk-prompt.txt，idle-master.png／idle-prompt.txt，wing-20-master.png／wing-20-prompt.txt。原生像素参考、部位对照、注册基准及冻结输入哈希见source/native-audit.json。

技术处理仅用于透明组件提取、统一哑光调色板、最近邻像素注册、翼部关节范围匹配、核心复用与无损索引PNG压缩。完整生成源图离线保留，不直接交给播放器加载。每个正式帧约2–12KB；完整战斗图集超过50KB参考值，保留384×544逐帧分辨率及完整深下拍翼尖，不降低质量追求体积。逐图尺寸、字节和用途见delivery-image-inventory.json。

## 验证与验收入口

- [地图深底](maps-dark.png)／[地图浅底](maps-light.png)
- [战斗深底](battle-dark.png)／[战斗浅底](battle-light.png)
- [最终视频地图连续帧](decoded-maps.png)
- [最终视频原作攻击连续帧](decoded-native-attack.png)
- [最终视频现行固有能力连续帧](decoded-current-innates.png)
- [结构、时序、中心与边界检查](verification.json)
- [19段视频的帧数、时长和尺寸核对](export-report.json)
- [最终合并与资源核对](final-validation.json)

已离线渲染深浅底、解码最终MP4检查；没有进行浏览器或可见Godot窗口验收。对照页沿用既有自适应布局和柔和焦点阴影，本轮新增入口自然换行、保留内边距。原作参考与新增稿同步，用户可逐帧或慢速验收。
'''
 (OUT/'README.md').write_text(text)
def inventory(data):
 paths=set(OUT.rglob('*.png'))
 for a in data['actions']:
  if a.get('still'):paths.add(ROOT/a['still'])
  if a.get('closeVideo'):paths.add(ROOT/a['closeVideo'].replace('/videos/','/stills/').replace('.mp4','.png'))
 records=[]
 for p in sorted(paths):
  im=Image.open(p);offline=A.SRC in p.parents
  role='离线生成源图／原作部位参考'if offline else'视频解码检查'if 'decoded'in p.parts else'4倍像素帧'if p.parent.name in['battle','tactical-idle','tactical-walk']else'图集或验收检查图'
  n=p.stat().st_size;reason=''
  if n>=50000:reason='离线源图保留，不由播放器加载'if offline else'完整图集／检查画面保留分辨率、文字和透明轮廓；无损压缩，质量优先'
  records.append({'path':p.relative_to(ROOT).as_posix(),'purpose':role,'size':list(im.size),'bytes':n,'sha256':sha(p),'over_50kb_reason':reason})
 A.write(OUT/'delivery-image-inventory.json',{'images':records,'runtime_images_replaced':False})
def page():
 p=ROOT/'index.html';before=sha(p);text=p.read_text();default='professions-class-5-enemy-battle--original_class_5_enemy_normal'
 panel='''<section class="panel" id="bone-wing-beast-progress" aria-label="敌方骸翼兽全动作" style="margin-bottom:24px">
<div class="heading"><h2>骸翼兽 · 蓝紫骨龙全动作</h2><p>待验收 · 16项动作</p></div>
<p class="action-note" style="margin:0 0 16px">地图待机与四向飞移固定头部、胸廓和骨盆，双翼按原作节奏拍动；近爪在胸前，远爪与远翼在胸后。战斗保留原作抬翼、展开、弧形下扫、深下拍及飞移回位，共507帧，第244帧结算。现行「骸颚撕咬／蚀息」另列对照，单次命中；骨骼与翼膜采用柔和蓝紫哑光配色。</p>
<nav class="links" aria-label="骸翼兽动作入口"><a href="?action=professions-class-5-enemy-maps-tactical-idle--idle-cycle#motion-player">地图待机</a><a href="?action=professions-class-5-enemy-maps-tactical-walk--walk-up#motion-player">向上飞移</a><a href="?action=professions-class-5-enemy-maps-tactical-walk--walk-right#motion-player">向右飞移</a><a href="?action=professions-class-5-enemy-maps-tactical-walk--walk-down#motion-player">向下飞移</a><a href="?action=professions-class-5-enemy-maps-tactical-walk--walk-left#motion-player">向左飞移</a><a href="?action=professions-class-5-enemy-battle--original_class_5_enemy_normal#motion-player">原作普通攻击</a><a href="?action=professions-class-5-enemy-battle--innate-bone-bite#motion-player">骸颚撕咬</a><a href="?action=professions-class-5-enemy-battle--innate-eroding-breath#motion-player">蚀息</a><a href="?action=professions-class-5-enemy-battle--reaction-idle#motion-player">战斗待机</a><a href="?action=professions-class-5-enemy-battle--reaction-hit#motion-player">受击</a><a href="?action=professions-class-5-enemy-battle--reaction-miss#motion-player">未命中</a><a href="?action=professions-class-5-enemy-battle--reaction-exit#motion-player">退场</a></nav>
<nav class="links" aria-label="骸翼兽制作检查" style="margin-top:14px"><a href="bone-wing-beast-complete-v1-20261024/maps-light.png">地图全姿势</a><a href="bone-wing-beast-complete-v1-20261024/battle-light.png">战斗全姿势</a><a href="bone-wing-beast-complete-v1-20261024/decoded-native-attack.png">原作攻击连续帧</a><a href="bone-wing-beast-complete-v1-20261024/decoded-current-innates.png">撕咬／蚀息连续帧</a><a href="bone-wing-beast-complete-v1-20261024/README.md">制作与触发对应记录</a></nav>
</section>

'''
 if 'id="bone-wing-beast-progress"'not in text:text=text.replace('<section class="panel" id="stone-wing-progress"',panel+'<section class="panel" id="stone-wing-progress"',1)
 text=re.sub(r'(<body data-default-action=")[^"]+',r'\g<1>'+default,text,count=1)
 text=re.sub(r'(<span class="badge">)[^<]+',r'\g<1>骸翼兽 · 蓝紫骨龙',text,count=1)
 match=re.search(r'<tr><td>5</td>.*?</tr>',text);assert match
 old=match.group();tds=re.findall(r'<td>.*?</td>',old);assert len(tds)==5 and '骸翼兽'in tds[2]
 links=''.join(f'<a href="?action={action}#motion-player">{label}</a>'for label,action in [('待机','professions-class-5-enemy-maps-tactical-idle--idle-cycle'),('行走','professions-class-5-enemy-maps-tactical-walk--walk-up'),('战斗',default),('蚀息','professions-class-5-enemy-battle--innate-eroding-breath')])
 new='<tr>'+''.join(tds[:4])+'<td>'+links+'</td></tr>';text=text[:match.start()]+new+text[match.end():]
 text=re.sub(r'(src="(?:gallery-data.js|tools/gallery.js)[^"]*)"',lambda m:m[1]+(''if'&bone_wing='in m[1]else'&bone_wing=v1-20261024')+'"',text)
 assert sha(p)==before;p.write_text(text)
 cat=ROOT/'healer-saint-complete-v1-20261023/profession-catalog-sync.json';c=read(cat);before_c=copy.deepcopy(c);row=next(r for r in c['classes']if r['class_id']==5);row['gallery_coverage']['enemy']={'tactical-idle':'professions-class-5-enemy-maps-tactical-idle--idle-cycle','tactical-walk':'professions-class-5-enemy-maps-tactical-walk--walk-up','battle':default};row['enemy_art_revision']=REV;row['enemy_art_identity']='柔和蓝紫骨龙；原作骨龙翼关节与动作程序；现行撕咬／蚀息另列对照'
 assert[r for r in c['classes']if r['class_id']!=5]==[r for r in before_c['classes']if r['class_id']!=5];assert row['gallery_coverage']['ally']==next(r for r in before_c['classes']if r['class_id']==5)['gallery_coverage']['ally'];A.write(cat,c)
 A.write(OUT/'page-update.json',{'index_before_sha256':before,'index_after_sha256':sha(p),'new_panel':'bone-wing-beast-progress','default_action':default,'catalog_only_class_5_enemy_changed':True,'existing_panels_preserved':True})
class Tags(HTMLParser):
 def __init__(self):super().__init__();self.ids=[];self.links=[]
 def handle_starttag(self,t,a):
  a=dict(a)
  if'id'in a:self.ids.append(a['id'])
  if'href'in a:self.links.append(a['href'])
def validate():
 local=read(OUT/'gallery-data.json');live=read(ROOT/'demos/gallery-data.json');js=(ROOT/'gallery-data.js').read_text();assert json.loads(js.split('=',1)[1].strip().removesuffix(';'))==live
 acts={a['id']:a for a in live['actions']};profiles={p['id']:p for p in live['profiles']};checks=0
 for p in local['profiles']:assert profiles[p['id']]==p;checks+=1
 for a in local['actions']:
  assert acts[a['id']]==a and a['ready']and a['video']and a['still'];checks+=1
  for field in['video','still','closeVideo']:
   if not a.get(field):continue
   file=ROOT/a[field];assert file.exists();meta=read(file.with_suffix('.json'));assert meta['contentDigest']==a['contentDigest'];checks+=1
 html=(ROOT/'index.html').read_text();tags=Tags();tags.feed(html);assert len(tags.ids)==len(set(tags.ids));assert 'bone-wing-beast-progress'in tags.ids
 panel=html.split('id="bone-wing-beast-progress"',1)[1].split('</section>',1)[0];pt=Tags();pt.feed(panel)
 for href in pt.links:
  url=urlsplit(href);action=parse_qs(url.query).get('action')
  if action:assert action[0]in acts and acts[action[0]]['ready']
  else:assert(ROOT/unquote(url.path)).is_file()
  checks+=1
 assert read(OUT/'verification.json')['passed'];assert len(read(OUT/'export-report.json')['decoded_videos'])==19
 audit=read(A.SRC/'native-audit.json');assert all(sha(ROOT/p)==audit['inputs_sha256'][k]for k,p in audit['inputs'].items())
 baseline=read(A.SRC/'baseline.json');assert all(sha(ROOT.parents[1]/p)==h for p,h in baseline['runtime_hashes'].items())
 im=Image.open(OUT/'battle/frame-050.png').convert('RGBA');base=Image.open(OUT/'battle/frame-018.png').convert('RGBA');shifted=Image.new('RGBA',base.size);shifted.alpha_composite(base,(-64,0));diff=ImageChops.difference(im,shifted);diff.paste((0,0,0,0),(0,312,124,404));assert not any(ch.getbbox()for ch in diff.split());checks+=1
 inventory(local)
 A.write(OUT/'final-validation.json',{'passed':True,'checks':checks,'profiles':3,'actions':16,'exported_videos':19,'decoded_qa_frames':len(read(OUT/'decoded-frame-audit.json')['frames']),'native_attack_frames':507,'native_display_contact_frame':244,'map_body_core_drift_pixels':0,'left_right_mirrors_exact':True,'custom_jaw_body_wings_claws_tail_exact_to_frame_18':True,'all_new_panel_links_resolve':True,'unique_html_ids':True,'gallery_js_json_equal':True,'all_target_media_digests_current':True,'runtime_files_unchanged':True,'native_sources_unchanged':True,'browser_visual_inspection':False,'scope':'review gallery only','user_acceptance':'pending'})
 print(json.dumps(read(OUT/'final-validation.json'),ensure_ascii=False))
def main():
 p=argparse.ArgumentParser();p.add_argument('--qa',action='store_true');p.add_argument('--page',action='store_true');p.add_argument('--validate',action='store_true');a=p.parse_args()
 if a.qa:qa();docs()
 if a.page:page()
 if a.validate:validate()
if __name__=='__main__':main()
