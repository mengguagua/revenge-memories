#!/usr/bin/env python3
"""Build the chapter-three review only from frozen data and completed checks."""
from pathlib import Path
from PIL import Image
import hashlib, html, json, re, shutil

R = Path(__file__).resolve().parents[1]
O = R / 'reports/chapter3-environment-20261023'
read = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
e = html.escape
codes = ['M31', 'M32', 'M33', 'F31', 'F32', 'F33', 'S31', 'S32']
rooms = ['H30', 'H31', 'H32', 'H33', 'H34', 'H35', 'H36', 'H37', 'H10']
inv = read(O/'invariants-audit.json')
pack = read(O/'package-checks.json')
rules = read(O/'rules-probe.json')
material = read(O/'material-review.json')
selection = read(O/'selected-play.json')
flow = read(O/'flow-continuation.json')
worldphase = read(O/'world/phase-fixture.json')
hubphase = read(O/'hubs/phase-fixture.json')
hubinputs = read(O/'hubs/interaction-review.json')
terrain = read(O/'terrain-name-checks.json')
capture_paths = ['screenshots/captures.json', 'world/screenshots/captures.json',
                 'hubs/after/captures.json', 'details/captures.json', 'flow/captures.json']
captures = {p: read(O/p) for p in capture_paths}
for check in [inv, pack, rules, material, flow, worldphase, hubphase, hubinputs, terrain, *captures.values()]:
    assert check['passed']
current = inv['map_hashes']
assert all(pack['maps'][c]['sha256'] == h for c, h in current.items())
for c, h in current.items():
    assert sha(R/f'data/stages/{c}.json') == h
plays, total = {}, 0
for code in codes:
    plays[code] = []
    for label in selection[code]:
        path = O/f'play/{label}/{label}-play.json'
        record = read(path)
        b = next(b for b in record['battles'] if b['code'] == code)
        assert b['outcome'] == 'victory' and not b['failures']
        assert b['entry_map_sha256'] == b['map_sha256'] == current[code]
        assert not record['stat_edits'] and not record['forced_victories'] and not record['source_saves_modified']
        total += b['key_inputs']
        plays[code].append(dict(label=label, turns=b['final_turn'], inputs=b['key_inputs'], source=str(path.relative_to(O))))
shutil.copy2(R/'assets/world_tiles/formal-world-overview.png', O/'world/before-overview.png')
shutil.copy2(R/'assets/chapter3-environment-20261023/world/overview.png', O/'world/after-overview.png')

css = re.search(r'<style>(.*?)</style>', (R/'reports/chapter1-climate-20261022/index.html').read_text(), re.S).group(1)
css += '\nfigure img{object-fit:contain;image-rendering:pixelated} .shots{align-items:start} details{margin:24px 0} nav a:focus-visible{outline:none;box-shadow:0 0 18px #a8bdc488} .overflow{overflow:auto} a{overflow-wrap:anywhere}'
def figure(path, title):
    return f'<figure><a href="{path}" target="_blank"><img src="{path}" loading="lazy" alt="{e(title)}"></a><figcaption>{e(title)}</figcaption></figure>'
def start(title, subtitle):
    return ['<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+e(title)+'</title><style>'+css+'</style></head><body><main><div class="eyebrow">REVENGE MEMORIES / CHAPTER THREE / 2026.10.23</div><h1>'+e(title)+'</h1><span class="badge">0.10.13-environment</span><p>'+e(subtitle)+'</p>']

body = start('第三章 · 世界、战场与据点的环境统一', '逐一核对八张战斗地图、九处据点与两队行军区域：西队回到日返后的城镇、军需路与山村，东队仍在黑昼中的盐路和提炼院。室内石板、露天砌石、盐土、草地、船体甲板和木栈道按空间用途区分。')
body += ['<p>六张地图作环境修正；M31街区与M32军需大道经复查保持原图。战术格、部署、敌人、任务对象、道路通行与现有动画保持。变更已同步到代码、地图数据和独立桌面包。</p><nav><a href="#world">世界与故事时间</a>']
body += [f'<a href="#{c}">{c}</a>' for c in codes]
body += ['<a href="#hubs">九处据点</a><a href="#verify">两轮试玩</a><a href="../../../art-review/battle-maps-20261021/index.html">全部40图</a><a href="../../dist/RevengeMemories-Chapter3-Environment-20261023.app">当前独立应用</a></nav>']
body += ['<section class="panel" id="world"><h2>西大陆日返后转暖，东部黑昼继续</h2><p>第三章回到当前时间，西大陆城镇与军需路使用草地、土路和自然光；东部盐原继续庇护流失后的冷暗光。盐原营地在大地图的原沙地格修正为小片盐地，与战斗和安置处衔接；原节点、道路、解锁与移动数据不变。</p><p>季节仍按故事时间选择：第一章仪式前是冬景；第二章回到半年前，前段也保留冬景；第二章押送舰战后确认继续航行时，西大陆日返转暖与东群岛黑昼同时发生；第三章延续这个结果。下方“修改前”是第三章原本使用的日返后底图，不是第一章冬景回退。</p><div class="pair">', figure('world/before-overview.png', '修改前 · 第三章原底图／东部明亮、盐原营地为沙地'), figure('world/after-overview.png', '当前 · 西部日返自然光、东部黑昼与盐原营地盐地'), '</div><div class="shots">']
for name, title in [('west-city', '西队 · 海峡城自然光'), ('meeting-camp', '两队会合 · 沙岸营站'), ('salt-road', '东队 · 盐路冷暗光'), ('refinery', '东队 · 提炼院'), ('salt-camp', '盐原营地 · 盐地与当地光照'), ('salt-camp-overview-zoom', '全图放大 · 光照与局部行军一致')]:
    body.append(figure(f'world/screenshots/{name}.png', title))
body += ['</div><details><summary>八个行军节点的24张原生视口</summary><div class="shots">']
for shot in captures['world/screenshots/captures.json']['shots']:
    body.append(figure('world/screenshots/'+Path(shot['path']).name, shot.get('name', Path(shot['path']).stem)))
body += ['</div></details><p><a href="world/visual-review.json">世界图视觉检查</a> · <a href="world/phase-fixture.json">220项故事阶段显示检查</a></p></section>']

names = {'M31':'海峡城旧街 · 日返后的避难街区', 'M32':'军需大道 · 自然光与车场土路', 'M33':'沿海石堡 · 露天砌石庭院', 'F31':'码头脱围 · 岸院、木栈与低矮船舱', 'F32':'盐路解围 · 盐土、干路与黑昼', 'F33':'提炼院后庭 · 工房剖面与室内石地', 'S31':'山村地牢 · 无雪村舍与室内牢室', 'S32':'盐原营地 · 露天盐地与拘押营房'}
for m in material['maps']:
    code = m['code']; d = read(R/f'data/stages/{code}.json')
    body += [f'<section class="panel" id="{code}"><div class="eyebrow">{code} / {d["map"]["width"]} × {d["map"]["height"]}</div><h2>{e(names[code])}</h2><p>{e(m["conclusion"])}</p><div class="pair">', figure(f'before/{code}.png', '修改前 · 本轮开始时的运行版本'), figure(f'images/{code}.png', '当前Godot原生场景 · '+('环境修正' if m['changed'] else '复查后保持原样')), '</div>']
    if code == 'F33':
        body += ['<p>原先墙内摆放的整栋带屋顶营房会让玩家误读为空间套房。现改为同占地的工作台、储架和提炼器具；房间地面改室内磨损石板。工房门真实开启后，门槛继续使用相同室内石材。工作台沿用48×32尺寸，门、人员与通路位置保持。</p><div class="pair">', figure('details/F33-workshop-closed.png', '当前工房 · 工作台与室内石地'), figure('details/F33-workshop-open.png', '真实开门后 · 连续的室内石门槛'), '</div>']
    body += ['<div class="cards">']
    for i, p in enumerate(plays[code]):
        body.append(f'<article><h3>第{i+1}轮普通输入试玩</h3><div class="stat">第{p["turns"]}回合完成</div><p>胜利并完成对应战后操作；<a href="{p["source"]}">{p["inputs"]:,}次按键记录</a>。</p></article>')
    body += ['</div><div class="shots">']
    for suffix, title in [('deployment', '实际部署'), ('field', '实际推进 · 第6回合'), ('victory', '实际结算')]:
        body.append(figure(f'screenshots/{code}-{suffix}.png', code+' · '+title))
    body += ['</div></section>']

hubdesign = read(O/'hubs/design.json')
hubpage = start('第三章 · 九处据点完整前后对照', '同一真实据点记录分别用修改前和当前渲染器捕获。行走地面范围、碰撞、所有剧情对象与出口位置保持；只调整地面材质、同尺寸建筑外观和环境光。')
hubpage += ['<nav><a href="../index.html">返回第三章完整对照</a><a href="../../../dist/RevengeMemories-Chapter3-Environment-20261023.app">当前独立应用</a></nav>']
for room in rooms:
    hubpage += [f'<section class="panel" id="{room}"><h2>{room}</h2><p>{e(hubdesign["rooms"][room])}</p><div class="pair">', figure(f'before/{room}.png', room+' · 修改前'), figure(f'after/{room}.png', room+' · 当前原生视口'), '</div></section>']
hubpage += ['<p>九处据点合计19处可见剧情交互、200次普通按键通过；单独源记录隔离，未修改人物坐标或标记。1194项显示阶段和地面范围检查通过。H10只在第三章采用新沙岸材质，其他章节的共享场景不受覆盖。</p><p><a href="interaction-review.json">普通输入交互记录</a> · <a href="phase-fixture.json">据点显示范围检查</a> · <a href="visual-review.json">逐图视觉检查</a></p></main></body></html>']
(O/'hubs/index.html').write_text(''.join(hubpage))
body += ['<section class="panel" id="hubs"><h2>九处据点 · 与各自战场和地理环境衔接</h2><p>庆典与旧街用露天石庭，军需转运站用土道与仓门石台，沿海工房用岸侧仓库与接驳船，盐路和提炼院用盐地及冷暗光，山村安置处明确处在地牢之外，盐原营地使用营房外观。会合营站按世界图沙岸定位，不再出现停在陆地上的船舱。</p><div class="pair">']
for room in ['H30', 'H33', 'H34', 'H10']:
    body += [figure(f'hubs/before/{room}.png', room+' · 修改前'), figure(f'hubs/after/{room}.png', room+' · 当前')]
body += ['</div><p><a href="hubs/index.html">查看全部九处据点的完整前后对照</a></p></section>']

body += [f'<section class="panel" id="verify"><h2>两轮逐关试玩与章节衔接</h2><p>八张地图各完成两轮最终版本通关，共16场、{total:,}次普通按键。每场从真实游玩记录的隔离副本，经普通整备和当前地图入口开始，包含任务交互、胜利和对应战后操作。未编辑战斗属性、随机结果或强制胜利。工房最后一项修正完成后，F33又补做两轮，表中采用最终版本记录。</p><div class="overflow"><table><thead><tr><th>地图</th><th>第一轮</th><th>第二轮</th></tr></thead><tbody>']
for c in codes:
    body.append(f'<tr><td>{c}</td><td>{plays[c][0]["turns"]}回合</td><td>{plays[c][1]["turns"]}回合</td></tr>')
body += ['</tbody></table></div><p>从本轮M33真实战后记录，正常调动两队进入会合营站，完成会谈、关系与传令剧情，确认第三章结束并进入第四章。此项是章节衔接检查，范围与逐关试玩分别记录。</p><div class="pair">', figure('flow/chapter-end.png', '真实输入 · 第三章完成'), figure('flow/chapter4-start.png', '真实输入 · 第四章入口'), '</div>']
body += [f'<p>{rules["check_count"]}项规则与连通检查、{inv["check_count"]}项修改范围检查、{worldphase["count"]}项世界显示阶段检查、{hubphase["count"]}项据点显示范围检查、10项材质名称检查通过；19处据点可见交互通过。24张战斗、24张世界、9张据点、2张工房细节和2张章节衔接视口在后台捕获，记录的文字布局检查没有错误。</p><p>独立应用完成{pack["checks"]:,}项资源、地图、显示器与排除目录核对；包内40图的SHA-256与当前源数据逐一相同。第一、二章季节选择也在导出包中复查，避免世界底图被后续章节覆盖。</p>']
body += ['<details><summary>验证边界与保留的未完成尝试</summary><p>上述两轮是逐关的真实记录重开，不等于从新游戏完整通关两次。额外整章连续尝试继承了多名濒死队员，在M31剩一名敌军时达到测试驾驶的90回合上限，没有计作通关，也未为此修改伤情、敌人或难度。各关最终版本两轮均通过；章节衔接另从本轮战后记录验证。</p><p>本次没有安装手机包。HTML文件路径、图片及交互脚本检查与Godot文字布局检查已执行，未把它们表述为浏览器布局引擎实测。</p><p><a href="play/continuous/continuous-play.json">未完成的连续尝试原始记录</a> · <a href="flow-continuation.json">章节衔接记录</a></p></details><details><summary>新增素材与源图记录</summary><p>工房工作台由内置imagegen生成透明PNG，按实际48×32脚印等比导出，最终2461字节。原始1536×1024源图与完整提示词保存在工程离线source目录，未打入游戏包；运行图检查透明边缘、完整轮廓和实际像素尺寸。其余地面均复用既有原生像素瓦片；大图集保留原生分辨率和瓦片索引，体积按无损质量优先处理。</p><p><a href="../../source/chapter3-environment-20261023/workshop-prompt.txt">完整生成提示词</a> · <a href="../../source/chapter3-environment-20261023/export.json">源图与导出记录</a> · <a href="../../assets/chapter3-environment-20261023/maps/workshop-equipment.png">运行工作台48×32</a></p></details><p><a href="invariants-audit.json">修改范围检查</a> · <a href="rules-probe.json">规则检查</a> · <a href="package-checks.json">当前独立包验证</a> · <a href="delivery-summary.json">交付清单</a> · <a href="../../../docs2/完整游戏流程.md">完整流程文档1.18</a></p></section><footer>软件0.10.3，地图材质0.10.13-environment。第一、二章已确认的环境修订保留；其余章节战斗地图文件保持。不新增旧图兼容副本。</footer></main></body></html>']
(O/'index.html').write_text(''.join(body))
images = []
for folder in ['before', 'images', 'screenshots', 'world', 'world/screenshots', 'hubs/before', 'hubs/after', 'details', 'flow']:
    for p in sorted((O/folder).glob('*.png')):
        im = Image.open(p)
        images.append(dict(path=str(p.relative_to(O)), size=list(im.size), bytes=p.stat().st_size, sha256=sha(p)))
summary = dict(passed=True, date='2026-10-23', revision='0.10.13-environment', changed_maps=inv['changed_maps'], map_hashes=current, plays=plays, per_map_inputs=total, rules_checks=rules['check_count'], invariant_checks=inv['check_count'], world_fixture_checks=worldphase['count'], hub_fixture_checks=hubphase['count'], hub_interactions=len(hubinputs['records']), hub_inputs=hubinputs['inputs'], terrain_names=len(terrain['checks']), native_viewports=sum(len(c['shots'])for c in captures.values()), package_passed=pack['passed'], package_pck_sha256=pack['pck_sha256'], app_path=pack['app_path'], flow_continuation=flow, generated_asset=material.get('generated_asset'), images=images, limitations=['Two checkpoint replays per final map, not two new-game runs.', 'Optional continuous pilot stopped at M31 turn limit with inherited dying members; not counted as cleared.', 'Chapter transition separately passed from a real current-round post-battle record.', 'No phone installation; browser layout engine not automatically verified.'])
(O/'delivery-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({k:summary[k]for k in ['passed','per_map_inputs','native_viewports','package_passed']}, ensure_ascii=False))
