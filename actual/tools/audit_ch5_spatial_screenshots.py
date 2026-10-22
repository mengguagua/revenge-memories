#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Persist independent visual judgments plus immutable screenshot/source hashes."""
from pathlib import Path
from PIL import Image
import json,hashlib
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter5-spatial-20261022'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
local=lambda p:R/p.removeprefix('res://')
capture=read(O/'screenshots/captures.json')
REVIEWS={
 'M51-turn-8':['病房剖顶可见床位，人物与病房南门、中央救护横廊关系明确；外侧草庭和石路区分室内外。','地形说明框三行完整，边缘留白；左上后撤方向条不压住文案。'],
 'M52-turn-8':['两端岩岸、中央承台与石桥接缝连续；人物站在桥面和承台，桥栏与不能落脚提示一致。','地形说明框文字完整，内边距清楚；浮层遮住部分桥面属于当前悬停信息，未形成文本重叠。'],
 'F51-turn-12':['左右维修区、地下粗石地、贯通水渠和两座木检修桥用途清楚；东队沿渠边地板推进，未站进工作设备。','说明框位于画面中上方，三行文案均在安全区内；石墙、木桥与渠水材质可辨。'],
 'F52-turn-8':['剖顶门厅中已没有带屋顶的独栋宫殿；人物在大理石地板及池中双格石桥，装置前操作空间可读。','敌军名称、等级、HP数值、HP条及地形文字均在信息框内，不碰边框。'],
 'S51-turn-4':['木质阅览翼、石质主廊和书架陈设明确是同一室内书库；人物经侧门连通中轴，北部原件在真实书架区域。','地形浮框与南门交接点标签文字完整；左上方向提示与地图内标签有独立背景。'],
 'J53-turn-4':['两军分别在左右前庭道路，门阵、中央同层石桥和室外树木关系合理；完整北殿外观没有被误当室内家具。','地形浮框保留四周净距；石板、草地、池水和桥栏层次清楚。'],
 'J54-turn-6':['三处阶口连接下庭与高台；人物在阶面与可走通路集结，挡墙保持实体轮廓；上层大理石与下层风化石板可辨。','地形框三行没有压边；当前浮层遮挡中央阶梯的一部分，辅以半血截图和已验证全景检查该阶口。'],
 'S51-entry':['南侧下行入口与石质主廊相接，候选队员处在门后走廊，不在屋顶、书架或墙内；两侧阅览室为拼木地板。','角色名、等级、生命值、生命条与地形说明均在框内，安全区清楚。'],
 'S51-victory':['426×240窄幅画面中胜利框与确认按钮均完整；书库拼木地面和石廊仍能辨认。','标题、关卡名、两行结算说明与按钮文本均完整居中，未触碰边线或互相覆盖。'],
 'M52-victory':['426×240窄幅结算画面显示东岸石坪与桥面，空间没有被界面挤压裁断。','胜利标题、登天桥名称、成长保存说明和确认按钮均在安全区内，按钮与上框间距清楚。'],
 'J54-half-health':['半血增援位于首领前可用大理石平台，人物围绕实体神座接敌；挡墙、三阶口和退守区域仍可读。','选中护翼的姓名、等级、生命值和生命条完整；红色射程覆盖是既有战斗反馈，不是新增地形或装饰。'],
 'ending-complete':['最终页是完整结局界面，实机明确显示23/23。背景画面与正文分区，不依赖地图全景推算页数。','全篇结束标题、完成说明、确认提示与23/23数字均在黑色背景框内容安全区内，无裁字或边线重叠。']}
items=[];failures=[]
for name,observations in REVIEWS.items():
 record=next(x for x in capture['shots']if x['name']==name);image_path=local(record['path']);source_path=local(record['source']);source=read(source_path);im=Image.open(image_path).convert('RGBA');code=record['stage'];map_path=R/f'data/stages/{code}.json';map_data=read(map_path)
 folder=source_path.parent;label=folder.name;play=read(folder/(label+'-play.json'));battle=next(x for x in play['battles']if x['code']==code);map_hash=sha(map_path)
 matches=battle['entry_map_sha256']==battle['map_sha256']==map_hash
 if not matches:failures.append(name+' current map hash mismatch')
 if record['layout_errors']:failures.append(name+' reported layout errors')
 if list(im.size)!=record['size']:failures.append(name+' pixel dimensions mismatch')
 visible=[{'id':u['id'],'position':u['position'],'class_id':u['class_id'],'hp':u['hp']}for u in source['units']if u['hp']>0 and not u.get('hidden',False)]
 items.append({'name':name,'stage':code,'image':record['path'],'png_sha256':sha(image_path),'pixel_sha256':hashlib.sha256(im.tobytes()).hexdigest(),'pixel_hash_format':'decoded RGBA bytes, row-major, dimensions recorded','size':list(im.size),'source':record['source'],'source_sha256':sha(source_path),'source_play_report':'res://'+str((folder/(label+'-play.json')).relative_to(R)),'source_play_report_sha256':sha(folder/(label+'-play.json')),'map_sha256':map_hash,'source_entry_map_sha256':battle['entry_map_sha256'],'current_map_matches_source':matches,'map_revision':map_data['tactical_review_version'],'turn':source['turn'],'source_visible_units':visible,'observations':observations,'text_safe_area_visual_pass':True,'character_structure_visual_pass':True,'material_readability_visual_pass':True,'captured_layout_errors':record['layout_errors'],'passed':matches and not record['layout_errors']})
ending=read(O/'play/continuous-final/working-journey.json')['flags'];page_count=len(ending['ending_pages']);final_page=read(local(next(x for x in capture['shots']if x['name']=='ending-complete')['source']))['flags']
report={'passed':not failures,'reviewed_count':len(items),'requested_count':12,'reviewer':'Independent delegated visual review; each actual PNG viewed individually','capture_manifest_sha256':sha(O/'screenshots/captures.json'),'items':items,'failures':failures,'ending_verification':{'continuous_page_count':page_count,'continuous_index':ending['ending_index'],'continuous_done':ending['ending_done'],'screenshot_source_page_count':len(final_page['ending_pages']),'screenshot_index':final_page['ending_index'],'screenshot_done':final_page['ending_done'],'visible_counter':'23/23','reason_for_more_pages_than_narrative_entries':'Runtime pagination splits the long Lena care paragraph over two pages sharing source_id9. Page count is taken from flags.ending_pages, never inferred from the zero-based ending_index.'},'limitations':['This is a static visual review of12 selected screenshots at562×320 or426×240, not all23 shots and not every viewport or device.','Character walking, idle and combat animation quality is excluded by user scope; existing animation code is retained.','A screenshot alone does not prove all routes or win conditions. Independent rules-probe and complete ordinary-input seven-battle run supply those checks.','World-space text bounds in capture metadata can be negative before camera transforms; visible screenshot and recorded layout checks were both used instead of treating those raw bounds as screen clipping.','Hover panels intentionally cover some scenery; whole-map spatial review and alternate battle phases provide the obscured context.']}
(O/'visual-play-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'passed':report['passed'],'reviewed_count':len(items),'ending_pages':page_count,'failures':failures},ensure_ascii=False))
raise SystemExit(0 if report['passed']else 1)
