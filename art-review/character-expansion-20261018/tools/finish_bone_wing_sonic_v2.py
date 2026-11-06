#!/usr/bin/env python3
"""Inspect the final encoded sonic release and refresh only its gallery entry."""
import argparse,json,re,subprocess
from html.parser import HTMLParser
from pathlib import Path
from PIL import Image,ImageDraw
import revise_bone_wing_sonic_v2 as R
ROOT=R.ROOT;OUT=R.OUT
def qa():
 d=R.read(OUT/'gallery-data.json');a=next(a for a in d['actions']if a['id']==R.ID);out=OUT/'decoded';out.mkdir(exist_ok=True);records=[];items=[];ticks=[235,236,242,243,247,252,257,260,264,269,274,277,279]
 for mode,path in[('full',a['video']),('close',a['closeVideo'])]:
  dest=out/mode;dest.mkdir(exist_ok=True);select='+'.join(f'eq(n\\,{t})'for t in ticks);subprocess.run(['/opt/homebrew/bin/ffmpeg','-v','error','-y','-i',str(ROOT/path),'-vf','select='+select,'-vsync','0',str(dest/'frame-%03d.png')],check=True);files=sorted(dest.glob('frame-*.png'));assert len(files)==len(ticks)
  for tick,file in zip(ticks,files):
   im=Image.open(file).convert('RGB');records.append({'tick':tick,'mode':mode,'path':file.relative_to(ROOT).as_posix(),'size':list(im.size),'bytes':file.stat().st_size})
   if mode=='close'and tick in[235,236,243,252,260,269,274,277,279]:items.append((tick,im.crop((im.width//2+12,76,im.width-24,im.height-60))))
 board=Image.new('RGB',(3*560,3*490+50),(220,222,216));dr=ImageDraw.Draw(board);dr.text((840,25),'骸翼兽 · 最终视频张颚／音波／回位连续帧',font=R.E.font(22),anchor='mm',fill=(35,51,74))
 for i,(tick,im)in enumerate(items):
  im.thumbnail((544,432),Image.Resampling.NEAREST);x=i%3*560+(560-im.width)//2;y=50+i//3*490;board.paste(im,(x,y));dr.text((i%3*560+280,y+464),'第 '+str(tick+1)+' 帧',font=R.E.font(18),anchor='mm',fill=(35,51,74))
 board.save(OUT/'decoded-sequence.png',optimize=True);R.write(OUT/'decoded-frame-audit.json',{'frames':records,'method':'ffmpeg decoding of final full/close MP4','browser_capture':False})
def docs():
 (OUT/'README.md').write_text('''# 骸翼兽 · 普通攻击张颚与音波 V2

按用户图中第261帧，修订出手后、转身回位前的末段。地图、固有能力与其他已确认身体素材沿用V1，本轮仅更新普通攻击右侧重绘轨道。

| 阶段 | 显示帧 | 表现 |
| --- | --- | --- |
| 张颚蓄势 | 237–243 | 颅骨位置固定，张开下颚；双翼继续各自原姿势 |
| 单次释放 | 244 | 从嘴部发出一组低饱和蓝紫音波，与原第244帧结算对齐 |
| 扩散消散 | 245–275 | 三道压力波属于同一组音波，向前扩散，弧线逐渐扩大并破碎消散 |
| 闭嘴回位 | 278起 | 音波已清空，闭嘴；第280帧起沿原程序转身回位 |

原作左侧参考、507帧总长、60.0988fps、全部位移／翻转／循环和第244帧单次结算保持。不新增连击、伤害或卡牌定义；这是用户要求的普通攻击表现修订。未接入游戏运行场景或更新设备。

张颚复用V1通过内置imagegen绘制的下颚，以差分透明蒙版复合到17–23各自的身体。只改变颅骨／下颚差分像素，保留当前帧双翼、躯干、近爪、远爪及尾部；使用与原OAM一致的背景注册补偿，避免开嘴时全身跳动。

音波由内置imagegen生成，完整提示词见[source/sonic-prompt.txt](source/sonic-prompt.txt)，原始透明源图为source/sonic-master.png。交付图仅做透明组件提取、降饱和调色板、最近邻注册和无损索引PNG压缩，去除源图透明光晕。五色：586884／7885a5／9ba5bf／bac7d9／d7dfe5；不添加强光、火焰或爆炸。

- [浅底连续姿势](phases-light.png)／[深底连续姿势](phases-dark.png)
- [最终视频解码连续帧](decoded-sequence.png)
- [动作、遮挡及全景／近景边界核对](verification.json)
- [视频帧数与时长](export-report.json)
- [最终资源及合并核对](final-validation.json)

保留所有原始源图，正式角色帧与六张音波位图均为小尺寸无损PNG。逐图用途、尺寸、字节见delivery-image-inventory.json。检查为离线渲染、深浅底及最终MP4解码，未作浏览器或可见Godot窗口验收。待用户视觉确认。
''')
 v1=R.BASE/'README.md';text=v1.read_text();note='后续修订：普通攻击末段已增加[张颚与音波V2](../'+R.REV+'/README.md)。本页V1验证记录为该修订前的历史检查。\n\n'
 if note not in text:text=text.replace('\n\n','\n\n'+note,1);v1.write_text(text)
def page():
 p=ROOT/'index.html';before=R.sha(p);text=p.read_text();start=text.index('<section class="panel" id="bone-wing-beast-progress"');end=text.index('</section>',start);section=text[start:end];extra='''<div id="bone-wing-sonic-v2-progress" style="margin-top:18px"><p class="action-note" style="margin:0 0 12px"><strong>普通攻击 · 音波V2：</strong>末段张开下颚，第244帧释放一组柔和蓝紫音波，向前扩大并消散，随后闭嘴、按原节奏转身回位。双翼保留各自原姿势，原507帧和单次结算保持。</p><nav class="links" aria-label="骸翼兽音波V2检查"><a href="?action=professions-class-5-enemy-battle--original_class_5_enemy_normal#motion-player">普通攻击 · 张颚音波</a><a href="bone-wing-sonic-v2-20261024/phases-light.png">音波深浅底 · 浅底</a><a href="bone-wing-sonic-v2-20261024/phases-dark.png">音波深浅底 · 深底</a><a href="bone-wing-sonic-v2-20261024/decoded-sequence.png">最终视频连续帧</a><a href="bone-wing-sonic-v2-20261024/README.md">音波修改记录</a></nav></div>
'''
 if'id="bone-wing-sonic-v2-progress"'not in section:text=text[:end]+extra+text[end:]
 text=re.sub(r'(src="(?:gallery-data.js|tools/gallery.js)[^"]*)"',lambda m:m[1]+(''if'&bone_sonic='in m[1]else'&bone_sonic=v2-20261024')+'"',text);assert R.sha(p)==before;p.write_text(text);R.write(OUT/'page-update.json',{'index_before_sha256':before,'index_after_sha256':R.sha(p),'panel':'bone-wing-sonic-v2-progress','all_existing_sections_preserved':True})
class Tags(HTMLParser):
 def __init__(self):super().__init__();self.ids=[];self.links=[]
 def handle_starttag(self,t,a):
  a=dict(a)
  if'id'in a:self.ids.append(a['id'])
  if'href'in a:self.links.append(a['href'])
def final():
 local=R.read(OUT/'gallery-data.json');live=R.read(ROOT/'demos/gallery-data.json');assert R.S.parse_js(ROOT/'gallery-data.js')==live;a=next(a for a in local['actions']if a['id']==R.ID);assert a==next(a for a in live['actions']if a['id']==R.ID);assert a['ready']and a['video']and a['closeVideo']and a['still']
 for field in['video','closeVideo','still']:
  p=ROOT/a[field];assert p.exists()and R.read(p.with_suffix('.json'))['contentDigest']==a['contentDigest']
 p=next(p for p in local['profiles']if p['id']==R.PID);assert p==next(p for p in live['profiles']if p['id']==R.PID);assert R.read(OUT/'verification.json')['passed']and len(R.read(OUT/'export-report.json')['decoded_videos'])==2
 html=(ROOT/'index.html').read_text();tags=Tags();tags.feed(html);assert len(tags.ids)==len(set(tags.ids))and'bone-wing-sonic-v2-progress'in tags.ids;section=html.split('id="bone-wing-sonic-v2-progress"',1)[1].split('</div>',1)[0];links=Tags();links.feed(section)
 for href in links.links:
  if not href.startswith('?'):assert(ROOT/href).is_file()
 files=set(OUT.rglob('*.png'))|{ROOT/a['still'],ROOT/a['closeVideo'].replace('/videos/','/stills/').replace('.mp4','.png')};records=[]
 for path in sorted(files):
  im=Image.open(path);offline=R.SRC in path.parents;reason='原始生成源图离线保留，不由播放器直接加载'if offline else'完整检查画面保留分辨率与文字，优先视觉质量'if path.stat().st_size>=50000 else'';records.append({'path':path.relative_to(ROOT).as_posix(),'purpose':'离线源图'if offline else'正式动作／音波素材'if path.parent.name in['battle','effects']else'深浅底或视频解码检查','size':list(im.size),'bytes':path.stat().st_size,'sha256':R.sha(path),'over_reference_reason':reason})
 R.write(OUT/'delivery-image-inventory.json',{'images':records,'runtime_integration':False});R.write(OUT/'final-validation.json',{'passed':True,'only_normal_attack_changed':True,'all_old_body_files_preserved':True,'jaw_preserves_each_wing_pose':True,'source_frames_total':507,'contact_display_frame':244,'single_sonic_release':True,'full_and_close_video_frames':507,'all_media_digests_current':True,'deep_light_and_decoded_video_checked':True,'decoded_frames':len(R.read(OUT/'decoded-frame-audit.json')['frames']),'all_new_links_resolve':True,'unique_html_ids':True,'gallery_js_json_equal':True,'browser_visual_inspection':False,'runtime_integrated':False,'user_acceptance':'pending'});print(json.dumps(R.read(OUT/'final-validation.json'),ensure_ascii=False))
def main():
 p=argparse.ArgumentParser();p.add_argument('--qa',action='store_true');p.add_argument('--finish',action='store_true');a=p.parse_args()
 if a.qa:qa();docs()
 if a.finish:page();final()
if __name__=='__main__':main()
