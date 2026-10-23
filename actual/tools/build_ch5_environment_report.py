#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Final-chapter environment report backed by the selected completed input runs."""
from pathlib import Path
from PIL import Image
import json,html,hashlib,re,shutil
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter5-environment-20261023'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();e=html.escape
codes=read(O/'codes.json');selection=read(O/'selected-play.json');material=read(O/'material-review.json');inv=read(O/'invariants-audit.json');pack=read(O/'package-checks.json');rules=read(O/'rules-probe.json');wp=read(O/'world/phase-fixture.json');hp=read(O/'hubs/phase-fixture.json');hi=read(O/'hubs/interaction-review.json');tn=read(O/'terrain-name-checks.json');flow=read(O/'flow-continuation.json');hd=read(O/'hubs/design.json')
captures={k:read(O/k/'captures.json')for k in ['screenshots','world/screenshots','hubs/after','flow']}
for d in [material,inv,pack,rules,wp,hp,hi,tn,flow,*captures.values()]:assert d['passed']
assert inv['map_hashes']=={c:d['sha256']for c,d in pack['maps'].items()}
plays={};total=0
for c in codes:
 plays[c]=[]
 for label in selection[c]:
  p=O/f'play/{label}/{label}-play.json';d=read(p);b=next(b for b in d['battles']if b['code']==c)
  assert d['passed']and len(d['battles'])==7 and b['outcome']=='victory'and not b['failures']
  assert b['entry_map_sha256']==b['map_sha256']==inv['map_hashes'][c]==sha(R/f'data/stages/{c}.json')
  assert not d['stat_edits']and not d['forced_victories']and not d['source_saves_modified']
  total+=b['key_inputs'];plays[c].append({'label':label,'turns':b['final_turn'],'inputs':b['key_inputs'],'source':str(p.relative_to(O)),'ending_done':b.get('ending_done',False)})
shutil.copy2(R/'assets/chapter4-environment-20261023/world/overview-verified.png',O/'world/before-arrival.png')
shutil.copy2(R/'assets/world_tiles/formal-world-overview.png',O/'world/before-clear.png')
for phase in ['arrival','network','clear']:shutil.copy2(R/f'assets/chapter5-environment-20261023/world/overview-{phase}.png',O/f'world/after-{phase}.png')
css=re.search(r'<style>(.*?)</style>',(R/'reports/chapter4-environment-20261023/index.html').read_text(),re.S).group(1)
def fig(path,title):return f'<figure><a href="{path}" target="_blank"><img src="{path}" loading="lazy" alt="{e(title)}"></a><figcaption>{e(title)}</figcaption></figure>'
def start(title,lead):return ['<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+e(title)+'</title><style>'+css+'</style></head><body><main><div class="eyebrow">REVENGE MEMORIES / CHAPTER FIVE / 2026.10.23</div><h1>'+e(title)+'</h1><span class="badge">0.10.15-environment</span><p>'+e(lead)+'</p>']
body=start('第五章 · 环境与室内外材质再次复查','重新核对七张战斗地图、六处据点与世界环境。上轮确认的病房、日宫、书库、前庭和神座结构保留，集中修正地下与露天地面的区别、战后据点的室内空间，以及终战后的世界状态。')
body+=['<p>战斗图中只调整M52登天桥和F51祭所底层的地面材质；其余五图原文件、原生场景保持。全部行动格、桥梁通路、部署、敌人、任务对象、剧情、数值和现有动画沿用。六据点通过显示覆盖调整，原碰撞、对象和出入口保持。</p><nav><a href="#world">世界与自然日照</a>']+[f'<a href="#{c}">{c}</a>'for c in codes]+['<a href="#hubs">六处据点</a><a href="#verify">两轮与连续通关</a><a href="../../../art-review/battle-maps-20261021/index.html">全部40图</a><a href="../../dist/RevengeMemories-Chapter5-Environment-20261023.app">当前独立桌面包</a></nav>']
body+=['<section class="panel" id="world"><h2>神宫地理与讨神前后的照明</h2><p>世界图继续沿用第四章已确认的高地雪地、日照带、盐原和湿地，补神宫入口、桥头与建筑前场的石地。世界节点是地理位置与外部建筑标志；日宫和书库的室内材质由战场及据点呈现，不把世界图当室内平面图。原世界节点、道路、解锁与行军规则逐字节保持。</p><div class="pair">',fig('world/before-arrival.png','修改前 · 第五章到达时沿用第四章世界图'),fig('world/after-arrival.png','当前 · 保留寒区与局部保护，补神宫石质前场'),'</div><h3>地方循环扩大后，日宫与书库所在区域逐步变亮</h3><p>进入第五章时，祭所及邻近地区保留第四章验证后的亮光；完成F51交接后，修复网络扩展至日宫与书库前场。远处盐原与旧群岛仍处冷暗环境，直到乌库布·卡基败亡。</p><div class="pair">',fig('world/after-network.png','地方循环扩大后的原生世界预览'),fig('world/after-clear.png','终战后自然日照 · 原生显示规则预览'),'</div><p>上方终战后总览是渲染器对结局状态的显示预览，不表示结局菜单新增了自由行军入口。实际游戏仍进入原有逐页结局。雪地、盐土、湿地、海岸和断裂地理保持，不因照明恢复立即变成旧版草地。</p><details><summary>查看旧终战底图回退的问题</summary><div class="pair">',fig('world/before-clear.png','旧规则 · 终战后退回最早底图，北境雪地等消失'),fig('world/after-clear.png','当前规则 · 日照恢复，已确认地形保持'),'</div></details><div class="shots">']
for name,title in [('capital-arrival','第五章真实入口 · 北境雪地保留'),('bridge-gate','登天桥入口 · 石制前场'),('repair-network','F51后 · 祭所修复网络'),('palace-lower','日宫下层 · 所在地区亮光'),('archive','旧书库 · 外部地理节点'),('throne-before','终战前 · 神座入口')]:body.append(fig('world/screenshots/'+name+'.png',title))
body+=['</div><details><summary>全部24张世界实机视口</summary><div class="shots">']
for shot in captures['world/screenshots']['shots']:body.append(fig('world/screenshots/'+Path(shot['path']).name,shot['name']))
body+=['</div></details><p><a href="world/phase-fixture.json">268项故事阶段及地理检查</a> · <a href="world/visual-review.json">画面目检</a></p></section>']
for m in material['maps']:
 c=m['code'];d=read(R/f'data/stages/{c}.json');body+=[f'<section class="panel" id="{c}"><div class="eyebrow">{c} / {d["map"]["width"]} × {d["map"]["height"]}</div><h2>{e(d["name_zh"])}</h2><p>{e(m["conclusion"])}</p><div class="pair">',fig(f'before/{c}.png','修改前 · 本轮开始时的运行版本'),fig(f'images/{c}.png','当前原生场景 · '+('材质修正'if m['changed']else'复查后保持原样')),'</div><div class="cards">']
 for i,p in enumerate(plays[c]):body.append(f'<article><h3>第{i+1}轮最终版本试玩</h3><div class="stat">第{p["turns"]}回合完成</div><p><a href="{p["source"]}">{p["inputs"]:,}次普通按键记录</a>，含结算与对应后续操作。</p></article>')
 body+=['</div><div class="shots">']
 for suffix,title in [('deployment','实际出阵'),('field','第6回合推进'),('victory','终战结算进入结局'if c=='J54'else'实际结算')]:body.append(fig(f'screenshots/{c}-{suffix}.png',c+' · '+title))
 body+=['</div></section>']
hubbody=start('第五章 · 六处据点完整前后对照','同一真实战后记录分别使用本轮开始时和当前渲染器捕获。室外照护院、桥头营地与前庭保持外部建筑；修复间、东门廊与记录室明确改为去顶室内。')
hubbody+=['<nav><a href="../index.html">返回第五章完整对照</a></nav>']
for room,note in hd['rooms'].items():hubbody +=[f'<section class="panel" id="{room}"><h2>{room}</h2><p>{e(note)}</p><div class="pair">',fig(f'before/{room}.png',room+' · 修改前'),fig(f'after/{room}.png',room+' · 当前原生视口'),'</div></section>']
hubbody+=[f'<p>记录室书架库位由四个既有48×48完整模块组成，保留原96×96阻挡占地与南侧记录交接位置；原透明像素按无损导入核对。三处室内边界墙在原行走范围之外，南口保持打开。六据点{len(hi["records"])}处可见交互、{hi["inputs"]}次普通按键及{hp["count"]}项显示范围检查通过。</p><p><a href="interaction-review.json">普通输入交互记录</a> · <a href="phase-fixture.json">显示范围与尺寸核对</a> · <a href="visual-review.json">逐图目检</a></p></main></body></html>'];(O/'hubs/index.html').write_text(''.join(hubbody))
body+=['<section class="panel" id="hubs"><h2>不再在记录室中摆一整栋书库</h2><p>H53修复间使用室内石板，H54东门廊使用神宫大理石；H56记录室使用木地与石廊，完整屋顶书库改为同占地书架库位。三处室内原花丛改同占地储料箱。H51照护院、H52桥头营地、H55前庭整备保留外部建筑与草园，前场改露天砌石。</p><div class="pair">']
for room in ['H53','H54','H56']:body.extend([fig(f'hubs/before/{room}.png',room+' · 修改前'),fig(f'hubs/after/{room}.png',room+' · 当前')])
body+=['</div><p><a href="hubs/index.html">查看全部六处据点前后对照</a></p></section>',f'<section class="panel" id="verify"><h2>两轮逐关试玩 + 一次完整连续通关</h2><p>七图各完成两轮最终版本普通输入通关，共14场、{total:,}次按键。两轮均在素材完成导入后从真实记录的隔离副本重新进入当前地图，未编辑战斗属性、随机结果、位置或强制胜利。</p><div class="overflow"><table><thead><tr><th>地图</th><th>第一轮</th><th>第二轮</th><th>连续流程</th></tr></thead><tbody>']
for c in codes:
 b=next(b for b in flow['battles']if b['code']==c);body.append(f'<tr><td>{c}</td><td>{plays[c][0]["turns"]}回合</td><td>{plays[c][1]["turns"]}回合</td><td>{b["final_turn"]}回合</td></tr>')
body+=['</tbody></table></div><p>'+e(flow['description'])+'</p>',f'<p>连续流程共{flow["inputs"]:,}次按键，实际读完{flow["ending"]["page_count"]}页结局。此记录与两轮逐关重开分开保存；逐关样本的结局页数可随实际名册和伤情不同。</p><div class="shots">',fig('flow/merged.png','连续流程 · 正常名单确认后两军合流'),fig('flow/ending-first.png','连续流程 · 日光仍在'),fig('flow/ending-complete.png','连续流程 · 完整结局最后一页'),'</div>',f'<p>{rules["check_count"]}项规则、连通与保存检查，{inv["check_count"]}项修改范围检查，{wp["count"]}项世界阶段检查，{hp["count"]}项据点显示检查和{len(tn["checks"])}项材质名称检查通过。水体提示按人工水渠、室内蓄水池和庭院水池区分，通行与数值不变。21张战斗、24张世界、6张据点、3张合流与结局实机视口在后台捕获，记录的文字安全区检查无错误。</p>',f'<p>独立应用完成{pack["checks"]:,}项地图与资源核对，包内40图与当前源文件SHA-256逐一相同。导入后可见像素、书架透明边缘和原尺寸已核对，动画及战斗规则代码保持。</p><details><summary>验证边界与素材说明</summary><p>逐关两轮不等于两次从新游戏通关；另有本轮第四章完成记录开始、无重试的完整连续流程。早期在资源导入完成前启动的检查未计入最终两轮，最终选用记录中没有脚本或缺失资源错误。结局后的世界总览为只读显示规则预览，未新增终战后自由行军。</p><p>本轮只复用原生像素瓦片、设备与完整书架模块，没有新增AI生成素材。图集保留原始瓦片分辨率和索引，采用无损资源；大幅总览优先保持清晰度。未安装手机包；HTML资源与脚本检查不等于浏览器布局引擎实测。</p></details><p><a href="invariants-audit.json">修改范围检查</a> · <a href="rules-probe.json">规则检查</a> · <a href="flow-continuation.json">完整连续通关</a> · <a href="terrain-name-checks.json">材质名称检查</a> · <a href="package-checks.json">当前独立包核对</a> · <a href="delivery-summary.json">交付清单</a> · <a href="../../../docs2/完整游戏流程.md">完整流程文档1.20</a></p></section><footer>软件0.10.3，材质0.10.15-environment。第一至第四章地图和已确认环境保持。本轮不新增旧图兼容副本。</footer></main></body></html>'];(O/'index.html').write_text(''.join(body))
images=[]
for folder in ['before','images','screenshots','world','world/screenshots','hubs/before','hubs/after','flow']:
 for p in sorted((O/folder).glob('*.png')):images.append({'path':str(p.relative_to(O)),'size':list(Image.open(p).size),'bytes':p.stat().st_size,'sha256':sha(p)})
summary={'passed':True,'date':'2026-10-23','revision':'0.10.15-environment','changed_maps':inv['changed_maps'],'map_hashes':inv['map_hashes'],'plays':plays,'per_map_inputs':total,'rules_checks':rules['check_count'],'invariant_checks':inv['check_count'],'world_fixture_checks':wp['count'],'hub_fixture_checks':hp['count'],'terrain_names':len(tn['checks']),'hub_interactions':len(hi['records']),'native_viewports':sum(len(d['shots'])for d in captures.values()),'package_passed':pack['passed'],'package_pck_sha256':pack['pck_sha256'],'app_path':pack['app_path'],'flow_continuation':flow,'images':images,'limitations':['Two final checkpoint replays per map, not two new-game runs.','Additional full continuous chapter5 completion from current chapter4 source, no retry.','Post-ending clear-sky overview is a read-only rendering preview; no new free-roam menu.','No phone installation or browser layout-engine verification.']};(O/'delivery-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print({k:summary[k]for k in ['passed','per_map_inputs','native_viewports','package_passed']})
