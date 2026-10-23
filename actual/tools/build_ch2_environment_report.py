#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
import json,html,hashlib,re,shutil,subprocess
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter2-environment-20261023'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();e=html.escape
codes=['F21','F22','F23','F24','F25','F26','S21','S22']
notes={
'F21':('海上拦截 · 船医区与甲板舱','船体、双跳板、海水和后甲板布局原本合理。将船医恢复格的石质铺面改成木板，船员休息舱换同尺寸木质甲板舱，避免船上出现陆地小屋；恢复功能与站位保持。'),
'F22':('押送舰救援 · 露天甲板与室内囚舱','露天甲板保留旧木板，两间去顶囚舱改为干燥室内木地，开门后的门槛同步使用木地。船舱外形与船医区修正；救援门、三名俘虏、洛德及接应位置均保持。'),
'F23':('礁岛登岸 · 沙滩、草坡与黑昼初段','沙岸、草坡、林崖与渔村的空间关系成立，地面与布局保留。剧情已出现黑昼与异常魔物，因此环境改成较轻的冷暗光，与岸上据点和大地图一致。'),
'F24':('海灯岛防卫 · 保留航灯石庭','现有石制灯庭、草地边缘、沙岸和黑昼冷光已经符合剧情，地图文件与原生画面保持。战后据点原来的大片草地改成对应石庭，解决战场与据点的材质落差。'),
'F25':('潮狩军港 · 石铺仓院与室内牢房','露天仓院保留粗石铺面，东侧牢室与开门门槛改成室内石板。环境光同步黑昼中的军港据点，不再在离开海灯岛后突然恢复明亮白昼。'),
'F26':('断航古道 · 石岸、潮道与西渡亮光','石质古道、草坡、两条海上通道和接应石门关系成立，保持原文件与画面。这里穿过局部神幕前往西岸，按原剧情保留自然光；大地图在古道周围也恢复明亮。'),
'S21':('漂泊渔船 · 保留船板与真实沙岸','双船、跳板和接应沙岸符合救援场景，保留原材质与行动路线。船员休息舱换成同尺寸甲板舱，让船体读法与F21/F22一致。'),
'S22':('碎石海洞 · 灰岩主巷与潮湿沉积厅','室内海洞的明黄色户外土路改成磨损灰岩，保留较暗的潮湿沉积厅与潮池。主路仍可辨认，岩壁、拱门、藏身区、遗物与出口位置不变。')}
selection=read(O/'selected-play.json');inv=read(O/'invariants-audit.json');rules=read(O/'rules-probe.json');pack=read(O/'package-checks.json');worldphase=read(O/'world/phase-fixture.json');hubfreeze=read(O/'hubs/freeze.json')
shots=read(O/'screenshots/captures.json');worldshots=read(O/'world/screenshots/captures.json');worldreview=read(O/'world/visual-review.json');hubshots=read(O/'hubs/after/captures.json')
for d in [inv,rules,pack,worldphase,hubfreeze,shots,worldshots,worldreview,hubshots]:assert d['passed']
current=inv['map_hashes'];plays={};total=0
for c in codes:
 plays[c]=[]
 for label in selection[c]:
  p=O/f'play/{label}/{label}-play.json';record=read(p);b=next(b for b in record['battles']if b['code']==c)
  assert b['outcome']=='victory'and not b['failures']and b['entry_map_sha256']==b['map_sha256']==current[c]
  assert not record['stat_edits']and not record['forced_victories']and not record['source_saves_modified']
  total+=b['key_inputs'];plays[c].append({'label':label,'turns':b['final_turn'],'inputs':b['key_inputs'],'source':str(p.relative_to(O))})
world=O/'world';shutil.copy2(R/'assets/chapter1-climate-20261022/world/overview-winter.png',world/'before-overview.png');shutil.copy2(R/'assets/chapter2-environment-20261023/world/overview-blackday.png',world/'after-overview.png')
images=[]
for folder in ['before','images','screenshots','world/screenshots']:
 for p in sorted((O/folder).glob('*.png')):
  raw=Image.open(p).convert('RGBA').tobytes();subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(p)],check=True);im=Image.open(p)
  assert im.convert('RGBA').tobytes()==raw;images.append({'path':str(p.relative_to(O)),'size':list(im.size),'bytes':p.stat().st_size,'sha256':sha(p)})
css=re.search(r'<style>(.*?)</style>',(R/'reports/chapter1-climate-20261022/index.html').read_text(),re.S).group(1)
def figure(path,title):return f'<figure><a href="{path}" target="_blank"><img src="{path}" loading="lazy" alt="{e(title)}"></a><figcaption>{e(title)}</figcaption></figure>'
body=['<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>第二章 · 环境与室内外材质修订</title><style>'+css+'</style></head><body><main><div class="eyebrow">REVENGE MEMORIES / CHAPTER TWO / 2026.10.23</div><h1>第二章 · 世界、战场与据点的环境统一</h1><span class="badge">地图材质 0.10.12-environment</span><p>逐一核对八场战斗、七处据点及群岛航线。本章发生在海岛、船只、港口、古道与海洞；草坡、沙岸、木船甲板、室内木地、露天石铺与室内岩地应各有明确用途。黑昼按剧情阶段和地理位置衔接，不照搬第一章雪景。</p><p>六张战斗图作必要修正；海灯岛F24与断航古道F26已经合理，保持原样。保留整体构图、部署、敌人、任务位置、通行规则、剧情和现有动画。</p><nav><a href="#world">世界与黑昼</a>']
for c in codes:body.append(f'<a href="#{c}">{c}</a>')
body+=['<a href="#hubs">七处据点</a><a href="#verify">试玩记录</a><a href="../../../art-review/battle-maps-20261021/index.html">全部40图</a><a href="../../dist/RevengeMemories-Chapter2-Environment-20261023.app">独立桌面应用</a></nav><section class="panel" id="world"><h2>群岛黑昼延续，西渡古道恢复亮光</h2><p>第二章回到半年前，前段西大陆沿用第一章日返前的冬景，即使存档已经保存第一章完成状态也不会提前转暖。押送舰战后正常安置伤者、确认后续航行时，对应西大陆日返与东群岛黑昼同时发生：西大陆转暖，礁岛光线偏冷，海灯岛最暗，军港与据点保持中等冷暗。西侧古道位于局部神幕边缘，保留自然光。全图总览与局部行军画面使用同一故事阶段。下方是两个剧情时段的对照，雪线缩小表示日返后的西大陆转暖；不会仅因切换章节就回退。原节点、道路和解锁数据逐字节保持。</p><div class="pair">',figure('world/before-overview.png','第二章前段／西大陆沿用第一章日返前冬景'),figure('world/after-overview.png','黑昼开始后／西大陆日返转暖，东群岛黑昼'),'</div><div class="shots">']
for name,title in [('H21-windlamp-before','风灯岛：出航前自然光'),('H24-reef-after','礁岛：黑昼初段冷光'),('H25-beacon-after','海灯岛：黑昼最暗区域'),('H26-harbor-after','军港：延续黑昼'),('ancient-passage-light','断航古道：西渡神幕边缘'),('H25-beacon-after-overview-zoom','黑昼全图：放大后的同一环境')]:body.append(figure('world/screenshots/'+name+'.png',title))
body+=['</div><p><a href="world/visual-review.json">逐图视觉检查</a> · <a href="world/phase-fixture.json">章节及剧情阶段检查</a></p></section>']
for c in codes:
 d=read(R/f'data/stages/{c}.json');title,note=notes[c]
 body.append(f'<section class="panel" id="{c}"><div class="eyebrow">{c} / {d["map"]["width"]} × {d["map"]["height"]}</div><h2>{e(title)}</h2><p>{e(note)}</p><div class="pair">')
 body.extend([figure('before/'+c+'.png','修改前 · 上轮展示版本'),figure('images/'+c+'.png','当前Godot原生场景 · '+('保持原样'if c in ['F24','F26']else '环境修正')),'</div><div class="cards">'])
 for i,p in enumerate(plays[c]):body.append(f'<article><h3>第{i+1}轮普通输入试玩</h3><div class="stat">第{p["turns"]}回合完成</div><p>胜利并完成对应战后操作；<a href="{p["source"]}">{p["inputs"]:,}次按键记录</a>。</p></article>')
 body.append('</div><div class="shots">')
 for suffix,title in [('deployment','实际部署'),('field','实际推进'),('victory','实际结算')]:body.append(figure(f'screenshots/{c}-{suffix}.png',c+' · '+title))
 body.append('</div>')
 if c=='F22':body.append(figure('ships/images/F22-gates-open.png','真实开门后：两间囚舱与木门槛'))
 if c=='F25':body.append('<div class="pair">'+figure('coasts/details/F25-entry.png','关门时的牢室石地')+figure('coasts/details/F25-object-pilot_prison.png','真实开门后：门槛仍是室内石地')+'</div>')
 body.append('</section>')
body+=['<section class="panel" id="hubs"><h2>船缘、登船出口与岸侧据点</h2><p>H21—H26的海上出口补接驳船，短木栈明确通向船只；H22/H23木甲板补连续船缘，H25航灯前场改为与战场一致的石庭，H26岸侧仓院使用仓库外观。H24和黑昼后回访船团的光照同步。H27西岸广场保持原样。</p><div class="pair">']
for room,label in [('H22','船团甲板与接驳船'),('H25','航灯石庭'),('H26','军港仓院')]:
 body+= [figure('hubs/before/'+room+'.png',label+' · 修改前'),figure('hubs/after/'+room+'.png',label+' · 修改后')]
body+=['</div><p>七据点的地面通行、碰撞、出入口和全部剧情对象位置保持；28处对象完成普通输入确认。</p><p><a href="hubs/index.html">查看七据点完整前后对照</a></p></section><section class="panel" id="verify"><h2>两轮试玩与主流程检查</h2>',f'<p>八张关卡各完成两轮最终通关，共16场、{total:,}次按键，涵盖俘虏撤离、航灯守护、引航者救援、遗物取回、居民船通行与对应战后剧情。表内每场均从真实记录隔离副本，经普通整备、当前地图入口重开；未修改属性、随机结果或强制胜利。</p><div class="overflow"><table><thead><tr><th>地图</th><th>第一轮</th><th>第二轮</th></tr></thead><tbody>']
for c in codes:body.append(f'<tr><td>{c}</td><td>{plays[c][0]["turns"]}回合</td><td>{plays[c][1]["turns"]}回合</td></tr>')
body.append('</tbody></table></div>')
flowpath=O/'flow-continuation.json';flow=read(flowpath)if flowpath.exists()else None
if flow:
 assert flow['passed'] and len(flow['battles'])==8
 for b in flow['battles']:assert b['outcome']=='victory'and b['map_sha256']==current[b['code']]
 body.append('<p>'+e(flow['description'])+'</p><p><a href="flow-continuation.json">连续流程与章节衔接记录</a></p>')
 if (O/'flow/captures.json').exists():
  endingphotos=read(O/'flow/captures.json');assert endingphotos['passed']
  body.append('<div class="pair">')
  for shot in endingphotos['shots']:
   path='flow/'+Path(shot['path']).name
   body.append(figure(path,shot.get('title',shot.get('name','章节衔接'))))
  body.append('</div>')
body+= [f'<p>{rules["check_count"]}项规则及连通检查、{inv["check_count"]}项修改范围检查、220项世界显示与885项据点材质检查通过。24张战斗、21张世界图、7张据点当前实机视口完成后台捕获；文字布局检查无错误。独立应用的40张地图与新资源均与当前源数据一致。</p>',
'<details><summary>原始尝试与验证边界</summary><p>逐关两轮不等于从新游戏完整通关两次。早期F22冲过跳板后主角濒死，F24一次守灯尝试也失败；两份记录均保留。F22测试驾驶随后先守跳板清理主动追击兵，再整队登舰，普通输入两轮完成；F24地图未改，补测通过。未为测试降低敌人属性或改变胜败规则。</p><p>连续试玩首轮在F22因治疗者濒死、剩余近战守卫前的保守操作停滞，测试达91回合上限；属于自动操作策略未完成，未将它计作通关。连续验证的最终范围以单独记录为准。未安装手机包；HTML路径检查不等于浏览器布局引擎实测。</p><p><a href="play/round1-ships/round1-ships-play.json">初次船战记录</a> · <a href="play/round1-coasts/round1-coasts-play.json">初次海岸记录（含F24失败）</a> · <a href="play/continuous-final/continuous-final-play.json">初次连续流程记录</a></p></details><p><a href="invariants-audit.json">修改范围检查</a> · <a href="rules-probe.json">规则检查</a> · <a href="package-checks.json">独立包验证</a> · <a href="delivery-summary.json">交付清单</a> · <a href="../../../docs2/完整游戏流程.md">流程文档1.17</a></p></section><footer>软件0.10.3，地图材质0.10.12-environment。第一章已确认冬景及第三至第五章地图保持。仅调整必要的环境表现和材质；不新增旧图兼容副本。</footer></main></body></html>']
(O/'index.html').write_text(''.join(body))
summary={'passed':True,'date':'2026-10-23','revision':'0.10.12-environment','changed_maps':inv['changed_maps'],'unchanged_maps':inv['unchanged_maps'],'map_hashes':current,'plays':plays,'per_map_inputs':total,'world_story_time_correction':inv.get('world_story_time_correction'),'world_fixture_checks':220,'hub_fixture_checks':885,'rules_checks':rules['check_count'],'invariant_checks':inv['check_count'],'battle_screenshots':len(shots['shots']),'world_screenshots':len(worldshots['shots']),'hub_screenshots':len(hubshots['shots']),'package_passed':pack['passed'],'flow_continuation':flow,'images':images,'limitations':['16 successful per-map checkpoint plays, not two new-game runs.','Initial F22/F24 failed attempts and continuous F22 harness stall preserved.','No phone installation; browser layout not automatically verified.']}
(O/'delivery-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:summary[k]for k in ['passed','changed_maps','per_map_inputs','battle_screenshots','world_screenshots','hub_screenshots','package_passed']},ensure_ascii=False))
