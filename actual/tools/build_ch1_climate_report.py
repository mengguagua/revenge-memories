#!/usr/bin/env python3
"""Deliver current first-chapter climate art and actual-input verification."""
from pathlib import Path
from PIL import Image
import json,html,hashlib,subprocess
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter1-climate-20261022'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();e=html.escape
codes=['M11','M12','M13','M14','M15','S11','S12']
notes={
'M11':('流民林路 · 保留雪原样板','原有积雪、雪松、道路与双桥已经符合本章冬季设定。地图文件保持原样，作为其他外景的气候参照。'),
'M12':('丘堡粮站 · 积雪林地与清扫粮道','粮站周边改为雪原与雪松；主路、运输院和交接场保留压实裸土。仓顶、诊所屋檐与岩石改用同尺寸冬景，原有两条进攻路线及护粮目标不变。'),
'M13':('南岗押送所 · 冬季河谷与石地囚室','河岸和林带有雪，河水继续流动，横桥仍为木板。道路保留裸土，两个去顶囚室及开门门槛仍用室内石地，不向室内铺雪。'),
'M14':('旧塔外营 · 残雪冬营','雪松和冬岩包围清扫出的营道与集结场，帐顶积雪。双哨卡、投降对象与道路几何均保持，泥路和雪地在视觉上分清。'),
'M15':('海峡旧塔堡 · 寒地海岸与石坪','海岸外缘覆雪，院内石坪与港栈清扫；屋顶、海崖草冠及岩石改为冬景。牢室保留室内石地，木栈保留木板，海水没有被改成可通行冰面。'),
'S11':('旧矿工队 · 地下矿厅保持','地图发生在矿道内部，洞外大世界是雪地不代表矿厅也应积雪。原有岩地、轨道、坑壁和矿口保持，文件逐字节不变。'),
'S12':('林村诊所 · 积雪聚落与渡河救援','诊所周围改成积雪村落，雪松、冬岩和积雪屋顶与世界图一致。渡河仍沿原木桥，河道保持流动；屋前和道路保留压实路面。')}
selection=read(O/'selected-play.json');rules=read(O/'rules-probe.json');inv=read(O/'invariants-audit.json');phase=read(O/'side/hubs/phase-fixture.json');pack=read(O/'package-checks.json')
capture=read(O/'screenshots/captures.json');worldcap=read(O/'world/screenshots/captures.json');hubcap=read(O/'side/hubs/after/captures.json')
continuous=read(O/'play/continuous-recruits/continuous-recruits-play.json')
for d in [rules,inv,phase,pack,capture,worldcap,hubcap,continuous]:assert d['passed']
current=inv['map_hashes'];plays={};total=0
for code,labels in selection.items():
 plays[code]=[]
 for label in labels:
  path=O/f'play/{label}/{label}-play.json';d=read(path);b=next(v for v in d['battles']if v['code']==code)
  assert d['passed'] and b['entry_map_sha256']==b['map_sha256']==current[code]
  assert not d['stat_edits']and not d['forced_victories']and not d['source_saves_modified']
  total+=b['key_inputs'];plays[code].append({'turns':b['final_turn'],'inputs':b['key_inputs'],'path':str(path.relative_to(O))})
assert len(continuous['battles'])==6
for b in continuous['battles']:assert b['outcome']=='victory'and b['entry_map_sha256']==b['map_sha256']==current[b['code']]
ending=read(O/'play/continuous-recruits/continuous-recruits-chapter-end.json');nextchapter=read(O/'play/continuous-recruits/continuous-recruits-chapter2-start.json')
assert ending['flags']['chapter1_complete']and nextchapter['chapter']==2
assets=[]
for folder in ['before','images','screenshots','world/screenshots']:
 for p in sorted((O/folder).glob('*.png')):
  im=Image.open(p).convert('RGBA');raw=im.tobytes();subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(p)],check=True)
  assert Image.open(p).convert('RGBA').tobytes()==raw
  assets.append({'path':str(p.relative_to(O)),'size':list(im.size),'bytes':p.stat().st_size,'sha256':sha(p)})
css='''*{box-sizing:border-box}body{margin:0;background:#111c24;color:#dfebee;font:16px/1.8 system-ui,-apple-system,sans-serif}main{max-width:1400px;margin:auto;padding:44px 28px}h1{font-size:38px;line-height:1.35}h2{font-size:27px;line-height:1.5;margin:8px 0 16px}h3{font-size:19px}p{color:#b7c9d1}a{color:#b6d9df;text-underline-offset:4px}nav{display:flex;flex-wrap:wrap;gap:10px;margin:24px 0}nav a,.badge{background:#293d48;border-radius:9px;padding:9px 15px;text-decoration:none}a:focus-visible{outline:none;box-shadow:0 0 0 5px #82b8cb66}.panel{background:#1b2c35;padding:28px;border-radius:18px;margin:30px 0}.pair,.cards,.shots{display:grid;grid-template-columns:1fr 1fr;gap:24px}.shots{grid-template-columns:repeat(3,1fr)}figure{margin:0}figure img{display:block;width:100%;height:auto;image-rendering:pixelated;border-radius:10px;background:#101c22}figcaption{color:#c2d4db;margin:10px 0 14px;font-size:14px}.cards article{padding:17px 22px;background:#223842;border-radius:12px}.small,footer{font-size:13px;color:#99b2bd}.eyebrow{letter-spacing:2px;font-size:12px;color:#93b8c5}.stat{font-size:24px;color:#e8f2e9}details{padding:16px 20px;background:#223842;border-radius:12px;margin:20px 0}summary{cursor:pointer}table{width:100%;border-collapse:collapse}td,th{padding:12px;text-align:left;border-bottom:1px solid #ffffff13}.overflow{overflow-x:auto}footer{padding:20px 0}@media(max-width:850px){main{padding:24px 14px}.panel{padding:18px}.pair,.cards,.shots{grid-template-columns:1fr}h1{font-size:28px}h2{font-size:24px}}'''
def figure(path,title):return f'<figure><a href="{path}" target="_blank"><img src="{path}" loading="lazy" alt="{e(title)}"></a><figcaption>{e(title)}</figcaption></figure>'
body=['<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>第一章 · 冬景一致性修订</title><style>'+css+'</style></head><body><main>',
'<div class="eyebrow">REVENGE MEMORIES / CHAPTER ONE / 2026.10.23</div><h1>第一章 · 世界、战场与据点的冬景统一</h1><span class="badge">地图材质 0.10.11-climate</span><p>本章“日返”发生在旧塔堡战后。授爵礼前，雪原、粮站、押送所、外营与海峡城应属于同一寒季；不能仅因为关卡换了背景，就突然成为盛夏草地。本轮修正五张外景战斗图，并同步世界图、全图总览和六个室外据点。</p><p>保留已确认的整体构图与战术选择。雪覆盖室外土层与植被，清扫泥路、木桥、港栈、石院、室内囚室各保留自己的材质。部署、敌人、交互、剧情、行动数值和人物动画保持。</p><nav><a href="#world">大地图与季节</a>']
for c in codes:body.append(f'<a href="#{c}">{c}</a>')
body+=['<a href="#hubs">据点对照</a><a href="#verify">试玩记录</a><a href="../../../art-review/battle-maps-20261021/index.html">全部40图</a><a href="../../dist/RevengeMemories-Chapter1-Climate-20261022.app">独立桌面应用</a></nav>',
'<section class="panel" id="world"><h2>同一条行军路线，保持同一季节</h2><p>西南寒区现在连续覆盖第一章节点。世界图的道路、坐标、解锁与移动数据没有改动；仪式前渲染冬季地面和植被，仪式完成后恢复原有大地图。全图缩放使用同一冬景数据。</p><div class="pair">',
figure('world/before-overview.png','修改前／仪式后沿用的原世界底图'),figure('world/after-overview.png','修改后／第一章仪式前冬季底图'),
'</div><p class="small">以上为同一套原生瓦片组成的完整地形底图；下面是实际存档经普通按键进入世界与全图界面的引擎视口。</p><div class="shots">']
for name,title in [('snow-grain-world','粮站节点：与雪地战场一致'),('snow-camp-world','旧塔外营：寒区沿道路延续'),('snow-coast-world','海峡城：冬季海岸'),('snow-coast-world-overview','仪式前世界全图'),('snow-coast-world-overview-zoom','全图放大后的同一雪线'),('spring-after-ceremony','日返完成：恢复原大地图')]:body.append(figure('world/screenshots/'+name+'.png',title))
body+=['</div><p><a href="world/screenshots/captures.json">世界图实机截图记录</a> · <a href="side/hubs/phase-fixture.json">仪式前后及第0、2—5章显示选择检查</a></p></section>']
for c in codes:
 d=read(R/f'data/stages/{c}.json');title,description=notes[c]
 body.append(f'<section class="panel" id="{c}"><div class="eyebrow">{c} / {d["map"]["width"]} × {d["map"]["height"]}</div><h2>{e(title)}</h2><p>{e(description)}</p><div class="pair">')
 body.extend([figure('before/'+c+'.png','修改前 · 上轮展示版本'),figure('images/'+c+'.png','当前原生场景 · '+('保持原样'if c in ['M11','S11']else '冬景修订')),'</div>'])
 if c in plays:
  body.append('<div class="cards">')
  for i,p in enumerate(plays[c]):body.append(f'<article><h3>第{i+1}轮普通输入试玩</h3><div class="stat">第{p["turns"]}回合完成</div><p>胜利并完成对应战后操作；<a href="{p["path"]}">{p["inputs"]:,}次按键记录</a>。</p></article>')
  body.append('</div><div class="shots">')
  for suffix,title in [('deployment','实际部署'),('field','实际推进'),('victory','实际结算')]:body.append(figure(f'screenshots/{c}-{suffix}.png',c+' · '+title))
  body.append('</div>')
 else:body.append('<p class="small">M11源数据与修改前逐字节相同。本轮连续流程由M11真实通关记录出发，没有重新修改或重新通关M11。</p>')
 body.append('</section>')
body+=['<section class="panel" id="hubs"><h2>战后据点也应接得上冬天</h2><p>H02、H03、H05、H06、H07、H09六个室外据点同步寒季。H06清扫石院保留，其他院道仍可辨认；屋顶和林带换冬景。室内教堂H04、地下矿厅H08不积雪，修改前后原生截图像素相同。</p><div class="pair">',figure('side/hubs/before/H02.png','粮站据点 · 修改前草地'),figure('side/hubs/after/H02.png','粮站据点 · 修改后积雪与清扫道路'),figure('side/hubs/before/H06.png','旧塔内院 · 修改前草地外缘'),figure('side/hubs/after/H06.png','旧塔内院 · 冬景外缘与保留石坪'),'</div><p><a href="side/hubs/index.html">查看全部八处据点的实机前后对照</a></p></section>']
body+=['<section class="panel" id="verify"><h2>两轮逐关复测与连续流程</h2>',f'<p>六张关卡各完成两轮普通输入试玩，共12场、{total:,}次按键。另从M11真实通关记录连续完成 M12 → M13 → S11 → S12 → M14 → M15，{continuous["total_inputs"]:,}次按键，正常安置伤者、确认日返并进入第二章。各次通关的地图SHA均与最终地图一致。</p>',
'<div class="overflow"><table><thead><tr><th>地图</th><th>第一轮</th><th>第二轮</th><th>连续路线</th></tr></thead><tbody>']
for c in selection:
 b=next(b for b in continuous['battles']if b['code']==c);body.append(f'<tr><td>{c}</td><td>{plays[c][0]["turns"]}回合</td><td>{plays[c][1]["turns"]}回合</td><td>{b["final_turn"]}回合</td></tr>')
body+=['</tbody></table></div>',f'<p>{rules["check_count"]}项关卡规则与连通检查、{inv["check_count"]}项修改范围与素材检查、{phase["count"]}项季节显示检查通过。18张战斗视口、15张世界图视口与8张据点视口完成后台捕获；战斗和世界图文字布局检查均无错误。独立应用从隔离目录加载，40张运行地图及新素材检查通过。</p>',
'<details><summary>验证边界与保留的失败尝试</summary><p>两轮逐关试玩使用真实开发记录的隔离副本，经正常整备和当前关卡入口重开；不等于两次新游戏全通。连续路线继承实际成长、装备与伤情，没有修改角色属性、随机结果或强制胜利。</p><p>首次连续尝试在刚完成M11、仅三名队员时先进入S11，第6回合矿工死亡导致失败。随后选择先推进粮站、押送所并招募，再回头完成支线的正常路线，六战连续通过；未为通过检查降低难度或修改规则。失败记录保留，不能把它解释成“支线任意时机都必能完成”。</p><p>全部原关卡逻辑、单位与交互位置、主流程、动画保持；仅世界与据点显示代码选择寒季美术。没有安装或试玩手机包；HTML资源检查不等于浏览器布局引擎验收。</p><p><a href="play/continuous-final/continuous-final-play.json">早期三人矿道失败记录</a> · <a href="play/continuous-recruits/continuous-recruits-play.json">最终连续流程记录</a></p></details><p><a href="invariants-audit.json">修改范围证据</a> · <a href="rules-probe.json">关卡规则检查</a> · <a href="package-checks.json">独立包检查</a> · <a href="delivery-summary.json">交付清单</a> · <a href="../../../docs2/完整游戏流程.md">流程文档1.16</a></p></section>',
'<footer>软件版本0.10.3；地图材质0.10.11-climate。本页地图与截图均来自当前运行数据。5张外景战斗地图修改，M11、S11和第二至第五章33图保持；未新增旧图兼容副本。生成源图离线保留，运行素材优先无损压缩。图集超过体积参考时保留原始瓦片像素，详情见素材记录。</footer></main></body></html>']
(O/'index.html').write_text(''.join(body))
summary={'passed':True,'date':'2026-10-23','revision':'0.10.11-climate','maps':{c:current[c]for c in codes},'changed_maps':inv['changed_maps'],'unchanged_maps':inv['unchanged_maps'],'plays':plays,'per_map_inputs':total,'continuous_inputs':continuous['total_inputs'],'continuous_source':'play/continuous-recruits/continuous-recruits-play.json','continuous_chapter2':True,'battle_screenshots':len(capture['shots']),'world_screenshots':len(worldcap['shots']),'hub_screenshots':len(hubcap['shots']),'rules_checks':rules['check_count'],'invariant_checks':inv['check_count'],'phase_checks':phase['count'],'package_passed':pack['passed'],'images':assets,'limitations':['Two isolated checkpoint rounds, not two new-game playthroughs.','First three-person S11 continuous attempt failed; recorded, no game difficulty changes.','No mobile installation; HTML asset checking is not browser layout-engine QA.']}
(O/'delivery-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items()if k not in ['maps','plays','images','unchanged_maps','limitations']},ensure_ascii=False))
