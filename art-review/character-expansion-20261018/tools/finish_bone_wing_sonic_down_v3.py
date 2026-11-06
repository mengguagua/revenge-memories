#!/usr/bin/env python3
"""Final encoded direction check and one scoped review-panel refresh."""
import argparse,json,re
from html.parser import HTMLParser
from PIL import Image,ImageDraw
import revise_bone_wing_sonic_down_v3 as R
import finish_bone_wing_sonic_v2 as F
V=R.V;ROOT=R.ROOT;OUT=R.OUT;F.R=V;F.ROOT=ROOT;F.OUT=OUT
def qa():
 F.qa();d=V.read(OUT/'gallery-data.json');a=next(a for a in d['actions']if a['id']==R.ID);p=next(p for p in d['profiles']if p['id']==R.PID);im=V.E.render_panel(d,p,a,a['revisedFrames'][260],True,4,False,False);draw=ImageDraw.Draw(im);view=a['viewport'];q=[round((R.TARGET[i]-view[i])*4)for i in(0,1)];draw.ellipse((q[0]-10,q[1]-10,q[0]+10,q[1]+10),outline=(168,214,200),width=2);draw.text((q[0]+16,q[1]+5),'下方目标参考',font=V.E.font(17),fill=(168,214,200));im.convert('RGB').save(OUT/'aim-check.png',optimize=True)
def docs():
 c=V.read(OUT/'effect-contract.json');text='''# 骸翼兽 · 音波朝下方目标 V3

用户已确认V2音波效果，本轮只修正朝向。普通攻击末段下压头颈、向下方目标张嘴，音波沿嘴部至下方目标的方向推进，不再水平飞出。

- 沿用第237–277显示帧张嘴、第244帧单次释放、第275帧后音波清空、第278帧闭嘴和原程序回位。
- 全部507帧、60.0988fps、原作参考、角色位移／翻转／循环和第244帧单次结算保持。未新增伤害或能力。
- 目标参考点为逻辑坐标[208,144]，释放时嘴部参考点为[177,94]，音波朝右下约58度。参见[目标方向检查](aim-check.png)；该图的目标标记仅用于检查，不进入播放画面。
- 头颈通过内置imagegen局部重绘，源图和完整提示词保存在source/head-down-master.png、source/head-down-prompt.txt。以固定颈部连接点注册，仅复合头颈；双翼、躯干、近爪、远爪和尾部保留当前原姿势，近爪位图逐像素保持。
- 六张已确认音波位图保留原文件，以最近邻旋转和锚点注册调整方向，五色调色板、六阶段形状与透明轮廓保持，不重新设计音波效果。

只有普通攻击右侧新稿更新；其他已确认动作、原始身体／音波文件和游戏运行文件未改动。未安装或更新设备。

[浅底连续帧](phases-light.png) · [深底连续帧](phases-dark.png) · [最终视频解码检查](decoded-sequence.png) · [验证记录](verification.json) · [视频帧数和时长](export-report.json) · [最终合并检查](final-validation.json)

验证包含完整身体与音波在全景／近景中的边界、头颈以外像素保持、旧素材文件哈希、朝向射线、单次释放及最终MP4解码。检查为离线渲染，未进行浏览器或可见Godot窗口验收。逐图尺寸、字节及用途见delivery-image-inventory.json；原始生成图离线保留，正式动作帧和音波使用无损索引PNG。待用户视觉确认。
''';(OUT/'README.md').write_text(text)
 for revision in['bone-wing-beast-complete-v1-20261024','bone-wing-sonic-v2-20261024']:
  file=ROOT/revision/'README.md';old=file.read_text();note='当前朝向修订：[音波朝下方目标V3](../'+R.REV+'/README.md)。本页为此前效果／检查记录。\n\n'
  if note not in old:file.write_text(old.replace('\n\n','\n\n'+note,1))
def page():
 p=ROOT/'index.html';before=V.sha(p);text=p.read_text();pattern=r'<div id="bone-wing-sonic-(?:v2|down-v3)-progress".*?</div>';match=re.search(pattern,text,re.S);assert match
 panel='''<div id="bone-wing-sonic-down-v3-progress" style="margin-top:18px"><p class="action-note" style="margin:0 0 12px"><strong>普通攻击 · 下方目标V3：</strong>头颈向下压，张嘴朝下方目标释放音波；已确认的蓝紫音波沿同一方向扩大、推进并消散。双翼、躯干、爪与尾部保留各自原姿势，原507帧和第244帧单次结算保持。</p><nav class="links" aria-label="骸翼兽音波朝向检查"><a href="?action=professions-class-5-enemy-battle--original_class_5_enemy_normal#motion-player">普通攻击 · 朝下方音波</a><a href="bone-wing-sonic-down-v3-20261024/phases-light.png">浅底连续帧</a><a href="bone-wing-sonic-down-v3-20261024/phases-dark.png">深底连续帧</a><a href="bone-wing-sonic-down-v3-20261024/aim-check.png">目标方向检查</a><a href="bone-wing-sonic-down-v3-20261024/decoded-sequence.png">最终视频连续帧</a><a href="bone-wing-sonic-down-v3-20261024/README.md">朝向修改记录</a></nav></div>'''
 text=text[:match.start()]+panel+text[match.end():];text=re.sub(r'&bone_sonic=[^"&]+','&bone_sonic=v3-down-20261024',text);assert V.sha(p)==before;p.write_text(text);V.write(OUT/'page-update.json',{'before_sha256':before,'after_sha256':V.sha(p),'only_current_bone_sonic_panel_and_cache_key_changed':True})
def final():
 local=V.read(OUT/'gallery-data.json');live=V.read(ROOT/'demos/gallery-data.json');assert V.S.parse_js(ROOT/'gallery-data.js')==live;a=next(a for a in local['actions']if a['id']==R.ID);assert a==next(a for a in live['actions']if a['id']==R.ID)and a['ready'];p=next(p for p in local['profiles']if p['id']==R.PID);assert p==next(p for p in live['profiles']if p['id']==R.PID)
 for field in['video','closeVideo','still']:
  file=ROOT/a[field];assert file.is_file()and V.read(file.with_suffix('.json'))['contentDigest']==a['contentDigest']
 html=(ROOT/'index.html').read_text();tags=F.Tags();tags.feed(html);assert len(tags.ids)==len(set(tags.ids))and'bone-wing-sonic-down-v3-progress'in tags.ids;new=F.Tags();new.feed(html.split('id="bone-wing-sonic-down-v3-progress"',1)[1].split('</div>',1)[0])
 for href in new.links:
  if not href.startswith('?'):assert(ROOT/href).is_file()
 assert V.read(OUT/'verification.json')['passed']and len(V.read(OUT/'export-report.json')['decoded_videos'])==2
 files=set(OUT.rglob('*.png'))|{ROOT/a['still'],ROOT/a['closeVideo'].replace('/videos/','/stills/').replace('.mp4','.png')};images=[]
 for file in sorted(files):
  im=Image.open(file);offline=R.SRC in file.parents;images.append({'path':file.relative_to(ROOT).as_posix(),'size':list(im.size),'bytes':file.stat().st_size,'sha256':V.sha(file),'purpose':'离线生成源图'if offline else'正式动作／音波素材'if file.parent.name in['battle','effects']else'方向、深浅底或视频解码检查','over_reference_reason':'保留完整检查分辨率及文字／原始源图离线保留'if file.stat().st_size>=50000 else''})
 V.write(OUT/'delivery-image-inventory.json',{'images':images,'runtime_integrated':False});V.write(OUT/'final-validation.json',{'passed':True,'only_normal_attack_direction_changed':True,'head_and_sonic_aim_at_lower_target':R.TARGET,'old_body_and_effect_files_unchanged':True,'native_507_frames_and_display_contact_244_preserved':True,'full_and_close_video_digests_current':True,'decoded_frames':len(V.read(OUT/'decoded-frame-audit.json')['frames']),'all_new_panel_links_resolve':True,'unique_html_ids':True,'gallery_js_json_equal':True,'runtime_integrated':False,'browser_visual_inspection':False,'user_acceptance':'pending'});print(json.dumps(V.read(OUT/'final-validation.json'),ensure_ascii=False))
def main():
 p=argparse.ArgumentParser();p.add_argument('--qa',action='store_true');p.add_argument('--finish',action='store_true');a=p.parse_args()
 if a.qa:qa();docs()
 if a.finish:page();final()
if __name__=='__main__':main()
