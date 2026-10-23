#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
from PIL import Image
import json,hashlib,html,re,shutil
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter4-environment-20261023'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();e=html.escape
codes=read(O/'codes.json');selection=read(O/'selected-play.json');inv=read(O/'invariants-audit.json');material=read(O/'material-review.json');pack=read(O/'package-checks.json');rules=read(O/'rules-probe.json');flow=read(O/'flow-continuation.json');wp=read(O/'world/phase-fixture.json');hp=read(O/'hubs/phase-fixture.json');hi=read(O/'hubs/interaction-review.json');hd=read(O/'hubs/design.json')
captures={k:read(O/k/'captures.json')for k in ['screenshots','world/screenshots','hubs/after','flow']}
for d in [inv,material,pack,rules,flow,wp,hp,hi,*captures.values()]:assert d['passed']
assert inv['map_hashes']=={c:d['sha256']for c,d in pack['maps'].items()}
plays={};total=0
for c in codes:
 plays[c]=[]
 for label in selection[c]:
  path=O/f'play/{label}/{label}-play.json';d=read(path);b=next(b for b in d['battles']if b['code']==c)
  assert b['outcome']=='victory'and not b['failures']and b['entry_map_sha256']==b['map_sha256']==inv['map_hashes'][c]==sha(R/f'data/stages/{c}.json')
  assert not d['stat_edits']and not d['forced_victories']and not d['source_saves_modified']
  total+=b['key_inputs'];plays[c].append({'label':label,'turns':b['final_turn'],'inputs':b['key_inputs'],'source':str(path.relative_to(O))})
shutil.copy2(R/'assets/world_tiles/formal-world-overview.png',O/'world/before-overview.png')
for phase in ['before','trial','verified']:shutil.copy2(R/f'assets/chapter4-environment-20261023/world/overview-{phase}.png',O/f'world/after-{phase}.png')
css=re.search(r'<style>(.*?)</style>',(R/'reports/chapter3-environment-20261023/index.html').read_text(),re.S).group(1)
def fig(path,title):return f'<figure><a href="{path}" target="_blank"><img src="{path}" loading="lazy" alt="{e(title)}"></a><figcaption>{e(title)}</figcaption></figure>'
def start(title,lead):return ['<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+e(title)+'</title><style>'+css+'</style></head><body><main><div class="eyebrow">REVENGE MEMORIES / CHAPTER FOUR / 2026.10.23</div><h1>'+e(title)+'</h1><span class="badge">0.10.14-environment</span><p>'+e(lead)+'</p>']
body=start('第四章 · 世界、战场与据点的环境统一','十张战斗地图、十处战后据点与共享营站逐一复查。雪峡、日塔与黑钟村保留寒区；铁骑关和王都仍处日返保护带。东线沙城、盐原、湿沼与沉没祭所各用对应地表，黑昼一直延续到局部修复得到验证。')
body+=['<p>九张地图作必要的环境修正，M42铁骑封锁线原图保持。已确认M41的桥路、部署和战术构图保持，仅统一冬季医舍与岩脚残雪。全部关卡的行动格、敌我位置、任务对象、胜败规则、成长与人物动画沿用。代码、源地图和独立应用同步。</p><nav><a href="#world">世界与剧情光照</a>']+[f'<a href="#{c}">{c}</a>'for c in codes]+['<a href="#hubs">十一处据点</a><a href="#verify">两轮试玩</a><a href="../../../art-review/battle-maps-20261021/index.html">全部40图</a><a href="../../dist/RevengeMemories-Chapter4-Environment-20261023.app">当前独立桌面包</a></nav>']
body+=['<section class="panel" id="world"><h2>失去庇护的寒区与仍获日照的交通带</h2><p>雪峡村、北境日塔和黑钟村的战斗图一直是雪地，但旧世界图在这些节点显示草地。现按寒冷高地和村落范围补连续雪地、冬季林岩与清扫道路；保留铁骑关、王都的草地日照带。观测台改盐原，亡潮沼泽与孤岛改湿地，祭所节点用风化石地。第一、二章的故事时间选景及第三章盐原修订继续保留，原世界节点、路线、解锁和移动规则逐字节保持。实际完成第四章后进入第五章，沿用已确认的高地雪地和局部保护，避免只因切换章节就回退旧底图。</p><div class="pair">',fig('world/before-overview.png','修改前 · 第四章原底图：寒区草地、东线明亮'),fig('world/after-before.png','当前 · 寒区积雪、沙城与盐原、东部持续黑昼'),'</div><h3>试验成功后只恢复当地，不把整个东部突然照亮</h3><p>夺取祭所之前维持黑昼。三个调节点的隔离试验成功后，祭所本身恢复亮光；两岸D42验证完成后，亮区扩展到邻近亡潮沼泽。远处沙城、盐原、孤岛及旧群岛仍保持原有冷暗环境。雪地不会因安全停塔立即融化；气候与照明分别表达。</p><div class="pair">',fig('world/after-trial.png','局部试验成功 · 祭所亮光'),fig('world/after-verified.png','两岸验证完成 · 祭所与邻近湿地亮光'),'</div><div class="shots">']
for name,title in [('snow-village','雪峡村 · 世界积雪'),('north-tower','日塔 · 高地雪原'),('sand-city','沙城 · 沙地与冷光'),('shrine-before','真实出阵前 · 祭所黑昼'),('shrine-trial','真实试验成功后 · 祭所亮光'),('marsh-verified','真实两岸验证后 · 邻近沼泽亮光')]:body.append(fig('world/screenshots/'+name+'.png',title))
body+=['</div><details><summary>查看全部42张世界实机视口（局部、全图、放大）</summary><div class="shots">']
for shot in captures['world/screenshots']['shots']:body.append(fig('world/screenshots/'+Path(shot['path']).name,shot['name']))
body+=['</div></details><p><a href="world/phase-fixture.json">250项故事阶段及材质检查</a> · <a href="world/visual-review.json">世界画面目检</a></p></section>']
for m in material['maps']:
 c=m['code'];d=read(R/f'data/stages/{c}.json')
 body+=[f'<section class="panel" id="{c}"><div class="eyebrow">{c} / {d["map"]["width"]} × {d["map"]["height"]}</div><h2>{e(d["name_zh"])}</h2><p>{e(m["conclusion"])}</p><div class="pair">',fig(f'before/{c}.png','修改前 · 本轮开始时的运行版本'),fig(f'images/{c}.png','当前原生场景 · '+('环境修正'if m['changed']else'复查后保持原样')),'</div><div class="cards">']
 for i,p in enumerate(plays[c]):body.append(f'<article><h3>第{i+1}轮普通输入试玩</h3><div class="stat">第{p["turns"]}回合完成</div><p><a href="{p["source"]}">{p["inputs"]:,}次按键记录</a>，含实际战后操作。</p></article>')
 body+=['</div><div class="shots">']
 for suffix,title in [('deployment','实际出阵'),('field','第6回合推进'),('victory','实际结算')]:body.append(fig(f'screenshots/{c}-{suffix}.png',c+' · '+title))
 body+=['</div></section>']
hubbody=start('第四章 · 十一处据点前后对照','十处战后据点加H10共享营站。同一真实据点记录分别用本轮开始时和当前渲染器捕获；地面通行范围、碰撞、剧情对象和出口坐标均保持。')
hubbody+=['<nav><a href="../index.html">返回第四章完整对照</a></nav>']
for room,note in hd['rooms'].items():hubbody +=[f'<section class="panel" id="{room}"><h2>{room}</h2><p>{e(note)}</p><div class="pair">',fig(f'before/{room}.png',room+' · 修改前'),fig(f'after/{room}.png',room+' · 当前原生视口'),'</div></section>']
hubbody+=['<p>H43/H46的石墙画在原通行域之外，南出口保持打开；控制台、工作台沿用原建筑占地。H47/H48/H50展示接应码头与临时交接台，并非整座岛屿全景。H10复用第三章确认后的沙岸、土路与陆地补给仓房。</p>',f'<p>{len(hi["records"])}处可见交互、{hi["inputs"]}次普通按键与{hp["count"]}项显示范围检查通过。</p><p><a href="interaction-review.json">普通输入交互记录</a> · <a href="phase-fixture.json">显示与通行域检查</a> · <a href="visual-review.json">逐图画面检查</a></p></main></body></html>'];(O/'hubs/index.html').write_text(''.join(hubbody))
body+=['<section class="panel" id="hubs"><h2>控制室、东楼、井台与接应码头分别表达</h2><p>日塔控制室和观测台东楼从雪地／盐地小屋改为去顶室内石地、连续墙体与真实设备；取消室内完整屋顶房屋。沙城井台从盐地改沙地，投送站和伤兵门使用军营仓房。船口、祭所与孤岛交接台补通向船只的木登船口。会合营站沿用第三章沙岸材质。</p><div class="pair">']
for room in ['H43','H46','H45','H47']:body.extend([fig(f'hubs/before/{room}.png',room+' · 修改前'),fig(f'hubs/after/{room}.png',room+' · 当前')])
body+=['</div><p><a href="hubs/index.html">查看十一处据点的完整前后对照</a></p></section>',f'<section class="panel" id="verify"><h2>两轮逐关试玩与第五章入口</h2><p>十图各完成两轮最终版本通关，共20场、{total:,}次普通按键，包含守井、保护记录、居民和病人撤离、调节点控制及战后据点操作。使用真实开发记录的隔离副本，经普通整备重新进入当前地图；没有编辑属性、随机结果、人物位置或强制胜利。</p><div class="overflow"><table><thead><tr><th>地图</th><th>第一轮</th><th>第二轮</th></tr></thead><tbody>']
for c in codes:body.append(f'<tr><td>{c}</td><td>{plays[c][0]["turns"]}回合</td><td>{plays[c][1]["turns"]}回合</td></tr>')
body+=['</tbody></table></div><p>'+e(flow['description'])+'</p><div class="pair">',fig('flow/chapter-end.png','真实第四章收束'),fig('flow/chapter5-start.png','真实第五章入口'),'</div>',f'<p>{rules["check_count"]}项规则、连通与保存检查，{inv["check_count"]}项修改范围检查，{wp["count"]}项世界阶段检查，{hp["count"]}项据点显示检查通过。30张战斗、42张世界、11张据点和2张章节衔接实机视口在后台捕获，记录的文字布局检查没有错误。独立应用完成{pack["checks"]:,}项地图与资源核对，包内40图与当前源文件SHA-256逐一相同。</p><details><summary>验证范围与素材说明</summary><p>两轮逐关重开不等于从新游戏通关两次；章节入口从本轮真实F44战后记录单独验证。世界试验前、试验后与两岸验证后截图使用实际记录和普通结算／行军操作，未为截图改剧情标记。故事阶段组合测试只在内存中运行，另标为检查夹具。</p><p>本轮复用既有原生像素瓦片、冬季建筑和室内设备，没有新增AI生成素材。图集保留原始瓦片尺寸与索引，图片无损优化；未为体积牺牲清晰度。没有安装手机包；HTML资源和脚本检查不等于浏览器布局引擎实测。</p></details><p><a href="invariants-audit.json">修改范围检查</a> · <a href="rules-probe.json">规则检查</a> · <a href="flow-continuation.json">章节衔接</a> · <a href="package-checks.json">当前独立包验证</a> · <a href="delivery-summary.json">交付清单</a> · <a href="../../../docs2/完整游戏流程.md">完整流程文档1.19</a></p></section><footer>软件0.10.3，材质0.10.14-environment。第一至第三章地图与已确认环境保留；第五章战斗图保持。本轮不新增旧图兼容副本。</footer></main></body></html>'];(O/'index.html').write_text(''.join(body))
images=[]
for folder in ['before','images','screenshots','world','world/screenshots','hubs/before','hubs/after','flow']:
 for p in sorted((O/folder).glob('*.png')):images.append({'path':str(p.relative_to(O)),'size':list(Image.open(p).size),'bytes':p.stat().st_size,'sha256':sha(p)})
summary={'passed':True,'date':'2026-10-23','revision':'0.10.14-environment','changed_maps':inv['changed_maps'],'map_hashes':inv['map_hashes'],'plays':plays,'per_map_inputs':total,'rules_checks':rules['check_count'],'invariant_checks':inv['check_count'],'world_fixture_checks':wp['count'],'hub_fixture_checks':hp['count'],'hub_interactions':len(hi['records']),'native_viewports':sum(len(d['shots'])for d in captures.values()),'package_passed':pack['passed'],'package_pck_sha256':pack['pck_sha256'],'app_path':pack['app_path'],'flow_continuation':flow,'images':images,'limitations':['20 final checkpoint replays, not two new-game runs.','Chapter transition separately verified from this round real F44 post-battle record.','No phone installation or browser layout-engine test.']};(O/'delivery-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print({k:summary[k]for k in ['passed','per_map_inputs','native_viewports','package_passed']})
